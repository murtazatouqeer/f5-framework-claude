# NestJS Controller Template

Production-ready controller template with OpenAPI documentation.

## Basic Controller Structure

```typescript
import {
  Controller,
  Get,
  Post,
  Put,
  Patch,
  Delete,
  Body,
  Param,
  Query,
  Headers,
  HttpCode,
  HttpStatus,
  UseGuards,
  UseInterceptors,
  ParseUUIDPipe,
  ValidationPipe,
  SerializeOptions,
} from '@nestjs/common';
import {
  ApiTags,
  ApiOperation,
  ApiResponse,
  ApiBearerAuth,
  ApiParam,
  ApiQuery,
  ApiHeader,
  ApiBody,
  ApiConsumes,
  ApiProduces,
} from '@nestjs/swagger';
import { JwtAuthGuard } from '@/auth/guards/jwt-auth.guard';
import { RolesGuard } from '@/auth/guards/roles.guard';
import { Roles } from '@/auth/decorators/roles.decorator';
import { CurrentUser } from '@/auth/decorators/current-user.decorator';
import { User } from '@/users/entities/user.entity';

@ApiTags('{{resource}}')
@Controller('{{resource}}')
@UseGuards(JwtAuthGuard, RolesGuard)
@ApiBearerAuth()
@SerializeOptions({ strategy: 'excludeAll' })
export class {{ResourceName}}Controller {
  constructor(private readonly service: {{ResourceName}}Service) {}

  // Endpoints
}
```

## Standard CRUD Endpoints

### Create
```typescript
@Post()
@Roles('admin', 'user')
@ApiOperation({
  summary: 'Create new {{resource}}',
  description: 'Creates a new {{resource}} with the provided data'
})
@ApiBody({ type: Create{{ResourceName}}Dto })
@ApiResponse({
  status: 201,
  description: 'Successfully created',
  type: {{ResourceName}}ResponseDto
})
@ApiResponse({ status: 400, description: 'Validation error' })
@ApiResponse({ status: 401, description: 'Unauthorized' })
@ApiResponse({ status: 403, description: 'Forbidden' })
@ApiResponse({ status: 409, description: 'Conflict - duplicate entry' })
async create(
  @Body(new ValidationPipe({ transform: true })) dto: Create{{ResourceName}}Dto,
  @CurrentUser() user: User,
): Promise<{{ResourceName}}ResponseDto> {
  return this.service.create(dto, user.id);
}
```

### Read All (Paginated)
```typescript
@Get()
@Roles('admin', 'user')
@ApiOperation({ summary: 'Get all {{resource}}s with pagination and filters' })
@ApiQuery({ name: 'page', required: false, type: Number, example: 1 })
@ApiQuery({ name: 'limit', required: false, type: Number, example: 10 })
@ApiQuery({ name: 'search', required: false, type: String })
@ApiQuery({ name: 'status', required: false, enum: StatusEnum })
@ApiQuery({ name: 'sortBy', required: false, type: String })
@ApiQuery({ name: 'sortOrder', required: false, enum: ['ASC', 'DESC'] })
@ApiResponse({ status: 200, description: 'Paginated list' })
async findAll(
  @Query() query: FindAll{{ResourceName}}QueryDto,
  @CurrentUser() user: User,
): Promise<PaginatedResult<{{ResourceName}}ResponseDto>> {
  return this.service.findAll(query, user);
}
```

### Read One
```typescript
@Get(':id')
@Roles('admin', 'user')
@ApiOperation({ summary: 'Get {{resource}} by ID' })
@ApiParam({ name: 'id', type: String, format: 'uuid' })
@ApiResponse({ status: 200, description: 'Found', type: {{ResourceName}}ResponseDto })
@ApiResponse({ status: 404, description: 'Not found' })
async findOne(
  @Param('id', ParseUUIDPipe) id: string,
  @CurrentUser() user: User,
): Promise<{{ResourceName}}ResponseDto> {
  return this.service.findOne(id, user);
}
```

### Update (Full)
```typescript
@Put(':id')
@Roles('admin', 'user')
@ApiOperation({ summary: 'Update {{resource}} (full update)' })
@ApiParam({ name: 'id', type: String, format: 'uuid' })
@ApiBody({ type: Update{{ResourceName}}Dto })
@ApiResponse({ status: 200, description: 'Updated', type: {{ResourceName}}ResponseDto })
@ApiResponse({ status: 404, description: 'Not found' })
async update(
  @Param('id', ParseUUIDPipe) id: string,
  @Body(new ValidationPipe({ transform: true })) dto: Update{{ResourceName}}Dto,
  @CurrentUser() user: User,
): Promise<{{ResourceName}}ResponseDto> {
  return this.service.update(id, dto, user);
}
```

### Update (Partial)
```typescript
@Patch(':id')
@Roles('admin', 'user')
@ApiOperation({ summary: 'Partially update {{resource}}' })
@ApiParam({ name: 'id', type: String, format: 'uuid' })
@ApiBody({ type: Partial{{ResourceName}}Dto })
@ApiResponse({ status: 200, description: 'Updated', type: {{ResourceName}}ResponseDto })
@ApiResponse({ status: 404, description: 'Not found' })
async partialUpdate(
  @Param('id', ParseUUIDPipe) id: string,
  @Body(new ValidationPipe({ transform: true, skipMissingProperties: true }))
  dto: Partial{{ResourceName}}Dto,
  @CurrentUser() user: User,
): Promise<{{ResourceName}}ResponseDto> {
  return this.service.partialUpdate(id, dto, user);
}
```

### Delete
```typescript
@Delete(':id')
@Roles('admin')
@HttpCode(HttpStatus.NO_CONTENT)
@ApiOperation({ summary: 'Delete {{resource}}' })
@ApiParam({ name: 'id', type: String, format: 'uuid' })
@ApiResponse({ status: 204, description: 'Deleted' })
@ApiResponse({ status: 404, description: 'Not found' })
async remove(
  @Param('id', ParseUUIDPipe) id: string,
  @CurrentUser() user: User,
): Promise<void> {
  return this.service.remove(id, user);
}
```

## Advanced Patterns

### Nested Resource
```typescript
@Get(':parentId/children')
@ApiOperation({ summary: 'Get all children of parent' })
@ApiParam({ name: 'parentId', type: String, format: 'uuid' })
async findChildren(
  @Param('parentId', ParseUUIDPipe) parentId: string,
  @Query() query: PaginationQueryDto,
): Promise<PaginatedResult<ChildResponseDto>> {
  return this.service.findChildren(parentId, query);
}

@Post(':parentId/children')
@ApiOperation({ summary: 'Create child under parent' })
async createChild(
  @Param('parentId', ParseUUIDPipe) parentId: string,
  @Body() dto: CreateChildDto,
): Promise<ChildResponseDto> {
  return this.service.createChild(parentId, dto);
}
```

### File Upload
```typescript
@Post('upload')
@UseInterceptors(FileInterceptor('file'))
@ApiConsumes('multipart/form-data')
@ApiBody({
  schema: {
    type: 'object',
    properties: {
      file: {
        type: 'string',
        format: 'binary',
      },
    },
  },
})
@ApiResponse({ status: 201, description: 'File uploaded' })
async uploadFile(
  @UploadedFile(
    new ParseFilePipe({
      validators: [
        new MaxFileSizeValidator({ maxSize: 5 * 1024 * 1024 }), // 5MB
        new FileTypeValidator({ fileType: /(jpg|jpeg|png|pdf)$/ }),
      ],
    }),
  )
  file: Express.Multer.File,
): Promise<{ url: string }> {
  return this.service.uploadFile(file);
}
```

### Bulk Operations
```typescript
@Post('bulk')
@Roles('admin')
@ApiOperation({ summary: 'Create multiple {{resource}}s' })
@ApiBody({ type: [Create{{ResourceName}}Dto] })
@ApiResponse({ status: 201, description: 'Created', type: [{{ResourceName}}ResponseDto] })
async createMany(
  @Body(new ValidationPipe({ transform: true })) dtos: Create{{ResourceName}}Dto[],
): Promise<{{ResourceName}}ResponseDto[]> {
  return this.service.createMany(dtos);
}

@Delete('bulk')
@Roles('admin')
@HttpCode(HttpStatus.NO_CONTENT)
@ApiOperation({ summary: 'Delete multiple {{resource}}s' })
@ApiBody({ schema: { type: 'object', properties: { ids: { type: 'array', items: { type: 'string' } } } } })
async removeMany(@Body('ids') ids: string[]): Promise<void> {
  return this.service.removeMany(ids);
}
```

### Export/Import
```typescript
@Get('export')
@Roles('admin')
@ApiOperation({ summary: 'Export {{resource}}s to CSV' })
@ApiProduces('text/csv')
@Header('Content-Type', 'text/csv')
@Header('Content-Disposition', 'attachment; filename={{resource}}s.csv')
async export(@Query() filters: FilterDto, @Res() res: Response): Promise<void> {
  const csv = await this.service.exportToCsv(filters);
  res.send(csv);
}

@Post('import')
@Roles('admin')
@UseInterceptors(FileInterceptor('file'))
@ApiConsumes('multipart/form-data')
@ApiOperation({ summary: 'Import {{resource}}s from CSV' })
async import(
  @UploadedFile() file: Express.Multer.File,
): Promise<{ imported: number; errors: string[] }> {
  return this.service.importFromCsv(file);
}
```

### Custom Actions
```typescript
@Post(':id/activate')
@Roles('admin')
@ApiOperation({ summary: 'Activate {{resource}}' })
@ApiParam({ name: 'id', type: String })
@ApiResponse({ status: 200, description: 'Activated' })
async activate(@Param('id', ParseUUIDPipe) id: string): Promise<{{ResourceName}}ResponseDto> {
  return this.service.activate(id);
}

@Post(':id/deactivate')
@Roles('admin')
@ApiOperation({ summary: 'Deactivate {{resource}}' })
async deactivate(@Param('id', ParseUUIDPipe) id: string): Promise<{{ResourceName}}ResponseDto> {
  return this.service.deactivate(id);
}
```

## Controller Testing

```typescript
import { Test, TestingModule } from '@nestjs/testing';
import { INestApplication, ValidationPipe } from '@nestjs/common';
import * as request from 'supertest';

describe('{{ResourceName}}Controller (e2e)', () => {
  let app: INestApplication;
  let accessToken: string;

  const mockService = {
    create: jest.fn(),
    findAll: jest.fn(),
    findOne: jest.fn(),
    update: jest.fn(),
    remove: jest.fn(),
  };

  beforeAll(async () => {
    const module: TestingModule = await Test.createTestingModule({
      controllers: [{{ResourceName}}Controller],
      providers: [
        { provide: {{ResourceName}}Service, useValue: mockService },
      ],
    }).compile();

    app = module.createNestApplication();
    app.useGlobalPipes(new ValidationPipe({ transform: true }));
    await app.init();

    // Get auth token
    accessToken = 'test-token';
  });

  afterAll(async () => {
    await app.close();
  });

  describe('POST /{{resource}}', () => {
    it('should create a new {{resource}}', async () => {
      const dto = { name: 'Test' };
      const expected = { id: 'uuid', ...dto };
      mockService.create.mockResolvedValue(expected);

      const response = await request(app.getHttpServer())
        .post('/{{resource}}')
        .set('Authorization', `Bearer ${accessToken}`)
        .send(dto)
        .expect(201);

      expect(response.body).toEqual(expected);
    });

    it('should return 400 for invalid data', async () => {
      await request(app.getHttpServer())
        .post('/{{resource}}')
        .set('Authorization', `Bearer ${accessToken}`)
        .send({})
        .expect(400);
    });
  });

  describe('GET /{{resource}}/:id', () => {
    it('should return a {{resource}}', async () => {
      const expected = { id: 'uuid', name: 'Test' };
      mockService.findOne.mockResolvedValue(expected);

      const response = await request(app.getHttpServer())
        .get('/{{resource}}/uuid')
        .set('Authorization', `Bearer ${accessToken}`)
        .expect(200);

      expect(response.body).toEqual(expected);
    });

    it('should return 404 if not found', async () => {
      mockService.findOne.mockRejectedValue(new NotFoundException());

      await request(app.getHttpServer())
        .get('/{{resource}}/nonexistent')
        .set('Authorization', `Bearer ${accessToken}`)
        .expect(404);
    });
  });
});
```
