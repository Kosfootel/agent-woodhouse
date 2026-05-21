#!/usr/bin/env python3
"""
ASUS Router Monitor Agent for Vigil
Scrapes device list from ASUS GT6 router web interface
"""

import requests
import re
import json
import sqlite3
import hashlib
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class RouterDevice:
    mac: str
    ip: str
    hostname: str
    connection_type: str  # 'wired' or 'wifi'
    rssi: Optional[int] = None  # WiFi signal strength
    status: str = 'online'
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None


class ASUSRouterMonitor:
    """Monitor for ASUS GT6 router"""
    
    def __init__(self, router_ip: str = "192.168.50.1", db_path: str = "data/vigil.db"):
        self.router_ip = router_ip
        self.db_path = db_path
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.0'
        })
        self.token = None
        
    def authenticate(self, username: str, password: str) -> bool:
        """Authenticate to router and get session token"""
        try:
            # ASUS uses a token-based auth system
            login_url = f"http://{self.router_ip}/login.cgi"
            
            # Get initial token
            resp = self.session.get(f"http://{self.router_ip}/", timeout=10)
            
            # Extract token if present
            token_match = re.search(r'asus_token\s*=\s*["\']([^"\']+)', resp.text)
            if token_match:
                self.token = token_match.group(1)
            
            # Attempt login
            login_data = {
                'login_authorization': hashlib.md5(f"{username}:{password}".encode()).hexdigest()
            }
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
            }
            if self.token:
                headers['Cookie'] = f'asus_token={self.token}'
            
            resp = self.session.post(
                login_url,
                data=login_data,
                headers=headers,
                timeout=10,
                allow_redirects=False
            )
            
            # Check if login succeeded
            if resp.status_code in [200, 302] and 'logout' in resp.text.lower():
                logger.info("Successfully authenticated to router")
                return True
            
            logger.warning(f"Authentication may have failed: {resp.status_code}")
            return False
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False
    
    def get_client_list(self) -> List[RouterDevice]:
        """Fetch device list from router"""
        devices = []
        
        try:
            # ASUS uses a JavaScript API endpoint
            # Try the main client list endpoint
            url = f"http://{self.router_ip}/update_clients.asp"
            resp = self.session.get(url, timeout=10)
            
            if resp.status_code == 200:
                # Parse the JavaScript response
                # Format is typically: fromNetworkmapd = {...}
                devices = self._parse_asus_response(resp.text)
            
            # Also try the JSON endpoint
            if not devices:
                url = f"http://{self.router_ip}/appGet.cgi?hook=get_clientlist()"
                resp = self.session.get(url, timeout=10)
                if resp.status_code == 200:
                    devices = self._parse_json_response(resp.text)
                    
        except Exception as e:
            logger.error(f"Failed to fetch client list: {e}")
        
        return devices
    
    def _parse_asus_response(self, text: str) -> List[RouterDevice]:
        """Parse ASUS JavaScript response"""
        devices = []
        
        # Extract the networkmapd data
        match = re.search(r'fromNetworkmapd\s*=\s*({.*?});', text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(1))
                for mac, info in data.items():
                    if mac == 'maclist':
                        continue
                    
                    device = RouterDevice(
                        mac=mac.upper(),
                        ip=info.get('ip', 'unknown'),
                        hostname=info.get('name', 'Unknown Device'),
                        connection_type='wifi' if info.get('isWL', '0') == '1' else 'wired',
                        rssi=int(info.get('rssi', 0)) if info.get('rssi') else None,
                        status='online' if info.get('isOnline', '0') == '1' else 'offline',
                        last_seen=datetime.now().isoformat()
                    )
                    devices.append(device)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON: {e}")
        
        return devices
    
    def _parse_json_response(self, text: str) -> List[RouterDevice]:
        """Parse JSON API response"""
        devices = []
        
        try:
            data = json.loads(text)
            client_list = data.get('get_clientlist', {})
            
            for mac, info in client_list.items():
                if not isinstance(info, dict):
                    continue
                    
                device = RouterDevice(
                    mac=mac.upper(),
                    ip=info.get('ip', 'unknown'),
                    hostname=info.get('name', 'Unknown Device'),
                    connection_type='wifi' if info.get('isWL', 0) == 1 else 'wired',
                    rssi=info.get('rssi'),
                    status='online',
                    last_seen=datetime.now().isoformat()
                )
                devices.append(device)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
        
        return devices
    
    def store_devices(self, devices: List[RouterDevice]):
        """Store discovered devices in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        for device in devices:
            # Insert or update device
            cursor.execute('''
                INSERT INTO devices 
                (mac, ip, hostname, vendor, device_type, trust_score, status, first_seen, last_seen)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(mac) DO UPDATE SET
                    ip = excluded.ip,
                    hostname = excluded.hostname,
                    status = excluded.status,
                    last_seen = excluded.last_seen
            ''', (
                device.mac,
                device.ip,
                device.hostname,
                None,  # vendor - could lookup from MAC
                device.connection_type,
                50,  # default trust score
                device.status,
                now,
                now
            ))
            
            # Record observation
            cursor.execute('''
                INSERT INTO device_observations 
                (device_mac, source, confidence, raw_data, observed_at)
                VALUES (?, 'router', 0.9, ?, ?)
            ''', (
                device.mac,
                json.dumps({
                    'rssi': device.rssi,
                    'connection_type': device.connection_type
                }),
                now
            ))
        
        conn.commit()
        conn.close()
        logger.info(f"Stored {len(devices)} devices from router")
    
    def run_once(self, username: str = None, password: str = None) -> List[RouterDevice]:
        """Run single scan"""
        if username and password:
            if not self.authenticate(username, password):
                logger.error("Authentication failed")
                return []
        
        devices = self.get_client_list()
        if devices:
            self.store_devices(devices)
        
        return devices


def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ASUS Router Monitor for Vigil')
    parser.add_argument('--router-ip', default='192.168.50.1', help='Router IP address')
    parser.add_argument('--db-path', default='data/vigil.db', help='Database path')
    parser.add_argument('--username', help='Router admin username')
    parser.add_argument('--password', help='Router admin password')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    parser.add_argument('--interval', type=int, default=300, help='Scan interval in seconds')
    
    args = parser.parse_args()
    
    monitor = ASUSRouterMonitor(args.router_ip, args.db_path)
    
    if args.once:
        devices = monitor.run_once(args.username, args.password)
        print(f"Discovered {len(devices)} devices:")
        for d in devices:
            print(f"  {d.mac} - {d.ip} - {d.hostname} ({d.connection_type})")
    else:
        logger.info(f"Starting router monitor (interval: {args.interval}s)")
        while True:
            try:
                devices = monitor.run_once(args.username, args.password)
                logger.info(f"Scan complete: {len(devices)} devices found")
            except Exception as e:
                logger.error(f"Scan failed: {e}")
            
            time.sleep(args.interval)


if __name__ == '__main__':
    main()
