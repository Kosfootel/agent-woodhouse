import requests
import re
import base64

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
})

router_ip = '192.168.50.1'
username = 'admin'
password = 'LuckyToby1!'

print('=== Examining Main_Login.asp ===')
resp = session.get(f'http://{router_ip}/Main_Login.asp', timeout=10)

# Look for login form
form_match = re.search(r'<form[^>]*action=["\']([^"\']+)["\'][^>]*>(.*?)</form>', resp.text, re.DOTALL | re.I)
if form_match:
    print(f'Form action: {form_match.group(1)}')
    form_content = form_match.group(2)
    
    # Find all input fields
    inputs = re.findall(r'<input[^>]*name=["\']([^"\']+)["\'][^>]*>', form_content, re.I)
    print(f'Input fields: {inputs}')

# Look for JavaScript that handles login
print('\n=== Looking for login handler JS ===')
js_match = re.search(r'function\s+login[^}]*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}', resp.text, re.I)
if js_match:
    print(f'Login function found: {js_match.group(1)[:500]}')

# Look for any hash/encryption functions
print('\n=== Looking for password handling ===')
pwd_match = re.search(r'login_authorization|password.*encode|b64encode|hex_md5|sha256', resp.text, re.I)
print(f'Password encoding found: {pwd_match is not None}')

# Look for asus_specific variables
print('\n=== Looking for ASUS-specific variables ===')
for var in ['asus_token', 'csrf', 'b64pwd', 'encrypt_pwd']:
    if var in resp.text.lower():
        print(f'Found {var} in page')

# Try to find what happens on form submit
print('\n=== Looking for form submit handler ===')
onclick_match = re.findall(r'onclick=["\']([^"\']+)["\']', resp.text, re.I)
for handler in onclick_match[:5]:
    print(f'Onclick handler: {handler[:100]}')

# Try different login approaches
print('\n=== Test: POST with form-like data ===')
login_data = {
    'login_authorization': base64.b64encode(f'{username}:{password}'.encode()).decode(),
    'current_page': 'Main_Login.asp',
    'action_mode': '',
    'action_script': '',
    'action_wait': '5'
}

resp2 = session.post(f'http://{router_ip}/login.cgi', data=login_data, allow_redirects=False, timeout=10)
print(f'Status: {resp2.status_code}')
print(f'Cookies after login: {dict(session.cookies)}')

# Check if we got a token
token = session.cookies.get('asus_token')
if token:
    print(f'Got token: {token[:30]}...')
    
    # Try to use it
    print('\n=== Testing token with API call ===')
    api_resp = session.get(f'http://{router_ip}/appGet.cgi?hook=nvram_get(custom_clientlist)')
    print(f'API status: {api_resp.status_code}')
    print(f'Response preview: {api_resp.text[:200]}')
else:
    print('No asus_token cookie received')
    print(f'Response preview: {resp2.text[:300]}')
