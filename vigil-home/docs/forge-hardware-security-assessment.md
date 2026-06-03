# Forge Initial Hardware Security Assessment — Vigil Home

**Date:** 2026-05-06  
**Author:** Forge (Hardware Security Evaluator Agent)  
**Version:** 1.0  
**Status:** Initial Assessment

---

## Executive Summary

Three hardware platforms are under evaluation for Vigil Home: Raspberry Pi CM5 (BCM2712), Intel N100 (Alder Lake-N), and a custom ARM board. Each presents a distinct security profile with different risk vectors, certification paths, and supply chain implications.

**Security ranking (current state):**
1. **Intel N100 (hardened)** — Best security posture if ME is disabled and discrete TPM is used
2. **Custom ARM Board** — Highest potential ceiling, longest timeline, supply chain control
3. **Raspberry Pi CM5** — Fastest POC, but Broadcom blobs and no TrustZone limit production-readiness

---

## 1. Platform Security Track Record

### 1.1 Raspberry Pi CM5 / BCM2712

**Score:** 6/10 (acceptable for POC, limited for production)

**Strengths:**
- Secure boot via OTP bits + RSA key verification (documented for CM4/BCM2711, architecture continues to BCM2712)
- Signed bootloader chain (ROM → EEPROM → bootloader → kernel)
- Rollback-prevention: OTP bits can revoke old ROM keys
- EEPROM write-protect available

**Critical weaknesses:**
- **No TrustZone / Secure OS** — The BCM2712, like its predecessors, lacks hardware security enclave support. No trusted execution environment.
- **No hardware crypto accelerator** — SHA256 verification is done in software (adds ~3.5s to boot)
- **JTAG access** — Can be disabled in OTP, but must be explicitly configured
- **VideoCore GPU blob** — The proprietary GPU firmware runs on the same SoC as the application. This blob is closed-source, un-auditable, and has ring-0-like access to memory. This is the single largest security concern.
- **No memory encryption** — No hardware TME or similar. Must rely on software encryption (LUKS) with performance penalty.
- **Broadcom supply chain** — Single-source for SoC. Supply chain volatility (historical shortage experience).

**CVE history:** BCM2712-specific CVEs are minimal because the chip is relatively new (~late 2023). However, the Linux kernel vulnerabilities that affect Raspberry Pi are numerous:
- **Multiple Ubuntu kernel CVEs (2025–2026):** USN-7585-7, USN-7922-4, USN-7909-5, USN-7990-6 — all affect Raspberry Pi kernel packages
- **CVE-2025-22011:** Linux kernel vulnerability (kernel 6.x)
- **eMMC CQE freezes:** Hardware issue causing I/O freezes on CM5 (open issue #6512)
- Bootloader firmware has regular EEPROM releases (last: 2026-02), indicating active patching but also ongoing bugs

### 1.2 Intel N100 / Alder Lake-N

**Score:** 8/10 (strongest option today with proper hardening)

**Strengths:**
- **Intel TME (Total Memory Encryption)** — Hardware-level AES-256 memory encryption at no extra cost
- **Intel Boot Guard + UEFI Secure Boot** — Mature, well-audited secure boot chain
- **Coreboot support** — Replace proprietary UEFI with open-source firmware on Topton N100 boards
- **ME can be mitigated** — HAP bit / AltMeDisable flag on Alder Lake (though the flag descriptor location changed on ADL, it's still workable)
- **Mature ecosystem** — Years of CVE handling, microcode updates, coordinated disclosure
- **Discrete TPM 2.0 via SPI** — Standard form factor, verified by community
- **No VideoCore-style black box** — No secondary opaque co-processor with full memory access

**Weaknesses:**
- **Intel ME (Management Engine)** — Proprietary ARM coprocessor running MINIX-based firmware with full system access. HAP bit only partially disables it (it enters a low-power state, not fully removed).
- **Microcode vulnerabilities** — Regular microcode patches required (INTEL-SA-01166, SA-01097, SA-01396)
- **CSME firmware vulnerabilities** — CVE-2025-20037 (TOCTOU race condition affecting CSME firmware < 16.1.38.2676) is the latest; Intel has a long history of CSME flaws
- **Power consumption** — 6W TDP vs ~3W for ARM, requires larger passive cooling
- **Boot Guard whitelist** — Intel controls the key signing; you cannot add your own keys to the boot chain without OEM support

**CVE history for N100/Alder Lake-Specific:**

| Advisory | Date | Severity | Type | Notes |
|----------|------|----------|------|-------|
| INTEL-SA-01166 | 2025-02 | Medium (5.3) | DoS | Improper FSM in hardware logic. Affects Alder Lake. Microcode fix available. |
| INTEL-SA-01097 | 2024-09 | Medium (5.3) | DoS | Improper FSM. Affects Alder Lake. |
| INTEL-SA-01396 | 2026-02 | Low (1.8) | Escalation of Privilege | Microcode flow vulnerability. Affects Alder Lake. |
| INTEL-SA-01280 / CVE-2025-20037 | 2025 | High | CSME TOCTOU | Local privilege escalation via race condition in CSME firmware < 16.1.38.2676 |
| INTEL-SA-01153 | 2025.1 IPU | Various | Processor | 2025.1 IPU — affects Alder Lake |
| INTEL-SA-01228 | 2025.1 IPU | Various | 13th/14th Gen | Does not affect N100 (Alder Lake-N) |

**Key insight:** The N100's CVEs are overwhelmingly "local privileged user can cause DoS" at Medium severity. No remote code execution CVEs in silicon for Alder Lake-N. The real concern is the Intel ME/CSME attack surface — but for a home appliance that doesn't use AMT, this is a controlled risk.

### 1.3 Custom ARM Board (Allwinner/Rockchip)

**Score:** 9/10 (potential — depends on implementation quality)

**Strengths:**
- Full design control over security architecture
- Can integrate OpenTitan or Microchip secure boot controller
- Can choose a SoC with TrustZone (most modern ARM SoCs)
- No proprietary management engine
- Full supply chain visibility
- Can eliminate binary blobs entirely

**Weaknesses:**
- **6-9 month minimum development timeline**
- **Regulatory certification burden** — FCC, CE from scratch (~$15-30K total)
- **Minimum order quantities** — 500-1000 units minimum for cost-effective pricing
- **Rockchip/Allwinner BSP quality varies** — Rockchip BSP quality on Linux is improving but still trails Raspberry Pi
- **BootROM vulnerabilities** — Several Allwinner and Rockchip SoCs have had OTP/bypass vulnerabilities in the past
- **Driver maturity** — Network and security driver maturity trails x86 significantly

---

## 2. Top 3 CVEs Affecting Each Option

### 2.1 Raspberry Pi CM5 / BCM2712

| # | CVE/Issue | Type | Severity | Impact |
|---|-----------|------|----------|--------|
| 1 | **USN-7922-4 / USN-7990-6** (2025–2026) | Linux kernel (Raspberry Pi) | Varies (High) | Multiple kernel vulnerabilities — privilege escalation, DoS, info leak. Patched in Ubuntu kernel. |
| 2 | **VideoCore GPU blob** (ongoing) | Proprietary firmware | **Architectural** | Closed-source co-processor with full memory access running on the same SoC. No CVEs assigned (not auditable). This is the defining security limitation of the platform. |
| 3 | **CVE-2025-22011** (2025) | Linux kernel | High | Vulnerability in kernel 6.x affecting Raspberry Pi. Details in NVD. |

**Additional concern:** eMMC CQE freeze issue (#6512) is a hardware reliability problem, not a security CVE, but affects device availability.

### 2.2 Intel N100 / Alder Lake-N

| # | CVE/Advisory | Type | CVSS | Impact |
|---|-------------|------|------|--------|
| 1 | **CVE-2025-20037** (INTEL-SA-01280) | CSME firmware TOCTOU | High | Local privilege escalation via race condition in CSME firmware. Affects versions < 16.1.38.2676. Requires local privileged access to exploit. |
| 2 | **Intel ME / CSME attack surface** (ongoing) | Proprietary firmware | **Architectural** | The Management Engine runs a MINIX-based OS with full system access. Multiple historical CVEs (CVE-2017-5689, CVE-2019-0165, etc.). Mitigated by HAP bit + proper firmware updates. |
| 3 | **INTEL-SA-01166** (2025-02) | Hardware logic DoS | 5.3 Medium | Improper finite state machine in hardware. Requires local privileged access. Microcode fix available. |

**Notes:**
- The N100-specific CVEs are all Medium severity. The highest risks come from the ME/CSME architecture, which affects all Intel platforms.
- Intel has been responsive with microcode patches (2024.3 IPU, 2024.4 IPU, 2025.1 IPU, 2026.1 IPU).
- No remote code execution CVEs have been found in Alder Lake-N hardware.

### 2.3 Custom ARM Board (SoC-dependent)

| # | CVE/Issue | Type | Severity | Impact |
|---|-----------|------|----------|--------|
| 1 | **BootROM vulnerabilities** (SoC-dependent) | Mask ROM bugs | Varies | Historically, Allwinner (e.g., A64 bootROM bypass) and Rockchip SoCs have had mask-level flaws that cannot be patched. Requires careful SoC selection. |
| 2 | **BSP/driver quality** | Software | Varies | Allwinner/Rockchip BSP for Linux includes proprietary blob drivers. Quality and security patch velocity vary significantly by vendor. |
| 3 | **No existing secure boot maturity** | Architecture | **Design risk** | Unlike the CM5 (documented secure boot) or N100 (Boot Guard), a custom board requires designing and validating the secure boot chain from scratch. Higher implementation risk. |

---

## 3. TPM Vendor Assessment

### 3.1 Discrete TPM 2.0 Vendor Comparison

| Vendor | Model | CC EAL | FIPS 140-2/3 | Side-Channel Resistance | Security Notes |
|--------|-------|--------|-------------|------------------------|----------------|
| **Infineon** | SLB9672 (OPTIGA) | EAL4+ (AVA_VAN.5) | Level 2 ✓ | SPA, DPA, DFA resistant | **Recommended.** Well-documented, good community support, SPI interface. PQC-protected firmware updates. |
| **Infineon** | SLB9670 | EAL4+ | Level 2 ✓ | — | Older, being phased out. |
| **Nuvoton** | NPCT7xx | EAL4+ | Level 2 ✓ | ECDSA timing leakage found (CVE-2020-25082) | Good support but TPMScan found timing leakage in ECC algorithms. |
| **STMicro** | ST33KTPM | EAL4+ | FIPS 140-3 ✓ | DPA/SPA protected | Newest entry. FIPS 140-3 certified. Good option but newer ecosystem. |
| **Intel PTT** | fTPM (firmware) | None | None | CSME-bound | **Not recommended for Vigil.** fTPM shares attack surface with ME. |

### 3.2 Recommendation: Infineon SLB9672

The **Infineon SLB9672** is the best choice for Vigil Home:

- **CC EAL4+ with AVA_VAN.5** — The highest assurance level commonly available for discrete TPMs. AVA_VAN.5 means the design was evaluated against high attack potential.
- **FIPS 140-2 Level 2 certified** — Active certification for FW 17/27 (BSI-DSZ-CC-1179-V5-2025). Newer firmware also targets FIPS 140-3.
- **Post-quantum cryptography support** — XMSS-based firmware update mechanism for future-proofing.
- **Broad ecosystem support** — Well-integrated with Linux tpm2-tools, U-Boot, coreboot.
- **SPI interface** — Standard, well-understood bus. The CM5 and N100 both support SPI TPM modules.
- **Good supply availability** — Available from Mouser, Digi-Key, authorized distributors (~$8-12/unit at volume).

**Key certifications confirmed (2026):**
| Certificate | ID | Valid Until | Level |
|-------------|-----|-------------|-------|
| Common Criteria (DE) | BSI-DSZ-CC-1113-V6-2025 | Active (2025) | EAL4+, AVA_VAN.5 |
| Common Criteria (DE) | BSI-DSZ-CC-1179-V5-2025 | Active (2025) | EAL4+, AVA_VAN.5 (FW v17.x) |
| FIPS 140-2 | Certificate #4347 | Active | Level 2 |
| FIPS 140-2 (FW v17/27) | Certificate #4468 | Active | Level 2 |

**Nuvoton alternative:** If Infineon supply is constrained, Nuvoton NPCT7xx is acceptable, but note the TPMScan-identified timing leakage in ECC algorithms (even in CC EAL4+ certified versions — highlighting the limits of CC evaluation).

**Avoid:** Intel PTT (firmware TPM) — shares the Management Engine attack surface.

### 3.3 Sourcing Vendors

| Component | Preferred Vendor | Alternate | Notes |
|-----------|-----------------|-----------|-------|
| **Infineon SLB9672** | Mouser Electronics | Digi-Key, Arrow | $8-12/unit, SPI interface |
| **Infineon SLB9673** | Mouser Electronics | Digi-Key | Newer (FW v17/v27), FIPS 140-2 L2 |
| **Nuvoton NPCT7xx** | Digi-Key | Avnet | Good second source |
| **ST33KTPM** | STMicro direct | Mouser | FIPS 140-3, newer to market |

---

## 4. FIPS 140-2 Level 2 Validation Path

### 4.1 What FIPS 140-2 Level 2 Covers

FIPS 140-2 Level 2 requires:
- **Role-based authentication** — The cryptographic module must authenticate operators
- **Tamper-evident coatings or seals** — Physical evidence of tampering
- **Cryptographic algorithms** — Must use FIPS-approved algorithms (AES, RSA, SHA-2/3, HMAC, DRBG)
- **Key management** — Secure key generation, storage, and zeroization
- **Operational environment** — Limited operating system with security policy

### 4.2 Key insight: TPM covers the crypto module

For Vigil Home, the TPM itself handles the cryptographic module requirements. The **Infineon SLB9672 is already FIPS 140-2 Level 2 certified.** This means:
- The cryptographic boundary is the TPM chip itself
- We don't need to certify the entire appliance as a FIPS module
- We only need to demonstrate that the TPM is used in a FIPS-compliant manner

### 4.3 Path Options

| Approach | Effort | Cost | Timeline | Complexity |
|----------|--------|------|----------|------------|
| **A. Leverage existing TPM cert** | Low | ~$20-50K for integration testing | 3-6 months | Low — Use SLB9672 FIPS-certified module as-is |
| **B. Certify the appliance** | High | ~$150-300K | 9-18 months | High — Full module validation for entire Vigil Home |
| **C. Software crypto module** | Medium | ~$100-200K | 6-12 months | Medium — Certify software cryptography (OpenSSL FIPS module) |

**Recommended approach: Option A** — Leverage the SLB9672's existing FIPS 140-2 Level 2 certification. The TPM handles: key generation, storage, RNG, and cryptographic operations. The appliance software uses the TPM as its cryptographic module, which is already validated.

### 4.4 Step-by-Step Path for Option A

1. **Select SLB9672 FW revision** (v15.22.16832.00 or v17.24.19084.00) with active FIPS cert
2. **Submit request** to NIST CMVP for dependency on existing certificate
3. **Document integration** — Show that all cryptographic operations route through the TPM
4. **Write security policy** — Describe operational environment, key management, roles
5. **Perform integration testing** — FIPS-approved lab validates correct usage
6. **Submit for FIPS 140-2 validation** (Level 2) — Leverages existing TPM cert
7. **Receive validation** (estimated 3-6 months)

### 4.5 Transition to FIPS 140-3

**Note:** NIST stopped accepting new FIPS 140-2 submissions after September 2024. Existing certificates remain valid, but **new validations must be FIPS 140-3**. The Infineon SLB9672 also targets FIPS 140-3 certification (in process).

For Vigil Home production (Phase 3), target FIPS 140-3 directly:
- FIPS 140-3 Level 2 requires: role-based auth, tamper evidence, non-invasive attack mitigation
- The SLB9672 (and ST33KTPM) are already targeting FIPS 140-3
- Cost: ~$50-80K for integration
- Timeline: ~6-12 months

---

## 5. Recommended Platform Path

### Phase 1 — POC (Now): **Raspberry Pi CM5 + Infineon SLB9672**

- Fastest time to market (weeks, not months)
- External SPI TPM for basic hardware root of trust
- U-Boot verified boot for signed kernel
- LUKS encryption for storage
- Accept the VideoCore blob risk for POC
- **Cost:** ~$65-85 BOM + $8 TPM
- **Security level:** Adequate for POC, not for production

**Critical hardening for CM5 POC:**
- Disable JTAG in OTP
- Enable signed boot (OTP provisioning)
- Use external TPM (not VideoCore-based)
- Disable unused boot modes in BOOT_ORDER
- Encrypt rootfs with LUKS
- Remove `pi` user, disable password auth

### Phase 2 — Beta (3-6 months): **Intel N100 + Coreboot + Infineon SLB9672**

- Coreboot replaces UEFI (Topton N100 has working coreboot)
- HAP bit set to minimize ME activity
- Intel TME provides hardware memory encryption at no cost
- Discrete TPM for hardware root of trust
- Regular microcode updates from Intel
- **Cost:** ~$95-125 BOM + $8 TPM
- **Security level:** Strong. Best available on current hardware.

**Critical hardening for N100:**
- Configure coreboot with HAP (AltMeDisable) flag
- Use discrete TPM (not PTT/fTPM)
- Regular microcode updates (subscribe to Intel SA notifications)
- UEFI Secure Boot with custom keys
- Enable Intel TME (Total Memory Encryption)
- Disable AMT in firmware
- Full disk encryption (LUKS)
- Lock flash descriptor to prevent unauthorized firmware writes

### Phase 3 — Production (6-12 months): **Custom ARM Board**

- Full control over security architecture
- Integrated OpenTitan or Microchip secure boot controller
- No proprietary blobs
- Supply chain verified
- Tamper-evident design for FIPS
- **Cost:** ~$45-65 BOM at volume
- **Security level:** Highest potential (if implemented correctly)

**Hardening for custom ARM:**
- OpenTitan for hardware root of trust
- TF-A (Trusted Firmware-A) for secure boot
- OP-TEE for trusted execution
- Discrete TPM or integrated secure element
- Memory encryption via ARMv8.4 TME (if SoC supports)
- Physical tamper sensors (accelerometer + switch)

---

## 6. Certification Roadmap

| Certification | Phase | Timeline | Cost (est.) | Priority |
|---------------|-------|----------|-------------|----------|
| **FIPS 140-2 L2** (via SLB9672) | Phase 1 (POC) | 3-6 months | $20-50K | Medium |
| **FIPS 140-3 L2** | Phase 2 (Beta) | 6-12 months | $50-80K | High |
| **Common Criteria EAL4+** | Phase 3 (Production) | 12-18 months | $200-500K | Low (govt. sales only) |
| **ioXt** | Phase 2 (Beta) | 3-6 months | $10-25K | High |
| **UL 2900** | Phase 2 (Beta) | 6-9 months | $30-60K | Medium |

---

## 7. Ongoing CVE Monitoring Recommendations

### Establish a CVE monitoring pipeline:

1. **Subscribe to Intel Security Advisories** — https://www.intel.com/content/www/us/en/security-center/default.html
2. **Monitor Ubuntu USN for Raspberry Pi kernels** — USN-* series for arm64
3. **Track NVD for Infineon SLB9672** — Currently no critical CVEs, but check regularly
4. **Monitor coreboot.org security issues** — For Phase 2 coreboot deployment
5. **Automated tooling:** Set up `cve-bin-tool` or similar in CI to scan for known CVEs in the image

### Forge deliverables schedule:
| Deliverable | Frequency | Next Due |
|-------------|-----------|----------|
| Weekly CVE digest | Weekly | 2026-05-13 |
| Supply chain risk assessment | Monthly | 2026-06-06 |
| Security posture report | Quarterly | 2026-08-06 |
| Incident response | As-needed | N/A |
| Pre-production security gate | Per-release | TBD |

---

## 8. Open Questions for Discussion

1. **Is the VideoCore blob risk acceptable for Phase 1 POC?** For a guardian device, an un-auditable co-processor with full memory access on the same SoC is a genuine concern, even for POC.
2. **Intel ME: How much is "disabled" acceptable?** HAP bit leaves ME in a low-power idle state. For a home appliance that doesn't use AMT, this is likely acceptable, but purists will want full removal.
3. **FIPS 140-3 vs FIPS 140-2:** Since NIST stopped accepting new 140-2 submissions in Sept 2024, we should target FIPS 140-3 directly for Phase 2.
4. **Coreboot N100 board selection:** The Topton N100 has verified coreboot support, but we need to confirm SPI flash region is unlocked on production boards. Protectli VP3210 is another option.
5. **Custom ARM SoC selection:** Rockchip RK3588 or RK3568? Allwinner H618? Each has different TrustZone support and blob profiles. Requires deeper evaluation in Phase 3 planning.

---

*Report generated by Forge, Hardware Security Evaluator Agent.*  
*Next deliverable: Weekly CVE digest — due 2026-05-13.*
