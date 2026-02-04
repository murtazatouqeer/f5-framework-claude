---
name: focus-management
description: Managing focus for accessible interactions
category: accessibility/keyboard
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# Focus Management

## Overview

Proper focus management ensures keyboard users know where they are on the page and can navigate efficiently. Poor focus management creates confusion and makes applications unusable for keyboard users.

## Focus Indicators

### Default Browser Focus

```css
/* Default (don't remove without replacement!) */
:focus {
  outline: auto;
}

/* ❌ Never do this without replacement */
:focus {
  outline: none;
}
```

### Custom Focus Styles

```css
/* ✅ Custom visible focus */
:focus {
  outline: 2px solid #0066cc;
  outline-offset: 2px;
}

/* High contrast focus */
:focus {
  outline: 3px solid #000;
  outline-offset: 2px;
  box-shadow: 0 0 0 5px #fff;
}

/* Focus ring for specific elements */
button:focus,
a:focus {
  outline: 2px solid currentColor;
  outline-offset: 2px;
}

/* Card/container focus */
.card:focus-within {
  box-shadow: 0 0 0 3px #0066cc;
}
```

### Focus-Visible

```css
/* Only show focus ring for keyboard users */
:focus {
  outline: none;
}

:focus-visible {
  outline: 2px solid #0066cc;
  outline-offset: 2px;
}

/* Polyfill for older browsers */
.js-focus-visible :focus:not(.focus-visible) {
  outline: none;
}

.js-focus-visible .focus-visible {
  outline: 2px solid #0066cc;
}
```

## Moving Focus

### Programmatic Focus

```javascript
// Move focus to an element
element.focus();

// Focus with scroll behavior
element.focus({ preventScroll: true });

// Focus options (experimental)
element.focus({ focusVisible: true });
```

### Focus After Actions

```javascript
// After opening modal
function openModal() {
  const modal = document.getElementById('modal');
  modal.hidden = false;
  
  // Focus first focusable element in modal
  const firstFocusable = modal.querySelector(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );
  firstFocusable.focus();
}

// After closing modal
let previousFocus;

function openModal() {
  previousFocus = document.activeElement;
  // ... open modal
}

function closeModal() {
  // ... close modal
  previousFocus.focus();
}
```

### Focus After Content Changes

```javascript
// After loading new content
async function loadMoreItems() {
  const container = document.getElementById('items');
  const lastItem = container.lastElementChild;
  
  const newItems = await fetchItems();
  container.append(...newItems);
  
  // Focus first new item
  lastItem.nextElementSibling.focus();
}

// After deleting item
function deleteItem(item) {
  const next = item.nextElementSibling;
  const prev = item.previousElementSibling;
  
  item.remove();
  
  // Focus adjacent item
  (next || prev)?.focus();
}
```

## Focus Trapping

### Modal Focus Trap

```html
<div id="modal" role="dialog" aria-modal="true" hidden>
  <button id="close-btn">Close</button>
  <h2>Modal Title</h2>
  <p>Modal content...</p>
  <button id="action-btn">Action</button>
</div>

<script>
const modal = document.getElementById('modal');
const focusableElements = modal.querySelectorAll(
  'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
);
const firstFocusable = focusableElements[0];
const lastFocusable = focusableElements[focusableElements.length - 1];

modal.addEventListener('keydown', (e) => {
  if (e.key !== 'Tab') return;
  
  if (e.shiftKey) {
    // Shift + Tab
    if (document.activeElement === firstFocusable) {
      e.preventDefault();
      lastFocusable.focus();
    }
  } else {
    // Tab
    if (document.activeElement === lastFocusable) {
      e.preventDefault();
      firstFocusable.focus();
    }
  }
});
</script>
```

### Inert Attribute

```html
<!-- Hide background from keyboard when modal is open -->
<main id="main" inert>
  <!-- Background content -->
</main>

<dialog open>
  <!-- Modal content (not inert) -->
</dialog>

<script>
function openModal() {
  document.getElementById('main').inert = true;
  dialog.showModal();
}

function closeModal() {
  dialog.close();
  document.getElementById('main').inert = false;
}
</script>

<!-- Polyfill for inert -->
<script src="https://unpkg.com/wicg-inert@latest/dist/inert.min.js"></script>
```

### Focus Trap Library

```javascript
import { createFocusTrap } from 'focus-trap';

const modal = document.getElementById('modal');

const focusTrap = createFocusTrap(modal, {
  initialFocus: '#first-input',
  fallbackFocus: modal,
  escapeDeactivates: true,
  clickOutsideDeactivates: true,
  returnFocusOnDeactivate: true
});

function openModal() {
  modal.hidden = false;
  focusTrap.activate();
}

function closeModal() {
  focusTrap.deactivate();
  modal.hidden = true;
}
```

## Focus Zones

### Skip to Main Content

```html
<a href="#main-content" class="skip-link">Skip to main content</a>

<header><!-- Header content --></header>

<main id="main-content" tabindex="-1">
  <h1>Page Title</h1>
  <!-- Main content -->
</main>

<style>
.skip-link {
  position: absolute;
  top: -40px;
  left: 0;
  padding: 8px;
  background: #000;
  color: #fff;
  z-index: 100;
}

.skip-link:focus {
  top: 0;
}
</style>
```

### Focus Regions

```html
<!-- Announce focus changes to screen readers -->
<main id="main" aria-live="polite">
  <!-- Content that changes -->
</main>

<!-- Focus group for toolbar -->
<div role="toolbar" aria-label="Text formatting">
  <button>Bold</button>
  <button>Italic</button>
  <button>Underline</button>
</div>
```

## SPA Navigation

### Route Change Focus

```javascript
// React Router
import { useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';

function App() {
  const mainRef = useRef(null);
  const location = useLocation();
  
  useEffect(() => {
    // Focus main content on route change
    mainRef.current?.focus();
    
    // Announce route change
    document.title = `${getPageTitle(location)} - My App`;
  }, [location]);
  
  return (
    <main ref={mainRef} tabIndex={-1}>
      {/* Routes */}
    </main>
  );
}
```

### Live Region Announcement

```html
<div 
  id="route-announcer" 
  role="status" 
  aria-live="polite" 
  aria-atomic="true"
  class="visually-hidden"
></div>

<script>
function announceRouteChange(title) {
  const announcer = document.getElementById('route-announcer');
  announcer.textContent = `Navigated to ${title}`;
}
</script>
```

## Focus Best Practices

### Do's

```javascript
// ✅ Focus heading after navigation
function navigateToPage() {
  loadPage();
  document.querySelector('h1').focus();
}

// ✅ Return focus after modal closes
let previousFocus;
function closeModal() {
  modal.hidden = true;
  previousFocus.focus();
}

// ✅ Focus error summary
function showErrors(errors) {
  const summary = document.getElementById('error-summary');
  summary.innerHTML = renderErrors(errors);
  summary.focus();
}
```

### Don'ts

```javascript
// ❌ Focus jumping unexpectedly
input.addEventListener('blur', () => {
  someOtherElement.focus(); // Disorienting
});

// ❌ Removing focus on click
button.addEventListener('click', () => {
  document.activeElement.blur(); // Loses focus
});

// ❌ Auto-focusing without user action
window.addEventListener('load', () => {
  someInput.focus(); // May be unexpected
});
```

## Component Examples

### Accordion

```javascript
function toggleAccordion(header) {
  const panel = header.nextElementSibling;
  const expanded = header.getAttribute('aria-expanded') === 'true';
  
  header.setAttribute('aria-expanded', !expanded);
  panel.hidden = expanded;
  
  // Focus stays on header
}
```

### Tab Panel

```javascript
function selectTab(tab) {
  // Deselect all
  tabs.forEach(t => {
    t.setAttribute('aria-selected', 'false');
    t.setAttribute('tabindex', '-1');
  });
  panels.forEach(p => p.hidden = true);
  
  // Select new tab
  tab.setAttribute('aria-selected', 'true');
  tab.setAttribute('tabindex', '0');
  
  const panel = document.getElementById(tab.getAttribute('aria-controls'));
  panel.hidden = false;
  
  // Keep focus on tab
  tab.focus();
}
```

### Dropdown Menu

```javascript
function openMenu(button, menu) {
  button.setAttribute('aria-expanded', 'true');
  menu.hidden = false;
  
  // Focus first menu item
  menu.querySelector('[role="menuitem"]').focus();
}

function closeMenu(button, menu) {
  button.setAttribute('aria-expanded', 'false');
  menu.hidden = true;
  
  // Return focus to button
  button.focus();
}
```

## Testing Focus

```javascript
// Track focus changes
document.addEventListener('focusin', (e) => {
  console.log('Focus moved to:', e.target);
});

// Test focus trap
function testFocusTrap(container) {
  const focusable = container.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );
  
  console.log('Focusable elements in trap:', focusable.length);
  focusable.forEach((el, i) => {
    console.log(`${i + 1}. ${el.tagName} - ${el.textContent?.trim() || el.id}`);
  });
}

// Check focus visibility
function auditFocusStyles() {
  const focusable = document.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );
  
  focusable.forEach(el => {
    el.focus();
    const styles = getComputedStyle(el);
    
    if (styles.outline === 'none' && styles.boxShadow === 'none') {
      console.warn('No focus indicator:', el);
    }
  });
}
```

## Summary

| Scenario | Focus Action |
|----------|--------------|
| Modal opens | Focus first element in modal |
| Modal closes | Return focus to trigger |
| Content loads | Focus new content or heading |
| Item deleted | Focus adjacent item |
| Error occurs | Focus error message/summary |
| Route changes | Focus main heading or content |
| Form submits | Focus success message or first error |
