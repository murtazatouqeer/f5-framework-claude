package com.example.app.service;

import com.example.app.domain.entity.Role;
import com.example.app.domain.entity.User;
import com.example.app.domain.entity.UserStatus;
import com.example.app.exception.BusinessException;
import com.example.app.repository.RoleRepository;
import com.example.app.repository.UserRepository;
import com.example.app.web.dto.*;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.authentication.LockedException;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
public class AuthService {

    private final UserRepository userRepository;
    private final RoleRepository roleRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtService jwtService;
    private final AuthenticationManager authenticationManager;

    @Value("${auth.max-login-attempts:5}")
    private int maxLoginAttempts;

    @Value("${auth.lock-duration-minutes:30}")
    private int lockDurationMinutes;

    /**
     * Register a new user.
     */
    @Transactional
    public AuthResponse register(RegisterRequest request) {
        log.info("Registering new user: {}", request.email());

        // Check if email already exists
        if (userRepository.existsByEmail(request.email())) {
            throw new BusinessException("EMAIL_EXISTS", "Email is already registered");
        }

        // Get default role
        Role userRole = roleRepository.findByName(Role.USER)
            .orElseThrow(() -> new BusinessException("ROLE_NOT_FOUND", "Default user role not found"));

        // Create user
        User user = User.builder()
            .email(request.email().toLowerCase().trim())
            .passwordHash(passwordEncoder.encode(request.password()))
            .name(request.name().trim())
            .status(UserStatus.ACTIVE)
            .build();

        user.addRole(userRole);

        User savedUser = userRepository.save(user);
        log.info("User registered successfully: {}", savedUser.getId());

        // Generate tokens
        String accessToken = jwtService.generateToken(savedUser);
        String refreshToken = jwtService.generateRefreshToken(savedUser);

        return new AuthResponse(
            accessToken,
            refreshToken,
            jwtService.getExpirationTime(),
            mapToUserResponse(savedUser)
        );
    }

    /**
     * Authenticate user and generate tokens.
     */
    @Transactional
    public AuthResponse login(LoginRequest request, String ipAddress) {
        log.info("Login attempt for: {}", request.email());

        // Find user
        User user = userRepository.findByEmail(request.email().toLowerCase())
            .orElseThrow(() -> new BadCredentialsException("Invalid email or password"));

        // Check if account is locked
        if (!user.isAccountNonLocked()) {
            throw new LockedException("Account is locked. Please try again later.");
        }

        // Check if account is active
        if (!user.isEnabled()) {
            throw new BusinessException("ACCOUNT_DISABLED", "Account is disabled");
        }

        try {
            // Authenticate
            authenticationManager.authenticate(
                new UsernamePasswordAuthenticationToken(request.email(), request.password())
            );

            // Record successful login
            user.recordSuccessfulLogin(ipAddress);
            userRepository.save(user);

            // Generate tokens
            String accessToken = jwtService.generateToken(user);
            String refreshToken = jwtService.generateRefreshToken(user);

            log.info("User logged in successfully: {}", user.getId());

            return new AuthResponse(
                accessToken,
                refreshToken,
                jwtService.getExpirationTime(),
                mapToUserResponse(user)
            );

        } catch (BadCredentialsException e) {
            // Record failed login
            user.recordFailedLogin(maxLoginAttempts, lockDurationMinutes);
            userRepository.save(user);

            log.warn("Failed login attempt for: {} (attempt: {})", request.email(), user.getFailedLoginAttempts());
            throw new BadCredentialsException("Invalid email or password");
        }
    }

    /**
     * Refresh access token using refresh token.
     */
    @Transactional(readOnly = true)
    public AuthResponse refreshToken(RefreshTokenRequest request) {
        log.debug("Refreshing token");

        JwtService.TokenValidationResult validation = jwtService.validateToken(request.refreshToken());

        if (!validation.valid()) {
            throw new BusinessException("INVALID_REFRESH_TOKEN", validation.error());
        }

        User user = userRepository.findByEmail(validation.username())
            .orElseThrow(() -> new BusinessException("USER_NOT_FOUND", "User not found"));

        if (!user.isEnabled()) {
            throw new BusinessException("ACCOUNT_DISABLED", "Account is disabled");
        }

        // Generate new access token
        String accessToken = jwtService.generateToken(user);

        return new AuthResponse(
            accessToken,
            request.refreshToken(), // Return same refresh token
            jwtService.getExpirationTime(),
            mapToUserResponse(user)
        );
    }

    /**
     * Logout user by blacklisting their token.
     */
    public void logout(String token) {
        jwtService.blacklistToken(token);
        SecurityContextHolder.clearContext();
        log.info("User logged out successfully");
    }

    /**
     * Get current authenticated user.
     */
    @Transactional(readOnly = true)
    public UserResponse getCurrentUser() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();

        if (authentication == null || !authentication.isAuthenticated()) {
            throw new BusinessException("NOT_AUTHENTICATED", "User is not authenticated");
        }

        String email = authentication.getName();
        User user = userRepository.findByEmail(email)
            .orElseThrow(() -> new BusinessException("USER_NOT_FOUND", "User not found"));

        return mapToUserResponse(user);
    }

    /**
     * Change password for current user.
     */
    @Transactional
    public void changePassword(ChangePasswordRequest request) {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        String email = authentication.getName();

        User user = userRepository.findByEmail(email)
            .orElseThrow(() -> new BusinessException("USER_NOT_FOUND", "User not found"));

        // Verify current password
        if (!passwordEncoder.matches(request.currentPassword(), user.getPasswordHash())) {
            throw new BusinessException("INVALID_PASSWORD", "Current password is incorrect");
        }

        // Update password
        user.setPasswordHash(passwordEncoder.encode(request.newPassword()));
        userRepository.save(user);

        log.info("Password changed for user: {}", user.getId());
    }

    // ==================== Helper Methods ====================

    private UserResponse mapToUserResponse(User user) {
        return new UserResponse(
            user.getId(),
            user.getEmail(),
            user.getName(),
            user.getAvatarUrl(),
            user.getRoles().stream().map(Role::getName).toList(),
            user.isEmailVerified(),
            user.getLastLoginAt(),
            user.getCreatedAt()
        );
    }
}
