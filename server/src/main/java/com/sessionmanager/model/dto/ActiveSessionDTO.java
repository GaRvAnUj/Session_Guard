package com.sessionmanager.model.dto;

import java.time.LocalDateTime;

public class ActiveSessionDTO {
    private String sessionId;
    private String machineId;
    private LocalDateTime startTime;
    private String status;
    private int eventCount;
    private boolean integrityValid;

    public ActiveSessionDTO() {}

    public ActiveSessionDTO(String sessionId, String machineId, LocalDateTime startTime, String status, int eventCount, boolean integrityValid) {
        this.sessionId = sessionId;
        this.machineId = machineId;
        this.startTime = startTime;
        this.status = status;
        this.eventCount = eventCount;
        this.integrityValid = integrityValid;
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

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public int getEventCount() {
        return eventCount;
    }

    public void setEventCount(int eventCount) {
        this.eventCount = eventCount;
    }

    public boolean isIntegrityValid() {
        return integrityValid;
    }

    public void setIntegrityValid(boolean integrityValid) {
        this.integrityValid = integrityValid;
    }
}
