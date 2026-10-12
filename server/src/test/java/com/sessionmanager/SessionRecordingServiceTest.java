package com.sessionmanager;

import com.sessionmanager.model.Session;
import com.sessionmanager.model.SessionEvent;
import com.sessionmanager.model.SessionStatus;
import com.sessionmanager.model.dto.IntegrityVerificationDTO;
import com.sessionmanager.model.dto.SessionEventDTO;
import com.sessionmanager.repository.SessionEventRepository;
import com.sessionmanager.repository.SessionRepository;
import com.sessionmanager.service.CryptoService;
import com.sessionmanager.service.IntegrityVerificationService;
import com.sessionmanager.service.SessionRecordingService;
import com.sessionmanager.util.CryptoUtil;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;

import java.time.LocalDateTime;
import java.util.*;

import static org.junit.jupiter.api.Assertions.*;

@SpringBootTest
@ActiveProfiles("dev")
public class SessionRecordingServiceTest {

    @Autowired
    private SessionRecordingService recordingService;

    @Autowired
    private IntegrityVerificationService integrityService;

    @Autowired
    private CryptoService cryptoService;

    @Autowired
    private SessionRepository sessionRepository;

    @Autowired
    private SessionEventRepository eventRepository;

    private String testSessionId;

    @BeforeEach
    void setUp() {
        testSessionId = "test_sess_" + UUID.randomUUID().toString().substring(0, 8);
        Session s = new Session(testSessionId, "PC_TEST_01", LocalDateTime.now(), SessionStatus.ACTIVE);
        sessionRepository.save(s);
    }

    @Test
    void testIntegrityVerification_ValidChain_ShouldPass() {
        // Build valid chained events
        Session s = sessionRepository.findById(testSessionId).orElseThrow();
        String genesisHash = CryptoUtil.sha256Hex(testSessionId + ":genesis");

        List<SessionEvent> events = new ArrayList<>();

        String lastHash = genesisHash;
        for (int i = 0; i < 3; i++) {
            SessionEvent e = new SessionEvent();
            e.setSession(s);
            e.setTimestamp(LocalDateTime.now().plusSeconds(i));
            e.setEventType("process_start");
            e.setEventData("{\"process_name\":\"app" + i + ".exe\"}");
            e.setPreviousEventHash(lastHash);

            // Compute valid HMAC
            SessionEventDTO dto = new SessionEventDTO();
            dto.setSessionId(testSessionId);
            dto.setTimestamp(e.getTimestamp().toString());
            dto.setEventType(e.getEventType());
            dto.setPreviousEventHash(lastHash);
            Map<String, Object> map = new HashMap<>();
            map.put("process_name", "app" + i + ".exe");
            dto.setEventData(map);

            String canonical = CryptoUtil.createCanonicalEventString(dto);
            String hmac = cryptoService.calculateHmac(canonical);
            e.setIntegrityHash(hmac);
            e.setReceivedAt(LocalDateTime.now());
            e.setVerified(true);

            lastHash = hmac;
            events.add(eventRepository.save(e));
        }

        IntegrityVerificationDTO result = integrityService.verifyFullChain(events);
        assertTrue(result.isValid(), "Unmodified chain should be valid");
        assertEquals(0, result.getBrokenLinks().size(), "There should be 0 broken links");
    }

    @Test
    void testIntegrityVerification_TamperedEvent_ShouldFail() {
        Session s = sessionRepository.findById(testSessionId).orElseThrow();
        String genesisHash = CryptoUtil.sha256Hex(testSessionId + ":genesis");

        List<SessionEvent> events = new ArrayList<>();

        SessionEvent e1 = new SessionEvent();
        e1.setSession(s);
        e1.setTimestamp(LocalDateTime.now());
        e1.setEventType("process_start");
        e1.setEventData("{\"process_name\":\"calc.exe\"}");
        e1.setPreviousEventHash(genesisHash);
        e1.setIntegrityHash("valid_hmac_1");
        e1.setReceivedAt(LocalDateTime.now());
        e1.setVerified(true);
        events.add(eventRepository.save(e1));

        // Event 2 is tampered (bad previous hash)
        SessionEvent e2 = new SessionEvent();
        e2.setSession(s);
        e2.setTimestamp(LocalDateTime.now().plusSeconds(1));
        e2.setEventType("file_operation");
        e2.setEventData("{\"operation\":\"delete\"}");
        e2.setPreviousEventHash("TAMPERED_BROKEN_HASH");
        e2.setIntegrityHash("valid_hmac_2");
        e2.setReceivedAt(LocalDateTime.now());
        e2.setVerified(true);
        events.add(eventRepository.save(e2));

        IntegrityVerificationDTO result = integrityService.verifyFullChain(events);
        assertFalse(result.isValid(), "Tampered chain should be flagged as invalid");
        assertTrue(result.getBrokenLinks().contains(1), "Broken link should identify index 1");
    }
}
