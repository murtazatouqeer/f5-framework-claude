# Angular Bundle Optimization

## Overview

Bundle optimization reduces application size and improves load times. Angular provides several built-in features and strategies for optimizing bundles.

## Build Optimization

### Production Build

```bash
# Optimized production build
ng build --configuration=production

# Equivalent to
ng build --optimization --output-hashing=all --source-map=false
```

### Angular.json Configuration

```json
{
  "configurations": {
    "production": {
      "budgets": [
        {
          "type": "initial",
          "maximumWarning": "500kb",
          "maximumError": "1mb"
        },
        {
          "type": "anyComponentStyle",
          "maximumWarning": "2kb",
          "maximumError": "4kb"
        }
      ],
      "outputHashing": "all",
      "optimization": {
        "scripts": true,
        "styles": {
          "minify": true,
          "inlineCritical": true
        },
        "fonts": {
          "inline": true
        }
      },
      "sourceMap": false,
      "namedChunks": false
    }
  }
}
```

## Code Splitting

### Route-Based Splitting

```typescript
// app.routes.ts
export const routes: Routes = [
  {
    path: '',
    loadComponent: () => import('./features/home/home.component')
      .then(m => m.HomeComponent),
  },
  {
    path: 'products',
    loadChildren: () => import('./features/products/products.routes')
      .then(m => m.PRODUCTS_ROUTES),
  },
  {
    path: 'admin',
    loadChildren: () => import('./features/admin/admin.routes')
      .then(m => m.ADMIN_ROUTES),
  },
];
```

### Component-Level Splitting

```typescript
@Component({
  template: `
    @defer (on viewport) {
      <app-heavy-component />
    } @placeholder {
      <div class="placeholder">Loading...</div>
    }
  `,
})
export class DeferredComponent {}
```

### Named Chunks

```typescript
// Named chunks for debugging
{
  path: 'admin',
  loadChildren: () => import(
    /* webpackChunkName: "admin" */
    './features/admin/admin.routes'
  ).then(m => m.ADMIN_ROUTES),
}
```

## Tree Shaking

### Export Optimization

```typescript
// Good: Named exports allow tree shaking
export { UserService } from './user.service';
export { AuthService } from './auth.service';

// Avoid: Barrel files can prevent tree shaking
export * from './user.service';
export * from './auth.service';
```

### providedIn: 'root'

```typescript
// Automatically tree-shaken if not used
@Injectable({ providedIn: 'root' })
export class OptionalService {
  // Only included in bundle if injected somewhere
}
```

### Side-Effect Free Modules

```json
// package.json
{
  "sideEffects": [
    "*.css",
    "*.scss"
  ]
}
```

## Dependency Optimization

### Analyze Bundle

```bash
# Install bundle analyzer
npm install -D webpack-bundle-analyzer source-map-explorer

# Build with stats
ng build --stats-json

# Analyze
npx webpack-bundle-analyzer dist/my-app/stats.json

# Or use source-map-explorer
ng build --source-map
npx source-map-explorer dist/my-app/main.*.js
```

### Import Optimization

```typescript
// Bad: Imports entire library
import { cloneDeep, debounce, throttle } from 'lodash';

// Good: Import specific functions
import cloneDeep from 'lodash/cloneDeep';
import debounce from 'lodash/debounce';

// Better: Use native alternatives when possible
const clone = structuredClone(obj);
```

### Date Library Optimization

```typescript
// Avoid: moment.js is large
import moment from 'moment'; // ~70KB

// Better: date-fns with tree shaking
import { format, parseISO } from 'date-fns'; // ~2KB per function

// Best: Native Intl API
const formatted = new Intl.DateTimeFormat('en-US').format(date);
```

### RxJS Import Optimization

```typescript
// Good: Import from specific paths
import { map, filter } from 'rxjs/operators';
import { Observable, Subject } from 'rxjs';

// Modern RxJS (7+) supports direct imports
import { map, filter, Observable, Subject } from 'rxjs';
```

## Preloading Strategies

### Selective Preloading

```typescript
// core/preloading/selective.strategy.ts
@Injectable({ providedIn: 'root' })
export class SelectivePreloadingStrategy implements PreloadingStrategy {
  preload(route: Route, load: () => Observable<any>): Observable<any> {
    if (route.data?.['preload']) {
      return load();
    }
    return of(null);
  }
}

// app.config.ts
provideRouter(
  routes,
  withPreloading(SelectivePreloadingStrategy),
)

// Route configuration
{
  path: 'products',
  loadChildren: () => import('./products/products.routes'),
  data: { preload: true },
}
```

### Network-Aware Preloading

```typescript
@Injectable({ providedIn: 'root' })
export class NetworkAwarePreloadingStrategy implements PreloadingStrategy {
  preload(route: Route, load: () => Observable<any>): Observable<any> {
    const connection = (navigator as any).connection;

    // Don't preload on slow connections
    if (connection?.saveData ||
        connection?.effectiveType === '2g' ||
        connection?.effectiveType === 'slow-2g') {
      return of(null);
    }

    if (route.data?.['preload']) {
      return load();
    }

    return of(null);
  }
}
```

## Deferred Loading (Angular 17+)

### @defer Block

```typescript
@Component({
  template: `
    <!-- Load when visible -->
    @defer (on viewport) {
      <app-heavy-chart [data]="chartData" />
    } @loading (minimum 200ms) {
      <app-skeleton-loader />
    } @placeholder {
      <div class="chart-placeholder"></div>
    } @error {
      <div class="error">Failed to load chart</div>
    }
  `,
})
export class DashboardComponent {
  chartData = signal<ChartData | null>(null);
}
```

### Defer Triggers

```typescript
@Component({
  template: `
    <!-- On viewport entry -->
    @defer (on viewport) {
      <app-component />
    }

    <!-- On user interaction -->
    @defer (on interaction) {
      <app-component />
    }

    <!-- On hover -->
    @defer (on hover) {
      <app-component />
    }

    <!-- On idle -->
    @defer (on idle) {
      <app-component />
    }

    <!-- On timer -->
    @defer (on timer(2000ms)) {
      <app-component />
    }

    <!-- When condition is true -->
    @defer (when isReady()) {
      <app-component />
    }

    <!-- Prefetch separately from render -->
    @defer (on viewport; prefetch on idle) {
      <app-component />
    }
  `,
})
export class DeferExamplesComponent {
  isReady = signal(false);
}
```

## Image Optimization

### NgOptimizedImage

```typescript
import { NgOptimizedImage } from '@angular/common';

@Component({
  imports: [NgOptimizedImage],
  template: `
    <!-- Optimized image with automatic srcset -->
    <img
      ngSrc="assets/hero.jpg"
      width="800"
      height="400"
      priority
    >

    <!-- Fill mode for responsive images -->
    <div class="image-container">
      <img ngSrc="assets/background.jpg" fill>
    </div>

    <!-- Lazy loading (default) -->
    <img ngSrc="assets/product.jpg" width="300" height="200">
  `,
  styles: `
    .image-container {
      position: relative;
      width: 100%;
      height: 400px;
    }
  `,
})
export class ImageComponent {}
```

### Image Loader Configuration

```typescript
// app.config.ts
import { provideImgixLoader, provideCloudinaryLoader } from '@angular/common';

export const appConfig: ApplicationConfig = {
  providers: [
    // Use Imgix
    provideImgixLoader('https://my-site.imgix.net/'),

    // Or Cloudinary
    provideCloudinaryLoader('https://res.cloudinary.com/my-cloud/'),
  ],
};

// Usage
@Component({
  template: `<img ngSrc="images/hero.jpg" width="800" height="400">`,
})
export class HeroComponent {}
// Generates: https://my-site.imgix.net/images/hero.jpg?auto=format&w=800
```

## Font Optimization

### Inline Critical Fonts

```json
// angular.json
{
  "optimization": {
    "fonts": {
      "inline": true
    }
  }
}
```

### Preload Fonts

```html
<!-- index.html -->
<link rel="preload" href="assets/fonts/roboto.woff2" as="font" type="font/woff2" crossorigin>
```

### Font Display

```css
@font-face {
  font-family: 'Roboto';
  src: url('/assets/fonts/roboto.woff2') format('woff2');
  font-display: swap; /* Show fallback immediately, swap when loaded */
}
```

## Service Worker

### Enable PWA

```bash
ng add @angular/pwa
```

### ngsw-config.json

```json
{
  "index": "/index.html",
  "assetGroups": [
    {
      "name": "app",
      "installMode": "prefetch",
      "resources": {
        "files": [
          "/favicon.ico",
          "/index.html",
          "/manifest.webmanifest",
          "/*.css",
          "/*.js"
        ]
      }
    },
    {
      "name": "assets",
      "installMode": "lazy",
      "updateMode": "prefetch",
      "resources": {
        "files": [
          "/assets/**",
          "/*.(png|jpg|jpeg|svg|gif)"
        ]
      }
    }
  ],
  "dataGroups": [
    {
      "name": "api",
      "urls": ["/api/**"],
      "cacheConfig": {
        "maxSize": 100,
        "maxAge": "1h",
        "timeout": "10s",
        "strategy": "freshness"
      }
    }
  ]
}
```

## Budget Configuration

```json
// angular.json
{
  "budgets": [
    {
      "type": "initial",
      "maximumWarning": "500kb",
      "maximumError": "1mb"
    },
    {
      "type": "anyComponentStyle",
      "maximumWarning": "2kb",
      "maximumError": "4kb"
    },
    {
      "type": "anyScript",
      "maximumWarning": "100kb",
      "maximumError": "200kb"
    },
    {
      "type": "any",
      "maximumWarning": "200kb",
      "maximumError": "400kb"
    }
  ]
}
```

## Best Practices

1. **Use lazy loading**: Split code by routes
2. **Analyze bundles regularly**: Catch size regressions
3. **Import selectively**: Avoid importing entire libraries
4. **Use @defer**: For below-the-fold content
5. **Optimize images**: Use NgOptimizedImage
6. **Enable service worker**: For caching and offline support
7. **Set budgets**: Enforce size limits in CI
8. **Use production builds**: Never deploy development builds
