---
name: text-sizing
description: Responsive and accessible text sizing
category: accessibility/visual
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# Text Sizing

## Overview

Accessible text sizing ensures users can resize text up to 200% without loss of content or functionality. This helps users with low vision read content comfortably.

## WCAG Requirements

| Criterion | Requirement |
|-----------|-------------|
| 1.4.4 Resize Text (AA) | Text resizable to 200% without AT |
| 1.4.10 Reflow (AA) | Content reflows at 320px width |
| 1.4.12 Text Spacing (AA) | Content works with increased spacing |

## Relative Units

### Use Relative Units

```css
/* ✅ Good: Relative units */
html {
  font-size: 100%;  /* Respects user preferences */
}

body {
  font-size: 1rem;     /* 16px at default */
  line-height: 1.5;    /* Relative to font size */
}

h1 { font-size: 2.5rem; }   /* 40px */
h2 { font-size: 2rem; }     /* 32px */
h3 { font-size: 1.5rem; }   /* 24px */
p  { font-size: 1rem; }     /* 16px */
small { font-size: 0.875rem; } /* 14px */

/* ❌ Bad: Fixed units */
body {
  font-size: 16px;  /* Doesn't scale with user preferences */
}
```

### Em vs Rem

```css
/* rem: relative to root (html) font size */
.container {
  padding: 1.5rem;     /* Always 24px at default */
  margin-bottom: 2rem; /* Always 32px at default */
}

/* em: relative to parent font size */
.button {
  font-size: 1rem;
  padding: 0.5em 1em;  /* Scales with button font size */
}

.button-large {
  font-size: 1.25rem;
  padding: 0.5em 1em;  /* Padding scales up too */
}

/* Use rem for layout, em for component spacing */
```

## Fluid Typography

### CSS Clamp

```css
/* Fluid font size between 320px and 1200px viewport */
h1 {
  font-size: clamp(2rem, 5vw + 1rem, 4rem);
  /* min: 32px, preferred: 5vw + 16px, max: 64px */
}

h2 {
  font-size: clamp(1.5rem, 3vw + 0.5rem, 2.5rem);
}

p {
  font-size: clamp(1rem, 1vw + 0.75rem, 1.25rem);
}
```

### Responsive Scale

```css
:root {
  /* Base size */
  --font-size-base: 1rem;
  
  /* Type scale (1.25 ratio) */
  --font-size-sm: 0.8rem;
  --font-size-md: 1rem;
  --font-size-lg: 1.25rem;
  --font-size-xl: 1.563rem;
  --font-size-2xl: 1.953rem;
  --font-size-3xl: 2.441rem;
  --font-size-4xl: 3.052rem;
}

/* Increase scale on larger screens */
@media (min-width: 768px) {
  :root {
    --font-size-base: 1.125rem;
  }
}

h1 { font-size: var(--font-size-4xl); }
h2 { font-size: var(--font-size-3xl); }
h3 { font-size: var(--font-size-2xl); }
h4 { font-size: var(--font-size-xl); }
```

## Line Height and Spacing

```css
/* Optimal line height for readability */
body {
  line-height: 1.5;  /* WCAG minimum for body text */
}

h1, h2, h3 {
  line-height: 1.2;  /* Tighter for headings */
}

/* Paragraph spacing */
p {
  margin-bottom: 1em;  /* Scales with font size */
}

/* Letter spacing */
.small-caps {
  letter-spacing: 0.1em;  /* Improves readability */
}

/* Word spacing */
.justified-text {
  word-spacing: 0.05em;
  text-align: justify;
}
```

## Text Spacing Override Support

```css
/* WCAG 1.4.12: Support custom text spacing */
/* Users may inject styles like: */
/* line-height: 1.5 !important; */
/* letter-spacing: 0.12em !important; */
/* word-spacing: 0.16em !important; */
/* paragraph margin-bottom: 2em !important; */

/* Ensure content still works */
.container {
  /* Use min-height, not height */
  min-height: 200px;  /* ✅ */
  /* height: 200px;    ❌ Content may overflow */
  
  /* Allow overflow */
  overflow: visible;  /* ✅ */
  /* overflow: hidden;  ❌ May clip text */
}

/* Test with bookmarklet */
/* javascript:(function(){var style=document.createElement('style');style.innerHTML='*{line-height:1.5!important;letter-spacing:0.12em!important;word-spacing:0.16em!important}p{margin-bottom:2em!important}';document.head.appendChild(style);})(); */
```

## Zoom Support

### 200% Zoom

```css
/* Content must work at 200% zoom */

/* ❌ Fixed width containers */
.container {
  width: 1200px;  /* May require horizontal scroll */
}

/* ✅ Max-width with flexibility */
.container {
  max-width: 75rem;
  width: 100%;
  margin: 0 auto;
}

/* ❌ Fixed height with overflow hidden */
.card {
  height: 300px;
  overflow: hidden;
}

/* ✅ Min-height and visible overflow */
.card {
  min-height: 300px;
  overflow: visible;
}
```

### 320px Viewport (Reflow)

```css
/* Content reflows at 320px (400% zoom on 1280px) */

/* Single column on small screens */
@media (max-width: 320px) {
  .grid {
    grid-template-columns: 1fr;
  }
  
  .sidebar {
    display: none;  /* Or move to accordion */
  }
}

/* Prevent horizontal scroll */
* {
  max-width: 100%;
}

img, video, iframe {
  max-width: 100%;
  height: auto;
}
```

## Minimum Text Size

```css
/* Never go below readable sizes */
body {
  font-size: max(1rem, 16px);  /* At least 16px */
}

small, .caption {
  font-size: max(0.75rem, 12px);  /* At least 12px */
}

/* Interactive elements need larger text */
button, input, select {
  font-size: max(1rem, 16px);  /* Prevents iOS zoom */
}

/* Labels and form text */
label {
  font-size: 1rem;
}
```

## Touch Target Size

```css
/* WCAG 2.5.5: Target Size */
button, 
a, 
input[type="checkbox"],
input[type="radio"] {
  min-width: 44px;
  min-height: 44px;
}

/* For inline links, add padding */
a {
  padding: 4px;
  margin: -4px;
}

/* Touch-friendly spacing */
nav ul {
  display: flex;
  gap: 8px;
}

nav a {
  padding: 12px 16px;
  display: inline-block;
}
```

## Testing Text Sizing

### Browser Zoom Test

```markdown
1. Set browser zoom to 200%
2. Check all content is visible
3. No horizontal scrolling required
4. No text overlaps or gets cut off
5. All functionality works
```

### Text-Only Zoom

```markdown
1. Firefox: View → Zoom → Zoom Text Only
2. Increase to 200%
3. Check content adapts properly
```

### Text Spacing Test

```javascript
// Bookmarklet to test WCAG 1.4.12
javascript:(function(){
  var style = document.createElement('style');
  style.innerHTML = `
    * {
      line-height: 1.5 !important;
      letter-spacing: 0.12em !important;
      word-spacing: 0.16em !important;
    }
    p {
      margin-bottom: 2em !important;
    }
  `;
  document.head.appendChild(style);
})();
```

## Common Issues

### Issue: Text Truncation

```css
/* ❌ Text gets cut off */
.card-title {
  height: 48px;
  overflow: hidden;
}

/* ✅ Allow expansion */
.card-title {
  min-height: 48px;
  overflow: visible;
}

/* Or use line-clamp with fallback */
.card-title {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
```

### Issue: Overlapping Text

```css
/* ❌ Fixed positioning causes overlap */
.label {
  position: absolute;
  top: 10px;
}

/* ✅ Relative positioning */
.label {
  position: relative;
  margin-bottom: 8px;
}
```

### Issue: Input Zoom on iOS

```css
/* ❌ Small inputs trigger zoom on iOS */
input {
  font-size: 14px;
}

/* ✅ 16px prevents auto-zoom */
input {
  font-size: 16px;  /* Or 1rem */
}
```

## Summary

| Principle | Implementation |
|-----------|----------------|
| Use relative units | rem, em instead of px |
| Support 200% zoom | Max-width, min-height |
| Support reflow at 320px | Responsive design |
| Support text spacing | No fixed heights |
| Minimum readable size | 16px for body, 12px minimum |
| Touch-friendly targets | 44x44px minimum |
