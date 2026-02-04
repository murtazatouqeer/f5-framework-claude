---
name: wcag-overview
description: Overview of WCAG guidelines and compliance levels
category: accessibility/fundamentals
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# WCAG Overview

## What is WCAG?

Web Content Accessibility Guidelines (WCAG) are technical standards for making web content accessible to people with disabilities. Developed by W3C's Web Accessibility Initiative (WAI).

## WCAG Versions

| Version | Released | Status |
|---------|----------|--------|
| WCAG 2.0 | 2008 | Stable, ISO standard |
| WCAG 2.1 | 2018 | Current recommendation |
| WCAG 2.2 | 2023 | Latest version |
| WCAG 3.0 | Draft | In development |

## Conformance Levels

### Level A (Minimum)

Essential requirements without which some users cannot access content.

| Guideline | Requirement |
|-----------|-------------|
| 1.1.1 | Non-text content has text alternative |
| 1.3.1 | Info and relationships conveyed programmatically |
| 2.1.1 | All functionality available from keyboard |
| 2.4.1 | Bypass blocks mechanism |
| 4.1.1 | Valid HTML parsing |

### Level AA (Recommended)

Standard for most organizations and legal requirements.

| Guideline | Requirement |
|-----------|-------------|
| 1.4.3 | Contrast minimum 4.5:1 |
| 1.4.4 | Text resizable up to 200% |
| 2.4.6 | Headings and labels descriptive |
| 2.4.7 | Focus visible |
| 3.3.3 | Error suggestions provided |

### Level AAA (Enhanced)

Highest level, not always achievable for all content.

| Guideline | Requirement |
|-----------|-------------|
| 1.4.6 | Enhanced contrast 7:1 |
| 2.4.9 | Link purpose from link text alone |
| 3.1.5 | Reading level assistance |
| 3.2.5 | Change on request only |

## The POUR Principles

### 1. Perceivable

Content must be presented in ways users can perceive.

```html
<!-- Text alternatives -->
<img src="chart.png" alt="Sales increased 25% in Q4 2024">

<!-- Captions -->
<video>
  <track kind="captions" src="captions.vtt" srclang="en">
</video>

<!-- Color not sole conveyor -->
<span class="error">
  <span aria-hidden="true">⚠️</span>
  Error: Invalid email
</span>
```

### 2. Operable

UI components must be operable by all users.

```html
<!-- Keyboard accessible -->
<button onclick="submit()">Submit</button>

<!-- Sufficient time -->
<div role="alert">
  Session expires in 5 minutes.
  <button onclick="extendSession()">Extend</button>
</div>

<!-- No seizure-inducing content -->
<!-- Avoid flashing more than 3 times per second -->
```

### 3. Understandable

Information and UI operation must be understandable.

```html
<!-- Page language -->
<html lang="en">

<!-- Consistent navigation -->
<nav aria-label="Main">
  <!-- Same order on every page -->
</nav>

<!-- Error identification -->
<label for="email">Email</label>
<input id="email" aria-describedby="email-error" aria-invalid="true">
<span id="email-error">Please enter a valid email address</span>
```

### 4. Robust

Content must be robust enough for assistive technologies.

```html
<!-- Valid HTML -->
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Page Title</title>
</head>

<!-- Proper ARIA usage -->
<button aria-expanded="false" aria-controls="menu">Menu</button>
<ul id="menu" hidden>...</ul>
```

## WCAG 2.2 New Success Criteria

| Criterion | Level | Description |
|-----------|-------|-------------|
| 2.4.11 | AA | Focus not obscured (minimum) |
| 2.4.12 | AAA | Focus not obscured (enhanced) |
| 2.4.13 | AAA | Focus appearance |
| 2.5.7 | AA | Dragging movements alternative |
| 2.5.8 | AA | Target size (minimum) 24×24px |
| 3.2.6 | A | Consistent help location |
| 3.3.7 | A | Redundant entry |
| 3.3.8 | AA | Accessible authentication |
| 3.3.9 | AAA | Accessible authentication (enhanced) |

## Conformance Requirements

To claim conformance:

1. **Full pages** - All content on page must conform
2. **Complete processes** - All steps in a process must conform
3. **Accessibility supported** - Technologies used in accessible way
4. **Non-interference** - Inaccessible content doesn't block access
5. **Conformance statement** - Optional but recommended

## Conformance Statement Example

```markdown
## Accessibility Statement

This website conforms to WCAG 2.1 Level AA.

### Conformance Status
Partially conformant due to:
- Some third-party content
- Legacy PDF documents

### Feedback
Contact accessibility@example.com for issues.

### Last reviewed: January 2024
```

## Quick Compliance Checklist

### Level A Essentials

- [ ] All images have alt text
- [ ] All form fields have labels
- [ ] No keyboard traps
- [ ] Page has title
- [ ] Color not only indicator
- [ ] No auto-playing audio
- [ ] Content readable without CSS

### Level AA Requirements

- [ ] Contrast ratio 4.5:1 (text)
- [ ] Contrast ratio 3:1 (large text, UI)
- [ ] Text resizable to 200%
- [ ] Focus visible
- [ ] Multiple navigation methods
- [ ] Consistent navigation
- [ ] Error suggestions

## Resources

- [WCAG 2.1 Guidelines](https://www.w3.org/TR/WCAG21/)
- [Understanding WCAG 2.1](https://www.w3.org/WAI/WCAG21/Understanding/)
- [WCAG Quick Reference](https://www.w3.org/WAI/WCAG21/quickref/)
- [WCAG 2.2 What's New](https://www.w3.org/TR/WCAG22/)
