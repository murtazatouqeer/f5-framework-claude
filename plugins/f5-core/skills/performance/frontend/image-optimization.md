---
name: image-optimization
description: Image optimization techniques for web performance
category: performance/frontend
applies_to: frontend
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Image Optimization

## Overview

Images often account for 50%+ of page weight. Proper optimization can
dramatically improve load times and user experience.

## Image Formats

| Format | Best For | Compression | Transparency | Animation |
|--------|----------|-------------|--------------|-----------|
| JPEG | Photos | Lossy | No | No |
| PNG | Graphics, text | Lossless | Yes | No |
| WebP | All types | Both | Yes | Yes |
| AVIF | All types | Both | Yes | Yes |
| SVG | Icons, logos | Vector | Yes | Yes |

## Responsive Images

### srcset and sizes

```html
<!-- Responsive images with srcset -->
<img
  src="image-800.jpg"
  srcset="
    image-400.jpg 400w,
    image-800.jpg 800w,
    image-1200.jpg 1200w,
    image-1600.jpg 1600w
  "
  sizes="
    (max-width: 400px) 100vw,
    (max-width: 800px) 50vw,
    33vw
  "
  alt="Description"
  loading="lazy"
/>

<!-- High DPI displays -->
<img
  src="logo.png"
  srcset="
    logo.png 1x,
    logo@2x.png 2x,
    logo@3x.png 3x
  "
  alt="Logo"
/>
```

### Picture Element

```html
<!-- Modern format with fallback -->
<picture>
  <source
    srcset="image.avif"
    type="image/avif"
  />
  <source
    srcset="image.webp"
    type="image/webp"
  />
  <img
    src="image.jpg"
    alt="Description"
    loading="lazy"
  />
</picture>

<!-- Art direction - different images for different screens -->
<picture>
  <source
    media="(min-width: 1024px)"
    srcset="hero-desktop.webp"
  />
  <source
    media="(min-width: 768px)"
    srcset="hero-tablet.webp"
  />
  <img
    src="hero-mobile.webp"
    alt="Hero image"
  />
</picture>
```

## React Image Components

### Optimized Image Component

```typescript
interface OptimizedImageProps {
  src: string;
  alt: string;
  width: number;
  height: number;
  priority?: boolean;
  className?: string;
}

function OptimizedImage({
  src,
  alt,
  width,
  height,
  priority = false,
  className,
}: OptimizedImageProps) {
  const [isLoaded, setIsLoaded] = useState(false);
  const [error, setError] = useState(false);

  // Generate srcset for responsive images
  const generateSrcSet = (baseSrc: string) => {
    const widths = [320, 640, 960, 1280, 1920];
    return widths
      .filter((w) => w <= width * 2)
      .map((w) => `${getResizedUrl(baseSrc, w)} ${w}w`)
      .join(', ');
  };

  return (
    <div
      className={`image-wrapper ${className}`}
      style={{ aspectRatio: `${width}/${height}` }}
    >
      {!isLoaded && !error && (
        <div className="skeleton" />
      )}

      {error ? (
        <div className="error-placeholder">
          <ImageIcon />
        </div>
      ) : (
        <picture>
          <source
            srcSet={generateSrcSet(src.replace(/\.\w+$/, '.avif'))}
            type="image/avif"
          />
          <source
            srcSet={generateSrcSet(src.replace(/\.\w+$/, '.webp'))}
            type="image/webp"
          />
          <img
            src={src}
            srcSet={generateSrcSet(src)}
            sizes={`(max-width: ${width}px) 100vw, ${width}px`}
            alt={alt}
            width={width}
            height={height}
            loading={priority ? 'eager' : 'lazy'}
            decoding={priority ? 'sync' : 'async'}
            onLoad={() => setIsLoaded(true)}
            onError={() => setError(true)}
          />
        </picture>
      )}
    </div>
  );
}
```

### Next.js Image

```typescript
import Image from 'next/image';

function ProductImage({ product }: { product: Product }) {
  return (
    <Image
      src={product.imageUrl}
      alt={product.name}
      width={800}
      height={600}
      placeholder="blur"
      blurDataURL={product.blurDataUrl}
      priority={false}
      quality={75}
      sizes="(max-width: 768px) 100vw, 50vw"
    />
  );
}

// next.config.js
module.exports = {
  images: {
    formats: ['image/avif', 'image/webp'],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
    domains: ['images.example.com'],
    minimumCacheTTL: 60 * 60 * 24 * 365, // 1 year
  },
};
```

## Image Processing

### Sharp for Node.js

```typescript
import sharp from 'sharp';
import path from 'path';

async function optimizeImage(
  inputPath: string,
  outputDir: string,
  options: { widths: number[]; quality: number }
): Promise<void> {
  const { widths, quality } = options;
  const filename = path.basename(inputPath, path.extname(inputPath));

  for (const width of widths) {
    // JPEG
    await sharp(inputPath)
      .resize(width, null, { withoutEnlargement: true })
      .jpeg({ quality, progressive: true })
      .toFile(path.join(outputDir, `${filename}-${width}.jpg`));

    // WebP
    await sharp(inputPath)
      .resize(width, null, { withoutEnlargement: true })
      .webp({ quality })
      .toFile(path.join(outputDir, `${filename}-${width}.webp`));

    // AVIF
    await sharp(inputPath)
      .resize(width, null, { withoutEnlargement: true })
      .avif({ quality })
      .toFile(path.join(outputDir, `${filename}-${width}.avif`));
  }
}

// Generate blur placeholder
async function generateBlurDataUrl(imagePath: string): Promise<string> {
  const buffer = await sharp(imagePath)
    .resize(10, 10, { fit: 'inside' })
    .toBuffer();

  return `data:image/jpeg;base64,${buffer.toString('base64')}`;
}
```

### Build-Time Optimization

```javascript
// webpack.config.js
const ImageMinimizerPlugin = require('image-minimizer-webpack-plugin');

module.exports = {
  optimization: {
    minimizer: [
      new ImageMinimizerPlugin({
        minimizer: {
          implementation: ImageMinimizerPlugin.sharpMinify,
          options: {
            encodeOptions: {
              jpeg: { quality: 80, progressive: true },
              webp: { quality: 80 },
              avif: { quality: 65 },
              png: { compressionLevel: 9 },
            },
          },
        },
        generator: [
          {
            preset: 'webp',
            implementation: ImageMinimizerPlugin.sharpGenerate,
            options: {
              encodeOptions: { webp: { quality: 80 } },
            },
          },
        ],
      }),
    ],
  },
};
```

## CDN and Image Services

### Cloudinary

```typescript
// Cloudinary URL transformation
function cloudinaryUrl(
  publicId: string,
  options: {
    width?: number;
    height?: number;
    format?: 'auto' | 'webp' | 'avif';
    quality?: 'auto' | number;
  }
): string {
  const { width, height, format = 'auto', quality = 'auto' } = options;

  const transformations = [
    `f_${format}`,
    `q_${quality}`,
    width && `w_${width}`,
    height && `h_${height}`,
    'c_fill', // Crop mode
  ].filter(Boolean).join(',');

  return `https://res.cloudinary.com/${CLOUD_NAME}/image/upload/${transformations}/${publicId}`;
}

// Usage
<img
  src={cloudinaryUrl('products/shoe', { width: 800, format: 'auto' })}
  alt="Shoe"
/>
```

### Imgix

```typescript
// Imgix URL builder
import ImgixClient from '@imgix/js-core';

const client = new ImgixClient({
  domain: 'example.imgix.net',
  secureURLToken: process.env.IMGIX_TOKEN,
});

function getImgixUrl(path: string, params: object): string {
  return client.buildURL(path, {
    auto: 'format,compress',
    ...params,
  });
}

// Generate srcset
function getImgixSrcSet(path: string, options: {
  widths?: number[];
  aspectRatio?: number;
}): string {
  return client.buildSrcSet(path, {
    auto: 'format,compress',
    fit: 'crop',
    ar: options.aspectRatio,
  }, {
    widths: options.widths || [320, 640, 960, 1280, 1920],
  });
}
```

## SVG Optimization

```typescript
// SVGO configuration
// svgo.config.js
module.exports = {
  plugins: [
    'preset-default',
    'removeDimensions',
    {
      name: 'removeAttrs',
      params: { attrs: '(fill|stroke)' },
    },
    {
      name: 'addAttributesToSVGElement',
      params: { attributes: [{ 'aria-hidden': 'true' }] },
    },
  ],
};

// Inline SVG component
function Icon({ name, className }: { name: string; className?: string }) {
  const IconComponent = icons[name];
  return (
    <IconComponent
      className={className}
      aria-hidden="true"
    />
  );
}

// SVG sprite usage
function SpriteIcon({ id, className }: { id: string; className?: string }) {
  return (
    <svg className={className} aria-hidden="true">
      <use href={`/sprites.svg#${id}`} />
    </svg>
  );
}
```

## Performance Metrics

### Measure Image Impact

```typescript
// Measure image load times
function measureImagePerformance(): void {
  const entries = performance.getEntriesByType('resource')
    .filter((entry) => entry.initiatorType === 'img');

  entries.forEach((entry) => {
    console.log({
      name: entry.name,
      duration: entry.duration,
      transferSize: entry.transferSize,
      decodedBodySize: entry.decodedBodySize,
    });
  });
}

// LCP monitoring
new PerformanceObserver((list) => {
  const entries = list.getEntries();
  const lastEntry = entries[entries.length - 1];

  if (lastEntry.element?.tagName === 'IMG') {
    console.log('LCP is an image:', {
      src: lastEntry.element.src,
      time: lastEntry.startTime,
    });
  }
}).observe({ type: 'largest-contentful-paint', buffered: true });
```

## Best Practices Checklist

```
┌─────────────────────────────────────────────────────────────┐
│                Image Optimization Checklist                  │
├─────────────────────────────────────────────────────────────┤
│ ☐ Use modern formats (WebP, AVIF) with fallbacks           │
│ ☐ Implement responsive images with srcset/sizes            │
│ ☐ Set explicit width/height to prevent layout shift        │
│ ☐ Use lazy loading for below-the-fold images               │
│ ☐ Prioritize LCP image with fetchpriority="high"           │
│ ☐ Compress images appropriately (quality 75-85%)           │
│ ☐ Use blur placeholders for perceived performance          │
│ ☐ Serve images from CDN with optimization                  │
│ ☐ Use SVG for icons and logos                              │
│ ☐ Monitor LCP and image-related metrics                    │
└─────────────────────────────────────────────────────────────┘
```

## Quick Reference

```html
<!-- Optimal image element -->
<img
  src="image.jpg"
  srcset="image-400.webp 400w, image-800.webp 800w, image-1200.webp 1200w"
  sizes="(max-width: 600px) 100vw, (max-width: 1200px) 50vw, 600px"
  alt="Descriptive alt text"
  width="800"
  height="600"
  loading="lazy"
  decoding="async"
  fetchpriority="auto"
/>

<!-- Critical above-fold image -->
<img
  src="hero.jpg"
  alt="Hero"
  width="1920"
  height="1080"
  fetchpriority="high"
  decoding="sync"
/>
```
