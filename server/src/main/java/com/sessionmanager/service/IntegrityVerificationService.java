package com.sessionmanager.service;

import com.sessionmanager.model.SessionEvent;
import com.sessionmanager.model.dto.IntegrityVerificationDTO;
import com.sessionmanager.model.dto.SessionEventDTO;
import com.sessionmanager.repository.SessionEventRepository;
import com.sessionmanager.util.CryptoUtil;
import com.sessionmanager.util.HashChainValidator;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class IntegrityVerificationService {

    private static final Logger log = LoggerFactory.getLogger(IntegrityVerificationService.class);

    @Autowired
    private CryptoService cryptoService;

    @Autowired
    private SessionEventRepository eventRepository;

    /**
     * Verifies the cryptographic HMAC signature of an incoming event DTO.
     */
    public boolean verifyIntegrity(SessionEventDTO event) {
        if (event == null || event.getIntegrityHash() == null) {
            return false;
        }

        String canonical = CryptoUtil.createCanonicalEventString(event);
        String expectedHmac = cryptoService.calculateHmac(canonical);

        boolean matches = expectedHmac.equalsIgnoreCase(event.getIntegrityHash());
        if (!matches) {
            log.warn("HMAC signature mismatch! Client: {}, Computed: {}", event.getIntegrityHash(), expectedHmac);
        }
        return matches;
    }

    /**
     * Verifies that the event's previous_event_hash correctly links to the preceding event.
     */
    public boolean verifyHashChain(SessionEventDTO event, String sessionId) {
        List<SessionEvent> existingEvents = eventRepository.findBySessionIdOrderByTimestampAsc(sessionId);
        if (existingEvents.isEmpty()) {
            // First event: Previous hash must be non-empty genesis hash
            return event.getPreviousEventHash() != null && !event.getPreviousEventHash().isEmpty();
        }

        SessionEvent lastEvent = existingEvents.get(existingEvents.size() - 1);
        boolean linksProperly = lastEvent.getIntegrityHash().equalsIgnoreCase(event.getPreviousEventHash());
        if (!linksProperly) {
            log.error("Hash chain break detected in session {}: Expected prev {}, found {}",
                    sessionId, lastEvent.getIntegrityHash(), event.getPreviousEventHash());
        }
        return linksProperly;
    }

    /**
     * Validates the complete cryptographic chain for all stored events in a session.
     */
    public IntegrityVerificationDTO verifyFullChain(String sessionId) {
        List<SessionEvent> events = eventRepository.findBySessionIdOrderByTimestampAsc(sessionId);
        return HashChainValidator.validateChain(events, cryptoService.getHmacKeyBytes());
    }

    public IntegrityVerificationDTO verifyFullChain(List<SessionEvent> events) {
        return HashChainValidator.validateChain(events, cryptoService.getHmacKeyBytes());
    }
}
