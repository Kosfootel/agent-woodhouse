"""Admin API router for Vigil."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import sqlite3
import os
import shutil
from datetime import datetime

router = APIRouter(prefix="/api", tags=["admin"])

# Database path
DB_PATH = "/home/erik-ross/projects/vigil-home/vigil.db"
VIGIL_DIR = "/home/erik-ross/projects/vigil-home"


class ResetRequest(BaseModel):
    confirm: bool = False
    keep_devices: bool = False


class ResetResponse(BaseModel):
    success: bool
    message: str
    details: Dict[str, Any]


def get_db_connection():
    """Get a database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@router.post("/reset", response_model=ResetResponse)
async def reset_vigil(request: ResetRequest):
    """
    Reset Vigil to initial state.
    This clears alerts, observations, and optionally devices.
    Triggers the setup wizard on next dashboard load.
    """
    if not request.confirm:
        raise HTTPException(
            status_code=400, 
            detail="Reset requires confirm=true. This is destructive!"
        )

    try:
        results = {
            "alerts_cleared": 0,
            "observations_cleared": 0,
            "devices_cleared": 0,
            "router_config_reset": False,
            "myhomeid_sync_reset": False,
            "setup_wizard_triggered": True
        }

        conn = get_db_connection()
        cursor = conn.cursor()

        # Clear alerts
        cursor.execute("DELETE FROM alerts")
        results["alerts_cleared"] = cursor.rowcount

        # Clear device observations
        cursor.execute("DELETE FROM device_observations")
        results["observations_cleared"] = cursor.rowcount

        # Clear network flows
        cursor.execute("DELETE FROM network_flows")
        results["network_flows_cleared"] = cursor.rowcount

        # Optionally clear devices
        if not request.keep_devices:
            cursor.execute("DELETE FROM devices")
            results["devices_cleared"] = cursor.rowcount
        else:
            # Just mark all devices as offline/unknown
            cursor.execute("UPDATE devices SET status = 'inactive', trust_score = 50.0")
            results["devices_marked_inactive"] = cursor.rowcount

        # Reset myhomeid sync state
        cursor.execute("""
            UPDATE myhomeid_sync 
            SET last_sync = NULL, 
                sync_token = NULL, 
                devices_synced = 0,
                last_sync_status = 'pending',
                last_error = NULL
            WHERE id = 1
        """)
        results["myhomeid_sync_reset"] = cursor.rowcount > 0

        # Reset router config connection status
        cursor.execute("""
            UPDATE router_config 
            SET connection_status = 'disconnected',
                last_connected = NULL
            WHERE id = 1
        """)
        results["router_config_reset"] = cursor.rowcount > 0

        # Create a flag file to trigger setup wizard
        setup_flag_file = os.path.join(VIGIL_DIR, ".reset_triggered")
        with open(setup_flag_file, "w") as f:
            f.write(f"Reset triggered at {datetime.now().isoformat()}\n")

        conn.commit()
        conn.close()

        return ResetResponse(
            success=True,
            message="Vigil has been reset. Please reload the dashboard to start the setup wizard.",
            details=results
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reset failed: {str(e)}")


@router.get("/health")
async def health_check():
    """Check if the API is healthy and database is accessible."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM devices")
        device_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM alerts WHERE acknowledged = 0")
        unack_alerts = cursor.fetchone()[0]
        conn.close()

        return {
            "status": "healthy",
            "database": "connected",
            "devices": device_count,
            "unacknowledged_alerts": unack_alerts,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")
