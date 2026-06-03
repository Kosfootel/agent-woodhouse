#!/usr/bin/env python3
"""
ASUS Router Authentication Research

Based on testing, the ASUS GT6 router:
1. Requires login via /login.cgi
2. Uses login_authorization field
3. Has "encrypt" references in the page
4. Is redirecting to login page (authentication failing)

Hypotheses:
- Password may need client-side encryption before base64 encoding
- May require specific CSRF token or session cookie first
- May use different base64 variant
- May require specific User-Agent or headers
"""

import requests
import re
import base64
import hashlib
import html

session = requests.Session()
router_ip = '192.168.50.1'
username = 'admin'
password = 'LuckyToby1!'

def try_login(auth_value, description):
    """Try a login method and report results."""
    sess = requests.Session()
    sess.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': f'http://{router_ip}/Main_Login.asp',
    })
    
    resp = sess.post(f'http://{router_ip}/login.cgi',
        data={'login_authorization': auth_value},
        allow_redirects=False,
        timeout=10)
    
    cookies = list(sess.cookies.keys())
    has_token = 'asus_token' in cookies
    
    print(f"{description}:")
    print(f"  Status: {resp.status_code}")
    print(f"  Has asus_token: {has_token}")
    print(f"  Response: {resp.text[:100].replace(chr(10), ' ')}")
    print()
    
    return has_token

print("=== ASUS GT6 Authentication Research ===")
print()

# First, let's see what the actual login form submits
print("--- Checking form submission requirements ---")
sess = requests.Session()
resp = sess.get(f'http://{router_ip}/Main_Login.asp')

# Look for any JavaScript that processes the login
print("JavaScript login handling:")
scripts = re.findall(r'<script[^>]*>(.*?)</script>', resp.text, re.DOTALL | re.I)
for i, script in enumerate(scripts):
    if 'login' in script.lower() or 'auth' in script.lower() or 'encrypt' in script.lower():
        print(f"  Script {i+1} contains login/auth/encrypt logic")
        # Look for specific patterns
        if 'hex' in script.lower():
            print(f"    - Contains hex reference")
        if 'base64' in script.lower():
            print(f"    - Contains base64 reference")
        if 'sha' in script.lower():
            print(f"    - Contains SHA reference")

# Try common encodings
print()
print("=== Testing Authentication Methods ===")
print()

methods = [
    # Standard base64
    (base64.b64encode(f'{username}:{password}'.encode()).decode(), "Standard base64"),
    
    # Base64 with URL-safe variant
    (base64.urlsafe_b64encode(f'{username}:{password}'.encode()).decode(), "URL-safe base64"),
    
    # Just password base64
    (base64.b64encode(password.encode()).decode(), "Password-only base64"),
    
    # Hex encoding
    (f'{username}:{password}'.encode().hex(), "Hex encoded"),
    
    # Try MD5 hash of password
    (f'{username}:{hashlib.md5(password.encode()).hexdigest()}', "MD5 password hash"),
    
    # Try SHA256 hash of password  
    (f'{username}:{hashlib.sha256(password.encode()).hexdigest()}', "SHA256 password hash"),
    
    # Try with HTTP basic auth format (same as base64)
    (base64.b64encode(f'{username}:{password}'.encode()).decode(), "HTTP Basic auth format"),
]

for auth_val, desc in methods:
    if try_login(auth_val, desc):
        print("*** SUCCESS! ***")
        break

print()
print("=== Conclusion ===")
print("If none of the above worked, the ASUS GT6 likely uses:")
print("1. Client-side JavaScript encryption before transmission")
print("2. A CSRF token or hidden field that must be included")
print("3. Session cookie requirement before login POST")
print("4. Different endpoint or protocol")
print()
print("Recommendation: Use ARP scanning as fallback, or")
print("investigate the JavaScript login handler more deeply.")
