package com.sessionmanager.model.dto;

import java.util.ArrayList;
import java.util.List;

public class IntegrityVerificationDTO {
    private String sessionId;
    private boolean valid;
    private int totalEventsEvaluated;
    private int verifiedEventsCount;
    private List<Integer> brokenLinks = new ArrayList<>();
    private List<String> issues = new ArrayList<>();
    private String verificationTimestamp;

    public IntegrityVerificationDTO() {}

    public String getSessionId() {
        return sessionId;
    }

    public void setSessionId(String sessionId) {
        this.sessionId = sessionId;
    }

    public boolean isValid() {
        return valid;
    }

    public void setValid(boolean valid) {
        this.valid = valid;
    }

    public int getTotalEventsEvaluated() {
        return totalEventsEvaluated;
    }

    public void setTotalEventsEvaluated(int totalEventsEvaluated) {
        this.totalEventsEvaluated = totalEventsEvaluated;
    }

    public int getVerifiedEventsCount() {
        return verifiedEventsCount;
    }

    public void setVerifiedEventsCount(int verifiedEventsCount) {
        this.verifiedEventsCount = verifiedEventsCount;
    }

    public List<Integer> getBrokenLinks() {
        return brokenLinks;
    }

    public void setBrokenLinks(List<Integer> brokenLinks) {
        this.brokenLinks = brokenLinks;
    }

    public List<String> getIssues() {
        return issues;
    }

    public void setIssues(List<String> issues) {
        this.issues = issues;
    }

    public String getVerificationTimestamp() {
        return verificationTimestamp;
    }

    public void setVerificationTimestamp(String verificationTimestamp) {
        this.verificationTimestamp = verificationTimestamp;
    }
}
