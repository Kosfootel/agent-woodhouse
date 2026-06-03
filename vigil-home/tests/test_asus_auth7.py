#!/usr/bin/env python3
"""
Extract and analyze the JavaScript login handler from ASUS GT6
"""

import requests
import re

router_ip = '192.168.50.1'

sess = requests.Session()
resp = sess.get(f'http://{router_ip}/Main_Login.asp')

print("=== Extracting JavaScript from Main_Login.asp ===")
print()

# Get all scripts
scripts = re.findall(r'<script[^>]*>(.*?)</script>', resp.text, re.DOTALL | re.I)

print(f"Found {len(scripts)} script blocks")
print()

for i, script in enumerate(scripts):
    script_lower = script.lower()
    if any(keyword in script_lower for keyword in ['login', 'auth', 'encrypt', 'password', 'b64', 'hex']):
        print(f"=== SCRIPT {i+1} (contains relevant keywords) ===")
        print(script[:2000])  # First 2000 chars
        print("... [truncated]" if len(script) > 2000 else "")
        print()
        print("-" * 60)
        print()

# Also look for external JS files that might handle login
print("=== External JavaScript Files ===")
js_files = re.findall(r'src=["\']([^"\']+\.js)["\']', resp.text)
print(f"Found {len(js_files)} external JS files:")
for js in js_files:
    print(f"  - {js}")

# Try to fetch the first few JS files to check for login logic
print()
print("=== Fetching key JS files ===")
for js in js_files[:3]:
    js_url = f'http://{router_ip}{js}' if js.startswith('/') else f'http://{router_ip}/{js}'
    try:
        js_resp = sess.get(js_url, timeout=5)
        if 'login' in js_resp.text.lower() or 'auth' in js_resp.text.lower() or 'encrypt' in js_resp.text.lower():
            print(f"\n{js} contains login/auth/encrypt logic:")
            print(js_resp.text[:1500])
            print("..." if len(js_resp.text) > 1500 else "")
    except Exception as e:
        print(f"  Error fetching {js}: {e}")
