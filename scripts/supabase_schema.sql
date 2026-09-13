-- ==============================================================================
-- Supabase / PostgreSQL Schema Migration: Enterprise CCTV Platform
-- Includes Departments, Cameras, Health, Maintenance, AI/LPR Detections, Users, and Audit Logs
-- Security: Row Level Security (RLS) with Service Role and Authenticated Policies
-- ==============================================================================

-- Extension setup
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ------------------------------------------------------------------------------
-- 1. Departments Table
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS departments (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) NOT NULL UNIQUE,
    category VARCHAR(100) NOT NULL,
    nodal_officer VARCHAR(255) NOT NULL,
    contact_email VARCHAR(255) NOT NULL,
    active_cameras INT DEFAULT 0,
    total_cameras INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ------------------------------------------------------------------------------
-- 2. Cameras Table (Geospatial, Technical, Storage, and Telemetry)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cameras (
    id VARCHAR(64) PRIMARY KEY,
    asset_code VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    dept_id VARCHAR(64) NOT NULL REFERENCES departments(id) ON DELETE RESTRICT,
    dept_name VARCHAR(255) NOT NULL,
    station_division VARCHAR(255),
    responsible_officer VARCHAR(255),
    officer_phone VARCHAR(50),
    
    -- Geospatial
    state VARCHAR(100) DEFAULT 'Gujarat',
    district VARCHAR(100),
    taluka VARCHAR(100),
    ward_zone VARCHAR(100),
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    altitude DOUBLE PRECISION DEFAULT 0.0,
    fov_azimuth DOUBLE PRECISION DEFAULT 0.0,
    fov_angle DOUBLE PRECISION DEFAULT 60.0,
    coverage_radius DOUBLE PRECISION DEFAULT 100.0,
    
    -- Technical & Streaming
    camera_type VARCHAR(100) DEFAULT 'Bullet',
    resolution VARCHAR(50) DEFAULT '1080p',
    fps INT DEFAULT 25,
    bitrate_kbps INT DEFAULT 4096,
    link_type VARCHAR(50) DEFAULT 'Fiber',
    bandwidth_mbps INT DEFAULT 10,
    protocol VARCHAR(50) DEFAULT 'RTSP',
    stream_url TEXT,
    
    -- Storage
    storage_arch VARCHAR(50) DEFAULT 'Edge NVR',
    nvr_ip VARCHAR(50),
    nvr_port INT DEFAULT 80,
    storage_tb DOUBLE PRECISION DEFAULT 2.0,
    retention_days INT DEFAULT 30,
    
    -- Ownership & Vendor
    ownership VARCHAR(100) DEFAULT 'State Govt',
    vendor_name VARCHAR(100),
    amc_expiry DATE,
    warranty_status VARCHAR(100) DEFAULT 'Active',
    
    -- Status & Health
    status VARCHAR(50) DEFAULT 'Active',
    is_online BOOLEAN DEFAULT TRUE,
    last_ping TIMESTAMPTZ DEFAULT NOW(),
    health_score INT DEFAULT 100,
    vms_platform_id VARCHAR(64),
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ------------------------------------------------------------------------------
-- 3. Camera Health Telemetry Table
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS camera_health (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    camera_id VARCHAR(64) NOT NULL REFERENCES cameras(id) ON DELETE CASCADE,
    is_online BOOLEAN NOT NULL DEFAULT TRUE,
    health_score INT NOT NULL CHECK (health_score BETWEEN 0 AND 100),
    ping_latency_ms DOUBLE PRECISION DEFAULT 12.5,
    packet_loss_pct DOUBLE PRECISION DEFAULT 0.0,
    fps_current INT DEFAULT 25,
    bitrate_current_kbps INT DEFAULT 4096,
    last_heartbeat TIMESTAMPTZ DEFAULT NOW(),
    diagnostics JSONB DEFAULT '{}'::jsonb,
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

-- ------------------------------------------------------------------------------
-- 4. Maintenance Tickets Table
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS maintenance (
    id VARCHAR(64) PRIMARY KEY,
    ticket_code VARCHAR(100) NOT NULL UNIQUE,
    camera_id VARCHAR(64) NOT NULL REFERENCES cameras(id) ON DELETE CASCADE,
    camera_name VARCHAR(255),
    dept_id VARCHAR(64) REFERENCES departments(id),
    dept_name VARCHAR(255),
    issue_type VARCHAR(100) NOT NULL,
    severity VARCHAR(50) NOT NULL DEFAULT 'Medium',
    status VARCHAR(50) NOT NULL DEFAULT 'Open',
    sla_due_at TIMESTAMPTZ,
    assigned_technician_id VARCHAR(64),
    assigned_technician_name VARCHAR(255),
    vendor_name VARCHAR(255),
    repair_cost_inr DOUBLE PRECISION DEFAULT 0.0,
    resolution_summary TEXT,
    photo_evidence_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ------------------------------------------------------------------------------
-- 5. AI Detections Table (Intrusions, Crowds, Anomalies)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ai_detections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    camera_id VARCHAR(64) NOT NULL REFERENCES cameras(id) ON DELETE CASCADE,
    camera_name VARCHAR(255),
    dept_name VARCHAR(255),
    detection_type VARCHAR(100) NOT NULL,
    label VARCHAR(100) NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    bbox JSONB,
    snapshot_url TEXT,
    video_url TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ------------------------------------------------------------------------------
-- 6. License Plate Detections Table (Intel OpenVINO LPR / ANPR)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS license_plate_detections (
    id VARCHAR(64) PRIMARY KEY,
    camera_id VARCHAR(64) NOT NULL REFERENCES cameras(id) ON DELETE CASCADE,
    plate_number VARCHAR(64) NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    bbox JSONB,
    image_reference TEXT,
    video_reference TEXT,
    detection_type VARCHAR(50) DEFAULT 'ANPR',
    vehicle_type VARCHAR(100) DEFAULT 'Automobile',
    vehicle_color VARCHAR(100),
    is_watchlist_hit BOOLEAN DEFAULT FALSE,
    watchlist_category VARCHAR(100),
    watchlist_severity VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ------------------------------------------------------------------------------
-- 7. Users Table (Enterprise RBAC & Clearance Governance)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(64) PRIMARY KEY,
    username VARCHAR(100) UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    full_name VARCHAR(255) NOT NULL,
    password_hash TEXT,
    role VARCHAR(50) NOT NULL DEFAULT 'OPERATOR',
    role_title VARCHAR(100) DEFAULT 'Operator',
    department_id VARCHAR(64) REFERENCES departments(id),
    department VARCHAR(255),
    employee_id VARCHAR(100) DEFAULT 'GJ-000',
    badge_code VARCHAR(100) DEFAULT 'GJ-000',
    mfa_enabled BOOLEAN DEFAULT FALSE,
    mfa_secret TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    verification_status VARCHAR(50) DEFAULT 'APPROVED',
    status VARCHAR(50) DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ------------------------------------------------------------------------------
-- 8. Audit Logs Table (Ponytail Immutable Forensics)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_logs (
    id VARCHAR(64) PRIMARY KEY,
    camera_id VARCHAR(64),
    user_id VARCHAR(64),
    user_name VARCHAR(255),
    role VARCHAR(50),
    action_type VARCHAR(100) NOT NULL,
    previous_state TEXT,
    new_state TEXT,
    justification TEXT,
    client_ip VARCHAR(50) DEFAULT '127.0.0.1',
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ------------------------------------------------------------------------------
-- Query Performance Indexes
-- ------------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_cameras_dept ON cameras(dept_id);
CREATE INDEX IF NOT EXISTS idx_cameras_geo ON cameras(latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_cameras_status ON cameras(status, is_online);
CREATE INDEX IF NOT EXISTS idx_lpr_plate ON license_plate_detections(plate_number);
CREATE INDEX IF NOT EXISTS idx_lpr_cam_time ON license_plate_detections(camera_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_lpr_watchlist ON license_plate_detections(is_watchlist_hit) WHERE is_watchlist_hit = TRUE;
CREATE INDEX IF NOT EXISTS idx_camera_health_cam ON camera_health(camera_id, recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_time ON audit_logs(timestamp DESC);

-- ------------------------------------------------------------------------------
-- Row Level Security (RLS) Configuration
-- ------------------------------------------------------------------------------
ALTER TABLE departments ENABLE ROW LEVEL SECURITY;
ALTER TABLE cameras ENABLE ROW LEVEL SECURITY;
ALTER TABLE camera_health ENABLE ROW LEVEL SECURITY;
ALTER TABLE maintenance ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_detections ENABLE ROW LEVEL SECURITY;
ALTER TABLE license_plate_detections ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- Backend Service Role Policies (Full access for FastAPI Backend)
DROP POLICY IF EXISTS service_role_all_departments ON departments;
CREATE POLICY service_role_all_departments ON departments FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS service_role_all_cameras ON cameras;
CREATE POLICY service_role_all_cameras ON cameras FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS service_role_all_health ON camera_health;
CREATE POLICY service_role_all_health ON camera_health FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS service_role_all_maintenance ON maintenance;
CREATE POLICY service_role_all_maintenance ON maintenance FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS service_role_all_ai_detections ON ai_detections;
CREATE POLICY service_role_all_ai_detections ON ai_detections FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS service_role_all_lpr ON license_plate_detections;
CREATE POLICY service_role_all_lpr ON license_plate_detections FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS service_role_all_users ON users;
CREATE POLICY service_role_all_users ON users FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS service_role_all_audit ON audit_logs;
CREATE POLICY service_role_all_audit ON audit_logs FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Authenticated Users Read-Only Access
DROP POLICY IF EXISTS authenticated_read_departments ON departments;
CREATE POLICY authenticated_read_departments ON departments FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS authenticated_read_cameras ON cameras;
CREATE POLICY authenticated_read_cameras ON cameras FOR SELECT TO authenticated USING (true);

DROP POLICY IF EXISTS authenticated_read_lpr ON license_plate_detections;
CREATE POLICY authenticated_read_lpr ON license_plate_detections FOR SELECT TO authenticated USING (true);
