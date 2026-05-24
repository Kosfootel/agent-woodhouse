# Vigil Host-Based Containment Architecture

## Problem Statement
When Vigil lacks router/switch administrative access, traditional network-level containment (VLAN isolation, ACL blocking) is impossible. We need an alternative architecture.

## Architecture Options

### Option A: Agent Self-Protection (Recommended)
Deploy lightweight agents to endpoints that:
1. Monitor local traffic for attack patterns
2. Self-quarantine when Vigil signals threat
3. Report local security events to Vigil

**Pros:**
- Works without router access
- Fine-grained per-host control
- Can detect insider threats

**Cons:**
- Requires agent installation on each endpoint
- Compromised agents can't self-protect
- Doesn't stop network-level attacks

### Option B: Network Gateway Mode
Deploy Vigil as a transparent bridge/gateway:
1. Physical: Vigil device sits between router and LAN
2. All traffic passes through Vigil
3. Vigil can drop/block packets

**Pros:**
- Full network visibility
- Can block at wire speed
- No agent installation needed

**Cons:**
- Single point of failure
- Requires network reconfiguration
- Hardware appliance needed

### Option C: DNS-Based Containment
Use DNS redirection for containment:
1. Vigil controls local DNS
2. Threat devices resolve malicious domains to honeypot IPs
3. Legitimate devices get real IPs

**Pros:**
- Easy to implement
- Works at application layer

**Cons:**
- Only blocks DNS-based attacks
- Bypassed with hardcoded IPs
- Doesn't stop lateral movement

### Option D: ARP Spoofing Defense
Use ARP manipulation:
1. Vigil announces itself as gateway for threat devices
2. Intercepts and drops their traffic
3. Or redirects to honeypot

**Pros:**
- Works at Layer 2
- No router needed

**Cons:**
- Detected by modern OS (ARP spoofing warnings)
- Unreliable on switched networks
- May cause network instability

## Recommended Architecture: Hybrid

**Tier 1: Agent Self-Protection**
- Deploy to critical endpoints (servers, workstations)
- Self-quarantine capability
- Report to Vigil

**Tier 2: DNS Containment**  
- Deploy to all devices via DHCP DNS settings
- Block malicious domains
- Redirect to honeypot

**Tier 3: Vigil Appliance Mode (Future)**
- Optional bridge mode for high-security deployments
- Full network control when router access available

## Implementation Plan

### Phase 1: Agent API Design

Vigil endpoints needed:

```python
# Agent polls for containment status
GET /api/agents/{agent_id}/status
Response: {
    "containment_level": "none" | "watch" | "isolate" | "quarantine",
    "threat_indicators": [...],
    "actions_required": ["drop_outbound", "alert_only"]
}

# Agent reports local security events
POST /api/agents/{agent_id}/events
Body: {
    "event_type": "suspicious_connection" | "malware_detected" | "policy_violation",
    "details": {...},
    "timestamp": "..."
}

# Agent self-quarantine confirmation
POST /api/agents/{agent_id}/quarantine
Body: {
    "reason": "...",
    "confirmed": true
}
```

### Phase 2: Agent SDK

Python/JavaScript SDK for endpoint agents:

```python
from vigil_agent import VigilAgent

agent = VigilAgent(vigil_server="192.168.50.30")
agent.start_monitoring()

# Automatic response to containment signals
@agent.on_containment_signal
async def handle_containment(level, threats):
    if level == "isolate":
        await isolate_host()  # Disable network interfaces
        await notify_user("Host isolated due to security threat")
```

### Phase 3: Vigil Coordination Logic

Vigil decides containment level per agent:
- Based on threat intelligence
- Based on behavioral anomalies  
- Based on network-wide attack patterns

## Security Considerations

1. **Agent Authentication:** Agents must authenticate to Vigil
2. **Tamper Resistance:** Agents should detect if being disabled
3. **Fail-Safe:** If Vigil unreachable, agents default to permissive mode (alert only)
4. **Recovery:** Clear path to remove containment

## Trade-offs Documented

| Approach | Router Required | Coverage | Effectiveness | Complexity |
|----------|----------------|----------|---------------|------------|
| Router ACLs | ✓ Yes | Network-wide | High | Low |
| Host Agents | ✗ No | Agent endpoints only | Medium | Medium |
| Gateway Mode | ✗ No | All traffic | High | High |
| DNS Redirection | ✗ No | DNS traffic only | Low | Low |
| ARP Spoofing | ✗ No | Layer 2 | Medium | Medium |

## Recommendation

**Immediate:** Implement Agent Self-Protection API in Vigil (Phase 1)
**Short-term:** Build reference agent implementation (Phase 2)
**Future:** Support Gateway Mode for deployments with router access
