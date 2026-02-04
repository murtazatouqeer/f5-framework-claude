---
name: skip-links
description: Skip navigation links for keyboard users
category: accessibility/keyboard
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# Skip Links

## Overview

Skip links allow keyboard users to bypass repetitive content and jump directly to main sections. They're essential for pages with navigation menus.

## Basic Implementation

### Simple Skip Link

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <title>Page Title</title>
  <style>
    .skip-link {
      position: absolute;
      top: -40px;
      left: 0;
      background: #000;
      color: #fff;
      padding: 8px 16px;
      z-index: 100;
      text-decoration: none;
    }
    
    .skip-link:focus {
      top: 0;
    }
  </style>
</head>
<body>
  <a href="#main-content" class="skip-link">Skip to main content</a>
  
  <header>
    <nav>
      <!-- Many navigation links -->
    </nav>
  </header>
  
  <main id="main-content" tabindex="-1">
    <h1>Page Title</h1>
    <!-- Main content -->
  </main>
</body>
</html>
```

### Target Element Setup

```html
<!-- Option 1: ID on main element -->
<main id="main-content" tabindex="-1">
  <h1>Welcome</h1>
</main>

<!-- Option 2: ID on heading -->
<main>
  <h1 id="main-content" tabindex="-1">Welcome</h1>
</main>

<!-- Option 3: Wrapper div -->
<div id="main-content" tabindex="-1">
  <main>
    <h1>Welcome</h1>
  </main>
</div>
```

## Multiple Skip Links

```html
<div class="skip-links">
  <a href="#main-content" class="skip-link">Skip to main content</a>
  <a href="#navigation" class="skip-link">Skip to navigation</a>
  <a href="#search" class="skip-link">Skip to search</a>
</div>

<header>
  <nav id="navigation" tabindex="-1">
    <!-- Navigation -->
  </nav>
  <form id="search" role="search" tabindex="-1">
    <!-- Search form -->
  </form>
</header>

<main id="main-content" tabindex="-1">
  <!-- Main content -->
</main>

<style>
.skip-links {
  position: absolute;
  top: 0;
  left: 0;
  z-index: 100;
}

.skip-link {
  position: absolute;
  top: -100px;
  left: 0;
  background: #000;
  color: #fff;
  padding: 8px 16px;
  text-decoration: none;
}

.skip-link:focus {
  top: 0;
  position: relative;
  display: block;
}
</style>
```

## Styling Options

### Basic Visible on Focus

```css
.skip-link {
  position: absolute;
  top: -100%;
  left: 16px;
  background-color: #1a1a1a;
  color: #ffffff;
  padding: 12px 24px;
  font-weight: bold;
  text-decoration: none;
  border-radius: 0 0 4px 4px;
  z-index: 9999;
  transition: top 0.2s ease-in-out;
}

.skip-link:focus {
  top: 0;
}
```

### With Animation

```css
.skip-link {
  position: fixed;
  top: 0;
  left: 50%;
  transform: translateX(-50%) translateY(-100%);
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  padding: 16px 32px;
  font-size: 1rem;
  font-weight: 600;
  text-decoration: none;
  border-radius: 0 0 8px 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  z-index: 9999;
  transition: transform 0.3s ease;
}

.skip-link:focus {
  transform: translateX(-50%) translateY(0);
  outline: 3px solid #fff;
  outline-offset: 2px;
}
```

### High Contrast

```css
.skip-link {
  position: absolute;
  top: -50px;
  left: 0;
  background: #ffff00;
  color: #000000;
  padding: 16px 24px;
  font-size: 1.125rem;
  font-weight: bold;
  text-decoration: underline;
  text-underline-offset: 4px;
  border: 3px solid #000;
  z-index: 9999;
}

.skip-link:focus {
  top: 0;
  outline: 4px solid #000;
  outline-offset: 4px;
}
```

## JavaScript Enhancement

### Smooth Scroll with Focus

```html
<a href="#main-content" class="skip-link" id="skip-link">
  Skip to main content
</a>

<script>
document.getElementById('skip-link').addEventListener('click', (e) => {
  e.preventDefault();
  
  const target = document.getElementById('main-content');
  
  // Smooth scroll
  target.scrollIntoView({ behavior: 'smooth' });
  
  // Set focus after scroll
  setTimeout(() => {
    target.focus();
  }, 500);
});
</script>
```

### Dynamic Target (SPA)

```javascript
// React example
function SkipLink() {
  const handleClick = (e) => {
    e.preventDefault();
    const main = document.querySelector('main');
    main.setAttribute('tabindex', '-1');
    main.focus();
    main.scrollIntoView({ behavior: 'smooth' });
  };
  
  return (
    <a href="#main" className="skip-link" onClick={handleClick}>
      Skip to main content
    </a>
  );
}
```

### Skip Link Menu

```html
<nav class="skip-nav" aria-label="Skip links">
  <button aria-expanded="false" aria-controls="skip-menu">
    Skip to section
  </button>
  <ul id="skip-menu" role="menu" hidden>
    <li role="menuitem">
      <a href="#main-content">Main content</a>
    </li>
    <li role="menuitem">
      <a href="#navigation">Navigation</a>
    </li>
    <li role="menuitem">
      <a href="#footer">Footer</a>
    </li>
  </ul>
</nav>

<script>
const skipButton = document.querySelector('.skip-nav button');
const skipMenu = document.getElementById('skip-menu');

skipButton.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' || e.key === ' ' || e.key === 'ArrowDown') {
    e.preventDefault();
    skipButton.setAttribute('aria-expanded', 'true');
    skipMenu.hidden = false;
    skipMenu.querySelector('a').focus();
  }
});

skipMenu.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    skipButton.setAttribute('aria-expanded', 'false');
    skipMenu.hidden = true;
    skipButton.focus();
  }
});
</script>
```

## Framework Examples

### React

```jsx
// components/SkipLink.jsx
export function SkipLink({ target = "main-content", children = "Skip to main content" }) {
  const handleClick = (e) => {
    e.preventDefault();
    const element = document.getElementById(target);
    if (element) {
      element.setAttribute('tabindex', '-1');
      element.focus();
    }
  };
  
  return (
    <a href={`#${target}`} className="skip-link" onClick={handleClick}>
      {children}
    </a>
  );
}

// App.jsx
function App() {
  return (
    <>
      <SkipLink />
      <Header />
      <main id="main-content">
        <Routes />
      </main>
      <Footer />
    </>
  );
}
```

### Vue

```vue
<!-- SkipLink.vue -->
<template>
  <a :href="`#${target}`" class="skip-link" @click="handleClick">
    <slot>Skip to main content</slot>
  </a>
</template>

<script setup>
const props = defineProps({
  target: {
    type: String,
    default: 'main-content'
  }
});

function handleClick(e) {
  e.preventDefault();
  const element = document.getElementById(props.target);
  if (element) {
    element.setAttribute('tabindex', '-1');
    element.focus();
  }
}
</script>

<style scoped>
.skip-link {
  position: absolute;
  top: -100%;
  left: 0;
  /* ... */
}

.skip-link:focus {
  top: 0;
}
</style>
```

### Angular

```typescript
// skip-link.component.ts
import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-skip-link',
  template: `
    <a [href]="'#' + target" class="skip-link" (click)="handleClick($event)">
      <ng-content>Skip to main content</ng-content>
    </a>
  `,
  styles: [`
    .skip-link {
      position: absolute;
      top: -100%;
      /* ... */
    }
    .skip-link:focus {
      top: 0;
    }
  `]
})
export class SkipLinkComponent {
  @Input() target = 'main-content';
  
  handleClick(event: Event) {
    event.preventDefault();
    const element = document.getElementById(this.target);
    if (element) {
      element.setAttribute('tabindex', '-1');
      element.focus();
    }
  }
}
```

## Common Issues and Fixes

### Issue: Skip Link Not Working

```html
<!-- ❌ Problem: No tabindex on target -->
<main id="main-content">
  <!-- Content -->
</main>

<!-- ✅ Solution: Add tabindex="-1" -->
<main id="main-content" tabindex="-1">
  <!-- Content -->
</main>
```

### Issue: Focus Outline Visible

```css
/* Remove focus outline from skip target */
#main-content:focus {
  outline: none;
}

/* Or use more subtle indicator */
#main-content:focus {
  outline: 2px solid transparent;
}
```

### Issue: Skip Link Always Visible

```css
/* Use clip instead of display:none */
.skip-link {
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

.skip-link:focus {
  position: fixed;
  top: 0;
  left: 0;
  width: auto;
  height: auto;
  padding: 16px;
  margin: 0;
  overflow: visible;
  clip: auto;
  white-space: normal;
  z-index: 9999;
}
```

## Testing

### Manual Testing

1. Load page
2. Press Tab key
3. Skip link should be first focusable element
4. Skip link should become visible on focus
5. Press Enter
6. Focus should move to main content
7. Continue tabbing should go through main content

### Automated Testing

```javascript
// Cypress test
describe('Skip Links', () => {
  it('should skip to main content', () => {
    cy.visit('/');
    
    // Tab to skip link
    cy.get('body').tab();
    
    // Verify skip link is visible
    cy.get('.skip-link').should('be.visible');
    
    // Activate skip link
    cy.get('.skip-link').type('{enter}');
    
    // Verify focus moved to main content
    cy.focused().should('have.id', 'main-content');
  });
});
```

## Summary

| Requirement | Implementation |
|-------------|----------------|
| First focusable | Place skip link first in DOM |
| Hidden until focus | CSS positioning techniques |
| Visible on focus | :focus styles |
| Links to main | href points to main content ID |
| Target focusable | tabindex="-1" on target |
| Keyboard activation | Works with Enter key |
