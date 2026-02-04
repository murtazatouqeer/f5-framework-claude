---
name: headings
description: Proper heading structure for document accessibility
category: accessibility/html
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# Headings

## Overview

Headings create an outline of your page content. Screen reader users often navigate by headings, making proper structure essential for accessibility.

## Heading Levels

```html
<h1>Page Title (Level 1)</h1>
  <h2>Section (Level 2)</h2>
    <h3>Subsection (Level 3)</h3>
      <h4>Sub-subsection (Level 4)</h4>
        <h5>Minor section (Level 5)</h5>
          <h6>Smallest heading (Level 6)</h6>
```

## Heading Rules

### 1. One H1 Per Page

```html
<!-- ✅ Good: Single h1 -->
<body>
  <header>
    <nav>...</nav>
  </header>
  <main>
    <h1>Product Details</h1>
    <h2>Features</h2>
    <h2>Specifications</h2>
  </main>
</body>

<!-- ❌ Bad: Multiple h1s -->
<body>
  <header>
    <h1>Site Name</h1>
  </header>
  <main>
    <h1>Page Title</h1>
  </main>
</body>
```

### 2. Don't Skip Levels

```html
<!-- ✅ Good: Sequential levels -->
<h1>Page Title</h1>
  <h2>Section 1</h2>
    <h3>Subsection 1.1</h3>
    <h3>Subsection 1.2</h3>
  <h2>Section 2</h2>
    <h3>Subsection 2.1</h3>

<!-- ❌ Bad: Skipped h2 -->
<h1>Page Title</h1>
  <h3>Subsection</h3>  <!-- Missing h2 -->
  <h4>Sub-subsection</h4>
```

### 3. Heading Hierarchy Reflects Content

```html
<!-- Document outline should make sense -->
<h1>Complete Guide to Web Accessibility</h1>
  <h2>Introduction</h2>
  <h2>Understanding WCAG</h2>
    <h3>WCAG Principles</h3>
      <h4>Perceivable</h4>
      <h4>Operable</h4>
      <h4>Understandable</h4>
      <h4>Robust</h4>
    <h3>Conformance Levels</h3>
  <h2>Implementation Guide</h2>
    <h3>HTML Best Practices</h3>
    <h3>CSS Considerations</h3>
    <h3>JavaScript Accessibility</h3>
  <h2>Testing</h2>
  <h2>Conclusion</h2>
```

## Common Patterns

### Page with Sidebar

```html
<body>
  <header>
    <nav aria-label="Main">...</nav>
  </header>
  
  <main>
    <h1>Article Title</h1>
    
    <article>
      <h2>Introduction</h2>
      <p>...</p>
      
      <h2>Main Points</h2>
      <h3>Point One</h3>
      <p>...</p>
      <h3>Point Two</h3>
      <p>...</p>
      
      <h2>Conclusion</h2>
      <p>...</p>
    </article>
  </main>
  
  <aside aria-labelledby="related-heading">
    <h2 id="related-heading">Related Articles</h2>
    <ul>...</ul>
  </aside>
</body>
```

### Card Layout

```html
<!-- Card headings continue hierarchy -->
<main>
  <h1>Our Products</h1>
  
  <section aria-labelledby="featured">
    <h2 id="featured">Featured Products</h2>
    
    <article class="card">
      <h3>Product A</h3>
      <p>Description...</p>
    </article>
    
    <article class="card">
      <h3>Product B</h3>
      <p>Description...</p>
    </article>
  </section>
  
  <section aria-labelledby="categories">
    <h2 id="categories">Categories</h2>
    
    <article class="card">
      <h3>Electronics</h3>
      <p>...</p>
    </article>
    
    <article class="card">
      <h3>Clothing</h3>
      <p>...</p>
    </article>
  </section>
</main>
```

### Modal/Dialog

```html
<!-- Modal headings are independent -->
<main>
  <h1>Dashboard</h1>
  <h2>Overview</h2>
  <button aria-haspopup="dialog">Edit Settings</button>
</main>

<!-- Modal starts fresh hierarchy -->
<dialog aria-labelledby="dialog-title">
  <h2 id="dialog-title">Edit Settings</h2>
  <form>
    <h3>General</h3>
    <fieldset>...</fieldset>
    
    <h3>Notifications</h3>
    <fieldset>...</fieldset>
  </form>
</dialog>
```

## Visually Hidden Headings

```html
<!-- For screen reader navigation without visual heading -->
<section aria-labelledby="nav-heading">
  <h2 id="nav-heading" class="visually-hidden">Main Navigation</h2>
  <nav>
    <ul>...</ul>
  </nav>
</section>

<!-- CSS for visually hidden -->
<style>
.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
</style>
```

## Styling Headings

```css
/* Don't use heading tags for styling */
/* Use CSS classes instead */

/* ❌ Bad: Using h4 because it's smaller */
/* Just wanted smaller text, not a heading */

/* ✅ Good: Use appropriate heading with styling */
h2 {
  font-size: 1.5rem;
  font-weight: 600;
}

h2.section-title {
  font-size: 2rem;
  color: #333;
}

h2.card-title {
  font-size: 1.25rem;
  color: #666;
}

/* Visual-only heading styles */
.heading-style-large {
  font-size: 2rem;
  font-weight: bold;
}

.heading-style-small {
  font-size: 1rem;
  font-weight: 600;
}
```

## Anti-Patterns

```html
<!-- ❌ Using headings for styling only -->
<h4>This text should just be bold</h4>
<strong>Use strong or CSS instead</strong>

<!-- ❌ Empty headings -->
<h2></h2>

<!-- ❌ Image-only heading without alt -->
<h1><img src="logo.png"></h1>
<!-- ✅ Fix -->
<h1><img src="logo.png" alt="Company Name"></h1>

<!-- ❌ Non-descriptive headings -->
<h2>Click Here</h2>
<h2>More Info</h2>
<!-- ✅ Fix -->
<h2>Product Features</h2>
<h2>Contact Information</h2>

<!-- ❌ Divs styled as headings -->
<div class="heading">Section Title</div>
<!-- ✅ Fix -->
<h2 class="heading">Section Title</h2>
```

## Dynamic Headings

```html
<!-- React component with proper heading level -->
<script>
function Section({ level, title, children }) {
  const Heading = `h${level}`;
  return (
    <section>
      <Heading>{title}</Heading>
      {children}
    </section>
  );
}

// Usage
<Section level={2} title="Features">
  <Section level={3} title="Speed">
    <p>Fast loading times...</p>
  </Section>
  <Section level={3} title="Security">
    <p>Built-in protection...</p>
  </Section>
</Section>
</script>
```

## Testing Headings

### Browser Tools

```javascript
// List all headings in console
document.querySelectorAll('h1, h2, h3, h4, h5, h6').forEach(h => {
  console.log(`${h.tagName}: ${h.textContent.trim()}`);
});

// Check heading hierarchy
function checkHeadingHierarchy() {
  const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
  let prevLevel = 0;
  const issues = [];
  
  headings.forEach(h => {
    const level = parseInt(h.tagName[1]);
    
    if (level - prevLevel > 1) {
      issues.push({
        element: h,
        issue: `Skipped from h${prevLevel} to h${level}`,
        text: h.textContent.trim()
      });
    }
    
    prevLevel = level;
  });
  
  return issues;
}
```

### Heading Outline

```
h1: Complete Guide to Accessibility
├── h2: Introduction
├── h2: Core Concepts
│   ├── h3: Perceivable
│   ├── h3: Operable
│   └── h3: Understandable
├── h2: Implementation
│   ├── h3: HTML Techniques
│   │   ├── h4: Semantic Elements
│   │   └── h4: ARIA Labels
│   └── h3: CSS Techniques
└── h2: Conclusion
```

## Screen Reader Navigation

| Screen Reader | Heading Navigation |
|---------------|-------------------|
| NVDA | H (next heading), Shift+H (previous), 1-6 (specific level) |
| JAWS | H (next heading), Shift+H (previous), 1-6 (specific level) |
| VoiceOver | VO+Command+H (next), Web Rotor → Headings |
| TalkBack | Swipe up/down, select "Headings" |

## Summary Checklist

- [ ] Single h1 per page
- [ ] No skipped heading levels
- [ ] Headings describe content accurately
- [ ] Heading hierarchy creates logical outline
- [ ] No empty headings
- [ ] Headings used for structure, not styling
- [ ] Visually hidden headings where needed
- [ ] Dynamic components maintain hierarchy
