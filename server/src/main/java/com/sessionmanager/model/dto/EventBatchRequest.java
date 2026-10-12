package com.sessionmanager.model.dto;

import java.util.List;

public class EventBatchRequest {
    private String sessionId;
    private List<String> encryptedEvents; // Base64 encoded Fernet/AES-256 tokens
    private Integer batchCount;

    public EventBatchRequest() {}

    public String getSessionId() {
        return sessionId;
    }

    public void setSessionId(String sessionId) {
        this.sessionId = sessionId;
    }

    public List<String> getEncryptedEvents() {
        return encryptedEvents;
    }

    public void setEncryptedEvents(List<String> encryptedEvents) {
        this.encryptedEvents = encryptedEvents;
    }

    public Integer getBatchCount() {
        return batchCount;
    }

    public void setBatchCount(Integer batchCount) {
        this.batchCount = batchCount;
    }
}
