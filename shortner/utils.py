import hashlib
import base62
from django.utils import timezone

class URLShortener:
    @staticmethod
    def generate_short_code(url, user_id=None):
        timestamp = str(timezone.now().timestamp()).encode('utf-8')
        user_id = str(user_id).encode('utf-8') if user_id else b''
        url = url.encode('utf-8')
        
        input_data = timestamp + user_id + url
        hash_object = hashlib.md5(input_data)
        hash_hex = hash_object.hexdigest()
        
        return base62.encodebytes(hash_hex.encode())[:6]