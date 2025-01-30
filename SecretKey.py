import secrets

secure_key = secrets.token_hex(64)
print(secure_key)
