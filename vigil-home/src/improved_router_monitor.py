"""
Improved router device discovery with MAC vendor lookup and hostname resolution.
"""
import subprocess
import re
import sqlite3
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

# MAC OUI database (top vendors - expanded list)
MAC_OUI_DB = {
    '00:E0:4C': 'Realtek Semiconductor',
    '38:05:25': 'Intel Corporate',
    '40:6C:8F': 'Apple Inc',
    '08:BF:B8': 'ASUSTeK Computer Inc',
    '00:23:81': 'Hewlett Packard',
    '58:FD:B1': 'AzureWave Technologies',
    'A8:6E:84': 'LG Electronics',
    '10:B1:DF': 'Sony Corporation',
    '4C:BA:D7': 'Samsung Electronics',
    'C8:A3:62': 'Samsung Electronics',
    'DA:EC:34': 'Apple Inc',
    '0E:0A:55': 'Apple Inc',
    'DA:45:15': 'Google Inc',
    '0E:EC:BE': 'Microsoft Corporation',
    'AA:68:3C': 'Docker Inc',
    'AA:F1:E8': 'Docker Inc',
}

@dataclass
class DiscoveredDevice:
    mac: str
    ip: str
    hostname: Optional[str] = None
    vendor: Optional[str] = None
    connection_type: str = "unknown"


def get_mac_vendor(mac: str) -> Optional[str]:
    """Look up vendor from MAC OUI."""
    # Normalize MAC
    mac_upper = mac.upper().replace('-', ':').replace('.', ':')
    oui = mac_upper[:8]
    return MAC_OUI_DB.get(oui)


def resolve_hostname(ip: str) -> Optional[str]:
    """Try to resolve hostname via reverse DNS."""
    try:
        result = subprocess.run(
            ['nslookup', ip],
            capture_output=True,
            text=True,
            timeout=2
        )
        # Parse nslookup output for name
        for line in result.stdout.split('\n'):
            if 'name =' in line:
                return line.split('name =')[1].strip().rstrip('.')
    except:
        pass
    return None


def get_arp_devices() -> List[DiscoveredDevice]:
    """Get devices from ARP table with improved metadata."""
    devices = []
    
    try:
        result = subprocess.run(
            ['ip', 'neigh', 'show'],
            capture_output=True,
            text=True
        )
        
        for line in result.stdout.split('\n'):
            # Parse: 192.168.50.24 dev eth0 lladdr 00:e0:4c:be:fa:cc REACHABLE
            match = re.match(r'^(\d+\.\d+\.\d+\.\d+)\s+.*lladdr\s+([0-9a-f:]+)\s+.*REACHABLE',
                            line.lower())
            if match:
                ip = match.group(1)
                mac = match.group(2)
                
                # Skip localhost and multicast
                if ip.startswith('127.') or mac.startswith('01:00:5e') or mac.startswith('33:33'):
                    continue
                
                # Look up vendor
                vendor = get_mac_vendor(mac)
                
                # Try to resolve hostname
                hostname = resolve_hostname(ip)
                
                devices.append(DiscoveredDevice(
                    mac=mac.upper(),
                    ip=ip,
                    hostname=hostname,
                    vendor=vendor,
                    connection_type='ethernet'
                ))
    except Exception as e:
        print(f"ARP scan error: {e}")
    
    return devices


def scan_network_subnet(subnet: str = "192.168.50") -> List[DiscoveredDevice]:
    """Scan network subnet for active hosts."""
    devices = []
    
    # Quick ping sweep to populate ARP table
    try:
        # Use fping for faster scanning
        subprocess.run(
            ['fping', '-a', '-g', f'{subnet}.0/24'],
            capture_output=True,
            timeout=30
        )
    except FileNotFoundError:
        # Fallback: ping common addresses
        for i in range(1, 255):
            subprocess.run(
                ['ping', '-c', '1', '-W', '0.1', f'{subnet}.{i}'],
                capture_output=True
            )
    except:
        pass
    
    # Get ARP entries after scan
    return get_arp_devices()


class ImprovedRouterMonitor:
    """Router monitor with ARP fallback and MAC vendor lookup."""
    
    def __init__(self, router_ip: str, username: str = None, password: str = None):
        self.router_ip = router_ip
        self.username = username
        self.password = password
        self.devices = []
    
    def get_devices(self) -> List[Dict]:
        """Get devices with improved metadata."""
        # Try router API first
        # ... (router-specific code would go here)
        
        # Fall back to ARP scan
        devices = scan_network_subnet()
        
        return [
            {
                'mac': d.mac,
                'ip': d.ip,
                'hostname': d.hostname or d.vendor or 'Unknown Device',
                'vendor': d.vendor,
                'connection_type': d.connection_type
            }
            for d in devices
        ]


if __name__ == '__main__':
    monitor = ImprovedRouterMonitor('192.168.50.1')
    devices = monitor.get_devices()
    
    print(f"Found {len(devices)} devices:\n")
    for d in devices:
        print(f"MAC: {d['mac']}")
        print(f"IP: {d['ip']}")
        print(f"Hostname: {d['hostname']}")
        print(f"Vendor: {d['vendor']}")
        print(f"Type: {d['connection_type']}")
        print()
