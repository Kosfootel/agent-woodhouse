"""
Active scanning module for Vigil - finds devices that don't respond to passive discovery
"""
import asyncio
import socket
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class ActiveDiscovery:
    """Active network scanning for device discovery"""
    
    # Common ports to check
    COMMON_PORTS = [22, 80, 443, 445, 3389, 5900, 8080, 8000, 9000, 161, 139]
    
    # Service signatures for OS detection
    SERVICE_SIGNATURES = {
        'SSH': {22: b'SSH'},
        'HTTP': {80: b'HTTP', 8080: b'HTTP'},
        'HTTPS': {443: b'', 8443: b''},
        'SMB': {445: b'SMB'},
        'RDP': {3389: b'RDP'},
        'VNC': {5900: b'RFB'},
        'SNMP': {161: b''},
        'NetBIOS': {139: b''},
    }
    
    async def scan_host(self, ip: str, timeout: float = 2.0) -> Optional[Dict]:
        """Scan a single host for open ports"""
        open_ports = []
        
        for port in self.COMMON_PORTS:
            try:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(ip, port),
                    timeout=timeout
                )
                
                # Try to grab banner
                banner = b''
                try:
                    banner = await asyncio.wait_for(reader.read(1024), timeout=1.0)
                except:
                    pass
                
                writer.close()
                await writer.wait_closed()
                
                open_ports.append({
                    'port': port,
                    'banner': banner.decode('utf-8', errors='ignore')[:100]
                })
                logger.info(f"Found open port {port} on {ip}")
                
            except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
                continue
        
        if open_ports:
            return {
                'ip': ip,
                'open_ports': open_ports,
                'discovery_method': 'active_scan',
                'confidence': 0.6 + (len(open_ports) * 0.1)
            }
        return None
    
    async def scan_network(self, network: str = "192.168.50", timeout: float = 2.0) -> List[Dict]:
        """Scan entire network range 192.168.50.1-254"""
        logger.info(f"Starting active scan of {network}.1-254...")
        
        tasks = []
        for i in range(1, 255):
            ip = f"{network}.{i}"
            tasks.append(self.scan_host(ip, timeout))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        found_devices = []
        for result in results:
            if isinstance(result, dict):
                found_devices.append(result)
                logger.info(f"Active scan found device at {result['ip']}")
        
        logger.info(f"Active scan complete. Found {len(found_devices)} devices")
        return found_devices
    
    def fingerprint_os(self, open_ports: List[Dict]) -> str:
        """Basic OS fingerprinting from open ports"""
        port_numbers = [p['port'] for p in open_ports]
        banners = [p.get('banner', '').lower() for p in open_ports]
        
        # Check banners for specific signatures
        for banner in banners:
            if 'windows' in banner or 'win32' in banner or 'win64' in banner:
                return "Windows"
            if 'ubuntu' in banner or 'debian' in banner or 'linux' in banner:
                return "Linux"
            if 'darwin' in banner or 'macos' in banner or 'mac os' in banner:
                return "macOS"
        
        if 3389 in port_numbers:
            return "Windows"
        elif 445 in port_numbers and 22 in port_numbers:
            return "Linux/macOS"
        elif 22 in port_numbers:
            return "Linux/Unix"
        elif 445 in port_numbers:
            return "Windows"
        elif 5900 in port_numbers:
            return "Desktop (VNC)"
        elif 161 in port_numbers:
            return "Network Device"
        elif 139 in port_numbers:
            return "Windows/Samba"
        return "Unknown"
    
    def infer_device_type(self, open_ports: List[Dict], os_guess: str) -> str:
        """Infer device type from ports and OS"""
        port_numbers = [p['port'] for p in open_ports]
        
        # Web services on non-standard ports often indicate IoT/developer devices
        if 8080 in port_numbers or 8000 in port_numbers or 9000 in port_numbers:
            if any(p in port_numbers for p in [22, 443]):
                return "server"
            return "iot"
        
        if 80 in port_numbers or 443 in port_numbers:
            if 22 in port_numbers:
                return "server"
            return "web_device"
        
        if 3389 in port_numbers:
            return "workstation"
        
        if 5900 in port_numbers:
            return "desktop"
        
        if 445 in port_numbers:
            return "workstation"
        
        if 22 in port_numbers:
            return "server"
        
        if 161 in port_numbers:
            return "network_device"
        
        return "unknown"

# Convenience function
async def run_active_scan(network: str = "192.168.50", timeout: float = 2.0) -> List[Dict]:
    """Run active scan and return discovered devices"""
    scanner = ActiveDiscovery()
    return await scanner.scan_network(network, timeout)
