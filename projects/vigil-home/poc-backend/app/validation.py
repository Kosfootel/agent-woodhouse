"""Vigil Home — Input Validation

Validates and sanitizes user input for MAC addresses, IP addresses, and hostnames.
Used to prevent injection attacks and ensure data integrity.

Per SECURITY-HARDENING-PLAN.md Phase 2.
"""

import re
import ipaddress
from typing import Optional, Tuple

from pydantic import BaseModel, field_validator, ValidationError


# ── Validation patterns ────────────────────────────────────────────

# IEEE 802 MAC address formats: 00:1A:2B:3C:4D:5E or 00-1A-2B-3C-4D-5E or 001A.2B3C.4D5E
MAC_REGEX = re.compile(
    r'^([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$'  # colon/dash separated
    r'|^([0-9A-Fa-f]{4}\.){2}[0-9A-Fa-f]{4}$'   # Cisco dot notation
)

# Hostname: alphanumeric + hyphens, max 253 chars, no leading/trailing hyphens
# Per RFC 952 and RFC 1123
HOSTNAME_REGEX = re.compile(
    r'^(?!-)'           # No leading hyphen
    r'[A-Za-z0-9-]{1,63}'  # Label: 1-63 alphanumeric + hyphens
    r'(?<!-)$'          # No trailing hyphen
    r'|^'               # OR (for multi-label hostnames)
    r'(?:(?!-)[A-Za-z0-9-]{1,63}(?<!-)\.)+'  # Multiple labels
    r'(?:(?!-)[A-Za-z0-9-]{1,63}(?<!-))$'   # Final label
)

# Device type: alphanumeric + spaces/hyphens/underscores, max 64 chars
DEVICE_TYPE_REGEX = re.compile(r'^[A-Za-z0-9 _-]{1,64}$')


# ── Validation functions ───────────────────────────────────────────

def validate_mac(mac: str) -> str:
    """Validate and normalize a MAC address.

    Accepts:
    - Colon-separated: 00:1A:2B:3C:4D:5E
    - Dash-separated: 00-1A-2B-3C-4D-5E
    - Cisco dot: 001A.2B3C.4D5E

    Returns:
        Normalized MAC in colon-separated uppercase format.

    Raises:
        ValueError: If MAC address format is invalid.
    """
    if not MAC_REGEX.match(mac):
        raise ValueError(
            f"Invalid MAC address format: {mac}. "
            "Expected format: 00:1A:2B:3C:4D:5E or 00-1A-2B-3C-4D-5E"
        )
    # Normalize to uppercase colon-separated
    normalized = mac.replace('-', ':').replace('.', '')
    # Insert colons if Cisco format was used
    if len(normalized) == 12:
        normalized = ':'.join(normalized[i:i+2] for i in range(0, 12, 2))
    return normalized.upper()


def validate_ip(ip: str) -> str:
    """Validate an IP address (IPv4 or IPv6).

    Returns:
        The validated IP address (normalized by ipaddress module).

    Raises:
        ValueError: If IP address is invalid.
    """
    try:
        # This will raise ValueError for invalid IPs
        addr = ipaddress.ip_address(ip)
        return str(addr)
    except ValueError:
        raise ValueError(
            f"Invalid IP address: {ip}. "
            "Expected IPv4 (e.g., 192.168.1.1) or IPv6 (e.g., 2001:db8::1)"
        )


def validate_hostname(hostname: Optional[str]) -> Optional[str]:
    """Validate a hostname per RFC 952 and RFC 1123.

    Returns:
        The validated hostname, or None if input was None/empty.

    Raises:
        ValueError: If hostname format is invalid.
    """
    if not hostname:
        return None

    hostname = hostname.strip()
    if not hostname:
        return None

    if len(hostname) > 253:
        raise ValueError(
            f"Hostname too long: {len(hostname)} chars (max 253)"
        )

    if not HOSTNAME_REGEX.match(hostname):
        raise ValueError(
            f"Invalid hostname: {hostname}. "
            "Must be alphanumeric with hyphens, no leading/trailing hyphens"
        )

    return hostname


def validate_device_type(device_type: Optional[str]) -> Optional[str]:
    """Validate a device type string.

    Returns:
        The validated device type, or None if input was None/empty.

    Raises:
        ValueError: If device type format is invalid.
    """
    if not device_type:
        return None

    device_type = device_type.strip()
    if not device_type:
        return None

    if not DEVICE_TYPE_REGEX.match(device_type):
        raise ValueError(
            f"Invalid device type: {device_type}. "
            "Must be alphanumeric with spaces, hyphens, or underscores (max 64 chars)"
        )

    return device_type


def validate_severity(severity: str) -> str:
    """Validate a severity level string.

    Returns:
        The validated severity in lowercase.

    Raises:
        ValueError: If severity is not a valid level.
    """
    valid = {"info", "low", "medium", "high", "critical"}
    severity_lower = severity.lower()
    if severity_lower not in valid:
        raise ValueError(
            f"Invalid severity: {severity}. "
            f"Must be one of: {', '.join(sorted(valid))}"
        )
    return severity_lower


def validate_alert_status(status: str) -> str:
    """Validate an alert status string.

    Returns:
        The validated status in lowercase.

    Raises:
        ValueError: If status is not valid.
    """
    valid = {"open", "acknowledged", "resolved"}
    status_lower = status.lower()
    if status_lower not in valid:
        raise ValueError(
            f"Invalid alert status: {status}. "
            f"Must be one of: {', '.join(sorted(valid))}"
        )
    return status_lower


# ── Pydantic models with validators ────────────────────────────────


class ValidatedDeviceInput(BaseModel):
    """Pydantic model with built-in validation for device creation."""

    mac: str
    ip: str
    hostname: Optional[str] = None
    device_type: Optional[str] = None

    @field_validator('mac')
    @classmethod
    def _validate_mac(cls, v: str) -> str:
        return validate_mac(v)

    @field_validator('ip')
    @classmethod
    def _validate_ip(cls, v: str) -> str:
        return validate_ip(v)

    @field_validator('hostname')
    @classmethod
    def _validate_hostname(cls, v: Optional[str]) -> Optional[str]:
        return validate_hostname(v)

    @field_validator('device_type')
    @classmethod
    def _validate_device_type(cls, v: Optional[str]) -> Optional[str]:
        return validate_device_type(v)


class ValidatedEventInput(BaseModel):
    """Pydantic model with built-in validation for event ingestion."""

    device_id: int
    event_type: str = "generic"
    severity: str = "info"
    value: Optional[float] = None
    details: Optional[dict] = None

    @field_validator('severity')
    @classmethod
    def _validate_severity(cls, v: str) -> str:
        return validate_severity(v)

    @field_validator('event_type')
    @classmethod
    def _validate_event_type(cls, v: str) -> str:
        if not v or len(v) > 64:
            raise ValueError("event_type must be 1-64 characters")
        return v.strip()
