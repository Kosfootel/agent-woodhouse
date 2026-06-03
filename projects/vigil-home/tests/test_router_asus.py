#!/usr/bin/env python3
"""Test ASUS router authentication methods"""
import sys
sys.path.insert(0, '/home/erik-ross/vigil/backend/app')
import requests
import hashlib
import base64
import json

router_ip = '192.168.50.1'
username = 'admin'
password = 'LuckyToby1!'

session = requests.Session()

# Method 1: Direct login with username/password in specific format
print("=== Method 1: Standard login form ===")
login_url = f"http://{router_ip}/login.cgi"

# Try form-based login
data = {
    'username': username,
    'pwd': password,
}
response = session.post(login_url, data=data, allow_redirects=True)
print(f"Status: {response.status_code}")
print(f"Cookies after login: {dict(session.cookies)}")
print(f"Response: {response.text[:500]}")

# Check if we got a token
token = session.cookies.get('asus_token') or session.cookies.get('AiCSRF_token')
print(f"Token from cookies: {token}")

# Method 2: Try with authorization header
print("\n=== Method 2: Authorization header ===")
session2 = requests.Session()
auth_str = base64.b64encode(f"{username}:{password}".encode()).decode()
headers = {'Authorization': f'Basic {auth_str}'}
response2 = session2.post(login_url, headers=headers, data={'login_authorization': auth_str})
print(f"Status: {response2.status_code}")
print(f"Cookies: {dict(session2.cookies)}")
print(f"Response: {response2.text[:500]}")

# Method 3: ASUS-specific login with hash
print("\n=== Method 3: ASUS hash login ===")
session3 = requests.Session()
# ASUS sometimes uses a hash of username+password
login_hash = hashlib.md5(f"{username}:{password}".encode()).hexdigest()
data3 = {
    'login_authorization': base64.b64encode(f"{username}:{password}".encode()).decode()
}
response3 = session3.post(login_url, data=data3)
print(f"Status: {response3.status_code}")
print(f"Cookies: {dict(session3.cookies)}")
print(f"Response: {response3.text[:500]}")

# Try accessing device list with current session
print("\n=== Test device access ===")
test_url = f"http://{router_ip}/appGet.cgi?hook=nvram_get(custom_clientlist)"
response_test = session.get(test_url)
print(f"Device list status: {response_test.status_code}")
print(f"Response: {response_test.text[:500]}")

# Check what other endpoints might work
print("\n=== Check available endpoints ===")
endpoints = ['/ajax_status.asp', '/update_clients.asp', '/status.asp', '/']
for ep in endpoints:
    try:
        r = session.get(f"http://{router_ip}{ep}", timeout=5)
        print(f"{ep}: {r.status_code} (len={len(r.text)})")
    except Exception as e:
        print(f"{ep}: Error - {e}")
