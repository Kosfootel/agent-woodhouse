# DETECTION-RULES.md — Draft Detection Rules for Vigil Home

**Last Updated:** 2026-05-06  
**Format:** Sigma-inspired YAML + Vigil Home native fields  
**Version:** 1.0  

---

## Rule Format Legend

```yaml
title: Rule name
id: VHR-XXXX        # Vigil Home Rule ID
status: draft       # draft | test | active
description: What this rule detects
references:
  - Source URL
tags:
  - attack.ics.TAXXXX   # MITRE ATT&CK mapping
  - vigil.device_type    # Device type filter
  - vigil.threat_tier    # Whisper/Mention/Alert/Alarm

logsource:
  category: network
  protocol: [tcp, udp, dns, http, mqtt, ...]

detection:
  # Vigil Home detection logic (pseudocode)

falsepositives:
  - Known legitimate scenarios

level: low | medium | high | critical
```

---

## Table of Contents

- [Rule Categories](#rule-categories)
- [VHR-001: IoT Device Port Scanning LAN](#vhr-001-iot-device-port-scanning-lan)
- [VHR-002: IoT Device Connection to Known C2 IP](#vhr-002-iot-device-connection-to-known-c2-ip)
- [VHR-003: IoT Device Beaconing Detection](#vhr-003-iot-device-beaconing-detection)
- [VHR-004: Default Credential Login Attempt (Inbound)](#vhr-004-default-credential-login-attempt-inbound)
- [VHR-005: Router DNS Configuration Change](#vhr-005-router-dns-configuration-change)
- [VHR-006: Firmware Download from Non-Vendor Host](#hr-006-firmware-download-from-non-vendor-host)
- [VHR-007: IoT Device Sending Data During Quiet Hours](#vhr-007-iot-device-sending-data-during-quiet-hours)
- [VHR-008: Multiple Failed Auth Attempts From IoT Device](#vhr-008-multiple-failed-auth-attempts-from-iot-device)
- [VHR-009: Device Connecting to New Geographic Region](#vhr-009-device-connecting-to-new-geographic-region)
- [VHR-010: UPnP / SSDP Reflection Traffic](#vhr-010-upnp--ssdp-reflection-traffic)
- [VHR-011: MQTT Wildcard Topic Subscription from IoT Device](#vhr-011-mqtt-wildcard-topic-subscription-from-iot-device)
- [VHR-012: Encrypted Traffic to Dynamic DNS Domain](#vhr-012-encrypted-traffic-to-dynamic-dns-domain)
- [VHR-013: Outbound Connection to Stratum (Mining) Protocol](#vhr-013-outbound-connection-to-stratum-mining-protocol)
- [VHR-014: Device Traffic Volume Anomaly](#vhr-014-device-traffic-volume-anomaly)
- [VHR-015: New Device Detected](#vhr-015-new-device-detected)
- [VHR-016: Trust Score Degradation Alert](#vhr-016-trust-score-degradation-alert)
- [VHR-017: Multiple IoT Beacons Simultaneously](#vhr-017-multiple-iot-beacons-simultaneously)
- [VHR-018: SMB Brute Force From Local Device](#vhr-018-smb-brute-force-from-local-device)
- [VHR-019: Camera Streaming to Non-Vendor Destination](#vhr-019-camera-streaming-to-non-vendor-destination)
- [VHR-020: DNS Tunnel Detection (High Entropy)](#vhr-020-dns-tunnel-detection-high-entropy)
- [VHR-021: Device Firmware Version Reverted](#vhr-021-device-firmware-version-reverted)
- [VHR-022: EV Charger / Solar Inverter Anomalous Activity](#vhr-022-ev-charger--solar-inverter-anomalous-activity)
- [VHR-023: Unknown Device with Aggressive Scanning](#vhr-023-unknown-device-with-aggressive-scanning)
- [VHR-024: Duplicate SSID (Evil Twin Detection)](#vhr-024-duplicate-ssid-evil-twin-detection)
- [VHR-025: CleanSL8 Authorized Agent Deviation](#vhr-025-cleansl8-authorized-agent-deviation)

---

## Rule Categories

| Category | Rules | Tier |
|----------|-------|------|
| Network Reconnaissance | VHR-001, VHR-023 | Alert |
| C2 Detection | VHR-002, VHR-003, VHR-017 | Alert/Alarm |
| Credential Attacks | VHR-004, VHR-008 | Alert |
| Configuration Tampering | VHR-005, VHR-021 | Alarm |
| Data Exfiltration | VHR-007, VHR-009, VHR-019, VHR-020 | Alert/Alarm |
| Protocol Abuse | VHR-010, VHR-011, VHR-012 | Mention/Alert |
| Malicious Activity | VHR-006, VHR-013 | Alert/Alarm |
| Behavioral Anomaly | VHR-014, VHR-022 | Mention/Alert |
| Trust & Device Mgmt | VHR-015, VHR-016 | Whisper/Alert |
| Physical/Proximity | VHR-024 | Mention |
| Authorized Agents | VHR-025 | Alarm |

---

## VHR-001: IoT Device Port Scanning LAN

```yaml
title: IoT Device Port Scanning LAN
id: VHR-001
status: active
description: >
  Detects when an IoT device conducts port scanning against
  other hosts on the local network. IoT devices should not
  network scan — this indicates compromise or malware.
references:
  - https://attack.mitre.org/techniques/T1046/
  - https://attack.mitre.org/versions/v18/tactics/ics/TA0112/
tags:
  - attack.ics.TA0112
  - attack.enterprise.T1046
  - vigil.threat_tier.alert
  - vigil.lateral_movement

logsource:
  category: network
  protocol: [tcp, udp]

detection:
  # Count unique destination IP:port pairs from source device
  # over a 60-second sliding window
  time_window: 60s
  # Threshold: 10+ unique destination IP:port pairs
  threshold:
    unique_destinations: 10
  # Exclude known hubs/routers (allow scanning)
  exclude_hubs: true
  # IoT devices should have no scanning baseline
  # If a device's scanning baselines exceeds expected,
  # treat as anomalous

  condition: >
    count(distinct(dest_ip:dest_port)) > 10
    AND device.type IN ['camera', 'tv', 'speaker', 'lock',
                        'thermostat', 'light', 'plug', 'sensor',
                        'appliance', 'unknown']
    AND device NOT IN whitelisted_scanners
    AND not authenticated_as('CleanSL8')

falsepositives:
  - Smart hubs/bridges conducting device discovery
  - Security cameras with UPnP discovery enabled
  - CleanSL8 authenticated agents (handled by VHR-025)

level: high
narrative: >
  "{device_name} is scanning other devices on your network.
  This is unusual behavior. I've restricted its network access
  for your safety."

containment: auto_contain
```

---

## VHR-002: IoT Device Connection to Known C2 IP

```yaml
title: IoT Device Connection to Known C2 IP
id: VHR-002
status: active
description: >
  Detects outbound connections from any IoT device to
  known Command & Control IP addresses from threat intelligence feeds.
references:
  - https://sslbl.abuse.ch/
  - https://feodotracker.abuse.ch/
  - https://www.cisa.gov/known-exploited-vulnerabilities-catalog
tags:
  - attack.ics.TA0115
  - attack.enterprise.T1071
  - vigil.threat_tier.alarm

logsource:
  category: network
  protocol: [tcp, udp]

detection:
  # C2 IP list updated from abuse.ch, CISA KEV, MISP
  c2_blocklist: abuse.ch/cisa/misp
  # Connection to any IP in blocklist
  condition: dest_ip IN c2_blocklist
  # TLS: also check JA3 fingerprint against SSLBL
  condition_enhanced: dest_ip IN c2_blocklist OR ja3_hash IN sslbl_ja3

falsepositives:
  - False positives extremely rare if C2 list well-maintained

level: critical
narrative: >
  "I detected {device_name} connecting to a known malicious
  server. This device may be compromised. I've quarantined it
  immediately."

containment: quarantine
```

---

## VHR-003: IoT Device Beaconing Detection

```yaml
title: IoT Device Beaconing Detection
id: VHR-003
status: draft
description: >
  Detects periodic outbound connections (beaconing) from IoT devices
  to the same destination, indicative of C2 communication.
references:
  - https://attack.mitre.org/versions/v18/tactics/ics/TA0115/
tags:
  - attack.ics.TA0115
  - vigil.threat_tier.alert

logsource:
  category: network
  protocol: [tcp]

detection:
  # Analyze connection timestamps to single destination over 4h window
  time_window: 4h
  # Beacon detection algorithm
  condition: >
    connections_to_single_dest > 20
    AND connection_interval_std_dev < 0.3 * mean_interval
    AND NOT is_legitimate_cloud_service(dest_ip)
    AND NOT is_known_update_server(dest_ip)

falsepositives:
  - Legitimate cloud polling (e.g., Nest every 5 min)
  - DNS/NTP queries (should be excluded)
  - MQTT persistent connections

level: high
narrative: >
  "{device_name} is regularly contacting {dest_ip} at
  predictable intervals. This pattern can indicate a hidden
  command channel. I'm watching closely."

containment: alert_and_monitor
```

---

## VHR-004: Default Credential Login Attempt (Inbound)

```yaml
title: Default Credential Login Attempt (Inbound)
id: VHR-004
status: active
description: >
  Detects inbound login attempts using known default credentials
  against IoT devices. Strong indicator of active exploitation attempt.
references:
  - https://github.com/ihebski/DefaultCreds-cheat-sheet
tags:
  - attack.ics.TA0107
  - attack.enterprise.T1110
  - vigil.threat_tier.alert

logsource:
  category: network
  protocol: [telnet, ssh, http, https]

detection:
  # Monitor telnet/SSH/HTTP auth attempts to IoT devices
  # from both WAN and LAN sources
  auth_failure_window: 300s
  condition: >
    username_password IN default_credential_database
    AND auth_result = 'failed'
    # Rate: 3+ attempts with default creds in 5 min
    AND count(attempts) > 2

  # Successful login with default creds is immediate ALARM
  condition_alarm: >
    username_password IN default_credential_database
    AND auth_result = 'success'

falsepositives:
  - Homeowner testing device configuration
  - Automated device registration (rare)

level: high (failure), critical (success)
narrative_failure: >
  "Someone is trying to log into {device_name} using factory
  default passwords. This is how IoT devices get compromised."

narrative_success: >
  "ALARM: Someone successfully logged into {device_name}
  using default credentials. I've quarantined this device."

containment: auto_contain (on success)
```

---

## VHR-005: Router DNS Configuration Change

```yaml
title: Router DNS Configuration Change
id: VHR-005
status: active
description: >
  Detects changes to the home router's DNS server configuration.
  DNS hijacking is a common attack — redirecting traffic to
  malicious servers.
references:
  - https://attack.mitre.org/techniques/T1556/
tags:
  - attack.ics.TA0111
  - vigil.threat_tier.alarm

logsource:
  category: network
  protocol: [dns]

detection:
  # Baseline: known DNS servers (ISP, 8.8.8.8, 1.1.1.1, etc.)
  baselined_dns_servers: []
  
  # Detect DHCP offer with different DNS
  condition_dhcp: >
    dhcp.dns_server NOT IN baselined_dns_servers
    AND not homeowner_initiated_change

  # Detect DNS query routing to non-standard resolver
  condition_dns: >
    dns.dest_ip NOT IN [known_resolver_1, known_resolver_2]
    AND dns.dest_ip != baselined_gateway
    AND not device_is_vpn_client

falsepositives:
  - Homeowner changing DNS (Pi-hole, NextDNS, etc.)
  - VPN client routing DNS
  - Guest network separate resolver

level: critical
narrative: >
  "Your router is directing DNS traffic to {new_dns_server}
  instead of its usual servers. This could mean someone
  changed the settings. I'll alert you each time this happens."

containment: notify_and_log (config change cannot be blocked by Vigil)
```

---

## VHR-006: Firmware Download from Non-Vendor Host

```yaml
title: Firmware Download from Non-Vendor Host
id: VHR-006
status: draft
description: >
  Detects when an IoT device downloads a firmware image from
  a host that is not its known vendor update server.
references:
  - https://attack.mitre.org/techniques/T1195/
tags:
  - attack.ics.TA0107
  - attack.enterprise.T1195
  - vigil.threat_tier.alarm

logsource:
  category: network
  protocol: [http, https, tftp]

detection:
  # Each device type has known update servers mapped
  expected_update_servers: device.specific
  
  condition: >
    bytes_transferred > 500KB
    AND device_connected_to_update_server = false
    AND NOT dest_ip IN expected_update_servers
    AND (
      http.response.content_type IN ['application/octet-stream',
                                     'application/x-firmware',
                                     'application/x-bin']
      OR url_contains_extension(['.bin', '.img', '.fw', '.rom'])
      OR protocol = 'tftp'
    )

falsepositives:
  - Vendor migrating to new update infrastructure
  - Device downloading large media file (unlikely from IoT)
  - Multi-CDN delivery for updates

level: critical
narrative: >
  "{device_name} is downloading firmware from {dest_ip},
  which is not its regular update server. This could be a
  malicious firmware injection attempt. I've blocked the download."

containment: block_connection
```

---

## VHR-007: IoT Device Sending Data During Quiet Hours

```yaml
title: IoT Device Sending Data During Quiet Hours
id: VHR-007
status: draft
description: >
  Detects unusual network activity from IoT devices during
  quiet hours (02:00-06:00 local) that does not match
  expected update or maintenance patterns.
tags:
  - vigil.threat_tier.mention

logsource:
  category: network

detection:
  quiet_hours: 02:00-06:00
  # Each device has expected quiet-hours activity
  # e.g., cameras may send timelapse, but speakers should not
  
  condition: >
    current_time IN quiet_hours
    AND NOT is_scheduled_update_activity
    AND activity_type NOT IN expected_quiet_activity
    AND data_sent > 100KB  # Small pings/heartbeats are normal

falsepositives:
  - Scheduled firmware updates (check OTA schedule)
  - Timezone changes
  - User manually interacting with device

level: medium
narrative: >
  "{device_name} sent data to {dest_ip} at 3 AM. This is
  unusual for this device. It could be an automated update,
  but I'm noting it for your awareness."
```

---

## VHR-008: Multiple Failed Auth Attempts From IoT Device

```yaml
title: Multiple Failed Auth Attempts From IoT Device
id: VHR-008
status: active
description: >
  Detects when an IoT device attempts multiple failed
  authentications against another device on the LAN.
  Indicates compromised device attempting lateral movement.
references:
  - https://attack.mitre.org/versions/v18/tactics/ics/TA0113/
tags:
  - attack.ics.TA0113
  - vigil.threat_tier.alarm

logsource:
  category: network
  protocol: [ssh, http, smb, telnet]

detection:
  time_window: 300s
  condition: >
    source IN iot_devices
    AND auth_result = 'failed'
    AND count(failures) > 5
    AND source != dest  # Not self-test
    AND not authenticated_as('CleanSL8')

falsepositives:
  - Misconfigured device trying to connect to wrong service
  - Home automation testing device connectivity

level: high
narrative: >
  "{source_name} is attempting to log into {dest_name} 
  and failing repeatedly. This device may be compromised
  and trying to spread to other devices."

containment: auto_contain_source
```

---

## VHR-009: Device Connecting to New Geographic Region

```yaml
title: Device Connecting to New Geographic Region
id: VHR-009
status: draft
description: >
  Detects when an IoT device establishes connections to
  IP addresses in a country/region it has never connected
  to before.
tags:
  - vigil.threat_tier.mention

logsource:
  category: network
  protocol: [tcp]

detection:
  # Maintain geographic baseline per device
  # GeoIP lookup on destinations
  
  condition: >
    dest_country NOT IN device.geo_baseline
    AND dest_ip NOT IN device.cloud_baseline_bypass
    AND not device_type IN ['tv', 'speaker']
    # TVs and speakers legitimately connect to many CDNs globally

falsepositives:
  - CDN load-balancing (TVs, streaming devices — exclude)
  - Vendor adding new cloud regions
  - VPN/proxy usage (legitimate)

level: medium
narrative: >
  "{device_name} is communicating with a server in {country},
  which is unusual for this device. It's never done this before."
```

---

## VHR-010: UPnP / SSDP Reflection Traffic

```yaml
title: UPnP/SSDP Reflection Traffic
id: VHR-010
status: draft
description: >
  Detects SSDP reflection patterns — where an IoT device
  is used in a DDoS amplification attack.
references:
  - https://www.us-cert.gov/ncas/alerts/TA14-017A
tags:
  - attack.ics.TA0117
  - vigil.threat_tier.alert

logsource:
  category: network
  protocol: [udp]
  port: 1900

detection:
  # Normal: devices send small M-SEARCH queries
  # Anomalous: device sending large NOTIFY responses to WAN IPs
  
  condition: >
    protocol = 'SSDP'
    AND response_size > 1000
    AND dest_ip NOT IN local_subnet
    # DDoS reflection: source IP is the amplifier
    AND rate_of_responses_per_min > 10

falsepositives:
  - Router announcing services to WAN (known, can baseline)
  - UPnP proxies

level: high
narrative: >
  "{device_name} is sending unusually large UPnP responses
  to external addresses. This can be used in DDoS attacks.
  I'm restricting its UPnP access."

containment: block_ssdp
```

---

## VHR-011: MQTT Wildcard Topic Subscription from IoT Device

```yaml
title: MQTT Wildcard Topic Subscription from IoT Device
id: VHR-011
status: draft
description: >
  Detects IoT devices subscribing to MQTT wildcard topics,
  which allows the device to receive ALL messages on the broker.
  Indicates reconnaissance or data harvesting.
references:
  - https://www.hivemq.com/blog/mqtt-security-fundamentals/
tags:
  - vigil.threat_tier.alarm

logsource:
  category: network
  protocol: [mqtt]

detection:
  condition: >
    mqtt.packet_type = 'SUBSCRIBE'
    AND (
      mqtt.topic_filter = '#'
      OR mqtt.topic_filter CONTAINS '+'
    )
    AND device.type IN ['camera', 'thermostat', 'light',
                        'plug', 'sensor', 'unknown']

falsepositives:
  - MQTT dashboard/bridge devices (SmartThings, HomeAssistant)
  - MQTT broker itself

level: high
narrative: >
  "{device_name} just subscribed to ALL MQTT topics on your
  network. This device should only see its own data.
  I'm blocking its broker access."

containment: block_mqtt
```

---

## VHR-012: Encrypted Traffic to Dynamic DNS Domain

```yaml
title: Encrypted Traffic to Dynamic DNS Domain
id: VHR-012
status: draft
description: >
  Detects TLS connections from IoT devices to dynamic DNS
  domains. IoT devices should connect to stable vendor
  domains, not DDNS services (often used by C2 infrastructure).
references:
  - https://attack.mitre.org/techniques/T1568/
tags:
  - attack.ics.TA0111
  - vigil.threat_tier.alert

logsource:
  category: network
  protocol: [dns, tls]

detection:
  ddns_suffixes:
    - duckdns.org
    - no-ip.com
    - dyn.com
    - dyndns.org
    - dy.fi
    - afraid.org
    - freedns.afraid.org
    - changeip.com
    - dhis.org
    - dnspod.com
  
  condition: >
    dns.query ENDS_WITH ddns_suffixes
    AND device.type NOT IN ['tv', 'speaker']
    # TVs occasionally use DDNS for P2P streaming features

falsepositives:
  - Homeowner running personal services on DDNS
  - Some vendor IoT platforms use DDNS for device discovery

level: high
narrative: >
  "{device_name} is connecting to {dns_query}, a dynamic
  DNS address. Cybercriminals often use dynamic DNS for
  hidden command servers. I'm restricting this connection."

containment: block_dns
```

---

## VHR-013: Outbound Connection to Stratum (Mining) Protocol

```yaml
title: Outbound Connection to Stratum (Mining) Protocol
id: VHR-013
status: active
description: >
  Detects IoT devices connecting to cryptocurrency mining
  pool servers on standard Stratum protocol ports.
  Indicates cryptojacking malware on the device.
tags:
  - vigil.threat_tier.alarm

logsource:
  category: network
  protocol: [tcp]

detection:
  mining_pool_ports:
    - 3333  # Stratum
    - 4444  # Stratum backup
    - 5555  # Stratum backup
    - 8332  # Bitcoin RPC
    - 8333  # Bitcoin network
    - 9340  # Litecoin
    - 14444 # XMRig default
  
  # Known mining pool IPs/domsins
  known_mining_pools:
    - pool.minexmr.com
    - xmrpool.eu
    - nanopool.org
    - supportxmr.com
  
  condition: >
    dest_port IN mining_pool_ports
    OR dns.query MATCHES known_mining_pools
    AND device.type IN iot_devices

falsepositives:
  - Extremely rare for IoT devices to legitimately mine

level: critical
narrative: >
  "{device_name} is connecting to a cryptocurrency mining
  pool. This device has been infected with cryptojacking
  malware. I've quarantined it."

containment: quarantine
```

---

## VHR-014: Device Traffic Volume Anomaly

```yaml
title: Device Traffic Volume Anomaly
id: VHR-014
status: draft
description: >
  Detects when an IoT device's traffic volume significantly
  deviates from its established baseline.
tags:
  - vigil.threat_tier.mention

logsource:
  category: network

detection:
  # Baseline: running 14-day average
  # Anomaly: >5 sigma from rolling average
  
  condition: >
    current_hourly_volume > 5 * rolling_24h_std_dev
    OR current_hourly_volume > 10 * rolling_7d_mean

falsepositives:
  - Large firmware update
  - Camera recording event (motion detection spike)
  - TV streaming 4K content

level: medium
narrative: >
  "{device_name}'s network usage just jumped significantly
  above normal — {percentage}% increase. This could indicate
  data exfiltration or a firmware download. I'm investigating."
```

---

## VHR-015: New Device Detected

```yaml
title: New Device Detected
id: VHR-015
status: active
description: >
  Detects a new device joining the network for the first time.
  Triggers device fingerprinting, initial trust score assignment,
  and baseline establishment.
tags:
  - vigil.threat_tier.whisper

logsource:
  category: device_discovery

detection:
  # Triggered on ARP, DHCP ACK, or first-seen traffic
  condition: mac_address NOT IN device_inventory

falsepositives:
  - None (this is a legitimate event)

level: low
narrative: >
  "I've detected a new device on your network:
  {device_name} ({device_type}). 
  I'm learning its normal behavior patterns.
  Initial trust score: {trust_score}"
```

---

## VHR-016: Trust Score Degradation Alert

```yaml
title: Trust Score Degradation Alert
id: VHR-016
status: active
description: >
  Alerts when a device's trust score drops below configured
  thresholds. Escalates through the communication tiers.
tags:
  - vigil.threat_tier.whisper  # base, escalates

detection:
  # Trust score is a composite of:
  # - Behavioral anomalies
  # - Known vulnerabilities (CVE match)
  # - New connection patterns
  # - Baseline deviations

  # Thresholds map to communication tiers
  condition_whisper: trust_score BETWEEN 0.6 AND 0.8
  condition_mention: trust_score BETWEEN 0.4 AND 0.6
  condition_alert: trust_score BETWEEN 0.2 AND 0.4
  condition_alarm: trust_score < 0.2

narrative_whisper: |
  "{device_name}'s trust score has decreased to {score}.
  Nothing alarming yet — I'll keep watching."

narrative_mention: |
  "I've noticed some unusual patterns from {device_name}.
  Trust score: {score}\nReasons: {reason_list}\n
  I'm keeping an eye on things."

narrative_alert: |
  "{device_name} is behaving suspiciously.\n
  Trust score: {score}\n
  Reasons: {reason_list}\n
  I've restricted its network access pending your review."

narrative_alarm: |
  "URGENT: {device_name} triggered a security concern.\n
  Trust score: {score}\n
  Reasons: {reason_list}\n
  Device is isolated pending your decision."

containment: auto_contain (if alert or alarm)
```

---

## VHR-017: Multiple IoT Beacons Simultaneously

```yaml
title: Multiple IoT Beacons Simultaneously
id: VHR-017
status: draft
description: >
  Detects when multiple IoT devices begin beaconing to the
  same C2 server at the same time. Indicates coordinated
  botnet activation.
references:
  - https://attack.mitre.org/versions/v18/tactics/ics/TA0117/
tags:
  - attack.ics.TA0117
  - vigil.threat_tier.alarm

logsource:
  category: network

detection:
  time_window: 60s
  condition: >
    count(distinct(sources)) > 3
    AND same_destination = true
    AND NOT is_legitimate_cloud_service(dest)
    AND is_beaconing_pattern(dest)

falsepositives:
  - Multiple devices updating firmware simultaneously
  - Multi-device sync feature (e.g., Philips Hue broadcast)

level: critical
narrative: >
  "Multiple devices on your network are simultaneously 
  communicating with {dest_ip}. This coordinated activity
  is a strong sign of botnet infection. I'm containing all
  affected devices."

containment: auto_contain_all
```

---

## VHR-018: SMB Brute Force From Local Device

```yaml
title: SMB Brute Force From Local Device
id: VHR-018
status: active
description: >
  Detects when a local IoT device attempts multiple SMB
  authentication failures against a NAS or Windows machine.
  Indicates ransomware propagation or lateral movement.
references:
  - https://attack.mitre.org/techniques/T1110/
tags:
  - attack.enterprise.T1110
  - vigil.threat_tier.alarm

logsource:
  category: network
  protocol: [smb]

detection:
  time_window: 300s
  condition: >
    smb.command IN ['SessionSetup']
    AND smb.ntlmssp.status = 'STATUS_LOGON_FAILURE'
    AND count(failures) > 3
    AND source IN iot_devices

falsepositives:
  - Misconfigured network drive mount
  - Genuine user from IoT device (unlikely)

level: high
narrative: >
  "{source_name} is trying to access your NAS/computer using
  the wrong password. This device may have ransomware or
  other malware. I've restricted its access."

containment: block_smb
```

---

## VHR-019: Camera Streaming to Non-Vendor Destination

```yaml
title: Camera Streaming to Non-Vendor Destination
id: VHR-019
status: active
description: >
  Detects when a security camera or doorbell sends video/audio
  streams to destinations other than its known vendor cloud.
  Possible privacy violation or data exfiltration.
tags:
  - vigil.threat_tier.alarm

logsource:
  category: network
  protocol: [rtsp, rtp, hls, webrtc, http]

detection:
  # Build baseline of known camera destinations
  # Expected: vendor cloud (ring.com, wyze.com, etc.)
  # Local: NVR IP on LAN
  
  expected_stream_destinations:
    - cloud: [known_vendor_domains]
    - local: [nvr_ips]
  
  condition: >
    stream_protocol IN ['RTSP', 'RTP', 'HLS', 'WebRTC']
    AND data_direction = 'outbound'
    AND dest NOT IN expected_stream_destinations
    AND bytes_transferred > 1MB

falsepositives:
  - Multi-vendor camera setup (some cameras support multiple clouds)
  - Camera firmware update (large binary, not stream)

level: critical
narrative: >
  "Your camera {device_name} is sending video to {dest_ip},
  which is not its usual destination. Your video feed may
  be compromised. I've blocked this connection."

containment: block_stream
```

---

## VHR-020: DNS Tunnel Detection (High Entropy)

```yaml
title: DNS Tunnel Detection (High Entropy)
id: VHR-020
status: draft
description: >
  Detects potential DNS tunneling by analyzing DNS query
  subdomain entropy. High-entropy subdomains at regular
  intervals indicate data exfiltration.
references:
  - https://attack.mitre.org/techniques/T1572/
tags:
  - attack.enterprise.T1572
  - vigil.threat_tier.alert

logsource:
  category: network
  protocol: [dns]

detection:
  # Shannon entropy calculation on subdomain labels
  # Normal IoT: short, predictable subdomains
  # Tunneling: long, random-looking subdomains
  # Also: high volume, regular intervals, unusual record types
  
  entropy_threshold: 4.5  # Shannon entropy
  time_window: 300s
  
  condition: >
    entropy(subdomain) > entropy_threshold
    AND length(fqdn) > 40  # Long FQDN
    AND count(queries) > 20  # Volume
    AND record_type IN ['TXT', 'NULL', 'MX']  # Unusual types for IoT
  
  # Also detect high NXDOMAIN rate (exfiltration via NX)
  condition_dns_tunnel: >
    nxdomain_rate > 0.3  # >30% of queries result in NXDOMAIN
    AND count(queries) > 50

falsepositives:
  - Some CDN dynamic DNS (Akamai, Cloudflare)
  - Apple Push Notification Service (APNS)
  - Very rare for IoT devices

level: high
narrative: >
  "{device_name} is sending unusual DNS queries that could
  be tunneling data out of your network. I'm monitoring
  closely and will block if pattern continues."

containment: block_dns_if_persistent
```

---

## VHR-021: Device Firmware Version Reverted

```yaml
title: Device Firmware Version Reverted
id: VHR-021
status: draft
description: >
  Detects when an IoT device's firmware version decreases
  (rollback/downgrade). Firmware downgrade attacks remove
  security patches and re-enable previously fixed CVEs.
references:
  - https://attack.mitre.org/techniques/T1473/
  - https://attack.mitre.org/versions/v18/tactics/ics/TA0109/
tags:
  - attack.ics.TA0109
  - attack.ics.TA0111
  - vigil.threat_tier.alarm

logsource:
  category: firmware_management

detection:
  # Track firmware version per device
  # Version stored in device fingerprint
  condition: >
    device.firmware_version < previous_firmware_version
    AND time_since_first_seen > 7d  # Skip initial learning
    AND not firmware_update_authorized

falsepositives:
  - Vendor reverting a faulty update
  - Manual rollback by homeowner (should be authorized)

level: high
narrative: >
  "{device_name}'s firmware was reverted to an older version.
  Downgrading firmware can remove security protections.
  Did you authorize this change?"
```

---

## VHR-022: EV Charger / Solar Inverter Anomalous Activity

```yaml
title: EV Charger / Solar Inverter Anomalous Activity
id: VHR-022
status: draft
description: >
  Detects anomalous behavior from smart energy devices
  (EV chargers, solar inverters). These devices are an
  emerging attack surface per the 2025 IoT report.
references:
  - https://www.bitdefender.com/en-us/blog/hotforsecurity/bitdefender-and-netgear-2025-iot-security-landscape-report
tags:
  - vigil.threat_tier.alert

logsource:
  category: network

detection:
  # Solar inverter patterns
  # Expected: periodic energy reporting (5-15 min)
  # Anomalous: Modbus commands from unknown source
  
  condition_inverter: >
    device.type = 'solar_inverter'
    AND (dest_port = 502 AND dest NOT IN known_modbus_monitors)  # Modbus
    OR (protocol = 'modbus' AND function_code IN ['write_multiple',
                                                   'write_single'])
  
  condition_charger: >
    device.type = 'ev_charger'
    AND (
      dest_port = 443 AND NOT dest IN known_charger_clouds
      OR charge_control_command AND NOT homeowner_initiated
    )

falsepositives:
  - Solar installer monitoring panels
  - Utility company demand response program

level: high (energy control), medium (monitoring)
narrative: >
  "Your {device_type} received unexpected control commands
  from {source_ip}. Energy system controls should only
  come from authorized sources. I'm investigating."
```

---

## VHR-023: Unknown Device with Aggressive Scanning

```yaml
title: Unknown Device with Aggressive Scanning
id: VHR-023
status: active
description: >
  Detects when an unrecognized device begins aggressive
  network scanning immediately after connecting.
  Strong indicator of adversarial device.
tags:
  - vigil.threat_tier.alarm

logsource:
  category: device_discovery
  protocol: [arp, tcp, icmp]

detection:
  new_device_window: 300s (5 min after first seen)
  
  condition: >
    device.age < 300s
    AND device.status = 'unknown'
    AND (
      arp_scan_rate > 10/min
      OR syn_scan_rate > 5/min
      OR connections_to_management_ports > 3
    )

falsepositives:
  - Network troubleshooting tool
  - New security appliance (should be whitelisted)

level: critical
narrative: >
  "An unknown device joined your network and immediately
  started scanning it. This is not normal behavior for
  a standard device. I've quarantined it for your safety."

containment: quarantine
```

---

## VHR-024: Duplicate SSID (Evil Twin Detection)

```yaml
title: Duplicate SSID (Evil Twin Detection)
id: VHR-024
status: draft
description: >
  Detects when a new Wi-Fi access point announces the same
  SSID as the home network. Indicates a potential evil twin
  or rogue AP attack.
references:
  - https://attack.mitre.org/techniques/T1557/
tags:
  - attack.enterprise.T1557
  - vigil.threat_tier.mention

logsource:
  category: wireless

detection:
  # Monitor 802.11 beacon frames for duplicate SSIDs
  known_bssid: registered_router
  known_ssid: home_network
  
  condition: >
    wifi.ssid = known_ssid
    AND wifi.bssid != known_bssid
    AND wifi.signal_strength != expected_level

falsepositives:
  - Mesh node or extender joining network
  - Neighbor with same SSID (rare)

level: medium
narrative: >
  "I detected another Wi-Fi access point using your home
  network's name. This could be a fake access point designed
  to capture your traffic. I'm noting the signal location."
  
containment: notify_only (limited wireless visibility)
```

---

## VHR-025: CleanSL8 Authorized Agent Deviation

```yaml
title: CleanSL8 Authorized Agent Deviation
id: VHR-025
status: draft
description: >
  Detects when a CleanSL8 authenticated agent deviates from
  its authorized behavior profile. Authorized agents have
  strict scope — any deviation triggers immediate containment.
references:
  - PRODUCT-REQUIREMENTS.md (FR-6.6)
  - CONTAINMENT-ACTUATION.md (CleanSL8 Exception Pattern)
tags:
  - vigil.threat_tier.alarm
  - vigil.cleansl8

logsource:
  category: cleansl8_agent

detection:
  # CleanSL8 agents are pre-authenticated via Shibboleth
  # They have an authorized capability profile
  
  authorized_capabilities:
    - port_scanning (expected)
    - device_inventory (expected)
    - baseline_extraction (expected)
  
  unauthorized_capabilities:
    - data_exfiltration
    - credential_testing
    - firewall_config_change
    - firmware_modification
    - large_data_download (>100MB)
  
  condition: >
    agent_authenticated = true
    AND authorized_until > current_time
    AND (
      activity NOT IN authorized_capabilities
      OR activity IN unauthorized_capabilities
    )

falsepositives:
  - Agent version update changing behavior protocols
  - Should be extremely rare

level: critical
narrative: >
  "A verified CleanSL8 agent attempted an unauthorized action
  — {activity}. The agent's authorization has been revoked
  and it has been contained pending investigation."

containment: revoke_and_contain
```

---

## Rule Testing & Validation

### Test Your Rules
```bash
# For Sigma-format rules
sigma validate rule.yml
sigma check -c config.yaml rule.yml

# For Suricata conversion
sigma convert -t suricata -o rule.rules rule.yml

# Test with sample pcap
suricata -r sample_iot_mirai.pcap -S rule.rules -l /tmp/
```

### Recommended Test Dataset Sources
1. **Mirai pcap samples** — Available via various malware repositories
2. **Botnet traffic captures** — Stratosphere IPS project
3. **CIC IoT dataset** — Canadian Institute for Cybersecurity
4. **Your own Vigil Home test network** — Real-world validation crucial

---

## Rule Maintenance

| Task | Frequency | Owner |
|------|-----------|-------|
| Review false positive reports | Weekly | Detection engineering |
| Update C2 blocklist | Daily+ | Automated feed |
| Update DDNS domain list | Monthly | Threat intel |
| Rebaseline traffic volumes | Weekly | Automated |
| Add new device types | As discovered | Device inventory |
| Calibrate beaconing detection | Monthly | ML pipeline |
| Audit CleanSL8 auth patterns | Per integration | Security review |
