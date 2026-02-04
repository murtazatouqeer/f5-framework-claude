# OAuth2 Resource Server Patterns

OAuth2 resource server configuration for Spring Boot APIs.

## Dependencies

```groovy
dependencies {
    implementation 'org.springframework.boot:spring-boot-starter-oauth2-resource-server'
    implementation 'org.springframework.security:spring-security-oauth2-jose'
}
```

## JWT Resource Server Configuration

### Basic Configuration

```yaml
# application.yml
spring:
  security:
    oauth2:
      resourceserver:
        jwt:
          issuer-uri: https://auth.example.com/
          # OR specify jwk-set-uri directly
          # jwk-set-uri: https://auth.example.com/.well-known/jwks.json
```

### Security Config for Resource Server

```java
package com.example.app.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.oauth2.server.resource.authentication.JwtAuthenticationConverter;
import org.springframework.security.oauth2.server.resource.authentication.JwtGrantedAuthoritiesConverter;
import org.springframework.security.web.SecurityFilterChain;

@Configuration
@EnableWebSecurity
@EnableMethodSecurity
public class OAuth2ResourceServerConfig {

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
            .csrf(csrf -> csrf.disable())
            .sessionManagement(session ->
                session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/api/v1/public/**").permitAll()
                .requestMatchers("/actuator/health").permitAll()
                .anyRequest().authenticated()
            )
            .oauth2ResourceServer(oauth2 -> oauth2
                .jwt(jwt -> jwt
                    .jwtAuthenticationConverter(jwtAuthenticationConverter())
                )
            );

        return http.build();
    }

    @Bean
    public JwtAuthenticationConverter jwtAuthenticationConverter() {
        JwtGrantedAuthoritiesConverter grantedAuthoritiesConverter = new JwtGrantedAuthoritiesConverter();
        grantedAuthoritiesConverter.setAuthoritiesClaimName("roles");
        grantedAuthoritiesConverter.setAuthorityPrefix("ROLE_");

        JwtAuthenticationConverter jwtAuthenticationConverter = new JwtAuthenticationConverter();
        jwtAuthenticationConverter.setJwtGrantedAuthoritiesConverter(grantedAuthoritiesConverter);
        return jwtAuthenticationConverter;
    }
}
```

### Custom JWT Decoder

```java
@Configuration
public class JwtConfig {

    @Value("${spring.security.oauth2.resourceserver.jwt.issuer-uri}")
    private String issuerUri;

    @Bean
    public JwtDecoder jwtDecoder() {
        NimbusJwtDecoder jwtDecoder = JwtDecoders.fromIssuerLocation(issuerUri);

        OAuth2TokenValidator<Jwt> withIssuer = JwtValidators.createDefaultWithIssuer(issuerUri);
        OAuth2TokenValidator<Jwt> withAudience = new AudienceValidator("my-api");
        OAuth2TokenValidator<Jwt> validator = new DelegatingOAuth2TokenValidator<>(
            withIssuer, withAudience);

        jwtDecoder.setJwtValidator(validator);

        return jwtDecoder;
    }
}

// Custom audience validator
public class AudienceValidator implements OAuth2TokenValidator<Jwt> {

    private final String audience;

    public AudienceValidator(String audience) {
        this.audience = audience;
    }

    @Override
    public OAuth2TokenValidatorResult validate(Jwt jwt) {
        if (jwt.getAudience().contains(audience)) {
            return OAuth2TokenValidatorResult.success();
        }
        return OAuth2TokenValidatorResult.failure(
            new OAuth2Error("invalid_token", "Required audience not found", null));
    }
}
```

## Custom Claims Extraction

### Custom Principal

```java
package com.example.app.security;

import lombok.Getter;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.security.oauth2.server.resource.authentication.JwtAuthenticationToken;

import java.util.Collection;
import java.util.UUID;

@Getter
public class CustomJwtAuthenticationToken extends JwtAuthenticationToken {

    private final UUID userId;
    private final String email;
    private final String tenantId;

    public CustomJwtAuthenticationToken(
            Jwt jwt,
            Collection<? extends GrantedAuthority> authorities,
            String name,
            UUID userId,
            String email,
            String tenantId) {
        super(jwt, authorities, name);
        this.userId = userId;
        this.email = email;
        this.tenantId = tenantId;
    }
}
```

### Custom Authentication Converter

```java
@Component
public class CustomJwtAuthenticationConverter implements Converter<Jwt, AbstractAuthenticationToken> {

    private final JwtGrantedAuthoritiesConverter authoritiesConverter;

    public CustomJwtAuthenticationConverter() {
        this.authoritiesConverter = new JwtGrantedAuthoritiesConverter();
        this.authoritiesConverter.setAuthoritiesClaimName("roles");
        this.authoritiesConverter.setAuthorityPrefix("ROLE_");
    }

    @Override
    public AbstractAuthenticationToken convert(Jwt jwt) {
        Collection<GrantedAuthority> authorities = authoritiesConverter.convert(jwt);

        // Extract custom claims
        UUID userId = UUID.fromString(jwt.getClaimAsString("sub"));
        String email = jwt.getClaimAsString("email");
        String tenantId = jwt.getClaimAsString("tenant_id");

        return new CustomJwtAuthenticationToken(
            jwt,
            authorities,
            jwt.getSubject(),
            userId,
            email,
            tenantId
        );
    }
}

// Use in security config
@Bean
public SecurityFilterChain securityFilterChain(
        HttpSecurity http,
        CustomJwtAuthenticationConverter jwtConverter) throws Exception {
    http.oauth2ResourceServer(oauth2 -> oauth2
        .jwt(jwt -> jwt.jwtAuthenticationConverter(jwtConverter))
    );
    return http.build();
}
```

### Security Context Helper

```java
@Component
public class SecurityContextHelper {

    public Optional<CustomJwtAuthenticationToken> getAuthentication() {
        return Optional.ofNullable(SecurityContextHolder.getContext().getAuthentication())
            .filter(auth -> auth instanceof CustomJwtAuthenticationToken)
            .map(auth -> (CustomJwtAuthenticationToken) auth);
    }

    public Optional<UUID> getCurrentUserId() {
        return getAuthentication().map(CustomJwtAuthenticationToken::getUserId);
    }

    public Optional<String> getCurrentTenantId() {
        return getAuthentication().map(CustomJwtAuthenticationToken::getTenantId);
    }

    public Optional<String> getCurrentEmail() {
        return getAuthentication().map(CustomJwtAuthenticationToken::getEmail);
    }

    public Jwt getCurrentJwt() {
        return getAuthentication()
            .map(CustomJwtAuthenticationToken::getToken)
            .orElseThrow(() -> new IllegalStateException("No JWT in security context"));
    }

    public boolean hasRole(String role) {
        return getAuthentication()
            .map(auth -> auth.getAuthorities().stream()
                .anyMatch(a -> a.getAuthority().equals("ROLE_" + role)))
            .orElse(false);
    }
}
```

## Multi-Tenant Support

### Tenant Context

```java
@Component
@RequestScope
@Getter
@Setter
public class TenantContext {
    private String tenantId;
}

@Component
@RequiredArgsConstructor
public class TenantFilter extends OncePerRequestFilter {

    private final SecurityContextHelper securityContextHelper;
    private final TenantContext tenantContext;

    @Override
    protected void doFilterInternal(
            HttpServletRequest request,
            HttpServletResponse response,
            FilterChain filterChain) throws ServletException, IOException {

        securityContextHelper.getCurrentTenantId()
            .ifPresent(tenantContext::setTenantId);

        filterChain.doFilter(request, response);
    }
}
```

### Tenant-Aware Repository

```java
public interface TenantAwareRepository<T, ID> extends JpaRepository<T, ID> {

    @Query("SELECT e FROM #{#entityName} e WHERE e.tenantId = :tenantId")
    List<T> findAllByTenantId(@Param("tenantId") String tenantId);

    @Query("SELECT e FROM #{#entityName} e WHERE e.id = :id AND e.tenantId = :tenantId")
    Optional<T> findByIdAndTenantId(@Param("id") ID id, @Param("tenantId") String tenantId);
}

@Service
@RequiredArgsConstructor
public class ProductService {

    private final ProductRepository productRepository;
    private final TenantContext tenantContext;

    public List<Product> findAll() {
        return productRepository.findAllByTenantId(tenantContext.getTenantId());
    }

    public Optional<Product> findById(UUID id) {
        return productRepository.findByIdAndTenantId(id, tenantContext.getTenantId());
    }
}
```

## Scope-Based Authorization

### Configure Scope Authorities

```java
@Bean
public JwtAuthenticationConverter jwtAuthenticationConverter() {
    JwtGrantedAuthoritiesConverter scopeConverter = new JwtGrantedAuthoritiesConverter();
    scopeConverter.setAuthoritiesClaimName("scope");
    scopeConverter.setAuthorityPrefix("SCOPE_");

    JwtGrantedAuthoritiesConverter rolesConverter = new JwtGrantedAuthoritiesConverter();
    rolesConverter.setAuthoritiesClaimName("roles");
    rolesConverter.setAuthorityPrefix("ROLE_");

    JwtAuthenticationConverter jwtConverter = new JwtAuthenticationConverter();
    jwtConverter.setJwtGrantedAuthoritiesConverter(jwt -> {
        Collection<GrantedAuthority> authorities = new ArrayList<>();
        authorities.addAll(scopeConverter.convert(jwt));
        authorities.addAll(rolesConverter.convert(jwt));
        return authorities;
    });

    return jwtConverter;
}
```

### Use Scopes in Authorization

```java
@RestController
@RequestMapping("/api/v1/products")
public class ProductController {

    @GetMapping
    @PreAuthorize("hasAuthority('SCOPE_read:products')")
    public List<ProductResponse> list() {
        return productService.findAll();
    }

    @PostMapping
    @PreAuthorize("hasAuthority('SCOPE_write:products')")
    public ProductResponse create(@RequestBody ProductRequest request) {
        return productService.create(request);
    }

    @DeleteMapping("/{id}")
    @PreAuthorize("hasAuthority('SCOPE_delete:products') or hasRole('ADMIN')")
    public void delete(@PathVariable UUID id) {
        productService.delete(id);
    }
}
```

## Token Introspection (Opaque Tokens)

```yaml
# application.yml
spring:
  security:
    oauth2:
      resourceserver:
        opaquetoken:
          introspection-uri: https://auth.example.com/oauth/introspect
          client-id: my-api
          client-secret: ${OAUTH_CLIENT_SECRET}
```

```java
@Configuration
public class OpaqueTokenConfig {

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http.oauth2ResourceServer(oauth2 -> oauth2
            .opaqueToken(opaque -> opaque
                .introspector(opaqueTokenIntrospector())
            )
        );
        return http.build();
    }

    @Bean
    public OpaqueTokenIntrospector opaqueTokenIntrospector() {
        return new NimbusOpaqueTokenIntrospector(
            introspectionUri,
            clientId,
            clientSecret
        );
    }
}
```

## Error Handling

```java
@Configuration
public class OAuth2ErrorConfig {

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http.oauth2ResourceServer(oauth2 -> oauth2
            .jwt(jwt -> jwt.jwtAuthenticationConverter(jwtAuthenticationConverter()))
            .authenticationEntryPoint(authenticationEntryPoint())
            .accessDeniedHandler(accessDeniedHandler())
        );
        return http.build();
    }

    @Bean
    public AuthenticationEntryPoint authenticationEntryPoint() {
        return (request, response, authException) -> {
            response.setContentType(MediaType.APPLICATION_JSON_VALUE);
            response.setStatus(HttpStatus.UNAUTHORIZED.value());

            String message = "Invalid or missing token";
            if (authException instanceof InvalidBearerTokenException) {
                message = "Token validation failed: " + authException.getMessage();
            }

            response.getWriter().write(objectMapper.writeValueAsString(
                new ErrorResponse("unauthorized", message)
            ));
        };
    }

    @Bean
    public AccessDeniedHandler accessDeniedHandler() {
        return (request, response, accessDeniedException) -> {
            response.setContentType(MediaType.APPLICATION_JSON_VALUE);
            response.setStatus(HttpStatus.FORBIDDEN.value());
            response.getWriter().write(objectMapper.writeValueAsString(
                new ErrorResponse("forbidden", "Insufficient permissions")
            ));
        };
    }
}
```

## Testing with OAuth2

```java
@SpringBootTest
@AutoConfigureMockMvc
class ProductControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Test
    @WithMockUser(roles = "USER")
    void listProducts_authenticated() throws Exception {
        mockMvc.perform(get("/api/v1/products"))
            .andExpect(status().isOk());
    }

    @Test
    void listProducts_withJwt() throws Exception {
        mockMvc.perform(get("/api/v1/products")
                .with(jwt()
                    .authorities(new SimpleGrantedAuthority("SCOPE_read:products"))
                    .jwt(jwt -> jwt
                        .subject("user-123")
                        .claim("email", "user@example.com")
                        .claim("tenant_id", "tenant-1")
                    )
                ))
            .andExpect(status().isOk());
    }

    @Test
    void listProducts_unauthenticated() throws Exception {
        mockMvc.perform(get("/api/v1/products"))
            .andExpect(status().isUnauthorized());
    }
}
```

## Best Practices

1. **Validate issuer and audience** - Prevent token confusion attacks
2. **Use short token lifetimes** - Minimize risk from stolen tokens
3. **Implement token revocation** - Support logout and security incidents
4. **Log authentication events** - For audit and security monitoring
5. **Use scopes for API access** - Fine-grained authorization
6. **Tenant isolation** - Ensure data separation in multi-tenant apps
7. **Handle errors gracefully** - Provide meaningful error responses
8. **Test thoroughly** - Include authentication in test coverage
