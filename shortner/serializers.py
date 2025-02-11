from rest_framework import serializers
from .models import URL

class URLSerializer(serializers.ModelSerializer):
    short_url = serializers.SerializerMethodField()

    class Meta:
        model = URL
        fields = ['long_url', 'short_code', 'custom_alias', 'expires_at', 'short_url']
        read_only_fields = ['short_code', 'short_url']

    def get_short_url(self, obj):
        from django.conf import settings
        return f"{settings.SITE_URL}/{obj.short_code}"