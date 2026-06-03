import requests
import re
import base64

# Test different authentication approaches
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
})

router_ip = '192.168.50.1'
username = 'admin'
password = 'LuckyToby1!'

print('=== Test 1: Check login page structure ===')
resp = session.get(f'http://{router_ip}/Main_Login.asp', timeout=10)
print(f'Status: {resp.status_code}')
print(f'Contains form: {"login_form" in resp.text}')
print(f'Contains csrf: {"csrf_token" in resp.text.lower() or "asus_token" in resp.text.lower()}')

# Look for any tokens in the page
csrf_match = re.search(r'name=["\']csrf_token["\'][^>]*value=["\']([^"\']+)', resp.text, re.I)
if csrf_match:
    print(f'Found csrf_token: {csrf_match.group(1)[:20]}...')

asus_token_match = re.search(r'asus_token\s*[=:]\s*["\']([^"\']+)', resp.text, re.I)
if asus_token_match:
    print(f'Found asus_token in page: {asus_token_match.group(1)[:20]}...')

print()
print('=== Test 2: Standard form POST ===')
login_data = {
    'login_authorization': base64.b64encode(f'{username}:{password}'.encode()).decode(),
}
resp2 = session.post(f'http://{router_ip}/login.cgi', data=login_data, allow_redirects=False, timeout=10)
print(f'Status: {resp2.status_code}')
print(f'Location header: {resp2.headers.get("Location", "none")}')
print(f'Set-Cookie: {"asus_token" in str(resp2.cookies)}')

print()
print('=== Test 3: Try with session token ===')
for cookie in session.cookies:
    print(f'Cookie: {cookie.name}={cookie.value[:20]}...')

print()
print('=== Test 4: Check for login.asp vs login.cgi ===')
resp3 = session.get(f'http://{router_ip}/login.asp', timeout=5)
print(f'/login.asp exists: {resp3.status_code == 200 and "login" in resp3.text.lower()}')

print()
print('=== Test 5: Look for hidden form fields ===')
hidden_match = re.findall(r'type=["\']hidden["\'][^>]*name=["\']([^"\']+)["\'][^>]*value=["\']([^"\']*)', resp.text, re.I)
for name, value in hidden_match[:5]:
    print(f'Hidden field: {name}={value[:30]}' if value else f'Hidden field: {name}=(empty)')
