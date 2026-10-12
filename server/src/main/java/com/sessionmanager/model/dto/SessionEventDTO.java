package com.sessionmanager.model.dto;

import com.google.gson.annotations.SerializedName;
import java.util.Map;

public class SessionEventDTO {

    @SerializedName("session_id")
    private String sessionId;

    @SerializedName("timestamp")
    private String timestamp;

    @SerializedName("event_type")
    private String eventType;

    @SerializedName("event_data")
    private Map<String, Object> eventData;

    @SerializedName("previous_event_hash")
    private String previousEventHash;

    @SerializedName("integrity_hash")
    private String integrityHash;

    public SessionEventDTO() {}

    public String getSessionId() {
        return sessionId;
    }

    public void setSessionId(String sessionId) {
        this.sessionId = sessionId;
    }

    public String getTimestamp() {
        return timestamp;
    }

    public void setTimestamp(String timestamp) {
        this.timestamp = timestamp;
    }

    public String getEventType() {
        return eventType;
    }

    public void setEventType(String eventType) {
        this.eventType = eventType;
    }

    public Map<String, Object> getEventData() {
        return eventData;
    }

    public void setEventData(Map<String, Object> eventData) {
        this.eventData = eventData;
    }

    public String getPreviousEventHash() {
        return previousEventHash;
    }

    public void setPreviousEventHash(String previousEventHash) {
        this.previousEventHash = previousEventHash;
    }

    public String getIntegrityHash() {
        return integrityHash;
    }

    public void setIntegrityHash(String integrityHash) {
        this.integrityHash = integrityHash;
    }
}
