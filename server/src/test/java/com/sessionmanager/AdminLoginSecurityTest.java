package com.sessionmanager;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;

import java.util.Map;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("dev")
class AdminLoginSecurityTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    void adminLoginIssuesTokenAndProtectsAdminRoutes() throws Exception {
        mockMvc.perform(get("/api/admin/quarantine"))
                .andExpect(status().isUnauthorized());
        mockMvc.perform(get("/api/audit/sessions"))
                .andExpect(status().isUnauthorized());
        mockMvc.perform(get("/api/sessions/active"))
                .andExpect(status().isUnauthorized());

        mockMvc.perform(post("/api/admin/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"username":"admin","password":"wrong"}
                                """))
                .andExpect(status().isUnauthorized());

        MvcResult loginResult = mockMvc.perform(post("/api/admin/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"username":"admin","password":"admin"}
                                """))
                .andExpect(status().isOk())
                .andReturn();
        Map<String, Object> response = objectMapper.readValue(
                loginResult.getResponse().getContentAsString(),
                new TypeReference<>() {});
        String token = (String) response.get("token");

        mockMvc.perform(get("/api/admin/quarantine")
                        .header("Authorization", "Bearer " + token))
                .andExpect(status().isOk());
        mockMvc.perform(get("/api/audit/sessions")
                        .header("Authorization", "Bearer " + token))
                .andExpect(status().isOk());
        mockMvc.perform(get("/api/sessions/active")
                        .header("Authorization", "Bearer " + token))
                .andExpect(status().isOk());
        mockMvc.perform(post("/api/sessions/start")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"machineId":"PC_CLIENT_TEST"}
                                """))
                .andExpect(status().isUnauthorized());
        mockMvc.perform(post("/api/sessions/start")
                        .header("X-API-KEY", "secure-client-api-key-2026-public-lab")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                {"machineId":"PC_CLIENT_TEST"}
                                """))
                .andExpect(status().isOk());
    }
}
