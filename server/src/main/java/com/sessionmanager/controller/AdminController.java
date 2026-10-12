package com.sessionmanager.controller;

import com.sessionmanager.model.dto.PanicLockCommandDTO;
import com.sessionmanager.security.JwtTokenProvider;
import com.sessionmanager.service.SessionService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.ArrayList;
import java.security.Principal;

@RestController
@RequestMapping("/api/admin")
@CrossOrigin(origins = "*")
public class AdminController {

    @Autowired
    private SessionService sessionService;

    @Autowired
    private JwtTokenProvider jwtTokenProvider;

    @Value("${session-manager.admin.username:admin}")
    private String adminUsername;

    @Value("${session-manager.admin.password:admin}")
    private String adminPassword;

    @PostMapping("/login")
    public ResponseEntity<Map<String, Object>> login(@RequestBody Map<String, String> credentials) {
        if (credentials == null) {
            return ResponseEntity.status(401).build();
        }
        String username = credentials.getOrDefault("username", "");
        String password = credentials.getOrDefault("password", "");

        if (adminUsername.equals(username) && adminPassword.equals(password) && !password.isEmpty()) {
            String token = jwtTokenProvider.generateToken(username, "ROLE_ADMIN");
            Map<String, Object> resp = new HashMap<>();
            resp.put("token", token);
            resp.put("username", username);
            resp.put("role", "ROLE_ADMIN");
            return ResponseEntity.ok(resp);
        }

        return ResponseEntity.status(401).build();
    }

    @PostMapping("/panic-lock")
    public ResponseEntity<Map<String, String>> triggerPanicLock(
            @RequestBody PanicLockCommandDTO request, Principal principal) {
        String machineId = request != null && request.getMachineId() != null ? request.getMachineId() : "ALL";
        String reason = request != null && request.getReason() != null ? request.getReason() : "Emergency Admin Trigger";

        sessionService.panicLock(machineId, reason, principal.getName());

        Map<String, String> resp = new HashMap<>();
        resp.put("status", "SUCCESS");
        resp.put("message", "Panic lock dispatched to " + machineId);
        return ResponseEntity.ok(resp);
    }

    @GetMapping("/commands/{machineId}")
    public ResponseEntity<List<Map<String, Object>>> pollCommands(@PathVariable String machineId) {
        List<Map<String, Object>> commands = sessionService.getPendingCommands(machineId);
        return ResponseEntity.ok(commands);
    }

    @GetMapping("/quarantine")
    public ResponseEntity<List<Map<String, Object>>> getQuarantineItems() {
        return ResponseEntity.ok(sessionService.getQuarantineItems());
    }

    @PostMapping("/quarantine/{machineId}/restore")
    public ResponseEntity<Map<String, Object>> restoreQuarantineItems(
            @PathVariable String machineId, @RequestBody Map<String, List<String>> request, Principal principal) {
        return queueQuarantineAction(machineId, request, "RESTORE_QUARANTINE", principal);
    }

    @PostMapping("/quarantine/{machineId}/permanently-delete")
    public ResponseEntity<Map<String, Object>> permanentlyDeleteQuarantineItems(
            @PathVariable String machineId, @RequestBody Map<String, List<String>> request, Principal principal) {
        return queueQuarantineAction(machineId, request, "PERMANENTLY_DELETE_QUARANTINE", principal);
    }

    private ResponseEntity<Map<String, Object>> queueQuarantineAction(
            String machineId, Map<String, List<String>> request, String action, Principal principal) {
        List<String> itemIds = request == null ? new ArrayList<>() : request.get("itemIds");
        try {
            sessionService.queueQuarantineAction(machineId, itemIds, action, principal.getName());
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().body(Map.of("detail", e.getMessage()));
        }
        return ResponseEntity.ok(Map.of("status", "QUEUED", "machineId", machineId, "count", itemIds.size()));
    }

    @GetMapping("/compliance-stats")
    public ResponseEntity<Map<String, Object>> getComplianceStats() {
        Map<String, Object> stats = new HashMap<>();
        stats.put("gdprCompliant", true);
        stats.put("retentionDays", 30);
        stats.put("screenRecordingActive", false);
        stats.put("keyloggingActive", false);
        stats.put("contentInspectionActive", false);
        stats.put("metadataHashingActive", true);
        stats.put("hmacChainVerificationActive", true);
        stats.put("adminManagedQuarantineActive", true);
        return ResponseEntity.ok(stats);
    }
}
