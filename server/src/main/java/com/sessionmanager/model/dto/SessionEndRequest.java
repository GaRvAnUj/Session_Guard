package com.sessionmanager.model.dto;

public class SessionEndRequest {
    private String sessionId;

    public SessionEndRequest() {}

    public SessionEndRequest(String sessionId) {
        this.sessionId = sessionId;
    }

    public String getSessionId() {
        return sessionId;
    }

    public void setSessionId(String sessionId) {
        this.sessionId = sessionId;
    }
}
