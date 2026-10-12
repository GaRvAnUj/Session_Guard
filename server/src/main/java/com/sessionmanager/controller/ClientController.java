package com.sessionmanager.controller;

import com.sessionmanager.service.SessionService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/client")
@CrossOrigin(origins = "*")
public class ClientController {

    private final SessionService sessionService;

    public ClientController(SessionService sessionService) {
        this.sessionService = sessionService;
    }

    @PutMapping("/quarantine/{machineId}")
    public ResponseEntity<Map<String, Object>> syncQuarantineItems(
            @PathVariable String machineId, @RequestBody Map<String, List<Map<String, Object>>> request) {
        List<Map<String, Object>> items = request == null ? null : request.get("items");
        if (items == null) {
            return ResponseEntity.badRequest().body(Map.of("detail", "Quarantine items are required."));
        }
        sessionService.syncQuarantineItems(machineId, items);
        return ResponseEntity.ok(Map.of("status", "SYNCED", "count", items.size()));
    }
}
