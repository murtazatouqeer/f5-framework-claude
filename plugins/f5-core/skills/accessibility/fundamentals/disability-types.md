---
name: disability-types
description: Understanding different types of disabilities and user needs
category: accessibility/fundamentals
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# Understanding Disability Types

## Overview

Understanding different disabilities helps create better accessible experiences. Disabilities can be permanent, temporary, or situational.

## Visual Disabilities

### Blindness

**Users:** Rely on screen readers to navigate.

**Design considerations:**
```html
<!-- Provide text alternatives -->
<img src="product.jpg" alt="Blue wireless headphones with cushioned ear cups">

<!-- Logical heading structure -->
<h1>Product Details</h1>
<h2>Features</h2>
<h2>Specifications</h2>
<h2>Reviews</h2>

<!-- Descriptive link text -->
<a href="/order">Order Blue Wireless Headphones</a>
<!-- Not: <a href="/order">Click here</a> -->

<!-- Form labels -->
<label for="quantity">Quantity</label>
<input type="number" id="quantity" name="quantity">
```

### Low Vision

**Users:** Use screen magnification, large text, high contrast.

**Design considerations:**
```css
/* Scalable text */
body {
  font-size: 100%; /* Respects user settings */
}

h1 { font-size: 2rem; }
p { font-size: 1rem; }

/* Sufficient contrast */
.text {
  color: #333;      /* On white: 12.6:1 ratio */
  background: #fff;
}

/* Don't rely on color alone */
.error {
  color: #d32f2f;
  border-left: 4px solid #d32f2f;
}
.error::before {
  content: "⚠ ";
}

/* Support zoom */
@media (min-width: 320px) {
  /* Content reflows at 400% zoom */
}
```

### Color Blindness

**Users:** Cannot distinguish certain colors (8% of men, 0.5% of women).

**Design considerations:**
```css
/* Don't rely on color alone */

/* ❌ Bad: Only color difference */
.status-active { color: green; }
.status-inactive { color: red; }

/* ✅ Good: Color + text/icon */
.status-active::before { content: "✓ "; }
.status-inactive::before { content: "✗ "; }

/* ✅ Good: Color + pattern for charts */
.chart-series-1 { 
  background: #0066cc;
  background-image: repeating-linear-gradient(/* pattern */);
}
```

```html
<!-- Links with underlines, not just color -->
<a href="/help" style="text-decoration: underline;">Get help</a>

<!-- Form errors with icon + text -->
<span class="error">
  <svg aria-hidden="true"><!-- error icon --></svg>
  Please enter a valid email
</span>
```

## Auditory Disabilities

### Deafness / Hard of Hearing

**Users:** Rely on captions, transcripts, visual alternatives.

**Design considerations:**
```html
<!-- Video with captions -->
<video controls>
  <source src="demo.mp4" type="video/mp4">
  <track 
    kind="captions" 
    src="demo.vtt" 
    srclang="en" 
    label="English"
    default
  >
</video>

<!-- Audio with transcript -->
<audio controls src="podcast.mp3">
  <a href="podcast.mp3">Download podcast</a>
</audio>
<details>
  <summary>View transcript</summary>
  <p>Welcome to episode 10. Today we discuss...</p>
</details>

<!-- Visual alerts, not just audio -->
<div role="alert" class="notification">
  New message received
</div>
```

## Motor Disabilities

### Limited Mobility / Dexterity

**Users:** May use keyboard, switch devices, voice control, eye tracking.

**Design considerations:**
```html
<!-- Large click targets -->
<button class="large-target">Submit</button>

<!-- Sufficient spacing -->
<nav>
  <a href="/">Home</a>
  <a href="/about">About</a> <!-- Spaced apart -->
</nav>

<!-- Don't require precise movements -->
<!-- ❌ Bad: Drag to reorder -->
<!-- ✅ Good: Buttons to move up/down -->
<li>
  Item 1
  <button aria-label="Move up">↑</button>
  <button aria-label="Move down">↓</button>
</li>
```

```css
/* Large touch targets */
button, a, input {
  min-height: 44px;
  min-width: 44px;
  padding: 12px;
}

/* Spacing between interactive elements */
.button-group button {
  margin: 8px;
}
```

### Tremors

**Users:** May have difficulty with precise pointing.

**Design considerations:**
```css
/* Generous target sizes */
.action-button {
  padding: 16px 24px;
  font-size: 1.125rem;
}

/* Avoid hover-only interactions */
.tooltip-trigger:hover .tooltip,
.tooltip-trigger:focus .tooltip {
  display: block;
}
```

## Cognitive Disabilities

### Learning Disabilities / ADHD / Autism

**Users:** Need clear, consistent, predictable interfaces.

**Design considerations:**
```html
<!-- Clear, simple language -->
<h1>Reset Your Password</h1>
<p>Enter your email address. We'll send you a link to create a new password.</p>

<!-- Step-by-step processes -->
<ol>
  <li>Enter your email</li>
  <li>Check your inbox</li>
  <li>Click the reset link</li>
  <li>Create new password</li>
</ol>

<!-- Current position in process -->
<nav aria-label="Progress">
  <ol>
    <li aria-current="step">Shipping</li>
    <li>Payment</li>
    <li>Review</li>
  </ol>
</nav>

<!-- Consistent navigation -->
<!-- Same navigation on every page -->
```

```css
/* Reduce visual clutter */
.content {
  max-width: 70ch;
  line-height: 1.6;
}

/* Allow sufficient time */
/* No auto-advancing carousels */
/* User-controlled timeouts */
```

### Memory Impairments

**Users:** Need to be able to review information, not rely on recall.

**Design considerations:**
```html
<!-- Don't require memorization -->
<!-- Show confirmation details -->
<section>
  <h2>Your Order</h2>
  <p>Order #12345</p>
  <p>3 items totaling $150</p>
  <button>View Details</button>
</section>

<!-- Save progress -->
<form>
  <p>Your progress is automatically saved.</p>
  <!-- Long form fields -->
</form>

<!-- Visible password option -->
<label for="password">Password</label>
<input type="password" id="password">
<button type="button" onclick="togglePassword()">Show password</button>
```

## Situational Disabilities

| Permanent | Temporary | Situational |
|-----------|-----------|-------------|
| Blind | Eye surgery | Bright sunlight |
| Deaf | Ear infection | Loud environment |
| One arm | Broken arm | Holding baby |
| Non-verbal | Laryngitis | Heavy accent |

## Assistive Technologies

| Disability | Common AT |
|------------|-----------|
| Blindness | Screen readers (NVDA, JAWS, VoiceOver) |
| Low vision | Screen magnifiers, high contrast mode |
| Motor | Switch devices, voice control, eye gaze |
| Deaf/HoH | Captions, hearing loops |
| Cognitive | Text-to-speech, reading rulers |

## Design Recommendations Summary

| Disability | Key Recommendations |
|------------|---------------------|
| Visual | Alt text, headings, contrast, zoom support |
| Auditory | Captions, transcripts, visual alerts |
| Motor | Large targets, keyboard access, no time limits |
| Cognitive | Clear language, consistent layout, no distractions |
