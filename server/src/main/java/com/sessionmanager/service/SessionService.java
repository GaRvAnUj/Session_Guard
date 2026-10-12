package com.sessionmanager.service;

import com.sessionmanager.model.AuditLog;
import com.sessionmanager.model.Session;
import com.sessionmanager.model.SessionStatus;
import com.sessionmanager.model.dto.ActiveSessionDTO;
import com.sessionmanager.repository.AuditLogRepository;
import com.sessionmanager.repository.SessionEventRepository;
import com.sessionmanager.repository.SessionRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class SessionService {

    private static final Logger log = LoggerFactory.getLogger(SessionService.class);

    @Autowired
    private SessionRepository sessionRepository;

    @Autowired
    private SessionEventRepository eventRepository;

    @Autowired
    private AuditLogRepository auditLogRepository;

    @Autowired
    private AlertService alertService;

    // In-memory queue of pending administrative commands keyed by machineId
    private final Map<String, List<Map<String, Object>>> machineCommandQueue = new ConcurrentHashMap<>();
    private final Map<String, List<Map<String, Object>>> machineQuarantineItems = new ConcurrentHashMap<>();

    @Transactional
    public String createSession(String machineId) {
        String sessionId = "sess_" + machineId + "_" + UUID.randomUUID().toString().replace("-", "").substring(0, 12);
        Session session = new Session(sessionId, machineId, LocalDateTime.now(), SessionStatus.ACTIVE);
        sessionRepository.save(session);

        auditLogRepository.save(new AuditLog(sessionId, machineId, "SESSION_START", "Session initialized by client", LocalDateTime.now()));
        alertService.sendSessionStatusUpdate(sessionId, machineId, "ACTIVE");

        log.info("Created new session {} for machine {}", sessionId, machineId);
        return sessionId;
    }

    @Transactional
    public void endSession(String sessionId) {
        Optional<Session> opt = sessionRepository.findById(sessionId);
        if (opt.isPresent()) {
            Session session = opt.get();
            session.setStatus(SessionStatus.COMPLETED);
            session.setEndTime(LocalDateTime.now());
            sessionRepository.save(session);

            auditLogRepository.save(new AuditLog(sessionId, session.getMachineId(), "SESSION_END", "Session completed", LocalDateTime.now()));
            alertService.sendSessionStatusUpdate(sessionId, session.getMachineId(), "COMPLETED");

            log.info("Session {} completed.", sessionId);
        }
    }

    @Transactional(readOnly = true)
    public List<ActiveSessionDTO> getActiveSessions() {
        List<Session> active = sessionRepository.findByStatus(SessionStatus.ACTIVE);
        List<ActiveSessionDTO> dtos = new ArrayList<>();

        for (Session s : active) {
            int eventCount = eventRepository.countBySessionId(s.getSessionId());
            dtos.add(new ActiveSessionDTO(
                    s.getSessionId(),
                    s.getMachineId(),
                    s.getStartTime(),
                    s.getStatus().name(),
                    eventCount,
                    true
            ));
        }
        return dtos;
    }

    @Transactional
    public void panicLock(String machineId, String reason, String adminUser) {
        log.warn("Triggering PANIC LOCK on machine {} by {}: {}", machineId, adminUser, reason);

        // Find active session on machine
        Optional<Session> activeSession = sessionRepository.findFirstByMachineIdAndStatusOrderByStartTimeDesc(
                machineId, SessionStatus.ACTIVE);

        String sessionId = activeSession.map(Session::getSessionId).orElse("NONE");
        if (activeSession.isPresent()) {
            Session s = activeSession.get();
            s.setStatus(SessionStatus.PANIC_LOCKED);
            s.setEndTime(LocalDateTime.now());
            sessionRepository.save(s);
        }

        // Add to machine's pending command queue so client executes immediately
        List<Map<String, Object>> cmds = machineCommandQueue.computeIfAbsent(machineId, k -> new ArrayList<>());
        Map<String, Object> panicCmd = new HashMap<>();
        panicCmd.put("type", "PANIC_LOCK");
        panicCmd.put("machineId", machineId);
        panicCmd.put("reason", reason);
        panicCmd.put("timestamp", LocalDateTime.now().toString());
        cmds.add(panicCmd);

        auditLogRepository.save(new AuditLog(sessionId, machineId, "PANIC_LOCK", "Panic lock ordered by " + adminUser + ": " + reason, LocalDateTime.now()));
        alertService.sendPanicLockAlert(machineId, sessionId, reason);
    }

    public List<Map<String, Object>> getPendingCommands(String machineId) {
        List<Map<String, Object>> cmds = machineCommandQueue.remove(machineId);
        return cmds != null ? cmds : Collections.emptyList();
    }

    public void syncQuarantineItems(String machineId, List<Map<String, Object>> items) {
        List<Map<String, Object>> records = new ArrayList<>();
        for (Map<String, Object> item : items) {
            Map<String, Object> record = new HashMap<>(item);
            record.put("machineId", machineId);
            records.add(record);
        }
        machineQuarantineItems.put(machineId, records);
    }

    public List<Map<String, Object>> getQuarantineItems() {
        List<Map<String, Object>> items = new ArrayList<>();
        machineQuarantineItems.values().forEach(items::addAll);
        return items;
    }

    public void queueQuarantineAction(String machineId, List<String> itemIds, String action, String authorizedBy) {
        Set<String> knownIds = new HashSet<>();
        for (Map<String, Object> item : machineQuarantineItems.getOrDefault(machineId, Collections.emptyList())) {
            Object itemId = item.get("itemId");
            if (itemId != null) {
                knownIds.add(itemId.toString());
            }
        }
        if (itemIds == null || itemIds.isEmpty() || !knownIds.containsAll(itemIds)) {
            throw new IllegalArgumentException("Select valid quarantined files for this workstation.");
        }
        Map<String, Object> command = new HashMap<>();
        command.put("type", action);
        command.put("itemIds", new ArrayList<>(itemIds));
        command.put("authorizedBy", authorizedBy);
        command.put("requestedAt", LocalDateTime.now().toString());
        machineCommandQueue.computeIfAbsent(machineId, key -> new ArrayList<>()).add(command);
    }
}
