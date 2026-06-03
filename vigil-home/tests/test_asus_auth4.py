import requests
import re
import base64

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
})

router_ip = '192.168.50.1'
username = 'admin'
password = 'LuckyToby1!'

print('=== Deep Dive into Login Page ===')
resp = session.get(f'http://{router_ip}/Main_Login.asp', timeout=10)

# Look for JavaScript files
print('\n--- JavaScript files ---')
js_files = re.findall(r'src=["\']([^"\']+\.js)["\']', resp.text)
for js in js_files[:10]:
    print(f'JS file: {js}')

# Look for login function in the HTML
print('\n--- Login function in HTML ---')
login_func = re.search(r'function\s+login\s*\([^)]*\)\s*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}', resp.text, re.I)
if login_func:
    print(f'Found login function: {login_func.group(1)[:500]}')

# Look for any cookie/session handling
print('\n--- Cookie handling ---')
cookie_refs = re.findall(r'document\.cookie[^;]*', resp.text, re.I)
for ref in cookie_refs[:5]:
    print(f'Cookie ref: {ref}')

# Try to find what sets the asus_token
print('\n--- Looking for token setting ---')
token_set = re.findall(r'asus_token\s*=\s*([^;\s]+)', resp.text, re.I)
for ts in token_set[:5]:
    print(f'Token set: {ts[:100]}')

# Check for ajax login endpoint
print('\n--- Looking for AJAX endpoints ---')
ajax_refs = re.findall(r'ajax_url|api_url|login_url\s*=\s*["\']([^"\']+)["\']', resp.text, re.I)
for ref in ajax_refs[:5]:
    print(f'AJAX ref: {ref}')

# Try to fetch the main JS files to understand login
print('\n--- Fetching main JS to check login logic ---')
main_js = re.search(r'general\.js|main\.js|asus.*\.js', resp.text, re.I)
if main_js:
    print(f'Found potential JS: {main_js.group(0)}')

# Check for captive portal or special handling
print('\n--- Checking for special handling ---')
if 'captive' in resp.text.lower():
    print('Captive portal detected')
if 'two_factor' in resp.text.lower() or '2fa' in resp.text.lower():
    print('Two-factor auth may be required')

# Try with headers that mimic browser more closely
print('\n--- Test with full browser headers ---')
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Referer': f'http://{router_ip}/Main_Login.asp',
    'Origin': f'http://{router_ip}',
    'Connection': 'keep-alive',
}

session2 = requests.Session()
session2.headers.update(headers)

# Get login page again with proper headers
resp2 = session2.get(f'http://{router_ip}/Main_Login.asp', timeout=10)
print(f'Login page with headers: {resp2.status_code}')

# Try login
login_data = {
    'login_authorization': base64.b64encode(f'{username}:{password}'.encode()).decode(),
    'current_page': 'Main_Login.asp'
}

resp3 = session2.post(f'http://{router_ip}/login.cgi', 
    data=login_data,
    headers={'X-Requested-With': 'XMLHttpRequest'},
    allow_redirects=False, timeout=10)
print(f'Login attempt: {resp3.status_code}')
print(f'Cookies: {dict(session2.cookies)}')
print(f'Response preview: {resp3.text[:300]}')
