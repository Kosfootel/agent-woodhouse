"""
Router Integration Module for vigil-home
Handles router discovery, API communication, and device synchronization.
"""

import asyncio
import ipaddress
import json
import logging
import re
import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Set, Any
from urllib.parse import urljoin

import aiohttp
import xml.etree.ElementTree as ET
from cryptography.fernet import Fernet
import base64
import hashlib

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class RouterDevice:
    """Represents a device discovered on the network."""
    mac_address: str
    ip_address: str
    name: str = ""
    device_type: str = "unknown"
    is_connected: bool = True
    first_seen: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RouterInfo:
    """Represents discovered router information."""
    ip_address: str
    mac_address: Optional[str] = None
    brand: str = "unknown"
    model: str = "unknown"
    api_endpoint: Optional[str] = None
    discovery_method: str = "unknown"
    ssdp_location: Optional[str] = None


# ============================================================================
# Secure Credential Manager
# ============================================================================

class SecureCredentialManager:
    """
    Manages router credentials with Fernet AES-256 encryption.
    Stores credentials in SQLite database.
    """
    
    def __init__(self, db_path: str = "router_credentials.db"):
        self.db_path = db_path
        self._init_db()
        self._key = self._get_or_create_key()
        self._cipher = Fernet(self._key)
    
    def _init_db(self):
        """Initialize the credentials database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS credentials (
                    router_id TEXT PRIMARY KEY,
                    username_encrypted BLOB,
                    password_encrypted BLOB,
                    api_key_encrypted BLOB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS encryption_key (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    key_value BLOB NOT NULL
                )
            """)
            conn.commit()
    
    def _get_or_create_key(self) -> bytes:
        """Get existing encryption key or create new one."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT key_value FROM encryption_key WHERE id = 1")
            row = cursor.fetchone()
            if row:
                return row[0]
            
            # Generate new key
            key = Fernet.generate_key()
            conn.execute("INSERT INTO encryption_key (id, key_value) VALUES (1, ?)", (key,))
            conn.commit()
            return key
    
    def store_credentials(self, router_id: str, username: str, password: str, api_key: Optional[str] = None):
        """Store encrypted credentials for a router."""
        encrypted_user = self._cipher.encrypt(username.encode())
        encrypted_pass = self._cipher.encrypt(password.encode())
        encrypted_api = self._cipher.encrypt(api_key.encode()) if api_key else None
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO credentials 
                (router_id, username_encrypted, password_encrypted, api_key_encrypted, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (router_id, encrypted_user, encrypted_pass, encrypted_api))
            conn.commit()
    
    def get_credentials(self, router_id: str) -> Optional[Dict[str, str]]:
        """Retrieve and decrypt credentials for a router."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """SELECT username_encrypted, password_encrypted, api_key_encrypted 
                   FROM credentials WHERE router_id = ?""",
                (router_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            
            result = {
                "username": self._cipher.decrypt(row[0]).decode(),
                "password": self._cipher.decrypt(row[1]).decode(),
            }
            if row[2]:
                result["api_key"] = self._cipher.decrypt(row[2]).decode()
            return result
    
    def delete_credentials(self, router_id: str):
        """Delete credentials for a router."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM credentials WHERE router_id = ?", (router_id,))
            conn.commit()


# ============================================================================
# Router API Client Base Class
# ============================================================================

class RouterAPIClient(ABC):
    """
    Abstract base class for router API clients.
    Implementations must provide router-specific communication logic.
    """
    
    def __init__(self, host: str, credentials: Dict[str, str]):
        self.host = host
        self.credentials = credentials
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            self.session = None
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with the router. Returns True on success."""
        pass
    
    @abstractmethod
    async def get_connected_devices(self) -> List[RouterDevice]:
        """Fetch list of connected devices from router."""
        pass
    
    @abstractmethod
    async def get_device_details(self, mac_address: str) -> Optional[RouterDevice]:
        """Get detailed information about a specific device."""
        pass
    
    @abstractmethod
    async def get_router_info(self) -> Dict[str, Any]:
        """Get router status and information."""
        pass
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> aiohttp.ClientResponse:
        """Make HTTP request with error handling."""
        if not self.session:
            raise RuntimeError("Client not in async context")
        
        url = urljoin(f"http://{self.host}", endpoint)
        try:
            async with self.session.request(method, url, **kwargs) as response:
                response.raise_for_status()
                return response
        except aiohttp.ClientError as e:
            logger.error(f"Request failed: {e}")
            raise


# ============================================================================
# ASUSWRT Implementation (for ASUS GT6)
# ============================================================================

class ASUSWRTClient(RouterAPIClient):
    """
    ASUSWRT API client for ASUS routers including GT6.
    Supports both traditional HTTP API and newer REST API.
    """
    
    def __init__(self, host: str, credentials: Dict[str, str], use_https: bool = False):
        super().__init__(host, credentials)
        self.use_https = use_https
        self.protocol = "https" if use_https else "http"
        self._token: Optional[str] = None
        self._cookies: Dict[str, str] = {}
    
    def _get_base_url(self) -> str:
        return f"{self.protocol}://{self.host}"
    
    async def authenticate(self) -> bool:
        """Authenticate with ASUS router using login.cgi."""
        if not self.session:
            raise RuntimeError("Client not in async context")
        
        login_url = f"{self._get_base_url()}/login.cgi"
        
        # ASUSWRT expects username and password in specific format
        data = {
            "login_authorization": base64.b64encode(
                f"{self.credentials['username']}:{self.credentials['password']}".encode()
            ).decode()
        }
        
        try:
            async with self.session.post(login_url, data=data, ssl=False) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("success"):
                        self._token = result.get("asus_token")
                        # Store cookies for subsequent requests
                        self._cookies = {k: v for k, v in response.cookies.items()}
                        logger.info(f"Successfully authenticated with ASUS router at {self.host}")
                        return True
                    else:
                        logger.error(f"Authentication failed: {result}")
                        return False
                else:
                    logger.error(f"Authentication HTTP error: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    async def get_connected_devices(self) -> List[RouterDevice]:
        """Fetch connected devices from ASUS router."""
        if not self._token:
            if not await self.authenticate():
                raise RuntimeError("Not authenticated")
        
        devices = []
        
        # ASUSWRT provides client list via appGet.cgi
        try:
            async with self.session.post(
                f"{self._get_base_url()}/appGet.cgi",
                data={"hook": "get_clientlist()"},
                cookies=self._cookies,
                headers={"Authorization": f"Bearer {self._token}"},
                ssl=False
            ) as response:
                data = await response.json()
                
                if "get_clientlist" in data:
                    client_list = data["get_clientlist"]
                    for mac, client_info in client_list.items():
                        if mac == "CLIENT_LIST":
                            continue
                        
                        device = RouterDevice(
                            mac_address=mac.upper(),
                            ip_address=client_info.get("ip", "unknown"),
                            name=client_info.get("nickName", client_info.get("name", "Unknown")),
                            device_type=client_info.get("type", "unknown"),
                            is_connected=client_info.get("isOnline", "0") == "1",
                            metadata={
                                "rssi": client_info.get("rssi", 0),
                                "connection_type": client_info.get("isWL", "0"),
                                "vendor": client_info.get("vendor", "")
                            }
                        )
                        devices.append(device)
        
        except Exception as e:
            logger.error(f"Failed to get connected devices: {e}")
        
        return devices
    
    async def get_device_details(self, mac_address: str) -> Optional[RouterDevice]:
        """Get detailed info for a specific device."""
        devices = await self.get_connected_devices()
        for device in devices:
            if device.mac_address.upper() == mac_address.upper():
                return device
        return None
    
    async def get_router_info(self) -> Dict[str, Any]:
        """Get ASUS router system information."""
        if not self._token:
            if not await self.authenticate():
                raise RuntimeError("Not authenticated")
        
        try:
            async with self.session.post(
                f"{self._get_base_url()}/appGet.cgi",
                data={"hook": "get_sysinfo()"},
                cookies=self._cookies,
                headers={"Authorization": f"Bearer {self._token}"},
                ssl=False
            ) as response:
                data = await response.json()
                return {
                    "model": data.get("model_name", "Unknown"),
                    "firmware": data.get("firmver", "Unknown"),
                    "uptime": data.get("uptime", "Unknown"),
                    "cpu_usage": data.get("cpu_usage", {}),
                    "memory_usage": data.get("memory_usage", {})
                }
        except Exception as e:
            logger.error(f"Failed to get router info: {e}")
            return {}


# ============================================================================
# Router Discovery
# ============================================================================

class RouterDiscovery:
    """
    Discovers routers on the local network using multiple methods:
    - Gateway IP detection
    - MAC OUI lookup for router manufacturers
    - SSDP/UPnP discovery
    """
    
    # Common router manufacturer OUIs
    ROUTER_OUIS = {
        "ASUSTek": ["04:D4:C4", "E0:3F:49", "AC:22:0B", "F0:2F:74", "30:85:A9"],
        "Netgear": ["28:C6:8E", "A0:04:60", "20:E5:2A", "44:94:FC"],
        "TP-Link": ["C0:25:E9", "18:A6:F7", "60:A4:B7", "10:27:F5"],
        "Linksys": ["58:EF:68", "20:AA:4B", "C0:56:27", "10:06:45"],
        "Ubiquiti": ["74:83:C2", "78:8A:20", "18:E8:DD", "E0:63:DA"],
    }
    
    SSDP_MSEARCH = """M-SEARCH * HTTP/1.1
HOST: 239.255.255.250:1900
MAN: "ssdp:discover"
MX: 3
ST: urn:schemas-upnp-org:device:InternetGatewayDevice:1

"""
    
    def __init__(self):
        self.discovered_routers: List[RouterInfo] = []
    
    def get_default_gateway(self) -> Optional[str]:
        """Get the default gateway IP address."""
        try:
            import subprocess
            result = subprocess.run(["ip", "route"], capture_output=True, text=True)
            for line in result.stdout.split("\n"):
                if "default" in line:
                    parts = line.split()
                    if "via" in parts:
                        return parts[parts.index("via") + 1]
        except Exception as e:
            logger.error(f"Failed to get default gateway: {e}")
        return None
    
    def get_mac_from_ip(self, ip: str) -> Optional[str]:
        """Get MAC address from IP using ARP table."""
        try:
            import subprocess
            result = subprocess.run(["ip", "neigh", "show", ip], capture_output=True, text=True)
            match = re.search(r"lladdr\s+([0-9a-fA-F:]{17})", result.stdout)
            if match:
                return match.group(1).upper()
        except Exception as e:
            logger.error(f"Failed to get MAC for {ip}: {e}")
        return None
    
    def identify_vendor_from_oui(self, mac: str) -> Optional[str]:
        """Identify router vendor from MAC OUI."""
        oui = mac[:8].upper()
        for vendor, ouis in self.ROUTER_OUIS.items():
            if any(o.upper() == oui for o in ouis):
                return vendor
        return None
    
    async def ssdp_discovery(self, timeout: int = 5) -> List[RouterInfo]:
        """Discover routers via SSDP/UPnP."""
        routers = []
        
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.settimeout(timeout)
            
            # Send SSDP M-SEARCH
            sock.sendto(self.SSDP_MSEARCH.encode(), ("239.255.255.250", 1900))
            
            # Collect responses
            start_time = asyncio.get_event_loop().time()
            while asyncio.get_event_loop().time() - start_time < timeout:
                try:
                    data, addr = sock.recvfrom(1024)
                    response = data.decode("utf-8", errors="ignore")
                    
                    # Parse SSDP response
                    location = None
                    for line in response.split("\r\n"):
                        if line.lower().startswith("location:"):
                            location = line.split(":", 1)[1].strip()
                    
                    if location:
                        routers.append(RouterInfo(
                            ip_address=addr[0],
                            discovery_method="SSDP",
                            ssdp_location=location,
                            api_endpoint=location
                        ))
                
                except socket.timeout:
                    break
            
            sock.close()
        
        except Exception as e:
            logger.error(f"SSDP discovery failed: {e}")
        
        return routers
    
    async def discover(self) -> List[RouterInfo]:
        """Run all discovery methods and return found routers."""
        routers = []
        
        # Method 1: Gateway detection
        gateway = self.get_default_gateway()
        if gateway:
            logger.info(f"Found default gateway: {gateway}")
            gateway_mac = self.get_mac_from_ip(gateway)
            vendor = self.identify_vendor_from_oui(gateway_mac) if gateway_mac else None
            
            routers.append(RouterInfo(
                ip_address=gateway,
                mac_address=gateway_mac,
                brand=vendor or "unknown",
                discovery_method="gateway"
            ))
        
        # Method 2: SSDP discovery
        ssdp_routers = await self.ssdp_discovery()
        for router in ssdp_routers:
            # Merge with existing if same IP
            existing = next((r for r in routers if r.ip_address == router.ip_address), None)
            if existing:
                existing.discovery_method = "gateway+SSDP"
                existing.api_endpoint = router.api_endpoint
            else:
                routers.append(router)
        
        self.discovered_routers = routers
        return routers


# ============================================================================
# Device Sync Service
# ============================================================================

class DeviceSyncService:
    """
    Polls router for devices and synchronizes with local SQLite database.
    """
    
    def __init__(self, db_path: str = "vigil_devices.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize the devices database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS devices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mac_address TEXT UNIQUE NOT NULL,
                    ip_address TEXT,
                    name TEXT,
                    device_type TEXT,
                    is_connected BOOLEAN DEFAULT 1,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    router_ip TEXT,
                    metadata TEXT
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_mac ON devices(mac_address)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_connected ON devices(is_connected)
            """)
            conn.commit()
    
    def sync_devices(self, devices: List[RouterDevice], router_ip: str):
        """Synchronize device list with database."""
        current_macs = {d.mac_address.upper() for d in devices}
        
        with sqlite3.connect(self.db_path) as conn:
            # Mark all devices from this router as offline first
            conn.execute(
                "UPDATE devices SET is_connected = 0 WHERE router_ip = ?",
                (router_ip,)
            )
            
            # Update or insert current devices
            for device in devices:
                metadata_json = json.dumps(device.metadata)
                
                conn.execute("""
                    INSERT INTO devices 
                    (mac_address, ip_address, name, device_type, is_connected, 
                     last_seen, router_ip, metadata)
                    VALUES (?, ?, ?, ?, 1, CURRENT_TIMESTAMP, ?, ?)
                    ON CONFLICT(mac_address) DO UPDATE SET
                        ip_address = excluded.ip_address,
                        name = excluded.name,
                        device_type = excluded.device_type,
                        is_connected = 1,
                        last_seen = CURRENT_TIMESTAMP,
                        router_ip = excluded.router_ip,
                        metadata = excluded.metadata
                """, (device.mac_address.upper(), device.ip_address, device.name,
                       device.device_type, router_ip, metadata_json))
            
            conn.commit()
    
    def get_devices(self, connected_only: bool = False) -> List[Dict]:
        """Get devices from database."""
        query = "SELECT * FROM devices"
        if connected_only:
            query += " WHERE is_connected = 1"
        query += " ORDER BY last_seen DESC"
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query)
            return [dict(row) for row in cursor.fetchall()]
    
    def get_device_by_mac(self, mac_address: str) -> Optional[Dict]:
        """Get a specific device by MAC address."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM devices WHERE mac_address = ?",
                (mac_address.upper(),)
            )
            row = cursor.fetchone()
            return dict(row) if row else None


# ============================================================================
# FastAPI Router Endpoints (Stubs)
# ============================================================================

"""
Stub FastAPI endpoints for router integration.

Usage:
    from fastapi import APIRouter, HTTPException, Depends
    from pydantic import BaseModel
    
    router = APIRouter(prefix="/router", tags=["router"])


class RouterConfig(BaseModel):
    ip_address: str
    username: str
    password: str
    brand: str = "auto"


class DeviceResponse(BaseModel):
    mac_address: str
    ip_address: str
    name: str
    device_type: str
    is_connected: bool


@router.get("/discover")
async def discover_routers() -> Dict:
    '''Discover routers on the network.'''
    discovery = RouterDiscovery()
    routers = await discovery.discover()
    return {
        "routers": [
            {
                "ip": r.ip_address,
                "brand": r.brand,
                "method": r.discovery_method
            }
            for r in routers
        ]
    }


@router.post("/configure")
async def configure_router(config: RouterConfig) -> Dict:
    '''Configure a router with credentials.'''
    cred_manager = SecureCredentialManager()
    router_id = f"router_{config.ip_address.replace('.', '_')}"
    
    cred_manager.store_credentials(
        router_id=router_id,
        username=config.username,
        password=config.password
    )
    
    return {
        "status": "configured",
        "router_id": router_id,
        "ip_address": config.ip_address
    }


@router.post("/sync")
async def sync_devices(router_id: str) -> Dict:
    '''Sync devices from configured router.'''
    cred_manager = SecureCredentialManager()
    credentials = cred_manager.get_credentials(router_id)
    
    if not credentials:
        raise HTTPException(status_code=404, detail="Router not configured")
    
    # Extract IP from router_id
    ip = router_id.replace("router_", "").replace("_", ".")
    
    async with ASUSWRTClient(ip, credentials) as client:
        devices = await client.get_connected_devices()
        sync_service = DeviceSyncService()
        sync_service.sync_devices(devices, ip)
    
    return {
        "synced": len(devices),
        "devices": [
            DeviceResponse(
                mac_address=d.mac_address,
                ip_address=d.ip_address,
                name=d.name,
                device_type=d.device_type,
                is_connected=d.is_connected
            )
            for d in devices
        ]
    }


@router.get("/devices")
async def list_devices(connected_only: bool = False) -> List[DeviceResponse]:
    '''List all devices from database.'''
    sync_service = DeviceSyncService()
    devices = sync_service.get_devices(connected_only)
    return [
        DeviceResponse(
            mac_address=d["mac_address"],
            ip_address=d["ip_address"],
            name=d["name"] or "Unknown",
            device_type=d["device_type"] or "unknown",
            is_connected=bool(d["is_connected"])
        )
        for d in devices
    ]
"""
