#!/usr/bin/env python3
"""Full ASUS GT6 login test with proper flow"""
import requests
import base64
import hashlib
import re
import json

router_ip = '192.168.50.1'
username = 'admin'
password = 'LuckyToby1!'

session = requests.Session()

# Step 1: Get login page to establish session
print("=== Step 1: Get login page ===")
login_page = session.get(f"http://{router_ip}/Main_Login.asp", timeout=10)
print(f"Status: {login_page.status_code}")
print(f"Session cookies: {dict(session.cookies)}")

# Step 2: Get the router info which may have a token
print("\n=== Step 2: Get router info ===")
try:
    info = session.get(f"http://{router_ip}/ajax_status.asp", timeout=5)
    print(f"Status: {info.status_code}")
    print(f"Response length: {len(info.text)}")
except:
    print("Failed to get router info")

# Step 3: Look for asus_token in the login page HTML
print("\n=== Step 3: Extract tokens ===")
token_match = re.search(r'asus_token\s*=\s*["\']([^"\']+)["\']', login_page.text)
if token_match:
    asus_token = token_match.group(1)
    print(f"Found asus_token: {asus_token}")
else:
    print("No asus_token found in page")

# Step 4: Perform login with proper encoding
print("\n=== Step 4: Login ===")
login_url = f"http://{router_ip}/login.cgi"

# ASUS uses base64 encoded credentials
encoded_creds = base64.b64encode(f"{username}:{password}".encode()).decode()

login_data = {
    'login_authorization': encoded_creds,
    'current_page': 'Main_Login.asp',
    'next_page': 'Main_Login.asp',
}

print(f"Login data: {login_data}")

# Make the login request
response = session.post(login_url, data=login_data, allow_redirects=True)
print(f"Status: {response.status_code}")
print(f"Response headers: {dict(response.headers)}")
print(f"Cookies after login: {dict(session.cookies)}")
print(f"Response text:\n{response.text[:1000]}")

# Step 5: Check if login was successful
if 'Main_Login.asp' in response.text and 'href' in response.text:
    print("\nWARNING: Still redirecting to login page - login failed")
else:
    print("\nLogin may have succeeded!")

# Step 6: Try to get device list
print("\n=== Step 5: Try device list ===")
device_url = f"http://{router_ip}/appGet.cgi?hook=nvram_get(custom_clientlist)"
response2 = session.get(device_url)
print(f"Status: {response2.status_code}")
print(f"Response:\n{response2.text[:500]}")

# Try with token if we have one
if 'asus_token' in dict(session.cookies):
    print("\n=== Step 6: Retry with explicit token ===")
    token = session.cookies.get('asus_token')
    headers = {'Cookie': f'asus_token={token}'}
    response3 = session.get(device_url, headers=headers)
    print(f"Status: {response3.status_code}")
    print(f"Response:\n{response3.text[:500]}")

# Step 7: Try different API endpoint format
print("\n=== Step 7: Try nvram API ===")
try:
    nvram_url = f"http://{router_ip}/appGet.cgi"
    nvram_params = {'hook': 'nvram_get(custom_clientlist)'}
    response4 = session.get(nvram_url, params=nvram_params)
    print(f"Status: {response4.status_code}")
    print(f"Response:\n{response4.text[:500]}")
except Exception as e:
    print(f"Error: {e}")

# Step 8: Try using the REST API if available
print("\n=== Step 8: Check REST API ===")
try:
    rest_url = f"http://{router_ip}/rest/v1/client"
    response5 = session.get(rest_url)
    print(f"Status: {response5.status_code}")
    if response5.status_code == 200:
        print(f"Response:\n{response5.text[:1000]}")
except Exception as e:
    print(f"REST API not available: {e}")
