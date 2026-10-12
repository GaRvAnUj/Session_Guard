package com.sessionmanager.service;

import com.sessionmanager.util.CryptoUtil;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Base64;

@Service
public class CryptoService {

    private static final Logger log = LoggerFactory.getLogger(CryptoService.class);

    private final byte[] aesKeyBytes;
    private final byte[] hmacKeyBytes;

    public CryptoService(
            @Value("${session-manager.crypto.aes-key:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=}") String aesKeyBase64,
            @Value("${session-manager.crypto.hmac-key:c2VjdXJlLXNlc3Npb24tbWFuYWdlci1obWFjLXNlY3JldC0yNTY=}") String hmacKeyBase64) {
        
        this.aesKeyBytes = deriveKey(aesKeyBase64, "default-session-aes-key");
        this.hmacKeyBytes = deriveKey(hmacKeyBase64, "default-session-hmac-key");

        log.info("CryptoService initialized with 256-bit AES and HMAC keys.");
    }

    private static byte[] deriveKey(String keyBase64, String fallbackSeed) {
        try {
            byte[] decoded;
            String cleaned = (keyBase64 != null) ? keyBase64.trim() : "";
            try {
                decoded = Base64.getUrlDecoder().decode(cleaned);
            } catch (IllegalArgumentException e1) {
                try {
                    decoded = Base64.getDecoder().decode(cleaned);
                } catch (IllegalArgumentException e2) {
                    decoded = fallbackSeed.getBytes(StandardCharsets.UTF_8);
                }
            }
            if (decoded.length == 32) {
                return decoded;
            }
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            return md.digest(decoded);
        } catch (Exception e) {
            try {
                MessageDigest md = MessageDigest.getInstance("SHA-256");
                return md.digest(fallbackSeed.getBytes(StandardCharsets.UTF_8));
            } catch (Exception fatal) {
                throw new IllegalStateException("SHA-256 algorithm unavailable", fatal);
            }
        }
    }

    public String decryptAES256Fernet(String encryptedTokenBase64) {
        try {
            return CryptoUtil.decryptFernet(encryptedTokenBase64, this.aesKeyBytes);
        } catch (Exception e) {
            log.error("Failed to decrypt AES-256 Fernet payload: {}", e.getMessage());
            throw new RuntimeException("Decryption error: " + e.getMessage(), e);
        }
    }

    public String decryptAES256(String encryptedTokenBase64) {
        return decryptAES256Fernet(encryptedTokenBase64);
    }

    public String decryptAES256(byte[] encryptedBytes) {
        if (encryptedBytes == null) {
            throw new IllegalArgumentException("Encrypted bytes cannot be null");
        }
        return decryptAES256Fernet(new String(encryptedBytes, StandardCharsets.UTF_8));
    }

    public String calculateHmac(String canonicalData) {
        return CryptoUtil.computeHmacSha256(this.hmacKeyBytes, canonicalData);
    }

    public byte[] getHmacKeyBytes() {
        return hmacKeyBytes;
    }

    public byte[] getAesKeyBytes() {
        return aesKeyBytes;
    }
}
