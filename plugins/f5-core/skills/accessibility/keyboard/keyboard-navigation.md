---
name: keyboard-navigation
description: Keyboard navigation patterns and implementation
category: accessibility/keyboard
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# Keyboard Navigation

## Overview

Keyboard accessibility ensures users can navigate and operate all interactive elements without a mouse. This is essential for users with motor disabilities, power users, and screen reader users.

## Focusable Elements

### Natively Focusable

```html
<!-- These are focusable by default -->
<a href="/page">Link</a>
<button>Button</button>
<input type="text">
<select>...</select>
<textarea></textarea>
<details><summary>Toggle</summary></details>

<!-- Not focusable by default -->
<div>Not focusable</div>
<span>Not focusable</span>
<p>Not focusable</p>
```

### Making Elements Focusable

```html
<!-- tabindex="0": Add to tab order -->
<div tabindex="0" role="button" onclick="handleClick()">
  Custom Button
</div>

<!-- tabindex="-1": Focusable via script only -->
<div tabindex="-1" id="modal">
  Modal content (focused programmatically)
</div>

<!-- ❌ tabindex > 0: Avoid - creates confusing order -->
<button tabindex="5">Don't do this</button>
```

## Tab Order

### Natural Tab Order

```html
<!-- Elements are focused in DOM order -->
<form>
  <input type="text" placeholder="First">     <!-- Tab 1 -->
  <input type="text" placeholder="Second">    <!-- Tab 2 -->
  <input type="text" placeholder="Third">     <!-- Tab 3 -->
  <button type="submit">Submit</button>       <!-- Tab 4 -->
</form>
```

### Removing from Tab Order

```html
<!-- Remove from tab order -->
<button tabindex="-1">Not in tab order</button>
<input type="text" disabled> <!-- Disabled = not focusable -->

<!-- Hidden elements are not focusable -->
<button hidden>Hidden</button>
<button style="display: none;">Hidden</button>
<button style="visibility: hidden;">Hidden</button>
```

## Common Keyboard Patterns

### Standard Keys

| Key | Action |
|-----|--------|
| Tab | Move to next focusable element |
| Shift + Tab | Move to previous focusable element |
| Enter | Activate buttons, links |
| Space | Activate buttons, toggle checkboxes |
| Arrow keys | Navigate within widgets |
| Escape | Close dialogs, cancel actions |
| Home/End | Jump to first/last item |

### Button Interaction

```html
<button onclick="handleClick()">Click Me</button>

<!-- Activated by: Enter or Space -->
```

### Link Interaction

```html
<a href="/page">Go to Page</a>

<!-- Activated by: Enter only -->
```

### Checkbox Interaction

```html
<input type="checkbox" id="agree">
<label for="agree">I agree</label>

<!-- Toggled by: Space -->
```

## Custom Widget Keyboard Support

### Custom Button

```html
<div 
  role="button"
  tabindex="0"
  onclick="handleClick()"
  onkeydown="handleKeydown(event)"
>
  Custom Button
</div>

<script>
function handleKeydown(event) {
  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault();
    handleClick();
  }
}
</script>
```

### Tab Panel Navigation

```html
<div role="tablist" aria-label="Product tabs">
  <button role="tab" aria-selected="true" tabindex="0">Details</button>
  <button role="tab" aria-selected="false" tabindex="-1">Reviews</button>
  <button role="tab" aria-selected="false" tabindex="-1">Specs</button>
</div>

<script>
const tabs = document.querySelectorAll('[role="tab"]');

tabs.forEach(tab => {
  tab.addEventListener('keydown', (e) => {
    let index = Array.from(tabs).indexOf(e.target);
    
    switch (e.key) {
      case 'ArrowRight':
        index = (index + 1) % tabs.length;
        break;
      case 'ArrowLeft':
        index = (index - 1 + tabs.length) % tabs.length;
        break;
      case 'Home':
        index = 0;
        break;
      case 'End':
        index = tabs.length - 1;
        break;
      default:
        return;
    }
    
    e.preventDefault();
    selectTab(tabs[index]);
  });
});

function selectTab(tab) {
  tabs.forEach(t => {
    t.setAttribute('aria-selected', 'false');
    t.setAttribute('tabindex', '-1');
  });
  tab.setAttribute('aria-selected', 'true');
  tab.setAttribute('tabindex', '0');
  tab.focus();
}
</script>
```

### Menu Navigation

```html
<button 
  aria-haspopup="menu" 
  aria-expanded="false"
  aria-controls="menu"
>
  Options
</button>
<ul role="menu" id="menu" hidden>
  <li role="menuitem" tabindex="-1">Edit</li>
  <li role="menuitem" tabindex="-1">Duplicate</li>
  <li role="menuitem" tabindex="-1">Delete</li>
</ul>

<script>
const menuButton = document.querySelector('[aria-haspopup="menu"]');
const menu = document.getElementById('menu');
const menuItems = menu.querySelectorAll('[role="menuitem"]');

menuButton.addEventListener('keydown', (e) => {
  if (e.key === 'ArrowDown' || e.key === 'Enter' || e.key === ' ') {
    e.preventDefault();
    openMenu();
    menuItems[0].focus();
  }
});

menu.addEventListener('keydown', (e) => {
  const currentIndex = Array.from(menuItems).indexOf(document.activeElement);
  
  switch (e.key) {
    case 'ArrowDown':
      e.preventDefault();
      menuItems[(currentIndex + 1) % menuItems.length].focus();
      break;
    case 'ArrowUp':
      e.preventDefault();
      menuItems[(currentIndex - 1 + menuItems.length) % menuItems.length].focus();
      break;
    case 'Escape':
      closeMenu();
      menuButton.focus();
      break;
    case 'Tab':
      closeMenu();
      break;
  }
});
</script>
```

### Listbox Navigation

```html
<label id="color-label">Choose color:</label>
<ul 
  role="listbox" 
  tabindex="0"
  aria-labelledby="color-label"
  aria-activedescendant="color-red"
>
  <li role="option" id="color-red" aria-selected="true">Red</li>
  <li role="option" id="color-blue" aria-selected="false">Blue</li>
  <li role="option" id="color-green" aria-selected="false">Green</li>
</ul>

<script>
const listbox = document.querySelector('[role="listbox"]');
const options = listbox.querySelectorAll('[role="option"]');

listbox.addEventListener('keydown', (e) => {
  const currentId = listbox.getAttribute('aria-activedescendant');
  const current = document.getElementById(currentId);
  const currentIndex = Array.from(options).indexOf(current);
  let newIndex = currentIndex;
  
  switch (e.key) {
    case 'ArrowDown':
      newIndex = Math.min(currentIndex + 1, options.length - 1);
      break;
    case 'ArrowUp':
      newIndex = Math.max(currentIndex - 1, 0);
      break;
    case 'Home':
      newIndex = 0;
      break;
    case 'End':
      newIndex = options.length - 1;
      break;
    case 'Enter':
    case ' ':
      selectOption(options[currentIndex]);
      return;
    default:
      return;
  }
  
  e.preventDefault();
  listbox.setAttribute('aria-activedescendant', options[newIndex].id);
  options.forEach(o => o.classList.remove('focused'));
  options[newIndex].classList.add('focused');
});
</script>
```

## Roving Tabindex

For composite widgets, only one element is in tab order at a time.

```html
<div role="toolbar" aria-label="Text formatting">
  <button tabindex="0">Bold</button>
  <button tabindex="-1">Italic</button>
  <button tabindex="-1">Underline</button>
</div>

<script>
const toolbar = document.querySelector('[role="toolbar"]');
const buttons = toolbar.querySelectorAll('button');

toolbar.addEventListener('keydown', (e) => {
  const current = document.activeElement;
  const index = Array.from(buttons).indexOf(current);
  let newIndex = index;
  
  switch (e.key) {
    case 'ArrowRight':
      newIndex = (index + 1) % buttons.length;
      break;
    case 'ArrowLeft':
      newIndex = (index - 1 + buttons.length) % buttons.length;
      break;
    default:
      return;
  }
  
  e.preventDefault();
  
  // Update tabindex
  buttons[index].setAttribute('tabindex', '-1');
  buttons[newIndex].setAttribute('tabindex', '0');
  buttons[newIndex].focus();
});
</script>
```

## Keyboard Shortcuts

```html
<script>
document.addEventListener('keydown', (e) => {
  // Check for modifier keys
  const isCtrl = e.ctrlKey || e.metaKey;
  const isShift = e.shiftKey;
  
  // Global shortcuts
  if (isCtrl && e.key === 'k') {
    e.preventDefault();
    openSearch();
  }
  
  if (e.key === '?' && !isInputFocused()) {
    openHelp();
  }
  
  // Escape to close
  if (e.key === 'Escape') {
    closeModal();
  }
});

function isInputFocused() {
  const active = document.activeElement;
  return active.tagName === 'INPUT' || 
         active.tagName === 'TEXTAREA' ||
         active.isContentEditable;
}
</script>

<!-- Document keyboard shortcuts -->
<div class="keyboard-help" hidden>
  <h2>Keyboard Shortcuts</h2>
  <dl>
    <dt><kbd>Ctrl</kbd> + <kbd>K</kbd></dt>
    <dd>Open search</dd>
    <dt><kbd>?</kbd></dt>
    <dd>Show keyboard shortcuts</dd>
    <dt><kbd>Esc</kbd></dt>
    <dd>Close dialog</dd>
  </dl>
</div>
```

## Testing Keyboard Navigation

```javascript
// Automated keyboard testing
function testKeyboardNavigation() {
  const focusableSelector = 
    'a[href], button, input, select, textarea, [tabindex]:not([tabindex="-1"])';
  
  const focusable = document.querySelectorAll(focusableSelector);
  const issues = [];
  
  focusable.forEach(el => {
    // Check for visible focus indicator
    el.focus();
    const style = getComputedStyle(el);
    const hasOutline = style.outline !== 'none' && style.outline !== '';
    const hasBoxShadow = style.boxShadow !== 'none';
    
    if (!hasOutline && !hasBoxShadow) {
      issues.push({
        element: el,
        issue: 'No visible focus indicator'
      });
    }
    
    // Check for custom widgets without keyboard handlers
    if (el.hasAttribute('role') && el.onclick && !el.onkeydown) {
      issues.push({
        element: el,
        issue: 'Custom widget without keyboard handler'
      });
    }
  });
  
  return issues;
}
```

## Summary

| Requirement | Implementation |
|-------------|----------------|
| All interactive elements focusable | Use native elements or tabindex="0" |
| Logical tab order | Follow DOM order, avoid tabindex > 0 |
| Visible focus indicator | CSS :focus styles |
| Arrow key navigation | For composite widgets |
| Enter/Space activation | Keyboard handlers for custom widgets |
| Escape to close | Modal, dropdown, menu |
| No keyboard traps | Can always tab away |
