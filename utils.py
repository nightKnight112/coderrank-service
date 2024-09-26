import jwt

def decode_token(token, secret):
    return jwt.decode(token, algorithms=["HS256"], key=secret)