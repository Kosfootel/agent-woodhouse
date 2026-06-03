#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/erik-ross/vigil/backend/app')
from router_monitor import ASUSRouterClient
import logging

logging.basicConfig(level=logging.DEBUG)

try:
    client = ASUSRouterClient('192.168.50.1', 'admin', 'LuckyToby1!')
    print('Attempting login...')
    client.login()
    print(f'Login successful, token: {client._token}')
    
    # Try appGet.cgi
    print('Fetching client list...')
    response = client._make_request("/appGet.cgi", params={
        "hook": "nvram_get(custom_clientlist)"
    })
    print(f'Response status: {response.status_code}')
    print(f'Response text (first 500 chars):')
    print(response.text[:500])
    
    # Try alternative approach
    print('\n--- Trying networkmap ---')
    response2 = client._make_request("/appGet.cgi", params={
        "hook": "get_networkmap_fullmesh()"
    })
    print(f'Networkmap status: {response2.status_code}')
    print(f'Networkmap text (first 500 chars):')
    print(response2.text[:500])
    
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
