---
name: aria-basics
description: ARIA fundamentals - when and how to use ARIA
category: accessibility/aria
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# ARIA Basics

## Overview

ARIA (Accessible Rich Internet Applications) adds semantics to HTML when native elements are insufficient. It provides roles, states, and properties for assistive technologies.

## The First Rule of ARIA

> **Don't use ARIA if you can use native HTML.**

```html
<!-- ❌ Unnecessary ARIA -->
<div role="button" tabindex="0" onclick="submit()">Submit</div>

<!-- ✅ Use native HTML -->
<button type="submit">Submit</button>

<!-- ❌ Redundant ARIA -->
<nav role="navigation">...</nav>
<button role="button">Click</button>

<!-- ✅ Native elements have implicit roles -->
<nav>...</nav>
<button>Click</button>
```

## Five Rules of ARIA

### 1. Don't Use ARIA If Native HTML Works

```html
<!-- ❌ ARIA checkbox -->
<div role="checkbox" aria-checked="false" tabindex="0">Agree</div>

<!-- ✅ Native checkbox -->
<input type="checkbox" id="agree">
<label for="agree">Agree</label>
```

### 2. Don't Change Native Semantics

```html
<!-- ❌ Changing button to heading -->
<button role="heading" aria-level="1">Title</button>

<!-- ✅ Use appropriate element -->
<h1>Title</h1>
<button>Click Me</button>
```

### 3. All Interactive ARIA Must Be Keyboard Accessible

```html
<!-- ❌ Not keyboard accessible -->
<div role="button" onclick="doSomething()">Click</div>

<!-- ✅ Keyboard accessible -->
<div 
  role="button" 
  tabindex="0" 
  onclick="doSomething()"
  onkeydown="handleKeyDown(event)"
>Click</div>

<script>
function handleKeyDown(e) {
  if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault();
    doSomething();
  }
}
</script>
```

### 4. Don't Hide Focusable Elements

```html
<!-- ❌ Hidden but focusable -->
<button aria-hidden="true">Click Me</button>

<!-- ✅ Properly hidden -->
<button hidden>Click Me</button>
<button style="display: none;">Click Me</button>
```

### 5. Interactive Elements Must Have Accessible Names

```html
<!-- ❌ No accessible name -->
<button><svg>...</svg></button>

<!-- ✅ With accessible name -->
<button aria-label="Close"><svg aria-hidden="true">...</svg></button>
<button><span class="visually-hidden">Close</span><svg aria-hidden="true">...</svg></button>
```

## ARIA Categories

### Roles

Define what an element is.

```html
<div role="button">...</div>
<div role="tablist">...</div>
<div role="alert">...</div>
```

### States

Current condition of an element.

```html
<button aria-pressed="true">...</button>
<div aria-expanded="false">...</div>
<input aria-invalid="true">
```

### Properties

Characteristics that don't change.

```html
<input aria-required="true">
<div aria-labelledby="heading-id">...</div>
<button aria-haspopup="menu">...</button>
```

## Common ARIA Attributes

### Labeling

```html
<!-- aria-label: Provides label directly -->
<button aria-label="Close dialog">×</button>

<!-- aria-labelledby: References another element -->
<h2 id="dialog-title">Confirm Action</h2>
<div role="dialog" aria-labelledby="dialog-title">...</div>

<!-- aria-describedby: Provides additional description -->
<label for="password">Password</label>
<input type="password" id="password" aria-describedby="password-hint">
<span id="password-hint">Must be at least 8 characters</span>
```

### States

```html
<!-- aria-expanded: Shows expansion state -->
<button aria-expanded="false" aria-controls="menu">Menu</button>
<ul id="menu" hidden>...</ul>

<!-- aria-selected: Shows selection state -->
<li role="option" aria-selected="true">Option 1</li>

<!-- aria-checked: Shows checked state -->
<div role="checkbox" aria-checked="mixed">...</div>

<!-- aria-disabled: Shows disabled state -->
<button aria-disabled="true">Submit</button>

<!-- aria-hidden: Hides from AT -->
<span aria-hidden="true">★★★☆☆</span>
<span class="visually-hidden">3 out of 5 stars</span>
```

### Relationships

```html
<!-- aria-controls: Element controls another -->
<button aria-controls="content" aria-expanded="false">Toggle</button>
<div id="content">...</div>

<!-- aria-owns: Element owns another (for DOM issues) -->
<div role="listbox" aria-owns="option-1 option-2">
  <!-- Options might be elsewhere in DOM -->
</div>

<!-- aria-activedescendant: Current active child -->
<ul role="listbox" aria-activedescendant="option-2">
  <li id="option-1" role="option">One</li>
  <li id="option-2" role="option">Two</li>
</ul>
```

## When to Use ARIA

### ✅ Good Use Cases

```html
<!-- Custom widgets not in HTML -->
<div role="tablist">
  <button role="tab" aria-selected="true">Tab 1</button>
  <button role="tab" aria-selected="false">Tab 2</button>
</div>

<!-- Dynamic content updates -->
<div role="status" aria-live="polite">
  Items in cart: 3
</div>

<!-- Complex interactive patterns -->
<div role="tree" aria-label="File browser">
  <div role="treeitem" aria-expanded="true">Folder</div>
</div>

<!-- Enhancing semantic meaning -->
<nav aria-label="Primary navigation">...</nav>
<nav aria-label="Footer navigation">...</nav>
```

### ❌ Bad Use Cases

```html
<!-- Replicating native elements -->
<div role="button" tabindex="0">Click</div>
<!-- Use: <button>Click</button> -->

<!-- Adding redundant roles -->
<button role="button">Click</button>
<!-- Just: <button>Click</button> -->

<!-- Misusing roles -->
<div role="heading">Not a real heading</div>
<!-- Use: <h2>Real heading</h2> -->
```

## ARIA and HTML5

| HTML5 Element | Implicit Role | ARIA Needed? |
|---------------|---------------|--------------|
| `<button>` | button | No |
| `<a href>` | link | No |
| `<nav>` | navigation | No |
| `<main>` | main | No |
| `<header>` | banner* | No |
| `<footer>` | contentinfo* | No |
| `<aside>` | complementary | No |
| `<article>` | article | No |
| `<section>` | region** | Sometimes |
| `<form>` | form** | Sometimes |

\* When direct child of body
\** Only with accessible name

## Testing ARIA

```javascript
// Check for ARIA usage
function auditAria() {
  const elementsWithRoles = document.querySelectorAll('[role]');
  const elementsWithAria = document.querySelectorAll('[aria-*]');
  
  elementsWithRoles.forEach(el => {
    // Check if native element would work
    const role = el.getAttribute('role');
    const nativeAlternatives = {
      'button': '<button>',
      'link': '<a href>',
      'checkbox': '<input type="checkbox">',
      'radio': '<input type="radio">',
      'textbox': '<input type="text">',
      'listbox': '<select>',
      'heading': '<h1>-<h6>'
    };
    
    if (nativeAlternatives[role]) {
      console.warn(`Consider using ${nativeAlternatives[role]} instead of role="${role}"`, el);
    }
  });
}
```

## Summary

| Do | Don't |
|----|-------|
| Use native HTML first | Add ARIA to native elements |
| Add ARIA for custom widgets | Change native semantics |
| Ensure keyboard accessibility | Use ARIA without keyboard support |
| Test with screen readers | Assume ARIA fixes everything |
| Keep ARIA current (states) | Set ARIA and forget it |
