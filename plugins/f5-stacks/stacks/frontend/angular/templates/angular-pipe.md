# Angular Pipe Template

## Basic Pure Pipe

```typescript
// shared/pipes/{{name}}.pipe.ts
import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: '{{camelName}}',
  standalone: true,
  pure: true, // Default - only recalculates when input changes
})
export class {{PascalName}}Pipe implements PipeTransform {
  transform(value: string | null | undefined): string {
    if (!value) return '';
    // Transform logic
    return value.toUpperCase();
  }
}
```

## Pipe with Arguments

```typescript
// shared/pipes/truncate.pipe.ts
import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'truncate',
  standalone: true,
})
export class TruncatePipe implements PipeTransform {
  transform(
    value: string | null | undefined,
    limit: number = 100,
    ellipsis: string = '...'
  ): string {
    if (!value) return '';
    if (value.length <= limit) return value;
    return value.substring(0, limit) + ellipsis;
  }
}

// Usage: {{ text | truncate:50:'...' }}
```

## Currency Format Pipe

```typescript
// shared/pipes/currency-format.pipe.ts
import { Pipe, PipeTransform, inject, LOCALE_ID } from '@angular/core';
import { formatCurrency, getCurrencySymbol } from '@angular/common';

@Pipe({
  name: 'currencyFormat',
  standalone: true,
})
export class CurrencyFormatPipe implements PipeTransform {
  private locale = inject(LOCALE_ID);

  transform(
    value: number | null | undefined,
    currencyCode: string = 'USD',
    display: 'code' | 'symbol' | 'symbol-narrow' = 'symbol',
    digitsInfo: string = '1.2-2'
  ): string {
    if (value == null) return '';

    return formatCurrency(
      value,
      this.locale,
      getCurrencySymbol(currencyCode, display === 'symbol-narrow' ? 'narrow' : 'wide'),
      currencyCode,
      digitsInfo
    );
  }
}

// Usage: {{ price | currencyFormat:'EUR':'symbol':'1.2-2' }}
```

## Date Relative Pipe

```typescript
// shared/pipes/relative-time.pipe.ts
import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'relativeTime',
  standalone: true,
})
export class RelativeTimePipe implements PipeTransform {
  transform(value: Date | string | number | null | undefined): string {
    if (!value) return '';

    const date = new Date(value);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHour = Math.floor(diffMin / 60);
    const diffDay = Math.floor(diffHour / 24);
    const diffMonth = Math.floor(diffDay / 30);
    const diffYear = Math.floor(diffMonth / 12);

    if (diffSec < 60) return 'just now';
    if (diffMin < 60) return `${diffMin} minute${diffMin > 1 ? 's' : ''} ago`;
    if (diffHour < 24) return `${diffHour} hour${diffHour > 1 ? 's' : ''} ago`;
    if (diffDay < 30) return `${diffDay} day${diffDay > 1 ? 's' : ''} ago`;
    if (diffMonth < 12) return `${diffMonth} month${diffMonth > 1 ? 's' : ''} ago`;
    return `${diffYear} year${diffYear > 1 ? 's' : ''} ago`;
  }
}

// Usage: {{ createdAt | relativeTime }}
```

## Filter Array Pipe

```typescript
// shared/pipes/filter.pipe.ts
import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'filter',
  standalone: true,
})
export class FilterPipe implements PipeTransform {
  transform<T>(
    items: T[] | null | undefined,
    field: keyof T,
    value: any
  ): T[] {
    if (!items || !field) return items || [];
    return items.filter(item => item[field] === value);
  }
}

// Usage: {{ users | filter:'role':'admin' }}
```

## Search Filter Pipe

```typescript
// shared/pipes/search.pipe.ts
import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'search',
  standalone: true,
})
export class SearchPipe implements PipeTransform {
  transform<T extends Record<string, any>>(
    items: T[] | null | undefined,
    searchTerm: string,
    fields: (keyof T)[]
  ): T[] {
    if (!items || !searchTerm || !fields.length) return items || [];

    const term = searchTerm.toLowerCase();

    return items.filter(item =>
      fields.some(field => {
        const value = item[field];
        if (value == null) return false;
        return String(value).toLowerCase().includes(term);
      })
    );
  }
}

// Usage: {{ users | search:searchQuery:['name', 'email'] }}
```

## Sort Pipe

```typescript
// shared/pipes/sort.pipe.ts
import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'sort',
  standalone: true,
})
export class SortPipe implements PipeTransform {
  transform<T>(
    items: T[] | null | undefined,
    field: keyof T,
    direction: 'asc' | 'desc' = 'asc'
  ): T[] {
    if (!items || !field) return items || [];

    return [...items].sort((a, b) => {
      const aVal = a[field];
      const bVal = b[field];

      if (aVal == null) return direction === 'asc' ? 1 : -1;
      if (bVal == null) return direction === 'asc' ? -1 : 1;

      if (aVal < bVal) return direction === 'asc' ? -1 : 1;
      if (aVal > bVal) return direction === 'asc' ? 1 : -1;
      return 0;
    });
  }
}

// Usage: {{ items | sort:'name':'desc' }}
```

## Safe HTML Pipe

```typescript
// shared/pipes/safe-html.pipe.ts
import { Pipe, PipeTransform, inject } from '@angular/core';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';

@Pipe({
  name: 'safeHtml',
  standalone: true,
})
export class SafeHtmlPipe implements PipeTransform {
  private sanitizer = inject(DomSanitizer);

  transform(value: string | null | undefined): SafeHtml {
    if (!value) return '';
    return this.sanitizer.bypassSecurityTrustHtml(value);
  }
}

// Usage: <div [innerHTML]="content | safeHtml"></div>
// Warning: Only use with trusted content!
```

## File Size Pipe

```typescript
// shared/pipes/file-size.pipe.ts
import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'fileSize',
  standalone: true,
})
export class FileSizePipe implements PipeTransform {
  private units = ['B', 'KB', 'MB', 'GB', 'TB'];

  transform(
    bytes: number | null | undefined,
    precision: number = 2
  ): string {
    if (bytes == null || isNaN(bytes)) return '';
    if (bytes === 0) return '0 B';

    const unitIndex = Math.floor(Math.log(bytes) / Math.log(1024));
    const value = bytes / Math.pow(1024, unitIndex);

    return `${value.toFixed(precision)} ${this.units[unitIndex]}`;
  }
}

// Usage: {{ file.size | fileSize:1 }}
```

## Highlight Pipe

```typescript
// shared/pipes/highlight.pipe.ts
import { Pipe, PipeTransform, inject } from '@angular/core';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';

@Pipe({
  name: 'highlight',
  standalone: true,
})
export class HighlightPipe implements PipeTransform {
  private sanitizer = inject(DomSanitizer);

  transform(
    text: string | null | undefined,
    search: string,
    cssClass: string = 'highlight'
  ): SafeHtml {
    if (!text || !search) return text || '';

    const escaped = search.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const pattern = new RegExp(`(${escaped})`, 'gi');
    const result = text.replace(pattern, `<mark class="${cssClass}">$1</mark>`);

    return this.sanitizer.bypassSecurityTrustHtml(result);
  }
}

// Usage: <span [innerHTML]="name | highlight:searchTerm"></span>
```

## Impure Pipe (Use Sparingly)

```typescript
// shared/pipes/time-ago.pipe.ts
import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'timeAgoLive',
  standalone: true,
  pure: false, // Re-evaluates on every change detection cycle
})
export class TimeAgoLivePipe implements PipeTransform {
  transform(value: Date | string | number | null | undefined): string {
    if (!value) return '';

    const date = new Date(value);
    const now = new Date();
    const diffSec = Math.floor((now.getTime() - date.getTime()) / 1000);

    if (diffSec < 60) return `${diffSec}s ago`;
    if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`;
    if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h ago`;
    return `${Math.floor(diffSec / 86400)}d ago`;
  }
}

// Warning: Impure pipes can impact performance!
// Consider using signals or observables instead.
```

## Async Pipe Alternative with Signals

```typescript
// shared/pipes/signal.pipe.ts
import { Pipe, PipeTransform, signal, effect } from '@angular/core';
import { Observable, Subscription } from 'rxjs';

// Instead of creating a custom async pipe, use toSignal()
// This is just for demonstration

import { toSignal } from '@angular/core/rxjs-interop';

// In component:
// data = toSignal(this.dataService.getData(), { initialValue: [] });
// Then in template: {{ data() }}
```

## Pluralize Pipe

```typescript
// shared/pipes/pluralize.pipe.ts
import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'pluralize',
  standalone: true,
})
export class PluralizePipe implements PipeTransform {
  transform(
    count: number | null | undefined,
    singular: string,
    plural?: string
  ): string {
    if (count == null) return '';

    const word = count === 1 ? singular : (plural || `${singular}s`);
    return `${count} ${word}`;
  }
}

// Usage: {{ items.length | pluralize:'item':'items' }}
// Output: "1 item" or "5 items"
```

## Mask Pipe

```typescript
// shared/pipes/mask.pipe.ts
import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'mask',
  standalone: true,
})
export class MaskPipe implements PipeTransform {
  transform(
    value: string | null | undefined,
    visibleStart: number = 4,
    visibleEnd: number = 4,
    maskChar: string = '*'
  ): string {
    if (!value) return '';

    const length = value.length;
    if (length <= visibleStart + visibleEnd) return value;

    const start = value.substring(0, visibleStart);
    const end = value.substring(length - visibleEnd);
    const masked = maskChar.repeat(length - visibleStart - visibleEnd);

    return `${start}${masked}${end}`;
  }
}

// Usage: {{ creditCard | mask:4:4:'*' }}
// Output: "1234********5678"
```

## Phone Format Pipe

```typescript
// shared/pipes/phone.pipe.ts
import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'phone',
  standalone: true,
})
export class PhonePipe implements PipeTransform {
  transform(
    value: string | null | undefined,
    format: 'us' | 'international' = 'us'
  ): string {
    if (!value) return '';

    const digits = value.replace(/\D/g, '');

    if (format === 'us' && digits.length === 10) {
      return `(${digits.slice(0, 3)}) ${digits.slice(3, 6)}-${digits.slice(6)}`;
    }

    if (format === 'international' && digits.length >= 10) {
      const countryCode = digits.slice(0, digits.length - 10);
      const number = digits.slice(-10);
      return `+${countryCode} ${number.slice(0, 3)} ${number.slice(3, 6)} ${number.slice(6)}`;
    }

    return value;
  }
}

// Usage: {{ phoneNumber | phone:'us' }}
```

## Pipe Barrel Export

```typescript
// shared/pipes/index.ts
export * from './truncate.pipe';
export * from './currency-format.pipe';
export * from './relative-time.pipe';
export * from './filter.pipe';
export * from './search.pipe';
export * from './sort.pipe';
export * from './safe-html.pipe';
export * from './file-size.pipe';
export * from './highlight.pipe';
export * from './pluralize.pipe';
export * from './mask.pipe';
export * from './phone.pipe';
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{name}}` | kebab-case name | `relative-time` |
| `{{camelName}}` | camelCase name | `relativeTime` |
| `{{PascalName}}` | PascalCase name | `RelativeTime` |
