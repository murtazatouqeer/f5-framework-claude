# Angular Control Flow

## Overview

Angular 17+ introduces built-in control flow syntax with `@if`, `@for`, `@switch`, and `@defer`. This replaces the older structural directives like `*ngIf` and `*ngFor`.

## @if Block

### Basic Conditionals

```html
<!-- Simple condition -->
@if (isLoggedIn()) {
  <app-dashboard />
}

<!-- With else -->
@if (user()) {
  <p>Welcome, {{ user().name }}!</p>
} @else {
  <p>Please log in</p>
}

<!-- Multiple conditions -->
@if (isLoading()) {
  <app-spinner />
} @else if (error()) {
  <app-error-message [error]="error()" />
} @else if (data()) {
  <app-content [data]="data()" />
} @else {
  <p>No data available</p>
}
```

### Complex Conditions

```html
<!-- Combined conditions -->
@if (user() && user().isAdmin) {
  <app-admin-panel />
}

<!-- With computed values -->
@if (hasPermission()) {
  <button>Edit</button>
}

<!-- Null checks -->
@if (items()?.length > 0) {
  <app-item-list [items]="items()" />
}
```

## @for Block

### Basic Iteration

```html
<!-- Simple loop -->
@for (item of items(); track item.id) {
  <div class="item">{{ item.name }}</div>
}

<!-- With empty state -->
@for (product of products(); track product.id) {
  <app-product-card [product]="product" />
} @empty {
  <p class="no-results">No products found</p>
}
```

### Track Expression

```html
<!-- Track by id (most common) -->
@for (user of users(); track user.id) {
  <app-user-card [user]="user" />
}

<!-- Track by index -->
@for (item of items(); track $index) {
  <div>{{ item }}</div>
}

<!-- Track by composite key -->
@for (item of items(); track item.category + item.id) {
  <div>{{ item.name }}</div>
}

<!-- Track by identity (for primitive arrays) -->
@for (name of names(); track name) {
  <span>{{ name }}</span>
}
```

### Loop Context Variables

```html
@for (item of items(); track item.id; let idx = $index, first = $first, last = $last, even = $even, odd = $odd, count = $count) {
  <div
    [class.first]="first"
    [class.last]="last"
    [class.even]="even"
    [class.odd]="odd"
  >
    {{ idx + 1 }} of {{ count }}: {{ item.name }}
  </div>
}

<!-- Shorthand syntax -->
@for (item of items(); track item.id; let i = $index) {
  <div>{{ i + 1 }}. {{ item.name }}</div>
}
```

### Nested Loops

```html
@for (category of categories(); track category.id) {
  <div class="category">
    <h3>{{ category.name }}</h3>

    @for (item of category.items; track item.id) {
      <div class="item">
        {{ item.name }} - {{ item.price | currency }}
      </div>
    } @empty {
      <p>No items in this category</p>
    }
  </div>
}
```

## @switch Block

### Basic Switch

```html
@switch (status()) {
  @case ('loading') {
    <app-loading-spinner />
  }
  @case ('error') {
    <app-error-message />
  }
  @case ('success') {
    <app-content />
  }
  @default {
    <p>Unknown status</p>
  }
}
```

### Complex Cases

```html
@switch (userRole()) {
  @case ('admin') {
    <app-admin-dashboard />
  }
  @case ('manager') {
    <app-manager-dashboard />
  }
  @case ('user') {
    <app-user-dashboard />
  }
  @default {
    <app-guest-view />
  }
}

<!-- Switch on computed value -->
@switch (getDisplayMode()) {
  @case ('grid') {
    <app-grid-view [items]="items()" />
  }
  @case ('list') {
    <app-list-view [items]="items()" />
  }
  @case ('table') {
    <app-table-view [items]="items()" />
  }
}
```

## @defer Block

Lazy load parts of the template for better performance.

### Basic Defer

```html
<!-- Load when browser is idle -->
@defer {
  <app-heavy-component />
}

<!-- With placeholder -->
@defer {
  <app-comments [postId]="postId()" />
} @placeholder {
  <p>Loading comments...</p>
}

<!-- Full syntax -->
@defer {
  <app-analytics-dashboard />
} @loading {
  <app-loading-skeleton />
} @placeholder {
  <div class="placeholder">Analytics will load soon</div>
} @error {
  <p>Failed to load analytics</p>
}
```

### Defer Triggers

```html
<!-- On viewport (lazy load when visible) -->
@defer (on viewport) {
  <app-below-fold-content />
}

<!-- On interaction -->
@defer (on interaction) {
  <app-interactive-widget />
} @placeholder {
  <button>Click to load widget</button>
}

<!-- On hover -->
@defer (on hover) {
  <app-tooltip-content />
} @placeholder {
  <span>Hover for details</span>
}

<!-- On timer -->
@defer (on timer(2s)) {
  <app-promotional-banner />
}

<!-- On idle -->
@defer (on idle) {
  <app-non-critical-content />
}

<!-- Multiple triggers -->
@defer (on viewport; on timer(5s)) {
  <app-content />
}
```

### Prefetch

```html
<!-- Prefetch on idle, load on viewport -->
@defer (on viewport; prefetch on idle) {
  <app-heavy-component />
}

<!-- Prefetch on hover, load on interaction -->
@defer (on interaction; prefetch on hover) {
  <app-modal />
} @placeholder {
  <button>Open Modal</button>
}
```

### Minimum Loading Time

```html
<!-- Show loading for at least 500ms -->
@defer {
  <app-data-table />
} @loading (minimum 500ms) {
  <app-table-skeleton />
} @placeholder (minimum 100ms) {
  <p>Preparing to load...</p>
}

<!-- After delay -->
@defer {
  <app-content />
} @loading (after 200ms; minimum 500ms) {
  <app-spinner />
}
```

## Migration from Legacy Syntax

### *ngIf to @if

```html
<!-- Old -->
<div *ngIf="isVisible">Content</div>
<div *ngIf="user; else noUser">{{ user.name }}</div>
<ng-template #noUser>Not logged in</ng-template>

<!-- New -->
@if (isVisible) {
  <div>Content</div>
}

@if (user()) {
  <div>{{ user().name }}</div>
} @else {
  Not logged in
}
```

### *ngFor to @for

```html
<!-- Old -->
<div *ngFor="let item of items; let i = index; trackBy: trackById">
  {{ i }}: {{ item.name }}
</div>

<!-- New -->
@for (item of items(); track item.id; let i = $index) {
  <div>{{ i }}: {{ item.name }}</div>
}
```

### ngSwitch to @switch

```html
<!-- Old -->
<div [ngSwitch]="status">
  <p *ngSwitchCase="'loading'">Loading...</p>
  <p *ngSwitchCase="'error'">Error!</p>
  <p *ngSwitchDefault>Ready</p>
</div>

<!-- New -->
@switch (status()) {
  @case ('loading') {
    <p>Loading...</p>
  }
  @case ('error') {
    <p>Error!</p>
  }
  @default {
    <p>Ready</p>
  }
}
```

## Best Practices

1. **Always use track**: For `@for` loops to optimize rendering
2. **Use @defer for heavy content**: Improve initial load time
3. **Prefer computed signals**: Over complex template expressions
4. **Use @empty for better UX**: Show feedback for empty lists
5. **Combine conditions**: Use `@else if` chains for related checks
6. **Prefetch strategically**: Balance bandwidth vs. perceived performance
7. **Set minimum loading times**: Prevent loading state flicker
