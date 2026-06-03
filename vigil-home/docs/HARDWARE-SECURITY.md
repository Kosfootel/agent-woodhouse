# Vigil Home — Hardware Security Requirements

**Version:** 0.1  
**Date:** 2026-05-06  
**Status:** Draft — Security-First Design

---

## Threat Model: The Guardian's Dilemma

**Vigil Home occupies the most sensitive network position possible.**

### Critical Risks

| Threat | Impact | Likelihood |
|--------|--------|------------|
| **Compromised Vigil** | Attacker sees all traffic, manipulates trust scores, disables protection | Medium |
| **Supply Chain Attack** | Malicious firmware, backdoored components, hidden radios | Medium |
| **Physical Tampering** | Device accessed in home, hardware implants, extraction | Low-Medium |
| **Network Isolation Failure** | Vigil bypassed, traffic routes around, monitoring blind | Low |
| **Update Hijacking** | Malicious OTA, rollback attack, bricking | Low |

### Security Principle

> **"The guardian must be unassailable."**

Vigil Home must be harder to compromise than any device it protects.

---

## Security Requirements by Layer

### Layer 1: Supply Chain

**Requirement SC-1:** BOM traceability
- All components sourced from authorized distributors
- No gray market, no brokers for critical components
- Certificate of authenticity for CPUs, TPMs, storage

**Requirement SC-2:** Firmware provenance
- All firmware signed by Agency.services
- Reproducible builds
- No binary blobs from untrusted sources

**Requirement SC-3:** Manufacturing security
- Assembly in US or allied nation
- Personnel background checks for line workers
- Physical security controls at facility

### Layer 2: Boot Security

**Requirement BS-1:** Hardware root of trust
- Discrete TPM 2.0 (not firmware-based fTPM)
- Secure boot with verified chain
- Measured boot (record boot state)

**Requirement BS-2:** Bootloader protections
- Signed bootloader (ED25519 or RSA-4096)
- Rollback protection (anti-downgrade)
- No unsigned recovery mode

**Requirement BS-3:** Boot integrity verification
- Self-test on each boot
- Alert if boot chain modified
- Option for user-visible integrity indicator

### Layer 3: Runtime Security

**Requirement RT-1:** Memory protection
- Full memory encryption (AES-256)
- Stack protection (canaries)
- ASLR for all processes

**Requirement RT-2:** Network isolation
- Separate network namespaces
- Unprivileged process monitoring
- Hardware firewall rules (eBPF/XDP)

**Requirement RT-3:** Minimal attack surface
- No SSH (local console only)
- No web interface on device (app-only)
- No unnecessary services

**Requirement RT-4:** Intrusion detection
- Self-monitoring for compromise
- Tamper-evident logging
- Automatic quarantine on breach detection

### Layer 4: Update Security

**Requirement UP-1:** Signed updates
- Dual-signature (Agency + independent)
- Certificate pinning
- Automatic revocation check

**Requirement UP-2:** Atomic updates
- A/B partition scheme
- Automatic rollback on failure
- User confirmation for major updates

**Requirement UP-3:** Offline update capability
- USB-based update option
- Signed update packages
- No dependency on cloud for critical patches

### Layer 5: Physical Security

**Requirement PH-1:** Tamper evidence
- Security screws (not prevention, evidence)
- Tamper-evident seals
- Internal sensors (accelerometer for movement)

**Requirement PH-2:** Side-channel resistance
- No electromagnetic leakage
- Power analysis resistant
- Physical shielding

**Requirement PH-3:** Destruction capability
- Optional: Secure wipe on tamper
- Crypto key destruction
- Configurable by user

---

## Platform-Specific Security Profiles

### Option A: Raspberry Pi CM5 + Security Hardening

**Base Security:** Moderate  
**Hardened Security:** Moderate-High

| Control | Implementation | Cost |
|---------|---------------|------|
| Secure Boot | OTP bits + signed kernel | $0 |
| TPM 2.0 | External SPI module (Infineon SLB9672) | $8 |
| Memory Encryption | Software (RAM encryption driver) | Performance hit |
| Bootloader | U-Boot with verified boot | OSS |
| Updates | Mender or RAUC (A/B) | OSS |
| Physical | Security screws + case seal | $2 |

**Security Score:** 6/10 (Acceptable for POC)  
**Production Readiness:** Low (Broadcom blobs remain)

---

### Option B: Intel N100 + Security Hardening

**Base Security:** Moderate-High  
**Hardened Security:** High

| Control | Implementation | Cost |
|---------|---------------|------|
| Secure Boot | Intel Boot Guard + UEFI Secure Boot | $0 |
| TPM 2.0 | Discrete module (preferred) or PTT | $0-8 |
| Memory Encryption | Intel TME (Total Memory Encryption) | $0 |
| Bootloader | Coreboot + Intel FSP | OSS |
| ME Mitigation | Intel ME Cleaner (HAP bit, partial disable) | OSS |
| Updates | fwupd + custom signing | OSS |
| Physical | Security screws + tamper switch | $5 |

**Security Score:** 8/10  
**Production Readiness:** High

**Critical:** Must disable Intel ME or set HAP bit. ME is attack surface.

---

### Option C: Custom ARM Board + Security Design

**Base Security:** Low (if rushed)  
**Designed Security:** Very High

| Control | Implementation | Cost |
|---------|---------------|------|
| Secure Boot | OpenTitan or Microchip secure boot | $5-15 |
| TPM 2.0 | Integrated ATECC608A or discrete | $2-5 |
| Memory Encryption | ARM TrustZone + OP-TEE | $0 |
| Bootloader | TF-A (Trusted Firmware-A) | OSS |
| Root of Trust | OpenTitan or custom HSM | $10-50 |
| Updates | SWUpdate or custom (signed) | OSS |
| Physical | Tamper-evident case + sensors | $10-20 |

**Security Score:** 9/10 (if properly implemented)  
**Production Readiness:** Medium-High (lead time)

---

## Recommended Security Architecture

### Phase 1: POC (Months 1-3)

**Platform:** Hardened Raspberry Pi CM5
- External TPM module
- Signed U-Boot + kernel
- LUKS encryption
- Security screws

**Rationale:** Fastest path, acceptable risk for POC

### Phase 2: Beta (Months 4-6)

**Platform:** Hardened Intel N100
- Coreboot firmware
- Intel ME disabled
- Discrete TPM
- Full disk encryption

**Rationale:** Balance of security and time-to-market

### Phase 3: Production (Months 7-12)

**Platform:** Custom ARM Board
- OpenTitan root of trust
- Integrated secure elements
- Supply chain verified
- Tamper-evident design

**Rationale:** Maximum security, supply chain control

---

## Security Certifications Target

| Certification | Value | Effort | Priority |
|--------------|-------|--------|----------|
| **Common Criteria EAL4+** | Government/military sales | High | Phase 3 |
| **FIPS 140-2 Level 2** | Crypto module validation | Medium | Phase 2 |
| **ioXt Alliance** | IoT security standard | Low-Medium | Phase 2 |
| **UL 2900** | Cybersecurity for IoT | Medium | Phase 2 |
| **NIST Cybersecurity Framework** | Enterprise adoption | Low | Phase 1 |

---

## Security Validation Checklist

### Before Production

- [ ] Secure boot chain verified (no bypass)
- [ ] TPM 2.0 functional and initialized
- [ ] Memory encryption enabled
- [ ] Update signing keys generated (HSM-backed)
- [ ] Physical tamper switches tested
- [ ] Side-channel analysis (power, EM)
- [ ] Penetration test (external firm)
- [ ] Firmware binary audit
- [ ] Supply chain audit
- [ ] Incident response plan

### Ongoing

- [ ] Monthly CVE review for all components
- [ ] Quarterly security updates
- [ ] Annual penetration test
- [ ] Supply chain re-verification
- [ ] Bug bounty program (Phase 2+)

---

## "Forge" Agent Integration

**Forge:** Hardware Security Evaluator Agent

**Responsibilities:**
- BOM security scoring
- Firmware vulnerability scanning
- CVE monitoring for components
- Supply chain risk assessment
- Certification gap analysis

**Deliverables:**
- Pre-production security gate review
- Quarterly security posture report
- Incident response (hardware CVEs)
- Competitive security analysis

**Trigger:**
```
/forge evaluate --bom vigil-home-bom-v0.2.json
/forge audit --release candidate-2026-08-15
/forge cve --component "Intel N100" --severity critical
```

---

## Open Questions

1. **Physical destruction:** Offer "panic button" wipe capability?
2. **Air-gapped mode:** Function without internet (reduced features)?
3. **Supply chain:** US-only components worth 40% cost premium?
4. **Bug bounty:** Run public bounty program?

---

*Next: Forge agent implementation or hardware sourcing with security requirements*
