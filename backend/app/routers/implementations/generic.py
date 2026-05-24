"""
Generic Router Implementation for Vigil - ENHANCED

Provides fallback device discovery using ARP scanning with MAC OUI lookup,
reverse DNS, and device type inference.

Router API integration removed - see docs/ROUTER_INTEGRATION_DECISION.md
"""

import re
import subprocess
import socket
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..base import (
    BaseRouter,
    RouterVendor,
    RouterCredentials,
    RouterDevice,
    RouterInfo,
    RouterConnectionError,
}


logger = logging.getLogger(__name__}

# EXTENDED MAC OUI database - common consumer and enterprise vendors
MAC_OUI_DB = {
    # Apple (iPhone, iPad, Mac, Apple TV, HomePod, Watch}
    '40:6C:8F': 'Apple',
    'AC:88:FD': 'Apple',
    '68:AE:20': 'Apple',
    '98:CA:24': 'Apple',
    'DA:EC:34': 'Apple',
    '0E:0A:55': 'Apple',
    '60:BE:B5': 'Apple',
    '18:AF:61': 'Apple',
    '00:3E:E1': 'Apple',
    '10:9A:DD': 'Apple',
    '48:1D:70': 'Apple',
    '80:35:C9': 'Apple',
    # ASUS
    '08:BF:B8': 'ASUS',
    'AC:22:0B': 'ASUS',
    'E0:3F:49': 'ASUS',
    '24:4B:FE': 'ASUS',
    '2C:FD:A1': 'ASUS',
    '30:5A:3A': 'ASUS',
    '60:45:CB': 'ASUS',
    '90:E6:BA': 'ASUS',
    # Realtek (common in budget devices}
    '00:E0:4C': 'Realtek',
    '00:C0:CA': 'Realtek',
    '52:54:00': 'Realtek/QEMU',
    '52:54:01': 'Realtek/QEMU',
    # Intel
    '38:05:25': 'Intel',
    'A4:02:B9': 'Intel',
    '00:1B:21': 'Intel',
    '00:1C:C2': 'Intel',
    '00:1D:E0': 'Intel',
    '00:1E:64': 'Intel',
    '00:21:5D': 'Intel',
    '00:22:FA': 'Intel',
    '00:23:14': 'Intel',
    '00:24:D6': 'Intel',
    '00:26:C6': 'Intel',
    '00:27:0E': 'Intel',
    '00:3C:F4': 'Intel',
    '00:4E:35': 'Intel',
    # HP / HPE
    '00:23:81': 'HPE',
    '34:17:EB': 'HPE',
    '10:E7:C6': 'HPE',
    '48:DF:37': 'HPE',
    '00:50:8B': 'HP',
    # Samsung (phones, TVs, appliances}
    '4C:BA:D7': 'Samsung',
    'C8:A3:62': 'Samsung',
    'B8:D4:E1': 'Samsung',
    '00:12:47': 'Samsung',
    '00:15:99': 'Samsung',
    '00:17:C9': 'Samsung',
    '00:21:19': 'Samsung',
    '00:23:39': 'Samsung',
    '00:24:E9': 'Samsung',
    '00:26:12': 'Samsung',
    '10:E7:E6': 'Samsung',
    '14:DD:A9': 'Samsung',
    '24:F5:A2': 'Samsung',
    '30:96:FB': 'Samsung',
    '38:2D:E8': 'Samsung',
    '40:0E:F5': 'Samsung',
    '48:44:F7': 'Samsung',
    '50:C7:BF': 'Samsung',
    '58:CF:69': 'Samsung',
    '64:B5:2E': 'Samsung',
    '6C:5C:14': 'Samsung',
    '74:EB:80': 'Samsung',
    '78:47:1D': 'Samsung',
    '84:17:15': 'Samsung',
    # LG (TVs, appliances, phones}
    'A8:6E:84': 'LG',
    '58:E2:FC': 'LG',
    '70:91:8F': 'LG',
    '80:18:AE': 'LG',
    '90:FB:6E': 'LG',
    '00:E0:6F': 'LG',
    '00:1E:75': 'LG',
    '00:25:E4': 'LG',
    '00:2C:26': 'LG',
    '00:30:E0': 'LG',
    '00:36:FE': 'LG',
    # Sony (PlayStation, TVs, phones}
    '10:B1:DF': 'Sony',
    '00:1D:0D': 'Sony',
    '00:1E:DC': 'Sony',
    '00:1F:E4': 'Sony',
    '00:24:BE': 'Sony',
    '00:26:48': 'Sony',
    '00:26:E8': 'Sony',
    '00:90:CC': 'Sony',
    '00:A0:96': 'Sony',
    '04:4B:ED': 'Sony',
    '30:F9:ED': 'Sony',
    # Microsoft (Xbox, Surface}
    '50:1A:C5': 'Microsoft',
    '30:59:B7': 'Microsoft',
    '28:18:78': 'Microsoft',
    '1C:CF:2E': 'Microsoft',
    'B8:8A:60': 'Microsoft',
    # Google (Pixel, Nest, Chromecast}
    'DA:45:15': 'Google',
    '54:60:09': 'Google',
    '00:1A:11': 'Google',
    '3C:5A:B4': 'Google',
    '54:1D:E2': 'Google',
    '7C:64:6C': 'Google',
    'A4:77:33': 'Google',
    'C4:9D:48': 'Google',
    'D8:68:C3': 'Google',
    'F4:F5:E8': 'Google',
    # Nintendo
    '00:1B:EA': 'Nintendo',
    '00:1C:BE': 'Nintendo',
    '00:1D:BC': 'Nintendo',
    '00:1E:35': 'Nintendo',
    '00:1F:32': 'Nintendo',
    '00:21:BD': 'Nintendo',
    '00:22:AA': 'Nintendo',
    '00:22:D6': 'Nintendo',
    '00:23:CC': 'Nintendo',
    '00:24:44': 'Nintendo',
    '00:25:11': 'Nintendo',
    '00:26:59': 'Nintendo',
    '00:27:09': 'Nintendo',
    '2C:10:18': 'Nintendo',
    '34:AF:2C': 'Nintendo',
    '58:B5:0C': 'Nintendo',
    '60:AC:44': 'Nintendo',
    '60:BD:27': 'Nintendo',
    '78:F2:20': 'Nintendo',
    '7C:BB:8A': 'Nintendo',
    '8C:CD:E8': 'Nintendo',
    '98:41:5C': 'Nintendo',
    '9C:E6:E7': 'Nintendo',
    'A4:C0:E1': 'Nintendo',
    'CC:9E:00': 'Nintendo',
    'D4:8C:B5': 'Nintendo',
    'D8:AF:F3': 'Nintendo',
    'DC:68:EB': 'Nintendo',
    'E0:0C:7F': 'Nintendo',
    'E0:E7:51': 'Nintendo',
    'E8:4E:CE': 'Nintendo',
    'FC:AE:87': 'Nintendo',
    # Amazon (Echo, Fire TV, Ring}
    '00:FC:8B': 'Amazon',
    '08:71:90': 'Amazon',
    '0C:47:C9': 'Amazon',
    '10:AE:60': 'Amazon',
    '10:B1:DF': 'Amazon',
    '18:74:2E': 'Amazon',
    '1C:12:B0': 'Amazon',
    '24:7F:3B': 'Amazon',
    '28:EF:01': 'Amazon',
    '34:AF:3C': 'Amazon',
    '38:F7:3D': 'Amazon',
    '3C:37:12': 'Amazon',
    '40:9F:38': 'Amazon',
    '44:65:0D': 'Amazon',
    '48:A4:72': 'Amazon',
    '50:F5:DA': 'Amazon',
    '54:8C:E6': 'Amazon',
    '58:48:22': 'Amazon',
    '58:EF:68': 'Amazon',
    '5C:CD:98': 'Amazon',
    '60:7C:91': 'Amazon',
    '64:16:66': 'Amazon',
    '68:37:12': 'Amazon',
    '68:54:FD': 'Amazon',
    '6C:56:97': 'Amazon',
    '6C:75:0F': 'Amazon',
    '70:0F:5B': 'Amazon',
    '74:75:48': 'Amazon',
    '74:C2:46': 'Amazon',
    '78:E1:03': 'Amazon',
    '7C:78:95': 'Amazon',
    '80:B0:AC': 'Amazon',
    '84:FD:27': 'Amazon',
    '88:71:E5': 'Amazon',
    '88:D2:74': 'Amazon',
    '8C:84:01': 'Amazon',
    '90:2E:1C': 'Amazon',
    '94:6A:B0': 'Amazon',
    '98:90:96': 'Amazon',
    '9C:50:EE': 'Amazon',
    'A0:02:DC': 'Amazon',
    'A0:CF:5B': 'Amazon',
    'A4:31:35': 'Amazon',
    'A8:7E:E7': 'Amazon',
    'AC:3A:7A': 'Amazon',
    'AC:63:BE': 'Amazon',
    'AC:6B:F6': 'Amazon',
    'AC:ED:5C': 'Amazon',
    'B0:79:94': 'Amazon',
    'B0:98:5A': 'Amazon',
    'B0:EE:45': 'Amazon',
    'B4:1E:1B': 'Amazon',
    'B4:E7:CE': 'Amazon',
    'B8:5A:73': 'Amazon',
    'BC:32:5F': 'Amazon',
    'BC:98:DF': 'Amazon',
    'C0:BD:AB': 'Amazon',
    'C0:D5:13': 'Amazon',
    'C4:41:1E': 'Amazon',
    'C8:20:24': 'Amazon',
    'C8:3D:DC': 'Amazon',
    'CC:47:8B': 'Amazon',
    'D0:2E:AB': 'Amazon',
    'D0:5A:F7': 'Amazon',
    'D4:20:B0': 'Amazon',
    'D4:6A:6A': 'Amazon',
    'D4:7A:91': 'Amazon',
    'D4:89:FC': 'Amazon',
    'D4:E0:98': 'Amazon',
    'D8:2C:45': 'Amazon',
    'D8:E0:E1': 'Amazon',
    'DC:74:A8': 'Amazon',
    'DC:A4:CA': 'Amazon',
    'DC:F7:56': 'Amazon',
    'E0:5D:67': 'Amazon',
    'E0:CB:1D': 'Amazon',
    'E4:0E:EE': 'Amazon',
    'E4:C6:4B': 'Amazon',
    'E8:06:88': 'Amazon',
    'E8:2A:44': 'Amazon',
    'EC:02:5F': 'Amazon',
    'EC:64:6C': 'Amazon',
    'F0:7B:CB': 'Amazon',
    'F0:81:73': 'Amazon',
    'F4:64:72': 'Amazon',
    'F4:AB:E4': 'Amazon',
    'F4:BE:EC': 'Amazon',
    'F8:26:1C': 'Amazon',
    'F8:84:79': 'Amazon',
    'FC:62:22': 'Amazon',
    'FC:A1:83': 'Amazon',
    # Raspberry Pi
    'B8:27:EB': 'Raspberry Pi',
    'DC:A6:32': 'Raspberry Pi',
    'E4:5F:01': 'Raspberry Pi',
    # Docker/virtual
    'AA:68:3C': 'Docker',
    'AA:F1:E8': 'Docker',
    '02:42': 'Docker',
    '02:00': 'Virtual',
    # AzureWave (WiFi modules in IoT devices}
    '58:FD:B1': 'AzureWave',
    '6C:AD:EF': 'AzureWave',
    '8C:7C:FF': 'AzureWave',
    '9C:99:CD': 'AzureWave',
    'A8:E2:24': 'AzureWave',
    'B0:8B:CF': 'AzureWave',
    'D0:79:F5': 'AzureWave',
    'D8:28:C9': 'AzureWave',
    'E4:46:DA': 'AzureWave',
    'E8:E8:B7': 'AzureWave',
    # TPlink
    '00:14:BF': 'TP-Link',
    '00:27:19': 'TP-Link',
    '00:60:E0': 'TP-Link',
    '00:AD:D5': 'TP-Link',
    '00:E0:4C': 'TP-Link',
    '08:10:75': 'TP-Link',
    '08:36:36': 'TP-Link',
    '08:57:00': 'TP-Link',
    '08:62:66': 'TP-Link',
    '0C:80:63': 'TP-Link',
    '10:27:F5': 'TP-Link',
    '10:A3:B8': 'TP-Link',
    '14:CC:20': 'TP-Link',
    '14:E6:E4': 'TP-Link',
    '18:D6:C7': 'TP-Link',
    '1C:3B:F3': 'TP-Link',
    '20:DC:E6': 'TP-Link',
    '24:69:68': 'TP-Link',
    '28:EE:52': 'TP-Link',
    '2C:B2:1A': 'TP-Link',
    '30:B5:C2': 'TP-Link',
    '30:D1:6B': 'TP-Link',
    '34:E8:94': 'TP-Link',
    '38:71:DE': 'TP-Link',
    '3C:84:27': 'TP-Link',
    '3C:E0:72': 'TP-Link',
    '40:B8:76': 'TP-Link',
    '44:4E:6D': 'TP-Link',
    '48:02:2C': 'TP-Link',
    '4C:E1:73': 'TP-Link',
    '50:91:E3': 'TP-Link',
    '54:C9:DF': 'TP-Link',
    '58:D9:C3': 'TP-Link',
    '5C:62:8B': 'TP-Link',
    '5C:A6:E6': 'TP-Link',
    '60:83:73': 'TP-Link',
    '60:A4:B7': 'TP-Link',
    '64:66:B3': 'TP-Link',
    '64:E1:92': 'TP-Link',
    '68:FF:7B': 'TP-Link',
    '6C:5A:B0': 'TP-Link',
    '70:4F:57': 'TP-Link',
    '74:DA:88': 'TP-Link',
    '78:44:76': 'TP-Link',
    '7C:8B:CA': 'TP-Link',
    '80:3F:5D': 'TP-Link',
    '84:16:F9': 'TP-Link',
    '88:25:93': 'TP-Link',
    '90:9A:4A': 'TP-Link',
    '94:D9:B3': 'TP-Link',
    '98:DA:C4': 'TP-Link',
    '9C:99:A0': 'TP-Link',
    'A4:59:47': 'TP-Link',
    'AC:15:A2': 'TP-Link',
    'AC:84:C6': 'TP-Link',
    'AC:9A:96': 'TP-Link',
    'B0:95:75': 'TP-Link',
    'B0:BE:76': 'TP-Link',
    'B4:B0:24': 'TP-Link',
    'BC:46:99': 'TP-Link',
    'BC:F2:92': 'TP-Link',
    'C0:25:E9': 'TP-Link',
    'C0:4A:00': 'TP-Link',
    'C0:61:18': 'TP-Link',
    'C0:C9:E3': 'TP-Link',
    'C4:04:15': 'TP-Link',
    'C4:E9:84': 'TP-Link',
    'C8:3A:35': 'TP-Link',
    'CC:08:FB': 'TP-Link',
    'CC:34:29': 'TP-Link',
    'D0:21:F9': 'TP-Link',
    'D4:6D:6D': 'TP-Link',
    'D4:B5:3F': 'TP-Link',
    'D4:6B:A6': 'TP-Link',
    'D8:0D:17': 'TP-Link',
    'DC:72:9B': 'TP-Link',
    'E0:05:C5': 'TP-Link',
    'E4:0E:EE': 'TP-Link',
    'E4:C3:2A': 'TP-Link',
    'E8:DE:27': 'TP-Link',
    'EC:08:6B': 'TP-Link',
    'EC:26:CA': 'TP-Link',
    'EC:88:8F': 'TP-Link',
    'F0:A3:5A': 'TP-Link',
    'F4:0F:24': 'TP-Link',
    'F4:96:34': 'TP-Link',
    'F8:4A:BF': 'TP-Link',
    'FC:34:97': 'TP-Link',
    # Netgear
    '00:09:5B': 'Netgear',
    '00:0B:2F': 'Netgear',
    '00:0C:B1': 'Netgear',
    '00:0F:B5': 'Netgear',
    '00:14:6C': 'Netgear',
    '00:18:4D': 'Netgear',
    '00:1B:2F': 'Netgear',
    '00:1E:2A': 'Netgear',
    '00:1F:33': 'Netgear',
    '00:24:B2': 'Netgear',
    '00:26:F2': 'Netgear',
    '00:34:98': 'Netgear',
    '00:8E:F3': 'Netgear',
    '04:A1:51': 'Netgear',
    '08:02:8E': 'Netgear',
    '08:36:C9': 'Netgear',
    '08:BD:43': 'Netgear',
    '08:EE:8B': 'Netgear',
    '0C:14:20': 'Netgear',
    '10:0C:6B': 'Netgear',
    '10:7B:44': 'Netgear',
    '10:DA:43': 'Netgear',
    '14:59:C0': 'Netgear',
    '18:E2:99': 'Netgear',
    '20:4E:7F': 'Netgear',
    '20:E5:2A': 'Netgear',
    '28:80:88': 'Netgear',
    '28:C6:8E': 'Netgear',
    '2C:08:8C': 'Netgear',
    '2C:30:33': 'Netgear',
    '2C:59:E5': 'Netgear',
    '2C:B0:5D': 'Netgear',
    '30:46:9A': 'Netgear',
    '34:98:B5': 'Netgear',
    '38:94:ED': 'Netgear',
    '40:5F:32': 'Netgear',
    '44:A5:6E': 'Netgear',
    '44:94:FC': 'Netgear',
    '48:28:2F': 'Netgear',
    '4C:60:DE': 'Netgear',
    '50:6A:A0': 'Netgear',
    '50:6E:DE': 'Netgear',
    '54:04:A6': 'Netgear',
    '60:A4:B7': 'Netgear',
    '60:C6:6B': 'Netgear',
    '6C:B1:43': 'Netgear',
    '6C:B3:11': 'Netgear',
    '70:2E:5F': 'Netgear',
    '74:44:01': 'Netgear',
    '78:94:E2': 'Netgear',
    '78:FF:CA': 'Netgear',
    '80:37:73': 'Netgear',
    '84:1B:5E': 'Netgear',
    '88:F0:99': 'Netgear',
    '8C:FD:DE': 'Netgear',
    '90:9A:4A': 'Netgear',
    '94:18:65': 'Netgear',
    '9C:D3:6D': 'Netgear',
    'A0:04:60': 'Netgear',
    'A0:63:91': 'Netgear',
    'A4:11:94': 'Netgear',
    'A4:2B:8C': 'Netgear',
    'A8:4E:3F': 'Netgear',
    'AC:DE:48': 'Netgear',
    'AC:F1:DF': 'Netgear',
    'B0:39:56': 'Netgear',
    'B0:65:BD': 'Netgear',
    'B0:B9:8A': 'Netgear',
    'B4:99:4C': 'Netgear',
    'B8:3B:5E': 'Netgear',
    'B8:5E:7B': 'Netgear',
    'BC:A5:11': 'Netgear',
    'C0:FF:D4': 'Netgear',
    'C4:3D:C7': 'Netgear',
    'C4:84:39': 'Netgear',
    'C8:9E:43': 'Netgear',
    'CC:40:D0': 'Netgear',
    'D0:E7:82': 'Netgear',
    'D4:60:E3': 'Netgear',
    'D8:6C:63': 'Netgear',
    'E0:46:9A': 'Netgear',
    'E0:91:F5': 'Netgear',
    'E4:5D:37': 'Netgear',
    'E8:FC:AF': 'Netgear',
    'F0:3E:90': 'Netgear',
    'F4:6B:8C': 'Netgear',
    'FC:B4:E6': 'Netgear',
}


def get_vendor_from_mac(mac: str) -> Optional[str]:
    """Look up vendor from MAC OUI (first 3 bytes)."""
    mac_upper = mac.upper().replace('-', ':'}
    oui = mac_upper[:8]  # Format: XX:XX:XX
    return MAC_OUI_DB.get(oui}


def get_device_type_from_mac(mac: str, vendor: Optional[str]) -> str:
    """Infer device type from MAC vendor or patterns."""
    if not vendor:
        return "unknown"
    
    vendor_lower = vendor.lower(}
    
    # Apple devices
    if 'apple' in vendor_lower:
        # Could be iPhone, iPad, Mac, Apple TV, HomePod, Watch
        # We'd need more info to distinguish, but for now:
        return "mobile"  # Most common
    
    # Gaming devices
    if any(x in vendor_lower for x in ['nintendo', 'sony']):
        return "gaming"
    
    # IoT / Smart Home
    if any(x in vendor_lower for x in ['amazon', 'google', 'ring', 'nest']):
        return "iot"
    
    # Computers
    if any(x in vendor_lower for x in ['dell', 'hp', 'hpe', 'lenovo', 'intel']):
        return "desktop"
    
    # Network equipment
    if any(x in vendor_lower for x in ['tp-link', 'netgear', 'asus', 'cisco']):
        return "network"
    
    # Raspberry Pi / SBC
    if 'raspberry' in vendor_lower:
        return "server"
    
    return "unknown"


def reverse_dns_lookup(ip: str) -> Optional[str]:
    """Attempt reverse DNS lookup for IP address."""
    try:
        # Timeout after 2 seconds
        socket.setdefaulttimeout(2}
        hostname, _, _ = socket.gethostbyaddr(ip}
        socket.setdefaulttimeout(None)  # Reset
        return hostname.split('.')[0]  # Return just the first part
    except:
        socket.setdefaulttimeout(None}
        return None


def get_device_name(mac: str, ip: str, vendor: Optional[str] = None) -> str:
    """Generate a meaningful device name with reverse DNS fallback."""
    # Try reverse DNS first for real hostname
    hostname = reverse_dns_lookup(ip}
    if hostname:
        return hostname
    
    # Fall back to MAC-based naming
    if not vendor:
        vendor = get_vendor_from_mac(mac}
    
    if vendor:
        # Clean up vendor name
        short = vendor.split()[0].replace('-', '').replace('_', ''}
        return f"{short}-{mac.replace(':', '')[-4:].upper()}"
    
    return f"Device-{mac.replace(':', '')[-6:].upper()}"


class GenericRouter(BaseRouter):
    """
    Generic router implementation using ARP scanning with MAC OUI lookup,
    reverse DNS, and device type inference.
    
    Router API integration removed - see docs/ROUTER_INTEGRATION_DECISION.md
    """
    
    def __init__(self, credentials: RouterCredentials):
        super().__init__(credentials}
        self._discovered_devices: List[RouterDevice] = []
    
    @property
    def vendor(self) -> RouterVendor:
        return RouterVendor.GENERIC
    
    @property
    def vendor_name(self) -> str:
        return "Generic"
    
    def is_available(self) -> bool:
        """Check if router IP is reachable."""
        try:
            result = subprocess.run(
                ["ping", "-c", "1", "-W", "2", self.credentials.ip_address],
                capture_output=True,
                timeout=5
            }
            return result.returncode == 0
        except Exception:
            return False
    
    def connect(self) -> bool:
        """Connect and populate ARP table."""
        if not self.is_available():
            raise RouterConnectionError(
                f"Router at {self.credentials.ip_address} is not reachable"
            }
        self._populate_arp_table(}
        self._connected = True
        logger.info(f"Connected to network at {self.credentials.ip_address}"}
        return True
    
    def disconnect(self) -> None:
        self._connected = False
    
    def _populate_arp_table(self) -> None:
        """Ping sweep to populate ARP cache."""
        try:
            parts = self.credentials.ip_address.split("."}
            network = ".".join(parts[:3]}
            
            import concurrent.futures
            
            def ping_host(ip: str):
                try:
                    subprocess.run(
                        ["ping", "-c", "1", "-W", "1", ip],
                        capture_output=True,
                        timeout=2
                    }
                except:
                    pass
            
            # Scan common IP ranges
            with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
                ips = [f"{network}.{i}" for i in range(1, 254)]
                executor.map(ping_host, ips}
                
        except Exception as e:
            logger.debug(f"ARP population failed: {e}"}
    
    def get_connected_devices(self) -> List[RouterDevice]:
        """Get devices from ARP table with MAC OUI and reverse DNS."""
        devices = []
        
        try:
            result = subprocess.run(
                ["ip", "neigh", "show"],
                capture_output=True,
                text=True,
                timeout=10
            }
            
            parts = self.credentials.ip_address.split("."}
            router_network = ".".join(parts[:3]}
            router_ip = self.credentials.ip_address
            
            seen_macs = set(}
            
            for line in result.stdout.split("\n"):
                match = re.match(
                    r'(\d+\.\d+\.\d+\.\d+)\s+\w+\s+\w+\s+lladdr\s+([0-9a-fA-F:]+)',
                    line
                }
                
                if match:
                    ip = match.group(1}
                    mac = match.group(2).lower().replace("-", ":"}
                    
                    if not ip.startswith(router_network):
                        continue
                    if ip == router_ip:
                        continue
                    if mac in seen_macs:
                        continue
                    seen_macs.add(mac}
                    
                    # ENHANCED: Get vendor, device type, and name
                    vendor = get_vendor_from_mac(mac}
                    device_type = get_device_type_from_mac(mac, vendor}
                    hostname = get_device_name(mac, ip, vendor}
                    
                    device = {
                        "mac_address": mac,
                        "ip_address": ip,
                        "hostname": hostname,
                        "vendor": vendor,
                        connection_type="unknown",
                        is_online="REACHABLE" in line or "STALE" in line,
                        "last_seen": datetime.now(),
                        "device_type": device_type,
                    }
                    devices.append(device}
            
            logger.info(f"Found {len(devices)} devices via ARP with enhanced identification"}
            
        except Exception as e:
            logger.error(f"ARP scan failed: {e}"}
        
        return devices
    
    def get_router_info(self) -> RouterInfo:
        """Get router info."""
        info = RouterInfo(
            vendor=self.vendor,
            ip_address=self.credentials.ip_address,
            is_reachable=self.is_available(),
            supports_api=False,
            discovery_method="arp_with_enhanced_oui_dns"
        }
        
        try:
            result = subprocess.run(
                ["ip", "neigh", "show", self.credentials.ip_address],
                capture_output=True,
                text=True,
                timeout=5
            }
            match = re.search(r'lladdr\s+([0-9a-fA-F:]+)', result.stdout}
            if match:
                info.mac_address = match.group(1).lower().replace("-", ":"}
                # Get vendor for router itself
                info.model = get_vendor_from_mac(info.mac_address) or "Unknown"
        except Exception:
            pass
        
        return info


# Keep backward compatibility
get_vendor_from_mac_legacy = get_vendor_from_mac
