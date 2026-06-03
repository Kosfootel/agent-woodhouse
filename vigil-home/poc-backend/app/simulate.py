"""Vigil Home - Synthetic Suricata eve.json simulator for testing."""

import json
import random
import time
import os
from datetime import datetime, timezone

EVE_PATH = "/var/log/suricata/eve.json"
INTERVAL = float(os.environ.get("VIGIL_SIM_INTERVAL", "3.0"))

DEVICE_TEMPLATES = [
    {"ip": "192.168.1.10", "mac": "aa:bb:cc:dd:ee:01", "host": "phone-erik"},
    {"ip": "192.168.1.20", "mac": "aa:bb:cc:dd:ee:02", "host": "laptop-erik"},
    {"ip": "192.168.1.30", "mac": "aa:bb:cc:dd:ee:03", "host": "nest-camera"},
    {"ip": "192.168.1.40", "mac": "aa:bb:cc:dd:ee:04", "host": "roku-living"},
    {"ip": "192.168.1.50", "mac": "aa:bb:cc:dd:ee:05", "host": "thermostat-hall"},
    {"ip": "10.0.0.99", "mac": "ff:ee:dd:cc:bb:aa", "host": "unknown-sensor"},
]

EVENT_TYPES = ["flow", "dns", "http", "tls"]

ALERT_TEMPLATES = [
    {"category": "Attempted Information Leak", "sig": "ET INFO Observed DNS Query to .xyz Domain", "severity": 2},
    {"category": "Potentially Bad Traffic", "sig": "ET POLICY Suspicious Inbound to IoT Device on Port 23", "severity": 2},
    {"category": "A Network Trojan was Detected", "sig": "ET TROJAN Known Malicious IP Connection", "severity": 1},
    {"category": "Misc Attack", "sig": "ET SCAN NMAP -sS Stealth Scan Detected", "severity": 2},
    {"category": "Attempted Administrator Privilege Gain", "sig": "ET WEB_SERVER Attempt to Access Admin Panel", "severity": 1},
]


def make_timestamp():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def make_flow_event(device):
    return {
        "timestamp": make_timestamp(),
        "event_type": "flow",
        "src_ip": device["ip"],
        "src_port": random.randint(1024, 65535),
        "dest_ip": random.choice(["8.8.8.8", "1.1.1.1", "93.184.216.34", "142.250.80.46"]),
        "dest_port": random.choice([80, 443, 53, 22]),
        "proto": random.choice(["TCP", "UDP"]),
        "flow": {
            "pkts_toserver": random.randint(1, 50),
            "pkts_toclient": random.randint(1, 50),
            "bytes_toserver": random.randint(100, 5000),
            "bytes_toclient": random.randint(100, 5000),
            "start": make_timestamp(),
            "end": make_timestamp(),
            "age": random.randint(1, 30),
            "state": random.choice(["new", "established", "closed"]),
        },
        "host": device["host"],
        "in_iface": "eth0",
    }


def make_dns_event(device):
    return {
        "timestamp": make_timestamp(),
        "event_type": "dns",
        "src_ip": device["ip"],
        "src_port": random.randint(1024, 65535),
        "dest_ip": "8.8.8.8",
        "dest_port": 53,
        "proto": "UDP",
        "dns": {
            "rrname": random.choice([
                "google.com", "facebook.com", "api.weather.gov",
                "updates.nest.com", "device-metrics-us.amazon.com",
                "evil-malware.xyz", "phishing-attempt.tk",
            ]),
            "rrtype": random.choice(["A", "AAAA", "TXT"]),
            "rcode": random.choices(
                ["NOERROR", "NXDOMAIN", "SERVFAIL"],
                weights=[90, 7, 3],
            )[0],
        },
        "host": device["host"],
    }


def make_http_event(device):
    return {
        "timestamp": make_timestamp(),
        "event_type": "http",
        "src_ip": device["ip"],
        "src_port": random.randint(1024, 65535),
        "dest_ip": random.choice(["142.250.80.46", "93.184.216.34"]),
        "dest_port": 80,
        "proto": "TCP",
        "http": {
            "hostname": random.choice(["google.com", "example.com", "admin-panel.local"]),
            "url": random.choice(["/", "/login", "/api/v1/data", "/wp-admin"]),
            "http_method": random.choice(["GET", "POST"]),
            "status": random.choices([200, 301, 302, 404, 500], weights=[80, 5, 5, 7, 3])[0],
            "http_user_agent": "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36",
        },
        "host": device["host"],
    }


def make_tls_event(device):
    return {
        "timestamp": make_timestamp(),
        "event_type": "tls",
        "src_ip": device["ip"],
        "src_port": random.randint(1024, 65535),
        "dest_ip": random.choice(["142.250.80.46", "93.184.216.34"]),
        "dest_port": 443,
        "proto": "TCP",
        "tls": {
            "subject": "CN=*.google.com",
            "issuerdn": "CN=GTS CA 1O1,O=Google Trust Services,C=US",
            "fingerprint": "".join(random.choices("0123456789abcdef", k=40)),
            "version": "TLS 1.3",
            "sni": random.choice(["google.com", "facebook.com", "api.nest.com"]),
        },
        "host": device["host"],
    }


def make_alert(device):
    """Generate a malicious event for a random device (10% of events)."""
    alert_template = random.choice(ALERT_TEMPLATES)
    dest = random.choice(["185.130.5.133", "45.33.32.156", "91.121.87.34"])
    return {
        "timestamp": make_timestamp(),
        "event_type": "alert",
        "src_ip": device["ip"],
        "src_port": random.randint(1024, 65535),
        "dest_ip": dest,
        "dest_port": random.choice([80, 443, 23, 4444, 53]),
        "proto": "TCP",
        "alert": {
            "action": "alert",
            "gid": 1,
            "signature_id": random.randint(2000000, 2999999),
            "rev": random.randint(1, 10),
            "severity": alert_template["severity"],
            "category": alert_template["category"],
            "signature": alert_template["sig"],
        },
        "host": device["host"],
    }


def simulate():
    """Main loop: write JSON lines to eve.json."""
    os.makedirs(os.path.dirname(EVE_PATH), exist_ok=True)

    with open(EVE_PATH, "a") as f:
        cycle = 0
        while True:
            device = random.choice(DEVICE_TEMPLATES)

            # Pick event type
            is_alert = random.random() < 0.08  # ~8% alerts

            if is_alert:
                record = make_alert(device)
            else:
                evt_type = random.choice(EVENT_TYPES)
                makers = {
                    "flow": make_flow_event,
                    "dns": make_dns_event,
                    "http": make_http_event,
                    "tls": make_tls_event,
                }
                record = makers[evt_type](device)

            f.write(json.dumps(record) + "\n")
            f.flush()
            cycle += 1

            # Print a status line every 20 events
            if cycle % 20 == 0:
                evt_label = "alert" if is_alert else record["event_type"]
                print(f"[{cycle}] Wrote {evt_label} from {device['host']} ({device['ip']}) -> {record.get('dest_ip', 'N/A')}")

            time.sleep(INTERVAL)


if __name__ == "__main__":
    simulate()
