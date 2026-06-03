#!/usr/bin/env python3
import sys
sys.path.insert(0, 'app')
from routers.factory import get_connected_devices

print("Testing device discovery...")

try:
    devices = get_connected_devices(
        router_ip="192.168.50.1",
        username="admin",
        password="LuckyToby1!"
    )
    print(f"Found {len(devices)} devices:")
    for d in devices[:5]:
        print(f"  - {d['hostname']}: {d['ip_address']} ({d['mac_address']})")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
