import jwt, random, string, requests

def decode_token(token, secret):
    return jwt.decode(token, algorithms=["HS256"], key=secret)

def generate_random_secret_key(length):
    hexString = string.hexdigits
    return ''.join(random.choice(hexString) for i in range(length))

def check_is_admin(headers):
    response = requests.get("http://127.0.0.1:5000/verify-admin", headers=headers)
    is_admin = response.json()["is_admin"]
    return is_admin