package com.sessionmanager.model.dto;

public class PanicLockCommandDTO {
    private String machineId;
    private String reason;
    private String adminUser;

    public PanicLockCommandDTO() {}

    public PanicLockCommandDTO(String machineId, String reason, String adminUser) {
        this.machineId = machineId;
        this.reason = reason;
        this.adminUser = adminUser;
    }

    public String getMachineId() {
        return machineId;
    }

    public void setMachineId(String machineId) {
        this.machineId = machineId;
    }

    public String getReason() {
        return reason;
    }

    public void setReason(String reason) {
        this.reason = reason;
    }

    public String getAdminUser() {
        return adminUser;
    }

    public void setAdminUser(String adminUser) {
        this.adminUser = adminUser;
    }
}
