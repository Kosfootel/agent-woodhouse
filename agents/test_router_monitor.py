#!/usr/bin/env python3
"""
Quick test script for router monitor
Usage: python3 test_router_monitor.py [username] [password]
"""

import sys
import os
sys.path.insert(0, '/home/erik-ross/vigil')

from agents.router_monitor import ASUSRouterMonitor

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 test_router_monitor.py <username> <password>")
        print("\nOr set environment variables:")
        print("  export ROUTER_USER=admin")
        print("  export ROUTER_PASS=yourpassword")
        print("  python3 test_router_monitor.py")
        sys.exit(1)
    
    username = sys.argv[1] if len(sys.argv) > 1 else os.getenv('ROUTER_USER')
    password = sys.argv[2] if len(sys.argv) > 2 else os.getenv('ROUTER_PASS')
    
    if not username or not password:
        print("Error: Username and password required")
        sys.exit(1)
    
    print(f"Connecting to ASUS router at 192.168.50.1...")
    monitor = ASUSRouterMonitor()
    
    devices = monitor.run_once(username, password)
    
    if devices:
        print(f"\n✅ Found {len(devices)} devices:")
        for d in devices:
            rssi_info = f" (RSSI: {d.rssi}dBm)" if d.rssi else ""
            print(f"  📱 {d.hostname}")
            print(f"     MAC: {d.mac} | IP: {d.ip} | Type: {d.connection_type}{rssi_info}")
            print()
    else:
        print("\n⚠️ No devices found or authentication failed")
        print("\nTroubleshooting:")
        print("  1. Verify router IP is 192.168.50.1")
        print("  2. Check username/password")
        print("  3. Ensure router web interface is accessible")
        print("  4. Try accessing http://192.168.50.1 from browser")

if __name__ == '__main__':
    main()
