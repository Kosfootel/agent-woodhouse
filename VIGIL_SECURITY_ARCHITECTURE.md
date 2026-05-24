# Vigil Security Architecture Report

**Date:** 2026-05-24  
**Branch:** hermes/vigil-playbooks-models  
**Report Author:** Woodhouse (Subagent)  

---

## Executive Summary

This report documents the implementation of **active network scanning** capabilities and the **host-based containment architecture** for Vigil. When router administrative access is unavailable, Vigil must employ alternative methods for device discovery and threat containment.

---

## Part 1: Active Scanning Implementation

### What Was Implemented

A new module `app/active_discovery.py` provides TCP SYN port scanning and OS fingerprinting capabilities:

- **TCP Port Scanning:** Scans common ports (22, 80, 443, 445, 3389, 5900, 8080, 8000, 9000, 161, 139) across the entire 192.168.50.0/24 network
- **Banner Grabbing:** Attempts to capture service banners for additional identification
- **OS Fingerprinting:** Infers operating systems from port combinations and banners
- **Device Type Inference:** Classifies devices as servers, workstations, IoT, etc.

### Scanning Results

**Test Run (2026-05-24):**
```
Discovery complete. ARP: 12, Multi-protocol: 2, Active: 13, Total in DB: 16
```

**Active Scanning Discoveries:**
| IP Address | Open Ports | OS Guess | Device Type |
|------------|------------|----------|-------------|
| 192.168.50.1 | 80, 139, 445 | Windows | workstation |
| 192.168.50.2 | 80 | Unknown | web_device |
| 192.168.50.22 | 22, 80, 3389 | Windows | workstation |
| 192.168.50.23 | 22 | Linux/Unix | server |
| 192.168.50.24 | 22, 445 | Linux/macOS | workstation |
| 192.168.50.25 | 22, 445 | Linux/macOS | workstation |
| 192.168.50.30 | 22, 80, 8000, 8080 | Linux | server |
| 192.168.50.32 | 22, 80, 3389 | Windows | workstation |
| 192.168.50.65 | 80 | Unknown | web_device |
| 192.168.50.76 | 445 | Windows | workstation |
| 192.168.50.77 | 22, 445 | Linux/macOS | workstation |
| 192.168.50.192 | 80, 443 | Unknown | web_device |
| 192.168.50.201 | 22, 445 | Linux/macOS | workstation |

**Key Finding:** Active scanning found 13 devices, including **2 new devices** (192.168.50.76 and 192.168.50.77) that were not visible via ARP or passive discovery methods.

### Technical Details

**Async Implementation:**
- Uses Python `asyncio` for concurrent scanning of 254 IPs
- Semaphore-controlled concurrency (20 concurrent connections)
- Timeout per host: 2 seconds
- Total scan time: ~2-3 minutes for entire /24 network

**Integration Points:**
- Added `import_active_scan_results()` function in `setup.py`
- Runs after ARP and multi-protocol discovery
- Creates devices with `trust_score=40.0` (lower than passive discovery)
- Metadata includes open ports, OS guess, and confidence level

---

## Part 2: Host-Based Containment Architecture

### Problem Addressed

Without router administrative access, traditional network containment (VLAN isolation, ACL blocking) is unavailable. Vigil needs alternative mechanisms to protect the network.

### Architecture Options Analyzed

| Approach | Router Required | Coverage | Effectiveness | Complexity | Recommendation |
|----------|----------------|----------|---------------|------------|----------------|
| Router ACLs | Yes | Network-wide | High | Low | Not applicable |
| Host Agents | No | Agent endpoints only | Medium | Medium | **Primary** |
| Gateway Mode | No | All traffic | High | High | Future |
| DNS Redirection | No | DNS traffic only | Low | Low | Secondary |
| ARP Spoofing | No | Layer 2 | Medium | Medium | Not recommended |

### Recommended Hybrid Architecture

**Tier 1: Agent Self-Protection (Immediate)**
- Deploy lightweight agents to critical endpoints
- Agents self-quarantine based on Vigil signals
- Report local security events to Vigil

**Tier 2: DNS-Based Containment (Short-term)**
- Redirect malicious domains to honeypot IPs
- Deploy via DHCP DNS settings
- Limited to DNS-dependent attacks

**Tier 3: Vigil Appliance Mode (Future)**
- Optional transparent bridge deployment
- Full network control when router access available
- Hardware appliance required

### Agent API Design (Phase 1)

```python
# Agent polls for containment status
GET /api/agents/{agent_id}/status
Response: {
    "containment_level": "none" | "watch" | "isolate" | "quarantine",
    "threat_indicators": [...],
    "actions_required": ["drop_outbound", "alert_only"]
}

# Agent reports security events
POST /api/agents/{agent_id}/events
Body: {
    "event_type": "suspicious_connection" | "malware_detected",
    "details": {...},
    "timestamp": "..."
}

# Self-quarantine confirmation
POST /api/agents/{agent_id}/quarantine
Body: {"reason": "...", "confirmed": true}
```

### Security Considerations

1. **Authentication:** Agents must authenticate to Vigil using certificates/tokens
2. **Tamper Resistance:** Agents should detect and alert if being disabled
3. **Fail-Safe:** Default to permissive mode if Vigil unreachable
4. **Recovery:** Documented process for removing containment

---

## Part 3: Implementation Roadmap

### Immediate (This Sprint)
- [x] Active scanning module implemented
- [x] TCP port scanning operational
- [x] OS fingerprinting working
- [x] Integration with discovery workflow complete

### Short-term (Next 2-4 Weeks)
- [ ] Implement Agent Self-Protection API endpoints
- [ ] Design agent authentication mechanism
- [ ] Build reference Python agent implementation
- [ ] Document agent installation process

### Medium-term (Next 1-3 Months)
- [ ] DNS-based containment implementation
- [ ] Agent tamper-resistance features
- [ ] Agent health monitoring
- [ ] Automated containment decision engine

### Future (3+ Months)
- [ ] Vigil Appliance Mode (bridge/gateway)
- [ ] Hardware appliance certification
- [ ] Enterprise deployment automation

---

## Part 4: Trade-off Analysis

### Discovery Methods Comparison

| Method | Speed | Coverage | Accuracy | Intrusiveness | Completeness |
|--------|-------|----------|----------|---------------|--------------|
| ARP Table | Fast | Local subnet only | High (MAC-based) | None | Medium |
| Multi-Protocol | Medium | Broadcast domains | Medium | Low | Low |
| Active Scan | Slow | Configurable ranges | High (port-based) | Medium | **High** |
| Router API | Fast | Entire network | High | None | High (if available) |

**Recommendation:** Use all methods in sequence - ARP first, then multi-protocol, then active scan for remaining gaps.

### Containment Methods Comparison

| Method | Effectiveness | Deployability | Maintainability | Cost | Recommendation |
|--------|---------------|---------------|-----------------|------|----------------|
| Host Agents | Medium | High | Medium | Low | **Primary** |
| DNS Redirection | Low | High | High | Low | Secondary |
| Gateway Mode | High | Low | Low | High | Future |
| ARP Spoofing | Medium | Low | Low | Low | Avoid |

---

## Conclusion

The active scanning implementation successfully addresses the device discovery gap when router access is unavailable. Testing confirmed discovery of 2 additional devices not visible through passive methods.

The host-based containment architecture provides a viable alternative to network-level controls, with a clear implementation path from agent-based protection to full gateway mode.

**Next Steps:**
1. Monitor active scanning performance in production
2. Begin Phase 1 of agent API implementation
3. Validate containment decisions with agent telemetry

---

**Files Modified:**
- `backend/app/active_discovery.py` (new)
- `backend/app/routers/setup.py` (modified)

**Documents Created:**
- `VIGIL_HOST_CONTAINMENT_SPEC.md`
- `VIGIL_SECURITY_ARCHITECTURE.md`

**Commit:** `18b19f8` - "feat: add active port scanning for device discovery"
