-- ====================================================================
-- Secure Session Manager - Realistic Demo Seed Data
-- ====================================================================

-- 1. Insert Demo Sessions
INSERT INTO sessions (session_id, machine_id, start_time, end_time, status) VALUES
('sess_PC_LAB_01_20261005', 'PC_LAB_01', CURRENT_TIMESTAMP - INTERVAL '45 minutes', NULL, 'ACTIVE'),
('sess_PC_LAB_02_20261005', 'PC_LAB_02', CURRENT_TIMESTAMP - INTERVAL '2 hours', CURRENT_TIMESTAMP - INTERVAL '30 minutes', 'COMPLETED'),
('sess_PC_LIBRARY_03_20261005', 'PC_LIBRARY_03', CURRENT_TIMESTAMP - INTERVAL '15 minutes', NULL, 'ACTIVE'),
('sess_PC_LAB_04_TAMPERED', 'PC_LAB_04', CURRENT_TIMESTAMP - INTERVAL '1 hour', NULL, 'ACTIVE');

-- 2. Insert Valid Session Events (Session 1: PC_LAB_01)
-- Genesis Hash: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
INSERT INTO session_events (session_id, timestamp, event_type, event_data, integrity_hash, previous_event_hash, verified) VALUES
('sess_PC_LAB_01_20261005', CURRENT_TIMESTAMP - INTERVAL '44 minutes', 'session_lifecycle', 
 '{"action":"login","machine_id":"PC_LAB_01","status":"ACTIVE"}', 
 'a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90', 
 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', TRUE),

('sess_PC_LAB_01_20261005', CURRENT_TIMESTAMP - INTERVAL '42 minutes', 'process_start', 
 '{"process_name":"chrome.exe","cpu_percent":4.5,"memory_mb":180.2,"exe_path_hash":"67406a782b535d57bdf8f1a7d65600c3b0f5de41f92e666a7b7d06bbd92aa9f3","exe_path_hash_short":"67406a782b535d57"}', 
 'b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90a1', 
 'a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90', TRUE),

('sess_PC_LAB_01_20261005', CURRENT_TIMESTAMP - INTERVAL '35 minutes', 'file_operation', 
 '{"operation":"create","extension":".pdf","size_bytes":245800,"path_hash":"8d7c3f9e2b4a1c5f6e7d8c9b0a1f2e3d4c5b6a7f8e9d0c1b2a3f4e5d6c7b8a9f","path_hash_short":"8d7c3f9e2b4a1c5f"}', 
 'c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2', 
 'b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90a1', TRUE),

('sess_PC_LAB_01_20261005', CURRENT_TIMESTAMP - INTERVAL '20 minutes', 'network_connection', 
 '{"protocol":"TCP","remote_port":443,"bytes_sent":2048,"bytes_received":8192,"remote_ip_hash":"f4b3c2a10987654321fedcba0987654321fedcba0987654321fedcba09876543","remote_ip_hash_short":"f4b3c2a109876543"}', 
 'd4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3', 
 'c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2', TRUE);

-- 3. Insert Tampered Session (For Live Demo to demonstrate detection of broken hash chain)
INSERT INTO session_events (session_id, timestamp, event_type, event_data, integrity_hash, previous_event_hash, verified) VALUES
('sess_PC_LAB_04_TAMPERED', CURRENT_TIMESTAMP - INTERVAL '58 minutes', 'process_start', 
 '{"process_name":"cmd.exe","cpu_percent":0.5,"memory_mb":25.0}', 
 '99887766554433221100aabbccddeeff99887766554433221100aabbccddeeff', 
 'genesis_hash_000000000000000000000000000000000000000000000000000', TRUE),

('sess_PC_LAB_04_TAMPERED', CURRENT_TIMESTAMP - INTERVAL '50 minutes', 'file_operation', 
 '{"operation":"write","extension":".bat","size_bytes":1024}', 
 '112233445566778899aabbccddeeff00112233445566778899aabbccddeeff00', 
 'TAMPERED_BROKEN_CHAIN_LINK_INVALID_HASH_DETECTED_HERE_XXXXXXXXX', FALSE);

-- 4. Insert Audit Logs
INSERT INTO audit_logs (session_id, machine_id, action, details) VALUES
('sess_PC_LAB_01_20261005', 'PC_LAB_01', 'SESSION_START', 'User authenticated via laboratory terminal'),
('sess_PC_LAB_02_20261005', 'PC_LAB_02', 'SESSION_END', 'DoD 5220.22-M 3-pass file wipe and browser cache purged on logout'),
('sess_PC_LAB_04_TAMPERED', 'PC_LAB_04', 'INTEGRITY_ALERT', 'Automated detector flagged broken HMAC hash chain linkage');
