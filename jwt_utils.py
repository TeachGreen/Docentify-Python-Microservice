
from base64 import urlsafe_b64decode
from fastapi import Request
from json import loads


def base64url_decode(data):
    padded = data + '=' * (-len(data) % 4)
    return urlsafe_b64decode(padded)


def get_jwt_data(request: Request):
    jwt = request.headers.get("Authorization").replace("Bearer ", "")
    return loads(base64url_decode(jwt))