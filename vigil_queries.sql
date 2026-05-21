-- Vigil Sample Queries
-- Common operations for the Vigil database

-- ============================================
-- DEVICES
-- ============================================

-- Get all active devices with basic info
SELECT id, mac, ip, hostname, vendor, trust_score, last_seen, nickname
FROM devices
WHERE status = 'active'
ORDER BY last_seen DESC;

-- Find device by MAC address
SELECT * FROM devices WHERE mac = 'aa:bb:cc:dd:ee:ff';

-- Insert new device
INSERT INTO devices (mac, ip, hostname, vendor, device_type, trust_score, nickname)
VALUES ('aa:bb:cc:dd:ee:ff', '192.168.50.100', 'iphone-john', 'Apple Inc.', 'phone', 75.0, 'John Phone');

-- Update device trust score
UPDATE devices 
SET trust_score = 30.0, status = 'quarantined' 
WHERE mac = 'aa:bb:cc:dd:ee:ff';

-- Update device last seen
UPDATE devices 
SET last_seen = CURRENT_TIMESTAMP, ip = '192.168.50.101'
WHERE mac = 'aa:bb:cc:dd:ee:ff';

-- Get devices with low trust scores
SELECT mac, hostname, trust_score, status
FROM devices
WHERE trust_score < 50
ORDER BY trust_score ASC;

-- Search devices by nickname or hostname
SELECT * FROM devices 
WHERE nickname LIKE '%john%' OR hostname LIKE '%john%';

-- ============================================
-- DEVICE OBSERVATIONS
-- ============================================

-- Add observation from Suricata
INSERT INTO device_observations 
(device_id, source, observation_type, raw_data, confidence)
VALUES (1, 'suricata', 'dns_query', '{"domain": "example.com", "type": "A"}', 0.95);

-- Get recent observations for a device
SELECT * FROM device_observations
WHERE device_id = 1
ORDER BY timestamp DESC
LIMIT 100;

-- Get observations by source
SELECT d.mac, d.hostname, o.observation_type, o.timestamp, o.confidence
FROM device_observations o
JOIN devices d ON o.device_id = d.id
WHERE o.source = 'suricata'
AND o.timestamp > datetime('now', '-24 hours')
ORDER BY o.timestamp DESC;

-- ============================================
-- ALERTS
-- ============================================

-- Create new alert
INSERT INTO alerts (device_id, severity, alert_type, title, description)
VALUES (1, 'high', 'new_device', 'New Device Connected', 'Unknown device detected on network');

-- Get all unacknowledged alerts
SELECT a.*, d.mac, d.hostname
FROM alerts a
LEFT JOIN devices d ON a.device_id = d.id
WHERE a.acknowledged = FALSE
ORDER BY 
    CASE a.severity 
        WHEN 'critical' THEN 1 
        WHEN 'high' THEN 2 
        WHEN 'medium' THEN 3 
        WHEN 'low' THEN 4 
        ELSE 5 
    END,
    a.created_at DESC;

-- Acknowledge an alert
UPDATE alerts 
SET acknowledged = TRUE, acknowledged_by = 'admin', acknowledged_at = CURRENT_TIMESTAMP
WHERE id = 1;

-- Get alert statistics
SELECT 
    severity, 
    COUNT(*) as total,
    SUM(CASE WHEN acknowledged THEN 1 ELSE 0 END) as acknowledged_count
FROM alerts
WHERE created_at > datetime('now', '-7 days')
GROUP BY severity;

-- ============================================
-- NETWORK FLOWS
-- ============================================

-- Record a network flow
INSERT INTO network_flows 
(source_mac, dest_mac, source_ip, dest_ip, source_port, dest_port, 
 protocol, bytes_in, bytes_out, packets_in, packets_out)
VALUES ('aa:bb:cc:dd:ee:ff', '11:22:33:44:55:66', '192.168.50.100', '8.8.8.8',
        54321, 53, 'udp', 100, 150, 1, 1);

-- Get top talkers (by bytes) in last hour
SELECT 
    source_mac,
    SUM(bytes_in + bytes_out) as total_bytes,
    COUNT(*) as flow_count
FROM network_flows
WHERE timestamp > datetime('now', '-1 hour')
GROUP BY source_mac
ORDER BY total_bytes DESC
LIMIT 10;

-- Get traffic by protocol
SELECT 
    protocol,
    COUNT(*) as flow_count,
    SUM(bytes_in + bytes_out) as total_bytes
FROM network_flows
WHERE timestamp > datetime('now', '-24 hours')
GROUP BY protocol;

-- ============================================
-- MYHOMEID SYNC
-- ============================================

-- Update sync status
UPDATE myhomeid_sync 
SET last_sync = CURRENT_TIMESTAMP, 
    sync_token = 'abc123',
    devices_synced = 15,
    last_sync_status = 'success'
WHERE id = 1;

-- Record sync failure
UPDATE myhomeid_sync 
SET last_sync = CURRENT_TIMESTAMP,
    last_sync_status = 'failed',
    last_error = 'Connection timeout after 30s'
WHERE id = 1;

-- Get current sync state
SELECT * FROM myhomeid_sync WHERE id = 1;

-- ============================================
-- ROUTER CONFIG
-- ============================================

-- Store router credentials (password should be encrypted before insert)
INSERT INTO router_config (router_ip, username, password_encrypted, config_data)
VALUES ('192.168.50.1', 'admin', 'ENCRYPTED_PASSWORD', 
        '{"model": "ASUS_RT-AC86U", "firmware": "3.0.0.4"}');

-- Update connection status
UPDATE router_config 
SET connection_status = 'connected', last_connected = CURRENT_TIMESTAMP
WHERE id = 1;

-- Get router config
SELECT router_ip, username, password_encrypted, connection_status, last_connected
FROM router_config WHERE id = 1;

-- ============================================
-- AGENT LOGS
-- ============================================

-- Log agent action
INSERT INTO agent_logs 
(agent_name, action, target_type, target_id, result, details, duration_ms)
VALUES ('device-scanner', 'device_discovery', 'device', 1, 'success', 
        '{"ip": "192.168.50.100", "method": "arp"}', 150);

-- Get recent agent activity
SELECT * FROM agent_logs
WHERE timestamp > datetime('now', '-1 hour')
ORDER BY timestamp DESC;

-- Get agent success/failure rates
SELECT 
    agent_name,
    COUNT(*) as total_actions,
    SUM(CASE WHEN result = 'success' THEN 1 ELSE 0 END) as successes,
    SUM(CASE WHEN result = 'failure' THEN 1 ELSE 0 END) as failures,
    ROUND(AVG(duration_ms), 2) as avg_duration_ms
FROM agent_logs
WHERE timestamp > datetime('now', '-24 hours')
GROUP BY agent_name;

-- ============================================
-- MAINTENANCE QUERIES
-- ============================================

-- Vacuum and optimize (run periodically)
VACUUM;
ANALYZE;

-- Check database size
SELECT 
    page_count * page_size as size_bytes,
    ROUND((page_count * page_size) / 1024.0 / 1024.0, 2) as size_mb
FROM pragma_page_count(), pragma_page_size();

-- Get table row counts
SELECT 
    'devices' as table_name, COUNT(*) as row_count FROM devices
UNION ALL
SELECT 'device_observations', COUNT(*) FROM device_observations
UNION ALL
SELECT 'alerts', COUNT(*) FROM alerts
UNION ALL
SELECT 'network_flows', COUNT(*) FROM network_flows
UNION ALL
SELECT 'agent_logs', COUNT(*) FROM agent_logs;

-- Clean old network flows (retention policy)
DELETE FROM network_flows
WHERE timestamp < datetime('now', '-30 days');

-- Archive old observations
DELETE FROM device_observations
WHERE timestamp < datetime('now', '-90 days');
