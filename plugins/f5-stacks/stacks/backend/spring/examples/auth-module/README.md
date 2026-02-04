# Authentication Module Example

Complete Spring Security + JWT authentication module for Spring Boot.

## Structure

```
auth-module/
├── config/
│   └── SecurityConfig.java
├── entity/
│   ├── User.java
│   └── Role.java
├── repository/
│   └── UserRepository.java
├── service/
│   ├── AuthService.java
│   └── JwtService.java
├── controller/
│   └── AuthController.java
├── dto/
│   ├── LoginRequest.java
│   ├── RegisterRequest.java
│   └── AuthResponse.java
├── filter/
│   └── JwtAuthenticationFilter.java
└── migration/
    └── V1__create_users_table.sql
```

## Features

- JWT-based authentication
- User registration and login
- Password hashing with BCrypt
- Role-based access control (RBAC)
- Refresh token support
- Token blacklisting on logout
- Spring Security integration
- Custom UserDetails implementation

## Configuration

Add to `application.yml`:

```yaml
jwt:
  secret: your-256-bit-secret-key-here-minimum-32-characters
  expiration: 86400000  # 24 hours
  refresh-expiration: 604800000  # 7 days
```

## API Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/auth/register` | Register new user | No |
| POST | `/api/v1/auth/login` | Login user | No |
| POST | `/api/v1/auth/refresh` | Refresh access token | No |
| POST | `/api/v1/auth/logout` | Logout (blacklist token) | Yes |
| GET | `/api/v1/auth/me` | Get current user | Yes |

## Dependencies

```xml
<dependencies>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-security</artifactId>
    </dependency>
    <dependency>
        <groupId>io.jsonwebtoken</groupId>
        <artifactId>jjwt-api</artifactId>
        <version>0.12.3</version>
    </dependency>
    <dependency>
        <groupId>io.jsonwebtoken</groupId>
        <artifactId>jjwt-impl</artifactId>
        <version>0.12.3</version>
        <scope>runtime</scope>
    </dependency>
    <dependency>
        <groupId>io.jsonwebtoken</groupId>
        <artifactId>jjwt-jackson</artifactId>
        <version>0.12.3</version>
        <scope>runtime</scope>
    </dependency>
</dependencies>
```

## Usage

1. Copy files to your project
2. Configure JWT secret in application.yml
3. Run the migration
4. Test with curl or Postman:

```bash
# Register
curl -X POST http://localhost:8080/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123","name":"John Doe"}'

# Login
curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}'

# Access protected resource
curl http://localhost:8080/api/v1/products \
  -H "Authorization: Bearer YOUR_TOKEN"
```
