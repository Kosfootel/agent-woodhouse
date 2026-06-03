"""
Router Discovery Module for Vigil

Automatically detects router vendor and capabilities using various
methods: MAC OUI lookup, HTTP fingerprinting, SNMP, UPnP.
"""

import re
import json
import socket
import subprocess
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from .base import RouterVendor, RouterInfo


# Common router OUIs (first 3 octets of MAC)
ROUTER_OUIS = {
    # ASUS
    "08:BF:B8": RouterVendor.ASUS,
    "AC:22:0B": RouterVendor.ASUS,
    "E0:3F:49": RouterVendor.ASUS,
    "04:D4:C4": RouterVendor.ASUS,
    "14:DA:E9": RouterVendor.ASUS,
    "60:45:CB": RouterVendor.ASUS,
    
    # TP-Link
    "18:D6:C7": RouterVendor.TP_LINK,
    "50:C7:BF": RouterVendor.TP_LINK,
    "C0:C9:E8": RouterVendor.TP_LINK,
    "10:27:BE": RouterVendor.TP_LINK,
    "54:AF:97": RouterVendor.TP_LINK,
    "30:B5:C2": RouterVendor.TP_LINK,
    "00:5F:67": RouterVendor.TP_LINK,
    "EC:08:6B": RouterVendor.TP_LINK,
    
    # Netgear
    "20:E5:2A": RouterVendor.NETGEAR,
    "74:44:01": RouterVendor.NETGEAR,
    "10:0D:7F": RouterVendor.NETGEAR,
    "28:80:23": RouterVendor.NETGEAR,
    "9C:D3:6D": RouterVendor.NETGEAR,
    "A0:04:60": RouterVendor.NETGEAR,
    
    # Ubiquiti
    "18:D8:0C": RouterVendor.UBIQUITI,
    "24:A4:3C": RouterVendor.UBIQUITI,
    "68:D7:9A": RouterVendor.UBIQUITI,
    "E0:63:DA": RouterVendor.UBIQUITI,
    "E2:63:DA": RouterVendor.UBIQUITI,
    
    # Linksys
    "20:2B:20": RouterVendor.LINKSYS,
    "58:EF:68": RouterVendor.LINKSYS,
    "94:10:3E": RouterVendor.LINKSYS,
    "14:91:82": RouterVendor.LINKSYS,
}

# HTTP endpoint signatures for fingerprinting
ROUTER_SIGNATURES = {
    RouterVendor.ASUS: {
        "endpoints": ["/login.cgi", "/Main_Login.asp", "/appGet.cgi"],
        "response_patterns": ["ASUS", "RT-", "GT-", "ZenWiFi"],
        "title_patterns": ["ASUS", "Wireless Router"],
    },
    RouterVendor.TP_LINK: {
        "endpoints": ["/", "/login.htm", "/cgi-bin/luci"],
        "response_patterns": ["TP-LINK", "TP-Link", "Deco"],
        "title_patterns": ["TP-Link", "TL-"],
    },
    RouterVendor.NETGEAR: {
        "endpoints": ["/", "/login.htm", "/soap", "/MNU_access.htm"],
        "response_patterns": ["NETGEAR", "Netgear", "Nighthawk", "Orbi"],
        "title_patterns": ["NETGEAR", "Nighthawk"],
    },
    RouterVendor.UBIQUITI: {
        "endpoints": ["/", "/login", "/api"],
        "response_patterns": ["UniFi", "EdgeRouter", "Ubiquiti"],
        "title_patterns": ["UniFi", "EdgeRouter"],
    },
}


@dataclass
class DiscoveryResult:
    """Result of router discovery."""
    vendor: RouterVendor
    confidence: float  # 0.0 to 1.0
    method: str
    router_info: Optional[RouterInfo] = None
    error: Optional[str] = None


class RouterDiscovery:
    """
    Discovers router vendor and capabilities.
    
    Uses multiple methods in order of reliability:
    1. MAC OUI lookup (most reliable if available)
    2. HTTP fingerprinting
    3. SNMP system description
    4. UPnP device description
    """
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
    
    def discover(self, router_ip: str) -> DiscoveryResult:
        """
        Discover router at given IP.
        
        Args:
            router_ip: Router IP address
            
        Returns:
            DiscoveryResult with vendor and confidence
        """
        # Try methods in order of reliability
        
        # 1. MAC OUI lookup
        result = self._discover_by_mac(router_ip)
        if result.confidence >= 0.9:
            return result
        
        # 2. HTTP fingerprinting
        http_result = self._discover_by_http(router_ip)
        if http_result.confidence > result.confidence:
            result = http_result
        if result.confidence >= 0.9:
            return result
        
        # 3. SNMP (if available)
        snmp_result = self._discover_by_snmp(router_ip)
        if snmp_result.confidence > result.confidence:
            result = snmp_result
        
        return result
    
    def _discover_by_mac(self, router_ip: str) -> DiscoveryResult:
        """Discover router by MAC OUI lookup."""
        try:
            # Get MAC address from ARP table
            mac = self._get_mac_from_arp(router_ip)
            if not mac:
                return DiscoveryResult(
                    vendor=RouterVendor.GENERIC,
                    confidence=0.0,
                    method="mac",
                    error="MAC not found in ARP table"
                )
            
            # Extract OUI (first 3 octets)
            oui = mac.upper()[:8].replace(":", "")
            
            # Look up OUI
            for oui_pattern, vendor in ROUTER_OUIS.items():
                if oui_pattern.replace(":", "") == oui:
                    return DiscoveryResult(
                        vendor=vendor,
                        confidence=0.95,
                        method="mac_oui",
                        router_info=RouterInfo(
                            vendor=vendor,
                            ip_address=router_ip,
                            mac_address=mac,
                            is_reachable=True,
                            discovery_method="mac_oui"
                        )
                    )
            
            return DiscoveryResult(
                vendor=RouterVendor.GENERIC,
                confidence=0.3,
                method="mac_oui",
                router_info=RouterInfo(
                    vendor=RouterVendor.GENERIC,
                    ip_address=router_ip,
                    mac_address=mac,
                    is_reachable=True,
                    discovery_method="mac_oui"
                )
            )
            
        except Exception as e:
            return DiscoveryResult(
                vendor=RouterVendor.GENERIC,
                confidence=0.0,
                method="mac",
                error=str(e)
            )
    
    def _discover_by_http(self, router_ip: str) -> DiscoveryResult:
        """Discover router by HTTP fingerprinting."""
        import requests
        
        try:
            # Try to fetch the root page
            response = requests.get(
                f"http://{router_ip}/",
                timeout=self.timeout,
                allow_redirects=True
            )
            
            content = response.text.lower()
            
            # Check for vendor signatures
            for vendor, signatures in ROUTER_SIGNATURES.items():
                confidence = 0.0
                
                # Check response patterns
                for pattern in signatures["response_patterns"]:
                    if pattern.lower() in content:
                        confidence += 0.3
                
                # Check title patterns
                title_match = re.search(r'<title>([^]+)</title>', content, re.IGNORECASE)
                if title_match:
                    title = title_match.group(1).lower()
                    for pattern in signatures["title_patterns"]:
                        if pattern.lower() in title:
                            confidence += 0.4
                
                # Check specific endpoints
                for endpoint in signatures["endpoints"]:
                    try:
                        ep_response = requests.get(
                            f"http://{router_ip}{endpoint}",
                            timeout=5,
                            allow_redirects=True
                        )
                        if ep_response.status_code < 400:
                            confidence += 0.1
                    except:
                        pass
                
                if confidence > 0.5:
                    return DiscoveryResult(
                        vendor=vendor,
                        confidence=min(confidence, 0.9),
                        method="http_fingerprint",
                        router_info=RouterInfo(
                            vendor=vendor,
                            ip_address=router_ip,
                            is_reachable=True,
                            discovery_method="http_fingerprint"
                        )
                    )
            
            # If we got here, router responds to HTTP but we couldn't identify vendor
            return DiscoveryResult(
                vendor=RouterVendor.GENERIC,
                confidence=0.4,
                method="http_fingerprint",
                router_info=RouterInfo(
                    vendor=RouterVendor.GENERIC,
                    ip_address=router_ip,
                    is_reachable=True,
                    discovery_method="http_generic"
                )
            )
            
        except Exception as e:
            return DiscoveryResult(
                vendor=RouterVendor.GENERIC,
                confidence=0.0,
                method="http",
                error=str(e)
            )
    
    def _discover_by_snmp(self, router_ip: str) -> DiscoveryResult:
        """Discover router by SNMP system description."""
        # SNMP discovery requires pysnmp library
        # This is a placeholder for future implementation
        return DiscoveryResult(
            vendor=RouterVendor.GENERIC,
            confidence=0.0,
            method="snmp",
            error="SNMP not implemented"
        )
    
    def _get_mac_from_arp(self, ip_address: str) -> Optional[str]:
        """Get MAC address from ARP table."""
        try:
            result = subprocess.run(
                ["ip", "neigh", "show"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            for line in result.stdout.split("\n"):
                if ip_address in line:
                    # Parse: 192.168.50.1 dev enP7s7 lladdr 08:bf:b8:44:ca:70 REACHABLE
                    match = re.search(r'lladdr\s+([0-9a-fA-F:]+)', line)
                    if match:
                        return match.group(1).lower()
            
            return None
            
        except Exception:
            return None
    
    def get_vendor_from_mac(self, mac_address: str) -> Optional[RouterVendor]:
        """
        Get router vendor from MAC address.
        
        Args:
            mac_address: MAC address (e.g., "08:bf:b8:44:ca:70")
            
        Returns:
            RouterVendor if known, None otherwise
        """
        mac_upper = mac_address.upper().replace(":", "")[:6]
        
        for oui, vendor in ROUTER_OUIS.items():
            if oui.replace(":", "").startswith(mac_upper):
                return vendor
        
        return None
