# Accessible Components Reference

## Forms

### Accessible Form Pattern

```html
<form aria-labelledby="form-title">
  <h2 id="form-title">Contact Form</h2>

  <!-- Text input with label -->
  <div class="field">
    <label for="name">Name <span aria-hidden="true">*</span></label>
    <input
      type="text"
      id="name"
      name="name"
      required
      aria-required="true"
      autocomplete="name"
    >
  </div>

  <!-- Email with description -->
  <div class="field">
    <label for="email">Email</label>
    <input
      type="email"
      id="email"
      aria-describedby="email-hint"
      autocomplete="email"
    >
    <span id="email-hint">We'll never share your email</span>
  </div>

  <!-- Select -->
  <div class="field">
    <label for="topic">Topic</label>
    <select id="topic" name="topic">
      <option value="">Select a topic</option>
      <option value="support">Support</option>
      <option value="sales">Sales</option>
    </select>
  </div>

  <!-- Checkbox group -->
  <fieldset>
    <legend>Interests</legend>
    <label><input type="checkbox" name="interests" value="news"> News</label>
    <label><input type="checkbox" name="interests" value="updates"> Updates</label>
  </fieldset>

  <!-- Radio group -->
  <fieldset>
    <legend>Preferred contact method</legend>
    <label><input type="radio" name="contact" value="email"> Email</label>
    <label><input type="radio" name="contact" value="phone"> Phone</label>
  </fieldset>

  <button type="submit">Submit</button>
</form>
```

### Error Handling

```html
<div class="field error">
  <label for="email">Email</label>
  <input
    type="email"
    id="email"
    aria-invalid="true"
    aria-describedby="email-error"
  >
  <span id="email-error" role="alert">
    Please enter a valid email address
  </span>
</div>
```

## Modal Dialog

```html
<div
  role="dialog"
  aria-modal="true"
  aria-labelledby="modal-title"
  aria-describedby="modal-desc"
>
  <h2 id="modal-title">Confirm Delete</h2>
  <p id="modal-desc">Are you sure you want to delete this item?</p>

  <div class="modal-actions">
    <button onclick="closeModal()">Cancel</button>
    <button onclick="confirmDelete()">Delete</button>
  </div>

  <button
    aria-label="Close"
    class="close-btn"
    onclick="closeModal()"
  >×</button>
</div>
```

### Focus Management

```typescript
class Modal {
  private previousFocus: HTMLElement | null = null;
  private modal: HTMLElement;

  open() {
    this.previousFocus = document.activeElement as HTMLElement;
    this.modal.hidden = false;

    // Focus first focusable element
    const focusable = this.modal.querySelector<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    focusable?.focus();

    // Trap focus
    this.modal.addEventListener('keydown', this.trapFocus);
  }

  close() {
    this.modal.hidden = true;
    this.previousFocus?.focus();
  }

  private trapFocus = (e: KeyboardEvent) => {
    if (e.key !== 'Tab') return;

    const focusables = this.modal.querySelectorAll<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    const first = focusables[0];
    const last = focusables[focusables.length - 1];

    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  };
}
```

## Tables

### Data Table

```html
<table>
  <caption>Monthly Sales Report</caption>
  <thead>
    <tr>
      <th scope="col">Month</th>
      <th scope="col">Revenue</th>
      <th scope="col">Growth</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th scope="row">January</th>
      <td>$10,000</td>
      <td>5%</td>
    </tr>
    <tr>
      <th scope="row">February</th>
      <td>$12,000</td>
      <td>20%</td>
    </tr>
  </tbody>
</table>
```

### Sortable Table Header

```html
<th scope="col">
  <button aria-sort="ascending">
    Date
    <span aria-hidden="true">▲</span>
  </button>
</th>
```

## Buttons

### Button Patterns

```html
<!-- Standard button -->
<button type="button">Click Me</button>

<!-- Icon button with label -->
<button aria-label="Delete item">
  <svg aria-hidden="true">...</svg>
</button>

<!-- Toggle button -->
<button aria-pressed="false" onclick="toggle(this)">
  Bold
</button>

<!-- Loading button -->
<button aria-busy="true" disabled>
  <span aria-hidden="true" class="spinner"></span>
  Loading...
</button>
```

### Button States

```css
/* Visible focus */
button:focus-visible {
  outline: 2px solid #005fcc;
  outline-offset: 2px;
}

/* Disabled state */
button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
```

## Navigation

### Skip Link

```html
<a href="#main-content" class="skip-link">
  Skip to main content
</a>

<nav aria-label="Main">...</nav>

<main id="main-content">
  <!-- Main content -->
</main>
```

```css
.skip-link {
  position: absolute;
  top: -40px;
  left: 0;
  background: #000;
  color: #fff;
  padding: 8px;
  z-index: 100;
}

.skip-link:focus {
  top: 0;
}
```

### Breadcrumbs

```html
<nav aria-label="Breadcrumb">
  <ol>
    <li><a href="/">Home</a></li>
    <li><a href="/products">Products</a></li>
    <li><a href="/products/shoes" aria-current="page">Shoes</a></li>
  </ol>
</nav>
```

## Visually Hidden Text

```css
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
```

```html
<button>
  <svg aria-hidden="true">...</svg>
  <span class="visually-hidden">Close menu</span>
</button>
```
