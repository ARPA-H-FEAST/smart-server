# No OIDC
# (Blown up with each new installation of DB ... )
# client_id = ""
# client_secret = ""

# With OIDC
client_id = "u02S3i6zqDAl0YqImmZKwtnDvVel25cxpKxFkjfM"
client_secret = "pGVq2Ztbp7SpvcvS5AKN2zzk83w6P2bAlB3rUZ5mebPFO1GRhcJ21StlsAyQd9vNmMNbnLAztWh8N9w25oYEUh2BVxdQiPYxcAs6pPG2Xm3MsOmwkV30w2ca6fTsDCpy"

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
