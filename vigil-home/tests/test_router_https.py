#!/usr/bin/env python3
"""Test HTTPS and other ASUS authentication variants"""
import requests
import base64
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

router_ip = '192.168.50.1'
username = 'admin'
password = 'LuckyToby1!'

# Try HTTPS
print("=== Try HTTPS login ===")
session = requests.Session()
session.verify = False

login_url = f"https://{router_ip}/login.cgi"
encoded_creds = base64.b64encode(f"{username}:{password}".encode()).decode()

login_data = {
    'login_authorization': encoded_creds,
    'current_page': 'Main_Login.asp',
    'next_page': 'Main_Login.asp',
}

try:
    response = session.post(login_url, data=login_data, allow_redirects=True, timeout=10)
    print(f"HTTPS Status: {response.status_code}")
    print(f"Cookies: {dict(session.cookies)}")
    print(f"Response: {response.text[:500]}")
except Exception as e:
    print(f"HTTPS error: {e}")

# Try admin endpoints
print("\n=== Check admin endpoints ===")
endpoints = [
    '/admin.asp',
    '/Advanced_OpenVPNClient_Content.asp',
    '/QIS_wizard.htm',
    '/router_info.asp',
    '/get_clientlist.asp',
]

session2 = requests.Session()
for ep in endpoints:
    try:
        url = f"http://{router_ip}{ep}"
        r = session2.get(url, timeout=5)
        print(f"{ep}: {r.status_code} (len={len(r.text)})")
    except Exception as e:
        print(f"{ep}: Error - {e}")

# Try getting client list via different method
print("\n=== Check for client list endpoints ===")
client_endpoints = [
    '/update_clients.asp',
    '/get_clientlist.asp',
    '/client_status.asp',
    '/networkmap.asp',
]

for ep in client_endpoints:
    try:
        url = f"http://{router_ip}{ep}"
        r = session2.get(url, timeout=5)
        print(f"{ep}: {r.status_code} (len={len(r.text)})")
        if r.status_code == 200 and len(r.text) > 100:
            print(f"  Content preview: {r.text[:300]}")
    except Exception as e:
        print(f"{ep}: Error - {e}")
