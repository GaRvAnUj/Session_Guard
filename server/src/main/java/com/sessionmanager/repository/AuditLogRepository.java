package com.sessionmanager.repository;

import com.sessionmanager.model.AuditLog;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface AuditLogRepository extends JpaRepository<AuditLog, Long> {
    List<AuditLog> findBySessionIdOrderByTimestampDesc(String sessionId);
    List<AuditLog> findByMachineIdOrderByTimestampDesc(String machineId);
}
