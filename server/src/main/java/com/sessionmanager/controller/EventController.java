package com.sessionmanager.controller;

import com.sessionmanager.model.dto.EventBatchRequest;
import com.sessionmanager.service.SessionRecordingService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/events")
@CrossOrigin(origins = "*")
public class EventController {

    @Autowired
    private SessionRecordingService recordingService;

    @PostMapping
    public ResponseEntity<Void> receiveEvents(@RequestBody EventBatchRequest request) {
        if (request == null || request.getSessionId() == null || request.getEncryptedEvents() == null) {
            return ResponseEntity.badRequest().build();
        }

        recordingService.processEvents(request.getEncryptedEvents(), request.getSessionId());
        return ResponseEntity.status(HttpStatus.CREATED).build();
    }
}
