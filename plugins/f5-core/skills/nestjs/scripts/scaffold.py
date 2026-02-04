#!/usr/bin/env python3
"""
NestJS Module Scaffolder

Creates complete NestJS module structure with optional CRUD, auth, and Swagger support.
Follows F5 Framework quality gates and traceability requirements.

Usage:
    python scaffold.py <module-name> [options]

Examples:
    python scaffold.py user --crud
    python scaffold.py order --crud --auth
    python scaffold.py product --crud --swagger --path src/modules
"""

import argparse
import os
import sys
from pathlib import Path
from datetime import datetime

# ============================================================
# Templates
# ============================================================

MODULE_TEMPLATE = '''// REQ-{req_id}: {module_title} module
// @design DD-{module_name}
import {{ Module }} from '@nestjs/common';
{imports}

@Module({{
  imports: [{module_imports}],
  controllers: [{module_name_pascal}Controller],
  providers: [{providers}],
  exports: [{module_name_pascal}Service],
}})
export class {module_name_pascal}Module {{}}
'''

CONTROLLER_TEMPLATE = '''// REQ-{req_id}: {module_title} API endpoints
import {{
  Controller,
  Get,
  Post,
  Put,
  Delete,
  Body,
  Param,
  Query,
  ParseUUIDPipe,
  HttpStatus,
  HttpCode,{auth_imports}
}} from '@nestjs/common';
{swagger_imports}
import {{ {module_name_pascal}Service }} from './{module_name}.service';
import {{ Create{module_name_pascal}Dto }} from './dto/create-{module_name}.dto';
import {{ Update{module_name_pascal}Dto }} from './dto/update-{module_name}.dto';
import {{ {module_name_pascal}ResponseDto }} from './dto/{module_name}-response.dto';
import {{ PaginationDto }} from '../../common/dto/pagination.dto';

{swagger_tags}
@Controller('{module_name_plural}')
{auth_decorators}export class {module_name_pascal}Controller {{
  constructor(private readonly {module_name_camel}Service: {module_name_pascal}Service) {{}}

  @Post()
  @HttpCode(HttpStatus.CREATED){crud_decorators_create}
  async create(@Body() dto: Create{module_name_pascal}Dto): Promise<{module_name_pascal}ResponseDto> {{
    return this.{module_name_camel}Service.create(dto);
  }}

  @Get()
  @HttpCode(HttpStatus.OK){crud_decorators_find_all}
  async findAll(@Query() pagination: PaginationDto): Promise<{module_name_pascal}ResponseDto[]> {{
    return this.{module_name_camel}Service.findAll(pagination);
  }}

  @Get(':id')
  @HttpCode(HttpStatus.OK){crud_decorators_find_one}
  async findOne(@Param('id', ParseUUIDPipe) id: string): Promise<{module_name_pascal}ResponseDto> {{
    return this.{module_name_camel}Service.findOne(id);
  }}

  @Put(':id')
  @HttpCode(HttpStatus.OK){crud_decorators_update}
  async update(
    @Param('id', ParseUUIDPipe) id: string,
    @Body() dto: Update{module_name_pascal}Dto,
  ): Promise<{module_name_pascal}ResponseDto> {{
    return this.{module_name_camel}Service.update(id, dto);
  }}

  @Delete(':id')
  @HttpCode(HttpStatus.NO_CONTENT){crud_decorators_delete}
  async remove(@Param('id', ParseUUIDPipe) id: string): Promise<void> {{
    return this.{module_name_camel}Service.remove(id);
  }}
}}
'''

SERVICE_TEMPLATE = '''// REQ-{req_id}: {module_title} business logic
import {{ Injectable, NotFoundException, ConflictException }} from '@nestjs/common';
import {{ InjectRepository }} from '@nestjs/typeorm';
import {{ Repository }} from 'typeorm';
import {{ EventEmitter2 }} from '@nestjs/event-emitter';
import {{ {module_name_pascal} }} from './entities/{module_name}.entity';
import {{ Create{module_name_pascal}Dto }} from './dto/create-{module_name}.dto';
import {{ Update{module_name_pascal}Dto }} from './dto/update-{module_name}.dto';
import {{ PaginationDto }} from '../../common/dto/pagination.dto';

@Injectable()
export class {module_name_pascal}Service {{
  constructor(
    @InjectRepository({module_name_pascal})
    private readonly {module_name_camel}Repository: Repository<{module_name_pascal}>,
    private readonly eventEmitter: EventEmitter2,
  ) {{}}

  async create(dto: Create{module_name_pascal}Dto): Promise<{module_name_pascal}> {{
    const entity = this.{module_name_camel}Repository.create(dto);
    const saved = await this.{module_name_camel}Repository.save(entity);

    this.eventEmitter.emit('{module_name}.created', saved);

    return saved;
  }}

  async findAll(pagination: PaginationDto): Promise<{module_name_pascal}[]> {{
    const {{ page = 1, limit = 10 }} = pagination;

    return this.{module_name_camel}Repository.find({{
      skip: (page - 1) * limit,
      take: limit,
      order: {{ createdAt: 'DESC' }},
    }});
  }}

  async findOne(id: string): Promise<{module_name_pascal}> {{
    const entity = await this.{module_name_camel}Repository.findOne({{ where: {{ id }} }});

    if (!entity) {{
      throw new NotFoundException(`{module_name_pascal} with ID "${{id}}" not found`);
    }}

    return entity;
  }}

  async update(id: string, dto: Update{module_name_pascal}Dto): Promise<{module_name_pascal}> {{
    const entity = await this.findOne(id);

    Object.assign(entity, dto);
    const updated = await this.{module_name_camel}Repository.save(entity);

    this.eventEmitter.emit('{module_name}.updated', updated);

    return updated;
  }}

  async remove(id: string): Promise<void> {{
    const entity = await this.findOne(id);

    await this.{module_name_camel}Repository.remove(entity);

    this.eventEmitter.emit('{module_name}.deleted', {{ id }});
  }}
}}
'''

ENTITY_TEMPLATE = '''// REQ-{req_id}: {module_title} entity
import {{
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  UpdateDateColumn,
  Index,
}} from 'typeorm';

@Entity('{module_name_plural}')
@Index(['createdAt'])
export class {module_name_pascal} {{
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column()
  name: string;

  @Column({{ nullable: true }})
  description?: string;

  @Column({{ default: true }})
  isActive: boolean;

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;
}}
'''

CREATE_DTO_TEMPLATE = '''// REQ-{req_id}: {module_title} creation DTO
import {{ IsString, IsNotEmpty, IsOptional, MaxLength }} from 'class-validator';
{swagger_import}

export class Create{module_name_pascal}Dto {{
  {swagger_name}
  @IsString()
  @IsNotEmpty()
  @MaxLength(255)
  name: string;

  {swagger_description}
  @IsString()
  @IsOptional()
  @MaxLength(1000)
  description?: string;
}}
'''

UPDATE_DTO_TEMPLATE = '''// REQ-{req_id}: {module_title} update DTO
import {{ PartialType }} from '{partial_type_import}';
import {{ Create{module_name_pascal}Dto }} from './create-{module_name}.dto';

export class Update{module_name_pascal}Dto extends PartialType(Create{module_name_pascal}Dto) {{}}
'''

RESPONSE_DTO_TEMPLATE = '''// REQ-{req_id}: {module_title} response DTO
import {{ Expose }} from 'class-transformer';
{swagger_import}

export class {module_name_pascal}ResponseDto {{
  {swagger_id}
  @Expose()
  id: string;

  {swagger_name}
  @Expose()
  name: string;

  {swagger_description}
  @Expose()
  description?: string;

  {swagger_is_active}
  @Expose()
  isActive: boolean;

  {swagger_created_at}
  @Expose()
  createdAt: Date;

  {swagger_updated_at}
  @Expose()
  updatedAt: Date;
}}
'''

SERVICE_SPEC_TEMPLATE = '''// REQ-{req_id}: {module_title} service unit tests
import {{ Test, TestingModule }} from '@nestjs/testing';
import {{ getRepositoryToken }} from '@nestjs/typeorm';
import {{ EventEmitter2 }} from '@nestjs/event-emitter';
import {{ NotFoundException }} from '@nestjs/common';
import {{ {module_name_pascal}Service }} from '../{module_name}.service';
import {{ {module_name_pascal} }} from '../entities/{module_name}.entity';

describe('{module_name_pascal}Service', () => {{
  let service: {module_name_pascal}Service;
  let repository: jest.Mocked<any>;
  let eventEmitter: jest.Mocked<EventEmitter2>;

  const mock{module_name_pascal}: {module_name_pascal} = {{
    id: 'uuid-123',
    name: 'Test {module_name_pascal}',
    description: 'Test description',
    isActive: true,
    createdAt: new Date(),
    updatedAt: new Date(),
  }};

  beforeEach(async () => {{
    const module: TestingModule = await Test.createTestingModule({{
      providers: [
        {module_name_pascal}Service,
        {{
          provide: getRepositoryToken({module_name_pascal}),
          useValue: {{
            create: jest.fn(),
            save: jest.fn(),
            find: jest.fn(),
            findOne: jest.fn(),
            remove: jest.fn(),
          }},
        }},
        {{
          provide: EventEmitter2,
          useValue: {{
            emit: jest.fn(),
          }},
        }},
      ],
    }}).compile();

    service = module.get<{module_name_pascal}Service>({module_name_pascal}Service);
    repository = module.get(getRepositoryToken({module_name_pascal}));
    eventEmitter = module.get(EventEmitter2);
  }});

  it('should be defined', () => {{
    expect(service).toBeDefined();
  }});

  describe('create', () => {{
    it('should create a {module_name} successfully', async () => {{
      const dto = {{ name: 'Test', description: 'Desc' }};
      repository.create.mockReturnValue(mock{module_name_pascal});
      repository.save.mockResolvedValue(mock{module_name_pascal});

      const result = await service.create(dto);

      expect(result).toEqual(mock{module_name_pascal});
      expect(eventEmitter.emit).toHaveBeenCalledWith('{module_name}.created', mock{module_name_pascal});
    }});
  }});

  describe('findOne', () => {{
    it('should return a {module_name} by id', async () => {{
      repository.findOne.mockResolvedValue(mock{module_name_pascal});

      const result = await service.findOne('uuid-123');

      expect(result).toEqual(mock{module_name_pascal});
    }});

    it('should throw NotFoundException if not found', async () => {{
      repository.findOne.mockResolvedValue(null);

      await expect(service.findOne('invalid-id')).rejects.toThrow(NotFoundException);
    }});
  }});

  describe('update', () => {{
    it('should update a {module_name} successfully', async () => {{
      const dto = {{ name: 'Updated' }};
      const updated = {{ ...mock{module_name_pascal}, ...dto }};
      repository.findOne.mockResolvedValue(mock{module_name_pascal});
      repository.save.mockResolvedValue(updated);

      const result = await service.update('uuid-123', dto);

      expect(result.name).toBe('Updated');
      expect(eventEmitter.emit).toHaveBeenCalledWith('{module_name}.updated', updated);
    }});
  }});

  describe('remove', () => {{
    it('should remove a {module_name} successfully', async () => {{
      repository.findOne.mockResolvedValue(mock{module_name_pascal});
      repository.remove.mockResolvedValue(undefined);

      await service.remove('uuid-123');

      expect(eventEmitter.emit).toHaveBeenCalledWith('{module_name}.deleted', {{ id: 'uuid-123' }});
    }});
  }});
}});
'''

CONTROLLER_SPEC_TEMPLATE = '''// REQ-{req_id}: {module_title} controller unit tests
import {{ Test, TestingModule }} from '@nestjs/testing';
import {{ {module_name_pascal}Controller }} from '../{module_name}.controller';
import {{ {module_name_pascal}Service }} from '../{module_name}.service';

describe('{module_name_pascal}Controller', () => {{
  let controller: {module_name_pascal}Controller;
  let service: jest.Mocked<{module_name_pascal}Service>;

  const mock{module_name_pascal} = {{
    id: 'uuid-123',
    name: 'Test {module_name_pascal}',
    description: 'Test description',
    isActive: true,
    createdAt: new Date(),
    updatedAt: new Date(),
  }};

  beforeEach(async () => {{
    const module: TestingModule = await Test.createTestingModule({{
      controllers: [{module_name_pascal}Controller],
      providers: [
        {{
          provide: {module_name_pascal}Service,
          useValue: {{
            create: jest.fn(),
            findAll: jest.fn(),
            findOne: jest.fn(),
            update: jest.fn(),
            remove: jest.fn(),
          }},
        }},
      ],
    }}).compile();

    controller = module.get<{module_name_pascal}Controller>({module_name_pascal}Controller);
    service = module.get({module_name_pascal}Service);
  }});

  it('should be defined', () => {{
    expect(controller).toBeDefined();
  }});

  describe('create', () => {{
    it('should create a {module_name}', async () => {{
      const dto = {{ name: 'Test', description: 'Desc' }};
      service.create.mockResolvedValue(mock{module_name_pascal} as any);

      const result = await controller.create(dto);

      expect(result).toEqual(mock{module_name_pascal});
      expect(service.create).toHaveBeenCalledWith(dto);
    }});
  }});

  describe('findAll', () => {{
    it('should return array of {module_name_plural}', async () => {{
      service.findAll.mockResolvedValue([mock{module_name_pascal}] as any);

      const result = await controller.findAll({{ page: 1, limit: 10 }});

      expect(result).toEqual([mock{module_name_pascal}]);
    }});
  }});

  describe('findOne', () => {{
    it('should return a {module_name} by id', async () => {{
      service.findOne.mockResolvedValue(mock{module_name_pascal} as any);

      const result = await controller.findOne('uuid-123');

      expect(result).toEqual(mock{module_name_pascal});
    }});
  }});

  describe('update', () => {{
    it('should update a {module_name}', async () => {{
      const dto = {{ name: 'Updated' }};
      const updated = {{ ...mock{module_name_pascal}, ...dto }};
      service.update.mockResolvedValue(updated as any);

      const result = await controller.update('uuid-123', dto);

      expect(result.name).toBe('Updated');
    }});
  }});

  describe('remove', () => {{
    it('should remove a {module_name}', async () => {{
      service.remove.mockResolvedValue(undefined);

      await controller.remove('uuid-123');

      expect(service.remove).toHaveBeenCalledWith('uuid-123');
    }});
  }});
}});
'''

# ============================================================
# Helper Functions
# ============================================================

def to_pascal_case(name: str) -> str:
    """Convert kebab-case or snake_case to PascalCase."""
    return ''.join(word.capitalize() for word in name.replace('-', '_').split('_'))

def to_camel_case(name: str) -> str:
    """Convert kebab-case or snake_case to camelCase."""
    pascal = to_pascal_case(name)
    return pascal[0].lower() + pascal[1:] if pascal else ''

def to_plural(name: str) -> str:
    """Simple pluralization."""
    if name.endswith('y'):
        return name[:-1] + 'ies'
    elif name.endswith('s') or name.endswith('x') or name.endswith('ch') or name.endswith('sh'):
        return name + 'es'
    else:
        return name + 's'

def generate_req_id() -> str:
    """Generate requirement ID based on timestamp."""
    return datetime.now().strftime('%Y%m%d%H%M')

# ============================================================
# File Generators
# ============================================================

def generate_module(context: dict) -> str:
    """Generate module file content."""
    imports = ["import { TypeOrmModule } from '@nestjs/typeorm';"]
    imports.append(f"import {{ {context['pascal']}Controller }} from './{context['name']}.controller';")
    imports.append(f"import {{ {context['pascal']}Service }} from './{context['name']}.service';")
    imports.append(f"import {{ {context['pascal']} }} from './entities/{context['name']}.entity';")

    module_imports = f"TypeOrmModule.forFeature([{context['pascal']}])"
    providers = f"{context['pascal']}Service"

    if context['auth']:
        imports.insert(0, "import { JwtAuthGuard, RolesGuard } from '../../common/guards';")
        providers += ", JwtAuthGuard, RolesGuard"

    return MODULE_TEMPLATE.format(
        req_id=context['req_id'],
        module_title=context['title'],
        module_name=context['name'],
        module_name_pascal=context['pascal'],
        imports='\n'.join(imports),
        module_imports=module_imports,
        providers=providers,
    )

def generate_controller(context: dict) -> str:
    """Generate controller file content."""
    auth_imports = ''
    auth_decorators = ''
    swagger_imports = ''
    swagger_tags = ''
    crud_decorators = {
        'create': '', 'find_all': '', 'find_one': '', 'update': '', 'delete': ''
    }

    if context['auth']:
        auth_imports = '\n  UseGuards,'
        auth_decorators = "@UseGuards(JwtAuthGuard, RolesGuard)\n"

    if context['swagger']:
        swagger_imports = "import { ApiTags, ApiOperation, ApiResponse } from '@nestjs/swagger';\n"
        swagger_tags = f"@ApiTags('{context['plural']}')"
        crud_decorators['create'] = f"\n  @ApiOperation({{ summary: 'Create {context['name']}' }})\n  @ApiResponse({{ status: 201, type: {context['pascal']}ResponseDto }})"
        crud_decorators['find_all'] = f"\n  @ApiOperation({{ summary: 'Get all {context['plural']}' }})\n  @ApiResponse({{ status: 200, type: [{context['pascal']}ResponseDto] }})"
        crud_decorators['find_one'] = f"\n  @ApiOperation({{ summary: 'Get {context['name']} by ID' }})\n  @ApiResponse({{ status: 200, type: {context['pascal']}ResponseDto }})"
        crud_decorators['update'] = f"\n  @ApiOperation({{ summary: 'Update {context['name']}' }})\n  @ApiResponse({{ status: 200, type: {context['pascal']}ResponseDto }})"
        crud_decorators['delete'] = f"\n  @ApiOperation({{ summary: 'Delete {context['name']}' }})\n  @ApiResponse({{ status: 204 }})"

    return CONTROLLER_TEMPLATE.format(
        req_id=context['req_id'],
        module_title=context['title'],
        module_name=context['name'],
        module_name_pascal=context['pascal'],
        module_name_camel=context['camel'],
        module_name_plural=context['plural'],
        auth_imports=auth_imports,
        auth_decorators=auth_decorators,
        swagger_imports=swagger_imports,
        swagger_tags=swagger_tags,
        crud_decorators_create=crud_decorators['create'],
        crud_decorators_find_all=crud_decorators['find_all'],
        crud_decorators_find_one=crud_decorators['find_one'],
        crud_decorators_update=crud_decorators['update'],
        crud_decorators_delete=crud_decorators['delete'],
    )

def generate_service(context: dict) -> str:
    """Generate service file content."""
    return SERVICE_TEMPLATE.format(
        req_id=context['req_id'],
        module_title=context['title'],
        module_name=context['name'],
        module_name_pascal=context['pascal'],
        module_name_camel=context['camel'],
    )

def generate_entity(context: dict) -> str:
    """Generate entity file content."""
    return ENTITY_TEMPLATE.format(
        req_id=context['req_id'],
        module_title=context['title'],
        module_name_pascal=context['pascal'],
        module_name_plural=context['plural'],
    )

def generate_create_dto(context: dict) -> str:
    """Generate create DTO file content."""
    swagger_import = "import { ApiProperty } from '@nestjs/swagger';\n" if context['swagger'] else ''
    swagger_name = "@ApiProperty({ example: 'Example name' })" if context['swagger'] else ''
    swagger_description = "@ApiProperty({ example: 'Example description', required: false })" if context['swagger'] else ''

    return CREATE_DTO_TEMPLATE.format(
        req_id=context['req_id'],
        module_title=context['title'],
        module_name_pascal=context['pascal'],
        swagger_import=swagger_import,
        swagger_name=swagger_name,
        swagger_description=swagger_description,
    )

def generate_update_dto(context: dict) -> str:
    """Generate update DTO file content."""
    partial_import = '@nestjs/swagger' if context['swagger'] else '@nestjs/mapped-types'

    return UPDATE_DTO_TEMPLATE.format(
        req_id=context['req_id'],
        module_title=context['title'],
        module_name=context['name'],
        module_name_pascal=context['pascal'],
        partial_type_import=partial_import,
    )

def generate_response_dto(context: dict) -> str:
    """Generate response DTO file content."""
    swagger_import = "import { ApiProperty } from '@nestjs/swagger';\n" if context['swagger'] else ''
    swagger_deco = lambda ex: f"@ApiProperty({{ example: {ex} }})" if context['swagger'] else ''

    return RESPONSE_DTO_TEMPLATE.format(
        req_id=context['req_id'],
        module_title=context['title'],
        module_name_pascal=context['pascal'],
        swagger_import=swagger_import,
        swagger_id=swagger_deco("'uuid-123'"),
        swagger_name=swagger_deco("'Example name'"),
        swagger_description=swagger_deco("'Example description'"),
        swagger_is_active=swagger_deco('true'),
        swagger_created_at=swagger_deco("'2024-01-01T00:00:00Z'"),
        swagger_updated_at=swagger_deco("'2024-01-01T00:00:00Z'"),
    )

def generate_service_spec(context: dict) -> str:
    """Generate service unit test file content."""
    return SERVICE_SPEC_TEMPLATE.format(
        req_id=context['req_id'],
        module_title=context['title'],
        module_name=context['name'],
        module_name_pascal=context['pascal'],
        module_name_plural=context['plural'],
    )

def generate_controller_spec(context: dict) -> str:
    """Generate controller unit test file content."""
    return CONTROLLER_SPEC_TEMPLATE.format(
        req_id=context['req_id'],
        module_title=context['title'],
        module_name=context['name'],
        module_name_pascal=context['pascal'],
        module_name_plural=context['plural'],
    )

# ============================================================
# Main Scaffolder
# ============================================================

def scaffold_module(name: str, options: dict) -> None:
    """Scaffold complete NestJS module structure."""
    # Build context
    context = {
        'name': name.lower().replace('_', '-'),
        'pascal': to_pascal_case(name),
        'camel': to_camel_case(name),
        'plural': to_plural(name.lower().replace('_', '-')),
        'title': to_pascal_case(name).replace('_', ' '),
        'req_id': generate_req_id(),
        'crud': options.get('crud', False),
        'auth': options.get('auth', False),
        'swagger': options.get('swagger', True),
        'tests': options.get('tests', True),
    }

    # Determine base path
    base_path = Path(options.get('path', 'src/modules')) / context['name']

    # Create directories
    dirs = [
        base_path,
        base_path / 'dto',
        base_path / 'entities',
    ]
    if context['tests']:
        dirs.append(base_path / '__tests__')

    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    # Generate files
    files = [
        (base_path / f"{context['name']}.module.ts", generate_module(context)),
        (base_path / f"{context['name']}.controller.ts", generate_controller(context)),
        (base_path / f"{context['name']}.service.ts", generate_service(context)),
        (base_path / 'entities' / f"{context['name']}.entity.ts", generate_entity(context)),
        (base_path / 'dto' / f"create-{context['name']}.dto.ts", generate_create_dto(context)),
        (base_path / 'dto' / f"update-{context['name']}.dto.ts", generate_update_dto(context)),
        (base_path / 'dto' / f"{context['name']}-response.dto.ts", generate_response_dto(context)),
    ]

    if context['tests']:
        files.extend([
            (base_path / '__tests__' / f"{context['name']}.service.spec.ts", generate_service_spec(context)),
            (base_path / '__tests__' / f"{context['name']}.controller.spec.ts", generate_controller_spec(context)),
        ])

    # Write files
    print(f"\n{'=' * 60}")
    print("NestJS Module Scaffolder")
    print(f"{'=' * 60}")
    print(f"Module: {context['pascal']}")
    print(f"Options: {'crud ' if context['crud'] else ''}{'auth ' if context['auth'] else ''}{'swagger ' if context['swagger'] else ''}{'tests' if context['tests'] else ''}")
    print(f"Output: {base_path}")
    print(f"{'=' * 60}\n")

    for file_path, content in files:
        file_path.write_text(content)
        print(f"  Created: {file_path}")

    print(f"\n{'=' * 60}")
    print(f"✓ Successfully created {len(files)} files!")
    print(f"{'=' * 60}\n")

    # Print next steps
    print("Next steps:")
    print(f"  1. Import {context['pascal']}Module in AppModule")
    print(f"  2. Run migrations: npm run migration:generate")
    print(f"  3. Run tests: npm run test -- --testPathPattern={context['name']}")

def main():
    parser = argparse.ArgumentParser(
        description='NestJS Module Scaffolder - Creates complete module structure',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s user --crud
  %(prog)s order --crud --auth
  %(prog)s product --crud --swagger --path src/modules
        '''
    )

    parser.add_argument('name', help='Module name (kebab-case or snake_case)')
    parser.add_argument('--crud', action='store_true', help='Generate CRUD endpoints')
    parser.add_argument('--auth', action='store_true', help='Add authentication guards')
    parser.add_argument('--no-swagger', action='store_true', help='Disable Swagger decorators')
    parser.add_argument('--no-tests', action='store_true', help='Skip test file generation')
    parser.add_argument('--path', default='src/modules', help='Output directory (default: src/modules)')

    args = parser.parse_args()

    options = {
        'crud': args.crud,
        'auth': args.auth,
        'swagger': not args.no_swagger,
        'tests': not args.no_tests,
        'path': args.path,
    }

    try:
        scaffold_module(args.name, options)
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
