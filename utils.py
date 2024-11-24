import jwt, random, string

def decode_token(token, secret):
    return jwt.decode(token, algorithms=["HS256"], key=secret)

def generate_random_secret_key(length):
    hexString = string.hexdigits
    return ''.join(random.choice(hexString) for i in range(length))