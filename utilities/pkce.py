client_id = "xxxx"
client_secret = "xxxx"

# Adapted from tutorial here: https://django-oauth-toolkit.readthedocs.io/en/stable/getting_started.html

import random
import string
import base64
import hashlib

code_verifier = "".join(
    random.choice(string.ascii_uppercase + string.digits)
    for _ in range(random.randint(43, 128))
)

code_challenge = hashlib.sha256(code_verifier.encode("utf-8")).digest()
code_challenge = (
    base64.urlsafe_b64encode(code_challenge).decode("utf-8").replace("=", "")
)

print(f"Code verifier:\n{code_verifier}")
print(f"Code challenge:\n{code_challenge}")
