-- Vigil Unified Database Schema
-- Optimized for SQLite with WAL mode on Jetson Nano 4GB
-- Created: 2026-05-20

-- WAL mode for better concurrent read/write performance
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = -64000;  -- 64MB cache (fits within 4GB limit)
PRAGMA temp_store = MEMORY;

-- ============================================
-- 1. DEVICES - Core device registry
-- ============================================
CREATE TABLE IF NOT EXISTS devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mac TEXT UNIQUE NOT NULL,                     -- MAC address (normalized format)
    ip TEXT,                                      -- Last known IP
    hostname TEXT,                                -- Discovered or assigned hostname
    vendor TEXT,                                  -- OUI lookup result
    device_type TEXT,                             -- inferred type: phone, laptop, iot, unknown
    trust_score REAL DEFAULT 50.0 CHECK (trust_score >= 0 AND trust_score <= 100),
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'blocked', 'quarantined')),
    first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    nickname TEXT,                                -- User-friendly name
    owner TEXT,                                   -- Who owns this device
    myhomeid_reference TEXT,                      -- Link to myhomeid device ID
    metadata TEXT,                                -- JSON blob for extensible attributes
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 2. DEVICE_OBSERVATIONS - Raw data from various sources
-- ============================================
CREATE TABLE IF NOT EXISTS device_observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id INTEGER NOT NULL,
    source TEXT NOT NULL CHECK (source IN ('suricata', 'router', 'manual', 'myhomeid', 'agent')),
    observation_type TEXT NOT NULL,               -- What was observed: traffic, dhcp, arp, etc.
    raw_data TEXT,                                -- Raw observation data (JSON or text)
    confidence REAL DEFAULT 1.0 CHECK (confidence >= 0 AND confidence <= 1.0),
    ip_at_time TEXT,                              -- IP at time of observation
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE
);

-- ============================================
-- 3. ALERTS - Security events and notifications
-- ============================================
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id INTEGER,
    severity TEXT NOT NULL CHECK (severity IN ('info', 'low', 'medium', 'high', 'critical')),
    alert_type TEXT NOT NULL,                     -- Category: new_device, anomaly, threat, etc.
    title TEXT NOT NULL,
    description TEXT,
    details TEXT,                                 -- JSON blob with additional context
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_by TEXT,
    acknowledged_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE SET NULL
);

-- ============================================
-- 4. NETWORK_FLOWS - Traffic patterns and statistics
-- ============================================
CREATE TABLE IF NOT EXISTS network_flows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_mac TEXT NOT NULL,
    dest_mac TEXT,
    source_ip TEXT,
    dest_ip TEXT,
    source_port INTEGER,
    dest_port INTEGER,
    protocol TEXT,                                -- tcp, udp, icmp, etc.
    bytes_in INTEGER DEFAULT 0,
    bytes_out INTEGER DEFAULT 0,
    packets_in INTEGER DEFAULT 0,
    packets_out INTEGER DEFAULT 0,
    flow_start DATETIME,
    flow_end DATETIME,
    duration_seconds INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 5. MYHOMEID_SYNC - Sync state with myhomeid service
-- ============================================
CREATE TABLE IF NOT EXISTS myhomeid_sync (
    id INTEGER PRIMARY KEY CHECK (id = 1),        -- Single row table
    last_sync DATETIME,
    sync_token TEXT,                              -- Token for incremental sync
    devices_synced INTEGER DEFAULT 0,
    last_sync_status TEXT DEFAULT 'pending' CHECK (last_sync_status IN ('pending', 'success', 'failed', 'partial')),
    last_error TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Initialize the single row
INSERT OR IGNORE INTO myhomeid_sync (id) VALUES (1);

-- ============================================
-- 6. ROUTER_CONFIG - Stored router credentials
-- ============================================
CREATE TABLE IF NOT EXISTS router_config (
    id INTEGER PRIMARY KEY CHECK (id = 1),        -- Single row table
    router_ip TEXT NOT NULL,
    username TEXT,
    password_encrypted TEXT,                      -- Encrypted credentials
    config_data TEXT,                             -- JSON with router-specific settings
    last_connected DATETIME,
    connection_status TEXT DEFAULT 'disconnected' CHECK (connection_status IN ('connected', 'disconnected', 'error')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 7. AGENT_LOGS - Activity logging from agency agents
-- ============================================
CREATE TABLE IF NOT EXISTS agent_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_name TEXT NOT NULL,
    action TEXT NOT NULL,                         -- What the agent did
    target_type TEXT,                             -- device, alert, config, etc.
    target_id INTEGER,                            -- ID of the affected entity
    result TEXT NOT NULL CHECK (result IN ('success', 'failure', 'partial', 'skipped')),
    details TEXT,                                 -- JSON with action details
    duration_ms INTEGER,                          -- How long the action took
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- INDEXES - Optimized for Vigil query patterns
-- ============================================

-- Devices indexes
CREATE INDEX IF NOT EXISTS idx_devices_mac ON devices(mac);
CREATE INDEX IF NOT EXISTS idx_devices_status ON devices(status);
CREATE INDEX IF NOT EXISTS idx_devices_last_seen ON devices(last_seen);
CREATE INDEX IF NOT EXISTS idx_devices_trust_score ON devices(trust_score);
CREATE INDEX IF NOT EXISTS idx_devices_type ON devices(device_type);
CREATE INDEX IF NOT EXISTS idx_devices_ip ON devices(ip);

-- Observations indexes
CREATE INDEX IF NOT EXISTS idx_observations_device_id ON device_observations(device_id);
CREATE INDEX IF NOT EXISTS idx_observations_timestamp ON device_observations(timestamp);
CREATE INDEX IF NOT EXISTS idx_observations_source ON device_observations(source);
CREATE INDEX IF NOT EXISTS idx_observations_device_source ON device_observations(device_id, source);

-- Alerts indexes
CREATE INDEX IF NOT EXISTS idx_alerts_device_id ON alerts(device_id);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity);
CREATE INDEX IF NOT EXISTS idx_alerts_acknowledged ON alerts(acknowledged);
CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON alerts(created_at);
CREATE INDEX IF NOT EXISTS idx_alerts_unack_severity ON alerts(acknowledged, severity) WHERE acknowledged = FALSE;

-- Network flows indexes (partition-friendly for large tables)
CREATE INDEX IF NOT EXISTS idx_flows_source_mac ON network_flows(source_mac);
CREATE INDEX IF NOT EXISTS idx_flows_timestamp ON network_flows(timestamp);
CREATE INDEX IF NOT EXISTS idx_flows_dest_mac ON network_flows(dest_mac);
CREATE INDEX IF NOT EXISTS idx_flows_protocol ON network_flows(protocol);

-- Agent logs indexes
CREATE INDEX IF NOT EXISTS idx_agent_logs_agent ON agent_logs(agent_name);
CREATE INDEX IF NOT EXISTS idx_agent_logs_timestamp ON agent_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_agent_logs_action ON agent_logs(action);
CREATE INDEX IF NOT EXISTS idx_agent_logs_target ON agent_logs(target_type, target_id);

-- ============================================
-- VIEWS - Common query patterns
-- ============================================

-- Active devices with latest observation
CREATE VIEW IF NOT EXISTS v_active_devices AS
SELECT 
    d.*,
    (SELECT COUNT(*) FROM alerts WHERE device_id = d.id AND acknowledged = FALSE) as unacknowledged_alerts,
    (SELECT MAX(timestamp) FROM device_observations WHERE device_id = d.id) as last_observation
FROM devices d
WHERE d.status = 'active';

-- Recent alerts summary
CREATE VIEW IF NOT EXISTS v_recent_alerts AS
SELECT 
    a.*,
    d.mac as device_mac,
    d.hostname as device_hostname
FROM alerts a
LEFT JOIN devices d ON a.device_id = d.id
WHERE a.created_at > datetime('now', '-7 days')
ORDER BY a.created_at DESC;

-- High-traffic devices
CREATE VIEW IF NOT EXISTS v_device_traffic AS
SELECT 
    source_mac,
    COUNT(*) as flow_count,
    SUM(bytes_in + bytes_out) as total_bytes,
    MAX(timestamp) as last_activity
FROM network_flows
WHERE timestamp > datetime('now', '-24 hours')
GROUP BY source_mac;

-- ============================================
-- TRIGGERS - Maintain timestamps
-- ============================================

CREATE TRIGGER IF NOT EXISTS tr_devices_updated_at 
AFTER UPDATE ON devices
BEGIN
    UPDATE devices SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS tr_myhomeid_sync_updated_at 
AFTER UPDATE ON myhomeid_sync
BEGIN
    UPDATE myhomeid_sync SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS tr_router_config_updated_at 
AFTER UPDATE ON router_config
BEGIN
    UPDATE router_config SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
