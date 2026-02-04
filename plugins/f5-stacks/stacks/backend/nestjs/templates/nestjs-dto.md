---
name: nestjs-dto
description: NestJS DTO template with validation
applies_to: nestjs
category: template
---

# NestJS DTO Template

## Create DTO

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
} from 'class-validator';
import { Type } from 'class-transformer';
import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';

export class Create{{Entity}}Dto {
  @ApiProperty({ description: '{{field_description}}', example: '{{example}}' })
  @IsString()
  @IsNotEmpty()
  @MinLength({{min_length}})
  @MaxLength({{max_length}})
  {{field}}: string;

  @ApiPropertyOptional({ description: 'Optional field' })
  @IsOptional()
  @IsString()
  optionalField?: string;

  @ApiProperty({ description: 'Email address' })
  @IsEmail()
  email: string;

  @ApiProperty({ description: 'Numeric value', minimum: 0 })
  @IsNumber()
  @Min(0)
  amount: number;

  @ApiProperty({ enum: {{EnumName}}, description: 'Status' })
  @IsEnum({{EnumName}})
  status: {{EnumName}};

  @ApiProperty({ type: [String], description: 'Tags' })
  @IsArray()
  @IsString({ each: true })
  tags: string[];

  @ApiProperty({ type: () => NestedDto })
  @ValidateNested()
  @Type(() => NestedDto)
  nested: NestedDto;
}
```

## Update DTO

```typescript
// modules/{{module}}/dto/update-{{entity}}.dto.ts
import { PartialType } from '@nestjs/swagger';
import { Create{{Entity}}Dto } from './create-{{entity}}.dto';

export class Update{{Entity}}Dto extends PartialType(Create{{Entity}}Dto) {}
```

## Query DTO

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

  @ApiPropertyOptional()
  @IsOptional()
  @IsString()
  search?: string;

  @ApiPropertyOptional({ enum: ['asc', 'desc'], default: 'desc' })
  @IsOptional()
  @IsEnum(['asc', 'desc'])
  sortOrder?: 'asc' | 'desc' = 'desc';

  @ApiPropertyOptional()
  @IsOptional()
  @IsString()
  sortBy?: string = 'createdAt';
}
```

## Response DTO

```typescript
// modules/{{module}}/dto/{{entity}}-response.dto.ts
import { Expose, Type, Exclude } from 'class-transformer';
import { ApiProperty } from '@nestjs/swagger';

@Exclude()
export class {{Entity}}ResponseDto {
  @Expose()
  @ApiProperty()
  id: string;

  @Expose()
  @ApiProperty()
  {{field}}: string;

  @Expose()
  @ApiProperty()
  createdAt: Date;

  @Expose()
  @ApiProperty()
  updatedAt: Date;

  @Expose()
  @Type(() => RelatedResponseDto)
  @ApiProperty({ type: () => RelatedResponseDto })
  related: RelatedResponseDto;

  constructor(partial: Partial<{{Entity}}ResponseDto>) {
    Object.assign(this, partial);
  }
}
```

## Paginated Response DTO

```typescript
// common/dto/paginated-response.dto.ts
import { ApiProperty } from '@nestjs/swagger';

export class PaginatedResponseDto<T> {
  @ApiProperty({ isArray: true })
  items: T[];

  @ApiProperty()
  total: number;

  @ApiProperty()
  page: number;

  @ApiProperty()
  limit: number;

  @ApiProperty()
  totalPages: number;

  @ApiProperty()
  hasNext: boolean;

  @ApiProperty()
  hasPrevious: boolean;
}
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{module}}` | Module name (lowercase) | users |
| `{{entity}}` | Entity name (lowercase) | user |
| `{{Entity}}` | Entity name (PascalCase) | User |
| `{{field}}` | Field name | name |
| `{{field_description}}` | Field description | User full name |
| `{{example}}` | Example value | John Doe |
| `{{min_length}}` | Minimum length | 2 |
| `{{max_length}}` | Maximum length | 100 |
| `{{EnumName}}` | Enum type name | UserStatus |
