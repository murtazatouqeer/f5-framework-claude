# WCAG Reference

## Conformance Levels

### Level A (Minimum)

| Criterion | Requirement |
|-----------|-------------|
| 1.1.1 | Non-text content has text alternative |
| 1.3.1 | Info and relationships programmatic |
| 2.1.1 | Keyboard accessible |
| 2.4.1 | Bypass blocks mechanism |
| 4.1.1 | Valid HTML parsing |

### Level AA (Recommended)

| Criterion | Requirement |
|-----------|-------------|
| 1.4.3 | Contrast minimum 4.5:1 |
| 1.4.4 | Text resizable to 200% |
| 2.4.6 | Headings and labels descriptive |
| 2.4.7 | Focus visible |
| 3.3.3 | Error suggestions provided |

### Level AAA (Enhanced)

| Criterion | Requirement |
|-----------|-------------|
| 1.4.6 | Enhanced contrast 7:1 |
| 2.4.9 | Link purpose from text alone |
| 3.1.5 | Reading level assistance |

## POUR Principles

### 1. Perceivable

```html
<!-- Text alternatives -->
<img src="chart.png" alt="Sales increased 25% in Q4 2024">

<!-- Captions for video -->
<video>
  <track kind="captions" src="captions.vtt" srclang="en">
</video>

<!-- Color not sole conveyor -->
<span class="error">
  <span aria-hidden="true">⚠️</span>
  Error: Invalid email
</span>
```

### 2. Operable

```html
<!-- Keyboard accessible -->
<button onclick="submit()">Submit</button>

<!-- Sufficient time -->
<div role="alert">
  Session expires in 5 minutes.
  <button onclick="extendSession()">Extend</button>
</div>
```

### 3. Understandable

```html
<!-- Page language -->
<html lang="en">

<!-- Consistent navigation -->
<nav aria-label="Main">...</nav>

<!-- Error identification -->
<label for="email">Email</label>
<input id="email" aria-describedby="email-error" aria-invalid="true">
<span id="email-error">Please enter a valid email address</span>
```

### 4. Robust

```html
<!-- Valid HTML -->
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Page Title</title>
</head>

<!-- Proper ARIA usage -->
<button aria-expanded="false" aria-controls="menu">Menu</button>
<ul id="menu" hidden>...</ul>
```

## WCAG 2.2 New Criteria

| Criterion | Level | Description |
|-----------|-------|-------------|
| 2.4.11 | AA | Focus not obscured (minimum) |
| 2.5.7 | AA | Dragging movements alternative |
| 2.5.8 | AA | Target size minimum 24×24px |
| 3.2.6 | A | Consistent help location |
| 3.3.7 | A | Redundant entry |
| 3.3.8 | AA | Accessible authentication |

## Color Contrast

### Requirements

| Element | AA Ratio | AAA Ratio |
|---------|----------|-----------|
| Normal text | 4.5:1 | 7:1 |
| Large text (18px+) | 3:1 | 4.5:1 |
| UI components | 3:1 | N/A |

### Testing

```javascript
// Calculate contrast ratio
function getContrastRatio(foreground, background) {
  const getLuminance = (rgb) => {
    const [r, g, b] = rgb.map(c => {
      c = c / 255;
      return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
  };

  const l1 = getLuminance(foreground);
  const l2 = getLuminance(background);
  const ratio = (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
  return ratio.toFixed(2);
}
```

## Accessibility Statement

```markdown
## Accessibility Statement

This website conforms to WCAG 2.1 Level AA.

### Conformance Status
Partially conformant due to:
- Some third-party content
- Legacy PDF documents

### Feedback
Contact accessibility@example.com for issues.

### Last reviewed: January 2024
```

## Quick Compliance Checklist

### Level A

- [ ] All images have alt text
- [ ] All form fields have labels
- [ ] No keyboard traps
- [ ] Page has title
- [ ] Color not only indicator
- [ ] No auto-playing audio

### Level AA

- [ ] Contrast ratio 4.5:1 (text)
- [ ] Contrast ratio 3:1 (large text, UI)
- [ ] Text resizable to 200%
- [ ] Focus visible
- [ ] Multiple navigation methods
- [ ] Error suggestions
