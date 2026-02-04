---
name: accessibility-principles
description: Core accessibility principles and best practices
category: accessibility/fundamentals
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# Accessibility Principles

## Core Principles

### 1. Equivalent Experience

Everyone deserves an equivalent experience, not identical.

```html
<!-- Visual users see image, screen reader users hear description -->
<img 
  src="infographic.png" 
  alt="Infographic showing 3 steps: 1. Sign up, 2. Verify email, 3. Start using"
>

<!-- Interactive chart with data table alternative -->
<figure>
  <canvas id="chart" aria-label="Sales data chart"></canvas>
  <details>
    <summary>View data table</summary>
    <table>
      <!-- Accessible data representation -->
    </table>
  </details>
</figure>
```

### 2. Progressive Enhancement

Start with basic functionality, enhance for capable browsers.

```html
<!-- Basic: Works without JavaScript -->
<a href="/search">Search</a>

<!-- Enhanced: Modal search experience -->
<button 
  id="search-trigger"
  aria-haspopup="dialog"
  aria-expanded="false"
>
  Search
</button>
<div id="search-modal" role="dialog" hidden>
  <!-- Enhanced search UI -->
</div>

<script>
  // Progressive enhancement for capable browsers
  if ('dialog' in document.createElement('dialog')) {
    // Use native dialog
  }
</script>
```

### 3. Separation of Concerns

Separate structure (HTML), presentation (CSS), and behavior (JS).

```html
<!-- Structure -->
<nav aria-label="Main navigation">
  <ul>
    <li><a href="/">Home</a></li>
    <li><a href="/about">About</a></li>
  </ul>
</nav>
```

```css
/* Presentation */
nav ul {
  display: flex;
  list-style: none;
}

/* Focus styles */
nav a:focus {
  outline: 2px solid currentColor;
  outline-offset: 2px;
}
```

```javascript
// Behavior
nav.addEventListener('keydown', (e) => {
  if (e.key === 'ArrowRight') {
    // Move to next item
  }
});
```

### 4. Inclusive Design

Design for the full range of human diversity.

```css
/* Respect user preferences */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}

@media (prefers-color-scheme: dark) {
  :root {
    --bg-color: #1a1a1a;
    --text-color: #ffffff;
  }
}

@media (prefers-contrast: more) {
  :root {
    --border-width: 2px;
    --focus-width: 3px;
  }
}
```

## Design Principles

### Clear Visual Hierarchy

```css
/* Heading hierarchy */
h1 { font-size: 2.5rem; }
h2 { font-size: 2rem; }
h3 { font-size: 1.5rem; }
h4 { font-size: 1.25rem; }

/* Visual grouping */
.card {
  border: 1px solid #ccc;
  border-radius: 4px;
  padding: 1rem;
}

/* Whitespace for separation */
section + section {
  margin-top: 2rem;
}
```

### Obvious Interactive Elements

```css
/* Buttons look clickable */
button {
  padding: 0.5rem 1rem;
  background: #0066cc;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

button:hover {
  background: #0052a3;
}

button:focus {
  outline: 2px solid #0066cc;
  outline-offset: 2px;
}

/* Links are underlined or obviously styled */
a {
  color: #0066cc;
  text-decoration: underline;
}

a:hover {
  text-decoration: none;
}
```

### Forgiving Input

```html
<!-- Accept multiple formats -->
<label for="phone">Phone number</label>
<input 
  type="tel" 
  id="phone"
  placeholder="(555) 123-4567"
  aria-describedby="phone-hint"
>
<span id="phone-hint">
  Enter 10 digits, any format
</span>

<script>
// Clean up input on blur
phoneInput.addEventListener('blur', () => {
  const cleaned = phoneInput.value.replace(/\D/g, '');
  if (cleaned.length === 10) {
    phoneInput.value = formatPhone(cleaned);
  }
});
</script>
```

### Helpful Feedback

```html
<!-- Clear success message -->
<div role="alert" class="success">
  <strong>Success!</strong> Your profile has been updated.
</div>

<!-- Specific error message -->
<div role="alert" class="error">
  <strong>Error:</strong> Password must be at least 8 characters 
  and include a number.
</div>

<!-- Progress indication -->
<div role="progressbar" aria-valuenow="75" aria-valuemin="0" aria-valuemax="100">
  <span class="sr-only">75% complete</span>
</div>
```

## Implementation Principles

### Semantic First

Always start with semantic HTML.

```html
<!-- ❌ Div soup -->
<div class="header">
  <div class="nav">
    <div class="nav-item">Home</div>
  </div>
</div>

<!-- ✅ Semantic HTML -->
<header>
  <nav aria-label="Main">
    <ul>
      <li><a href="/">Home</a></li>
    </ul>
  </nav>
</header>
```

### ARIA as Enhancement

Use ARIA only when HTML falls short.

```html
<!-- ❌ Unnecessary ARIA -->
<button role="button">Click me</button>
<nav role="navigation">...</nav>

<!-- ✅ ARIA when needed -->
<div 
  role="tablist" 
  aria-label="Product information"
>
  <button role="tab" aria-selected="true">Details</button>
  <button role="tab" aria-selected="false">Reviews</button>
</div>
```

### Test with Real Users

Include people with disabilities in testing.

```markdown
## User Testing Checklist

### Participants
- [ ] Screen reader users (NVDA, JAWS, VoiceOver)
- [ ] Keyboard-only users
- [ ] Users with low vision
- [ ] Users with cognitive disabilities
- [ ] Users with motor disabilities

### Tasks to Test
- [ ] Complete main user flow
- [ ] Navigate to key pages
- [ ] Fill out forms
- [ ] Handle errors
- [ ] Use search function
```

## Common Patterns

### Mobile Touch Targets

```css
/* Minimum 44x44px touch targets */
button,
a,
input,
select {
  min-width: 44px;
  min-height: 44px;
}

/* Or add padding */
.nav-link {
  padding: 12px 16px;
}
```

### Error Prevention

```html
<!-- Confirm destructive actions -->
<button 
  onclick="confirmDelete()"
  aria-describedby="delete-warning"
>
  Delete Account
</button>
<span id="delete-warning" class="warning">
  This action cannot be undone
</span>

<!-- Form confirmation page -->
<section aria-labelledby="confirm-heading">
  <h2 id="confirm-heading">Confirm Your Order</h2>
  <dl>
    <dt>Item</dt>
    <dd>Widget Pro</dd>
    <dt>Price</dt>
    <dd>$99.99</dd>
  </dl>
  <button type="button" onclick="edit()">Edit Order</button>
  <button type="submit">Confirm Purchase</button>
</section>
```

### Clear Instructions

```html
<form>
  <p id="form-instructions">
    All fields marked with <span aria-hidden="true">*</span>
    <span class="sr-only">asterisk</span> are required.
  </p>
  
  <label for="name">
    Name <span aria-hidden="true">*</span>
  </label>
  <input 
    id="name" 
    required 
    aria-required="true"
    aria-describedby="form-instructions"
  >
</form>
```

## Accessibility Mindset

### Questions to Ask

1. Can all users perceive this content?
2. Can all users operate this control?
3. Can all users understand this information?
4. Does this work with assistive technology?

### Decision Framework

```
Is there a semantic HTML element?
├── Yes → Use it
└── No → Is there an established ARIA pattern?
    ├── Yes → Implement pattern correctly
    └── No → Create accessible custom solution
        └── Test thoroughly with AT users
```
