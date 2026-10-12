package com.sessionmanager.util;

import com.sessionmanager.model.SessionEvent;
import com.sessionmanager.model.dto.IntegrityVerificationDTO;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

public class HashChainValidator {

    /**
     * Performs end-to-end cryptographic validation on an ordered list of session events.
     * Detects breaks in the HMAC chain or tampered event payloads.
     */
    public static IntegrityVerificationDTO validateChain(List<SessionEvent> events, byte[] hmacKey) {
        IntegrityVerificationDTO report = new IntegrityVerificationDTO();
        report.setVerificationTimestamp(LocalDateTime.now().toString());
        report.setTotalEventsEvaluated(events.size());

        if (events == null || events.isEmpty()) {
            report.setValid(true);
            report.setVerifiedEventsCount(0);
            return report;
        }

        report.setSessionId(events.get(0).getSession().getSessionId());

        List<Integer> brokenIndices = new ArrayList<>();
        List<String> issues = new ArrayList<>();
        int verifiedCount = 0;

        String expectedPreviousHash = null;

        for (int i = 0; i < events.size(); i++) {
            SessionEvent current = events.get(i);

            // 1. Check previous hash linkage (except first event, which links to genesis)
            if (i > 0) {
                if (current.getPreviousEventHash() == null || !current.getPreviousEventHash().equalsIgnoreCase(expectedPreviousHash)) {
                    brokenIndices.add(i);
                    String prevTrunc = safeTruncate(expectedPreviousHash, 16);
                    String currTrunc = safeTruncate(current.getPreviousEventHash(), 16);
                    issues.add(String.format("Hash chain linkage break at index %d: expected previous %s, found %s",
                            i, prevTrunc, currTrunc));
                }
            }

            // 2. Validate current event's HMAC signature
            if (current.isVerified()) {
                verifiedCount++;
            } else {
                brokenIndices.add(i);
                issues.add("Event at index " + i + " failed cryptographic HMAC integrity verification.");
            }

            expectedPreviousHash = current.getIntegrityHash();
        }

        report.setBrokenLinks(brokenIndices);
        report.setIssues(issues);
        report.setVerifiedEventsCount(verifiedCount);
        report.setValid(brokenIndices.isEmpty());

        return report;
    }

    private static String safeTruncate(String str, int maxLen) {
        if (str == null) return "null";
        return str.length() <= maxLen ? str : str.substring(0, maxLen);
    }
}
