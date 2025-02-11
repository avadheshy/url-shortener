from django.db import models
from django.utils import timezone

class URL(models.Model):
    long_url = models.URLField(max_length=2048)
    short_code = models.CharField(max_length=10, unique=True, db_index=True)
    custom_alias = models.CharField(max_length=50, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    access_count = models.BigIntegerField(default=0)
    unique_visitors = models.BigIntegerField(default=0)
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['short_code']),
            models.Index(fields=['custom_alias']),
        ]

    def __str__(self):
        return f"{self.short_code} -> {self.long_url}"

class URLAccess(models.Model):
    url = models.ForeignKey(URL, on_delete=models.CASCADE, related_name='accesses')
    accessed_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(null=True, blank=True)
    referer = models.URLField(null=True, blank=True)
    country = models.CharField(max_length=2, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['url', 'accessed_at']),
            models.Index(fields=['ip_address']),
        ]
