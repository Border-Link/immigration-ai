import time

from django.contrib.auth.tokens import default_token_generator
from knox.crypto import hash_token
import secrets
import hashlib
import uuid

class GenerateHash:
    @staticmethod
    def generate_token(user):
        base_token = default_token_generator.make_token(user)
        random_salt = secrets.token_urlsafe(32)
        combined_token = f"{base_token}{random_salt}"

        return hash_token(hashlib.sha256(combined_token.encode()).hexdigest())

    @staticmethod
    def generate_ref(prefix:str, length:int=15):
        random_salt = secrets.token_urlsafe(32)
        timestamp = str(int(time.time()))
        combined_token = f"{random_salt}{timestamp}"
        full_hash = hash_token(hashlib.sha256(combined_token.encode()).hexdigest())
        return f"{prefix}_{full_hash[:length]}"



class GenerateUUID:
    @staticmethod
    def generate_uuid():
        return str(uuid.uuid4())
