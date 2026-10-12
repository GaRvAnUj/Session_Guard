package com.sessionmanager.controller;

import com.sessionmanager.model.dto.AuditTrailDTO;
import com.sessionmanager.model.dto.AuditTrailResponse;
import com.sessionmanager.model.dto.IntegrityVerificationDTO;
import com.sessionmanager.service.SessionRecordingService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDate;
import java.util.List;

@RestController
@RequestMapping("/api/audit")
@CrossOrigin(origins = "*")
public class AuditController {

    @Autowired
    private SessionRecordingService recordingService;

    @GetMapping("/sessions")
    public ResponseEntity<AuditTrailResponse> getSessionAudit(
            @RequestParam(required = false) String sessionId,
            @RequestParam(required = false) String machineId,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate date) {

        List<AuditTrailDTO> auditTrail = recordingService.getAuditTrail(sessionId, machineId, date);
        IntegrityVerificationDTO verification = null;
        boolean chainValid = true;

        if (sessionId != null && !sessionId.isEmpty()) {
            verification = recordingService.verifySessionIntegrity(sessionId);
            chainValid = verification.isValid();
        }

        return ResponseEntity.ok(new AuditTrailResponse(sessionId, auditTrail.size(), chainValid, auditTrail));
    }

    @GetMapping("/verify/{sessionId}")
    public ResponseEntity<IntegrityVerificationDTO> verifyIntegrity(
            @PathVariable String sessionId,
            @RequestHeader(value = "Authorization", required = false) String authHeader) {

        // Check for admin authentication
        if (authHeader == null || !authHeader.startsWith("Bearer ")) {
            // Return unauthorized error
            IntegrityVerificationDTO errorResult = new IntegrityVerificationDTO();
            errorResult.setSessionId(sessionId);
            errorResult.setValid(false);
            errorResult.setTotalEventsEvaluated(0);
            errorResult.setVerifiedEventsCount(0);
            errorResult.getIssues().add("Unauthorized access - admin login required");
            errorResult.setVerificationTimestamp(java.time.LocalDateTime.now().toString());
            return ResponseEntity.status(401).body(errorResult);
        }

        try {
            IntegrityVerificationDTO result = recordingService.verifySessionIntegrity(sessionId);
            if (result == null) {
                // Handle null result
                IntegrityVerificationDTO nullResult = new IntegrityVerificationDTO();
                nullResult.setSessionId(sessionId);
                nullResult.setValid(false);
                nullResult.setTotalEventsEvaluated(0);
                nullResult.setVerifiedEventsCount(0);
                nullResult.getIssues().add("No events found for session " + sessionId);
                nullResult.setVerificationTimestamp(java.time.LocalDateTime.now().toString());
                return ResponseEntity.ok(nullResult);
            }
            return ResponseEntity.ok(result);
        } catch (Exception e) {
            // Return error as verification result rather than throwing exception
            IntegrityVerificationDTO errorResult = new IntegrityVerificationDTO();
            errorResult.setSessionId(sessionId);
            errorResult.setValid(false);
            errorResult.setTotalEventsEvaluated(0);
            errorResult.setVerifiedEventsCount(0);
            errorResult.getIssues().add("Verification failed: " + e.getMessage());
            errorResult.setVerificationTimestamp(java.time.LocalDateTime.now().toString());
            return ResponseEntity.ok(errorResult);
        }
    }
}
