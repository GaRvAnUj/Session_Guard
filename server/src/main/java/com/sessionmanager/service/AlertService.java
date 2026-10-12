package com.sessionmanager.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

@Service
public class AlertService {

    private static final Logger log = LoggerFactory.getLogger(AlertService.class);

    @Autowired(required = false)
    private SimpMessagingTemplate messagingTemplate;

    public void sendTamperAlert(String sessionId, String details) {
        log.warn("TAMPER ALERT dispatched for session {}: {}", sessionId, details);
        Map<String, Object> payload = new HashMap<>();
        payload.put("type", "INTEGRITY_TAMPER_ALERT");
        payload.put("sessionId", sessionId);
        payload.put("details", details);
        payload.put("timestamp", LocalDateTime.now().toString());

        broadcast("/topic/alerts", payload);
    }

    public void sendPanicLockAlert(String machineId, String sessionId, String reason) {
        log.warn("PANIC LOCK ALERT for machine {} (session {}): {}", machineId, sessionId, reason);
        Map<String, Object> payload = new HashMap<>();
        payload.put("type", "PANIC_LOCK_ALERT");
        payload.put("machineId", machineId);
        payload.put("sessionId", sessionId);
        payload.put("reason", reason);
        payload.put("timestamp", LocalDateTime.now().toString());

        broadcast("/topic/alerts", payload);
    }

    public void sendSessionStatusUpdate(String sessionId, String machineId, String status) {
        Map<String, Object> payload = new HashMap<>();
        payload.put("type", "SESSION_UPDATE");
        payload.put("sessionId", sessionId);
        payload.put("machineId", machineId);
        payload.put("status", status);
        payload.put("timestamp", LocalDateTime.now().toString());

        broadcast("/topic/sessions", payload);
    }

    private void broadcast(String destination, Object payload) {
        if (messagingTemplate != null) {
            try {
                messagingTemplate.convertAndSend(destination, payload);
            } catch (Exception e) {
                log.debug("WebSocket broadcast skipped: {}", e.getMessage());
            }
        }
    }
}
