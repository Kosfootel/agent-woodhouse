"""
Generic Router Implementation for Vigil

Provides fallback device discovery using ARP scanning, SNMP, and UPnP.
This implementation works with any router but provides limited information.
"""

import re
import subprocess
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

import requests

from ..base import (
    BaseRouter,
    RouterVendor,
    RouterCredentials,
    RouterDevice,
    RouterInfo,
    RouterConnectionError,
)


logger = logging.getLogger(__name__)


class GenericRouter(BaseRouter):
    """
    Generic router implementation using ARP scanning.
    
    This is a fallback implementation that works with any router by
    using the system's ARP table to discover devices. It doesn't require
    router authentication or API access.
    
    Limitations:
    - Limited device information (MAC, IP only)
    - No bandwidth stats
    - No router configuration access
    - May not detect all devices (some may be filtered)
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
        """
        Check if router IP is reachable.
        
        Does a simple ping check to see if router is online.
        """
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
        """
        "Connect" to generic router.
        
        For generic implementation, this just verifies the router
        is reachable and populates the ARP table.
        """
        if not self.is_available():
            raise RouterConnectionError(
                f"Router at {self.credentials.ip_address} is not reachable"
            )
        
        # Trigger ARP population by pinging the network
        self._populate_arp_table()
        
        self._connected = True
        logger.info(f"Connected to generic router at {self.credentials.ip_address}")
        return True
    
    def disconnect(self) -> None:
        """No-op for generic router."""
        self._connected = False
    
    def _populate_arp_table(self) -> None:
        """Populate ARP table by pinging network range."""
        try:
            # Extract network prefix
            parts = self.credentials.ip_address.split(".")
            network = ".".join(parts[:3])
            
            # Ping common addresses to populate ARP
            # Do this in parallel with short timeout
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
            
            # Ping first 50 IPs in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
                ips = [f"{network}.{i}" for i in range(1, 51)]
                executor.map(ping_host, ips)
                
        except Exception as e:
            logger.debug(f"ARP population failed: {e}")
    
    def get_connected_devices(self) -> List[RouterDevice]:
        """
        Get devices from ARP table.
        
        Parses the system's ARP table to find devices on the
        same network as the router.
        """
        devices = []
        
        try:
            # Get ARP entries
            result = subprocess.run(
                ["ip", "neigh", "show"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Extract network prefix from router IP
            parts = self.credentials.ip_address.split(".")
            router_network = ".".join(parts[:3])
            router_ip = self.credentials.ip_address
            
            seen_macs = set()
            
            for line in result.stdout.split("\n"):
                # Parse: 192.168.50.24 dev enP7s7 lladdr 00:e0:4c:be:fa:cc REACHABLE
                match = re.match(
                    r'(\d+\.\d+\.\d+\.\d+)\s+\w+\s+\w+\s+lladdr\s+([0-9a-fA-F:]+)',
                    line
                )
                
                if match:
                    ip = match.group(1)
                    mac = match.group(2).lower().replace("-", ":")
                    
                    # Skip if not on same network
                    if not ip.startswith(router_network):
                        continue
                    
                    # Skip router itself
                    if ip == router_ip:
                        continue
                    
                    # Skip duplicates
                    if mac in seen_macs:
                        continue
                    seen_macs.add(mac)
                    
                    # Create device
                    device = RouterDevice(
                        mac_address=mac,
                        ip_address=ip,
                        hostname=f"Device-{mac.replace(':', '')[-6:].upper()}",
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
        """Get basic router info."""
        info = RouterInfo(
            vendor=self.vendor,
            ip_address=self.credentials.ip_address,
            is_reachable=self.is_available(),
            supports_api=False,
            discovery_method="arp_fallback"
        )
        
        # Try to get MAC address
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
    
    def try_upnp_discovery(self) -> List[RouterDevice]:
        """
        Try UPnP discovery as alternative.
        
        Some routers support UPnP IGD which can provide device info.
        """
        devices = []
        
        try:
            # This would require a UPnP library
            # Placeholder for future implementation
            logger.debug("UPnP discovery not yet implemented")
            
        except Exception as e:
            logger.debug(f"UPnP discovery failed: {e}")
        
        return devices
    
    def try_snmp_discovery(self, community: str = "public") -> List[RouterDevice]:
        """
        Try SNMP discovery as alternative.
        
        Some routers support SNMP which can provide device info.
        """
        devices = []
        
        try:
            # This would require pysnmp library
            # Placeholder for future implementation
            logger.debug("SNMP discovery not yet implemented")
            
        except Exception as e:
            logger.debug(f"SNMP discovery failed: {e}")
        
        return devices


def get_vendor_from_mac(mac_address: str) -> Optional[str]:
    """
    Get vendor name from MAC address OUI.
    
    Args:
        mac_address: MAC address (e.g., "08:bf:b8:44:ca:70")
        
    Returns:
        Vendor name if known, None otherwise
    """
    # OUI database (simplified)
    OUIS = {
        "08:BF:B8": "ASUSTeK Computer Inc.",
        "AC:22:0B": "ASUSTeK Computer Inc.",
        "E0:3F:49": "ASUSTeK Computer Inc.",
        "18:D6:C7": "TP-Link Technologies Co., Ltd.",
        "50:C7:BF": "TP-Link Technologies Co., Ltd.",
        "C0:C9:E8": "TP-Link Technologies Co., Ltd.",
        "20:E5:2A": "Netgear",
        "74:44:01": "Netgear",
        "28:80:23": "Netgear",
        "18:D8:0C": "Ubiquiti Networks Inc.",
        "24:A4:3C": "Ubiquiti Networks Inc.",
        "68:D7:9A": "Ubiquiti Networks Inc.",
    }
    
    oui = mac_address.upper()[:8].replace(":", "")
    
    for pattern, vendor in OUIS.items():
        if pattern.replace(":", "") == oui:
            return vendor
    
    return None
