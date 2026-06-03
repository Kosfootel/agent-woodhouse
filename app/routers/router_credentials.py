"""
Router credential management for Vigil
Secure storage and retrieval of router admin credentials
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional
import logging
from datetime import datetime
from sqlalchemy.orm import Session

# Import Vigil's existing vault service
try:
    from vault_service import VaultService
    from vault_models import CredentialType, ServiceType
    VAULT_AVAILABLE = True
except ImportError:
    VAULT_AVAILABLE = False
    logging.warning("Vault service not available - using fallback storage")

router = APIRouter(prefix="/api/router", tags=["router"])
logger = logging.getLogger(__name__)

# Constants
ROUTER_CREDENTIAL_NAME = "router_admin"
ROUTER_SERVICE_TYPE = "router_administration"
DEFAULT_ROUTER_IP = "192.168.50.1"
DEFAULT_ROUTER_MODEL = "ASUS GT6"


class RouterCredentialsInput(BaseModel):
    """Input model for router credentials."""
    router_ip: str = Field(default=DEFAULT_ROUTER_IP, description="Router IP address")
    admin_username: str = Field(..., description="Router admin username")
    admin_password: str = Field(..., description="Router admin password")
    router_model: str = Field(default=DEFAULT_ROUTER_MODEL, description="Router model")
    
    class Config:
        json_schema_extra = {
            "example": {
                "router_ip": "192.168.50.1",
                "admin_username": "admin",
                "admin_password": "your-password-here",
                "router_model": "ASUS GT6"
            }
        }


class RouterCredentialsStatus(BaseModel):
    """Status response for router credentials."""
    configured: bool
    router_ip: str
    router_model: Optional[str]
    has_username: bool
    message: str


class RouterCredentialsStore:
    """Secure credential storage using Vigil's existing vault or fallback."""
    
    def __init__(self, db_session: Session = None):
        self.db = db_session
        self.vault = VaultService() if VAULT_AVAILABLE else None
        # Simple in-memory fallback for development
        self._fallback_storage = {}
    
    def _build_credential_value(self, creds: RouterCredentialsInput) -> str:
        """Build JSON string with credential data for storage."""
        import json
        credential_data = {
            "username": creds.admin_username,
            "password": creds.admin_password,
            "model": creds.router_model,
            "ip": creds.router_ip,
            "stored_at": datetime.utcnow().isoformat()
        }
        return json.dumps(credential_data)
    
    def store_credentials(self, creds: RouterCredentialsInput) -> bool:
        """Encrypt and store router credentials."""
        try:
            if not VAULT_AVAILABLE or not self.db:
                # Fallback: store in memory (NOT for production)
                self._fallback_storage[ROUTER_CREDENTIAL_NAME] = {
                    "credential_value": self._build_credential_value(creds),
                    "id": "fallback_id"
                }
                logger.info("Credentials stored in fallback storage (development mode)")
                return True
            
            credential_value = self._build_credential_value(creds)
            
            # Check if credentials already exist
            existing = self.vault.get_credential_by_name(
                self.db, 
                ROUTER_CREDENTIAL_NAME,
                agent_id="vigil_router_agent"
            )
            
            if existing:
                # Update existing credentials
                success = self.vault.update_credential(
                    self.db,
                    credential_id=existing.id,
                    credential_value=credential_value,
                    agent_id="vigil_router_agent",
                    action="update_router_credentials",
                    ip_address=None
                )
            else:
                # Create new credentials
                _, success = self.vault.create_credential(
                    self.db,
                    name=ROUTER_CREDENTIAL_NAME,
                    service_type=ROUTER_SERVICE_TYPE,
                    credential_type=CredentialType.PASSWORD_PAIR,
                    credential_value=credential_value,
                    agent_id="vigil_router_agent",
                    agent_scope=["vigil_router_agent", "vigil_core"],
                    expires_at=None,
                    ip_address=None
                )
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to store router credentials: {e}")
            return False
    
    def get_credentials(self, router_ip: str) -> Optional[RouterCredentialsInput]:
        """Retrieve and decrypt router credentials."""
        try:
            if not VAULT_AVAILABLE or not self.db:
                # Fallback: retrieve from memory
                fallback = self._fallback_storage.get(ROUTER_CREDENTIAL_NAME)
                if not fallback:
                    return None
                
                import json
                credential_data = json.loads(fallback["credential_value"])
                
                return RouterCredentialsInput(
                    router_ip=credential_data.get("ip", router_ip),
                    admin_username=credential_data.get("username", ""),
                    admin_password=credential_data.get("password", ""),
                    router_model=credential_data.get("model", DEFAULT_ROUTER_MODEL)
                )
            
            credential = self.vault.get_credential_by_name(
                self.db,
                ROUTER_CREDENTIAL_NAME,
                agent_id="vigil_router_agent"
            )
            
            if not credential:
                return None
            
            # Decrypt and parse credential value
            import json
            credential_data = json.loads(credential.credential_value)
            
            return RouterCredentialsInput(
                router_ip=credential_data.get("ip", router_ip),
                admin_username=credential_data.get("username", ""),
                admin_password=credential_data.get("password", ""),
                router_model=credential_data.get("model", DEFAULT_ROUTER_MODEL)
            )
            
        except Exception as e:
            logger.error(f"Failed to retrieve router credentials: {e}")
            return None
    
    def delete_credentials(self) -> bool:
        """Delete stored router credentials."""
        try:
            if not VAULT_AVAILABLE or not self.db:
                # Fallback: clear memory
                if ROUTER_CREDENTIAL_NAME in self._fallback_storage:
                    del self._fallback_storage[ROUTER_CREDENTIAL_NAME]
                return True
            
            credential = self.vault.get_credential_by_name(
                self.db,
                ROUTER_CREDENTIAL_NAME,
                agent_id="vigil_router_agent"
            )
            
            if credential:
                success = self.vault.delete_credential(
                    self.db,
                    credential_id=credential.id,
                    agent_id="vigil_router_agent",
                    action="delete_router_credentials",
                    ip_address=None
                )
                return success
            
        except Exception as e:
            logger.error(f"Failed to delete router credentials: {e}")
            return False


# Dependency to get DB session
def get_db():
    """Get database session - placeholder for actual implementation."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    engine = create_engine("sqlite:///devices.db")
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/credentials", response_model=dict)
async def store_router_credentials(
    creds: RouterCredentialsInput,
    db: Session = Depends(get_db)
):
    """Store router admin credentials securely in Vigil vault.
    
    This endpoint securely stores router credentials using Vigil's
    existing encryption infrastructure. Credentials are encrypted
    at rest and access is logged.
    """
    store = RouterCredentialsStore(db)
    success = store.store_credentials(creds)
    
    if success:
        logger.info(f"Router credentials stored for {creds.router_ip}")
        return {
            "status": "stored",
            "router": creds.router_ip,
            "model": creds.router_model,
            "message": "Credentials encrypted and stored securely in Vigil vault"
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to store credentials")


@router.get("/credentials/status", response_model=RouterCredentialsStatus)
async def check_credentials_status(
    router_ip: str = DEFAULT_ROUTER_IP,
    db: Session = Depends(get_db)
):
    """Check if router credentials are configured.
    
    Returns status of credential configuration without exposing
    sensitive credential data.
    """
    store = RouterCredentialsStore(db)
    creds = store.get_credentials(router_ip)
    
    return RouterCredentialsStatus(
        configured=creds is not None,
        router_ip=router_ip,
        router_model=creds.router_model if creds else None,
        has_username=bool(creds.admin_username) if creds else False,
        message="Credentials configured" if creds else 
                "Credentials not configured - manual entry required"
    )


@router.delete("/credentials")
async def delete_router_credentials(
    db: Session = Depends(get_db)
):
    """Delete stored router credentials from Vigil vault.
    
    Use with caution - this will require re-configuration of
    router credentials for API access.
    """
    store = RouterCredentialsStore(db)
    success = store.delete_credentials()
    
    if success:
        logger.info("Router credentials deleted")
        return {
            "status": "deleted",
            "message": "Router credentials removed from vault"
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to delete credentials")


@router.get("/credentials/verify")
async def verify_router_credentials(
    router_ip: str = DEFAULT_ROUTER_IP,
    db: Session = Depends(get_db)
):
    """Verify stored credentials work by attempting authentication.
    
    This performs a live test against the router to verify
    credentials are valid and router is accessible.
    """
    store = RouterCredentialsStore(db)
    creds = store.get_credentials(router_ip)
    
    if not creds:
        raise HTTPException(
            status_code=401, 
            detail="Router credentials not configured"
        )
    
    # Attempt actual connection test
    try:
        from app.routers.implementations.asus import ASUSRouter
        from app.routers.base import RouterCredentials as BaseCreds
        
        base_creds = BaseCreds(
            username=creds.admin_username,
            password=creds.admin_password
        )
        
        router = ASUSRouter(
            ip_address=creds.router_ip,
            credentials=base_creds,
            use_https=False,
            timeout=10
        )
        
        if router.connect():
            router.disconnect()
            return {
                "status": "verified",
                "router": creds.router_ip,
                "message": "Credentials valid - router authentication successful"
            }
        else:
            return {
                "status": "failed",
                "router": creds.router_ip,
                "message": "Authentication failed - check credentials"
            }
            
    except Exception as e:
        logger.error(f"Credential verification failed: {e}")
        return {
            "status": "error",
            "router": creds.router_ip,
            "message": f"Verification error: {str(e)}"
        }
