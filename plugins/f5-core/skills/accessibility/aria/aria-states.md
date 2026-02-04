---
name: aria-states
description: ARIA states and properties for dynamic content
category: accessibility/aria
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# ARIA States and Properties

## Overview

ARIA states and properties provide additional information about elements to assistive technologies. States change during interaction, while properties typically remain constant.

## States vs Properties

| Type | Changes | Examples |
|------|---------|----------|
| **States** | Frequently | aria-checked, aria-expanded, aria-selected |
| **Properties** | Rarely/Never | aria-label, aria-describedby, aria-required |

## Common States

### aria-expanded

Indicates if a collapsible element is expanded.

```html
<!-- Accordion -->
<button 
  aria-expanded="false"
  aria-controls="panel-1"
>
  Section 1
</button>
<div id="panel-1" hidden>
  <p>Panel content...</p>
</div>

<script>
function togglePanel(button) {
  const expanded = button.getAttribute('aria-expanded') === 'true';
  const panel = document.getElementById(button.getAttribute('aria-controls'));
  
  button.setAttribute('aria-expanded', !expanded);
  panel.hidden = expanded;
}
</script>

<!-- Dropdown menu -->
<button 
  aria-expanded="false"
  aria-haspopup="menu"
  aria-controls="dropdown-menu"
>
  Options ▼
</button>
<ul id="dropdown-menu" role="menu" hidden>
  <li role="menuitem">Edit</li>
  <li role="menuitem">Delete</li>
</ul>
```

### aria-selected

Indicates selection state.

```html
<!-- Tabs -->
<div role="tablist">
  <button role="tab" aria-selected="true" id="tab-1">Tab 1</button>
  <button role="tab" aria-selected="false" id="tab-2">Tab 2</button>
</div>

<!-- Listbox -->
<ul role="listbox" aria-label="Choose color">
  <li role="option" aria-selected="true">Red</li>
  <li role="option" aria-selected="false">Blue</li>
  <li role="option" aria-selected="false">Green</li>
</ul>

<!-- Grid selection -->
<table role="grid" aria-multiselectable="true">
  <tr role="row" aria-selected="true">
    <td role="gridcell">Row 1</td>
  </tr>
  <tr role="row" aria-selected="false">
    <td role="gridcell">Row 2</td>
  </tr>
</table>
```

### aria-checked

Indicates checked state of checkboxes and radios.

```html
<!-- Checkbox -->
<div 
  role="checkbox" 
  tabindex="0"
  aria-checked="false"
>
  <span class="checkbox-icon" aria-hidden="true"></span>
  Accept terms
</div>

<!-- Tri-state checkbox -->
<div role="checkbox" aria-checked="mixed">
  Select all (2 of 5 selected)
</div>

<!-- Radio buttons -->
<div role="radiogroup" aria-labelledby="size-label">
  <span id="size-label">Size:</span>
  <div role="radio" aria-checked="true" tabindex="0">Small</div>
  <div role="radio" aria-checked="false" tabindex="-1">Medium</div>
  <div role="radio" aria-checked="false" tabindex="-1">Large</div>
</div>

<!-- Toggle switch -->
<button 
  role="switch" 
  aria-checked="false"
  aria-label="Dark mode"
>
  <span class="switch-thumb"></span>
</button>
```

### aria-pressed

Indicates pressed state of toggle buttons.

```html
<!-- Toggle button -->
<button 
  aria-pressed="false"
  onclick="toggleBold(this)"
>
  Bold
</button>

<script>
function toggleBold(button) {
  const pressed = button.getAttribute('aria-pressed') === 'true';
  button.setAttribute('aria-pressed', !pressed);
}
</script>

<!-- Button group -->
<div role="group" aria-label="Text formatting">
  <button aria-pressed="false">Bold</button>
  <button aria-pressed="true">Italic</button>
  <button aria-pressed="false">Underline</button>
</div>
```

### aria-disabled

Indicates element is disabled but visible.

```html
<!-- Disabled button (perceivable but not operable) -->
<button aria-disabled="true">
  Submit
</button>

<!-- vs HTML disabled (may be invisible to some AT) -->
<button disabled>Submit</button>

<!-- Disabled with explanation -->
<button 
  aria-disabled="true"
  aria-describedby="submit-hint"
>
  Submit
</button>
<span id="submit-hint">Complete required fields to submit</span>

<style>
button[aria-disabled="true"] {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
```

### aria-hidden

Hides element from assistive technology.

```html
<!-- Decorative icons -->
<button>
  <svg aria-hidden="true"><!-- icon --></svg>
  <span>Delete</span>
</button>

<!-- Duplicate content -->
<span aria-hidden="true">★★★☆☆</span>
<span class="visually-hidden">3 out of 5 stars</span>

<!-- Hide entire section from AT -->
<div aria-hidden="true">
  <p>This entire section is hidden from screen readers</p>
</div>

<!-- ⚠️ Warning: Don't hide focusable elements -->
<!-- ❌ Bad -->
<button aria-hidden="true">Click me</button>

<!-- When modal is open, hide background -->
<main aria-hidden="true">...</main>
<dialog open>...</dialog>
```

### aria-invalid

Indicates validation state.

```html
<!-- Invalid input -->
<label for="email">Email</label>
<input 
  type="email" 
  id="email"
  aria-invalid="true"
  aria-describedby="email-error"
>
<span id="email-error" class="error">Please enter a valid email address</span>

<!-- Valid input -->
<input type="email" aria-invalid="false">

<!-- Grammar/spelling error -->
<textarea aria-invalid="grammar">
  Their going to the store
</textarea>
```

### aria-busy

Indicates content is loading.

```html
<!-- Loading state -->
<div 
  role="region" 
  aria-busy="true"
  aria-label="Search results"
>
  <p>Loading...</p>
</div>

<!-- After loading -->
<div 
  role="region" 
  aria-busy="false"
  aria-label="Search results"
>
  <ul>
    <li>Result 1</li>
    <li>Result 2</li>
  </ul>
</div>

<!-- Live region with loading -->
<div 
  role="status"
  aria-live="polite"
  aria-busy="true"
>
  Updating...
</div>
```

### aria-current

Indicates current item in a set.

```html
<!-- Current page in navigation -->
<nav aria-label="Main">
  <ul>
    <li><a href="/">Home</a></li>
    <li><a href="/products" aria-current="page">Products</a></li>
    <li><a href="/about">About</a></li>
  </ul>
</nav>

<!-- Current step in wizard -->
<ol aria-label="Checkout progress">
  <li aria-current="step">1. Shipping</li>
  <li>2. Payment</li>
  <li>3. Review</li>
</ol>

<!-- Current date in calendar -->
<td aria-current="date">15</td>

<!-- Current time -->
<li aria-current="time">10:00 AM - Meeting</li>

<!-- Current location -->
<li aria-current="location">San Francisco</li>
```

## Common Properties

### aria-label

Provides accessible name.

```html
<!-- Icon button -->
<button aria-label="Close dialog">
  <svg aria-hidden="true"><!-- X icon --></svg>
</button>

<!-- Navigation -->
<nav aria-label="Primary navigation">...</nav>
<nav aria-label="Footer navigation">...</nav>

<!-- Search -->
<input type="search" aria-label="Search products">
```

### aria-labelledby

References element(s) for label.

```html
<!-- Reference heading -->
<section aria-labelledby="section-title">
  <h2 id="section-title">Features</h2>
  <p>Content...</p>
</section>

<!-- Multiple references -->
<button aria-labelledby="button-text button-count">
  <span id="button-text">Notifications</span>
  <span id="button-count">(5)</span>
</button>
<!-- Announced as: "Notifications (5)" -->

<!-- Dialog -->
<div role="dialog" aria-labelledby="dialog-title">
  <h2 id="dialog-title">Confirm Action</h2>
</div>
```

### aria-describedby

Provides additional description.

```html
<!-- Form field with hint -->
<label for="password">Password</label>
<input 
  type="password" 
  id="password"
  aria-describedby="password-requirements"
>
<div id="password-requirements">
  Must be 8+ characters with numbers and symbols
</div>

<!-- Error message -->
<input 
  type="email" 
  aria-invalid="true"
  aria-describedby="email-error"
>
<span id="email-error">Please enter a valid email</span>

<!-- Multiple descriptions -->
<input 
  type="text"
  aria-describedby="hint error"
>
<span id="hint">Enter your username</span>
<span id="error">Username is already taken</span>
```

### aria-required

Indicates required field.

```html
<label for="name">Name *</label>
<input 
  type="text" 
  id="name"
  required
  aria-required="true"
>

<!-- Note: HTML required also works, but aria-required 
     ensures screen readers announce it -->
```

### aria-readonly

Indicates read-only state.

```html
<label for="order-id">Order ID</label>
<input 
  type="text" 
  id="order-id"
  value="ORD-12345"
  readonly
  aria-readonly="true"
>
```

### aria-haspopup

Indicates popup type.

```html
<!-- Menu popup -->
<button aria-haspopup="menu" aria-expanded="false">
  Options
</button>

<!-- Dialog popup -->
<button aria-haspopup="dialog">
  Open Settings
</button>

<!-- Listbox popup -->
<input 
  type="text"
  role="combobox"
  aria-haspopup="listbox"
  aria-expanded="false"
>

<!-- Values: menu, listbox, tree, grid, dialog, true -->
```

### aria-controls

Identifies controlled element.

```html
<!-- Accordion -->
<button 
  aria-expanded="false"
  aria-controls="section-1-content"
>
  Section 1
</button>
<div id="section-1-content" hidden>
  Content here...
</div>

<!-- Tabs -->
<button role="tab" aria-controls="panel-1">Tab 1</button>
<div role="tabpanel" id="panel-1">Panel content</div>
```

### aria-owns

Defines parent-child relationship.

```html
<!-- When DOM structure doesn't match visual -->
<div role="listbox" aria-owns="option-1 option-2 option-3">
  <!-- Options may be elsewhere in DOM due to positioning -->
</div>

<!-- Somewhere else -->
<div id="option-1" role="option">Option 1</div>
<div id="option-2" role="option">Option 2</div>
<div id="option-3" role="option">Option 3</div>
```

### aria-activedescendant

Identifies active child element.

```html
<ul 
  role="listbox" 
  tabindex="0"
  aria-activedescendant="option-2"
>
  <li role="option" id="option-1">First</li>
  <li role="option" id="option-2">Second</li>
  <li role="option" id="option-3">Third</li>
</ul>

<script>
listbox.addEventListener('keydown', (e) => {
  // Update aria-activedescendant on arrow keys
  if (e.key === 'ArrowDown') {
    listbox.setAttribute('aria-activedescendant', 'option-3');
  }
});
</script>
```

## State Management Patterns

```javascript
// Generic state toggle
function toggleState(element, attribute) {
  const current = element.getAttribute(attribute) === 'true';
  element.setAttribute(attribute, !current);
  return !current;
}

// Accordion state
function toggleAccordion(trigger) {
  const expanded = toggleState(trigger, 'aria-expanded');
  const panel = document.getElementById(trigger.getAttribute('aria-controls'));
  panel.hidden = !expanded;
}

// Tab selection
function selectTab(tab) {
  // Deselect all tabs
  const tablist = tab.closest('[role="tablist"]');
  tablist.querySelectorAll('[role="tab"]').forEach(t => {
    t.setAttribute('aria-selected', 'false');
    t.setAttribute('tabindex', '-1');
  });
  
  // Select clicked tab
  tab.setAttribute('aria-selected', 'true');
  tab.setAttribute('tabindex', '0');
  
  // Show associated panel
  const panelId = tab.getAttribute('aria-controls');
  document.querySelectorAll('[role="tabpanel"]').forEach(p => p.hidden = true);
  document.getElementById(panelId).hidden = false;
}
```

## Quick Reference

| Attribute | Values | Use Case |
|-----------|--------|----------|
| aria-expanded | true/false | Collapsible content |
| aria-selected | true/false | Selection in lists |
| aria-checked | true/false/mixed | Checkboxes, switches |
| aria-pressed | true/false | Toggle buttons |
| aria-disabled | true/false | Non-interactive state |
| aria-hidden | true/false | Hide from AT |
| aria-invalid | true/false/grammar/spelling | Validation state |
| aria-busy | true/false | Loading state |
| aria-current | page/step/date/time/location/true | Current item |
