package com.sessionmanager.model.dto;

public class SessionStartResponse {
    private String sessionId;
    private String status;
    private String message;

    public SessionStartResponse() {}

    public SessionStartResponse(String sessionId) {
        this.sessionId = sessionId;
        this.status = "ACTIVE";
        this.message = "Session created successfully";
    }

    public String getSessionId() {
        return sessionId;
    }

    public void setSessionId(String sessionId) {
        this.sessionId = sessionId;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public String getMessage() {
        return message;
    }

    public void setMessage(String message) {
        this.message = message;
    }
}
