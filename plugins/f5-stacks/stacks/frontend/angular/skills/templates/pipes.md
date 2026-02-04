# Angular Pipes

## Overview

Pipes transform data for display in templates. Angular provides built-in pipes and supports custom pipes.

## Built-in Pipes

### Date Pipe

```html
<!-- Default format -->
<p>{{ today | date }}</p>

<!-- Predefined formats -->
<p>{{ today | date:'short' }}</p>      <!-- 9/3/10, 12:05 PM -->
<p>{{ today | date:'medium' }}</p>     <!-- Sep 3, 2010, 12:05:08 PM -->
<p>{{ today | date:'long' }}</p>       <!-- September 3, 2010 at 12:05:08 PM GMT+1 -->
<p>{{ today | date:'full' }}</p>       <!-- Friday, September 3, 2010 at 12:05:08 PM GMT+1 -->
<p>{{ today | date:'shortDate' }}</p>  <!-- 9/3/10 -->
<p>{{ today | date:'longDate' }}</p>   <!-- September 3, 2010 -->
<p>{{ today | date:'shortTime' }}</p>  <!-- 12:05 PM -->
<p>{{ today | date:'longTime' }}</p>   <!-- 12:05:08 PM GMT+1 -->

<!-- Custom format -->
<p>{{ today | date:'yyyy-MM-dd' }}</p>           <!-- 2010-09-03 -->
<p>{{ today | date:'dd/MM/yyyy HH:mm' }}</p>     <!-- 03/09/2010 12:05 -->
<p>{{ today | date:'EEEE, MMMM d, y' }}</p>      <!-- Friday, September 3, 2010 -->

<!-- With timezone -->
<p>{{ today | date:'full':'UTC' }}</p>
<p>{{ today | date:'short':'America/New_York' }}</p>

<!-- With locale -->
<p>{{ today | date:'full':'':'ja' }}</p>
```

### Currency Pipe

```html
<!-- Default -->
<p>{{ price | currency }}</p>                  <!-- $1,234.50 -->

<!-- Specific currency -->
<p>{{ price | currency:'EUR' }}</p>            <!-- €1,234.50 -->
<p>{{ price | currency:'JPY' }}</p>            <!-- ¥1,235 -->
<p>{{ price | currency:'GBP' }}</p>            <!-- £1,234.50 -->

<!-- Display options -->
<p>{{ price | currency:'USD':'symbol' }}</p>   <!-- $1,234.50 -->
<p>{{ price | currency:'USD':'code' }}</p>     <!-- USD1,234.50 -->
<p>{{ price | currency:'USD':'symbol-narrow' }}</p>

<!-- Digit info: {minIntegerDigits}.{minFractionDigits}-{maxFractionDigits} -->
<p>{{ price | currency:'USD':'symbol':'1.0-0' }}</p>  <!-- $1,235 -->
<p>{{ price | currency:'USD':'symbol':'1.2-2' }}</p>  <!-- $1,234.50 -->
```

### Number/Decimal Pipe

```html
<!-- Default -->
<p>{{ value | number }}</p>                    <!-- 1,234.5 -->

<!-- Digit info -->
<p>{{ value | number:'1.0-0' }}</p>            <!-- 1,235 -->
<p>{{ value | number:'1.2-2' }}</p>            <!-- 1,234.50 -->
<p>{{ value | number:'3.1-5' }}</p>            <!-- 001,234.5 -->

<!-- Percentage -->
<p>{{ 0.259 | percent }}</p>                   <!-- 26% -->
<p>{{ 0.259 | percent:'1.2-2' }}</p>           <!-- 25.90% -->
```

### Text Pipes

```html
<!-- Case transformation -->
<p>{{ 'Hello World' | uppercase }}</p>         <!-- HELLO WORLD -->
<p>{{ 'Hello World' | lowercase }}</p>         <!-- hello world -->
<p>{{ 'hello world' | titlecase }}</p>         <!-- Hello World -->

<!-- Slice -->
<p>{{ 'Hello World' | slice:0:5 }}</p>         <!-- Hello -->
<p>{{ 'Hello World' | slice:6 }}</p>           <!-- World -->
<p>{{ 'Hello World' | slice:-5 }}</p>          <!-- World -->
```

### JSON Pipe

```html
<!-- Debug objects -->
<pre>{{ user | json }}</pre>

<!-- Pretty print -->
<pre>{{ complexObject | json }}</pre>
```

### Async Pipe

```html
<!-- Subscribes and unsubscribes automatically -->
<p>{{ data$ | async }}</p>

<!-- With loading state -->
@if (data$ | async; as data) {
  <app-content [data]="data" />
} @else {
  <p>Loading...</p>
}

<!-- Multiple uses (each creates separate subscription!) -->
<!-- Better to use single subscription -->
@if (user$ | async; as user) {
  <p>{{ user.name }}</p>
  <p>{{ user.email }}</p>
}
```

### KeyValue Pipe

```html
<!-- Iterate over object -->
@for (item of object | keyvalue; track item.key) {
  <p>{{ item.key }}: {{ item.value }}</p>
}

<!-- Iterate over Map -->
@for (entry of map | keyvalue; track entry.key) {
  <p>{{ entry.key }} = {{ entry.value }}</p>
}

<!-- Custom comparator -->
@for (item of object | keyvalue:compareFn; track item.key) {
  <p>{{ item.key }}: {{ item.value }}</p>
}
```

## Custom Pipes

### Basic Custom Pipe

```typescript
import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  name: 'truncate',
  standalone: true,
})
export class TruncatePipe implements PipeTransform {
  transform(value: string, length = 50, suffix = '...'): string {
    if (!value || value.length <= length) {
      return value;
    }
    return value.substring(0, length).trim() + suffix;
  }
}

// Usage
// <p>{{ longText | truncate }}</p>
// <p>{{ longText | truncate:100 }}</p>
// <p>{{ longText | truncate:100:'…' }}</p>
```

### Pipe with Parameters

```typescript
@Pipe({
  name: 'fileSize',
  standalone: true,
})
export class FileSizePipe implements PipeTransform {
  private units = ['B', 'KB', 'MB', 'GB', 'TB'];

  transform(bytes: number, decimals = 2): string {
    if (bytes === 0) return '0 B';

    const k = 1024;
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    const size = bytes / Math.pow(k, i);

    return `${size.toFixed(decimals)} ${this.units[i]}`;
  }
}

// Usage
// <p>{{ 1024 | fileSize }}</p>         <!-- 1.00 KB -->
// <p>{{ 1536 | fileSize:1 }}</p>       <!-- 1.5 KB -->
```

### Pure vs Impure Pipes

```typescript
// Pure pipe (default) - called only when input value changes
@Pipe({
  name: 'filter',
  standalone: true,
  pure: true, // default
})
export class FilterPipe implements PipeTransform {
  transform<T>(items: T[], predicate: (item: T) => boolean): T[] {
    return items.filter(predicate);
  }
}

// Impure pipe - called on every change detection
@Pipe({
  name: 'sort',
  standalone: true,
  pure: false, // Use sparingly!
})
export class SortPipe implements PipeTransform {
  transform<T>(items: T[], key: keyof T): T[] {
    return [...items].sort((a, b) => {
      if (a[key] < b[key]) return -1;
      if (a[key] > b[key]) return 1;
      return 0;
    });
  }
}
```

### Pipe with Dependency Injection

```typescript
@Pipe({
  name: 'translate',
  standalone: true,
})
export class TranslatePipe implements PipeTransform {
  private translateService = inject(TranslateService);

  transform(key: string, params?: Record<string, string>): string {
    return this.translateService.translate(key, params);
  }
}

// Usage
// <p>{{ 'GREETING' | translate }}</p>
// <p>{{ 'WELCOME_USER' | translate:{ name: user.name } }}</p>
```

### Async Custom Pipe

```typescript
@Pipe({
  name: 'fetchUser',
  standalone: true,
})
export class FetchUserPipe implements PipeTransform {
  private userService = inject(UserService);

  transform(userId: string): Observable<User> {
    return this.userService.getUser(userId);
  }
}

// Usage
// @if (userId | fetchUser | async; as user) {
//   <p>{{ user.name }}</p>
// }
```

## Common Custom Pipes

### Time Ago Pipe

```typescript
@Pipe({
  name: 'timeAgo',
  standalone: true,
})
export class TimeAgoPipe implements PipeTransform {
  transform(value: Date | string | number): string {
    const date = new Date(value);
    const now = new Date();
    const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);

    if (seconds < 60) return 'just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)} minutes ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)} hours ago`;
    if (seconds < 2592000) return `${Math.floor(seconds / 86400)} days ago`;
    if (seconds < 31536000) return `${Math.floor(seconds / 2592000)} months ago`;
    return `${Math.floor(seconds / 31536000)} years ago`;
  }
}
```

### Safe HTML Pipe

```typescript
import { Pipe, PipeTransform, inject } from '@angular/core';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';

@Pipe({
  name: 'safeHtml',
  standalone: true,
})
export class SafeHtmlPipe implements PipeTransform {
  private sanitizer = inject(DomSanitizer);

  transform(value: string): SafeHtml {
    return this.sanitizer.bypassSecurityTrustHtml(value);
  }
}

// Usage (be careful - only use with trusted content)
// <div [innerHTML]="htmlContent | safeHtml"></div>
```

### Highlight Pipe

```typescript
@Pipe({
  name: 'highlight',
  standalone: true,
})
export class HighlightPipe implements PipeTransform {
  transform(text: string, search: string): string {
    if (!search || !text) return text;

    const pattern = search.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const regex = new RegExp(`(${pattern})`, 'gi');

    return text.replace(regex, '<mark>$1</mark>');
  }
}

// Usage
// <p [innerHTML]="item.name | highlight:searchTerm"></p>
```

## Chaining Pipes

```html
<!-- Multiple pipes -->
<p>{{ name | lowercase | titlecase }}</p>
<p>{{ date | date:'short' | uppercase }}</p>
<p>{{ longText | truncate:100 | uppercase }}</p>
```

## Best Practices

1. **Prefer pure pipes**: Impure pipes run on every change detection
2. **Keep pipes simple**: Move complex logic to services
3. **Use built-in pipes**: Before creating custom ones
4. **Cache expensive operations**: In impure pipes
5. **Avoid side effects**: Pipes should be pure functions
6. **Use async pipe**: Handles subscription management
7. **Type your transforms**: For better IDE support
