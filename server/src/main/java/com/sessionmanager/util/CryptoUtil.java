package com.sessionmanager.util;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.sessionmanager.model.dto.SessionEventDTO;

import javax.crypto.Cipher;
import javax.crypto.Mac;
import javax.crypto.spec.IvParameterSpec;
import javax.crypto.spec.SecretKeySpec;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.*;

public class CryptoUtil {

    private static final Gson canonicalGson = new GsonBuilder().create();

    public static String sha256Hex(String input) {
        if (input == null) return "";
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hash = digest.digest(input.getBytes(StandardCharsets.UTF_8));
            StringBuilder hexString = new StringBuilder();
            for (byte b : hash) {
                String hex = Integer.toHexString(0xff & b);
                if (hex.length() == 1) hexString.append('0');
                hexString.append(hex);
            }
            return hexString.toString();
        } catch (Exception e) {
            throw new RuntimeException("SHA-256 failure: " + e.getMessage(), e);
        }
    }

    public static String computeHmacSha256(byte[] hmacKey, String data) {
        try {
            Mac mac = Mac.getInstance("HmacSHA256");
            SecretKeySpec secretKeySpec = new SecretKeySpec(hmacKey, "HmacSHA256");
            mac.init(secretKeySpec);
            byte[] hmacBytes = mac.doFinal(data.getBytes(StandardCharsets.UTF_8));
            StringBuilder hexString = new StringBuilder();
            for (byte b : hmacBytes) {
                String hex = Integer.toHexString(0xff & b);
                if (hex.length() == 1) hexString.append('0');
                hexString.append(hex);
            }
            return hexString.toString();
        } catch (Exception e) {
            throw new RuntimeException("HMAC computation failure: " + e.getMessage(), e);
        }
    }

    /**
     * Serializes event metadata canonically (sorted keys) matching Python client.
     */
    public static String createCanonicalEventString(SessionEventDTO event) {
        Map<String, Object> canonicalMap = new TreeMap<>();
        canonicalMap.put("session_id", event.getSessionId());
        canonicalMap.put("timestamp", event.getTimestamp());
        canonicalMap.put("event_type", event.getEventType());
        canonicalMap.put("event_data", event.getEventData() != null ? new TreeMap<>(event.getEventData()) : Collections.emptyMap());
        canonicalMap.put("previous_event_hash", event.getPreviousEventHash());
        return canonicalGson.toJson(canonicalMap);
    }

    /**
     * Decrypts Python Fernet token (AES-128-CBC with PKCS7 padding & HMAC-SHA256 signing)
     * Fernet token format: Version (1 byte) || Timestamp (8 bytes) || IV (16 bytes) || Ciphertext (variable) || HMAC (32 bytes)
     */
    public static String decryptFernet(String fernetTokenBase64, byte[] fernetKeyBytes) throws Exception {
        byte[] token = Base64.getUrlDecoder().decode(fernetTokenBase64);
        if (token.length < 57) {
            throw new IllegalArgumentException("Invalid Fernet token length");
        }

        // Split Fernet 32-byte key: first 16 bytes for signing, second 16 bytes for AES encryption
        byte[] signingKey = Arrays.copyOfRange(fernetKeyBytes, 0, 16);
        byte[] encryptionKey = Arrays.copyOfRange(fernetKeyBytes, 16, 32);

        // Verify HMAC
        byte[] dataToVerify = Arrays.copyOfRange(token, 0, token.length - 32);
        byte[] receivedHmac = Arrays.copyOfRange(token, token.length - 32, token.length);

        Mac mac = Mac.getInstance("HmacSHA256");
        mac.init(new SecretKeySpec(signingKey, "HmacSHA256"));
        byte[] computedHmac = mac.doFinal(dataToVerify);

        if (!MessageDigest.isEqual(receivedHmac, computedHmac)) {
            throw new SecurityException("Fernet token signature validation failed");
        }

        // Extract IV and Ciphertext
        byte[] iv = Arrays.copyOfRange(token, 9, 25);
        byte[] ciphertext = Arrays.copyOfRange(token, 25, token.length - 32);

        Cipher cipher = Cipher.getInstance("AES/CBC/PKCS5Padding");
        cipher.init(Cipher.DECRYPT_MODE, new SecretKeySpec(encryptionKey, "AES"), new IvParameterSpec(iv));
        byte[] decrypted = cipher.doFinal(ciphertext);

        return new String(decrypted, StandardCharsets.UTF_8);
    }
}
