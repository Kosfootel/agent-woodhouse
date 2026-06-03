"""
Generic Router Implementation for Vigil - IMPROVED

Provides fallback device discovery using ARP scanning with MAC OUI lookup.
"""

import re
import subprocess
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
)


logger = logging.getLogger(__name__)

# Extended MAC OUI database for common vendors
MAC_OUI_DB = {
    # Apple
    '40:6C:8F': 'Apple Inc.',
    'AC:88:FD': 'Apple Inc.',
    '68:AE:20': 'Apple Inc.',
    '98:CA:24': 'Apple Inc.',
    'DA:EC:34': 'Apple Inc.',
    '0E:0A:55': 'Apple Inc.',
    # ASUS
    '08:BF:B8': 'ASUSTeK Computer Inc.',
    'AC:22:0B': 'ASUSTeK Computer Inc.',
    'E0:3F:49': 'ASUSTeK Computer Inc.',
    # Realtek
    '00:E0:4C': 'Realtek Semiconductor Corp.',
    # Intel
    '38:05:25': 'Intel Corporate',
    'A4:02:B9': 'Intel Corporate',
    # HP
    '00:23:81': 'Hewlett Packard Enterprise',
    # Samsung
    '4C:BA:D7': 'Samsung Electronics',
    'C8:A3:62': 'Samsung Electronics',
    # LG
    'A8:6E:84': 'LG Electronics',
    # Sony
    '10:B1:DF': 'Sony Corporation',
    # AzureWave
    '58:FD:B1': 'AzureWave Technologies',
    # Docker
    'AA:68:3C': 'Docker Container',
    'AA:F1:E8': 'Docker Container',
    # Microsoft
    '0E:EC:BE': 'Microsoft Corporation',
    # Google
    'DA:45:15': 'Google Inc.',
}


def get_vendor_from_mac(mac: str) -> Optional[str]:
    """Look up vendor from MAC OUI."""
    mac_upper = mac.upper().replace('-', ':')
    oui = mac_upper[:8]
    return MAC_OUI_DB.get(oui)


def get_device_name(mac: str, ip: str) -> str:
    """Generate a meaningful device name from MAC."""
    vendor = get_vendor_from_mac(mac)
    if vendor:
        # Extract short name from vendor
        short = vendor.split()[0]
        return f"{short}-{mac.replace(':', '')[-4:].upper()}"
    return f"Device-{mac.replace(':', '')[-6:].upper()}"


class GenericRouter(BaseRouter):
    """
    Generic router implementation using ARP scanning with MAC OUI lookup.
    """
    
    def __init__(self, credentials: RouterCredentials):
        super().__init__(credentials)
        self._discovered_devices: List[RouterDevice] = []
    
    @property
    def vendor(self) -> RouterVendor:
        return RouterVendor.GENERIC
    
    @property
    def vendor_name(self) -> str:
        return "Generic"
    
    def is_available(self) -> bool:
        try:
            result = subprocess.run(
                ["ping", "-c", "1", "-W", "2", self.credentials.ip_address],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def connect(self) -> bool:
        if not self.is_available():
            raise RouterConnectionError(
                f"Router at {self.credentials.ip_address} is not reachable"
            )
        self._populate_arp_table()
        self._connected = True
        logger.info(f"Connected to generic router at {self.credentials.ip_address}")
        return True
    
    def disconnect(self) -> None:
        self._connected = False
    
    def _populate_arp_table(self) -> None:
        try:
            parts = self.credentials.ip_address.split(".")
            network = ".".join(parts[:3])
            
            import concurrent.futures
            
            def ping_host(ip: str):
                try:
                    subprocess.run(
                        ["ping", "-c", "1", "-W", "1", ip],
                        capture_output=True,
                        timeout=2
                    )
                except:
                    pass
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
                ips = [f"{network}.{i}" for i in range(1, 51)]
                executor.map(ping_host, ips)
                
        except Exception as e:
            logger.debug(f"ARP population failed: {e}")
    
    def get_connected_devices(self) -> List[RouterDevice]:
        devices = []
        
        try:
            result = subprocess.run(
                ["ip", "neigh", "show"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            parts = self.credentials.ip_address.split(".")
            router_network = ".".join(parts[:3])
            router_ip = self.credentials.ip_address
            
            seen_macs = set()
            
            for line in result.stdout.split("\n"):
                match = re.match(
                    r'(\d+\.\d+\.\d+\.\d+)\s+\w+\s+\w+\s+lladdr\s+([0-9a-fA-F:]+)',
                    line
                )
                
                if match:
                    ip = match.group(1)
                    mac = match.group(2).lower().replace("-", ":")
                    
                    if not ip.startswith(router_network):
                        continue
                    if ip == router_ip:
                        continue
                    if mac in seen_macs:
                        continue
                    seen_macs.add(mac)
                    
                    # IMPROVED: Use MAC OUI lookup for device name
                    vendor = get_vendor_from_mac(mac)
                    hostname = get_device_name(mac, ip)
                    
                    device = RouterDevice(
                        mac_address=mac,
                        ip_address=ip,
                        hostname=hostname,
                        vendor=vendor,
                        connection_type="unknown",
                        is_online="REACHABLE" in line or "STALE" in line,
                        last_seen=datetime.now()
                    )
                    devices.append(device)
            
            logger.info(f"Found {len(devices)} devices via ARP")
            
        except Exception as e:
            logger.error(f"ARP scan failed: {e}")
        
        return devices
    
    def get_router_info(self) -> RouterInfo:
        info = RouterInfo(
            vendor=self.vendor,
            ip_address=self.credentials.ip_address,
            is_reachable=self.is_available(),
            supports_api=False,
            discovery_method="arp_fallback_with_oui"
        )
        
        try:
            result = subprocess.run(
                ["ip", "neigh", "show", self.credentials.ip_address],
                capture_output=True,
                text=True,
                timeout=5
            )
            match = re.search(r'lladdr\s+([0-9a-fA-F:]+)', result.stdout)
            if match:
                info.mac_address = match.group(1).lower().replace("-", ":")
        except Exception:
            pass
        
        return info


# Keep backward compatibility
def get_vendor_from_mac_legacy(mac_address: str) -> Optional[str]:
    """Legacy function for backward compatibility."""
    return get_vendor_from_mac(mac_address)
