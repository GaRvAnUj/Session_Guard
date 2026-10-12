package com.sessionmanager.controller;

import com.sessionmanager.model.dto.ActiveSessionDTO;
import com.sessionmanager.model.dto.SessionEndRequest;
import com.sessionmanager.model.dto.SessionStartRequest;
import com.sessionmanager.model.dto.SessionStartResponse;
import com.sessionmanager.service.SessionService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/sessions")
@CrossOrigin(origins = "*")
public class SessionController {

    @Autowired
    private SessionService sessionService;

    @PostMapping("/start")
    public ResponseEntity<SessionStartResponse> startSession(@RequestBody SessionStartRequest request) {
        String machineId = (request != null && request.getMachineId() != null) ? request.getMachineId() : "PC_DEFAULT";
        String sessionId = sessionService.createSession(machineId);
        return ResponseEntity.ok(new SessionStartResponse(sessionId));
    }

    @PostMapping("/end")
    public ResponseEntity<Void> endSession(@RequestBody SessionEndRequest request) {
        if (request != null && request.getSessionId() != null) {
            sessionService.endSession(request.getSessionId());
        }
        return ResponseEntity.ok().build();
    }

    @GetMapping("/active")
    public ResponseEntity<List<ActiveSessionDTO>> getActiveSessions() {
        return ResponseEntity.ok(sessionService.getActiveSessions());
    }
}
