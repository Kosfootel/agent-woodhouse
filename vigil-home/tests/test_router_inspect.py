#!/usr/bin/env python3
"""Inspect ASUS GT6 router login mechanism"""
import requests
import re

router_ip = '192.168.50.1'

session = requests.Session()

# First, let's see what the login page looks like
print("=== Fetching login page ===")
login_page = session.get(f"http://{router_ip}/Main_Login.asp", timeout=10)
print(f"Status: {login_page.status_code}")
print(f"Length: {len(login_page.text)}")
print(f"\nFirst 2000 chars of login page:")
print(login_page.text[:2000])

# Look for form fields, CSRF tokens, JavaScript
print("\n=== Looking for tokens/patterns ===")
patterns = [
    r'name=["\']token["\'][^>]*value=["\']([^"\']+)',
    r'csrf_token["\']?\s*[:=]\s*["\']([^"\']+)',
    r'asus_token["\']?\s*[:=]\s*["\']([^"\']+)',
    r'login_username',
    r'login_passwd',
]
for pattern in patterns:
    match = re.search(pattern, login_page.text, re.IGNORECASE)
    if match:
        print(f"Found: {pattern[:30]}... -> {match.group(0)[:100]}")

# Check cookies
print(f"\nCookies from login page: {dict(session.cookies)}")

# Try to find the actual form submission
print("\n=== Form analysis ===")
form_match = re.search(r'<form[^>]*login[^>]*>.*?</form>', login_page.text, re.DOTALL | re.IGNORECASE)
if form_match:
    print(f"Found form: {form_match.group(0)[:500]}")
else:
    print("No form found with 'login'")

# Look for JavaScript login functions
print("\n=== JavaScript login functions ===")
js_patterns = [
    r'function\s+login\s*\([^)]*\)\s*\{[^}]+\}',
    r'login\s*[:=]\s*function\s*\([^)]*\)\s*\{[^}]+\}',
]
for pattern in js_patterns:
    matches = re.findall(pattern, login_page.text, re.DOTALL)
    for m in matches[:2]:
        print(f"Found login function: {m[:300]}...")
