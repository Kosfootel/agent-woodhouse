#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/erik-ross/vigil/backend/app')
import requests
import base64
import re

# ASUS Router API Test
router_ip = '192.168.50.1'
username = 'admin'
password = 'LuckyToby1!'

session = requests.Session()

# Encode credentials
creds = f"{username}:{password}"
encoded = base64.b64encode(creds.encode()).decode()
print(f"Encoded creds: {encoded}")

# Login
login_url = f"http://{router_ip}/login.cgi"
login_data = {"login_authorization": encoded}

print(f"\nPOST {login_url}")
response = session.post(login_url, data=login_data, allow_redirects=True)
print(f"Status: {response.status_code}")
print(f"Headers: {dict(response.headers)}")
print(f"Cookies: {dict(session.cookies)}")
print(f"Response text (first 1000 chars):\n{response.text[:1000]}")

# Look for asus_token
asus_token = None
patterns = [
    r'asus_token\s*=\s*["\']?([^"\'\s;]+)',
    r'token\s*:\s*["\']?([^"\'\s,}]+)',
]
for pattern in patterns:
    match = re.search(pattern, response.text, re.IGNORECASE)
    if match:
        asus_token = match.group(1)
        print(f"\nFound token: {asus_token}")
        break

# Check for Set-Cookie
cookies = session.cookies.get_dict()
print(f"\nSession cookies: {cookies}")

# Try to make a request with cookies
test_url = f"http://{router_ip}/appGet.cgi?hook=nvram_get(custom_clientlist)"
print(f"\nGET {test_url}")
response2 = session.get(test_url)
print(f"Status: {response2.status_code}")
print(f"Response (first 500 chars):\n{response2.text[:500]}")

# If token found, try setting it as cookie
if asus_token:
    session.cookies.set('asus_token', asus_token)
    print(f"\nRetrying with asus_token cookie...")
    response3 = session.get(test_url)
    print(f"Status: {response3.status_code}")
    print(f"Response (first 500 chars):\n{response3.text[:500]}")
