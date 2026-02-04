---
name: nestjs-pipe
description: NestJS pipe template
applies_to: nestjs
category: template
---

# NestJS Pipe Template

## Basic Pipe

```typescript
// common/pipes/{{pipe}}.pipe.ts
import {
  PipeTransform,
  Injectable,
  ArgumentMetadata,
  BadRequestException,
} from '@nestjs/common';

@Injectable()
export class {{Pipe}}Pipe implements PipeTransform {
  transform(value: any, metadata: ArgumentMetadata) {
    // Transform logic
    return value;
  }
}
```

## Parse UUID Pipe

```typescript
// common/pipes/parse-uuid.pipe.ts
import {
  PipeTransform,
  Injectable,
  BadRequestException,
} from '@nestjs/common';
import { validate as uuidValidate, version as uuidVersion } from 'uuid';

@Injectable()
export class ParseUUIDPipe implements PipeTransform<string> {
  constructor(private readonly version?: 4 | 5) {}

  transform(value: string): string {
    if (!value) {
      throw new BadRequestException('UUID is required');
    }

    if (!uuidValidate(value)) {
      throw new BadRequestException(`Invalid UUID format: ${value}`);
    }

    if (this.version && uuidVersion(value) !== this.version) {
      throw new BadRequestException(
        `UUID must be version ${this.version}`,
      );
    }

    return value;
  }
}

// Usage
@Get(':id')
findOne(@Param('id', ParseUUIDPipe) id: string) {
  return this.service.findById(id);
}
```

## Parse Int Pipe with Options

```typescript
// common/pipes/parse-int.pipe.ts
import {
  PipeTransform,
  Injectable,
  BadRequestException,
} from '@nestjs/common';

export interface ParseIntPipeOptions {
  min?: number;
  max?: number;
  defaultValue?: number;
  optional?: boolean;
}

@Injectable()
export class ParseIntPipe implements PipeTransform<string, number> {
  constructor(private options: ParseIntPipeOptions = {}) {}

  transform(value: string): number {
    if (!value && this.options.optional) {
      return this.options.defaultValue;
    }

    const parsed = parseInt(value, 10);

    if (isNaN(parsed)) {
      throw new BadRequestException(`"${value}" is not a valid integer`);
    }

    if (this.options.min !== undefined && parsed < this.options.min) {
      throw new BadRequestException(
        `Value must be at least ${this.options.min}`,
      );
    }

    if (this.options.max !== undefined && parsed > this.options.max) {
      throw new BadRequestException(
        `Value must be at most ${this.options.max}`,
      );
    }

    return parsed;
  }
}

// Usage
@Get()
findAll(
  @Query('page', new ParseIntPipe({ min: 1, defaultValue: 1 })) page: number,
  @Query('limit', new ParseIntPipe({ min: 1, max: 100, defaultValue: 10 })) limit: number,
) {
  return this.service.findAll({ page, limit });
}
```

## Parse Boolean Pipe

```typescript
// common/pipes/parse-boolean.pipe.ts
import {
  PipeTransform,
  Injectable,
  BadRequestException,
} from '@nestjs/common';

@Injectable()
export class ParseBooleanPipe implements PipeTransform<string, boolean> {
  transform(value: string): boolean {
    if (value === undefined || value === null) {
      return false;
    }

    const truthyValues = ['true', '1', 'yes', 'on'];
    const falsyValues = ['false', '0', 'no', 'off'];

    const normalized = value.toLowerCase().trim();

    if (truthyValues.includes(normalized)) {
      return true;
    }

    if (falsyValues.includes(normalized)) {
      return false;
    }

    throw new BadRequestException(
      `"${value}" is not a valid boolean value`,
    );
  }
}
```

## Parse Date Pipe

```typescript
// common/pipes/parse-date.pipe.ts
import {
  PipeTransform,
  Injectable,
  BadRequestException,
} from '@nestjs/common';

export interface ParseDatePipeOptions {
  optional?: boolean;
  minDate?: Date;
  maxDate?: Date;
}

@Injectable()
export class ParseDatePipe implements PipeTransform<string, Date> {
  constructor(private options: ParseDatePipeOptions = {}) {}

  transform(value: string): Date {
    if (!value && this.options.optional) {
      return undefined;
    }

    const date = new Date(value);

    if (isNaN(date.getTime())) {
      throw new BadRequestException(`"${value}" is not a valid date`);
    }

    if (this.options.minDate && date < this.options.minDate) {
      throw new BadRequestException(
        `Date must be after ${this.options.minDate.toISOString()}`,
      );
    }

    if (this.options.maxDate && date > this.options.maxDate) {
      throw new BadRequestException(
        `Date must be before ${this.options.maxDate.toISOString()}`,
      );
    }

    return date;
  }
}
```

## Parse Enum Pipe

```typescript
// common/pipes/parse-enum.pipe.ts
import {
  PipeTransform,
  Injectable,
  BadRequestException,
} from '@nestjs/common';

@Injectable()
export class ParseEnumPipe<T extends object>
  implements PipeTransform<string, T[keyof T]>
{
  constructor(private enumType: T) {}

  transform(value: string): T[keyof T] {
    const enumValues = Object.values(this.enumType);

    if (!enumValues.includes(value as T[keyof T])) {
      throw new BadRequestException(
        `"${value}" must be one of: ${enumValues.join(', ')}`,
      );
    }

    return value as T[keyof T];
  }
}

// Usage
enum Status {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
}

@Get()
findByStatus(
  @Query('status', new ParseEnumPipe(Status)) status: Status,
) {
  return this.service.findByStatus(status);
}
```

## Trim Pipe

```typescript
// common/pipes/trim.pipe.ts
import { PipeTransform, Injectable } from '@nestjs/common';

@Injectable()
export class TrimPipe implements PipeTransform {
  transform(value: any): any {
    if (typeof value === 'string') {
      return value.trim();
    }

    if (typeof value === 'object' && value !== null) {
      return this.trimObject(value);
    }

    return value;
  }

  private trimObject(obj: any): any {
    const result: any = {};

    for (const key in obj) {
      if (obj.hasOwnProperty(key)) {
        const value = obj[key];
        if (typeof value === 'string') {
          result[key] = value.trim();
        } else if (typeof value === 'object' && value !== null) {
          result[key] = this.trimObject(value);
        } else {
          result[key] = value;
        }
      }
    }

    return result;
  }
}
```

## Sanitize HTML Pipe

```typescript
// common/pipes/sanitize-html.pipe.ts
import { PipeTransform, Injectable } from '@nestjs/common';
import * as sanitizeHtml from 'sanitize-html';

export interface SanitizeHtmlPipeOptions {
  allowedTags?: string[];
  allowedAttributes?: Record<string, string[]>;
}

@Injectable()
export class SanitizeHtmlPipe implements PipeTransform {
  constructor(private options: SanitizeHtmlPipeOptions = {}) {}

  transform(value: any): any {
    if (typeof value === 'string') {
      return this.sanitize(value);
    }

    if (typeof value === 'object' && value !== null) {
      return this.sanitizeObject(value);
    }

    return value;
  }

  private sanitize(value: string): string {
    return sanitizeHtml(value, {
      allowedTags: this.options.allowedTags || [],
      allowedAttributes: this.options.allowedAttributes || {},
    });
  }

  private sanitizeObject(obj: any): any {
    const result: any = {};

    for (const key in obj) {
      if (obj.hasOwnProperty(key)) {
        const value = obj[key];
        if (typeof value === 'string') {
          result[key] = this.sanitize(value);
        } else if (typeof value === 'object' && value !== null) {
          result[key] = this.sanitizeObject(value);
        } else {
          result[key] = value;
        }
      }
    }

    return result;
  }
}
```

## File Validation Pipe

```typescript
// common/pipes/file-validation.pipe.ts
import {
  PipeTransform,
  Injectable,
  BadRequestException,
  PayloadTooLargeException,
  UnsupportedMediaTypeException,
} from '@nestjs/common';

export interface FileValidationPipeOptions {
  maxSize?: number; // in bytes
  mimeTypes?: string[];
  required?: boolean;
}

@Injectable()
export class FileValidationPipe implements PipeTransform {
  constructor(private options: FileValidationPipeOptions = {}) {}

  transform(file: Express.Multer.File): Express.Multer.File {
    if (!file) {
      if (this.options.required) {
        throw new BadRequestException('File is required');
      }
      return file;
    }

    // Check file size
    if (this.options.maxSize && file.size > this.options.maxSize) {
      throw new PayloadTooLargeException(
        `File size exceeds ${this.options.maxSize / (1024 * 1024)}MB limit`,
      );
    }

    // Check mime type
    if (
      this.options.mimeTypes &&
      !this.options.mimeTypes.includes(file.mimetype)
    ) {
      throw new UnsupportedMediaTypeException(
        `File type ${file.mimetype} is not allowed. Allowed types: ${this.options.mimeTypes.join(', ')}`,
      );
    }

    return file;
  }
}

// Usage
@Post('upload')
@UseInterceptors(FileInterceptor('file'))
uploadFile(
  @UploadedFile(
    new FileValidationPipe({
      maxSize: 5 * 1024 * 1024, // 5MB
      mimeTypes: ['image/jpeg', 'image/png', 'application/pdf'],
      required: true,
    }),
  )
  file: Express.Multer.File,
) {
  return this.service.upload(file);
}
```

## Array Parse Pipe

```typescript
// common/pipes/parse-array.pipe.ts
import {
  PipeTransform,
  Injectable,
  BadRequestException,
} from '@nestjs/common';

export interface ParseArrayPipeOptions {
  separator?: string;
  unique?: boolean;
  maxLength?: number;
  itemType?: 'string' | 'number' | 'uuid';
}

@Injectable()
export class ParseArrayPipe implements PipeTransform<string, any[]> {
  constructor(private options: ParseArrayPipeOptions = {}) {}

  transform(value: string): any[] {
    if (!value) {
      return [];
    }

    const separator = this.options.separator || ',';
    let items = value.split(separator).map((item) => item.trim());

    // Remove duplicates if unique
    if (this.options.unique) {
      items = [...new Set(items)];
    }

    // Check max length
    if (this.options.maxLength && items.length > this.options.maxLength) {
      throw new BadRequestException(
        `Array exceeds maximum length of ${this.options.maxLength}`,
      );
    }

    // Transform item types
    return items.map((item) => this.transformItem(item));
  }

  private transformItem(item: string): any {
    switch (this.options.itemType) {
      case 'number':
        const num = parseInt(item, 10);
        if (isNaN(num)) {
          throw new BadRequestException(`"${item}" is not a valid number`);
        }
        return num;
      case 'uuid':
        const uuidRegex =
          /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
        if (!uuidRegex.test(item)) {
          throw new BadRequestException(`"${item}" is not a valid UUID`);
        }
        return item;
      default:
        return item;
    }
  }
}

// Usage
@Get()
findByIds(
  @Query('ids', new ParseArrayPipe({ itemType: 'uuid', unique: true }))
  ids: string[],
) {
  return this.service.findByIds(ids);
}
```

## Global Pipe Registration

```typescript
// main.ts
import { ValidationPipe } from '@nestjs/common';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);

  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true,
      forbidNonWhitelisted: true,
      transform: true,
      transformOptions: {
        enableImplicitConversion: true,
      },
    }),
    new TrimPipe(),
  );

  await app.listen(3000);
}

// Or via module
@Module({
  providers: [
    {
      provide: APP_PIPE,
      useClass: ValidationPipe,
    },
  ],
})
export class AppModule {}
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{pipe}}` | Pipe name (lowercase, kebab-case) | parse-uuid |
| `{{Pipe}}` | Pipe name (PascalCase) | ParseUUID |
