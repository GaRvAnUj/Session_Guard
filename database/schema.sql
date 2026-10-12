-- ====================================================================
-- Secure Session Manager - PostgreSQL Database Schema
-- Novelty: Privacy-Preserving Session Recording with HMAC Hash Chain
-- ====================================================================

-- 1. Create Sessions Table
CREATE TABLE IF NOT EXISTS sessions (
    session_id VARCHAR(64) PRIMARY KEY,
    machine_id VARCHAR(32) NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sessions_machine_id ON sessions(machine_id);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_start_time ON sessions(start_time);

-- 2. Create Session Events Table (Privacy-Preserved Metadata Only)
CREATE TABLE IF NOT EXISTS session_events (
    id BIGSERIAL PRIMARY KEY,
    session_id VARCHAR(64) NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    event_data TEXT NOT NULL,                  -- Encrypted JSON containing privacy-sanitized metadata
    integrity_hash VARCHAR(64) NOT NULL,       -- HMAC-SHA256 signature
    previous_event_hash VARCHAR(64) NOT NULL,  -- Cryptographic hash chain pointer
    received_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    verified BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_events_session_timestamp ON session_events(session_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_events_type ON session_events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_integrity ON session_events(integrity_hash);
CREATE INDEX IF NOT EXISTS idx_events_received_at ON session_events(received_at);

-- 3. Create Audit Logs Table
CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGSERIAL PRIMARY KEY,
    session_id VARCHAR(64) NOT NULL,
    machine_id VARCHAR(32) NOT NULL,
    action VARCHAR(50) NOT NULL,
    details TEXT,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_session ON audit_logs(session_id);
CREATE INDEX IF NOT EXISTS idx_audit_machine ON audit_logs(machine_id);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp);

-- 4. Automated 30-Day GDPR Retention Policy Cleanup Function
CREATE OR REPLACE FUNCTION purge_expired_session_records() 
RETURNS INTEGER AS $$
DECLARE
    deleted_events_count INTEGER;
BEGIN
    DELETE FROM session_events 
    WHERE received_at < (CURRENT_TIMESTAMP - INTERVAL '30 days');
    GET DIAGNOSTICS deleted_events_count = ROW_COUNT;
    
    RETURN deleted_events_count;
END;
$$ LANGUAGE plpgsql;
