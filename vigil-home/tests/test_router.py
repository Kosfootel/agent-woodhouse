#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/erik-ross/vigil/backend/app')
from router_monitor import get_connected_devices

try:
    devices = get_connected_devices('192.168.50.1', 'admin', 'LuckyToby1!')
    print(f'Found {len(devices)} devices')
    for d in devices[:5]:
        print(f"  - {d.get('hostname', 'unknown')}: {d.get('ip', 'N/A')}")
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
