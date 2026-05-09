# Vigil Home — Cloud/Container POC Plan

**Version:** 0.1  
**Date:** 2026-05-06  
**Status:** Draft — Software-First Architecture

---

## Philosophy: Software First, Hardware Second

**Why Cloud/Container POC wins:**
- **Zero procurement delay** — Start today, not in 2 weeks
- **Infinite test networks** — Spin up/down virtual environments at will
- **Rapid iteration** — CI/CD pipeline from day one
- **Team scaling** — Ray and Liz can contribute immediately
- **Hardware = deployment target** — Software proven before silicon

---

## Architecture: Container-Based Vigil

```
┌─────────────────────────────────────────────────────────────┐
│  Host Machine (Your MBP or Cloud Instance)                  │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  Vigil Core Container                                   ││
│  │  • Python detection engine                              ││
│  │  • SQLite database                                      ││
│  │  • REST API (FastAPI)                                   ││
│  │  • Narrative engine                                     ││
│  └────────────────────────┬────────────────────────────────┘│
│  ┌────────────────────────▼────────────────────────────────┐│
│  │  Suricata Container (IDS Mode)                          ││
│  │  • Traffic analysis                                     ││
│  │  • Emerging Threats rules                               ││
│  │  • JSON eve.json output                                 ││
│  └────────────────────────┬────────────────────────────────┘│
│  ┌────────────────────────▼────────────────────────────────┐│
│  │  Test Network (Docker Compose)                          ││
│  │  • Mock IoT devices (cameras, thermostats, etc.)        ││
│  │  • Attacker simulation (port scans, C2 beacons)       ││
│  │  • Legitimate traffic generators                        ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

---

## Two-Phase Approach

### Phase 1: Cloud/Container POC (Weeks 1-4)
**Goal:** Prove software architecture, detection rules, trust scoring

**Environment:** Docker Compose on your MacBook Pro or cloud instance

**What we build:**
- Detection engine with 25 rules
- Trust scoring algorithm
- Narrative generation
- Device fingerprinting
- Simulated containment logic

**What we defer:**
- Hardware VLAN isolation (simulated via network policies)
- Physical TPM (software HSM simulation)
- Hardware packet capture (libpcap in container)

### Phase 2: Hardware Migration (Weeks 5-8)
**Goal:** Port validated software to physical appliance

**Hardware:** N100 or CM5 (your choice, based on Phase 1 learnings)

**Migration path:**
- Export container images → Flash to hardware
- SQLite → Migration to hardware
- Simulated containment → Actual VLAN isolation
- Software HSM → Physical TPM

---

## Cloud POC Components

### 1. Vigil Core (Python + FastAPI)

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y \
    libpcap-dev \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Python requirements
COPY requirements.txt .
RUN pip install -r requirements.txt

# Application
COPY vigil/ ./vigil/
COPY config/ ./config/

EXPOSE 8000

CMD ["python", "-m", "vigil.main"]
```

**Key modules:**
- `detection.py` — Rule engine (VHR-001 to VHR-025)
- `trust.py` — Trust scoring algorithm
- `narrative.py` — Natural language generation
- `device.py` — Device fingerprinting
- `containment.py` — Simulated quarantine logic
- `api.py` — REST endpoints

### 2. Suricata Container

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  suricata:
    image: jasonish/suricata:latest
    network_mode: host  # Or specific Docker network
    volumes:
      - ./suricata/rules:/etc/suricata/rules
      - ./suricata/logs:/var/log/suricata
    cap_add:
      - NET_ADMIN
      - NET_RAW
    command: -i eth0 -c /etc/suricata/suricata.yaml

  vigil-core:
    build: ./vigil
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./suricata/logs:/var/log/suricata:ro
    environment:
      - SURICATA_EVE=/var/log/suricata/eve.json
      - DB_PATH=/app/data/vigil.db
    depends_on:
      - suricata

  vigil-ui:
    build: ./ui
    ports:
      - "3000:3000"
    environment:
      - VIGIL_API=http://vigil-core:8000

  # Test devices
  mock-camera:
    build: ./test-devices/camera
    networks:
      - iot-network
  
  mock-thermostat:
    build: ./test-devices/thermostat
    networks:
      - iot-network

  # Attacker simulation
  attacker:
    build: ./test-devices/attacker
    networks:
      - iot-network
    profiles: ["attack-testing"]

networks:
  iot-network:
    driver: bridge
```

### 3. Test Device Simulator

**Mock IoT Devices (Python scripts):**

```python
# test-devices/camera/device.py
"""Simulates a Ring-like security camera"""

import random
import time
import requests

class MockCamera:
    def __init__(self, device_id="cam-001"):
        self.device_id = device_id
        self.baseline = {
            "upload_mb_per_day": random.uniform(30, 80),
            "destinations": ["ring.com", "aws.device.ring.com"],
            "active_hours": (6, 23),
            "protocols": ["HTTPS", "MQTT"]
        }
    
    def run(self):
        while True:
            if self.is_active_hours():
                self.upload_clip()
            time.sleep(random.uniform(30, 300))
    
    def upload_clip(self):
        # Simulate video upload to cloud
        dest = random.choice(self.baseline["destinations"])
        size = random.uniform(1, 10)  # MB
        print(f"[{self.device_id}] Uploading {size:.1f}MB to {dest}")
        
    def is_active_hours(self):
        hour = time.localtime().tm_hour
        return self.baseline["active_hours"][0] <= hour <= self.baseline["active_hours"][1]

if __name__ == "__main__":
    camera = MockCamera()
    camera.run()
```

### 4. Attacker Simulation

**Attack scenarios in containers:**
- **Port scanner:** Nmap scans against test network
- **C2 beacon:** Periodic callbacks to "malicious" server
- **Credential brute-force:** Telnet/SSH attacks with default creds
- **Data exfiltration:** Unusual upload volumes

---

## Local Development Workflow

### Quick Start (5 minutes)

```bash
# Clone and start
git clone https://github.com/agency-services/vigil-home.git
cd vigil-home/poc-cloud
docker-compose up -d

# View dashboard
open http://localhost:3000

# Check API
curl http://localhost:8000/devices

# Simulate attack
docker-compose --profile attack-testing up -d attacker

# View narrative logs
docker-compose logs -f vigil-core | grep "NARRATIVE"
```

### Development Loop

```bash
# Edit detection rule
vim vigil/detection/rules/vhr_001_port_scan.py

# Reload in container
docker-compose restart vigil-core

# Test immediately
docker-compose exec attacker python /scripts/port_scan.py

# Check results
curl http://localhost:8000/alerts
```

---

## Migration to Hardware (Phase 2)

### Step 1: Container Export
```bash
# Export Vigil Core container
docker save vigil-core:latest > vigil-core.tar

# Export database
docker-compose exec vigil-core sqlite3 /app/data/vigil.db ".dump" > vigil-backup.sql
```

### Step 2: Hardware Setup
```bash
# On N100 hardware
apt-get install docker.io

# Import container
docker load < vigil-core.tar

# Restore database
sqlite3 /opt/vigil/data/vigil.db < vigil-backup.sql
```

### Step 3: Hardware-Specific Integration
```python
# hardware_adapter.py
# Replace simulated containment with real VLAN

class HardwareContainmentAdapter:
    def __init__(self):
        self.use_hardware = True  # Enable hardware VLAN
    
    def quarantine_device(self, mac_address):
        if self.use_hardware:
            # Real: Execute switch commands
            subprocess.run(["vlan-isolate", mac_address])
        else:
            # Simulated: Log only
            logger.info(f"[SIMULATED] Quarantine {mac_address}")
```

---

## Cost Comparison

| Approach | Startup Cost | Time to First Test | Hardware Required |
|----------|---------------|-------------------|-------------------|
| **CM5 First** | $150 | 1-2 weeks (shipping) | Yes |
| **N100 First** | $250 | 1-2 weeks (shipping) | Yes |
| **Cloud/Container** | $0 (use existing MBP) | Today | No |
| **Cloud + Hardware Later** | $0 now, $250 later | Today + 1 week | Eventually |

---

## Immediate Next Steps

### Today (No Purchase Required)
1. **Create directory structure**
2. **Initialize Docker Compose**
3. **Build Suricata container**
4. **Create first detection rule (VHR-001)**

### This Week
1. **Build mock device simulators** (camera, thermostat, speaker)
2. **Implement trust scoring**
3. **Build narrative engine**
4. **Create web UI**

### Hardware Decision Point (Week 2-3)
- Software proven working
- Decide: CM5 (cheap) vs. N100 (production)
- Order hardware while continuing software dev

---

## Deliverables

**Phase 1 (Cloud):**
- [ ] Working detection engine in containers
- [ ] 5 mock IoT devices
- [ ] 5 attack simulations
- [ ] Trust scoring visible in UI
- [ ] Narrative output generation

**Phase 2 (Hardware):**
- [ ] Software ported to physical appliance
- [ ] Hardware VLAN isolation working
- [ ] TPM integration
- [ ] Demo video recorded

---

## Recommendation

**Start immediately with cloud/container POC.**

Hardware becomes a deployment detail, not a dependency. We prove the concept with zero capital expenditure, then migrate to silicon once validated.

**This is how modern hardware products are built: software-first, iterate fast, deploy everywhere.**

---

**Shall I initialize the container POC structure now, sir?**
