---
name: forms
description: Creating accessible form controls and validation
category: accessibility/html
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# Accessible Forms

## Overview

Forms are critical interactive elements. Accessible forms ensure all users can input data, understand requirements, and recover from errors.

## Core Requirements

| Requirement | Implementation |
|-------------|----------------|
| Labels | Every input has associated label |
| Instructions | Clear guidance before form |
| Error messages | Specific, helpful error text |
| Focus management | Logical tab order |
| Grouping | Related fields grouped together |

## Labels

### Explicit Labels

```html
<!-- ✅ Explicit association with for/id -->
<label for="email">Email address</label>
<input type="email" id="email" name="email">

<!-- ✅ Wrapping label (implicit association) -->
<label>
  Email address
  <input type="email" name="email">
</label>
```

### Label Best Practices

```html
<!-- ✅ Descriptive labels -->
<label for="first-name">First name</label>
<input type="text" id="first-name" name="firstName">

<!-- ❌ Placeholder only (not a label) -->
<input type="text" placeholder="First name">

<!-- ❌ Title attribute only -->
<input type="text" title="First name">

<!-- ❌ Non-associated label -->
<label>Email</label>
<input type="email" id="user-email">
```

### Hidden Labels

```html
<!-- Visually hidden but accessible -->
<label for="search" class="visually-hidden">Search</label>
<input type="search" id="search" placeholder="Search...">
<button type="submit">
  <span class="visually-hidden">Submit search</span>
  <svg aria-hidden="true">...</svg>
</button>

<!-- Using aria-label -->
<input type="search" aria-label="Search products" placeholder="Search...">

<!-- Using aria-labelledby -->
<h2 id="search-heading">Product Search</h2>
<input type="search" aria-labelledby="search-heading" placeholder="Enter keywords...">
```

## Input Types

```html
<!-- Text inputs -->
<input type="text" id="name">
<input type="email" id="email">
<input type="tel" id="phone">
<input type="url" id="website">
<input type="password" id="password">
<input type="search" id="search">

<!-- Number inputs -->
<input type="number" id="quantity" min="1" max="100" step="1">
<input type="range" id="volume" min="0" max="100">

<!-- Date inputs -->
<input type="date" id="birthday">
<input type="time" id="appointment">
<input type="datetime-local" id="meeting">

<!-- Selection inputs -->
<input type="checkbox" id="agree">
<input type="radio" name="size" value="small" id="size-small">
<input type="file" id="upload" accept=".pdf,.doc">

<!-- Other -->
<input type="color" id="theme-color">
<input type="hidden" name="csrf" value="token">
```

## Form Structure

### Complete Form Example

```html
<form action="/register" method="POST" novalidate>
  <h1>Create Account</h1>
  <p>Fields marked with <span aria-hidden="true">*</span>
     <span class="visually-hidden">asterisk</span> are required.</p>
  
  <!-- Personal Information Group -->
  <fieldset>
    <legend>Personal Information</legend>
    
    <div class="form-group">
      <label for="first-name">
        First name <span aria-hidden="true">*</span>
      </label>
      <input 
        type="text" 
        id="first-name" 
        name="firstName"
        required
        aria-required="true"
        autocomplete="given-name"
      >
    </div>
    
    <div class="form-group">
      <label for="last-name">
        Last name <span aria-hidden="true">*</span>
      </label>
      <input 
        type="text" 
        id="last-name" 
        name="lastName"
        required
        aria-required="true"
        autocomplete="family-name"
      >
    </div>
    
    <div class="form-group">
      <label for="email">
        Email <span aria-hidden="true">*</span>
      </label>
      <input 
        type="email" 
        id="email" 
        name="email"
        required
        aria-required="true"
        aria-describedby="email-hint"
        autocomplete="email"
      >
      <span id="email-hint" class="hint">We'll never share your email.</span>
    </div>
  </fieldset>
  
  <!-- Account Security Group -->
  <fieldset>
    <legend>Account Security</legend>
    
    <div class="form-group">
      <label for="password">
        Password <span aria-hidden="true">*</span>
      </label>
      <input 
        type="password" 
        id="password" 
        name="password"
        required
        aria-required="true"
        aria-describedby="password-requirements"
        autocomplete="new-password"
        minlength="8"
      >
      <div id="password-requirements" class="hint">
        Must be at least 8 characters with one number and one symbol.
      </div>
    </div>
    
    <div class="form-group">
      <label for="confirm-password">
        Confirm password <span aria-hidden="true">*</span>
      </label>
      <input 
        type="password" 
        id="confirm-password" 
        name="confirmPassword"
        required
        aria-required="true"
        autocomplete="new-password"
      >
    </div>
  </fieldset>
  
  <!-- Preferences Group -->
  <fieldset>
    <legend>Communication Preferences</legend>
    
    <div class="checkbox-group">
      <input type="checkbox" id="newsletter" name="newsletter">
      <label for="newsletter">Send me the weekly newsletter</label>
    </div>
    
    <div class="checkbox-group">
      <input type="checkbox" id="updates" name="updates">
      <label for="updates">Notify me about product updates</label>
    </div>
  </fieldset>
  
  <!-- Terms -->
  <div class="form-group">
    <input 
      type="checkbox" 
      id="terms" 
      name="terms"
      required
      aria-required="true"
    >
    <label for="terms">
      I agree to the <a href="/terms">Terms of Service</a> 
      and <a href="/privacy">Privacy Policy</a>
      <span aria-hidden="true">*</span>
    </label>
  </div>
  
  <button type="submit">Create Account</button>
</form>
```

## Fieldsets and Legends

```html
<!-- Group related fields -->
<fieldset>
  <legend>Shipping Address</legend>
  
  <label for="street">Street address</label>
  <input type="text" id="street" name="street" autocomplete="street-address">
  
  <label for="city">City</label>
  <input type="text" id="city" name="city" autocomplete="address-level2">
  
  <label for="state">State</label>
  <select id="state" name="state" autocomplete="address-level1">
    <option value="">Select state</option>
    <option value="CA">California</option>
    <option value="NY">New York</option>
  </select>
  
  <label for="zip">ZIP code</label>
  <input type="text" id="zip" name="zip" autocomplete="postal-code" pattern="[0-9]{5}">
</fieldset>

<!-- Radio button groups -->
<fieldset>
  <legend>Select size</legend>
  
  <div>
    <input type="radio" id="size-s" name="size" value="small">
    <label for="size-s">Small</label>
  </div>
  <div>
    <input type="radio" id="size-m" name="size" value="medium">
    <label for="size-m">Medium</label>
  </div>
  <div>
    <input type="radio" id="size-l" name="size" value="large">
    <label for="size-l">Large</label>
  </div>
</fieldset>
```

## Error Handling

### Inline Errors

```html
<div class="form-group">
  <label for="email">Email</label>
  <input 
    type="email" 
    id="email" 
    name="email"
    aria-invalid="true"
    aria-describedby="email-error"
    class="error"
  >
  <span id="email-error" class="error-message" role="alert">
    Please enter a valid email address (e.g., name@example.com)
  </span>
</div>
```

### Error Summary

```html
<form>
  <!-- Error summary at top -->
  <div role="alert" aria-labelledby="error-summary-title" class="error-summary">
    <h2 id="error-summary-title">There are 2 errors in this form</h2>
    <ul>
      <li><a href="#email">Email: Please enter a valid email address</a></li>
      <li><a href="#password">Password: Must be at least 8 characters</a></li>
    </ul>
  </div>
  
  <!-- Form fields with errors -->
  <div class="form-group">
    <label for="email">Email</label>
    <input 
      type="email" 
      id="email"
      aria-invalid="true"
      aria-describedby="email-error"
    >
    <span id="email-error" class="error-message">
      Please enter a valid email address
    </span>
  </div>
</form>
```

### JavaScript Validation

```javascript
const form = document.querySelector('form');
const emailInput = document.getElementById('email');
const emailError = document.getElementById('email-error');

form.addEventListener('submit', (e) => {
  let hasErrors = false;
  const errors = [];
  
  // Validate email
  if (!emailInput.validity.valid) {
    hasErrors = true;
    emailInput.setAttribute('aria-invalid', 'true');
    emailError.textContent = getEmailErrorMessage(emailInput);
    errors.push({
      field: 'email',
      message: emailError.textContent
    });
  } else {
    emailInput.removeAttribute('aria-invalid');
    emailError.textContent = '';
  }
  
  if (hasErrors) {
    e.preventDefault();
    showErrorSummary(errors);
    // Focus first error field
    document.getElementById(errors[0].field).focus();
  }
});

function getEmailErrorMessage(input) {
  if (input.validity.valueMissing) {
    return 'Email is required';
  }
  if (input.validity.typeMismatch) {
    return 'Please enter a valid email address (e.g., name@example.com)';
  }
  return 'Invalid email';
}
```

## Select Elements

```html
<!-- Basic select -->
<label for="country">Country</label>
<select id="country" name="country">
  <option value="">Select a country</option>
  <option value="us">United States</option>
  <option value="ca">Canada</option>
  <option value="uk">United Kingdom</option>
</select>

<!-- Grouped options -->
<label for="car">Choose a car</label>
<select id="car" name="car">
  <optgroup label="Swedish Cars">
    <option value="volvo">Volvo</option>
    <option value="saab">Saab</option>
  </optgroup>
  <optgroup label="German Cars">
    <option value="mercedes">Mercedes</option>
    <option value="audi">Audi</option>
  </optgroup>
</select>

<!-- Multiple select -->
<label for="interests">Select your interests</label>
<select id="interests" name="interests" multiple aria-describedby="interests-hint">
  <option value="tech">Technology</option>
  <option value="sports">Sports</option>
  <option value="music">Music</option>
  <option value="art">Art</option>
</select>
<span id="interests-hint" class="hint">Hold Ctrl/Cmd to select multiple</span>
```

## Textareas

```html
<label for="message">Message</label>
<textarea 
  id="message" 
  name="message"
  rows="5"
  aria-describedby="message-hint message-counter"
  maxlength="500"
></textarea>
<span id="message-hint" class="hint">Describe your issue in detail.</span>
<span id="message-counter" class="counter" aria-live="polite">
  0/500 characters
</span>
```

## Autocomplete

```html
<!-- Common autocomplete values -->
<input type="text" autocomplete="name">
<input type="text" autocomplete="given-name">
<input type="text" autocomplete="family-name">
<input type="email" autocomplete="email">
<input type="tel" autocomplete="tel">
<input type="text" autocomplete="street-address">
<input type="text" autocomplete="address-level2"> <!-- City -->
<input type="text" autocomplete="address-level1"> <!-- State -->
<input type="text" autocomplete="postal-code">
<input type="text" autocomplete="country">
<input type="text" autocomplete="cc-name">
<input type="text" autocomplete="cc-number">
<input type="text" autocomplete="cc-exp">
<input type="text" autocomplete="cc-csc">
<input type="password" autocomplete="new-password">
<input type="password" autocomplete="current-password">
<input type="text" autocomplete="one-time-code">
```

## Disabled vs Read-only

```html
<!-- Disabled: Cannot interact, not submitted -->
<label for="disabled-field">Disabled field</label>
<input type="text" id="disabled-field" value="Cannot change" disabled>

<!-- Read-only: Cannot edit, but is submitted -->
<label for="readonly-field">Read-only field</label>
<input type="text" id="readonly-field" value="Will be submitted" readonly>

<!-- Programmatically disabled state -->
<fieldset disabled>
  <legend>This section is disabled</legend>
  <label for="name">Name</label>
  <input type="text" id="name">
</fieldset>
```

## Custom Controls

### Custom Checkbox

```html
<div class="custom-checkbox">
  <input 
    type="checkbox" 
    id="custom-check"
    class="visually-hidden"
  >
  <label for="custom-check">
    <span class="checkbox-visual" aria-hidden="true"></span>
    Accept terms and conditions
  </label>
</div>

<style>
.custom-checkbox input:focus + label .checkbox-visual {
  outline: 2px solid #0066cc;
  outline-offset: 2px;
}

.custom-checkbox input:checked + label .checkbox-visual {
  background: #0066cc;
}
</style>
```

### Custom Select (Combobox)

```html
<div class="combobox">
  <label id="combo-label">Choose a fruit</label>
  <div 
    role="combobox"
    aria-expanded="false"
    aria-haspopup="listbox"
    aria-labelledby="combo-label"
  >
    <input 
      type="text"
      aria-autocomplete="list"
      aria-controls="fruit-listbox"
    >
    <button 
      type="button"
      aria-label="Show options"
      tabindex="-1"
    >▼</button>
  </div>
  <ul 
    id="fruit-listbox"
    role="listbox"
    aria-labelledby="combo-label"
    hidden
  >
    <li role="option" id="opt-apple">Apple</li>
    <li role="option" id="opt-banana">Banana</li>
    <li role="option" id="opt-cherry">Cherry</li>
  </ul>
</div>
```

## Form Summary

| Element | Accessibility Requirement |
|---------|--------------------------|
| All inputs | Associated label |
| Required fields | `required` + `aria-required` |
| Invalid fields | `aria-invalid="true"` |
| Hints | `aria-describedby` |
| Errors | Linked with `aria-describedby` |
| Groups | `<fieldset>` + `<legend>` |
| Submit | Clear button text |
