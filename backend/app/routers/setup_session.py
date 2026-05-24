"""Setup Session Management for Vigil"""
from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["setup"])

# In-memory session storage (use Redis in production)
setup_sessions: dict = {}

class SessionResponse(BaseModel):
    session_id: str
    message: str

@router.post("/setup/session")
async def create_setup_session():
    """
    Create a new setup session.
    Returns a session ID for tracking setup progress.
    """
    session_id = str(uuid.uuid4())
    setup_sessions[session_id] = {
        "created_at": datetime.now(),
        "step": 1,
        "router_discovered": None,
        "router_connected": False
    }
    logger.info(f"Created setup session: {session_id}")
    return {
        "session_id": session_id,
        "message": "Setup session created successfully"
    }
