client_id = "IgymH0O1x9KAoOeWHm9LdI50QOjF7Cdd0ieKgn7G"
client_secret = "CjUITk4lbRb0opB8pibqRSXYxZvNQ9qahEV3rYmnIm2xLaM5AuVfa4nFDTCp1Q7EXXAzA2WxbNcyN5Chh1dPCqc8IVsf7MXPv6Ud4uvWEJXln42VvhDUJhiZRpmRBW9W"

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
