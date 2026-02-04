# NestJS Security Reference

Comprehensive security patterns and best practices for NestJS applications.

## Table of Contents

1. [JWT Authentication](#jwt-authentication)
2. [Role-Based Access Control](#role-based-access-control)
3. [API Security](#api-security)
4. [Data Protection](#data-protection)
5. [OWASP Checklist](#owasp-checklist)

---

## JWT Authentication

### Installation

```bash
npm install @nestjs/passport @nestjs/jwt passport passport-jwt bcrypt
npm install -D @types/passport-jwt @types/bcrypt
```

### Auth Module Setup

```typescript
// auth/auth.module.ts
@Module({
  imports: [
    PassportModule.register({ defaultStrategy: 'jwt' }),
    JwtModule.registerAsync({
      imports: [ConfigModule],
      useFactory: (config: ConfigService) => ({
        secret: config.get('JWT_SECRET'),
        signOptions: {
          expiresIn: config.get('JWT_EXPIRES_IN', '15m'),
        },
      }),
      inject: [ConfigService],
    }),
    UserModule,
  ],
  controllers: [AuthController],
  providers: [AuthService, JwtStrategy, LocalStrategy],
  exports: [AuthService],
})
export class AuthModule {}
```

### JWT Strategy

```typescript
// auth/strategies/jwt.strategy.ts
@Injectable()
export class JwtStrategy extends PassportStrategy(Strategy) {
  constructor(
    private configService: ConfigService,
    private userService: UserService,
  ) {
    super({
      jwtFromRequest: ExtractJwt.fromAuthHeaderAsBearerToken(),
      ignoreExpiration: false,
      secretOrKey: configService.get('JWT_SECRET'),
    });
  }

  async validate(payload: JwtPayload): Promise<User> {
    const user = await this.userService.findById(payload.sub);
    if (!user || !user.isActive) {
      throw new UnauthorizedException('Invalid token');
    }
    return user;
  }
}
```

### Local Strategy

```typescript
// auth/strategies/local.strategy.ts
@Injectable()
export class LocalStrategy extends PassportStrategy(Strategy) {
  constructor(private authService: AuthService) {
    super({ usernameField: 'email' });
  }

  async validate(email: string, password: string): Promise<User> {
    const user = await this.authService.validateUser(email, password);
    if (!user) {
      throw new UnauthorizedException('Invalid credentials');
    }
    return user;
  }
}
```

### Auth Service

```typescript
// auth/auth.service.ts
@Injectable()
export class AuthService {
  constructor(
    private userService: UserService,
    private jwtService: JwtService,
    private configService: ConfigService,
  ) {}

  async validateUser(email: string, password: string): Promise<User | null> {
    const user = await this.userService.findByEmail(email);
    if (user && await bcrypt.compare(password, user.password)) {
      return user;
    }
    return null;
  }

  async login(user: User): Promise<TokenResponse> {
    const payload: JwtPayload = {
      sub: user.id,
      email: user.email,
      roles: user.roles,
    };

    const [accessToken, refreshToken] = await Promise.all([
      this.jwtService.signAsync(payload),
      this.jwtService.signAsync(payload, {
        expiresIn: this.configService.get('JWT_REFRESH_EXPIRES_IN', '7d'),
      }),
    ]);

    // Store refresh token hash
    await this.userService.updateRefreshToken(user.id, refreshToken);

    return {
      accessToken,
      refreshToken,
      expiresIn: 900, // 15 minutes
    };
  }

  async refreshTokens(userId: string, refreshToken: string): Promise<TokenResponse> {
    const user = await this.userService.findById(userId);

    if (!user || !user.refreshTokenHash) {
      throw new UnauthorizedException('Access denied');
    }

    const isValid = await bcrypt.compare(refreshToken, user.refreshTokenHash);
    if (!isValid) {
      throw new UnauthorizedException('Invalid refresh token');
    }

    return this.login(user);
  }

  async logout(userId: string): Promise<void> {
    await this.userService.updateRefreshToken(userId, null);
  }
}
```

### Auth Controller

```typescript
// auth/auth.controller.ts
@ApiTags('auth')
@Controller('auth')
export class AuthController {
  constructor(private authService: AuthService) {}

  @Post('login')
  @UseGuards(LocalAuthGuard)
  @ApiOperation({ summary: 'User login' })
  async login(@Request() req, @Res({ passthrough: true }) res: Response) {
    const tokens = await this.authService.login(req.user);

    // Set refresh token as HTTP-only cookie
    res.cookie('refreshToken', tokens.refreshToken, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'strict',
      maxAge: 7 * 24 * 60 * 60 * 1000, // 7 days
    });

    return { accessToken: tokens.accessToken, expiresIn: tokens.expiresIn };
  }

  @Post('refresh')
  @ApiOperation({ summary: 'Refresh access token' })
  async refresh(@Req() req: Request, @CurrentUser() user: User) {
    const refreshToken = req.cookies['refreshToken'];
    if (!refreshToken) {
      throw new UnauthorizedException('Refresh token not found');
    }
    return this.authService.refreshTokens(user.id, refreshToken);
  }

  @Post('logout')
  @UseGuards(JwtAuthGuard)
  @ApiBearerAuth()
  @ApiOperation({ summary: 'User logout' })
  async logout(@Request() req, @Res({ passthrough: true }) res: Response) {
    await this.authService.logout(req.user.id);
    res.clearCookie('refreshToken');
    return { message: 'Logged out successfully' };
  }
}
```

### JWT Auth Guard

```typescript
// auth/guards/jwt-auth.guard.ts
@Injectable()
export class JwtAuthGuard extends AuthGuard('jwt') {
  constructor(private reflector: Reflector) {
    super();
  }

  canActivate(context: ExecutionContext) {
    // Check for @Public() decorator
    const isPublic = this.reflector.getAllAndOverride<boolean>(IS_PUBLIC_KEY, [
      context.getHandler(),
      context.getClass(),
    ]);

    if (isPublic) {
      return true;
    }

    return super.canActivate(context);
  }

  handleRequest(err: any, user: any, info: any) {
    if (err || !user) {
      throw err || new UnauthorizedException('Invalid or expired token');
    }
    return user;
  }
}
```

---

## Role-Based Access Control

### Setup

```typescript
// auth/decorators/roles.decorator.ts
export enum Role {
  User = 'user',
  Admin = 'admin',
  SuperAdmin = 'super_admin',
}

export const ROLES_KEY = 'roles';
export const Roles = (...roles: Role[]) => SetMetadata(ROLES_KEY, roles);

// auth/decorators/permissions.decorator.ts
export const PERMISSIONS_KEY = 'permissions';
export const Permissions = (...permissions: string[]) =>
  SetMetadata(PERMISSIONS_KEY, permissions);

// auth/decorators/public.decorator.ts
export const IS_PUBLIC_KEY = 'isPublic';
export const Public = () => SetMetadata(IS_PUBLIC_KEY, true);
```

### Roles Guard

```typescript
// auth/guards/roles.guard.ts
@Injectable()
export class RolesGuard implements CanActivate {
  constructor(private reflector: Reflector) {}

  canActivate(context: ExecutionContext): boolean {
    const requiredRoles = this.reflector.getAllAndOverride<Role[]>(ROLES_KEY, [
      context.getHandler(),
      context.getClass(),
    ]);

    if (!requiredRoles) {
      return true;
    }

    const { user } = context.switchToHttp().getRequest();
    return requiredRoles.some((role) => user.roles?.includes(role));
  }
}
```

### Permissions Guard (Fine-grained)

```typescript
// auth/guards/permissions.guard.ts
@Injectable()
export class PermissionsGuard implements CanActivate {
  constructor(
    private reflector: Reflector,
    private permissionService: PermissionService,
  ) {}

  async canActivate(context: ExecutionContext): Promise<boolean> {
    const requiredPermissions = this.reflector.getAllAndOverride<string[]>(
      PERMISSIONS_KEY,
      [context.getHandler(), context.getClass()],
    );

    if (!requiredPermissions) {
      return true;
    }

    const { user } = context.switchToHttp().getRequest();
    const userPermissions = await this.permissionService.getUserPermissions(user.id);

    return requiredPermissions.every((permission) =>
      userPermissions.includes(permission),
    );
  }
}
```

### Usage

```typescript
@Controller('admin')
@UseGuards(JwtAuthGuard, RolesGuard)
@Roles(Role.Admin)
export class AdminController {
  @Get('dashboard')
  getDashboard() {
    return { message: 'Admin dashboard' };
  }

  @Delete('users/:id')
  @Roles(Role.SuperAdmin) // Override class-level
  deleteUser(@Param('id') id: string) {
    return this.userService.delete(id);
  }

  @Post('settings')
  @Permissions('settings:write')
  updateSettings(@Body() dto: UpdateSettingsDto) {
    return this.settingsService.update(dto);
  }
}
```

### Resource Ownership Guard

```typescript
// auth/guards/owner.guard.ts
@Injectable()
export class OwnerGuard implements CanActivate {
  constructor(
    private reflector: Reflector,
    private dataSource: DataSource,
  ) {}

  async canActivate(context: ExecutionContext): Promise<boolean> {
    const request = context.switchToHttp().getRequest();
    const user = request.user;
    const resourceId = request.params.id;

    // Admin bypass
    if (user.roles.includes(Role.Admin)) {
      return true;
    }

    // Get resource type from metadata
    const resourceType = this.reflector.get<string>('resourceType', context.getHandler());
    if (!resourceType) {
      return true;
    }

    // Check ownership
    const resource = await this.dataSource
      .getRepository(resourceType)
      .findOne({ where: { id: resourceId } });

    return resource?.userId === user.id;
  }
}

// Usage
@Get(':id')
@UseGuards(JwtAuthGuard, OwnerGuard)
@SetMetadata('resourceType', 'Order')
findOne(@Param('id') id: string) {
  return this.orderService.findOne(id);
}
```

---

## API Security

### Helmet Configuration

```typescript
// main.ts
import helmet from 'helmet';

app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      scriptSrc: ["'self'"],
      imgSrc: ["'self'", 'data:', 'https:'],
    },
  },
  hsts: {
    maxAge: 31536000,
    includeSubDomains: true,
    preload: true,
  },
}));
```

### CORS Configuration

```typescript
// main.ts
app.enableCors({
  origin: process.env.ALLOWED_ORIGINS?.split(',') || ['http://localhost:3000'],
  methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'],
  allowedHeaders: ['Content-Type', 'Authorization'],
  credentials: true,
  maxAge: 86400,
});
```

### Rate Limiting

```typescript
// app.module.ts
import { ThrottlerModule, ThrottlerGuard } from '@nestjs/throttler';

@Module({
  imports: [
    ThrottlerModule.forRoot([
      {
        name: 'short',
        ttl: 1000,
        limit: 3,
      },
      {
        name: 'medium',
        ttl: 10000,
        limit: 20,
      },
      {
        name: 'long',
        ttl: 60000,
        limit: 100,
      },
    ]),
  ],
  providers: [
    {
      provide: APP_GUARD,
      useClass: ThrottlerGuard,
    },
  ],
})
export class AppModule {}

// Custom rate limit per endpoint
@Controller('auth')
export class AuthController {
  @Post('login')
  @Throttle({ short: { limit: 5, ttl: 60000 } }) // 5 attempts per minute
  login() {}
}
```

### Request Validation

```typescript
// main.ts
app.useGlobalPipes(
  new ValidationPipe({
    whitelist: true,           // Strip unknown properties
    forbidNonWhitelisted: true, // Throw on unknown properties
    transform: true,            // Auto-transform types
    transformOptions: {
      enableImplicitConversion: true,
    },
  }),
);
```

### CSRF Protection

```typescript
// main.ts
import * as csurf from 'csurf';

app.use(csurf({
  cookie: {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'strict',
  },
}));

// Controller
@Get('csrf-token')
getCsrfToken(@Req() req: Request) {
  return { csrfToken: req.csrfToken() };
}
```

---

## Data Protection

### Password Hashing

```typescript
// user/user.service.ts
import * as bcrypt from 'bcrypt';

@Injectable()
export class UserService {
  private readonly SALT_ROUNDS = 12;

  async create(dto: CreateUserDto): Promise<User> {
    const hashedPassword = await bcrypt.hash(dto.password, this.SALT_ROUNDS);
    return this.userRepository.save({
      ...dto,
      password: hashedPassword,
    });
  }

  async validatePassword(plain: string, hashed: string): Promise<boolean> {
    return bcrypt.compare(plain, hashed);
  }
}
```

### Sensitive Data Exclusion

```typescript
// user/entities/user.entity.ts
import { Exclude, Expose } from 'class-transformer';

@Entity()
export class User {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column()
  email: string;

  @Column()
  @Exclude() // Never expose password
  password: string;

  @Column({ nullable: true })
  @Exclude()
  refreshTokenHash: string;

  @Column({ type: 'jsonb', nullable: true })
  @Exclude()
  sensitiveData: object;
}

// Apply globally in main.ts
app.useGlobalInterceptors(new ClassSerializerInterceptor(app.get(Reflector)));
```

### Encryption Service

```typescript
// common/services/encryption.service.ts
import * as crypto from 'crypto';

@Injectable()
export class EncryptionService {
  private readonly algorithm = 'aes-256-gcm';
  private readonly key: Buffer;

  constructor(private configService: ConfigService) {
    this.key = Buffer.from(configService.get('ENCRYPTION_KEY'), 'hex');
  }

  encrypt(text: string): string {
    const iv = crypto.randomBytes(16);
    const cipher = crypto.createCipheriv(this.algorithm, this.key, iv);

    let encrypted = cipher.update(text, 'utf8', 'hex');
    encrypted += cipher.final('hex');

    const authTag = cipher.getAuthTag();

    return `${iv.toString('hex')}:${authTag.toString('hex')}:${encrypted}`;
  }

  decrypt(encryptedData: string): string {
    const [ivHex, authTagHex, encrypted] = encryptedData.split(':');

    const iv = Buffer.from(ivHex, 'hex');
    const authTag = Buffer.from(authTagHex, 'hex');

    const decipher = crypto.createDecipheriv(this.algorithm, this.key, iv);
    decipher.setAuthTag(authTag);

    let decrypted = decipher.update(encrypted, 'hex', 'utf8');
    decrypted += decipher.final('utf8');

    return decrypted;
  }
}
```

### Input Sanitization

```typescript
// common/pipes/sanitize.pipe.ts
import * as sanitizeHtml from 'sanitize-html';

@Injectable()
export class SanitizePipe implements PipeTransform {
  transform(value: any): any {
    if (typeof value === 'string') {
      return sanitizeHtml(value, {
        allowedTags: [],
        allowedAttributes: {},
      });
    }

    if (typeof value === 'object' && value !== null) {
      return Object.keys(value).reduce((acc, key) => {
        acc[key] = this.transform(value[key]);
        return acc;
      }, {} as any);
    }

    return value;
  }
}

// Usage
@Post()
create(@Body(new SanitizePipe()) dto: CreatePostDto) {}
```

---

## OWASP Checklist

### A01: Broken Access Control

- [x] Implement proper authorization on all endpoints
- [x] Use guards for role/permission checks
- [x] Validate resource ownership
- [x] Deny by default
- [x] Log access control failures

### A02: Cryptographic Failures

- [x] Use HTTPS in production
- [x] Hash passwords with bcrypt (cost >= 12)
- [x] Encrypt sensitive data at rest
- [x] Use strong JWT secrets (>= 256 bits)
- [x] Implement proper key management

### A03: Injection

- [x] Use parameterized queries (TypeORM/Prisma)
- [x] Validate all inputs with class-validator
- [x] Sanitize user inputs
- [x] Use ORM instead of raw queries

### A04: Insecure Design

- [x] Implement rate limiting
- [x] Use secure session management
- [x] Apply principle of least privilege
- [x] Validate business logic

### A05: Security Misconfiguration

- [x] Remove default credentials
- [x] Disable debug mode in production
- [x] Configure security headers (Helmet)
- [x] Keep dependencies updated
- [x] Implement proper error handling

### A06: Vulnerable Components

- [x] Run `npm audit` regularly
- [x] Keep dependencies updated
- [x] Remove unused dependencies
- [x] Monitor security advisories

### A07: Authentication Failures

- [x] Implement multi-factor authentication (optional)
- [x] Use secure password policies
- [x] Implement account lockout
- [x] Use secure session tokens
- [x] Implement proper logout

### A08: Data Integrity Failures

- [x] Verify data integrity
- [x] Sign JWTs properly
- [x] Validate file uploads
- [x] Use CSRF protection

### A09: Logging & Monitoring

- [x] Log authentication events
- [x] Log authorization failures
- [x] Monitor for suspicious activity
- [x] Implement alerting

### A10: SSRF

- [x] Validate and sanitize URLs
- [x] Use allowlists for external calls
- [x] Disable unnecessary protocols

---

## Security Audit Checklist

```typescript
// security-audit.ts - Run periodically
export const securityChecklist = {
  authentication: {
    jwtSecretStrength: 'Check JWT_SECRET is >= 256 bits',
    passwordHashing: 'Verify bcrypt with cost >= 12',
    tokenExpiration: 'Access token <= 15min, refresh <= 7days',
    secureTransmission: 'HTTPS only, secure cookies',
  },
  authorization: {
    guardCoverage: 'All endpoints have guards',
    roleValidation: 'Roles properly checked',
    ownershipValidation: 'Resource ownership verified',
  },
  dataProtection: {
    sensitiveDataExcluded: 'Passwords, tokens excluded from responses',
    encryptionAtRest: 'PII encrypted in database',
    inputValidation: 'All inputs validated and sanitized',
  },
  infrastructure: {
    helmetEnabled: 'Security headers configured',
    corsConfigured: 'CORS properly restricted',
    rateLimiting: 'Rate limits on sensitive endpoints',
  },
};
```

## F5 Quality Gates Mapping

| Gate | Security Deliverable |
|------|---------------------|
| D3 | Security architecture, threat model |
| D4 | Auth flow design, RBAC matrix |
| G2.5 | Security code review, OWASP check |
| G3 | Security unit tests, guard tests |
| G4 | Penetration testing, vulnerability scan |
