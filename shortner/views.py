from django.shortcuts import redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from django.db import models
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import URLSerializer
from .utils import URLShortener
from .tasks import record_url_access
# from ratelimit.decorators import ratelimit
from .models import URL,URLAccess
from django.db.models import F

@api_view(['POST'])
# @ratelimit(key='ip', rate='10/m', method=['POST'])
def create_short_url(request):
    serializer = URLSerializer(data=request.data)
    if serializer.is_valid():
        long_url = serializer.validated_data['long_url']
        custom_alias = serializer.validated_data.get('custom_alias')
        expires_in_days = serializer.validated_data.get('expires_in_days')
        
        if custom_alias:
            if URL.objects.filter(custom_alias=custom_alias).exists():
                return Response({'error': 'Custom alias already exists'}, status=400)
            short_code = custom_alias
        else:
            for _ in range(3):
                short_code = URLShortener.generate_short_code(long_url, request.user.id)
                if not URL.objects.filter(short_code=short_code).exists():
                    break
            else:
                return Response({'error': 'Failed to generate unique short code'}, status=500)
        
        expires_at = None
        if expires_in_days:
            expires_at = timezone.now() + timezone.timedelta(days=expires_in_days)
        
        url_obj = URL.objects.create(
            long_url=long_url,
            short_code=short_code,
            custom_alias=custom_alias,
            expires_at=expires_at,
            user=request.user if request.user.is_authenticated else None
        )
        
        return Response(URLSerializer(url_obj).data)
    return Response(serializer.errors, status=400)

@require_http_methods(["GET"])
def redirect_to_long_url(request, short_code):
    cache_key = f'url_shortener:{short_code}'
    long_url = cache.get(cache_key)
    if not long_url:
        url_obj = get_object_or_404(URL, short_code=short_code)
        
        if url_obj.expires_at and url_obj.expires_at < timezone.now():
            return JsonResponse({'error': 'URL has expired'}, status=410)
        
        long_url = url_obj.long_url
        cache.set(cache_key, long_url, 3600)
        
        record_url_access.delay(
            url_obj.id,
            request.META.get('REMOTE_ADDR'),
            request.META.get('HTTP_USER_AGENT'),
            request.META.get('HTTP_REFERER')
        )
    else:
        # If URL was cached, we still need to update the count
        url_obj = URL.objects.get(short_code=short_code)
        URL.objects.filter(id=url_obj.id).update(
            access_count=F('access_count') + 1
        )
    
    return redirect(long_url)

@api_view(['GET'])
def url_analytics(request, short_code):
    url_obj = get_object_or_404(URL, short_code=short_code)
    
    time_window = request.GET.get('window', '24h')
    since = timezone.now()
    if time_window == '24h':
        since -= timezone.timedelta(hours=24)
    elif time_window == '7d':
        since -= timezone.timedelta(days=7)
    elif time_window == '30d':
        since -= timezone.timedelta(days=30)
    
    accesses = URLAccess.objects.filter(
        url=url_obj,
        accessed_at__gte=since
    )
    analytics = {
        'total_clicks': url_obj.access_count,
        'unique_visitors': url_obj.unique_visitors,
        'recent_clicks': accesses.count(),
        'country_distribution': dict(
            accesses.exclude(country=None)
            .values_list('country')
            .annotate(count=models.Count('id'))
        ),
        'hourly_clicks': dict(
            accesses.annotate(hour=models.functions.ExtractHour('accessed_at'))
            .values('hour')
            .annotate(count=models.Count('id'))
        ),
        'top_referrers': list(
            accesses.exclude(referer=None)
            .values('referer')
            .annotate(count=models.Count('id'))
            .order_by('-count')[:5]
        )
    }
    
    return Response(analytics)