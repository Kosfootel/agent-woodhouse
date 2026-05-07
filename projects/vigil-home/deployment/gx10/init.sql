-- Create Vigil database tables

CREATE TABLE IF NOT EXISTS devices (
    id SERIAL PRIMARY KEY,
    mac_address VARCHAR(17) UNIQUE NOT NULL,
    ip_address INET,
    device_type VARCHAR(50),
    device_name VARCHAR(100),
    vendor VARCHAR(100),
    trust_score FLOAT DEFAULT 0.5,
    trust_alpha INT DEFAULT 1,
    trust_omega INT DEFAULT 1,
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    metadata JSONB
);

CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    device_id INT REFERENCES devices(id),
    event_type VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source_ip INET,
    dest_ip INET,
    source_port INT,
    dest_port INT,
    protocol VARCHAR(10),
    payload_size INT,
    raw_data JSONB,
    processed BOOLEAN DEFAULT false
);

CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    device_id INT REFERENCES devices(id),
    event_id INT REFERENCES events(id),
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) CHECK (severity IN ('info', 'low', 'medium', 'high', 'critical')),
    title VARCHAR(200),
    description TEXT,
    narrative TEXT,
    recommendation TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    acknowledged BOOLEAN DEFAULT false,
    resolved BOOLEAN DEFAULT false
);

CREATE TABLE IF NOT EXISTS trust_history (
    id SERIAL PRIMARY KEY,
    device_id INT REFERENCES devices(id),
    old_score FLOAT,
    new_score FLOAT,
    reason VARCHAR(100),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_devices_mac ON devices(mac_address);
CREATE INDEX IF NOT EXISTS idx_devices_trust ON devices(trust_score);
CREATE INDEX IF NOT EXISTS idx_events_device ON events(device_id);
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
CREATE INDEX IF NOT EXISTS idx_alerts_device ON alerts(device_id);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity);
CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp);
