package com.sessionmanager.repository;

import com.sessionmanager.model.Session;
import com.sessionmanager.model.SessionStatus;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

@Repository
public interface SessionRepository extends JpaRepository<Session, String> {
    List<Session> findByStatus(SessionStatus status);
    List<Session> findByMachineId(String machineId);
    List<Session> findByStartTimeBetween(LocalDateTime start, LocalDateTime end);
    Optional<Session> findFirstByMachineIdAndStatusOrderByStartTimeDesc(String machineId, SessionStatus status);
}
