import requests
import re
import base64
import hashlib

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Referer': 'http://192.168.50.1/Main_Login.asp'
})

router_ip = '192.168.50.1'
username = 'admin'
password = 'LuckyToby1!'

print('=== Testing Multiple Auth Methods ===')

# Method 1: Try with SHA256 (newer ASUS firmware)
print('\n--- Method 1: SHA256 hash ---')
auth_str = f"{username}:{password}"
sha256_auth = hashlib.sha256(auth_str.encode()).hexdigest()

resp1 = session.post(f'http://{router_ip}/login.cgi', 
    data={'login_authorization': sha256_auth},
    allow_redirects=False, timeout=10)
print(f'Status: {resp1.status_code}')
print(f'Cookies: {dict(session.cookies)}')

session.cookies.clear()

# Method 2: Try hex-encoded instead of base64
print('\n--- Method 2: Hex encoded ---')
hex_auth = auth_str.encode().hex()
resp2 = session.post(f'http://{router_ip}/login.cgi', 
    data={'login_authorization': hex_auth},
    allow_redirects=False, timeout=10)
print(f'Status: {resp2.status_code}')
print(f'Cookies: {dict(session.cookies)}')

session.cookies.clear()

# Method 3: Try direct username/password fields
print('\n--- Method 3: Direct fields ---')
resp3 = session.post(f'http://{router_ip}/login.cgi', 
    data={
        'login_username': username,
        'login_passwd': password,
        'login_authorization': base64.b64encode(f'{username}:{password}'.encode()).decode()
    },
    allow_redirects=False, timeout=10)
print(f'Status: {resp3.status_code}')
print(f'Cookies: {dict(session.cookies)}')

session.cookies.clear()

# Method 4: Check if router requires HTTPS
print('\n--- Method 4: Try HTTPS ---')
try:
    session2 = requests.Session()
    session2.headers.update({'User-Agent': 'Mozilla/5.0'})
    resp4 = session2.post(f'https://{router_ip}/login.cgi', 
        data={'login_authorization': base64.b64encode(f'{username}:{password}'.encode()).decode()},
        verify=False, timeout=10)
    print(f'Status: {resp4.status_code}')
    print(f'Cookies: {dict(session2.cookies)}')
except Exception as e:
    print(f'HTTPS error: {e}')

# Method 5: Check for different endpoint
print('\n--- Method 5: Check /appGet.cgi directly ---')
resp5 = session.get(f'http://{router_ip}/appGet.cgi?hook=nvram_get(custom_clientlist)', timeout=10)
print(f'Status: {resp5.status_code}')
print(f'Is redirect: {"Main_Login" in resp5.text}')

# Method 6: Try accessing as already-authenticated (maybe browser session exists)
print('\n--- Method 6: Check if any existing session ---')
resp6 = session.get(f'http://{router_ip}/ajax_status.asp', timeout=10)
print(f'Status: {resp6.status_code}')
print(f'Content length: {len(resp6.text)}')
print(f'Is auth: {"status" in resp6.text.lower() and "Main_Login" not in resp6.text}')
