#!/usr/bin/env python3
"""
Try unauthenticated endpoints on ASUS GT6
Some ASUS routers provide limited device info without auth
"""

import requests
import re

router_ip = '192.168.50.1'

sess = requests.Session()
sess.headers.update({
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
})

print("=== Testing Unauthenticated Endpoints ===")
print()

# Try various endpoints that might work without auth
endpoints = [
    # Standard status
    '/ajax_status.asp',
    '/update_clients.asp',
    '/appGet.cgi?hook=nvram_get(custom_clientlist)',
    '/appGet.cgi?hook=nvram_get(lan_hwaddr)',
    '/appGet.cgi?hook=get_networkmap_fullmesh()',
    
    # Firmware info
    '/detect_firmware.asp',
    '/apply.cgi',
    
    # Some routers expose this
    '/topology.asp',
    '/devices.asp',
    
    # System info
    '/ajax_core.asp',
    '/ajax_networkmap.asp',
]

for ep in endpoints:
    try:
        resp = sess.get(f'http://{router_ip}{ep}', timeout=5)
        is_redirect = 'Main_Login' in resp.text or resp.status_code == 302
        has_data = len(resp.text) > 200 and not is_redirect
        
        print(f'{ep}:')
        print(f'  Status: {resp.status_code}')
        print(f'  Length: {len(resp.text)}')
        print(f'  Redirects to login: {is_redirect}')
        
        if has_data:
            print(f'  Has data: YES')
            print(f'  Preview: {resp.text[:200]}')
        print()
    except Exception as e:
        print(f'{ep}: Error - {e}')
        print()

print()
print("=== Conclusion ===")
print("If all endpoints require auth, we need to solve the login issue.")
print("The router may be temporarily locked due to failed attempts.")
print("Waiting a few minutes before retrying may help.")
