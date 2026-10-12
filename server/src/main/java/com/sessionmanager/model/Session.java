package com.sessionmanager.model;

import com.fasterxml.jackson.annotation.JsonManagedReference;
import jakarta.persistence.*;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

@Entity
@Table(name = "sessions", indexes = {
    @Index(name = "idx_session_machine", columnList = "machineId"),
    @Index(name = "idx_session_status", columnList = "status")
})
public class Session {

    @Id
    @Column(length = 64, nullable = false)
    private String sessionId;

    @Column(nullable = false, length = 32)
    private String machineId;

    @Column(nullable = false)
    private LocalDateTime startTime;

    @Column
    private LocalDateTime endTime;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private SessionStatus status;

    @OneToMany(mappedBy = "session", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    @JsonManagedReference
    private List<SessionEvent> events = new ArrayList<>();

    public Session() {
    }

    public Session(String sessionId, String machineId, LocalDateTime startTime, SessionStatus status) {
        this.sessionId = sessionId;
        this.machineId = machineId;
        this.startTime = startTime;
        this.status = status;
    }

    public String getSessionId() {
        return sessionId;
    }

    public void setSessionId(String sessionId) {
        this.sessionId = sessionId;
    }

    public String getMachineId() {
        return machineId;
    }

    public void setMachineId(String machineId) {
        this.machineId = machineId;
    }

    public LocalDateTime getStartTime() {
        return startTime;
    }

    public void setStartTime(LocalDateTime startTime) {
        this.startTime = startTime;
    }

    public LocalDateTime getEndTime() {
        return endTime;
    }

    public void setEndTime(LocalDateTime endTime) {
        this.endTime = endTime;
    }

    public SessionStatus getStatus() {
        return status;
    }

    public void setStatus(SessionStatus status) {
        this.status = status;
    }

    public List<SessionEvent> getEvents() {
        return events;
    }

    public void setEvents(List<SessionEvent> events) {
        this.events = events;
    }
}
