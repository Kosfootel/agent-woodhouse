"""
Vigil Tier A - Security Router
FastAPI endpoints for security scanning, logging, and anomaly detection.
"""

import re
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.models import (
    get_db, PromptLog, ToolInvocation, MemoryAccess, 
    SecurityEvent, init_db
)

router = APIRouter(prefix="/security", tags=["security"])

# Load policy configuration
POLICY_PATH = Path(__file__).parent.parent.parent / "policy.yaml"

def load_policy() -> Dict:
    """Load security policy from YAML file."""
    try:
        with open(POLICY_PATH, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        # Return default policy if file can't be loaded
        return {
            "prompt_injection": {"blocked_patterns": []},
            "tool_invocation": {"blocked_tools": [], "blocked_paths": []},
            "memory_access": {"sensitivity_levels": {}},
            "anomaly_detection": {"thresholds": {}}
        }

# Initialize database on module load
init_db()


# ============ Pydantic Models ============

class ScanPromptRequest(BaseModel):
    agent_id: str
    prompt: str
    source_ip: Optional[str] = None


class ScanPromptResponse(BaseModel):
    blocked: bool
    reason: Optional[str] = None
    confidence: float
    matched_patterns: List[str]


class LogToolRequest(BaseModel):
    agent_id: str
    tool_name: str
    arguments: Dict[str, Any] = {}
    result: Optional[str] = None
    execution_time_ms: Optional[float] = None


class LogToolResponse(BaseModel):
    logged: bool
    blocked: bool
    block_reason: Optional[str] = None


class LogAccessRequest(BaseModel):
    agent_id: str
    access_type: str  # file_read, file_write, memory_read, etc.
    resource_path: str
    content_hash: Optional[str] = None
    size_bytes: Optional[int] = None


class LogAccessResponse(BaseModel):
    logged: bool
    sensitivity_level: str
    blocked: bool


class BaselineMetrics(BaseModel):
    agent_id: str
    prompts_per_hour: float
    tools_per_hour: float
    error_rate: float
    access_rate_per_hour: float
    total_prompts: int
    total_tools: int
    total_access: int
    window_hours: int = 1


class AnomalyItem(BaseModel):
    id: int
    agent_id: str
    timestamp: datetime
    event_type: str
    severity: str
    description: str
    acknowledged: bool


class AnomalyListResponse(BaseModel):
    anomalies: List[AnomalyItem]
    total_count: int
    unacknowledged_count: int


# ============ Endpoint 1: Prompt Scanning ============

@router.post("/scan-prompt", response_model=ScanPromptResponse)
def scan_prompt(request: ScanPromptRequest, db: Session = Depends(get_db)):
    """
    Scan a prompt for injection attacks.
    Detects: ignore_previous, system_override, jailbreak, delimiter attacks, encoding tricks
    """
    policy = load_policy()
    prompt_lower = request.prompt.lower()
    
    blocked = False
    reason = None
    confidence = 0.0
    matched_patterns = []
    
    # Define patterns inline to avoid YAML escaping issues
    pattern_definitions = [
        {
            "name": "ignore_previous",
            "severity": "critical",
            "confidence": 0.95,
            "patterns": [
                r"ignore\s+(all\s+)?(your\s+)?(previous|prior|above)\s+(instructions|constraints|rules|prompt|commands)",
                r"disregard\s+(everything\s+)?(you\s+were\s+)?(told|said|instructed)",
                r"forget\s+(your\s+)?(instructions|training|prompt)"
            ]
        },
        {
            "name": "system_override",
            "severity": "critical",
            "confidence": 0.92,
            "patterns": [
                r"you\s+(are|will\s+be|should\s+act\s+as)\s+(now\s+)?(a\s+|an\s+)?(unfiltered|unrestricted|uncensored)",
                r"(system|developer|administrator|user)\s+mode\s+(enabled|activated|on)",
                r"(bypass|disable|turn\s+off|remove)\s+(all\s+)?(restrictions|filters|safety|guardrails)"
            ]
        },
        {
            "name": "jailbreak",
            "severity": "critical",
            "confidence": 0.90,
            "patterns": [
                r"do\s+anything\s+now",
                r"(DAN|jailbreak|uncensored)\s+mode",
                r"you\s+can\s+(say|do)\s+(anything|whatever)",
                r"no\s+(ethical|moral|safety)\s+(constraints|limitations|restrictions)"
            ]
        },
        {
            "name": "delimiter_attack",
            "severity": "high",
            "confidence": 0.88,
            "patterns": [
                r"```\s*(system|user|assistant)",
                r'"""\s*(system|user|assistant)',
                r"</?system\s*>",
                r"---\s*system\s*---"
            ]
        },
        {
            "name": "encoding_tricks",
            "severity": "medium",
            "confidence": 0.75,
            "patterns": [
                r"base64:|base64_decode",
                r"\\x[0-9a-fA-F]{2}",
                r"\\u[0-9a-fA-F]{4}",
                r"\$\{.*\}"
            ]
        }
    ]
    
    for pattern_group in pattern_definitions:
        group_name = pattern_group.get("name", "unknown")
        patterns = pattern_group.get("patterns", [])
        group_confidence = pattern_group.get("confidence", 0.5)
        
        for pattern in patterns:
            try:
                if re.search(pattern, prompt_lower, re.IGNORECASE):
                    matched_patterns.append(group_name)
                    confidence = max(confidence, group_confidence)
                    if pattern_group.get("severity") == "critical":
                        blocked = True
                        reason = f"Critical pattern detected: {group_name}"
                    break
            except re.error:
                continue
    
    # Create log entry
    log_entry = PromptLog(
        agent_id=request.agent_id,
        prompt_text=request.prompt[:1000],  # Truncate for storage
        blocked=blocked,
        reason=reason,
        confidence=confidence,
        matched_patterns=matched_patterns,
        source_ip=request.source_ip
    )
    db.add(log_entry)
    db.commit()
    
    # Check for threshold anomalies
    _check_anomalies(db, request.agent_id)
    
    return ScanPromptResponse(
        blocked=blocked,
        reason=reason,
        confidence=confidence,
        matched_patterns=matched_patterns
    )


# ============ Endpoint 2: Tool Invocation Logging ============

@router.post("/log-tool", response_model=LogToolResponse)
def log_tool(request: LogToolRequest, db: Session = Depends(get_db)):
    """
    Log a tool invocation and check against block/allow lists.
    Blocks: shell_execute, file_read on sensitive paths, credential_access
    """
    policy = load_policy()
    
    blocked = False
    block_reason = None
    
    blocked_tools = policy.get("tool_invocation", {}).get("blocked_tools", [])
    blocked_paths = policy.get("tool_invocation", {}).get("blocked_paths", [])
    
    # Check if tool is blocked
    if request.tool_name in blocked_tools:
        blocked = True
        block_reason = f"Tool '{request.tool_name}' is in block list"
    
    # Check arguments for sensitive paths
    if not blocked:
        args_str = str(request.arguments)
        for path_pattern in blocked_paths:
            # Convert glob pattern to regex
            pattern = path_pattern.replace("*", ".*").replace("~", ".*")
            if re.search(pattern, args_str, re.IGNORECASE):
                blocked = True
                block_reason = f"Arguments match blocked path pattern: {path_pattern}"
                break
    
    # Create log entry
    log_entry = ToolInvocation(
        agent_id=request.agent_id,
        tool_name=request.tool_name,
        arguments=request.arguments,
        blocked=blocked,
        block_reason=block_reason,
        result=request.result[:500] if request.result else None,
        execution_time_ms=request.execution_time_ms
    )
    db.add(log_entry)
    db.commit()
    
    return LogToolResponse(
        logged=True,
        blocked=blocked,
        block_reason=block_reason
    )


# ============ Endpoint 3: Memory/Access Logging ============

@router.post("/log-access", response_model=LogAccessResponse)
def log_access(request: LogAccessRequest, db: Session = Depends(get_db)):
    """
    Log file/memory access and classify sensitivity.
    Levels: critical (SSH keys), high (configs), medium (docs), low (tmp)
    """
    policy = load_policy()
    
    sensitivity_levels = policy.get("memory_access", {}).get("sensitivity_levels", {})
    
    # Determine sensitivity level
    resource_lower = request.resource_path.lower()
    sensitivity = "low"  # Default
    blocked = False
    
    # Check critical patterns
    for pattern in sensitivity_levels.get("critical", []):
        if pattern.lower() in resource_lower:
            sensitivity = "critical"
            blocked = True
            break
    
    # Check high patterns
    if sensitivity == "low":
        for pattern in sensitivity_levels.get("high", []):
            if pattern.lower() in resource_lower:
                sensitivity = "high"
                break
    
    # Check medium patterns
    if sensitivity == "low":
        for pattern in sensitivity_levels.get("medium", []):
            if pattern.lower() in resource_lower:
                sensitivity = "medium"
                break
    
    # Create log entry
    log_entry = MemoryAccess(
        agent_id=request.agent_id,
        access_type=request.access_type,
        resource_path=request.resource_path,
        sensitivity_level=sensitivity,
        blocked=blocked,
        content_hash=request.content_hash,
        size_bytes=request.size_bytes
    )
    db.add(log_entry)
    db.commit()
    
    return LogAccessResponse(
        logged=True,
        sensitivity_level=sensitivity,
        blocked=blocked
    )


# ============ Endpoint 4: Baseline Metrics ============

@router.get("/baseline/{agent_id}", response_model=BaselineMetrics)
def get_baseline(agent_id: str, hours: int = 1, db: Session = Depends(get_db)):
    """
    Get baseline metrics for an agent.
    Returns: prompts_per_hour, tools_per_hour, error_rate, etc.
    """
    since = datetime.utcnow() - timedelta(hours=hours)
    
    # Count prompts
    total_prompts = db.query(PromptLog).filter(
        and_(PromptLog.agent_id == agent_id, PromptLog.timestamp >= since)
    ).count()
    
    # Count tools
    total_tools = db.query(ToolInvocation).filter(
        and_(ToolInvocation.agent_id == agent_id, ToolInvocation.timestamp >= since)
    ).count()
    
    # Count access operations
    total_access = db.query(MemoryAccess).filter(
        and_(MemoryAccess.agent_id == agent_id, MemoryAccess.timestamp >= since)
    ).count()
    
    # Count errors (blocked operations)
    prompt_errors = db.query(PromptLog).filter(
        and_(
            PromptLog.agent_id == agent_id,
            PromptLog.timestamp >= since,
            PromptLog.blocked == True
        )
    ).count()
    
    tool_errors = db.query(ToolInvocation).filter(
        and_(
            ToolInvocation.agent_id == agent_id,
            ToolInvocation.timestamp >= since,
            ToolInvocation.blocked == True
        )
    ).count()
    
    total_operations = total_prompts + total_tools
    total_errors = prompt_errors + tool_errors
    
    error_rate = total_errors / total_operations if total_operations > 0 else 0.0
    
    prompts_per_hour = total_prompts / hours
    tools_per_hour = total_tools / hours
    access_rate = total_access / hours
    
    return BaselineMetrics(
        agent_id=agent_id,
        prompts_per_hour=round(prompts_per_hour, 2),
        tools_per_hour=round(tools_per_hour, 2),
        error_rate=round(error_rate, 4),
        access_rate_per_hour=round(access_rate, 2),
        total_prompts=total_prompts,
        total_tools=total_tools,
        total_access=total_access,
        window_hours=hours
    )


# ============ Endpoint 5: Anomaly Detection ============

def _check_anomalies(db: Session, agent_id: str):
    """Check for anomalies and create security events if thresholds exceeded."""
    policy = load_policy()
    thresholds = policy.get("anomaly_detection", {}).get("thresholds", {})
    
    # Get metrics for last hour
    since = datetime.utcnow() - timedelta(hours=1)
    
    prompts_count = db.query(PromptLog).filter(
        and_(PromptLog.agent_id == agent_id, PromptLog.timestamp >= since)
    ).count()
    
    tools_count = db.query(ToolInvocation).filter(
        and_(ToolInvocation.agent_id == agent_id, ToolInvocation.timestamp >= since)
    ).count()
    
    # Check thresholds
    if prompts_count > thresholds.get("prompts_per_hour", 120):
        event = SecurityEvent(
            agent_id=agent_id,
            event_type="threshold_breach",
            severity="high",
            description=f"Prompt rate exceeded threshold: {prompts_count}/hour",
            details={"threshold": thresholds.get("prompts_per_hour"), "actual": prompts_count}
        )
        db.add(event)
    
    if tools_count > thresholds.get("tools_per_hour", 60):
        event = SecurityEvent(
            agent_id=agent_id,
            event_type="threshold_breach",
            severity="high",
            description=f"Tool invocation rate exceeded threshold: {tools_count}/hour",
            details={"threshold": thresholds.get("tools_per_hour"), "actual": tools_count}
        )
        db.add(event)
    
    db.commit()


@router.get("/anomalies", response_model=AnomalyListResponse)
def list_anomalies(
    agent_id: Optional[str] = None,
    severity: Optional[str] = None,
    acknowledged: Optional[bool] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    List detected anomalies with optional filtering.
    """
    query = db.query(SecurityEvent)
    
    if agent_id:
        query = query.filter(SecurityEvent.agent_id == agent_id)
    if severity:
        query = query.filter(SecurityEvent.severity == severity)
    if acknowledged is not None:
        query = query.filter(SecurityEvent.acknowledged == acknowledged)
    
    events = query.order_by(SecurityEvent.timestamp.desc()).limit(limit).all()
    
    total_count = db.query(SecurityEvent).count()
    unacknowledged_count = db.query(SecurityEvent).filter(
        SecurityEvent.acknowledged == False
    ).count()
    
    anomalies = [
        AnomalyItem(
            id=e.id,
            agent_id=e.agent_id,
            timestamp=e.timestamp,
            event_type=e.event_type,
            severity=e.severity,
            description=e.description,
            acknowledged=e.acknowledged
        )
        for e in events
    ]
    
    return AnomalyListResponse(
        anomalies=anomalies,
        total_count=total_count,
        unacknowledged_count=unacknowledged_count
    )


@router.post("/anomalies/{anomaly_id}/acknowledge")
def acknowledge_anomaly(anomaly_id: int, db: Session = Depends(get_db)):
    """Acknowledge a security event/anomaly."""
    event = db.query(SecurityEvent).filter(SecurityEvent.id == anomaly_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Anomaly not found")
    
    event.acknowledged = True
    db.commit()
    
    return {"acknowledged": True}


@router.get("/events")
def get_security_events(
    agent: str = None,
    severity: str = None,
    eventType: str = None,
    db: Session = Depends(get_db)
):
    """Get security events with optional filtering."""
    query = db.query(SecurityEvent)
    
    if agent:
        query = query.filter(SecurityEvent.agent_id == agent)
    if severity:
        query = query.filter(SecurityEvent.severity == severity)
    if eventType:
        query = query.filter(SecurityEvent.event_type == eventType)
    
    events = query.order_by(SecurityEvent.timestamp.desc()).all()
    
    return {
        "events": [
            {
                "id": e.id,
                "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                "agent": e.agent_id,
                "eventType": e.event_type,
                "severity": e.severity,
                "details": e.description,
            }
            for e in events
        ]
    }


@router.get("/blocked-stats")
def get_blocked_stats(db: Session = Depends(get_db)):
    """Get statistics on blocked prompts/actions."""
    # Count total blocked events
    total_blocked = db.query(SecurityEvent).filter(
        SecurityEvent.event_type.in_(["prompt_blocked", "tool_blocked", "memory_blocked"])
    ).count()
    
    # Get breakdown by category (event_type)
    categories = db.query(
        SecurityEvent.event_type,
        func.count(SecurityEvent.id).label("count")
    ).filter(
        SecurityEvent.event_type.in_(["prompt_blocked", "tool_blocked", "memory_blocked"])
    ).group_by(SecurityEvent.event_type).all()
    
    category_map = {
        "prompt_blocked": "Prompt",
        "tool_blocked": "Tool",
        "memory_blocked": "Memory",
    }
    
    colors = ["#dc2626", "#ea580c", "#ca8a04", "#16a34a", "#2563eb"]
    
    by_category = [
        {
            "category": category_map.get(cat, cat.replace("_", " ").title()),
            "count": count,
            "color": colors[i % len(colors)]
        }
        for i, (cat, count) in enumerate(categories)
    ]
    
    return {
        "total": total_blocked,
        "byCategory": by_category
    }


@router.get("/tool-usage")
def get_tool_usage(period: str = "24h", db: Session = Depends(get_db)):
    """Get tool usage statistics."""
    # Parse period
    hours = 24
    if period.endswith('h'):
        hours = int(period[:-1])
    elif period.endswith('d'):
        hours = int(period[:-1]) * 24
    
    since = datetime.utcnow() - timedelta(hours=hours)
    
    # Get tool usage by hour
    usages = db.query(
        ToolInvocation.tool_name,
        func.count(ToolInvocation.id).label("count")
    ).filter(
        ToolInvocation.timestamp >= since
    ).group_by(ToolInvocation.tool_name).all()
    
    return {
        "period": period,
        "tools": [
            {"name": name, "count": count}
            for name, count in usages
        ]
    }


@router.get("/memory-access")
def get_memory_access_stats(db: Session = Depends(get_db)):
    """Get memory access statistics for heatmap."""
    # Get access patterns by agent and sensitivity
    accesses = db.query(
        MemoryAccess.agent_id,
        MemoryAccess.sensitivity_level,
        func.count(MemoryAccess.id).label("count")
    ).group_by(
        MemoryAccess.agent_id,
        MemoryAccess.sensitivity_level
    ).all()
    
    # Build heatmap data
    agents = set()
    levels = ["public", "internal", "confidential", "restricted"]
    data = {}
    
    for agent_id, level, count in accesses:
        agents.add(agent_id)
        if agent_id not in data:
            data[agent_id] = {}
        data[agent_id][level] = count
    
    return {
        "agents": list(agents),
        "levels": levels,
        "data": [
            {
                "agent": agent,
                "level": level,
                "count": data.get(agent, {}).get(level, 0)
            }
            for agent in agents
            for level in levels
        ]
    }
