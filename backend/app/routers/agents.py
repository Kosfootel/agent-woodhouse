"""Agents API router for Vigil."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter(tags=["agents"])


class AgentResponse(BaseModel):
    id: str
    name: str
    status: str
    last_seen: Optional[str]
    ip_address: Optional[str]
    version: Optional[str]
    trust_level: str = "untrusted"
    trust_score: int = 50
    alert_count: int = 0
    is_trusted: bool = False
    is_blocked: bool = False


class AgentsListResponse(BaseModel):
    count: int
    agents: List[AgentResponse]


class TrustResponse(BaseModel):
    agent_id: str
    trust_level: str
    is_trusted: bool
    is_blocked: bool


# Static list for now - will integrate with mesh later
KNOWN_AGENTS = [
    {
        "id": "woodhouse",
        "name": "Woodhouse",
        "status": "online",
        "last_seen": "2026-05-24T18:00:00",
        "ip_address": "192.168.50.24",
        "version": "v0.1.0",
        "trust_level": "trusted",
        "trust_score": 95,
        "alert_count": 0,
        "is_trusted": True,
        "is_blocked": False
    },
    {
        "id": "ray",
        "name": "Ray",
        "status": "online",
        "last_seen": "2026-05-24T18:00:00",
        "ip_address": "192.168.50.30",
        "version": "v0.1.0",
        "trust_level": "trusted",
        "trust_score": 90,
        "alert_count": 0,
        "is_trusted": True,
        "is_blocked": False
    },
    {
        "id": "liz",
        "name": "Liz",
        "status": "online",
        "last_seen": "2026-05-24T18:00:00",
        "ip_address": "192.168.50.30",
        "version": "v0.1.0",
        "trust_level": "trusted",
        "trust_score": 88,
        "alert_count": 0,
        "is_trusted": True,
        "is_blocked": False
    }
]


@router.get("/agents", response_model=AgentsListResponse)
async def get_agents():
    """Get all registered agents."""
    return AgentsListResponse(
        count=len(KNOWN_AGENTS),
        agents=[AgentResponse(**a) for a in KNOWN_AGENTS]
    )


@router.get("/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str):
    """Get a specific agent by ID."""
    for agent in KNOWN_AGENTS:
        if agent["id"] == agent_id:
            return AgentResponse(**agent)
    return AgentResponse(
        id=agent_id,
        name=f"Agent {agent_id}",
        status="unknown",
        last_seen=None,
        ip_address=None,
        version=None,
        trust_level="untrusted",
        trust_score=50,
        alert_count=0,
        is_trusted=False,
        is_blocked=False
    )


@router.post("/agents/{agent_id}/trust", response_model=TrustResponse)
async def trust_agent(agent_id: str):
    """Toggle trust status for an agent."""
    for agent in KNOWN_AGENTS:
        if agent["id"] == agent_id:
            # Toggle trust status
            if agent["trust_level"] == "trusted":
                agent["trust_level"] = "untrusted"
                agent["is_trusted"] = False
            else:
                agent["trust_level"] = "trusted"
                agent["is_trusted"] = True
                agent["is_blocked"] = False  # Unblock if trusting
            return TrustResponse(
                agent_id=agent_id,
                trust_level=agent["trust_level"],
                is_trusted=agent["is_trusted"],
                is_blocked=agent["is_blocked"]
            )
    raise HTTPException(status_code=404, detail="Agent not found")


@router.post("/agents/{agent_id}/block", response_model=TrustResponse)
async def block_agent(agent_id: str):
    """Toggle block status for an agent."""
    for agent in KNOWN_AGENTS:
        if agent["id"] == agent_id:
            # Toggle block status
            if agent["trust_level"] == "blocked":
                agent["trust_level"] = "untrusted"
                agent["is_blocked"] = False
            else:
                agent["trust_level"] = "blocked"
                agent["is_blocked"] = True
                agent["is_trusted"] = False  # Untrust if blocking
            return TrustResponse(
                agent_id=agent_id,
                trust_level=agent["trust_level"],
                is_trusted=agent["is_trusted"],
                is_blocked=agent["is_blocked"]
            )
    raise HTTPException(status_code=404, detail="Agent not found")
