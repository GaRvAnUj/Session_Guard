package com.sessionmanager;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

/**
 * Secure Session Manager - Spring Boot Main Application.
 * Novelty: Privacy-Preserving Session Recording with HMAC-SHA256 Hash Chain Integrity.
 */
@SpringBootApplication
@EnableScheduling
public class SessionManagerApplication {

    public static void main(String[] args) {
        SpringApplication.run(SessionManagerApplication.class, args);
    }
}
