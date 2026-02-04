---
name: accessible-forms
description: Creating accessible form components
category: accessibility/components
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# Accessible Forms

## Overview

Forms are critical for user interaction. Accessible forms ensure all users can provide input, understand requirements, and recover from errors.

## Form Structure

### Basic Accessible Form

```html
<form action="/submit" method="post">
  <h2>Contact Form</h2>
  
  <div class="form-group">
    <label for="name">Full Name</label>
    <input 
      type="text" 
      id="name" 
      name="name"
      required
      autocomplete="name"
    >
  </div>
  
  <div class="form-group">
    <label for="email">Email Address</label>
    <input 
      type="email" 
      id="email" 
      name="email"
      required
      autocomplete="email"
    >
  </div>
  
  <div class="form-group">
    <label for="message">Message</label>
    <textarea 
      id="message" 
      name="message"
      required
    ></textarea>
  </div>
  
  <button type="submit">Send Message</button>
</form>
```

## Labels

### Explicit Labels (Preferred)

```html
<!-- Explicit association with for/id -->
<label for="email">Email Address</label>
<input type="email" id="email" name="email">
```

### Implicit Labels

```html
<!-- Implicit by wrapping (less reliable) -->
<label>
  Email Address
  <input type="email" name="email">
</label>
```

### Hidden Labels

```html
<!-- Visually hidden but accessible -->
<label for="search" class="visually-hidden">
  Search products
</label>
<input type="search" id="search" placeholder="Search...">
<button type="submit">Search</button>
```

### aria-label Alternative

```html
<!-- When label element not practical -->
<input 
  type="search" 
  aria-label="Search products"
  placeholder="Search..."
>
```

## Required Fields

### Marking Required Fields

```html
<!-- Visual indicator + programmatic -->
<label for="email">
  Email Address 
  <span aria-hidden="true">*</span>
</label>
<input 
  type="email" 
  id="email" 
  name="email"
  required
  aria-required="true"
>

<!-- Legend explaining asterisk -->
<p class="form-legend">
  <span aria-hidden="true">*</span> Required fields
</p>
```

### Better: Indicate Optional

```html
<!-- Mark optional instead of required -->
<label for="phone">
  Phone Number 
  <span class="optional">(optional)</span>
</label>
<input type="tel" id="phone" name="phone">
```

## Input Types

### Correct Input Types

```html
<!-- Email validation -->
<input type="email" id="email" autocomplete="email">

<!-- Phone with pattern -->
<input 
  type="tel" 
  id="phone" 
  autocomplete="tel"
  pattern="[0-9]{3}-[0-9]{3}-[0-9]{4}"
>

<!-- URL validation -->
<input type="url" id="website" autocomplete="url">

<!-- Number with constraints -->
<input 
  type="number" 
  id="quantity" 
  min="1" 
  max="100"
  step="1"
>

<!-- Date -->
<input type="date" id="birthday" autocomplete="bday">

<!-- Password with requirements -->
<input 
  type="password" 
  id="password"
  autocomplete="new-password"
  minlength="8"
  aria-describedby="password-requirements"
>
<p id="password-requirements">
  Password must be at least 8 characters
</p>
```

## Fieldsets and Legends

### Grouping Related Fields

```html
<fieldset>
  <legend>Shipping Address</legend>
  
  <div class="form-group">
    <label for="street">Street Address</label>
    <input type="text" id="street" autocomplete="street-address">
  </div>
  
  <div class="form-group">
    <label for="city">City</label>
    <input type="text" id="city" autocomplete="address-level2">
  </div>
  
  <div class="form-group">
    <label for="zip">ZIP Code</label>
    <input type="text" id="zip" autocomplete="postal-code">
  </div>
</fieldset>
```

### Radio Button Groups

```html
<fieldset>
  <legend>Preferred Contact Method</legend>
  
  <div class="radio-group">
    <input type="radio" id="contact-email" name="contact" value="email">
    <label for="contact-email">Email</label>
  </div>
  
  <div class="radio-group">
    <input type="radio" id="contact-phone" name="contact" value="phone">
    <label for="contact-phone">Phone</label>
  </div>
  
  <div class="radio-group">
    <input type="radio" id="contact-mail" name="contact" value="mail">
    <label for="contact-mail">Mail</label>
  </div>
</fieldset>
```

### Checkbox Groups

```html
<fieldset>
  <legend>Notification Preferences</legend>
  
  <div class="checkbox-group">
    <input type="checkbox" id="news" name="prefs" value="news">
    <label for="news">Newsletter</label>
  </div>
  
  <div class="checkbox-group">
    <input type="checkbox" id="updates" name="prefs" value="updates">
    <label for="updates">Product Updates</label>
  </div>
  
  <div class="checkbox-group">
    <input type="checkbox" id="offers" name="prefs" value="offers">
    <label for="offers">Special Offers</label>
  </div>
</fieldset>
```

## Help Text and Instructions

### Descriptions

```html
<div class="form-group">
  <label for="username">Username</label>
  <input 
    type="text" 
    id="username" 
    name="username"
    aria-describedby="username-help"
  >
  <p id="username-help" class="help-text">
    3-20 characters, letters and numbers only
  </p>
</div>
```

### Multiple Descriptions

```html
<div class="form-group">
  <label for="password">Password</label>
  <input 
    type="password" 
    id="password"
    aria-describedby="password-help password-requirements"
  >
  <p id="password-help" class="help-text">
    Create a strong password
  </p>
  <ul id="password-requirements" class="requirements">
    <li>At least 8 characters</li>
    <li>Include uppercase and lowercase</li>
    <li>Include a number</li>
  </ul>
</div>
```

## Error Handling

### Inline Errors

```html
<div class="form-group has-error">
  <label for="email">Email Address</label>
  <input 
    type="email" 
    id="email" 
    name="email"
    aria-invalid="true"
    aria-describedby="email-error"
    value="invalid-email"
  >
  <p id="email-error" class="error-message" role="alert">
    Please enter a valid email address
  </p>
</div>
```

### Error Summary

```html
<div role="alert" aria-labelledby="error-summary-title">
  <h2 id="error-summary-title">
    There were 2 errors with your submission
  </h2>
  <ul>
    <li>
      <a href="#email">Email address is required</a>
    </li>
    <li>
      <a href="#password">Password must be at least 8 characters</a>
    </li>
  </ul>
</div>
```

### Real-time Validation

```html
<div class="form-group">
  <label for="email">Email Address</label>
  <input 
    type="email" 
    id="email"
    aria-describedby="email-status"
  >
  <p id="email-status" aria-live="polite" class="validation-status">
    <!-- Populated by JavaScript -->
  </p>
</div>

<script>
const email = document.getElementById('email');
const status = document.getElementById('email-status');

email.addEventListener('blur', () => {
  if (email.validity.typeMismatch) {
    email.setAttribute('aria-invalid', 'true');
    status.textContent = 'Please enter a valid email address';
    status.className = 'validation-status error';
  } else if (email.value) {
    email.setAttribute('aria-invalid', 'false');
    status.textContent = 'Email format is valid';
    status.className = 'validation-status success';
  }
});
</script>
```

## Select Elements

### Native Select

```html
<div class="form-group">
  <label for="country">Country</label>
  <select id="country" name="country" autocomplete="country">
    <option value="">Select a country</option>
    <option value="us">United States</option>
    <option value="ca">Canada</option>
    <option value="uk">United Kingdom</option>
  </select>
</div>
```

### Grouped Options

```html
<div class="form-group">
  <label for="timezone">Time Zone</label>
  <select id="timezone" name="timezone">
    <optgroup label="North America">
      <option value="est">Eastern Time</option>
      <option value="cst">Central Time</option>
      <option value="pst">Pacific Time</option>
    </optgroup>
    <optgroup label="Europe">
      <option value="gmt">GMT</option>
      <option value="cet">Central European Time</option>
    </optgroup>
  </select>
</div>
```

## Custom Controls

### Custom Checkbox

```html
<div class="custom-checkbox">
  <input 
    type="checkbox" 
    id="terms" 
    name="terms"
    class="visually-hidden"
  >
  <label for="terms">
    <span class="checkbox-visual" aria-hidden="true"></span>
    I agree to the terms and conditions
  </label>
</div>
```

```css
.custom-checkbox input:focus + label .checkbox-visual {
  outline: 2px solid #005fcc;
  outline-offset: 2px;
}

.custom-checkbox input:checked + label .checkbox-visual::after {
  content: '✓';
}
```

### Custom Radio

```html
<div class="custom-radio">
  <input 
    type="radio" 
    id="plan-basic" 
    name="plan" 
    value="basic"
    class="visually-hidden"
  >
  <label for="plan-basic">
    <span class="radio-visual" aria-hidden="true"></span>
    Basic Plan - $9/month
  </label>
</div>
```

## Autocomplete

### Common Autocomplete Values

| Field | autocomplete |
|-------|--------------|
| Full name | `name` |
| Email | `email` |
| Phone | `tel` |
| Street address | `street-address` |
| City | `address-level2` |
| State/Province | `address-level1` |
| ZIP/Postal | `postal-code` |
| Country | `country` |
| Credit card number | `cc-number` |
| Expiration | `cc-exp` |
| CVV | `cc-csc` |
| Username | `username` |
| Current password | `current-password` |
| New password | `new-password` |

```html
<input 
  type="text" 
  id="name" 
  autocomplete="name"
>
```

## Focus Management

### Focus on Error

```javascript
function validateForm(form) {
  const firstError = form.querySelector('[aria-invalid="true"]');
  
  if (firstError) {
    // Move focus to first error
    firstError.focus();
    
    // Or focus error summary
    document.getElementById('error-summary').focus();
    return false;
  }
  
  return true;
}
```

### Multi-step Forms

```html
<div role="group" aria-labelledby="step-indicator">
  <p id="step-indicator">Step 2 of 3: Shipping Information</p>
  
  <!-- Form fields -->
  
  <div class="form-actions">
    <button type="button" onclick="previousStep()">Previous</button>
    <button type="button" onclick="nextStep()">Next</button>
  </div>
</div>
```

## CSS Considerations

```css
/* Ensure focus visibility */
input:focus,
select:focus,
textarea:focus {
  outline: 2px solid #005fcc;
  outline-offset: 2px;
}

/* Error state styling */
input[aria-invalid="true"] {
  border-color: #d32f2f;
}

/* Error message styling */
.error-message {
  color: #d32f2f;
  font-size: 0.875rem;
  margin-top: 0.25rem;
}

/* Required indicator */
.required::after {
  content: " *";
  color: #d32f2f;
}

/* Disabled state */
input:disabled,
select:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Touch target size */
input,
select {
  min-height: 44px;
  padding: 0.5rem;
}
```

## Testing Checklist

```markdown
## Form Accessibility Checklist

### Labels
- [ ] All inputs have labels
- [ ] Labels properly associated (for/id)
- [ ] Labels visible or accessible

### Structure
- [ ] Related fields grouped with fieldset/legend
- [ ] Logical tab order
- [ ] Fieldsets for radio/checkbox groups

### Instructions
- [ ] Required fields indicated
- [ ] Format hints provided
- [ ] Instructions before inputs

### Errors
- [ ] Errors associated with fields
- [ ] Error summary available
- [ ] Errors announced to screen readers
- [ ] Focus moves to error

### Keyboard
- [ ] All inputs reachable by Tab
- [ ] Custom controls keyboard accessible
- [ ] Focus visible on all elements

### Autocomplete
- [ ] Correct autocomplete values
- [ ] Browser autofill works
```

## Summary

| Requirement | Implementation |
|-------------|----------------|
| Labels | Explicit `<label for="id">` |
| Required | `required` + visual indicator |
| Grouping | `<fieldset>` + `<legend>` |
| Help text | `aria-describedby` |
| Errors | `aria-invalid` + `role="alert"` |
| Focus | Visible indicator, logical order |
| Autocomplete | Correct `autocomplete` values |
