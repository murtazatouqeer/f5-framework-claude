---
name: landmarks
description: ARIA landmarks and HTML5 sectioning elements
category: accessibility/html
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# Landmarks

## Overview

Landmarks are regions of a page that assistive technologies can use for navigation. They allow screen reader users to jump directly to important sections.

## Landmark Regions

| HTML5 Element | ARIA Role | Purpose |
|---------------|-----------|---------|
| `<header>` | `banner` | Site header (top-level only) |
| `<nav>` | `navigation` | Navigation links |
| `<main>` | `main` | Primary content |
| `<aside>` | `complementary` | Supporting content |
| `<footer>` | `contentinfo` | Site footer (top-level only) |
| `<section>` | `region` | Generic section (with label) |
| `<form>` | `form` | Form (with label) |
| - | `search` | Search functionality |

## Basic Page Structure

```html
<body>
  <!-- Banner landmark (implicit) -->
  <header>
    <a href="/" class="logo">Site Name</a>
    
    <!-- Navigation landmark -->
    <nav aria-label="Main">
      <ul>
        <li><a href="/">Home</a></li>
        <li><a href="/products">Products</a></li>
        <li><a href="/about">About</a></li>
      </ul>
    </nav>
    
    <!-- Search landmark -->
    <form role="search" aria-label="Site search">
      <label for="search" class="sr-only">Search</label>
      <input type="search" id="search" name="q">
      <button type="submit">Search</button>
    </form>
  </header>
  
  <!-- Main landmark -->
  <main id="main-content">
    <h1>Page Title</h1>
    <p>Main content...</p>
  </main>
  
  <!-- Complementary landmark -->
  <aside aria-label="Related content">
    <h2>Related Articles</h2>
    <ul>...</ul>
  </aside>
  
  <!-- Contentinfo landmark (implicit) -->
  <footer>
    <nav aria-label="Footer">
      <ul>
        <li><a href="/privacy">Privacy</a></li>
        <li><a href="/terms">Terms</a></li>
      </ul>
    </nav>
    <p>&copy; 2024 Company</p>
  </footer>
</body>
```

## Labeling Landmarks

### Multiple Landmarks of Same Type

```html
<!-- Multiple navigation landmarks need labels -->
<nav aria-label="Main navigation">
  <ul>
    <li><a href="/">Home</a></li>
    <li><a href="/products">Products</a></li>
  </ul>
</nav>

<nav aria-label="Breadcrumb">
  <ol>
    <li><a href="/">Home</a></li>
    <li><a href="/products">Products</a></li>
    <li aria-current="page">Widget</li>
  </ol>
</nav>

<nav aria-label="Footer navigation">
  <ul>
    <li><a href="/privacy">Privacy</a></li>
    <li><a href="/terms">Terms</a></li>
  </ul>
</nav>
```

### Using aria-labelledby

```html
<!-- Reference existing heading -->
<aside aria-labelledby="sidebar-heading">
  <h2 id="sidebar-heading">Related Products</h2>
  <ul>...</ul>
</aside>

<!-- Reference existing content -->
<section aria-labelledby="section-title">
  <h2 id="section-title">Features Overview</h2>
  <p>Our product features...</p>
</section>
```

### Using aria-label

```html
<!-- When no visible heading exists -->
<nav aria-label="Social media links">
  <ul>
    <li><a href="https://twitter.com/company" aria-label="Twitter">
      <svg>...</svg>
    </a></li>
    <li><a href="https://facebook.com/company" aria-label="Facebook">
      <svg>...</svg>
    </a></li>
  </ul>
</nav>
```

## Landmark Best Practices

### Do's

```html
<!-- ✅ One main landmark per page -->
<main>
  <h1>Page Title</h1>
  <p>Content...</p>
</main>

<!-- ✅ Label repeated landmarks -->
<nav aria-label="Primary">...</nav>
<nav aria-label="Secondary">...</nav>

<!-- ✅ Use header/footer at page level for banner/contentinfo -->
<body>
  <header><!-- Gets banner role --></header>
  <main>
    <article>
      <header><!-- No implicit role --></header>
    </article>
  </main>
  <footer><!-- Gets contentinfo role --></footer>
</body>
```

### Don'ts

```html
<!-- ❌ Multiple main landmarks -->
<main>Content 1</main>
<main>Content 2</main>

<!-- ❌ Unlabeled duplicate landmarks -->
<nav>...</nav>
<nav>...</nav>

<!-- ❌ Unnecessary role on semantic element -->
<header role="banner">...</header>
<nav role="navigation">...</nav>
```

## Search Landmark

```html
<!-- Search landmark with form -->
<form role="search" aria-label="Site search">
  <label for="site-search" class="visually-hidden">Search</label>
  <input 
    type="search" 
    id="site-search" 
    name="q"
    placeholder="Search..."
    aria-describedby="search-hint"
  >
  <span id="search-hint" class="visually-hidden">
    Search products and articles
  </span>
  <button type="submit">
    <span class="visually-hidden">Submit search</span>
    <svg aria-hidden="true"><!-- search icon --></svg>
  </button>
</form>

<!-- HTML5 search element (newer browsers) -->
<search>
  <form action="/search">
    <label for="q">Search</label>
    <input type="search" id="q" name="q">
    <button type="submit">Search</button>
  </form>
</search>
```

## Region Landmark

```html
<!-- Section with accessible name becomes region -->
<section aria-labelledby="pricing-heading">
  <h2 id="pricing-heading">Pricing Plans</h2>
  <div class="pricing-cards">...</div>
</section>

<!-- Without accessible name, no landmark role -->
<section>
  <h2>Features</h2>
  <p>This section is NOT a landmark</p>
</section>
```

## Complex Page Example

```html
<body>
  <header>
    <div class="logo">Company</div>
    
    <nav aria-label="Main">
      <ul>
        <li><a href="/">Home</a></li>
        <li><a href="/products">Products</a></li>
        <li><a href="/services">Services</a></li>
      </ul>
    </nav>
    
    <form role="search" aria-label="Site">
      <input type="search" aria-label="Search">
      <button type="submit">Search</button>
    </form>
    
    <nav aria-label="User account">
      <ul>
        <li><a href="/login">Login</a></li>
        <li><a href="/register">Register</a></li>
      </ul>
    </nav>
  </header>
  
  <nav aria-label="Breadcrumb">
    <ol>
      <li><a href="/">Home</a></li>
      <li><a href="/products">Products</a></li>
      <li aria-current="page">Widget Pro</li>
    </ol>
  </nav>
  
  <main>
    <article>
      <header>
        <h1>Widget Pro</h1>
        <p>The ultimate widget solution</p>
      </header>
      
      <section aria-labelledby="features">
        <h2 id="features">Features</h2>
        <ul>...</ul>
      </section>
      
      <section aria-labelledby="specs">
        <h2 id="specs">Specifications</h2>
        <table>...</table>
      </section>
      
      <section aria-labelledby="reviews">
        <h2 id="reviews">Customer Reviews</h2>
        <div class="reviews">...</div>
      </section>
    </article>
  </main>
  
  <aside aria-labelledby="related">
    <h2 id="related">Related Products</h2>
    <ul>...</ul>
  </aside>
  
  <aside aria-labelledby="support">
    <h2 id="support">Need Help?</h2>
    <p>Contact our support team...</p>
  </aside>
  
  <footer>
    <nav aria-label="Footer">
      <h2 class="visually-hidden">Footer Navigation</h2>
      <ul>
        <li><a href="/about">About Us</a></li>
        <li><a href="/contact">Contact</a></li>
        <li><a href="/privacy">Privacy Policy</a></li>
        <li><a href="/terms">Terms of Service</a></li>
      </ul>
    </nav>
    
    <nav aria-label="Social media">
      <h2 class="visually-hidden">Follow Us</h2>
      <ul>
        <li><a href="https://twitter.com/company">Twitter</a></li>
        <li><a href="https://facebook.com/company">Facebook</a></li>
      </ul>
    </nav>
    
    <p>&copy; 2024 Company Name</p>
  </footer>
</body>
```

## Screen Reader Landmark Navigation

| Screen Reader | Shortcut |
|---------------|----------|
| NVDA | D (landmark), 1-6 (headings) |
| JAWS | R (region), Q (main) |
| VoiceOver | Web rotor → Landmarks |
| TalkBack | Swipe up/down, Headings/Landmarks |

## Testing Landmarks

```javascript
// Check landmark structure
function auditLandmarks() {
  const landmarks = {
    banner: document.querySelectorAll('header, [role="banner"]'),
    navigation: document.querySelectorAll('nav, [role="navigation"]'),
    main: document.querySelectorAll('main, [role="main"]'),
    complementary: document.querySelectorAll('aside, [role="complementary"]'),
    contentinfo: document.querySelectorAll('footer, [role="contentinfo"]'),
    search: document.querySelectorAll('[role="search"]'),
    form: document.querySelectorAll('form[aria-label], form[aria-labelledby]'),
    region: document.querySelectorAll('section[aria-label], section[aria-labelledby]')
  };
  
  console.table({
    banner: landmarks.banner.length,
    navigation: landmarks.navigation.length,
    main: landmarks.main.length,
    complementary: landmarks.complementary.length,
    contentinfo: landmarks.contentinfo.length,
    search: landmarks.search.length,
    form: landmarks.form.length,
    region: landmarks.region.length
  });
  
  // Check for multiple main landmarks
  if (landmarks.main.length !== 1) {
    console.warn('Should have exactly 1 main landmark');
  }
  
  // Check navigation labels
  landmarks.navigation.forEach((nav, i) => {
    if (!nav.getAttribute('aria-label') && !nav.getAttribute('aria-labelledby')) {
      if (landmarks.navigation.length > 1) {
        console.warn(`Navigation ${i + 1} needs a label`);
      }
    }
  });
}
```

## Summary

| Recommendation | Implementation |
|----------------|----------------|
| Use semantic HTML | `<header>`, `<nav>`, `<main>`, `<footer>` |
| Label duplicates | `aria-label` or `aria-labelledby` |
| One main per page | Single `<main>` element |
| Use search role | `role="search"` on search forms |
| Test with screen reader | Navigate using landmarks |
