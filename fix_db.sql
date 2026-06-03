-- Recreate devices table with new schema
DROP TABLE IF EXISTS devices;

CREATE TABLE devices (
    id INTEGER PRIMARY KEY,
    mac VARCHAR UNIQUE,
    ip VARCHAR,
    hostname VARCHAR,
    nickname VARCHAR,
    vendor VARCHAR,
    device_type VARCHAR,
    trust_score FLOAT DEFAULT 50.0,
    containment_status VARCHAR DEFAULT 'observing',
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    online BOOLEAN DEFAULT 1,
    discovery_method VARCHAR DEFAULT 'manual',
    is_known BOOLEAN DEFAULT 0,
    last_ip_change TIMESTAMP
);

-- Insert old devices (6 devices from old data)
INSERT INTO devices (id, mac, ip, hostname, nickname, vendor, device_type, trust_score, containment_status, first_seen, last_seen, online, discovery_method, is_known) VALUES
(1, '30:C5:99:3E:A4:D4', '192.168.50.30', 'GX-10', 'GX-10 (Vigil Server)', NULL, NULL, 0.8, 'observing', '2026-05-20T20:29:15.474050', '2026-05-20T20:29:15.474050', 1, 'imported', 0),
(2, 'A8:6E:84:F5:3A:B4', '192.168.50.2', 'unknown', 'Gateway Device', NULL, NULL, 0.8, 'observing', '2026-05-20T20:29:15.474050', '2026-05-20T20:29:15.474050', 1, 'imported', 0),
(3, '40:6C:8F:0E:12:7F', '192.168.50.32', 'bettermachine-host', 'Dashboard Server', NULL, NULL, 0.8, 'observing', '2026-05-20T20:29:15.474050', '2026-05-20T20:29:15.474050', 1, 'imported', 0),
(4, 'C8:A3:62:14:21:58', '192.168.50.201', 'ERoss-31701', 'Erik''s Workstation', NULL, NULL, 0.8, 'observing', '2026-05-20T20:29:15.474050', '2026-05-20T20:29:15.474050', 1, 'imported', 0),
(5, '00:23:81:69:00:DF', '192.168.50.23', 'liz', 'Liz''s Device', NULL, NULL, 0.8, 'observing', '2026-05-20T20:29:15.474050', '2026-05-20T20:29:15.474050', 1, 'imported', 0),
(6, '00:E0:4C:BE:FA:CC', '192.168.50.24', 'unknown', 'Woodhouse (MBP_EDR_M1)', NULL, NULL, 0.8, 'observing', '2026-05-20T20:29:15.474050', '2026-05-20T20:29:15.474050', 1, 'imported', 0);

-- Create other required tables
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY,
    device_id INTEGER,
    type VARCHAR,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY,
    device_id INTEGER,
    type VARCHAR,
    severity VARCHAR,
    message TEXT,
    acknowledged BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    acknowledged_at TIMESTAMP,
    acknowledged_by VARCHAR
);

-- Create indices
CREATE INDEX IF NOT EXISTS idx_devices_mac ON devices(mac);
CREATE INDEX IF NOT EXISTS idx_devices_ip ON devices(ip);
CREATE INDEX IF NOT EXISTS idx_events_device_id ON events(device_id);
CREATE INDEX IF NOT EXISTS idx_alerts_device_id ON alerts(device_id);
