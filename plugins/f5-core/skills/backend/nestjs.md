---
name: nestjs
description: nestjs skill
category: backend
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---# NestJS Skill

## Auto-Activation
Triggered when:
- `package.json` contains `@nestjs/core`
- File patterns: `*.module.ts`, `*.controller.ts`, `*.service.ts`
- Directory structure contains `src/modules/`

## Expertise Areas

### Core Concepts
- Modules and dependency injection
- Controllers and routing
- Providers and services
- Middleware and guards
- Pipes and interceptors
- Exception filters

### Architecture Patterns
- Modular architecture
- Domain-Driven Design (DDD)
- CQRS pattern
- Event sourcing
- Microservices patterns

### Best Practices
- Use `@Injectable()` for all services
- Implement DTOs for request/response validation
- Use `class-validator` for input validation
- Implement proper error handling with exception filters
- Use `@nestjs/config` for configuration management
- Implement logging with `@nestjs/common` Logger

### Code Patterns

#### Module Structure
```typescript
@Module({
  imports: [DatabaseModule],
  controllers: [UserController],
  providers: [UserService],
  exports: [UserService],
})
export class UserModule {}
```

#### Service Pattern
```typescript
@Injectable()
export class UserService {
  constructor(
    @InjectRepository(User)
    private readonly userRepository: Repository<User>,
  ) {}
}
```

#### Controller Pattern
```typescript
@Controller('users')
@UseGuards(JwtAuthGuard)
export class UserController {
  constructor(private readonly userService: UserService) {}

  @Get(':id')
  async findOne(@Param('id') id: string): Promise<User> {
    return this.userService.findOne(id);
  }
}
```

## Integration with F5
- Works with `/f5-backend` command
- Follows D3/D4 design gate requirements
- Generates code with traceability comments
- Supports TDD workflow with f5-tester agent

## Testing Guidelines
- Unit test services with mocked dependencies
- Integration test controllers with `@nestjs/testing`
- E2E test with supertest
- Maintain 80% coverage for G3 gate
