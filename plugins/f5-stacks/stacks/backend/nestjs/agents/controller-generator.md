---
name: nestjs-controller-generator
description: Agent for generating NestJS controllers with CRUD operations
applies_to: nestjs
category: agent
---

# NestJS Controller Generator Agent

## Purpose

Generate production-ready NestJS controllers with proper decorators, validation, and Swagger documentation.

## Input Requirements

```yaml
required:
  - module_name: string        # e.g., "users"
  - entity_name: string        # e.g., "user"

optional:
  - base_path: string          # API path (defaults to module_name)
  - authentication: boolean    # Add JWT guard (default: true)
  - swagger: boolean           # Add Swagger decorators (default: true)
  - pagination: boolean        # Add paginated list endpoint (default: true)
  - soft_delete: boolean       # Use soft delete (default: true)
  - custom_endpoints: array    # Additional custom endpoints
  - roles: array               # Role-based access control
```

## Generation Process

### Step 1: Analyze Module Structure

```typescript
// Check existing service and DTOs
const serviceExists = await checkFile(`${moduleName}/${moduleName}.service.ts`);
const createDtoExists = await checkFile(`${moduleName}/dto/create-${entityName}.dto.ts`);
const updateDtoExists = await checkFile(`${moduleName}/dto/update-${entityName}.dto.ts`);
const queryDtoExists = await checkFile(`${moduleName}/dto/query-${entityName}.dto.ts`);
```

### Step 2: Generate Controller

```typescript
// modules/{{module}}/{{module}}.controller.ts
import {
  Controller,
  Get,
  Post,
  Body,
  Patch,
  Param,
  Delete,
  Query,
  UseGuards,
  ParseUUIDPipe,
  HttpStatus,
  HttpCode,
} from '@nestjs/common';
import {
  ApiTags,
  ApiOperation,
  ApiResponse,
  ApiBearerAuth,
  ApiParam,
  ApiQuery,
} from '@nestjs/swagger';
import { JwtAuthGuard } from '../../common/guards/jwt-auth.guard';
import { RolesGuard } from '../../common/guards/roles.guard';
import { Roles } from '../../common/decorators/roles.decorator';
import { CurrentUser } from '../../common/decorators/current-user.decorator';
import { {{Entity}}Service } from './{{module}}.service';
import { Create{{Entity}}Dto } from './dto/create-{{entity}}.dto';
import { Update{{Entity}}Dto } from './dto/update-{{entity}}.dto';
import { Query{{Entity}}Dto } from './dto/query-{{entity}}.dto';
import { {{Entity}}ResponseDto } from './dto/{{entity}}-response.dto';
import { PaginatedResponseDto } from '../../common/dto/paginated-response.dto';
import { Role } from '../../common/enums/role.enum';

@ApiTags('{{Module}}')
@ApiBearerAuth()
@UseGuards(JwtAuthGuard, RolesGuard)
@Controller('{{basePath}}')
export class {{Entity}}Controller {
  constructor(private readonly {{entity}}Service: {{Entity}}Service) {}

  @Post()
  @Roles(Role.ADMIN)
  @HttpCode(HttpStatus.CREATED)
  @ApiOperation({ summary: 'Create {{entity}}' })
  @ApiResponse({
    status: HttpStatus.CREATED,
    description: '{{Entity}} created successfully',
    type: {{Entity}}ResponseDto,
  })
  @ApiResponse({
    status: HttpStatus.BAD_REQUEST,
    description: 'Invalid input data',
  })
  @ApiResponse({
    status: HttpStatus.CONFLICT,
    description: '{{Entity}} already exists',
  })
  async create(
    @Body() createDto: Create{{Entity}}Dto,
    @CurrentUser() user: any,
  ): Promise<{{Entity}}ResponseDto> {
    return this.{{entity}}Service.create(createDto, user.id);
  }

  @Get()
  @ApiOperation({ summary: 'Get all {{entities}} with pagination' })
  @ApiResponse({
    status: HttpStatus.OK,
    description: 'List of {{entities}}',
    type: PaginatedResponseDto,
  })
  @ApiQuery({ name: 'page', required: false, type: Number })
  @ApiQuery({ name: 'limit', required: false, type: Number })
  @ApiQuery({ name: 'search', required: false, type: String })
  @ApiQuery({ name: 'sortBy', required: false, type: String })
  @ApiQuery({ name: 'sortOrder', required: false, enum: ['asc', 'desc'] })
  async findAll(
    @Query() query: Query{{Entity}}Dto,
  ): Promise<PaginatedResponseDto<{{Entity}}ResponseDto>> {
    return this.{{entity}}Service.findAll(query);
  }

  @Get(':id')
  @ApiOperation({ summary: 'Get {{entity}} by ID' })
  @ApiParam({ name: 'id', description: '{{Entity}} ID', type: String })
  @ApiResponse({
    status: HttpStatus.OK,
    description: '{{Entity}} found',
    type: {{Entity}}ResponseDto,
  })
  @ApiResponse({
    status: HttpStatus.NOT_FOUND,
    description: '{{Entity}} not found',
  })
  async findOne(
    @Param('id', ParseUUIDPipe) id: string,
  ): Promise<{{Entity}}ResponseDto> {
    return this.{{entity}}Service.findById(id);
  }

  @Patch(':id')
  @Roles(Role.ADMIN)
  @ApiOperation({ summary: 'Update {{entity}}' })
  @ApiParam({ name: 'id', description: '{{Entity}} ID', type: String })
  @ApiResponse({
    status: HttpStatus.OK,
    description: '{{Entity}} updated successfully',
    type: {{Entity}}ResponseDto,
  })
  @ApiResponse({
    status: HttpStatus.NOT_FOUND,
    description: '{{Entity}} not found',
  })
  @ApiResponse({
    status: HttpStatus.BAD_REQUEST,
    description: 'Invalid input data',
  })
  async update(
    @Param('id', ParseUUIDPipe) id: string,
    @Body() updateDto: Update{{Entity}}Dto,
  ): Promise<{{Entity}}ResponseDto> {
    return this.{{entity}}Service.update(id, updateDto);
  }

  @Delete(':id')
  @Roles(Role.ADMIN)
  @HttpCode(HttpStatus.NO_CONTENT)
  @ApiOperation({ summary: 'Delete {{entity}}' })
  @ApiParam({ name: 'id', description: '{{Entity}} ID', type: String })
  @ApiResponse({
    status: HttpStatus.NO_CONTENT,
    description: '{{Entity}} deleted successfully',
  })
  @ApiResponse({
    status: HttpStatus.NOT_FOUND,
    description: '{{Entity}} not found',
  })
  async remove(@Param('id', ParseUUIDPipe) id: string): Promise<void> {
    return this.{{entity}}Service.delete(id);
  }
}
```

### Step 3: Generate Optional Endpoints

#### Bulk Operations

```typescript
@Post('bulk')
@Roles(Role.ADMIN)
@HttpCode(HttpStatus.CREATED)
@ApiOperation({ summary: 'Bulk create {{entities}}' })
@ApiResponse({
  status: HttpStatus.CREATED,
  description: '{{Entities}} created successfully',
  type: [{{Entity}}ResponseDto],
})
async bulkCreate(
  @Body() createDtos: Create{{Entity}}Dto[],
  @CurrentUser() user: any,
): Promise<{{Entity}}ResponseDto[]> {
  return this.{{entity}}Service.bulkCreate(createDtos, user.id);
}

@Delete('bulk')
@Roles(Role.ADMIN)
@HttpCode(HttpStatus.NO_CONTENT)
@ApiOperation({ summary: 'Bulk delete {{entities}}' })
@ApiBody({ type: [String], description: 'Array of {{entity}} IDs' })
async bulkRemove(@Body() ids: string[]): Promise<void> {
  return this.{{entity}}Service.bulkDelete(ids);
}
```

#### Export Endpoint

```typescript
@Get('export')
@Roles(Role.ADMIN)
@ApiOperation({ summary: 'Export {{entities}} to CSV' })
@ApiResponse({
  status: HttpStatus.OK,
  description: 'CSV file',
  content: {
    'text/csv': {
      schema: { type: 'string', format: 'binary' },
    },
  },
})
async export(
  @Query() query: Query{{Entity}}Dto,
  @Res() res: Response,
): Promise<void> {
  const csv = await this.{{entity}}Service.exportToCsv(query);
  res.setHeader('Content-Type', 'text/csv');
  res.setHeader('Content-Disposition', 'attachment; filename={{entities}}.csv');
  res.send(csv);
}
```

### Step 4: Register in Module

```typescript
// modules/{{module}}/{{module}}.module.ts
import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { {{Entity}}Controller } from './{{module}}.controller';
import { {{Entity}}Service } from './{{module}}.service';
import { {{Entity}} } from './entities/{{entity}}.entity';

@Module({
  imports: [TypeOrmModule.forFeature([{{Entity}}])],
  controllers: [{{Entity}}Controller],
  providers: [{{Entity}}Service],
  exports: [{{Entity}}Service],
})
export class {{Module}}Module {}
```

## Output Files

```
modules/{{module}}/
├── {{module}}.controller.ts    # Generated controller
├── {{module}}.controller.spec.ts # Controller tests
└── {{module}}.module.ts        # Updated module
```

## Usage Example

```bash
# Generate controller via agent
@nestjs:controller-generator {
  "module_name": "products",
  "entity_name": "product",
  "authentication": true,
  "swagger": true,
  "pagination": true,
  "roles": ["admin", "user"]
}
```

## Validation Checklist

- [ ] Service exists and is injectable
- [ ] DTOs are defined and validated
- [ ] Swagger decorators are complete
- [ ] Authentication guards are applied
- [ ] Role-based access is configured
- [ ] Response types are specified
- [ ] Error responses are documented
- [ ] Module exports controller
