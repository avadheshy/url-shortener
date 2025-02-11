from celery import shared_task
from django.db.models import F
from django.core.cache import cache
import geoip2.database
from .models import URL, URLAccess

@shared_task
def record_url_access(url_id, ip_address, user_agent, referer):
    visitor_key = f'visitor:{url_id}:{ip_address}'
    is_new_visitor = not cache.get(visitor_key)
    
    if is_new_visitor:
        cache.set(visitor_key, True, 86400)
        URL.objects.filter(id=url_id).update(
            access_count=F('access_count') + 1,
            unique_visitors=F('unique_visitors') + 1
        )
    else:
        URL.objects.filter(id=url_id).update(access_count=F('access_count') + 1)
    
    try:
        with geoip2.database.Reader('path/to/GeoLite2-Country.mmdb') as reader:
            response = reader.country(ip_address)
            country_code = response.country.iso_code
    except:
        country_code = None
    
    URLAccess.objects.create(
        url_id=url_id,
        ip_address=ip_address,
        user_agent=user_agent,
        referer=referer,
        country=country_code
    )