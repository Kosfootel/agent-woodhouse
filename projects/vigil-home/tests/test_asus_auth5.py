import requests
import re
import base64
import hashlib

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
})

router_ip = '192.168.50.1'
username = 'admin'
password = 'LuckyToby1!'

print('=== Looking for newer ASUS authentication ===')

# Get the login page
resp = session.get(f'http://{router_ip}/Main_Login.asp', timeout=10)

# Check for newer firmware markers
print('--- Firmware version indicators ---')
if 'ASUSWRT' in resp.text:
    print('Found ASUSWRT marker')
if 'GT6' in resp.text:
    print('Found GT6 model reference')

# Look for any hash algorithms mentioned
print('\n--- Cryptographic functions ---')
crypto_funcs = re.findall(r'(sha256|md5|hex_md5|b64_sha256|encrypt)', resp.text, re.I)
if crypto_funcs:
    print(f'Found crypto refs: {set(crypto_funcs)}')

# Try the new auth endpoint used by newer ASUS routers
print('\n--- Trying /login.cgi with different encodings ---')

# Some newer ASUS routers use a different encoding
test_auths = [
    # Base64 standard
    base64.b64encode(f'{username}:{password}'.encode()).decode(),
    # Just base64 password
    base64.b64encode(password.encode()).decode(),
    # Hex encoded
    f'{username}:{password}'.encode().hex(),
    # URL encoded
    f'{username}%3A{password}',
    # Try with admin:admin for testing
    base64.b64encode(b'admin:admin').decode(),
]

for i, auth in enumerate(test_auths):
    session = requests.Session()  # Fresh session
    print(f'\nTest {i+1}: auth={auth[:30]}...')
    resp = session.post(f'http://{router_ip}/login.cgi', 
        data={'login_authorization': auth},
        allow_redirects=False, timeout=10)
    print(f'  Status: {resp.status_code}')
    print(f'  Cookies: {list(session.cookies.keys())}')
    if 'asus_token' in session.cookies:
        print(f'  SUCCESS! Token: {session.cookies["asus_token"][:30]}...')
        break
    if 'error' in resp.text.lower() and 'incorrect' in resp.text.lower():
        print('  Got incorrect password message')
    elif 'Main_Login' in resp.text:
        print('  Redirected to login')

# Try checking if there's a newer API endpoint
print('\n--- Checking for REST API endpoints ---')
endpoints = [
    '/rest_api.cgi',
    '/api.cgi',
    '/rpc',
    '/unauth.cgi',
]

for ep in endpoints:
    resp = session.get(f'http://{router_ip}{ep}', timeout=5)
    if resp.status_code != 404:
        print(f'{ep}: {resp.status_code}')

# Check for asuswrt-merlin markers
print('\n--- Looking for Merlin/Custom firmware markers ---')
if 'merlin' in resp.text.lower():
    print('Merlin firmware detected')
if '梅林' in resp.text:  # Chinese for Merlin
    print('Merlin firmware detected (Chinese)')
