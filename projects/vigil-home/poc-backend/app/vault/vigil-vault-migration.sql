-- Migration: Add Credential Vault tables for Vigil Home Automation
-- Phase 1A: Credential Vault Service
-- Created: 2026-05-20

-- =====================================================
-- Table: credential_vault
-- Stores encrypted credentials for home automation devices
-- =====================================================
CREATE TABLE IF NOT EXISTS credential_vault (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,                    -- Human-readable label
    service_type TEXT NOT NULL,            -- hue, nest, ring, myhomeid, etc.
    credential_type TEXT NOT NULL,         -- api_key, oauth_token, password, certificate
    encrypted_data BLOB NOT NULL,          -- AES-256-GCM encrypted credential data
    agent_scope TEXT,                      -- Comma-separated list of agent IDs allowed access
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME,                   -- Credential expiration for rotation alerts
    last_rotated DATETIME,
    last_accessed DATETIME,
    access_count INTEGER DEFAULT 0
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_vault_service_type ON credential_vault(service_type);
CREATE INDEX IF NOT EXISTS idx_vault_expires_at ON credential_vault(expires_at);
CREATE INDEX IF NOT EXISTS idx_vault_agent_scope ON credential_vault(agent_scope);

-- =====================================================
-- Table: credential_access_log
-- Audit trail for all credential access
-- =====================================================
CREATE TABLE IF NOT EXISTS credential_access_log (
    id TEXT PRIMARY KEY,
    credential_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,                -- Agent making the request
    action TEXT NOT NULL,                  -- read, write, rotate, delete, decrypt
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN NOT NULL,
    reason TEXT,                           -- For failed access or additional context
    ip_address TEXT,                       -- Source IP for security tracking
    FOREIGN KEY (credential_id) REFERENCES credential_vault(id) ON DELETE CASCADE
);

-- Indexes for audit queries
CREATE INDEX IF NOT EXISTS idx_access_log_credential_id ON credential_access_log(credential_id);
CREATE INDEX IF NOT EXISTS idx_access_log_agent_id ON credential_access_log(agent_id);
CREATE INDEX IF NOT EXISTS idx_access_log_timestamp ON credential_access_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_access_log_action ON credential_access_log(action);

-- =====================================================
-- View: vault_health_summary
-- Dashboard view for credential health monitoring
-- =====================================================
CREATE VIEW IF NOT EXISTS vault_health_summary AS
SELECT
    COUNT(*) as total_credentials,
    SUM(CASE WHEN expires_at IS NOT NULL AND expires_at < datetime('now', '+7 days') THEN 1 ELSE 0 END) as expiring_soon,
    SUM(CASE WHEN expires_at IS NOT NULL AND expires_at < datetime('now') THEN 1 ELSE 0 END) as expired,
    SUM(CASE WHEN last_rotated IS NULL OR (julianday('now') - julianday(last_rotated)) > 90 THEN 1 ELSE 0 END) as needs_rotation,
    MAX(access_count) as max_access_count,
    AVG(access_count) as avg_access_count
FROM credential_vault;

-- =====================================================
-- View: recent_access_activity
-- Dashboard view for recent credential access
-- =====================================================
CREATE VIEW IF NOT EXISTS recent_access_activity AS
SELECT
    l.id,
    l.credential_id,
    v.name as credential_name,
    v.service_type,
    l.agent_id,
    l.action,
    l.timestamp,
    l.success,
    l.reason
FROM credential_access_log l
JOIN credential_vault v ON l.credential_id = v.id
WHERE l.timestamp > datetime('now', '-24 hours')
ORDER BY l.timestamp DESC;
