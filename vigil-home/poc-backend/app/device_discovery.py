#!/usr/bin/env python3
"""
Vigil Enhanced Device Discovery Service

Provides active device identification through multiple methods:
- mDNS/Bonjour scanning for service discovery and hostnames
- NetBIOS name resolution for Windows/Samba devices
- SNMP read-only queries for system descriptions
- UPnP/SSDP discovery for IoT devices and smart home equipment

This service complements passive DHCP/ARP monitoring with active probing
to enrich device metadata and improve classification accuracy.
"""

from __future__ import annotations

import re
import json
import socket
import struct
import asyncio
import logging
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, List, Any, Tuple, Set
from datetime import datetime, timedelta
from enum import Enum
import xml.etree.ElementTree as ET

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

class DiscoveryConfig:
    """Configuration for device discovery methods."""
    
    # Timing settings
    MDNS_TIMEOUT = 3.0  # seconds
    NETBIOS_TIMEOUT = 2.0
    SNMP_TIMEOUT = 3.0
    UPNP_TIMEOUT = 3.0
    
    # Retry settings
    MAX_RETRIES = 2
    RETRY_DELAY = 1.0
    
    # mDNS settings
    MDNS_MULTICAST_ADDR = "224.0.0.251"
    MDNS_PORT = 5353
    
    # SSDP/UPnP settings
    SSDP_MULTICAST_ADDR = "239.255.255.250"
    SSDP_PORT = 1900
    
    # NetBIOS settings
    NETBIOS_NS_PORT = 137
    
    # SNMP settings
    SNMP_COMMUNITY = "public"  # Read-only community string
    SNMP_PORT = 161


# =============================================================================
# Data Models
# =============================================================================

class DiscoverySource(Enum):
    """Source of device discovery information."""
    MDNS = "mdns"
    NETBIOS = "netbios"
    SNMP = "snmp"
    UPNP = "upnp"
    DHCP = "dhcp"
    ARP = "arp"
    MANUAL = "manual"


@dataclass
class DiscoveryResult:
    """Result from a single discovery method."""
    source: DiscoverySource
    mac: Optional[str] = None
    ip: str = ""
    hostname: Optional[str] = None
    device_name: Optional[str] = None  # Friendly name from device
    device_type: Optional[str] = None  # Inferred or reported type
    vendor: Optional[str] = None
    model: Optional[str] = None
    services: List[str] = field(default_factory=list)
    raw_data: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source.value,
            "mac": self.mac,
            "ip": self.ip,
            "hostname": self.hostname,
            "device_name": self.device_name,
            "device_type": self.device_type,
            "vendor": self.vendor,
            "model": self.model,
            "services": self.services,
            "raw_data": self.raw_data,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class EnrichedDevice:
    """Device with enriched information from multiple discovery sources."""
    mac: str
    ip: str
    primary_name: Optional[str] = None  # Best name to display
    hostname: Optional[str] = None
    mdns_name: Optional[str] = None
    netbios_name: Optional[str] = None
    snmp_sysname: Optional[str] = None
    upnp_friendly_name: Optional[str] = None
    user_nickname: Optional[str] = None
    device_type: Optional[str] = None
    device_type_confidence: float = 0.0
    vendor: Optional[str] = None
    model: Optional[str] = None
    services: List[str] = field(default_factory=list)
    discovery_sources: List[str] = field(default_factory=list)
    discovery_results: List[DiscoveryResult] = field(default_factory=list)
    last_discovered: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "mac": self.mac,
            "ip": self.ip,
            "primary_name": self.primary_name,
            "hostname": self.hostname,
            "mdns_name": self.mdns_name,
            "netbios_name": self.netbios_name,
            "snmp_sysname": self.snmp_sysname,
            "upnp_friendly_name": self.upnp_friendly_name,
            "user_nickname": self.user_nickname,
            "device_type": self.device_type,
            "device_type_confidence": self.device_type_confidence,
            "vendor": self.vendor,
            "model": self.model,
            "services": self.services,
            "discovery_sources": self.discovery_sources,
            "last_discovered": self.last_discovered.isoformat(),
        }
    
    def calculate_primary_name(self) -> Optional[str]:
        """Determine the best name to display for this device."""
        # Priority order for primary name
        candidates = [
            self.user_nickname,
            self.upnp_friendly_name,
            self.mdns_name,
            self.netbios_name,
            self.snmp_sysname,
            self.hostname,
        ]
        
        for candidate in candidates:
            if candidate and candidate.strip() and candidate not in ["unknown", "", "android"]:
                # Filter out generic android hostnames
                if not candidate.startswith("android-"):
                    return candidate
        
        # Fall back to cleaned hostname if nothing better available
        if self.hostname and self.hostname.strip():
            return self.hostname
        
        return None


# =============================================================================
# mDNS Discovery
# =============================================================================

class MDNSDiscovery:
    """
    mDNS/Bonjour service discovery for device identification.
    
    Scans for mDNS services and extracts:
    - Hostnames (.local domains)
    - Service types (_http._tcp, etc.)
    - TXT records with device metadata
    """
    
    # Common service types to query
    SERVICE_TYPES = [
        "_services._dns-sd._udp",  # Service discovery
        "_http._tcp",
        "_https._tcp",
        "_device-info._tcp",
        "_workstation._tcp",
        "_ssh._tcp",
        "_smb._tcp",
        "_afpovertcp._tcp",
        "_googlecast._tcp",
        "_airplay._tcp",
        "_raop._tcp",  # AirPlay audio
        "_hap._tcp",   # HomeKit Accessory Protocol
        "_hue._tcp",   # Philips Hue
        "_sonos._tcp",  # Sonos speakers
        "_spotify-connect._tcp",
        "_printer._tcp",
        "_ipp._tcp",
        "_pdl-datastream._tcp",
        "_scanner._tcp",
        "_cameras._tcp",
        "_amzn-wplay._tcp",  # Amazon Fire TV
        "_androidtvremote._tcp",
        "_nvstream._tcp",  # NVIDIA Shield
    ]
    
    def __init__(self, timeout: float = DiscoveryConfig.MDNS_TIMEOUT):
        self.timeout = timeout
    
    async def discover(self, target_ip: Optional[str] = None) -> List[DiscoveryResult]:
        """
        Discover devices via mDNS/Bonjour.
        
        Args:
            target_ip: If specified, only query this IP. Otherwise broadcast.
        
        Returns:
            List of discovery results with mDNS information.
        """
        results = []
        
        try:
            # Try using avahi-browse if available (Linux)
            results = await self._discover_avahi(target_ip)
        except Exception as e:
            logger.debug(f"avahi discovery failed: {e}")
        
        if not results:
            # Fallback to socket-based discovery
            try:
                results = await self._discover_socket(target_ip)
            except Exception as e:
                logger.warning(f"mDNS socket discovery failed: {e}")
        
        return results
    
    async def _discover_avahi(self, target_ip: Optional[str] = None) -> List[DiscoveryResult]:
        """Use avahi-browse for mDNS discovery (Linux)."""
        results = []
        
        for service_type in self.SERVICE_TYPES[:5]:  # Limit to common services
            try:
                cmd = ["avahi-browse", "-r", "-p", "-t", service_type]
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                
                try:
                    stdout, stderr = await asyncio.wait_for(
                        proc.communicate(),
                        timeout=self.timeout,
                    )
                except asyncio.TimeoutError:
                    proc.kill()
                    continue
                
                output = stdout.decode("utf-8", errors="ignore")
                results.extend(self._parse_avahi_output(output))
                
            except FileNotFoundError:
                # avahi-browse not installed
                raise
            except Exception as e:
                logger.debug(f"avahi-browse error for {service_type}: {e}")
        
        return results
    
    def _parse_avahi_output(self, output: str) -> List[DiscoveryResult]:
        """Parse avahi-browse output."""
        results = []
        
        for line in output.strip().split("\n"):
            if not line.startswith("="):
                continue
            
            # Format: = <iface> <proto> <name> <type> <domain> <hostname> <ip>
            parts = line.split(";")
            if len(parts) >= 7:
                result = DiscoveryResult(
                    source=DiscoverySource.MDNS,
                    ip=parts[6],
                    hostname=parts[5],
                    device_name=parts[2],
                    services=[parts[3]],
                    confidence=0.9,
                )
                results.append(result)
        
        return results
    
    async def _discover_socket(self, target_ip: Optional[str] = None) -> List[DiscoveryResult]:
        """Fallback socket-based mDNS discovery."""
        results = []
        
        # This is a simplified implementation
        # Full implementation would require proper DNS packet construction
        # For now, we return empty results and rely on system tools
        
        logger.debug("Socket-based mDNS discovery not fully implemented, using system tools")
        return results
    
    async def query_device(self, ip: str) -> Optional[DiscoveryResult]:
        """Query a specific device for mDNS information."""
        # Try to resolve hostname via reverse mDNS
        try:
            hostname = socket.getnameinfo((ip, 0), socket.NI_NAMEREQD)[0]
            if ".local" in hostname:
                return DiscoveryResult(
                    source=DiscoverySource.MDNS,
                    ip=ip,
                    hostname=hostname,
                    confidence=0.7,
                )
        except Exception:
            pass
        
        return None


# =============================================================================
# NetBIOS Discovery
# =============================================================================

class NetBIOSDiscovery:
    """
    NetBIOS name resolution for Windows and Samba devices.
    
    Queries devices for their NetBIOS names which often provide
    more meaningful identifiers than DHCP hostnames.
    """
    
    # NetBIOS name service constants
    NBNS_PORT = 137
    
    # NetBIOS name query request template
    NAME_QUERY = struct.pack(
        "!HHHHHH",
        0x0000,  # Transaction ID
        0x0100,  # Flags: Recursion desired
        0x0001,  # Questions
        0x0000,  # Answer RRs
        0x0000,  # Authority RRs
        0x0000,  # Additional RRs
    )
    
    def __init__(self, timeout: float = DiscoveryConfig.NETBIOS_TIMEOUT):
        self.timeout = timeout
    
    def _encode_netbios_name(self, name: str) -> bytes:
        """Encode a NetBIOS name."""
        # Pad to 15 chars and encode
        padded = name.upper().ljust(15)[:15]
        encoded = b""
        for char in padded:
            encoded += bytes([0x41 + (ord(char) >> 4), 0x41 + (ord(char) & 0x0F)])
        encoded += b"AA"  # Scope (00)
        return encoded
    
    async def query_device(self, ip: str) -> Optional[DiscoveryResult]:
        """Query a device for NetBIOS name."""
        try:
            # Use nmblookup if available
            proc = await asyncio.create_subprocess_exec(
                "nmblookup",
                "-A", ip,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=self.timeout,
                )
            except asyncio.TimeoutError:
                proc.kill()
                return None
            
            output = stdout.decode("utf-8", errors="ignore")
            return self._parse_nmblookup_output(ip, output)
            
        except FileNotFoundError:
            logger.debug("nmblookup not available")
            return await self._query_socket(ip)
        except Exception as e:
            logger.debug(f"NetBIOS query failed for {ip}: {e}")
            return None
    
    def _parse_nmblookup_output(self, ip: str, output: str) -> Optional[DiscoveryResult]:
        """Parse nmblookup output."""
        name = None
        services = []
        
        for line in output.split("\n"):
            line = line.strip()
            
            # Look for the NetBIOS name
            if "<00>" in line and "-" not in line:
                parts = line.split()
                if parts:
                    name = parts[0]
            
            # Look for service types
            if "<20>" in line:
                services.append("file_server")
            if "<03>" in line:
                services.append("messenger")
            if "<06>" in line:
                services.append("remote_access")
            if "<21>" in line:
                services.append("ftp")
            if "<80>" in line:
                services.append("web_server")
        
        if name:
            return DiscoveryResult(
                source=DiscoverySource.NETBIOS,
                ip=ip,
                netbios_name=name,
                device_name=name,
                services=services,
                confidence=0.85,
            )
        
        return None
    
    async def _query_socket(self, ip: str) -> Optional[DiscoveryResult]:
        """Fallback socket-based NetBIOS query."""
        # Simplified implementation
        # Full implementation requires proper NetBIOS packet handling
        return None


# =============================================================================
# SNMP Discovery
# =============================================================================

class SNMPDiscovery:
    """
    SNMP read-only discovery for device information.
    
    Queries standard MIBs:
    - sysDescr (1.3.6.1.2.1.1.1.0): Device description
    - sysName (1.3.6.1.2.1.1.5.0): System name
    - sysContact (1.3.6.1.2.1.1.4.0): Contact info
    """
    
    # Standard SNMP OIDs
    OID_SYS_DESCR = "1.3.6.1.2.1.1.1.0"
    OID_SYS_NAME = "1.3.6.1.2.1.1.5.0"
    OID_SYS_CONTACT = "1.3.6.1.2.1.1.4.0"
    OID_SYS_LOCATION = "1.3.6.1.2.1.1.6.0"
    
    def __init__(self, 
                 community: str = DiscoveryConfig.SNMP_COMMUNITY,
                 timeout: float = DiscoveryConfig.SNMP_TIMEOUT):
        self.community = community
        self.timeout = timeout
    
    async def query_device(self, ip: str) -> Optional[DiscoveryResult]:
        """Query a device via SNMP for system information."""
        try:
            # Try snmpget first (requires net-snmp)
            sys_descr = await self._snmp_get(ip, self.OID_SYS_DESCR)
            sys_name = await self._snmp_get(ip, self.OID_SYS_NAME)
            
            if sys_descr or sys_name:
                vendor, model = self._parse_description(sys_descr or "")
                
                return DiscoveryResult(
                    source=DiscoverySource.SNMP,
                    ip=ip,
                    hostname=sys_name,
                    device_name=sys_name,
                    vendor=vendor,
                    model=model,
                    raw_data={
                        "sys_descr": sys_descr,
                        "sys_name": sys_name,
                    },
                    confidence=0.9 if sys_descr else 0.6,
                )
        
        except Exception as e:
            logger.debug(f"SNMP query failed for {ip}: {e}")
        
        return None
    
    async def _snmp_get(self, ip: str, oid: str) -> Optional[str]:
        """Execute snmpget command."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "snmpget",
                "-v", "2c",
                "-c", self.community,
                "-t", str(int(self.timeout)),
                "-O", "v",  # Value only
                ip,
                oid,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=self.timeout + 1,
                )
            except asyncio.TimeoutError:
                proc.kill()
                return None
            
            if proc.returncode == 0:
                value = stdout.decode("utf-8", errors="ignore").strip()
                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                return value if value else None
                
        except FileNotFoundError:
            logger.debug("snmpget not available")
        except Exception as e:
            logger.debug(f"snmpget error: {e}")
        
        return None
    
    def _parse_description(self, description: str) -> Tuple[Optional[str], Optional[str]]:
        """Parse sysDescr to extract vendor and model."""
        vendor = None
        model = None
        
        # Common patterns
        patterns = [
            (r"Cisco", r"Cisco\s+(\S+)"),
            (r"HP", r"HP\s+(\S+)"),
            (r"Juniper", r"Juniper\s+(\S+)"),
            (r"D-Link", r"D-Link\s+(\S+)"),
            (r"NETGEAR", r"NETGEAR\s+(\S+)"),
            (r"Synology", r"Synology\s+(\S+)"),
            (r"QNAP", r"QNAP\s+(\S+)"),
            (r"Linux", None),
            (r"Windows", None),
            (r"Ubuntu", None),
        ]
        
        for v, m in patterns:
            if v.lower() in description.lower():
                vendor = v
                if m:
                    match = re.search(m, description, re.IGNORECASE)
                    if match:
                        model = match.group(1)
                break
        
        return vendor, model


# =============================================================================
# UPnP/SSDP Discovery
# =============================================================================

class UPnPDiscovery:
    """
    UPnP/SSDP discovery for IoT and smart home devices.
    
    SSDP (Simple Service Discovery Protocol) multicast discovery
    finds devices that advertise themselves, including:
    - Smart TVs
    - Media streamers (Roku, Chromecast, etc.)
    - Printers
    - IoT hubs
    - Network cameras
    """
    
    # SSDP multicast address and port
    SSDP_ADDR = "239.255.255.250"
    SSDP_PORT = 1900
    
    # SSDP search request
    SEARCH_REQUEST = (
        "M-SEARCH * HTTP/1.1\r\n"
        "HOST: 239.255.255.250:1900\r\n"
        'MAN: "ssdp:discover"\r\n'
        "MX: 3\r\n"
        "ST: ssdp:all\r\n"
        "\r\n"
    )
    
    # Specific service types for more targeted discovery
    SERVICE_TYPES = [
        "ssdp:all",
        "urn:schemas-upnp-org:device:InternetGatewayDevice:1",
        "urn:schemas-upnp-org:device:MediaRenderer:1",
        "urn:schemas-upnp-org:device:MediaServer:1",
        "urn:schemas-upnp-org:device:Printer:1",
        "urn:schemas-upnp-org:device:Scanner:1",
        "urn:schemas-upnp-org:device:WANDevice:1",
        "urn:schemas-upnp-org:device:WANConnectionDevice:1",
        "urn:schemas-upnp-org:service:AVTransport:1",
        "urn:schemas-upnp-org:service:RenderingControl:1",
    ]
    
    def __init__(self, timeout: float = DiscoveryConfig.UPNP_TIMEOUT):
        self.timeout = timeout
    
    async def discover(self) -> List[DiscoveryResult]:
        """Discover UPnP devices on the network."""
        results = []
        discovered_ips = set()
        
        try:
            # Create UDP socket for SSDP
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(self.timeout)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Allow multicast
            sock.setsockopt(
                socket.IPPROTO_IP,
                socket.IP_MULTICAST_TTL,
                2
            )
            
            # Send search request
            sock.sendto(
                self.SEARCH_REQUEST.encode(),
                (self.SSDP_ADDR, self.SSDP_PORT),
            )
            
            # Collect responses
            start_time = asyncio.get_event_loop().time()
            while (asyncio.get_event_loop().time() - start_time) < self.timeout:
                try:
                    sock.settimeout(self.timeout - (asyncio.get_event_loop().time() - start_time))
                    data, addr = sock.recvfrom(1024)
                    
                    ip = addr[0]
                    if ip not in discovered_ips:
                        discovered_ips.add(ip)
                        result = self._parse_ssdp_response(ip, data.decode("utf-8", errors="ignore"))
                        if result:
                            results.append(result)
                            
                except socket.timeout:
                    break
            
            sock.close()
            
        except Exception as e:
            logger.debug(f"UPnP discovery error: {e}")
        
        # Fetch device descriptions for discovered devices
        await self._fetch_descriptions(results)
        
        return results
    
    def _parse_ssdp_response(self, ip: str, response: str) -> Optional[DiscoveryResult]:
        """Parse SSDP response packet."""
        lines = response.strip().split("\r\n")
        
        headers = {}
        for line in lines:
            if ":" in line:
                key, value = line.split(":", 1)
                headers[key.strip().lower()] = value.strip()
        
        # Extract information
        location = headers.get("location")
        usn = headers.get("usn", "")  # Unique Service Name
        server = headers.get("server", "")  # Server header often has device info
        st = headers.get("st", "")  # Search target / device type
        
        # Parse device type from USN or ST
        device_type = self._infer_device_type(st, server, usn)
        
        # Parse vendor from Server header
        vendor = self._parse_vendor(server)
        
        result = DiscoveryResult(
            source=DiscoverySource.UPNP,
            ip=ip,
            device_type=device_type,
            vendor=vendor,
            raw_data={
                "location": location,
                "usn": usn,
                "server": server,
                "st": st,
            },
            confidence=0.7,
        )
        
        # Store location for later description fetch
        if location:
            result.raw_data["description_url"] = location
        
        return result
    
    def _infer_device_type(self, st: str, server: str, usn: str) -> Optional[str]:
        """Infer device type from UPnP identifiers."""
        type_indicators = {
            "mediarenderer": "media_player",
            "mediaserver": "media_server",
            "printer": "printer",
            "scanner": "scanner",
            "camer": "camera",
            "gateway": "router",
            "wan": "router",
            "chromecast": "media_player",
            "roku": "media_player",
            "tv": "smart_tv",
            "smarttv": "smart_tv",
            "xbox": "gaming_console",
            "playstation": "gaming_console",
        }
        
        combined = f"{st} {server} {usn}".lower()
        
        for indicator, device_type in type_indicators.items():
            if indicator in combined:
                return device_type
        
        return None
    
    def _parse_vendor(self, server: str) -> Optional[str]:
        """Extract vendor from Server header."""
        vendors = ["Samsung", "LG", "Sony", "Panasonic", "Philips", "Roku", 
                   "Google", "Amazon", "Microsoft", "Apple", "Synology", 
                   "QNAP", "Asus", "Netgear", "TP-Link", "D-Link"]
        
        for vendor in vendors:
            if vendor.lower() in server.lower():
                return vendor
        
        return None
    
    async def _fetch_descriptions(self, results: List[DiscoveryResult]):
        """Fetch and parse device description XML for discovered devices."""
        for result in results:
            url = result.raw_data.get("description_url")
            if not url:
                continue
            
            try:
                # This would require aiohttp or similar
                # For now, we skip the description fetch
                pass
            except Exception as e:
                logger.debug(f"Failed to fetch UPnP description from {url}: {e}")
    
    def _parse_description_xml(self, xml_content: str) -> Dict[str, Any]:
        """Parse UPnP device description XML."""
        try:
            root = ET.fromstring(xml_content)
            
            # Extract device info
            device_info = {}
            
            # Namespace handling
            ns = {"upnp": "urn:schemas-upnp-org:device-1-0"}
            
            device = root.find(".//upnp:device", ns)
            if device is not None:
                device_info["device_type"] = self._get_xml_text(device, "upnp:deviceType", ns)
                device_info["friendly_name"] = self._get_xml_text(device, "upnp:friendlyName", ns)
                device_info["manufacturer"] = self._get_xml_text(device, "upnp:manufacturer", ns)
                device_info["model"] = self._get_xml_text(device, "upnp:modelName", ns)
                device_info["model_description"] = self._get_xml_text(device, "upnp:modelDescription", ns)
            
            return device_info
            
        except ET.ParseError as e:
            logger.debug(f"Failed to parse UPnP description: {e}")
            return {}
    
    def _get_xml_text(self, element: ET.Element, path: str, ns: Dict[str, str]) -> Optional[str]:
        """Safely extract text from XML element."""
        child = element.find(path, ns)
        return child.text if child is not None else None


# =============================================================================
# Device Discovery Service
# =============================================================================

class DeviceDiscoveryService:
    """
    Unified device discovery service that combines multiple discovery methods.
    
    Provides enriched device information by:
    1. Querying devices via multiple protocols (mDNS, NetBIOS, SNMP, UPnP)
    2. Aggregating results into a unified device profile
    3. Calculating confidence scores for identification
    """
    
    def __init__(self):
        self.mdns = MDNSDiscovery()
        self.netbios = NetBIOSDiscovery()
        self.snmp = SNMPDiscovery()
        self.upnp = UPnPDiscovery()
    
    async def discover_device(self, ip: str, mac: Optional[str] = None) -> EnrichedDevice:
        """
        Discover all available information about a device.
        
        Args:
            ip: Device IP address
            mac: Optional MAC address
        
        Returns:
            EnrichedDevice with combined discovery results
        """
        discovery_tasks = [
            ("mDNS", self.mdns.query_device(ip)),
            ("NetBIOS", self.netbios.query_device(ip)),
            ("SNMP", self.snmp.query_device(ip)),
        ]
        
        results = []
        for name, task in discovery_tasks:
            try:
                result = await asyncio.wait_for(task, timeout=5.0)
                if result:
                    result.mac = mac
                    results.append(result)
            except asyncio.TimeoutError:
                logger.debug(f"{name} discovery timed out for {ip}")
            except Exception as e:
                logger.debug(f"{name} discovery failed for {ip}: {e}")
        
        # Aggregate results into enriched device
        return self._aggregate_results(ip, mac, results)
    
    async def discover_all(self, devices: List[Dict[str, str]]) -> List[EnrichedDevice]:
        """
        Discover information for multiple devices.
        
        Args:
            devices: List of dicts with 'ip' and optionally 'mac' keys
        
        Returns:
            List of EnrichedDevice with discovery results
        """
        tasks = [self.discover_device(d["ip"], d.get("mac")) for d in devices]
        return await asyncio.gather(*tasks)
    
    async def scan_network(self) -> List[DiscoveryResult]:
        """Scan network for all discoverable devices via UPnP/SSDP."""
        return await self.upnp.discover()
    
    def _aggregate_results(self, ip: str, mac: Optional[str], 
                          results: List[DiscoveryResult]) -> EnrichedDevice:
        """Aggregate multiple discovery results into a unified device profile."""
        
        device = EnrichedDevice(mac=mac or "", ip=ip)
        device.discovery_results = results
        
        # Collect all discovery sources
        sources = []
        services = []
        
        # Priority order for name fields
        for result in results:
            sources.append(result.source.value)
            
            # Device name
            if result.source == DiscoverySource.MDNS:
                device.mdns_name = result.device_name or result.hostname
                services.extend(result.services)
            elif result.source == DiscoverySource.NETBIOS:
                device.netbios_name = result.device_name
                services.extend(result.services)
            elif result.source == DiscoverySource.SNMP:
                device.snmp_sysname = result.hostname
            elif result.source == DiscoverySource.UPNP:
                device.upnp_friendly_name = result.device_name
                services.extend(result.services)
            
            # Type and vendor (prefer higher confidence)
            if result.device_type and result.confidence > device.device_type_confidence:
                device.device_type = result.device_type
                device.device_type_confidence = result.confidence
            
            if result.vendor:
                device.vendor = result.vendor
            
            if result.model:
                device.model = result.model
        
        device.discovery_sources = sources
        device.services = list(set(services))  # Deduplicate
        
        # Calculate primary display name
        device.primary_name = device.calculate_primary_name()
        
        return device
    
    def suggest_device_type(self, device: EnrichedDevice) -> Tuple[Optional[str], float]:
        """
        Suggest device type based on discovery information.
        
        Returns:
            Tuple of (suggested_type, confidence)
        """
        # Service-based inference
        service_types = {
            "_airplay._tcp": ("media_player", 0.9),
            "_googlecast._tcp": ("media_player", 0.9),
            "_spotify-connect._tcp": ("media_player", 0.9),
            "_sonos._tcp": ("smart_speaker", 0.9),
            "_printer._tcp": ("printer", 0.9),
            "_ipp._tcp": ("printer", 0.9),
            "_scanner._tcp": ("scanner", 0.9),
            "_hap._tcp": ("smart_home_hub", 0.85),
            "_hue._tcp": ("smart_light", 0.9),
            "_cameras._tcp": ("camera", 0.9),
            "_amzn-wplay._tcp": ("media_player", 0.85),
            "_androidtvremote._tcp": ("smart_tv", 0.9),
            "_nvstream._tcp": ("gaming_console", 0.9),
            "_ssh._tcp": ("computer", 0.6),
            "_smb._tcp": ("computer", 0.6),
            "file_server": ("nas", 0.7),
            "web_server": ("server", 0.7),
        }
        
        for service, (device_type, confidence) in service_types.items():
            if any(service in s for s in device.services):
                return device_type, confidence
        
        # Name-based inference
        name = (device.primary_name or "").lower()
        name_patterns = {
            "tv": ("smart_tv", 0.7),
            "roku": ("media_player", 0.9),
            "chromecast": ("media_player", 0.9),
            "firetv": ("media_player", 0.9),
            "xbox": ("gaming_console", 0.9),
            "playstation": ("gaming_console", 0.9),
            "iphone": ("smartphone", 0.9),
            "ipad": ("tablet", 0.9),
            "macbook": ("laptop", 0.9),
            "printer": ("printer", 0.8),
            "camera": ("camera", 0.8),
        }
        
        for pattern, (device_type, confidence) in name_patterns.items():
            if pattern in name:
                return device_type, confidence
        
        return None, 0.0


# =============================================================================
# Utility Functions
# =============================================================================

def normalize_mac(mac: str) -> str:
    """Normalize MAC address to standard format (AA:BB:CC:DD:EE:FF)."""
    # Remove separators and convert to uppercase
    cleaned = re.sub(r"[^0-9a-fA-F]", "", mac).upper()
    # Add colons
    return ":".join(cleaned[i:i+2] for i in range(0, 12, 2))


def is_private_ip(ip: str) -> bool:
    """Check if IP is in private address space."""
    try:
        import ipaddress
        addr = ipaddress.ip_address(ip)
        return addr.is_private
    except ValueError:
        return False


# =============================================================================
# CLI Interface
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Vigil Device Discovery")
    parser.add_argument("command", choices=["discover", "scan", "query"])
    parser.add_argument("--ip", help="Target IP address")
    parser.add_argument("--mac", help="Target MAC address")
    parser.add_argument("--method", choices=["mdns", "netbios", "snmp", "upnp", "all"],
                       default="all", help="Discovery method")
    
    args = parser.parse_args()
    
    async def main():
        service = DeviceDiscoveryService()
        
        if args.command == "query" and args.ip:
            print(f"Querying device {args.ip}...")
            device = await service.discover_device(args.ip, args.mac)
            print(json.dumps(device.to_dict(), indent=2))
        
        elif args.command == "scan":
            print("Scanning network for UPnP devices...")
            results = await service.scan_network()
            for result in results:
                print(f"  {result.ip}: {result.device_type or 'unknown'} ({result.vendor or 'unknown'})")
        
        elif args.command == "discover":
            print("Running full network discovery...")
            # This would scan the local subnet
            pass
    
    asyncio.run(main())
