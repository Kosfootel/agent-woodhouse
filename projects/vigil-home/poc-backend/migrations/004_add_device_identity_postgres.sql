-- Migration 004: Add device identity fields for layperson-friendly UI
-- Run this against the Postgres database

-- Add new columns to devices table
ALTER TABLE devices 
ADD COLUMN IF NOT EXISTS nickname VARCHAR(128),
ADD COLUMN IF NOT EXISTS icon_type VARCHAR(64),
ADD COLUMN IF NOT EXISTS containment_status VARCHAR(32) DEFAULT 'pending_review',
ADD COLUMN IF NOT EXISTS user_trust_override BOOLEAN DEFAULT FALSE;

-- Backfill containment_status based on trust_score
UPDATE devices 
SET containment_status = CASE
    WHEN trust_score > 0.7 THEN 'trusted'
    WHEN trust_score < 0.3 THEN 'blocked'
    ELSE 'observing'
END
WHERE containment_status = 'pending_review' OR containment_status IS NULL;

-- Backfill icon_type based on device_type
UPDATE devices SET icon_type = 'smartphone' WHERE device_type IN ('phone', 'mobile') AND icon_type IS NULL;
UPDATE devices SET icon_type = 'laptop' WHERE device_type IN ('computer', 'laptop') AND icon_type IS NULL;
UPDATE devices SET icon_type = 'desktop' WHERE device_type = 'desktop' AND icon_type IS NULL;
UPDATE devices SET icon_type = 'tv' WHERE device_type IN ('tv', 'media') AND icon_type IS NULL;
UPDATE devices SET icon_type = 'camera' WHERE device_type IN ('camera', 'security_camera') AND icon_type IS NULL;
UPDATE devices SET icon_type = 'device' WHERE device_type IN ('iot', 'smart_device') AND icon_type IS NULL;
UPDATE devices SET icon_type = 'router' WHERE device_type = 'router' AND icon_type IS NULL;
UPDATE devices SET icon_type = 'server' WHERE device_type = 'server' AND icon_type IS NULL;

-- Verify the migration
SELECT 
    COUNT(*) as total_devices,
    COUNT(nickname) as devices_with_nickname,
    COUNT(icon_type) as devices_with_icon,
    COUNT(DISTINCT containment_status) as containment_statuses,
    containment_status
FROM devices 
GROUP BY containment_status;
