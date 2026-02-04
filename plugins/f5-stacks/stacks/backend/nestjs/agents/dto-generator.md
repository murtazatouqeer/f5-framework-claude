---
name: nestjs-dto-generator
description: Agent for generating NestJS DTOs with validation
applies_to: nestjs
category: agent
---

# NestJS DTO Generator Agent

## Purpose

Generate complete DTO sets (Create, Update, Query, Response) with proper validation decorators and Swagger documentation.

## Input Requirements

```yaml
required:
  - entity_name: string        # e.g., "user"
  - fields: array              # Field definitions

optional:
  - module_name: string        # Module path (defaults to entity_name + 's')
  - swagger: boolean           # Add Swagger decorators (default: true)
  - validation_groups: boolean # Add validation groups (default: false)
  - response_dto: boolean      # Generate response DTO (default: true)
  - query_dto: boolean         # Generate query DTO (default: true)
```

## Field Definition Schema

```yaml
fields:
  - name: string               # Field name
    type: string               # TypeScript type
    required: boolean          # Is required in create DTO
    validators: array          # Validation decorators
    swagger:                   # Swagger metadata
      description: string
      example: any
    create: boolean            # Include in create DTO (default: true)
    update: boolean            # Include in update DTO (default: true)
    response: boolean          # Include in response DTO (default: true)
    query: boolean             # Include as query filter (default: false)
```

## Generation Process

### Step 1: Parse Field Definitions

```typescript
interface FieldDefinition {
  name: string;
  type: string;
  required: boolean;
  validators: string[];
  swagger: {
    description: string;
    example: any;
  };
  create: boolean;
  update: boolean;
  response: boolean;
  query: boolean;
}

const fields: FieldDefinition[] = [
  {
    name: 'email',
    type: 'string',
    required: true,
    validators: ['IsEmail', 'IsNotEmpty'],
    swagger: {
      description: 'User email address',
      example: 'user@example.com',
    },
    create: true,
    update: true,
    response: true,
    query: true,
  },
  {
    name: 'name',
    type: 'string',
    required: true,
    validators: ['IsString', 'MinLength(2)', 'MaxLength(100)'],
    swagger: {
      description: 'User full name',
      example: 'John Doe',
    },
    create: true,
    update: true,
    response: true,
    query: false,
  },
  // ... more fields
];
```

### Step 2: Generate Create DTO

```typescript
// modules/{{module}}/dto/create-{{entity}}.dto.ts
import {
  IsString,
  IsNotEmpty,
  IsOptional,
  IsEmail,
  IsUUID,
  IsInt,
  IsNumber,
  IsBoolean,
  IsEnum,
  IsArray,
  IsDate,
  MinLength,
  MaxLength,
  Min,
  Max,
  ValidateNested,
  ArrayMinSize,
  ArrayMaxSize,
  Matches,
} from 'class-validator';
import { Type } from 'class-transformer';
import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';

export class Create{{Entity}}Dto {
{{#each createFields}}
  {{#if required}}
  @ApiProperty({
    description: '{{swagger.description}}',
    example: {{swagger.example}},
  })
  {{#each validators}}
  @{{this}}
  {{/each}}
  {{name}}: {{type}};
  {{else}}
  @ApiPropertyOptional({
    description: '{{swagger.description}}',
    example: {{swagger.example}},
  })
  @IsOptional()
  {{#each validators}}
  @{{this}}
  {{/each}}
  {{name}}?: {{type}};
  {{/if}}

{{/each}}
}
```

### Step 3: Generate Update DTO

```typescript
// modules/{{module}}/dto/update-{{entity}}.dto.ts
import { PartialType } from '@nestjs/swagger';
import { Create{{Entity}}Dto } from './create-{{entity}}.dto';

export class Update{{Entity}}Dto extends PartialType(Create{{Entity}}Dto) {}

// Or with custom fields
import { OmitType, PartialType } from '@nestjs/swagger';
import { Create{{Entity}}Dto } from './create-{{entity}}.dto';

export class Update{{Entity}}Dto extends PartialType(
  OmitType(Create{{Entity}}Dto, ['{{immutableField}}'] as const),
) {
  // Additional update-only fields
}
```

### Step 4: Generate Query DTO

```typescript
// modules/{{module}}/dto/query-{{entity}}.dto.ts
import { IsOptional, IsInt, IsString, IsEnum, Min, Max } from 'class-validator';
import { Type } from 'class-transformer';
import { ApiPropertyOptional } from '@nestjs/swagger';

export class Query{{Entity}}Dto {
  @ApiPropertyOptional({ default: 1, minimum: 1 })
  @IsOptional()
  @Type(() => Number)
  @IsInt()
  @Min(1)
  page?: number = 1;

  @ApiPropertyOptional({ default: 10, minimum: 1, maximum: 100 })
  @IsOptional()
  @Type(() => Number)
  @IsInt()
  @Min(1)
  @Max(100)
  limit?: number = 10;

  @ApiPropertyOptional({ description: 'Search term' })
  @IsOptional()
  @IsString()
  search?: string;

  @ApiPropertyOptional({ enum: ['asc', 'desc'], default: 'desc' })
  @IsOptional()
  @IsEnum(['asc', 'desc'])
  sortOrder?: 'asc' | 'desc' = 'desc';

  @ApiPropertyOptional({ default: 'createdAt' })
  @IsOptional()
  @IsString()
  sortBy?: string = 'createdAt';

{{#each queryFields}}
  @ApiPropertyOptional({ description: '{{swagger.description}}' })
  @IsOptional()
  {{#each validators}}
  @{{this}}
  {{/each}}
  {{name}}?: {{type}};

{{/each}}
}
```

### Step 5: Generate Response DTO

```typescript
// modules/{{module}}/dto/{{entity}}-response.dto.ts
import { Expose, Type, Exclude } from 'class-transformer';
import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';

@Exclude()
export class {{Entity}}ResponseDto {
  @Expose()
  @ApiProperty({ description: 'Unique identifier' })
  id: string;

{{#each responseFields}}
  @Expose()
  {{#if required}}
  @ApiProperty({
    description: '{{swagger.description}}',
    example: {{swagger.example}},
  })
  {{else}}
  @ApiPropertyOptional({
    description: '{{swagger.description}}',
    example: {{swagger.example}},
  })
  {{/if}}
  {{#if isNested}}
  @Type(() => {{nestedType}}ResponseDto)
  {{/if}}
  {{name}}{{#unless required}}?{{/unless}}: {{type}};

{{/each}}
  @Expose()
  @ApiProperty({ description: 'Creation timestamp' })
  createdAt: Date;

  @Expose()
  @ApiProperty({ description: 'Last update timestamp' })
  updatedAt: Date;

  constructor(partial: Partial<{{Entity}}ResponseDto>) {
    Object.assign(this, partial);
  }
}
```

### Step 6: Generate Index Export

```typescript
// modules/{{module}}/dto/index.ts
export * from './create-{{entity}}.dto';
export * from './update-{{entity}}.dto';
export * from './query-{{entity}}.dto';
export * from './{{entity}}-response.dto';
```

## Validator Mapping

| Field Type | Common Validators |
|------------|-------------------|
| string | IsString, IsNotEmpty, MinLength, MaxLength |
| email | IsEmail, IsNotEmpty |
| uuid | IsUUID |
| number | IsNumber, Min, Max |
| integer | IsInt, Min, Max |
| boolean | IsBoolean |
| date | IsDate, MinDate, MaxDate |
| enum | IsEnum |
| array | IsArray, ArrayMinSize, ArrayMaxSize |
| nested | ValidateNested, Type |

## Output Files

```
modules/{{module}}/dto/
├── create-{{entity}}.dto.ts
├── update-{{entity}}.dto.ts
├── query-{{entity}}.dto.ts
├── {{entity}}-response.dto.ts
└── index.ts
```

## Usage Example

```bash
# Generate DTOs via agent
@nestjs:dto-generator {
  "entity_name": "product",
  "module_name": "products",
  "fields": [
    {
      "name": "name",
      "type": "string",
      "required": true,
      "validators": ["IsString", "IsNotEmpty", "MinLength(2)", "MaxLength(100)"],
      "swagger": { "description": "Product name", "example": "Widget" }
    },
    {
      "name": "price",
      "type": "number",
      "required": true,
      "validators": ["IsNumber", "IsPositive", "Max(999999.99)"],
      "swagger": { "description": "Product price", "example": 29.99 }
    },
    {
      "name": "description",
      "type": "string",
      "required": false,
      "validators": ["IsString", "MaxLength(1000)"],
      "swagger": { "description": "Product description", "example": "A great widget" }
    }
  ]
}
```

## Validation Checklist

- [ ] All required fields have IsNotEmpty
- [ ] String fields have length constraints
- [ ] Number fields have range constraints
- [ ] Email fields use IsEmail
- [ ] UUID fields use IsUUID
- [ ] Nested objects use ValidateNested + Type
- [ ] Arrays have size constraints
- [ ] Swagger decorators have descriptions and examples
- [ ] Response DTO uses Expose decorator
- [ ] Index file exports all DTOs
