"""
Vigil Device Classifier
=======================
Identifies IoT device type from:
  - MAC OUI (Organisationally Unique Identifier, first 24 bits)
  - Behavioural signature matching (traffic patterns, protocols, ports)

MAC OUI Lookup
--------------
Built-in OUI database for common consumer device manufacturers.
For the POC this is embedded; in production it would load from
Wireshark's OUI database or a network-provided list.

Behavioural Signature Matching
-------------------------------
Each device type has a "behavioural fingerprint" — typical traffic
volumes, protocols, port ranges, and activity times.  The classifier
scores how well a device's observed behaviour matches each type.

API
---
    DeviceClassifier(oui_db=None, signatures=None)
        .classify(mac, features=None) -> list[Classification]
        .oui_vendor(mac) -> str | None
        .match_signature(features) -> list[Classification]
        .known_devices() -> dict
"""

import re
from dataclasses import dataclass, field
from typing import Any


# ── data structures ────────────────────────────────────────────────

@dataclass
class Classification:
    device_type: str
    label: str           # human-friendly label
    confidence: float    # 0.0–1.0
    source: str          # "oui" | "signature" | "combined"
    vendor: str | None = None


# ── built-in OUI database (common consumer IoT vendors) ────────────

# Format: OUI prefix (lowercase, no colons) -> vendor name
BUILTIN_OUI: dict[str, str] = {
    # Amazon / Ring / Eero
    "ac63be": "Amazon",
    "88f977": "Amazon",
    "e04f43": "Amazon",
    "a8da0c": "Amazon",
    "18bb0c": "Ring (Amazon)",
    "b066b6": "Eero (Amazon)",
    # Google / Nest
    "a45a1c": "Google",
    "e8abf3": "Google",
    "e0b7c1": "Google",
    "08b512": "Nest (Google)",
    "f4f5d8": "Nest (Google)",
    "18d6c7": "Google",
    # Apple
    "f0f61c": "Apple",
    "10fc3e": "Apple",
    "a4d1d2": "Apple",
    "bc9288": "Apple",
    # Samsung
    "bc5ff4": "Samsung",
    "b0e9f3": "Samsung",
    "3c6e0d": "Samsung",
    "5c4968": "Samsung",
    # Philips (Hue)
    "ecb5fa": "Philips (Hue)",
    "001788": "Philips (Hue)",
    # TP-Link / Kasa
    "dcefca": "TP-Link",
    "50c7bf": "TP-Link",
    "e84e06": "TP-Link",
    # Belkin / Wemo
    "ec1a59": "Belkin (Wemo)",
    "b2c9f8": "Belkin (Wemo)",
    # Sonos
    "b8e937": "Sonos",
    "e8f1b0": "Sonos",
    "78b26f": "Sonos",
    # Wyze
    "8cf5a3": "Wyze",
    # Lutron
    "3c2c99": "Lutron",
    "8b9c6e": "Lutron",
    # Ubiquiti
    "74acb9": "Ubiquiti",
    "b0aa36": "Ubiquiti",
    # Xiaomi
    "f0d5bf": "Xiaomi",
    "8cdeb8": "Xiaomi",
    "48a2e6": "Xiaomi",
    # Tuya / Smart Life
    "b05b1f": "Tuya",
    "2c2f8c": "Tuya",
    # ESP (ESP32/ESP8266 — often custom IoT)
    "24d7b9": "Espressif (ESP)",
    "30aea4": "Espressif (ESP)",
    "7cdfa1": "Espressif (ESP)",
    "cc50e3": "Espressif (ESP)",
    # Raspberry Pi Foundation
    "b827eb": "Raspberry Pi",
    "dca632": "Raspberry Pi",
    "e4f5f6": "Raspberry Pi",
    # Intel (often in smart displays / PCs)
    "f82e79": "Intel",
    "bcaec5": "Intel",
    # Realtek (smart TVs, IP cameras)
    "ec08c0": "Realtek",
    "001e8c": "Realtek",
    "0050b6": "Realtek",
}

# ── behavioural signatures ─────────────────────────────────────────

_Protocol = str  # e.g. "MQTT", "HTTP", "CoAP", "mDNS"
_PortRange = tuple[int, int]


@dataclass
class BehavioralSignature:
    device_type: str
    label: str
    vendor_prefixes: list[str] = field(default_factory=list)
    typical_protocols: list[str] = field(default_factory=list)
    typical_ports: list[_PortRange] = field(default_factory=list)
    typical_traffic_kbps: tuple[float, float] = (0.0, 0.0)   # (min, max)
    typical_connections_hour: tuple[int, int] = (0, 0)       # (min, max)
    active_hours: tuple[int, int] = (0, 24)                  # (start, end) UTC
    is_hub: bool = False        # bridges devices (e.g. Hue bridge)
    needs_hub: bool = False     # requires a hub/bridge

    def score(self, features: dict[str, Any]) -> tuple[float, list[str]]:
        """Calculate a match score and list matching signals.

        Returns (confidence [0-1], matching_reasons).
        """
        matches = []
        total_weight = 0.0
        earned = 0.0

        # 1. Protocol match (weight: 3)
        proto = features.get("protocols", [])
        if proto and self.typical_protocols:
            total_weight += 3.0
            matching = [p for p in proto if p in self.typical_protocols]
            if matching:
                earned += 3.0 * (len(matching) / len(self.typical_protocols))
                matches.append(f"protocols matched: {matching}")

        # 2. Port match (weight: 2)
        ports = features.get("ports", [])
        if ports and self.typical_ports:
            total_weight += 2.0
            matches_port = any(
                lo <= p <= hi for p in ports for (lo, hi) in self.typical_ports
            )
            if matches_port:
                earned += 2.0
                matches.append("ports matched")

        # 3. Traffic volume (weight: 2)
        kbps = features.get("traffic_kbps")
        lo, hi = self.typical_traffic_kbps
        if kbps is not None and hi > 0:
            total_weight += 2.0
            if lo <= kbps <= hi:
                earned += 2.0
                matches.append("traffic volume in range")

        # 4. Connection rate (weight: 1.5)
        conn = features.get("connections_hour")
        clo, chi = self.typical_connections_hour
        if conn is not None and chi > 0:
            total_weight += 1.5
            if clo <= conn <= chi:
                earned += 1.5
                matches.append("connection rate in range")

        # 5. Active hours (weight: 1)
        active_hour = features.get("active_hour")
        if active_hour is not None:
            total_weight += 1.0
            s, e = self.active_hours
            if s <= active_hour <= e:
                earned += 1.0
                matches.append(f"active in operating window ({s:02d}:00-{e:02d}:00)")

        # 6. Hub-related logic (weight: 1)
        is_hub_device = features.get("is_hub", False)
        total_weight += 1.0
        if self.is_hub and is_hub_device:
            earned += 1.0
            matches.append("identified as hub device")
        elif self.needs_hub and not features.get("has_hub", True):
            earned -= 1.0
            matches.append("missing required hub")

        confidence = earned / total_weight if total_weight > 0 else 0.0
        return (min(confidence, 1.0), matches)


# ── built-in signatures ────────────────────────────────────────────

BUILTIN_SIGNATURES: list[BehavioralSignature] = [
    # --- Smart speakers / displays ---
    BehavioralSignature(
        device_type="smart_speaker",
        label="Smart Speaker / Display",
        vendor_prefixes=["Google", "Amazon", "Apple", "Sonos"],
        typical_protocols=["HTTPS", "HTTP", "MQTT", "mDNS", "DNS"],
        typical_ports=[(443, 443), (80, 80), (5353, 5353)],
        typical_traffic_kbps=(5, 200),
        typical_connections_hour=(10, 200),
        active_hours=(6, 23),
    ),
    # --- IP cameras ---
    BehavioralSignature(
        device_type="camera",
        label="IP Camera / Video Doorbell",
        vendor_prefixes=["Wyze", "Ring", "Amazon", "Google"],
        typical_protocols=["RTSP", "HTTP", "HTTPS", "MQTT", "STUN"],
        typical_ports=[(554, 554), (80, 80), (443, 443)],
        typical_traffic_kbps=(50, 5000),
        typical_connections_hour=(50, 500),
        active_hours=(0, 24),
    ),
    # --- Smart plugs / switches ---
    BehavioralSignature(
        device_type="smart_plug",
        label="Smart Plug / Switch",
        vendor_prefixes=["TP-Link", "Belkin", "Tuya", "Kasa"],
        typical_protocols=["MQTT", "HTTPS", "CoAP"],
        typical_ports=[(8883, 8883), (443, 443), (5683, 5683)],
        typical_traffic_kbps=(0.1, 50),
        typical_connections_hour=(2, 60),
        active_hours=(0, 24),
    ),
    # --- Smart locks ---
    BehavioralSignature(
        device_type="smart_lock",
        label="Smart Lock",
        vendor_prefixes=["Ring", "Amazon"],
        typical_protocols=["BLE", "Z-Wave", "HTTPS", "MQTT"],
        typical_ports=[(443, 443)],
        typical_traffic_kbps=(0.1, 10),
        typical_connections_hour=(1, 30),
        active_hours=(0, 24),
    ),
    # --- Smart bulbs / lighting ---
    BehavioralSignature(
        device_type="smart_light",
        label="Smart Light / Bulb",
        vendor_prefixes=["Philips", "Lutron", "Tuya", "Xiaomi"],
        typical_protocols=["Zigbee", "Z-Wave", "MQTT"],
        typical_ports=[(443, 443)],
        typical_traffic_kbps=(0.1, 5),
        typical_connections_hour=(1, 20),
        active_hours=(0, 24),
    ),
    # --- Hubs / bridges ---
    BehavioralSignature(
        device_type="hub",
        label="Smart Home Hub / Bridge",
        vendor_prefixes=["Philips", "Samsung", "Amazon", "Lutron"],
        typical_protocols=["Zigbee", "Z-Wave", "MQTT", "HTTPS", "mDNS"],
        typical_ports=[(443, 443), (80, 80), (5353, 5353)],
        typical_traffic_kbps=(10, 500),
        typical_connections_hour=(50, 500),
        active_hours=(0, 24),
        is_hub=True,
    ),
    # --- Streaming devices ---
    BehavioralSignature(
        device_type="streaming",
        label="Streaming / Media Device",
        vendor_prefixes=["Google", "Amazon", "Apple", "Roku"],
        typical_protocols=["HTTPS", "HTTP", "DNS", "STUN"],
        typical_ports=[(443, 443), (80, 80)],
        typical_traffic_kbps=(100, 20000),
        typical_connections_hour=(20, 200),
        active_hours=(6, 23),
    ),
    # --- Smart TVs ---
    BehavioralSignature(
        device_type="smart_tv",
        label="Smart TV",
        vendor_prefixes=["Samsung", "LG", "Sony", "TCL", "Realtek"],
        typical_protocols=["HTTPS", "HTTP", "DNS", "SSDP", "mDNS"],
        typical_ports=[(443, 443), (80, 80), (1900, 1900), (5353, 5353)],
        typical_traffic_kbps=(50, 10000),
        typical_connections_hour=(10, 150),
        active_hours=(6, 23),
    ),
    # --- ESP / custom IoT devices ---
    BehavioralSignature(
        device_type="custom_iot",
        label="Custom IoT / Embedded Device",
        vendor_prefixes=["Espressif", "Raspberry Pi"],
        typical_protocols=["MQTT", "HTTP", "CoAP", "DNS"],
        typical_ports=[(80, 80), (443, 443), (1883, 1883), (5683, 5683)],
        typical_traffic_kbps=(0.5, 100),
        typical_connections_hour=(2, 100),
        active_hours=(0, 24),
    ),
]


# ── classifier ─────────────────────────────────────────────────────

class DeviceClassifier:
    """Classifies IoT devices by MAC OUI and behavioural signature.

    Parameters
    ----------
    oui_db : dict[str, str] | None
        MAC prefix -> vendor name map.  Uses BUILTIN_OUI if None.
    signatures : list[BehavioralSignature] | None
        Known device type signatures.  Uses BUILTIN_SIGNATURES if None.
    """

    def __init__(
        self,
        oui_db: dict[str, str] | None = None,
        signatures: list[BehavioralSignature] | None = None,
    ):
        self._oui = oui_db or BUILTIN_OUI
        self._signatures = signatures or BUILTIN_SIGNATURES

    def classify(
        self,
        mac: str,
        features: dict[str, Any] | None = None,
        top_n: int = 3,
    ) -> list[Classification]:
        """Classify a device by MAC and optional behavioural features.

        Parameters
        ----------
        mac : str
            MAC address in any common format (xx:xx:xx:xx:xx:xx,
            xx-xx-xx-xx-xx-xx, xxxxxxxxxxxx).
        features : dict | None
            Behavioural features (protocols, ports, traffic_kbps, etc).
        top_n : int
            Return top N classifications.

        Returns
        -------
        list[Classification]  — sorted by confidence descending.
        """
        vendor = self.oui_vendor(mac)
        results: list[Classification] = []

        # 1. OUI-based classifications (if vendor known)
        if vendor:
            conf = 1.0 if features else 0.6
            # Pick the most likely device type for this vendor
            matched_types = self._types_for_vendor(vendor)
            for dt in matched_types[:top_n]:
                sig = next(
                    (s for s in self._signatures if s.device_type == dt), None
                )
                label = sig.label if sig else dt.replace("_", " ").title()
                results.append(
                    Classification(
                        device_type=dt,
                        label=label,
                        confidence=conf * (0.9 if dt == matched_types[0] else 0.6),
                        source="oui",
                        vendor=vendor,
                    )
                )
            # If no type matches found, create a generic vendor entry
            if not results:
                results.append(
                    Classification(
                        device_type="generic_iot",
                        label=f"{vendor} Device",
                        confidence=0.5,
                        source="oui",
                        vendor=vendor,
                    )
                )

        # 2. Behavioural signature matching (if features provided)
        if features:
            sig_results = self.match_signature(features)
            # Merge: replace OUI-only results with signature results
            # if signature confidence > OUI confidence
            for sr in sig_results:
                existing = next(
                    (r for r in results if r.device_type == sr.device_type), None
                )
                if existing:
                    existing.confidence = max(existing.confidence, sr.confidence)
                    existing.source = "combined" if existing.source != "combined" else "combined"
                else:
                    results.append(sr)

        # If vendor known and we have features, boost vendor-matching signatures
        if vendor and features:
            for r in results:
                if r.vendor == vendor:
                    r.confidence = min(r.confidence * 1.2, 1.0)
                    if r.source == "signature":
                        r.source = "combined"

        # 3. Sort and return top N
        results.sort(key=lambda x: x.confidence, reverse=True)
        return results[:top_n]

    def oui_vendor(self, mac: str) -> str | None:
        """Look up vendor from MAC OUI (first 3 bytes)."""
        prefix = self._normalize_mac(mac)[:6]
        return self._oui.get(prefix)

    def match_signature(
        self,
        features: dict[str, Any],
        min_confidence: float = 0.0,
    ) -> list[Classification]:
        """Match behavioural features against all known signatures."""
        results: list[Classification] = []
        for sig in self._signatures:
            conf, reasons = sig.score(features)
            if conf >= min_confidence:
                results.append(
                    Classification(
                        device_type=sig.device_type,
                        label=sig.label,
                        confidence=conf,
                        source="signature",
                        vendor=self._vendor_for_type(sig.device_type),
                    )
                )
        results.sort(key=lambda x: x.confidence, reverse=True)
        return results

    def known_devices(self) -> dict[str, list[dict]]:
        """Return all known device types with their signatures."""
        result = {}
        for sig in self._signatures:
            result[sig.device_type] = {
                "label": sig.label,
                "vendor_prefixes": sig.vendor_prefixes,
                "typical_protocols": sig.typical_protocols,
                "typical_ports": sig.typical_ports,
                "typical_traffic_kbps": sig.typical_traffic_kbps,
                "typical_connections_hour": sig.typical_connections_hour,
                "active_hours": sig.active_hours,
                "is_hub": sig.is_hub,
                "needs_hub": sig.needs_hub,
            }
        return result

    # ── helpers ────────────────────────────────────────────────────

    @staticmethod
    def _normalize_mac(mac: str) -> str:
        """Strip separators and lowercase."""
        return re.sub(r"[:\-.\s]", "", mac.strip()).lower()

    def _types_for_vendor(self, vendor: str) -> list[str]:
        """Return device types associated with a vendor, ordered by
        likelihood."""
        matching = []
        for sig in self._signatures:
            if any(vp.lower() in vendor.lower() for vp in sig.vendor_prefixes):
                matching.append(sig.device_type)
        # Deduplicate
        seen: set[str] = set()
        return [x for x in matching if not (x in seen or seen.add(x))]

    def _vendor_for_type(self, device_type: str) -> str | None:
        """Return first vendor prefix found for this device type."""
        sig = next(
            (s for s in self._signatures if s.device_type == device_type), None
        )
        if sig and sig.vendor_prefixes:
            return sig.vendor_prefixes[0]
        return None


# ── Example usage ──────────────────────────────────────────────────

if __name__ == "__main__":
    print("═" * 50)
    print("Vigil Device Classifier — Examples")
    print("═" * 50)

    clf = DeviceClassifier()

    # 1. MAC-only lookup
    print("\n── MAC-only: Wyze Cam ──")
    mac = "8c:f5:a3:12:34:56"
    print(f"  MAC:     {mac}")
    print(f"  Vendor:  {clf.oui_vendor(mac)}")
    for c in clf.classify(mac):
        print(f"  → {c.label}: {c.confidence:.0%} ({c.source})")

    # 2. MAC + behavioural features
    print("\n── MAC + features: suspected camera ──")
    mac2 = "8c:f5:a3:ab:cd:ef"
    features = {
        "protocols": ["RTSP", "HTTPS", "MQTT"],
        "ports": [554, 443, 8883],
        "traffic_kbps": 1200.0,
        "connections_hour": 120,
        "active_hour": 14,
    }
    print(f"  MAC:     {mac2}")
    print(f"  Vendor:  {clf.oui_vendor(mac2)}")
    for c in clf.classify(mac2, features, top_n=3):
        print(f"  → {c.label}: {c.confidence:.0%} ({c.source}, "
              f"vendor={c.vendor})")

    # 3. Unknown vendor + strong behavioural signature
    print("\n── Unknown vendor, known behaviour ──")
    mac3 = "11:22:33:44:55:66"
    features3 = {
        "protocols": ["MQTT", "HTTPS"],
        "ports": [443, 1883],
        "traffic_kbps": 0.5,
        "connections_hour": 5,
        "active_hour": 20,
    }
    print(f"  MAC:     {mac3}")
    print(f"  Vendor:  {clf.oui_vendor(mac3)} (unknown)")
    for c in clf.classify(mac3, features3, top_n=2):
        print(f"  → {c.label}: {c.confidence:.0%} ({c.source})")

    # 4. List all known device types
    print("\n── All known device types ──")
    for dt, info in clf.known_devices().items():
        print(f"  {dt:20s} → {info['label']:25s}  "
              f"protos={info['typical_protocols'][:3]}")

    print("\nDone.")
