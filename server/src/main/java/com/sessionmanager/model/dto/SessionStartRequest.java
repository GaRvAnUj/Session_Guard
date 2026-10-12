package com.sessionmanager.model.dto;

public class SessionStartRequest {
    private String machineId;

    public SessionStartRequest() {}

    public SessionStartRequest(String machineId) {
        this.machineId = machineId;
    }

    public String getMachineId() {
        return machineId;
    }

    public void setMachineId(String machineId) {
        this.machineId = machineId;
    }
}
