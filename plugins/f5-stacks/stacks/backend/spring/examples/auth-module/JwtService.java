package com.example.app.service;

import io.jsonwebtoken.*;
import io.jsonwebtoken.io.Decoders;
import io.jsonwebtoken.security.Keys;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Service;

import javax.crypto.SecretKey;
import java.util.Date;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.function.Function;

@Slf4j
@Service
public class JwtService {

    @Value("${jwt.secret}")
    private String secretKey;

    @Value("${jwt.expiration:86400000}")
    private long jwtExpiration; // 24 hours default

    @Value("${jwt.refresh-expiration:604800000}")
    private long refreshExpiration; // 7 days default

    // Simple in-memory blacklist (use Redis in production)
    private final Map<String, Long> blacklistedTokens = new ConcurrentHashMap<>();

    public String extractUsername(String token) {
        return extractClaim(token, Claims::getSubject);
    }

    public String extractTokenId(String token) {
        return extractClaim(token, Claims::getId);
    }

    public <T> T extractClaim(String token, Function<Claims, T> claimsResolver) {
        final Claims claims = extractAllClaims(token);
        return claimsResolver.apply(claims);
    }

    public String generateToken(UserDetails userDetails) {
        return generateToken(new HashMap<>(), userDetails);
    }

    public String generateToken(Map<String, Object> extraClaims, UserDetails userDetails) {
        return buildToken(extraClaims, userDetails, jwtExpiration);
    }

    public String generateRefreshToken(UserDetails userDetails) {
        return buildToken(new HashMap<>(), userDetails, refreshExpiration);
    }

    private String buildToken(
            Map<String, Object> extraClaims,
            UserDetails userDetails,
            long expiration) {

        return Jwts.builder()
            .id(UUID.randomUUID().toString())
            .claims(extraClaims)
            .subject(userDetails.getUsername())
            .issuedAt(new Date(System.currentTimeMillis()))
            .expiration(new Date(System.currentTimeMillis() + expiration))
            .signWith(getSigningKey())
            .compact();
    }

    public boolean isTokenValid(String token, UserDetails userDetails) {
        final String username = extractUsername(token);
        return (username.equals(userDetails.getUsername()))
            && !isTokenExpired(token)
            && !isTokenBlacklisted(token);
    }

    public boolean isTokenExpired(String token) {
        return extractExpiration(token).before(new Date());
    }

    private Date extractExpiration(String token) {
        return extractClaim(token, Claims::getExpiration);
    }

    private Claims extractAllClaims(String token) {
        return Jwts.parser()
            .verifyWith(getSigningKey())
            .build()
            .parseSignedClaims(token)
            .getPayload();
    }

    private SecretKey getSigningKey() {
        byte[] keyBytes = Decoders.BASE64.decode(secretKey);
        return Keys.hmacShaKeyFor(keyBytes);
    }

    // ==================== Token Blacklisting ====================

    public void blacklistToken(String token) {
        try {
            String tokenId = extractTokenId(token);
            Date expiration = extractExpiration(token);
            blacklistedTokens.put(tokenId, expiration.getTime());
            log.info("Token blacklisted: {}", tokenId);
        } catch (Exception e) {
            log.warn("Failed to blacklist token: {}", e.getMessage());
        }
    }

    public boolean isTokenBlacklisted(String token) {
        try {
            String tokenId = extractTokenId(token);
            return blacklistedTokens.containsKey(tokenId);
        } catch (Exception e) {
            return false;
        }
    }

    // Clean up expired blacklisted tokens (call periodically)
    public void cleanupBlacklist() {
        long now = System.currentTimeMillis();
        blacklistedTokens.entrySet().removeIf(entry -> entry.getValue() < now);
    }

    // ==================== Token Validation ====================

    public TokenValidationResult validateToken(String token) {
        try {
            Claims claims = extractAllClaims(token);

            if (isTokenBlacklisted(token)) {
                return new TokenValidationResult(false, "Token has been revoked", null);
            }

            if (claims.getExpiration().before(new Date())) {
                return new TokenValidationResult(false, "Token has expired", null);
            }

            return new TokenValidationResult(true, null, claims.getSubject());

        } catch (ExpiredJwtException e) {
            return new TokenValidationResult(false, "Token has expired", null);
        } catch (MalformedJwtException e) {
            return new TokenValidationResult(false, "Invalid token format", null);
        } catch (SecurityException e) {
            return new TokenValidationResult(false, "Invalid token signature", null);
        } catch (Exception e) {
            return new TokenValidationResult(false, "Token validation failed: " + e.getMessage(), null);
        }
    }

    public record TokenValidationResult(boolean valid, String error, String username) {}

    // ==================== Token Info ====================

    public long getExpirationTime() {
        return jwtExpiration;
    }

    public long getRefreshExpirationTime() {
        return refreshExpiration;
    }
}
