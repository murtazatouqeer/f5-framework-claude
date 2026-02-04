---
name: accessible-buttons
description: Creating accessible button components
category: accessibility/components
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# Accessible Buttons

## Overview

Buttons are one of the most common interactive elements. Proper button implementation ensures all users can trigger actions regardless of how they interact with the page.

## Native Button Element

### Basic Button

```html
<!-- Always prefer native button -->
<button type="button">Click me</button>

<!-- Submit button for forms -->
<button type="submit">Submit</button>

<!-- Reset button -->
<button type="reset">Reset</button>
```

### Button with Icon and Text

```html
<!-- Icon with visible text (ideal) -->
<button type="button">
  <svg aria-hidden="true" focusable="false">
    <use href="#icon-save"></use>
  </svg>
  Save Document
</button>

<!-- Icon-only button (needs accessible name) -->
<button type="button" aria-label="Save document">
  <svg aria-hidden="true" focusable="false">
    <use href="#icon-save"></use>
  </svg>
</button>
```

## When to Use Different Elements

| Use Case | Element |
|----------|---------|
| Triggers action | `<button>` |
| Navigates to URL | `<a href>` |
| Submits form | `<button type="submit">` |
| Opens dialog | `<button>` + aria-haspopup |
| Toggles state | `<button>` + aria-pressed |

## Button States

### Toggle Button

```html
<!-- Toggle button (like bold in editor) -->
<button 
  type="button" 
  aria-pressed="false"
  onclick="toggleBold(this)"
>
  Bold
</button>

<script>
function toggleBold(button) {
  const pressed = button.getAttribute('aria-pressed') === 'true';
  button.setAttribute('aria-pressed', !pressed);
  // Apply bold formatting
}
</script>
```

### Expanded/Collapsed

```html
<!-- Button that controls expandable section -->
<button 
  type="button"
  aria-expanded="false"
  aria-controls="menu-items"
  onclick="toggleMenu(this)"
>
  Menu
</button>

<ul id="menu-items" hidden>
  <li><a href="/home">Home</a></li>
  <li><a href="/about">About</a></li>
</ul>

<script>
function toggleMenu(button) {
  const expanded = button.getAttribute('aria-expanded') === 'true';
  button.setAttribute('aria-expanded', !expanded);
  document.getElementById('menu-items').hidden = expanded;
}
</script>
```

### Disabled State

```html
<!-- Native disabled (removes from tab order) -->
<button type="button" disabled>
  Submit
</button>

<!-- aria-disabled (keeps in tab order, can explain why) -->
<button 
  type="button" 
  aria-disabled="true"
  aria-describedby="disable-reason"
>
  Submit
</button>
<span id="disable-reason" class="visually-hidden">
  Complete all required fields to enable submission
</span>
```

### Loading State

```html
<button 
  type="button" 
  aria-busy="true"
  aria-live="polite"
>
  <span class="spinner" aria-hidden="true"></span>
  <span class="button-text">Saving...</span>
</button>
```

## Custom Button (When Native Not Possible)

### Making Divs Accessible

```html
<!-- Custom button (use native when possible!) -->
<div 
  role="button"
  tabindex="0"
  onclick="doAction()"
  onkeydown="handleKeydown(event)"
>
  Custom Button
</div>

<script>
function handleKeydown(event) {
  // Activate on Enter and Space
  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault();
    doAction();
  }
}
</script>
```

### Required Attributes for Custom Buttons

| Attribute | Purpose |
|-----------|---------|
| `role="button"` | Announces as button |
| `tabindex="0"` | Makes focusable |
| `onclick` | Mouse activation |
| `onkeydown` | Keyboard activation (Enter + Space) |

## Button Groups

### Toolbar Pattern

```html
<div role="toolbar" aria-label="Text formatting">
  <button type="button" aria-pressed="false">Bold</button>
  <button type="button" aria-pressed="false">Italic</button>
  <button type="button" aria-pressed="false">Underline</button>
</div>
```

### Button Group with Label

```html
<div role="group" aria-label="Pagination">
  <button type="button" aria-label="Previous page">
    &lt; Prev
  </button>
  <button type="button" aria-current="page">2</button>
  <button type="button">3</button>
  <button type="button" aria-label="Next page">
    Next &gt;
  </button>
</div>
```

## Accessible Names

### Labeling Methods

```html
<!-- Visible text (preferred) -->
<button type="button">Save Changes</button>

<!-- aria-label for icon-only -->
<button type="button" aria-label="Close dialog">
  <svg aria-hidden="true">...</svg>
</button>

<!-- aria-labelledby for complex -->
<button type="button" aria-labelledby="action-label item-name">
  <span id="action-label">Delete</span>
</button>
<span id="item-name" class="visually-hidden">Invoice #123</span>

<!-- aria-describedby for additional context -->
<button 
  type="button" 
  aria-describedby="delete-warning"
>
  Delete Account
</button>
<p id="delete-warning" class="visually-hidden">
  This action cannot be undone
</p>
```

### Bad vs Good Labels

```html
<!-- Bad: Non-descriptive -->
<button>Click here</button>
<button>Submit</button>
<button aria-label="Button">...</button>

<!-- Good: Descriptive -->
<button>Add to cart</button>
<button>Submit application</button>
<button aria-label="Close notification">...</button>
```

## Focus Indicators

### CSS Focus Styles

```css
/* Visible focus indicator */
button:focus {
  outline: 2px solid #005fcc;
  outline-offset: 2px;
}

/* For browsers that support :focus-visible */
button:focus:not(:focus-visible) {
  outline: none;
}

button:focus-visible {
  outline: 2px solid #005fcc;
  outline-offset: 2px;
}

/* High contrast mode support */
@media (forced-colors: active) {
  button:focus {
    outline: 3px solid ButtonText;
  }
}
```

### Focus States

```css
/* Base button */
.button {
  background: #0066cc;
  color: white;
  border: none;
  padding: 0.75em 1.5em;
  border-radius: 4px;
  cursor: pointer;
}

/* Hover state */
.button:hover {
  background: #0052a3;
}

/* Focus state */
.button:focus-visible {
  outline: 3px solid #ffd700;
  outline-offset: 2px;
}

/* Active state */
.button:active {
  background: #004080;
}

/* Disabled state */
.button:disabled {
  background: #cccccc;
  color: #666666;
  cursor: not-allowed;
}
```

## Touch Target Size

```css
/* Minimum 44x44px touch target */
button {
  min-width: 44px;
  min-height: 44px;
  padding: 12px 16px;
}

/* Icon button */
.icon-button {
  width: 44px;
  height: 44px;
  padding: 10px;
}

/* Ensure adequate spacing */
.button-group button {
  margin: 4px;
}
```

## React Component Example

```jsx
function AccessibleButton({
  children,
  onClick,
  disabled = false,
  loading = false,
  pressed,
  expanded,
  controls,
  describedBy,
  ...props
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      aria-disabled={disabled}
      aria-busy={loading}
      aria-pressed={pressed}
      aria-expanded={expanded}
      aria-controls={controls}
      aria-describedby={describedBy}
      {...props}
    >
      {loading ? (
        <>
          <span className="spinner" aria-hidden="true" />
          <span className="visually-hidden">Loading</span>
          {children}
        </>
      ) : (
        children
      )}
    </button>
  );
}

// Usage
<AccessibleButton
  onClick={handleSave}
  loading={isSaving}
>
  Save Document
</AccessibleButton>

<AccessibleButton
  pressed={isBold}
  onClick={toggleBold}
>
  Bold
</AccessibleButton>
```

## Testing Checklist

```markdown
## Button Accessibility Checklist

### Keyboard
- [ ] Focusable with Tab
- [ ] Activates with Enter
- [ ] Activates with Space
- [ ] Focus indicator visible

### Screen Reader
- [ ] Role announced as "button"
- [ ] Name is descriptive
- [ ] State announced (pressed, expanded, disabled)
- [ ] Changes announced

### Visual
- [ ] Focus indicator visible (3:1 contrast)
- [ ] Disabled state distinguishable
- [ ] Loading state visible
- [ ] Touch target 44x44px minimum

### States
- [ ] Disabled state prevents activation
- [ ] Toggle state announced
- [ ] Expanded/collapsed state announced
- [ ] Loading state communicated
```

## Common Issues

### Issue: Div Used as Button

```html
<!-- Problem -->
<div class="button" onclick="doThing()">Click me</div>

<!-- Solution -->
<button type="button" class="button" onclick="doThing()">
  Click me
</button>
```

### Issue: Link Styled as Button

```html
<!-- Problem: Link that triggers action -->
<a href="#" onclick="doAction(); return false;">Submit</a>

<!-- Solution: Use button -->
<button type="button" onclick="doAction()">Submit</button>
```

### Issue: Missing Accessible Name

```html
<!-- Problem -->
<button><svg>...</svg></button>

<!-- Solution -->
<button aria-label="Close menu">
  <svg aria-hidden="true">...</svg>
</button>
```

## Summary

| Requirement | Implementation |
|-------------|----------------|
| Native element | `<button type="button">` |
| Keyboard support | Enter + Space activation |
| Accessible name | Visible text or aria-label |
| Focus indicator | 3:1 contrast, visible outline |
| Touch target | 44x44px minimum |
| States | aria-pressed, aria-expanded, disabled |
| Loading | aria-busy="true" |
