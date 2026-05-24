"""Agents API router for Vigil."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import get_db, Agent

router = APIRouter(prefix="/agents", tags=["agents"])


class AgentResponse(BaseModel):
    id: int
    name: str
    status: str
    last_seen: Optional[str]
    ip_address: Optional[str]
    version: Optional[str]

    class Config:
        from_attributes = True


class AgentsListResponse(BaseModel):
    count: int
    agents: List[AgentResponse]


@router.get("/", response_model=AgentsListResponse)
async def get_agents(db: Session = Depends(get_db)):
    """Get all registered agents."""
    agents = db.query(Agent).all()
    return AgentsListResponse(
        count=len(agents),
        agents=[AgentResponse(
            id=a.id,
            name=a.name,
            status=a.status,
            last_seen=a.last_seen.isoformat() if a.last_seen else None,
            ip_address=a.ip_address,
            version=a.version
        ) for a in agents]
    )


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: int, db: Session = Depends(get_db)):
    """Get a specific agent by ID."""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return AgentResponse(
        id=agent.id,
        name=agent.name,
        status=a.status,
        last_seen=agent.last_seen.isoformat() if agent.last_seen else None,
        ip_address=agent.ip_address,
        version=agent.version
    )
