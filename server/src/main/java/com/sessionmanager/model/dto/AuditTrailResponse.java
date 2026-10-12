package com.sessionmanager.model.dto;

import java.util.List;

public class AuditTrailResponse {
    private String sessionId;
    private int totalEvents;
    private boolean chainValid;
    private List<AuditTrailDTO> events;

    public AuditTrailResponse() {}

    public AuditTrailResponse(String sessionId, int totalEvents, boolean chainValid, List<AuditTrailDTO> events) {
        this.sessionId = sessionId;
        this.totalEvents = totalEvents;
        this.chainValid = chainValid;
        this.events = events;
    }

    public String getSessionId() {
        return sessionId;
    }

    public void setSessionId(String sessionId) {
        this.sessionId = sessionId;
    }

    public int getTotalEvents() {
        return totalEvents;
    }

    public void setTotalEvents(int totalEvents) {
        this.totalEvents = totalEvents;
    }

    public boolean isChainValid() {
        return chainValid;
    }

    public void setChainValid(boolean chainValid) {
        this.chainValid = chainValid;
    }

    public List<AuditTrailDTO> getEvents() {
        return events;
    }

    public void setEvents(List<AuditTrailDTO> events) {
        this.events = events;
    }
}
