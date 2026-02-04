# JWT Authentication

JWT token authentication implementation for Spring Boot REST APIs.

## Dependencies

```groovy
dependencies {
    implementation 'io.jsonwebtoken:jjwt-api:0.12.3'
    runtimeOnly 'io.jsonwebtoken:jjwt-impl:0.12.3'
    runtimeOnly 'io.jsonwebtoken:jjwt-jackson:0.12.3'
}
```

## Configuration

```yaml
# application.yml
app:
  jwt:
    secret: ${JWT_SECRET:your-256-bit-secret-key-here-must-be-at-least-256-bits}
    access-token-expiration: 900000      # 15 minutes in milliseconds
    refresh-token-expiration: 604800000  # 7 days in milliseconds
    issuer: myapp
```

## JWT Service

```java
package com.example.app.security;

import io.jsonwebtoken.*;
import io.jsonwebtoken.io.Decoders;
import io.jsonwebtoken.security.Keys;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Service;

import javax.crypto.SecretKey;
import java.util.*;
import java.util.function.Function;
import java.util.stream.Collectors;

@Slf4j
@Service
public class JwtService {

    @Value("${app.jwt.secret}")
    private String secretKey;

    @Value("${app.jwt.access-token-expiration}")
    private long accessTokenExpiration;

    @Value("${app.jwt.refresh-token-expiration}")
    private long refreshTokenExpiration;

    @Value("${app.jwt.issuer}")
    private String issuer;

    // Token blacklist (in production, use Redis)
    private final Set<String> blacklistedTokens = Collections.synchronizedSet(new HashSet<>());

    /**
     * Generate access token for user.
     */
    public String generateAccessToken(UserDetails userDetails) {
        Map<String, Object> claims = new HashMap<>();
        claims.put("type", "access");
        claims.put("roles", userDetails.getAuthorities().stream()
            .map(GrantedAuthority::getAuthority)
            .collect(Collectors.toList()));

        return buildToken(claims, userDetails.getUsername(), accessTokenExpiration);
    }

    /**
     * Generate access token with custom claims.
     */
    public String generateAccessToken(UserDetails userDetails, Map<String, Object> extraClaims) {
        Map<String, Object> claims = new HashMap<>(extraClaims);
        claims.put("type", "access");
        claims.put("roles", userDetails.getAuthorities().stream()
            .map(GrantedAuthority::getAuthority)
            .collect(Collectors.toList()));

        return buildToken(claims, userDetails.getUsername(), accessTokenExpiration);
    }

    /**
     * Generate refresh token for user.
     */
    public String generateRefreshToken(UserDetails userDetails) {
        Map<String, Object> claims = new HashMap<>();
        claims.put("type", "refresh");

        return buildToken(claims, userDetails.getUsername(), refreshTokenExpiration);
    }

    /**
     * Build JWT token with claims.
     */
    private String buildToken(Map<String, Object> claims, String subject, long expiration) {
        return Jwts.builder()
            .claims(claims)
            .subject(subject)
            .issuer(issuer)
            .issuedAt(new Date())
            .expiration(new Date(System.currentTimeMillis() + expiration))
            .id(UUID.randomUUID().toString())  // Unique token ID
            .signWith(getSigningKey(), Jwts.SIG.HS256)
            .compact();
    }

    /**
     * Validate token against user details.
     */
    public boolean isTokenValid(String token, UserDetails userDetails) {
        try {
            final String username = extractUsername(token);
            return username.equals(userDetails.getUsername())
                && !isTokenExpired(token)
                && !isTokenBlacklisted(token);
        } catch (JwtException e) {
            log.warn("JWT validation failed: {}", e.getMessage());
            return false;
        }
    }

    /**
     * Validate refresh token.
     */
    public boolean isRefreshTokenValid(String token) {
        try {
            Claims claims = extractAllClaims(token);
            String type = claims.get("type", String.class);
            return "refresh".equals(type)
                && !isTokenExpired(token)
                && !isTokenBlacklisted(token);
        } catch (JwtException e) {
            log.warn("Refresh token validation failed: {}", e.getMessage());
            return false;
        }
    }

    /**
     * Extract username from token.
     */
    public String extractUsername(String token) {
        return extractClaim(token, Claims::getSubject);
    }

    /**
     * Extract expiration from token.
     */
    public Date extractExpiration(String token) {
        return extractClaim(token, Claims::getExpiration);
    }

    /**
     * Extract token ID (jti).
     */
    public String extractTokenId(String token) {
        return extractClaim(token, Claims::getId);
    }

    /**
     * Extract roles from token.
     */
    @SuppressWarnings("unchecked")
    public List<String> extractRoles(String token) {
        Claims claims = extractAllClaims(token);
        return claims.get("roles", List.class);
    }

    /**
     * Extract specific claim from token.
     */
    public <T> T extractClaim(String token, Function<Claims, T> claimsResolver) {
        final Claims claims = extractAllClaims(token);
        return claimsResolver.apply(claims);
    }

    /**
     * Check if token is expired.
     */
    public boolean isTokenExpired(String token) {
        return extractExpiration(token).before(new Date());
    }

    /**
     * Invalidate token by adding to blacklist.
     */
    public void invalidateToken(String token) {
        String tokenId = extractTokenId(token);
        blacklistedTokens.add(tokenId);
        log.info("Token invalidated: {}", tokenId);
    }

    /**
     * Check if token is blacklisted.
     */
    public boolean isTokenBlacklisted(String token) {
        String tokenId = extractTokenId(token);
        return blacklistedTokens.contains(tokenId);
    }

    /**
     * Extract all claims from token.
     */
    private Claims extractAllClaims(String token) {
        return Jwts.parser()
            .verifyWith(getSigningKey())
            .build()
            .parseSignedClaims(token)
            .getPayload();
    }

    /**
     * Get signing key from secret.
     */
    private SecretKey getSigningKey() {
        byte[] keyBytes = Decoders.BASE64.decode(secretKey);
        return Keys.hmacShaKeyFor(keyBytes);
    }

    /**
     * Get access token expiration in seconds.
     */
    public long getAccessTokenExpirationSeconds() {
        return accessTokenExpiration / 1000;
    }
}
```

## JWT Authentication Filter

```java
package com.example.app.security;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.lang.NonNull;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.web.authentication.WebAuthenticationDetailsSource;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;

@Slf4j
@Component
@RequiredArgsConstructor
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    private final JwtService jwtService;
    private final UserDetailsService userDetailsService;

    @Override
    protected void doFilterInternal(
            @NonNull HttpServletRequest request,
            @NonNull HttpServletResponse response,
            @NonNull FilterChain filterChain
    ) throws ServletException, IOException {

        // Get Authorization header
        final String authHeader = request.getHeader("Authorization");

        // Check if header is present and starts with Bearer
        if (authHeader == null || !authHeader.startsWith("Bearer ")) {
            filterChain.doFilter(request, response);
            return;
        }

        try {
            // Extract token (remove "Bearer " prefix)
            final String jwt = authHeader.substring(7);
            final String username = jwtService.extractUsername(jwt);

            // If username exists and user not already authenticated
            if (username != null && SecurityContextHolder.getContext().getAuthentication() == null) {
                UserDetails userDetails = userDetailsService.loadUserByUsername(username);

                // Validate token
                if (jwtService.isTokenValid(jwt, userDetails)) {
                    UsernamePasswordAuthenticationToken authToken = new UsernamePasswordAuthenticationToken(
                        userDetails,
                        null,
                        userDetails.getAuthorities()
                    );

                    authToken.setDetails(
                        new WebAuthenticationDetailsSource().buildDetails(request)
                    );

                    // Set authentication in security context
                    SecurityContextHolder.getContext().setAuthentication(authToken);

                    log.debug("Authenticated user: {}", username);
                }
            }
        } catch (Exception e) {
            log.error("Cannot set user authentication: {}", e.getMessage());
        }

        filterChain.doFilter(request, response);
    }

    @Override
    protected boolean shouldNotFilter(HttpServletRequest request) {
        String path = request.getServletPath();
        return path.startsWith("/api/v1/auth/")
            || path.startsWith("/actuator/")
            || path.startsWith("/swagger-ui/")
            || path.startsWith("/v3/api-docs");
    }
}
```

## Auth Service

```java
package com.example.app.service;

import com.example.app.domain.entity.User;
import com.example.app.exception.InvalidCredentialsException;
import com.example.app.exception.UserAlreadyExistsException;
import com.example.app.repository.UserRepository;
import com.example.app.security.CustomUserDetails;
import com.example.app.security.JwtService;
import com.example.app.web.dto.*;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Slf4j
@Service
@RequiredArgsConstructor
public class AuthService {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtService jwtService;
    private final AuthenticationManager authenticationManager;

    @Transactional
    public AuthResponse register(RegisterRequest request) {
        log.info("Registering user: {}", request.email());

        // Check if user exists
        if (userRepository.existsByEmailIgnoreCase(request.email())) {
            throw new UserAlreadyExistsException("Email already registered");
        }

        // Create user
        User user = User.builder()
            .email(request.email().toLowerCase())
            .passwordHash(passwordEncoder.encode(request.password()))
            .firstName(request.firstName())
            .lastName(request.lastName())
            .isActive(true)
            .build();

        user.addRole(Role.USER);  // Default role

        User savedUser = userRepository.save(user);

        // Generate tokens
        CustomUserDetails userDetails = new CustomUserDetails(savedUser);
        String accessToken = jwtService.generateAccessToken(userDetails);
        String refreshToken = jwtService.generateRefreshToken(userDetails);

        log.info("User registered successfully: {}", savedUser.getId());

        return new AuthResponse(
            accessToken,
            refreshToken,
            jwtService.getAccessTokenExpirationSeconds(),
            toUserResponse(savedUser)
        );
    }

    public AuthResponse login(LoginRequest request) {
        log.info("Login attempt for: {}", request.email());

        try {
            // Authenticate
            authenticationManager.authenticate(
                new UsernamePasswordAuthenticationToken(
                    request.email().toLowerCase(),
                    request.password()
                )
            );
        } catch (AuthenticationException e) {
            log.warn("Login failed for: {}", request.email());
            throw new InvalidCredentialsException("Invalid email or password");
        }

        // Get user
        User user = userRepository.findByEmailIgnoreCase(request.email())
            .orElseThrow(() -> new InvalidCredentialsException("Invalid email or password"));

        // Update last login
        user.setLastLoginAt(Instant.now());
        userRepository.save(user);

        // Generate tokens
        CustomUserDetails userDetails = new CustomUserDetails(user);
        String accessToken = jwtService.generateAccessToken(userDetails);
        String refreshToken = jwtService.generateRefreshToken(userDetails);

        log.info("Login successful for: {}", user.getId());

        return new AuthResponse(
            accessToken,
            refreshToken,
            jwtService.getAccessTokenExpirationSeconds(),
            toUserResponse(user)
        );
    }

    public TokenResponse refreshToken(RefreshTokenRequest request) {
        String refreshToken = request.refreshToken();

        // Validate refresh token
        if (!jwtService.isRefreshTokenValid(refreshToken)) {
            throw new InvalidCredentialsException("Invalid or expired refresh token");
        }

        // Get username from token
        String username = jwtService.extractUsername(refreshToken);

        // Get user
        User user = userRepository.findByEmailIgnoreCase(username)
            .orElseThrow(() -> new InvalidCredentialsException("User not found"));

        // Generate new access token
        CustomUserDetails userDetails = new CustomUserDetails(user);
        String newAccessToken = jwtService.generateAccessToken(userDetails);

        return new TokenResponse(
            newAccessToken,
            jwtService.getAccessTokenExpirationSeconds()
        );
    }

    private UserResponse toUserResponse(User user) {
        return new UserResponse(
            user.getId(),
            user.getEmail(),
            user.getFirstName(),
            user.getLastName(),
            user.getRoles().stream().map(Role::getName).toList()
        );
    }
}
```

## Token Blacklist with Redis

```java
package com.example.app.security;

import lombok.RequiredArgsConstructor;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.util.Date;

@Service
@RequiredArgsConstructor
public class TokenBlacklistService {

    private static final String BLACKLIST_PREFIX = "jwt:blacklist:";

    private final RedisTemplate<String, String> redisTemplate;

    public void blacklistToken(String token, Date expiration) {
        String tokenId = extractTokenId(token);
        String key = BLACKLIST_PREFIX + tokenId;

        // Calculate TTL (time until token expires)
        long ttlMillis = expiration.getTime() - System.currentTimeMillis();

        if (ttlMillis > 0) {
            redisTemplate.opsForValue().set(
                key,
                "blacklisted",
                Duration.ofMillis(ttlMillis)
            );
        }
    }

    public boolean isBlacklisted(String token) {
        String tokenId = extractTokenId(token);
        String key = BLACKLIST_PREFIX + tokenId;
        return Boolean.TRUE.equals(redisTemplate.hasKey(key));
    }

    private String extractTokenId(String token) {
        // Extract jti claim
        return jwtService.extractTokenId(token);
    }
}
```

## Response with Tokens in Cookies (Optional)

```java
@RestController
@RequestMapping("/api/v1/auth")
public class AuthController {

    @PostMapping("/login")
    public ResponseEntity<AuthResponse> login(
            @Valid @RequestBody LoginRequest request,
            HttpServletResponse response) {

        AuthResponse authResponse = authService.login(request);

        // Set refresh token in HTTP-only cookie
        ResponseCookie refreshCookie = ResponseCookie.from("refreshToken", authResponse.refreshToken())
            .httpOnly(true)
            .secure(true)
            .path("/api/v1/auth/refresh")
            .maxAge(Duration.ofDays(7))
            .sameSite("Strict")
            .build();

        response.addHeader(HttpHeaders.SET_COOKIE, refreshCookie.toString());

        // Return access token in body only
        return ResponseEntity.ok(new AuthResponse(
            authResponse.accessToken(),
            null,  // Don't include refresh token in body
            authResponse.expiresIn(),
            authResponse.user()
        ));
    }
}
```

## Best Practices

1. **Use strong secret keys** - At least 256 bits for HS256
2. **Short access token lifetime** - 15-30 minutes
3. **Longer refresh token lifetime** - 7-30 days
4. **Token blacklisting** - Implement logout functionality
5. **Refresh token rotation** - Issue new refresh token on refresh
6. **Store refresh tokens securely** - HTTP-only cookies or secure storage
7. **Include minimal claims** - Don't store sensitive data in tokens
8. **Validate all claims** - issuer, expiration, audience
9. **Use HTTPS only** - Never transmit tokens over HTTP
10. **Log authentication events** - For security auditing
