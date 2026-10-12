package com.sessionmanager.repository;

import com.sessionmanager.model.SessionEvent;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;

@Repository
public interface SessionEventRepository extends JpaRepository<SessionEvent, Long> {

    @Query("SELECT e FROM SessionEvent e WHERE e.session.sessionId = :sessionId ORDER BY e.id ASC")
    List<SessionEvent> findBySessionIdOrderByTimestampAsc(@Param("sessionId") String sessionId);

    @Query("SELECT COUNT(e) FROM SessionEvent e WHERE e.session.sessionId = :sessionId")
    int countBySessionId(@Param("sessionId") String sessionId);

    @Modifying
    @Query("DELETE FROM SessionEvent e WHERE e.receivedAt < :cutoffDate")
    int purgeEventsOlderThan(@Param("cutoffDate") LocalDateTime cutoffDate);
}
