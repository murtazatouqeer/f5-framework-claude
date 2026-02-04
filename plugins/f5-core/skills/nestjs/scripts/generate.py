#!/usr/bin/env python3
"""
NestJS Component Generator

Generates individual NestJS components with proper structure and traceability.

Usage:
    python generate.py <type> <name> [options]

Types: controller, service, dto, entity, guard, interceptor, pipe, filter, module

Examples:
    python generate.py controller user
    python generate.py service user --repository
    python generate.py dto create-user --swagger
    python generate.py guard roles
    python generate.py interceptor logging
"""

import argparse
import os
import sys
from pathlib import Path
from datetime import datetime

# ============================================================
# Templates
# ============================================================

CONTROLLER_TEMPLATE = '''// REQ-{req_id}: {name_pascal} controller
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
  HttpCode,
}} from '@nestjs/common';
{swagger_imports}
import {{ {name_pascal}Service }} from './{name}.service';

{swagger_tags}
@Controller('{name_plural}')
export class {name_pascal}Controller {{
  constructor(private readonly {name_camel}Service: {name_pascal}Service) {{}}

  @Get()
  @HttpCode(HttpStatus.OK){swagger_find_all}
  async findAll(): Promise<any[]> {{
    return this.{name_camel}Service.findAll();
  }}

  @Get(':id')
  @HttpCode(HttpStatus.OK){swagger_find_one}
  async findOne(@Param('id', ParseUUIDPipe) id: string): Promise<any> {{
    return this.{name_camel}Service.findOne(id);
  }}
}}
'''

SERVICE_TEMPLATE = '''// REQ-{req_id}: {name_pascal} service
import {{ Injectable, NotFoundException }} from '@nestjs/common';
{repository_import}

@Injectable()
export class {name_pascal}Service {{
  {repository_constructor}

  async findAll(): Promise<any[]> {{
    {find_all_impl}
  }}

  async findOne(id: string): Promise<any> {{
    {find_one_impl}
  }}

  async create(dto: any): Promise<any> {{
    {create_impl}
  }}

  async update(id: string, dto: any): Promise<any> {{
    {update_impl}
  }}

  async remove(id: string): Promise<void> {{
    {remove_impl}
  }}
}}
'''

DTO_TEMPLATE = '''// REQ-{req_id}: {name_pascal} DTO
import {{ IsString, IsNotEmpty, IsOptional{extra_validators} }} from 'class-validator';
{swagger_import}

export class {name_pascal}Dto {{
  {swagger_example}
  @IsString()
  @IsNotEmpty()
  name: string;

  {swagger_description}
  @IsString()
  @IsOptional()
  description?: string;
}}
'''

ENTITY_TEMPLATE = '''// REQ-{req_id}: {name_pascal} entity
import {{
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  UpdateDateColumn,
}} from 'typeorm';

@Entity('{name_plural}')
export class {name_pascal} {{
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column()
  name: string;

  @Column({{ nullable: true }})
  description?: string;

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;
}}
'''

GUARD_TEMPLATE = '''// REQ-{req_id}: {name_pascal} guard
import {{ Injectable, CanActivate, ExecutionContext }} from '@nestjs/common';
import {{ Reflector }} from '@nestjs/core';
import {{ Observable }} from 'rxjs';

@Injectable()
export class {name_pascal}Guard implements CanActivate {{
  constructor(private reflector: Reflector) {{}}

  canActivate(
    context: ExecutionContext,
  ): boolean | Promise<boolean> | Observable<boolean> {{
    const request = context.switchToHttp().getRequest();

    // TODO: Implement guard logic
    // Example: Check roles, permissions, etc.

    return true;
  }}
}}
'''

INTERCEPTOR_TEMPLATE = '''// REQ-{req_id}: {name_pascal} interceptor
import {{
  Injectable,
  NestInterceptor,
  ExecutionContext,
  CallHandler,
}} from '@nestjs/common';
import {{ Observable }} from 'rxjs';
import {{ tap, map }} from 'rxjs/operators';

@Injectable()
export class {name_pascal}Interceptor implements NestInterceptor {{
  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {{
    const now = Date.now();

    return next.handle().pipe(
      tap(() => {{
        console.log(`{name_pascal}Interceptor: ${{Date.now() - now}}ms`);
      }}),
      map((data) => ({{
        data,
        timestamp: new Date().toISOString(),
      }})),
    );
  }}
}}
'''

PIPE_TEMPLATE = '''// REQ-{req_id}: {name_pascal} pipe
import {{
  PipeTransform,
  Injectable,
  ArgumentMetadata,
  BadRequestException,
}} from '@nestjs/common';

@Injectable()
export class {name_pascal}Pipe implements PipeTransform {{
  transform(value: any, metadata: ArgumentMetadata): any {{
    // TODO: Implement transformation/validation logic

    if (!value) {{
      throw new BadRequestException('Value is required');
    }}

    return value;
  }}
}}
'''

FILTER_TEMPLATE = '''// REQ-{req_id}: {name_pascal} exception filter
import {{
  ExceptionFilter,
  Catch,
  ArgumentsHost,
  HttpException,
  HttpStatus,
}} from '@nestjs/common';
import {{ Request, Response }} from 'express';

@Catch()
export class {name_pascal}Filter implements ExceptionFilter {{
  catch(exception: unknown, host: ArgumentsHost): void {{
    const ctx = host.switchToHttp();
    const response = ctx.getResponse<Response>();
    const request = ctx.getRequest<Request>();

    const status =
      exception instanceof HttpException
        ? exception.getStatus()
        : HttpStatus.INTERNAL_SERVER_ERROR;

    const message =
      exception instanceof HttpException
        ? exception.message
        : 'Internal server error';

    response.status(status).json({{
      statusCode: status,
      message,
      timestamp: new Date().toISOString(),
      path: request.url,
    }});
  }}
}}
'''

MODULE_TEMPLATE = '''// REQ-{req_id}: {name_pascal} module
import {{ Module }} from '@nestjs/common';

@Module({{
  imports: [],
  controllers: [],
  providers: [],
  exports: [],
}})
export class {name_pascal}Module {{}}
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
# Generators
# ============================================================

def generate_controller(name: str, options: dict) -> tuple:
    """Generate controller file."""
    swagger = options.get('swagger', False)
    pascal = to_pascal_case(name)
    camel = to_camel_case(name)
    plural = to_plural(name.lower())

    swagger_imports = "import { ApiTags, ApiOperation, ApiResponse } from '@nestjs/swagger';\n" if swagger else ''
    swagger_tags = f"@ApiTags('{plural}')" if swagger else ''
    swagger_find_all = f"\n  @ApiOperation({{ summary: 'Get all {plural}' }})" if swagger else ''
    swagger_find_one = f"\n  @ApiOperation({{ summary: 'Get {name} by ID' }})" if swagger else ''

    content = CONTROLLER_TEMPLATE.format(
        req_id=generate_req_id(),
        name=name.lower(),
        name_pascal=pascal,
        name_camel=camel,
        name_plural=plural,
        swagger_imports=swagger_imports,
        swagger_tags=swagger_tags,
        swagger_find_all=swagger_find_all,
        swagger_find_one=swagger_find_one,
    )

    filename = f"{name.lower()}.controller.ts"
    return filename, content

def generate_service(name: str, options: dict) -> tuple:
    """Generate service file."""
    repository = options.get('repository', False)
    pascal = to_pascal_case(name)
    camel = to_camel_case(name)

    if repository:
        repository_import = f"import {{ InjectRepository }} from '@nestjs/typeorm';\nimport {{ Repository }} from 'typeorm';\nimport {{ {pascal} }} from './entities/{name.lower()}.entity';"
        repository_constructor = f"constructor(\n    @InjectRepository({pascal})\n    private readonly {camel}Repository: Repository<{pascal}>,\n  ) {{}}"
        find_all_impl = f"return this.{camel}Repository.find();"
        find_one_impl = f"""const entity = await this.{camel}Repository.findOne({{ where: {{ id }} }});
    if (!entity) {{
      throw new NotFoundException(`{pascal} with ID "${{id}}" not found`);
    }}
    return entity;"""
        create_impl = f"const entity = this.{camel}Repository.create(dto);\n    return this.{camel}Repository.save(entity);"
        update_impl = f"await this.findOne(id);\n    return this.{camel}Repository.save({{ id, ...dto }});"
        remove_impl = f"const entity = await this.findOne(id);\n    await this.{camel}Repository.remove(entity);"
    else:
        repository_import = ""
        repository_constructor = "constructor() {}"
        find_all_impl = "// TODO: Implement findAll\n    return [];"
        find_one_impl = "// TODO: Implement findOne\n    return null;"
        create_impl = "// TODO: Implement create\n    return dto;"
        update_impl = "// TODO: Implement update\n    return { id, ...dto };"
        remove_impl = "// TODO: Implement remove"

    content = SERVICE_TEMPLATE.format(
        req_id=generate_req_id(),
        name=name.lower(),
        name_pascal=pascal,
        name_camel=camel,
        repository_import=repository_import,
        repository_constructor=repository_constructor,
        find_all_impl=find_all_impl,
        find_one_impl=find_one_impl,
        create_impl=create_impl,
        update_impl=update_impl,
        remove_impl=remove_impl,
    )

    filename = f"{name.lower()}.service.ts"
    return filename, content

def generate_dto(name: str, options: dict) -> tuple:
    """Generate DTO file."""
    swagger = options.get('swagger', False)
    pascal = to_pascal_case(name)

    swagger_import = "import { ApiProperty } from '@nestjs/swagger';\n" if swagger else ''
    swagger_example = "@ApiProperty({ example: 'Example name' })" if swagger else ''
    swagger_description = "@ApiProperty({ required: false })" if swagger else ''
    extra_validators = ', MaxLength' if swagger else ''

    content = DTO_TEMPLATE.format(
        req_id=generate_req_id(),
        name_pascal=pascal,
        swagger_import=swagger_import,
        swagger_example=swagger_example,
        swagger_description=swagger_description,
        extra_validators=extra_validators,
    )

    filename = f"{name.lower()}.dto.ts"
    return filename, content

def generate_entity(name: str, options: dict) -> tuple:
    """Generate entity file."""
    pascal = to_pascal_case(name)
    plural = to_plural(name.lower())

    content = ENTITY_TEMPLATE.format(
        req_id=generate_req_id(),
        name_pascal=pascal,
        name_plural=plural,
    )

    filename = f"{name.lower()}.entity.ts"
    return filename, content

def generate_guard(name: str, options: dict) -> tuple:
    """Generate guard file."""
    pascal = to_pascal_case(name)

    content = GUARD_TEMPLATE.format(
        req_id=generate_req_id(),
        name_pascal=pascal,
    )

    filename = f"{name.lower()}.guard.ts"
    return filename, content

def generate_interceptor(name: str, options: dict) -> tuple:
    """Generate interceptor file."""
    pascal = to_pascal_case(name)

    content = INTERCEPTOR_TEMPLATE.format(
        req_id=generate_req_id(),
        name_pascal=pascal,
    )

    filename = f"{name.lower()}.interceptor.ts"
    return filename, content

def generate_pipe(name: str, options: dict) -> tuple:
    """Generate pipe file."""
    pascal = to_pascal_case(name)

    content = PIPE_TEMPLATE.format(
        req_id=generate_req_id(),
        name_pascal=pascal,
    )

    filename = f"{name.lower()}.pipe.ts"
    return filename, content

def generate_filter(name: str, options: dict) -> tuple:
    """Generate exception filter file."""
    pascal = to_pascal_case(name)

    content = FILTER_TEMPLATE.format(
        req_id=generate_req_id(),
        name_pascal=pascal,
    )

    filename = f"{name.lower()}.filter.ts"
    return filename, content

def generate_module(name: str, options: dict) -> tuple:
    """Generate module file."""
    pascal = to_pascal_case(name)

    content = MODULE_TEMPLATE.format(
        req_id=generate_req_id(),
        name_pascal=pascal,
    )

    filename = f"{name.lower()}.module.ts"
    return filename, content

# Generator mapping
GENERATORS = {
    'controller': generate_controller,
    'service': generate_service,
    'dto': generate_dto,
    'entity': generate_entity,
    'guard': generate_guard,
    'interceptor': generate_interceptor,
    'pipe': generate_pipe,
    'filter': generate_filter,
    'module': generate_module,
}

# ============================================================
# Main Generator
# ============================================================

def generate_component(component_type: str, name: str, options: dict) -> None:
    """Generate a NestJS component."""
    if component_type not in GENERATORS:
        print(f"❌ Unknown component type: {component_type}", file=sys.stderr)
        print(f"   Available types: {', '.join(GENERATORS.keys())}", file=sys.stderr)
        sys.exit(1)

    generator = GENERATORS[component_type]
    filename, content = generator(name, options)

    # Determine output path
    base_path = Path(options.get('path', '.'))

    # Create subdirectory based on component type
    if component_type == 'dto':
        output_dir = base_path / 'dto'
    elif component_type == 'entity':
        output_dir = base_path / 'entities'
    elif component_type in ['guard', 'interceptor', 'pipe', 'filter']:
        output_dir = base_path / 'common' / f"{component_type}s"
    else:
        output_dir = base_path

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename

    # Write file
    output_path.write_text(content)

    print(f"\n{'=' * 60}")
    print("NestJS Component Generator")
    print(f"{'=' * 60}")
    print(f"Type: {component_type}")
    print(f"Name: {to_pascal_case(name)}")
    print(f"Output: {output_path}")
    print(f"{'=' * 60}")
    print(f"\n✓ Successfully created {filename}!\n")

def main():
    parser = argparse.ArgumentParser(
        description='NestJS Component Generator - Creates individual components',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Component Types:
  controller   - REST API controller
  service      - Business logic service
  dto          - Data Transfer Object
  entity       - TypeORM entity
  guard        - Route guard
  interceptor  - Request/response interceptor
  pipe         - Validation/transformation pipe
  filter       - Exception filter
  module       - NestJS module

Examples:
  %(prog)s controller user
  %(prog)s service user --repository
  %(prog)s dto create-user --swagger
  %(prog)s guard roles
  %(prog)s interceptor logging
        '''
    )

    parser.add_argument('type', choices=list(GENERATORS.keys()),
                        help='Component type to generate')
    parser.add_argument('name', help='Component name (kebab-case or snake_case)')
    parser.add_argument('--swagger', action='store_true',
                        help='Add Swagger decorators (for controller/dto)')
    parser.add_argument('--repository', action='store_true',
                        help='Add repository injection (for service)')
    parser.add_argument('--path', default='.',
                        help='Output directory (default: current directory)')

    args = parser.parse_args()

    options = {
        'swagger': args.swagger,
        'repository': args.repository,
        'path': args.path,
    }

    try:
        generate_component(args.type, args.name, options)
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
