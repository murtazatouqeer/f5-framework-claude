---
name: color-contrast
description: Color contrast requirements and implementation
category: accessibility/visual
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# Color Contrast

## Overview

Sufficient color contrast ensures text and UI elements are readable for users with low vision, color blindness, or in challenging viewing conditions.

## WCAG Requirements

| Content Type | Level AA | Level AAA |
|--------------|----------|-----------|
| Normal text | 4.5:1 | 7:1 |
| Large text (18pt+ or 14pt bold) | 3:1 | 4.5:1 |
| UI components & graphical objects | 3:1 | - |
| Focus indicators | 3:1 | - |

## Calculating Contrast Ratio

```javascript
// Calculate relative luminance
function getLuminance(r, g, b) {
  const [rs, gs, bs] = [r, g, b].map(c => {
    c = c / 255;
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
}

// Calculate contrast ratio
function getContrastRatio(color1, color2) {
  const l1 = getLuminance(...color1);
  const l2 = getLuminance(...color2);
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);
  return (lighter + 0.05) / (darker + 0.05);
}

// Example
const white = [255, 255, 255];
const darkGray = [51, 51, 51]; // #333333
const ratio = getContrastRatio(white, darkGray);
console.log(ratio); // 12.63:1 ✅
```

## Color Combinations

### Safe Combinations

```css
/* High contrast - all pass */
.text-primary {
  color: #1a1a1a;        /* On white: 16.1:1 */
  background: #ffffff;
}

.text-on-dark {
  color: #ffffff;        /* On dark: 16.1:1 */
  background: #1a1a1a;
}

/* Brand colors with sufficient contrast */
.brand-blue {
  color: #0052cc;        /* On white: 7.2:1 */
  background: #ffffff;
}

.brand-button {
  color: #ffffff;
  background: #0052cc;   /* White on blue: 7.2:1 */
}
```

### Problematic Combinations

```css
/* ❌ Insufficient contrast */
.low-contrast {
  color: #767676;        /* On white: 4.5:1 - minimum for normal text */
  background: #ffffff;
}

.very-low {
  color: #999999;        /* On white: 2.9:1 - fails AA */
  background: #ffffff;
}

/* ❌ Light on light */
.light-on-light {
  color: #cccccc;
  background: #f0f0f0;   /* 1.5:1 - fails */
}
```

## Implementation

### CSS Custom Properties

```css
:root {
  /* Primary palette */
  --color-text: #1a1a1a;
  --color-text-secondary: #595959;  /* 7:1 on white */
  --color-text-muted: #767676;      /* 4.5:1 on white - minimum */
  
  /* Backgrounds */
  --color-bg: #ffffff;
  --color-bg-secondary: #f5f5f5;
  
  /* Interactive */
  --color-link: #0066cc;            /* 5.9:1 on white */
  --color-link-hover: #004499;      /* 9.8:1 on white */
  
  /* Status */
  --color-error: #c41e3a;           /* 5.5:1 on white */
  --color-success: #1e7e34;         /* 5.9:1 on white */
  --color-warning: #856404;         /* 5.7:1 on white */
}

body {
  color: var(--color-text);
  background: var(--color-bg);
}
```

### Dark Mode

```css
@media (prefers-color-scheme: dark) {
  :root {
    --color-text: #f0f0f0;
    --color-text-secondary: #b3b3b3;
    --color-text-muted: #8c8c8c;
    
    --color-bg: #1a1a1a;
    --color-bg-secondary: #2d2d2d;
    
    --color-link: #6eb5ff;
    --color-link-hover: #a6d1ff;
    
    --color-error: #ff6b6b;
    --color-success: #51cf66;
    --color-warning: #ffd43b;
  }
}
```

### High Contrast Mode

```css
@media (prefers-contrast: more) {
  :root {
    --color-text: #000000;
    --color-text-secondary: #000000;
    --color-text-muted: #333333;
    
    --color-bg: #ffffff;
    
    --color-link: #0000ee;
    
    --border-width: 2px;
  }
  
  /* Ensure all borders are visible */
  button, input, select {
    border: 2px solid #000;
  }
  
  /* Stronger focus indicators */
  :focus {
    outline: 3px solid #000;
    outline-offset: 2px;
  }
}

/* Windows High Contrast Mode */
@media (forced-colors: active) {
  /* Let system colors take over */
  button {
    border: 2px solid ButtonText;
  }
  
  /* Ensure custom controls are visible */
  .custom-checkbox {
    forced-color-adjust: none;
    border: 2px solid CanvasText;
  }
}
```

## Color + Additional Indicators

```html
<!-- ❌ Color only for status -->
<span style="color: red;">Error</span>

<!-- ✅ Color + icon + text -->
<span class="error">
  <svg aria-hidden="true"><!-- error icon --></svg>
  Error: Invalid email address
</span>

<!-- ❌ Color only for links -->
<a href="/about" style="color: blue; text-decoration: none;">About</a>

<!-- ✅ Color + underline -->
<a href="/about" style="color: blue; text-decoration: underline;">About</a>

<!-- ❌ Color only for required fields -->
<label style="color: red;">Email</label>

<!-- ✅ Color + asterisk + text -->
<label>
  Email <span style="color: red;" aria-hidden="true">*</span>
  <span class="visually-hidden">(required)</span>
</label>
```

### Form Validation

```css
/* Error state with multiple indicators */
.input-error {
  border: 2px solid #c41e3a;    /* Red border */
  background: #fff5f5;          /* Light red background */
  padding-left: 36px;           /* Space for icon */
}

.input-error::before {
  content: "⚠";                 /* Warning icon */
  position: absolute;
  left: 12px;
  color: #c41e3a;
}

/* Error message */
.error-message {
  color: #c41e3a;
  display: flex;
  align-items: center;
  gap: 8px;
}

.error-message::before {
  content: "";
  width: 16px;
  height: 16px;
  background: url('error-icon.svg');
}
```

## Testing Contrast

### Browser DevTools

```javascript
// Chrome DevTools - Accessibility pane
// 1. Inspect element
// 2. Check "Accessibility" tab
// 3. View contrast ratio

// Firefox DevTools - Accessibility Inspector
// 1. Open Accessibility panel
// 2. Enable "Check for issues"
// 3. Filter by "Contrast"
```

### Automated Tools

```javascript
// Using axe-core
import { run } from 'axe-core';

run(document, {
  rules: ['color-contrast']
}).then(results => {
  console.log('Contrast violations:', results.violations);
});
```

### Manual Testing

```javascript
// Quick contrast check
function checkContrast(foreground, background) {
  // Parse colors
  const fg = parseColor(foreground);
  const bg = parseColor(background);
  
  // Calculate ratio
  const ratio = getContrastRatio(fg, bg);
  
  // Check against WCAG
  return {
    ratio: ratio.toFixed(2),
    passesAA_normal: ratio >= 4.5,
    passesAA_large: ratio >= 3,
    passesAAA_normal: ratio >= 7,
    passesAAA_large: ratio >= 4.5
  };
}
```

## Tools and Resources

| Tool | Purpose |
|------|---------|
| [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/) | Check specific colors |
| [Colour Contrast Analyser](https://www.tpgi.com/color-contrast-checker/) | Desktop app with eyedropper |
| [Accessible Colors](https://accessible-colors.com/) | Find accessible alternatives |
| [Contrast Grid](https://contrast-grid.eightshapes.com/) | Test palette combinations |
| [Stark](https://www.getstark.co/) | Figma/Sketch plugin |

## Common Issues

### Issue: Gray Text Too Light

```css
/* ❌ Fails contrast */
.muted-text {
  color: #999999;  /* 2.9:1 on white */
}

/* ✅ Passes AA */
.muted-text {
  color: #767676;  /* 4.5:1 on white */
}
```

### Issue: Placeholder Text

```css
/* ❌ Default placeholder is too light */
::placeholder {
  color: #a0a0a0;  /* Often fails */
}

/* ✅ Darker placeholder */
::placeholder {
  color: #767676;
  opacity: 1;  /* Override browser defaults */
}
```

### Issue: Disabled States

```css
/* Disabled states have reduced contrast requirement */
/* But should still be somewhat perceivable */

/* ❌ Too light */
button:disabled {
  color: #cccccc;
  background: #f0f0f0;
}

/* ✅ Still perceivable */
button:disabled {
  color: #767676;
  background: #e0e0e0;
  opacity: 0.7;
}
```

## Summary

| Text Type | Minimum Ratio | Example Colors |
|-----------|---------------|----------------|
| Normal text | 4.5:1 | #767676 on white |
| Large text | 3:1 | #949494 on white |
| UI components | 3:1 | Borders, icons |
| Focus indicators | 3:1 | Outline colors |
| Disabled (advisory) | - | Reduced requirements |
