---
name: bundle-optimization
description: JavaScript bundle optimization techniques
category: performance/frontend
applies_to: frontend
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Bundle Optimization

## Overview

Bundle optimization reduces JavaScript file sizes and improves load times.
Smaller bundles mean faster downloads, parsing, and execution.

## Bundle Analysis

### Webpack Bundle Analyzer

```javascript
// webpack.config.js
const BundleAnalyzerPlugin = require('webpack-bundle-analyzer').BundleAnalyzerPlugin;

module.exports = {
  plugins: [
    new BundleAnalyzerPlugin({
      analyzerMode: 'static',
      reportFilename: 'bundle-report.html',
      openAnalyzer: false,
    }),
  ],
};
```

### Vite Bundle Analysis

```bash
# Install rollup-plugin-visualizer
npm install -D rollup-plugin-visualizer
```

```javascript
// vite.config.js
import { visualizer } from 'rollup-plugin-visualizer';

export default defineConfig({
  plugins: [
    visualizer({
      filename: 'bundle-stats.html',
      gzipSize: true,
      brotliSize: true,
    }),
  ],
});
```

### Size Limits

```javascript
// package.json
{
  "size-limit": [
    {
      "path": "dist/index.js",
      "limit": "50 KB"
    },
    {
      "path": "dist/vendor.js",
      "limit": "150 KB"
    }
  ]
}
```

## Code Splitting

### Route-Based Splitting (React)

```typescript
// React.lazy for route-based splitting
import { lazy, Suspense } from 'react';
import { Routes, Route } from 'react-router-dom';

// Lazy load route components
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Settings = lazy(() => import('./pages/Settings'));
const Profile = lazy(() => import('./pages/Profile'));

function App() {
  return (
    <Suspense fallback={<Loading />}>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/profile" element={<Profile />} />
      </Routes>
    </Suspense>
  );
}

// Named chunks for better caching
const Dashboard = lazy(() =>
  import(/* webpackChunkName: "dashboard" */ './pages/Dashboard')
);
```

### Component-Based Splitting

```typescript
// Lazy load heavy components
const HeavyChart = lazy(() => import('./components/HeavyChart'));
const MarkdownEditor = lazy(() => import('./components/MarkdownEditor'));

function ProductPage() {
  const [showChart, setShowChart] = useState(false);

  return (
    <div>
      <ProductDetails />

      <button onClick={() => setShowChart(true)}>Show Analytics</button>

      {showChart && (
        <Suspense fallback={<ChartSkeleton />}>
          <HeavyChart />
        </Suspense>
      )}
    </div>
  );
}
```

### Dynamic Imports

```typescript
// Load module only when needed
async function handleExport() {
  // xlsx library only loaded when exporting
  const XLSX = await import('xlsx');
  const workbook = XLSX.utils.book_new();
  // ... export logic
}

// Conditional import based on feature flag
async function initAnalytics() {
  if (process.env.ENABLE_ANALYTICS) {
    const { initGA } = await import('./analytics');
    initGA();
  }
}
```

## Tree Shaking

### ES Module Imports

```typescript
// ❌ Bad - imports entire library
import _ from 'lodash';
_.get(obj, 'a.b.c');

// ✅ Good - imports only used function
import get from 'lodash/get';
get(obj, 'a.b.c');

// ✅ Better - use lodash-es for tree shaking
import { get } from 'lodash-es';

// ❌ Bad - barrel import
import { Button, Input, Modal } from './components';
// All components bundled even if only Button used

// ✅ Good - direct imports
import Button from './components/Button';
```

### Package.json sideEffects

```json
{
  "name": "my-library",
  "sideEffects": false,
  // Or specify files with side effects
  "sideEffects": [
    "*.css",
    "*.scss",
    "./src/polyfills.js"
  ]
}
```

### Webpack Configuration

```javascript
// webpack.config.js
module.exports = {
  mode: 'production',
  optimization: {
    usedExports: true,    // Mark unused exports
    sideEffects: true,    // Enable side effects detection
    minimize: true,
    minimizer: [
      new TerserPlugin({
        terserOptions: {
          compress: {
            dead_code: true,
            unused: true,
          },
        },
      }),
    ],
  },
};
```

## Vendor Chunking

### Webpack SplitChunks

```javascript
// webpack.config.js
module.exports = {
  optimization: {
    splitChunks: {
      chunks: 'all',
      cacheGroups: {
        // Vendor chunk for node_modules
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendor',
          chunks: 'all',
        },
        // Separate chunk for large libraries
        react: {
          test: /[\\/]node_modules[\\/](react|react-dom)[\\/]/,
          name: 'react',
          chunks: 'all',
          priority: 10,
        },
        // Common code between chunks
        common: {
          minChunks: 2,
          priority: -10,
          reuseExistingChunk: true,
        },
      },
    },
  },
};
```

### Vite Manual Chunks

```javascript
// vite.config.js
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom'],
          'ui-vendor': ['@radix-ui/react-dialog', '@radix-ui/react-dropdown-menu'],
          'chart-vendor': ['chart.js', 'react-chartjs-2'],
        },
      },
    },
  },
});

// Or function-based
manualChunks(id) {
  if (id.includes('node_modules')) {
    if (id.includes('react')) return 'react-vendor';
    if (id.includes('@radix')) return 'ui-vendor';
    return 'vendor';
  }
}
```

## Minification

### Terser Configuration

```javascript
// webpack.config.js
const TerserPlugin = require('terser-webpack-plugin');

module.exports = {
  optimization: {
    minimize: true,
    minimizer: [
      new TerserPlugin({
        terserOptions: {
          parse: { ecma: 2020 },
          compress: {
            ecma: 5,
            comparisons: false,
            inline: 2,
            drop_console: true,
            drop_debugger: true,
            pure_funcs: ['console.log', 'console.info'],
          },
          mangle: {
            safari10: true,
          },
          output: {
            ecma: 5,
            comments: false,
            ascii_only: true,
          },
        },
        parallel: true,
      }),
    ],
  },
};
```

### CSS Minification

```javascript
// webpack.config.js
const CssMinimizerPlugin = require('css-minimizer-webpack-plugin');

module.exports = {
  optimization: {
    minimizer: [
      `...`, // Keep existing minimizers
      new CssMinimizerPlugin({
        minimizerOptions: {
          preset: [
            'default',
            {
              discardComments: { removeAll: true },
            },
          ],
        },
      }),
    ],
  },
};
```

## Module Replacement

### Replace Heavy Libraries

```javascript
// webpack.config.js
const webpack = require('webpack');

module.exports = {
  resolve: {
    alias: {
      // Replace moment with lighter alternative
      moment: 'dayjs',

      // Use preact in production
      ...(process.env.NODE_ENV === 'production' && {
        react: 'preact/compat',
        'react-dom': 'preact/compat',
      }),
    },
  },
  plugins: [
    // Remove moment locales
    new webpack.IgnorePlugin({
      resourceRegExp: /^\.\/locale$/,
      contextRegExp: /moment$/,
    }),
  ],
};
```

### Polyfill Optimization

```javascript
// Only include needed polyfills
// babel.config.js
module.exports = {
  presets: [
    ['@babel/preset-env', {
      useBuiltIns: 'usage',
      corejs: 3,
      targets: {
        browsers: ['>0.25%', 'not dead'],
      },
    }],
  ],
};

// Or use browserslist
// .browserslistrc
> 0.5%
last 2 versions
not dead
not IE 11
```

## External Dependencies

```javascript
// webpack.config.js - externalize for CDN
module.exports = {
  externals: {
    react: 'React',
    'react-dom': 'ReactDOM',
    lodash: '_',
  },
};

// HTML template
<script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
<script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
```

## Performance Budget

```javascript
// webpack.config.js
module.exports = {
  performance: {
    hints: 'error', // 'warning' or false
    maxAssetSize: 250000,       // 250 KB
    maxEntrypointSize: 400000,  // 400 KB
    assetFilter: (assetFilename) => {
      return !/\.(map|txt)$/.test(assetFilename);
    },
  },
};

// Or use bundlesize
// package.json
{
  "bundlesize": [
    {
      "path": "./dist/*.js",
      "maxSize": "100 KB"
    }
  ]
}
```

## Best Practices Summary

```
┌─────────────────────────────────────────────────────────────┐
│                Bundle Optimization Checklist                │
├─────────────────────────────────────────────────────────────┤
│ ☐ Analyze bundle with webpack-bundle-analyzer              │
│ ☐ Implement route-based code splitting                     │
│ ☐ Use dynamic imports for heavy components                 │
│ ☐ Import only needed functions (tree shaking)              │
│ ☐ Configure vendor chunking for better caching             │
│ ☐ Enable minification in production                        │
│ ☐ Replace heavy libraries with lighter alternatives        │
│ ☐ Set performance budgets                                  │
│ ☐ Use modern JavaScript targets when possible              │
│ ☐ Monitor bundle size in CI/CD                             │
└─────────────────────────────────────────────────────────────┘
```
