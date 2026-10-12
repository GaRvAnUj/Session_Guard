package com.sessionmanager.security;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.Collections;

@Component
public class ApiKeyAuthenticationFilter extends OncePerRequestFilter {

    private final String expectedApiKey;
    private final JwtTokenProvider jwtTokenProvider;

    public ApiKeyAuthenticationFilter(
            @Value("${session-manager.api.client-api-key:secure-client-api-key-2026-public-lab}") String expectedApiKey,
            JwtTokenProvider jwtTokenProvider) {
        this.expectedApiKey = expectedApiKey;
        this.jwtTokenProvider = jwtTokenProvider;
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
            throws ServletException, IOException {

        String path = request.getRequestURI();

        // 1. Check for Client API Key (used by Python agent for /api/events, /api/sessions/start, etc.)
        String apiKeyHeader = request.getHeader("X-API-KEY");
        if (apiKeyHeader != null && apiKeyHeader.equals(expectedApiKey)) {
            UsernamePasswordAuthenticationToken auth = new UsernamePasswordAuthenticationToken(
                    "CLIENT_AGENT", null, Collections.singletonList(new SimpleGrantedAuthority("ROLE_CLIENT")));
            SecurityContextHolder.getContext().setAuthentication(auth);
            filterChain.doFilter(request, response);
            return;
        }

        // 2. Check for Admin JWT Bearer Token (used by React Dashboard)
        String authHeader = request.getHeader("Authorization");
        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            String token = authHeader.substring(7);
            if (jwtTokenProvider.validateToken(token)) {
                String username = jwtTokenProvider.getUsernameFromToken(token);
                UsernamePasswordAuthenticationToken auth = new UsernamePasswordAuthenticationToken(
                        username, null, Collections.singletonList(new SimpleGrantedAuthority("ROLE_ADMIN")));
                SecurityContextHolder.getContext().setAuthentication(auth);
                filterChain.doFilter(request, response);
                return;
            }
        }

        // Pass through - Spring Security will authorize public endpoints or reject secured ones
        filterChain.doFilter(request, response);
    }
}
