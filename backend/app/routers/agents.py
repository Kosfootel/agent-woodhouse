"""Agents API router for Vigil."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/agents", tags=["agents"])


class AgentResponse(BaseModel):
    id: str
    name: str
    status: str
    last_seen: Optional[str]
    ip_address: Optional[str]
    version: Optional[str]


class AgentsListResponse(BaseModel):
    count: int
    agents: List[AgentResponse]


# Static list for now - will integrate with mesh later
KNOWN_AGENTS = [
    {
        "id": "woodhouse",
        "name": "Woodhouse",
        "status": "online",
        "last_seen": "2026-05-23T21:00:00",
        "ip_address": "192.168.50.24",
        "version": "v0.1.0"
    }
]


@router.get("/", response_model=AgentsListResponse)
async def get_agents():
    """Get all registered agents."""
    return AgentsListResponse(
        count=len(KNOWN_AGENTS),
        agents=[AgentResponse(**a) for a in KNOWN_AGENTS]
    )


@router.get("/{agent_id}", response_model=AgentResponse)
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
        version=None
    )
