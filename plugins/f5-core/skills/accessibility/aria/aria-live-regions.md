---
name: aria-live-regions
description: ARIA live regions for announcing dynamic content
category: accessibility/aria
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# ARIA Live Regions

## Overview

Live regions announce dynamic content changes to screen readers. They're essential for SPAs, real-time updates, and any content that changes without page reload.

## Live Region Basics

```html
<!-- Polite: Waits for user to finish current task -->
<div aria-live="polite">
  <!-- Updates announced after current speech -->
</div>

<!-- Assertive: Interrupts immediately -->
<div aria-live="assertive">
  <!-- Updates announced immediately -->
</div>

<!-- Off: No announcements (default) -->
<div aria-live="off">
  <!-- Changes not announced -->
</div>
```

## When to Use Each Priority

| Priority | Use Case | Example |
|----------|----------|---------|
| `polite` | Non-urgent updates | Search results, status messages |
| `assertive` | Critical, time-sensitive | Errors, session expiring |
| `off` | Disable announcements | Pause live updates |

## Built-in Live Region Roles

### role="alert"

Assertive announcement for important messages.

```html
<!-- Error messages -->
<div role="alert">
  Error: Your session has expired. Please log in again.
</div>

<!-- Dynamic alert -->
<div id="alert-container" role="alert" aria-live="assertive"></div>

<script>
function showAlert(message) {
  const container = document.getElementById('alert-container');
  container.textContent = message;
}

// Usage
showAlert('Payment failed. Please try again.');
</script>
```

### role="status"

Polite announcement for status updates.

```html
<!-- Status messages -->
<div role="status">
  3 items added to cart
</div>

<!-- Loading indicator -->
<div role="status" aria-live="polite">
  Loading search results...
</div>

<!-- Form submission -->
<div role="status">
  Your message has been sent successfully.
</div>
```

### role="log"

For chat messages, activity feeds.

```html
<!-- Chat log -->
<div role="log" aria-label="Chat messages">
  <div>User: Hello!</div>
  <div>Support: Hi, how can I help?</div>
  <!-- New messages announced -->
</div>

<!-- Activity log -->
<div role="log" aria-label="Recent activity">
  <p>10:30 - File uploaded</p>
  <p>10:35 - File processed</p>
</div>
```

### role="marquee"

For non-essential, changing content.

```html
<!-- Stock ticker -->
<div role="marquee" aria-label="Stock prices">
  AAPL: $150.25 | GOOGL: $2,800.00 | MSFT: $300.50
</div>

<!-- News ticker -->
<div role="marquee" aria-label="Breaking news">
  Breaking: Important news headline...
</div>
```

### role="timer"

For countdown timers.

```html
<!-- Session timer -->
<div role="timer" aria-label="Session time remaining">
  05:00
</div>

<!-- Quiz timer -->
<div role="timer" aria-live="off" aria-label="Time remaining">
  <span id="minutes">10</span>:<span id="seconds">00</span>
</div>
<!-- Note: aria-live="off" to avoid constant announcements -->
```

## Live Region Attributes

### aria-atomic

Whether to announce entire region or just changes.

```html
<!-- Announce entire region on any change -->
<div aria-live="polite" aria-atomic="true">
  Cart total: $<span id="total">99.99</span>
</div>
<!-- Announces: "Cart total: $109.99" -->

<!-- Announce only changed content (default) -->
<div aria-live="polite" aria-atomic="false">
  Cart total: $<span id="total">99.99</span>
</div>
<!-- Announces: "109.99" -->
```

### aria-relevant

What types of changes to announce.

```html
<!-- Announce additions only (default) -->
<div aria-live="polite" aria-relevant="additions">
  <ul id="notifications">
    <!-- New items announced -->
  </ul>
</div>

<!-- Announce removals -->
<div aria-live="polite" aria-relevant="removals">
  <ul id="queue">
    <!-- Removed items announced -->
  </ul>
</div>

<!-- Announce text changes -->
<div aria-live="polite" aria-relevant="text">
  Status: <span id="status">Processing</span>
</div>

<!-- Announce all changes -->
<div aria-live="polite" aria-relevant="all">
  <!-- additions, removals, and text changes -->
</div>

<!-- Multiple values -->
<div aria-live="polite" aria-relevant="additions removals">
  <!-- Both additions and removals -->
</div>
```

### aria-busy

Suppress announcements while updating.

```html
<!-- While loading -->
<div 
  role="region" 
  aria-live="polite"
  aria-busy="true"
  aria-label="Search results"
>
  Loading results...
</div>

<!-- After loading complete -->
<div 
  role="region" 
  aria-live="polite"
  aria-busy="false"
  aria-label="Search results"
>
  <p>Found 25 results</p>
  <ul>
    <li>Result 1</li>
    <li>Result 2</li>
  </ul>
</div>

<script>
async function search(query) {
  const region = document.getElementById('results');
  
  // Start loading
  region.setAttribute('aria-busy', 'true');
  region.innerHTML = 'Loading...';
  
  // Fetch results
  const results = await fetchResults(query);
  
  // Update content
  region.innerHTML = renderResults(results);
  
  // Done loading - triggers announcement
  region.setAttribute('aria-busy', 'false');
}
</script>
```

## Common Patterns

### Form Validation

```html
<form>
  <div>
    <label for="email">Email</label>
    <input 
      type="email" 
      id="email"
      aria-describedby="email-error"
    >
    <!-- Error announced when populated -->
    <span id="email-error" role="alert" aria-live="assertive"></span>
  </div>
  
  <button type="submit">Submit</button>
  
  <!-- Success message -->
  <div role="status" id="form-status"></div>
</form>

<script>
function validateEmail(input) {
  const error = document.getElementById('email-error');
  
  if (!input.validity.valid) {
    error.textContent = 'Please enter a valid email address';
    input.setAttribute('aria-invalid', 'true');
  } else {
    error.textContent = '';
    input.removeAttribute('aria-invalid');
  }
}

function showSuccess() {
  document.getElementById('form-status').textContent = 
    'Form submitted successfully!';
}
</script>
```

### Shopping Cart

```html
<div id="cart-status" role="status" aria-live="polite" aria-atomic="true">
  Cart: <span id="cart-count">0</span> items
</div>

<script>
function updateCart(count) {
  document.getElementById('cart-count').textContent = count;
  // Entire region announced: "Cart: 3 items"
}
</script>
```

### Search Results

```html
<div id="search-region" aria-live="polite" aria-busy="false">
  <p id="result-count" role="status"></p>
  <ul id="results"></ul>
</div>

<script>
async function search(query) {
  const region = document.getElementById('search-region');
  const countEl = document.getElementById('result-count');
  const resultsEl = document.getElementById('results');
  
  region.setAttribute('aria-busy', 'true');
  
  const results = await fetchResults(query);
  
  resultsEl.innerHTML = results.map(r => `<li>${r.title}</li>`).join('');
  countEl.textContent = `Found ${results.length} results for "${query}"`;
  
  region.setAttribute('aria-busy', 'false');
}
</script>
```

### Toast Notifications

```html
<!-- Toast container -->
<div 
  id="toast-container"
  role="status"
  aria-live="polite"
  aria-atomic="true"
>
  <!-- Toasts inserted here -->
</div>

<script>
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  
  // For errors, use assertive
  if (type === 'error') {
    container.setAttribute('aria-live', 'assertive');
  }
  
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  
  container.appendChild(toast);
  
  // Remove after delay
  setTimeout(() => {
    toast.remove();
    container.setAttribute('aria-live', 'polite');
  }, 5000);
}
</script>
```

### Progress Updates

```html
<div 
  role="progressbar"
  aria-valuenow="0"
  aria-valuemin="0"
  aria-valuemax="100"
  aria-label="Upload progress"
>
  <div class="progress-fill"></div>
</div>

<!-- Status announcements -->
<div role="status" aria-live="polite" id="progress-status">
  Upload starting...
</div>

<script>
function updateProgress(percent) {
  const progressbar = document.querySelector('[role="progressbar"]');
  const status = document.getElementById('progress-status');
  
  progressbar.setAttribute('aria-valuenow', percent);
  
  // Announce at key milestones
  if (percent === 25) {
    status.textContent = '25% complete';
  } else if (percent === 50) {
    status.textContent = 'Halfway there!';
  } else if (percent === 100) {
    status.textContent = 'Upload complete!';
  }
}
</script>
```

### Character Counter

```html
<label for="bio">Bio</label>
<textarea id="bio" maxlength="200" aria-describedby="char-count"></textarea>
<div id="char-count" aria-live="polite">
  <span id="chars-remaining">200</span> characters remaining
</div>

<script>
const textarea = document.getElementById('bio');
const counter = document.getElementById('chars-remaining');

textarea.addEventListener('input', () => {
  const remaining = 200 - textarea.value.length;
  counter.textContent = remaining;
  
  // Warn when low
  if (remaining <= 20) {
    counter.parentElement.setAttribute('aria-live', 'assertive');
  }
});
</script>
```

## Best Practices

### Do's

```html
<!-- ✅ Use appropriate priority -->
<div role="status" aria-live="polite">
  Items saved
</div>

<!-- ✅ Keep messages concise -->
<div role="alert">
  Error: Invalid password
</div>

<!-- ✅ Use aria-busy for batch updates -->
<div aria-live="polite" aria-busy="true">
  <!-- Multiple updates happening -->
</div>
```

### Don'ts

```html
<!-- ❌ Too many live regions -->
<div aria-live="assertive">Region 1</div>
<div aria-live="assertive">Region 2</div>
<div aria-live="assertive">Region 3</div>

<!-- ❌ Constantly updating content -->
<div aria-live="polite">
  <!-- Timer updating every second -->
</div>

<!-- ❌ Using assertive for non-critical updates -->
<div aria-live="assertive">
  Your preference has been saved
</div>
```

## Summary

| Role/Attribute | Priority | Use Case |
|----------------|----------|----------|
| `role="alert"` | Assertive | Errors, critical warnings |
| `role="status"` | Polite | Status updates, success messages |
| `role="log"` | Polite | Chat, activity feeds |
| `aria-live="polite"` | Polite | Non-urgent updates |
| `aria-live="assertive"` | Assertive | Urgent, time-sensitive |
| `aria-atomic="true"` | - | Announce entire region |
| `aria-busy="true"` | - | Suppress during updates |
