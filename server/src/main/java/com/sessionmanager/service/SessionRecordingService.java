package com.sessionmanager.service;

import com.google.gson.Gson;
import com.google.gson.reflect.TypeToken;
import com.sessionmanager.model.Session;
import com.sessionmanager.model.SessionEvent;
import com.sessionmanager.model.SessionStatus;
import com.sessionmanager.model.dto.AuditTrailDTO;
import com.sessionmanager.model.dto.IntegrityVerificationDTO;
import com.sessionmanager.model.dto.SessionEventDTO;
import com.sessionmanager.repository.SessionEventRepository;
import com.sessionmanager.repository.SessionRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.lang.reflect.Type;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.stream.Collectors;

/**
 * SessionRecordingService (CORE NOVELTY)
 * Coordinates privacy-preserving session recording ingest, AES-256 decryption,
 * HMAC-SHA256 integrity verification, tamper detection, and audit trail presentation.
 */
@Service
public class SessionRecordingService {

    private static final Logger log = LoggerFactory.getLogger(SessionRecordingService.class);
    private static final Gson gson = new Gson();
    private static final Type MAP_TYPE = new TypeToken<Map<String, Object>>() {}.getType();

    @Autowired
    private CryptoService cryptoService;

    @Autowired
    private IntegrityVerificationService integrityService;

    @Autowired
    private SessionRepository sessionRepository;

    @Autowired
    private SessionEventRepository eventRepository;

    @Autowired
    private AlertService alertService;

    /**
     * Ingests a batch of AES-256 encrypted events, decrypts them,
     * verifies HMAC integrity and hash chain continuity, and persists valid events.
     */
    @Transactional
    public void processEvents(List<String> encryptedEventsBase64, String sessionId) {
        if (encryptedEventsBase64 == null || encryptedEventsBase64.isEmpty()) {
            return;
        }

        Session session = sessionRepository.findById(sessionId)
                .orElseGet(() -> {
                    Session created = new Session(sessionId, "UNKNOWN_HOST", LocalDateTime.now(), SessionStatus.ACTIVE);
                    return sessionRepository.save(created);
                });

        for (String encryptedToken : encryptedEventsBase64) {
            try {
                // 1. Decrypt AES-256 Fernet token
                String decryptedJson = cryptoService.decryptAES256Fernet(encryptedToken);
                SessionEventDTO eventDto = gson.fromJson(decryptedJson, SessionEventDTO.class);

                // 2. Verify HMAC integrity signature
                boolean hmacValid = integrityService.verifyIntegrity(eventDto);
                if (!hmacValid) {
                    log.warn("HMAC integrity signature verification failed for event in session {}", sessionId);
                    alertService.sendTamperAlert(sessionId, "Invalid HMAC signature on event: " + eventDto.getEventType());
                }

                // 3. Verify hash chain continuity
                boolean chainValid = integrityService.verifyHashChain(eventDto, sessionId);
                if (!chainValid) {
                    log.error("Hash chain broken in session {}! Possible unauthorized tamper or replay.", sessionId);
                    alertService.sendTamperAlert(sessionId, "Cryptographic hash chain broken at event: " + eventDto.getEventType());
                }

                // 4. Save to repository with verified flag
                SessionEvent entity = new SessionEvent();
                entity.setSession(session);

                LocalDateTime eventTime;
                try {
                    eventTime = LocalDateTime.parse(eventDto.getTimestamp(), DateTimeFormatter.ISO_DATE_TIME);
                } catch (Exception ex) {
                    eventTime = LocalDateTime.now();
                }

                entity.setTimestamp(eventTime);
                entity.setEventType(eventDto.getEventType());
                entity.setEventData(gson.toJson(eventDto.getEventData()));
                entity.setIntegrityHash(eventDto.getIntegrityHash());
                entity.setPreviousEventHash(eventDto.getPreviousEventHash());
                entity.setReceivedAt(LocalDateTime.now());
                entity.setVerified(hmacValid && chainValid);

                eventRepository.save(entity);

            } catch (Exception e) {
                log.error("Failed to process encrypted event token in session {}: {}", sessionId, e.getMessage());
            }
        }
    }

    /**
     * Retrieves privacy-preserving audit trail for a session.
     */
    @Transactional(readOnly = true)
    public List<AuditTrailDTO> getAuditTrail(String sessionId, String machineId, LocalDate date) {
        List<SessionEvent> events;

        if (sessionId != null && !sessionId.isEmpty()) {
            events = eventRepository.findBySessionIdOrderByTimestampAsc(sessionId);
        } else if (machineId != null && !machineId.isEmpty()) {
            List<Session> sessions = sessionRepository.findByMachineId(machineId);
            events = sessions.stream()
                    .flatMap(s -> eventRepository.findBySessionIdOrderByTimestampAsc(s.getSessionId()).stream())
                    .sorted(Comparator.comparing(SessionEvent::getTimestamp))
                    .collect(Collectors.toList());
        } else {
            events = eventRepository.findAll().stream()
                    .sorted(Comparator.comparing(SessionEvent::getTimestamp))
                    .limit(200)
                    .collect(Collectors.toList());
        }

        return events.stream().map(this::mapToAuditDTO).collect(Collectors.toList());
    }

    /**
     * Performs cryptographic validation of the session's hash chain to verify authenticity.
     */
    @Transactional(readOnly = true)
    public IntegrityVerificationDTO verifySessionIntegrity(String sessionId) {
        return integrityService.verifyFullChain(sessionId);
    }

    private AuditTrailDTO mapToAuditDTO(SessionEvent entity) {
        AuditTrailDTO dto = new AuditTrailDTO();
        dto.setId(entity.getId());
        dto.setSessionId(entity.getSession().getSessionId());
        dto.setTimestamp(entity.getTimestamp().toString());
        dto.setEventType(entity.getEventType());

        Map<String, Object> dataMap = Collections.emptyMap();
        try {
            dataMap = gson.fromJson(entity.getEventData(), MAP_TYPE);
        } catch (Exception ignored) {}

        dto.setEventData(dataMap);
        dto.setIntegrityHash(entity.getIntegrityHash());
        dto.setPreviousEventHash(entity.getPreviousEventHash());
        dto.setVerified(entity.isVerified());
        return dto;
    }

    /**
     * GDPR auto-purge: purge events older than 30 days every 24 hours.
     */
    @Scheduled(cron = "0 0 2 * * ?") // 2:00 AM daily
    @Transactional
    public void purgeExpiredEvents() {
        LocalDateTime cutoff = LocalDateTime.now().minusDays(30);
        int purged = eventRepository.purgeEventsOlderThan(cutoff);
        log.info("GDPR Retention Purge executed: removed {} events older than 30 days.", purged);
    }
}
