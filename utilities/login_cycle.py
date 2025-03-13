import json
import requests

import base64
import hashlib
import random
import secrets

base_url = "https://feast.mgpc.biochemistry.gwu.edu/testing-ui/"
login_info = {"email": "pmcneely@gwu.edu", "password": "pass123!"}
redirect_uri = "https://feast.mgpc.biochemistry.gwu.edu/gw-feast/callback/"
client_id = "5sUQbms4tORbBZQeuy8qh6I5SO2fS86y4rniQKOj"

# Create session
session = requests.Session()

# Create PKCE

def generate_code_verifier(length):
    return "".join(secrets.token_urlsafe(length))

code_verifier = generate_code_verifier(random.randint(43, 128))

def generate_code_challenge(code_verifier):
    hashed  = hashlib.sha256(code_verifier.encode("ascii")).digest()
    encoded = base64.urlsafe_b64encode(hashed).decode("ascii").rstrip("=")
    return encoded

code_challenge = generate_code_challenge(code_verifier)

# Get CSRF token
user_url = base_url + "users/whoami/"
response = session.get(user_url)

if response.ok:
    body = response.json()

print(f"Cookies: {session.cookies}")
print(f"Body: {body}")

# Login, get session information
login_url = base_url + "users/login/"
headers = {
    "Content-Type": "application/json"
}
response = session.post(login_url, 
    data=json.dumps(login_info),
    headers=headers,
    )

# print(f"---> Logged in: {response.text}")
# print(f"---> Logged in: {response.cookies}")
# print(f"---> Logged in: {response.headers}")

user_info = json.loads(response.text)

cookies = response.cookies.get_dict()
csrf = cookies['csrftoken']
session_id = cookies['sessionid']

# Submit OAuth request, handle return HTML
authorize_url = base_url + f"oauth/authorize/?response_type=code&code_challenge={code_challenge}"
authorize_url += f"&code_challenge_method=S256&redirect_uri={redirect_uri}&client_id={client_id}"

response = session.get(authorize_url)
# print(f"{response.text}")

import time
print("Sleeping")
time.sleep(5)
print("....resuming")

# Submit return form by "clicking" OK
payload = {
    "allow": "Authorize",
    "redirect_uri": redirect_uri,
    "scope": ["test"],
    "client_id": client_id,
    "response_type": "code",
}
headers = {
    "X-CSRFToken": csrf,
}
response = session.post(authorize_url, data=json.dumps(payload), headers=headers, allow_redirects=True)
# for var in vars(response):
#     print(var)
# print(response.status_code)
print(response.text)
# Initiate code exchange for token
