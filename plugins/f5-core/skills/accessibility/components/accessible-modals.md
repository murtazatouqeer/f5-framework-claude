---
name: accessible-modals
description: Creating accessible modal dialogs
category: accessibility/components
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# Accessible Modals

## Overview

Modal dialogs require careful attention to accessibility. They must manage focus, trap keyboard navigation, and communicate their purpose to assistive technology.

## Basic Structure

### Accessible Modal HTML

```html
<!-- Trigger button -->
<button 
  type="button" 
  id="open-modal"
  aria-haspopup="dialog"
>
  Open Settings
</button>

<!-- Modal dialog -->
<div 
  id="settings-modal"
  role="dialog"
  aria-modal="true"
  aria-labelledby="modal-title"
  aria-describedby="modal-description"
  hidden
>
  <div class="modal-content">
    <header class="modal-header">
      <h2 id="modal-title">Settings</h2>
      <button 
        type="button" 
        class="close-button"
        aria-label="Close settings"
      >
        ×
      </button>
    </header>
    
    <div class="modal-body">
      <p id="modal-description">
        Configure your application preferences below.
      </p>
      <!-- Modal content -->
    </div>
    
    <footer class="modal-actions">
      <button type="button" class="btn-secondary">Cancel</button>
      <button type="button" class="btn-primary">Save Changes</button>
    </footer>
  </div>
</div>

<!-- Backdrop -->
<div class="modal-backdrop" hidden></div>
```

## Dialog Types

### Modal vs Non-modal

```html
<!-- Modal: Blocks interaction with rest of page -->
<div 
  role="dialog" 
  aria-modal="true"
  aria-labelledby="modal-title"
>
  <!-- Content -->
</div>

<!-- Non-modal: Allows interaction with page -->
<div 
  role="dialog" 
  aria-modal="false"
  aria-labelledby="dialog-title"
>
  <!-- Content -->
</div>
```

### Alert Dialog

```html
<!-- Alert dialog for confirmations -->
<div 
  role="alertdialog"
  aria-modal="true"
  aria-labelledby="alert-title"
  aria-describedby="alert-description"
>
  <h2 id="alert-title">Delete Account?</h2>
  <p id="alert-description">
    This action cannot be undone. All your data will be permanently deleted.
  </p>
  <div class="dialog-actions">
    <button type="button">Cancel</button>
    <button type="button" class="danger">Delete</button>
  </div>
</div>
```

## Focus Management

### Focus Trap Implementation

```javascript
class FocusTrap {
  constructor(container) {
    this.container = container;
    this.focusableElements = this.getFocusableElements();
    this.firstElement = this.focusableElements[0];
    this.lastElement = this.focusableElements[this.focusableElements.length - 1];
  }
  
  getFocusableElements() {
    const selector = `
      a[href],
      button:not([disabled]),
      input:not([disabled]),
      select:not([disabled]),
      textarea:not([disabled]),
      [tabindex]:not([tabindex="-1"])
    `;
    return this.container.querySelectorAll(selector);
  }
  
  handleKeydown(event) {
    if (event.key !== 'Tab') return;
    
    if (event.shiftKey) {
      // Shift + Tab
      if (document.activeElement === this.firstElement) {
        event.preventDefault();
        this.lastElement.focus();
      }
    } else {
      // Tab
      if (document.activeElement === this.lastElement) {
        event.preventDefault();
        this.firstElement.focus();
      }
    }
  }
  
  activate() {
    this.firstElement.focus();
    this.container.addEventListener('keydown', (e) => this.handleKeydown(e));
  }
  
  deactivate() {
    this.container.removeEventListener('keydown', this.handleKeydown);
  }
}
```

### Complete Modal Controller

```javascript
class AccessibleModal {
  constructor(modalId, triggerId) {
    this.modal = document.getElementById(modalId);
    this.trigger = document.getElementById(triggerId);
    this.backdrop = document.querySelector('.modal-backdrop');
    this.closeButton = this.modal.querySelector('.close-button');
    this.previouslyFocused = null;
    this.focusTrap = new FocusTrap(this.modal);
    
    this.bindEvents();
  }
  
  bindEvents() {
    // Open modal
    this.trigger.addEventListener('click', () => this.open());
    
    // Close buttons
    this.closeButton.addEventListener('click', () => this.close());
    this.modal.querySelectorAll('[data-close-modal]').forEach(btn => {
      btn.addEventListener('click', () => this.close());
    });
    
    // Escape key
    this.modal.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') this.close();
    });
    
    // Click outside
    this.backdrop.addEventListener('click', () => this.close());
  }
  
  open() {
    // Store current focus
    this.previouslyFocused = document.activeElement;
    
    // Show modal
    this.modal.hidden = false;
    this.backdrop.hidden = false;
    
    // Prevent body scroll
    document.body.style.overflow = 'hidden';
    
    // Hide rest of page from screen readers
    document.getElementById('app').setAttribute('aria-hidden', 'true');
    
    // Activate focus trap
    this.focusTrap.activate();
  }
  
  close() {
    // Hide modal
    this.modal.hidden = true;
    this.backdrop.hidden = true;
    
    // Restore body scroll
    document.body.style.overflow = '';
    
    // Restore screen reader access
    document.getElementById('app').removeAttribute('aria-hidden');
    
    // Deactivate focus trap
    this.focusTrap.deactivate();
    
    // Return focus to trigger
    if (this.previouslyFocused) {
      this.previouslyFocused.focus();
    }
  }
}

// Initialize
const settingsModal = new AccessibleModal('settings-modal', 'open-modal');
```

## HTML dialog Element

### Native Dialog

```html
<button onclick="document.getElementById('native-dialog').showModal()">
  Open Dialog
</button>

<dialog id="native-dialog" aria-labelledby="dialog-heading">
  <h2 id="dialog-heading">Native Dialog</h2>
  <p>This is a native HTML dialog element.</p>
  <form method="dialog">
    <button value="cancel">Cancel</button>
    <button value="confirm">Confirm</button>
  </form>
</dialog>
```

### Styling Native Dialog

```css
dialog {
  border: none;
  border-radius: 8px;
  padding: 0;
  max-width: 500px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

dialog::backdrop {
  background: rgba(0, 0, 0, 0.5);
}

dialog:focus {
  outline: none;
}

dialog[open] {
  animation: fadeIn 200ms ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
```

### Dialog with Focus Management

```javascript
const dialog = document.getElementById('native-dialog');
let previouslyFocused;

function openDialog() {
  previouslyFocused = document.activeElement;
  dialog.showModal();
  
  // Focus first interactive element
  const firstFocusable = dialog.querySelector('button, input, select');
  if (firstFocusable) {
    firstFocusable.focus();
  }
}

dialog.addEventListener('close', () => {
  if (previouslyFocused) {
    previouslyFocused.focus();
  }
});
```

## Keyboard Navigation

### Expected Behavior

| Key | Action |
|-----|--------|
| Tab | Move to next focusable element |
| Shift+Tab | Move to previous focusable element |
| Escape | Close the modal |
| Enter | Activate focused button |

### Implementation

```javascript
modal.addEventListener('keydown', (event) => {
  switch(event.key) {
    case 'Escape':
      closeModal();
      break;
    case 'Tab':
      handleTabKey(event);
      break;
  }
});

function handleTabKey(event) {
  const focusable = modal.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );
  const first = focusable[0];
  const last = focusable[focusable.length - 1];
  
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault();
    last.focus();
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault();
    first.focus();
  }
}
```

## Screen Reader Considerations

### ARIA Attributes

```html
<div 
  role="dialog"
  aria-modal="true"
  aria-labelledby="modal-title"
  aria-describedby="modal-description"
>
  <!-- ... -->
</div>
```

| Attribute | Purpose |
|-----------|---------|
| `role="dialog"` | Identifies as dialog |
| `aria-modal="true"` | Indicates modal behavior |
| `aria-labelledby` | Links to title |
| `aria-describedby` | Links to description |
| `aria-hidden` | Hide background content |

### Hiding Background

```javascript
function openModal() {
  // Hide all siblings from screen readers
  const app = document.getElementById('app');
  app.setAttribute('aria-hidden', 'true');
  app.setAttribute('inert', '');  // Also prevents interaction
  
  modal.hidden = false;
}

function closeModal() {
  const app = document.getElementById('app');
  app.removeAttribute('aria-hidden');
  app.removeAttribute('inert');
  
  modal.hidden = true;
}
```

## Common Modal Patterns

### Confirmation Dialog

```html
<div role="alertdialog" aria-modal="true" aria-labelledby="confirm-title">
  <h2 id="confirm-title">Confirm Deletion</h2>
  <p>Are you sure you want to delete this item?</p>
  <div class="dialog-actions">
    <button type="button" data-close-modal>Cancel</button>
    <button type="button" class="danger" autofocus>Delete</button>
  </div>
</div>
```

### Form Modal

```html
<div role="dialog" aria-modal="true" aria-labelledby="form-title">
  <h2 id="form-title">Edit Profile</h2>
  
  <form id="profile-form">
    <div class="form-group">
      <label for="display-name">Display Name</label>
      <input type="text" id="display-name" required>
    </div>
    
    <div class="form-group">
      <label for="bio">Bio</label>
      <textarea id="bio"></textarea>
    </div>
    
    <div class="dialog-actions">
      <button type="button" data-close-modal>Cancel</button>
      <button type="submit">Save</button>
    </div>
  </form>
</div>
```

### Loading Modal

```html
<div 
  role="dialog" 
  aria-modal="true" 
  aria-labelledby="loading-title"
  aria-busy="true"
>
  <h2 id="loading-title" class="visually-hidden">Loading</h2>
  <div class="spinner" aria-hidden="true"></div>
  <p aria-live="polite">Processing your request...</p>
</div>
```

## CSS Styles

```css
/* Modal container */
.modal {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

/* Modal content */
.modal-content {
  background: white;
  border-radius: 8px;
  max-width: 500px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

/* Backdrop */
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 999;
}

/* Focus styles */
.modal-content:focus {
  outline: none;
}

.modal button:focus-visible,
.modal input:focus-visible {
  outline: 2px solid #005fcc;
  outline-offset: 2px;
}

/* Animations */
.modal[hidden] {
  display: none;
}

.modal:not([hidden]) {
  animation: fadeIn 200ms ease-out;
}

.modal-content {
  animation: slideIn 200ms ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideIn {
  from { transform: translateY(-20px); }
  to { transform: translateY(0); }
}

/* Reduce motion */
@media (prefers-reduced-motion: reduce) {
  .modal,
  .modal-content {
    animation: none;
  }
}
```

## React Example

```jsx
import { useEffect, useRef, useCallback } from 'react';

function Modal({ isOpen, onClose, title, children }) {
  const modalRef = useRef(null);
  const previousFocusRef = useRef(null);
  
  const handleKeyDown = useCallback((event) => {
    if (event.key === 'Escape') {
      onClose();
    }
  }, [onClose]);
  
  useEffect(() => {
    if (isOpen) {
      previousFocusRef.current = document.activeElement;
      modalRef.current?.focus();
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
      previousFocusRef.current?.focus();
    }
    
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);
  
  if (!isOpen) return null;
  
  return (
    <>
      <div className="modal-backdrop" onClick={onClose} />
      <div
        ref={modalRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
        tabIndex={-1}
        onKeyDown={handleKeyDown}
        className="modal"
      >
        <div className="modal-content">
          <header className="modal-header">
            <h2 id="modal-title">{title}</h2>
            <button
              type="button"
              onClick={onClose}
              aria-label="Close"
            >
              ×
            </button>
          </header>
          <div className="modal-body">
            {children}
          </div>
        </div>
      </div>
    </>
  );
}

// Usage
function App() {
  const [isOpen, setIsOpen] = useState(false);
  
  return (
    <>
      <button onClick={() => setIsOpen(true)}>
        Open Modal
      </button>
      
      <Modal
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        title="Settings"
      >
        <p>Modal content here</p>
      </Modal>
    </>
  );
}
```

## Testing Checklist

```markdown
## Modal Accessibility Checklist

### Focus Management
- [ ] Focus moves to modal on open
- [ ] Focus is trapped within modal
- [ ] Focus returns to trigger on close
- [ ] Tab cycles through focusable elements
- [ ] Shift+Tab works in reverse

### Keyboard
- [ ] Escape closes modal
- [ ] Tab navigation works
- [ ] Enter activates buttons

### Screen Reader
- [ ] Modal role announced
- [ ] Title announced
- [ ] Description announced (if present)
- [ ] Background content hidden

### Visual
- [ ] Focus indicator visible
- [ ] Modal visually above content
- [ ] Close button accessible
- [ ] Backdrop indicates modal state

### Behavior
- [ ] Body scroll prevented
- [ ] Click outside closes (if appropriate)
- [ ] Animation respects prefers-reduced-motion
```

## Summary

| Requirement | Implementation |
|-------------|----------------|
| Role | `role="dialog"` or `role="alertdialog"` |
| Modal behavior | `aria-modal="true"` |
| Title | `aria-labelledby` pointing to heading |
| Focus trap | JavaScript focus management |
| Close | Escape key + close button |
| Background | `aria-hidden="true"` on page content |
| Return focus | Focus trigger on close |
