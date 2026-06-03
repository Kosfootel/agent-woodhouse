# Vigil Home Appliance — Hardware Specification

**Version:** 0.1  
**Date:** 2026-05-06  
**Status:** Draft — Pending prototype selection

---

## Security Requirements

See `HARDWARE-SECURITY.md` for comprehensive security requirements including:
- Threat model for network-position guardian
- Supply chain security
- Boot and runtime protections
- Update security
- Physical tamper resistance
- Platform comparison (CM5 vs N100 vs Custom)
- Certification targets (Common Criteria, FIPS 140-2, ioXt)

**Security Principle:** Vigil Home must be harder to compromise than any device it protects.

## Design Principles

1. **Silent Operation:** Fanless, passively cooled
2. **Always-On:** Low power, no moving parts, 3-5 year lifespan
3. **Invisible:** Aesthetically neutral, bookshelf-friendly
4. **Future-Proof:** Over-specced for today's needs
5. **Secure:** Hardware root of trust, secure boot
6. **Unassailable:** Guardian must be unassailable (see SECURITY.md)

---

## Target Specifications

| Component | Target Spec | Notes |
|-----------|-------------|-------|
| **CPU** | ARM Cortex-A78 (8-core) or Intel N100 | Sufficient for edge ML inference |
| **RAM** | 8GB DDR4 / LPDDR4X | Headroom for future ML models |
| **Storage** | 128GB NVMe SSD + 64GB eMMC (boot) | Fast logging, redundant |
| **Network** | 2.5GbE + WiFi 6E | Handle saturated home connection |
| **Power** | 12V DC, 15W TDP max | USB-C PD compatible |
| **Form Factor** | 120mm × 120mm × 30mm | Pancake design, wall-mountable |
| **Cooling** | Passive (heatsink) | Zero moving parts |
| **Security** | TPM 2.0, Secure Boot | Hardware attestation |
| **Cost Target** | $80-120 BOM | $199-299 retail feasible |

---

## Reference Platform Options

### Option A: Raspberry Pi CM5 + Custom Carrier

**Pros:**
- Proven ecosystem
- Excellent documentation
- Low cost (~$50 module)
- Native ARM ML acceleration (Cortex-A78)

**Cons:**
- Supply chain volatility
- Custom carrier board required (8-12 week lead)
- Limited PCIe lanes

**Estimated BOM:** $65-85

### Option B: Intel N100 Mini-ITX

**Pros:**
- x86 compatibility (broader software support)
- Multiple off-the-shelf boards available
- Stronger single-thread performance

**Cons:**
- Higher power (6W TDP vs ~3W for CM5)
- Larger form factor
- More expensive ($80-120 module)

**Estimated BOM:** $95-125

### Option C: Custom ARM Board (Allwinner/Rockchip)

**Pros:**
- Lowest cost ($40-60 target)
- Full customization
- Potential for integrated WiFi/BT

**Cons:**
- 6-9 month development cycle
- Minimum order quantities (MOQ)
- Regulatory certification burden

**Estimated BOM:** $45-65 (at volume)

---

## Recommendation

**Phase 1 (POC):** Raspberry Pi CM5 + carrier board
- Fastest time to market
- Lowest technical risk
- Easy iteration

**Phase 2 (Production):** Custom ARM or Intel N100
- Cost optimization
- Supply chain stability
- Regulatory compliance

---

## Regulatory Requirements

| Certification | Jurisdiction | Cost | Timeline |
|--------------|--------------|------|----------|
| **FCC Part 15** | US | $3-5K | 4-6 weeks |
| **CE Mark** | EU | $5-8K | 6-8 weeks |
| **UL Listing** | US (optional) | $15-25K | 8-12 weeks |
| **Cyber Trust Mark** | UK (emerging) | TBD | TBD |

---

## Prototype Plan

**Week 1-2:** Order CM5 dev kit + carrier boards
**Week 3-4:** Port Vigil software stack, validate ML inference
**Week 5-6:** Thermal testing, enclosure design
**Week 7-8:** Alpha units for internal testing

---

## Open Questions

1. WiFi 6E vs WiFi 6 (6E adds 6GHz, higher cost)
2. Include Thread/Zigbee radio for smart home direct control?
3. Battery backup requirement?
4. Wall-mount vs shelf placement preference?

---

*Next: Sourcing analysis and BOM finalization*
