---
name: accessibility
description: Web accessibility guidelines and implementation
category: skill
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: true
context: inject
version: 1.0.0
---

# Accessibility Skills

## Overview

Web accessibility (a11y) ensures websites are usable by everyone, including people with disabilities. Accessible design benefits all users and is often required by law.

## WCAG Principles (POUR)

| Principle | Description | Examples |
|-----------|-------------|----------|
| **P**erceivable | Info must be presentable to users | Alt text, captions, contrast |
| **O**perable | UI must be operable by everyone | Keyboard access, timing |
| **U**nderstandable | Info and UI must be understandable | Clear labels, error handling |
| **R**obust | Content must work with assistive tech | Valid HTML, ARIA |

## WCAG Conformance Levels

| Level | Description | Target Audience |
|-------|-------------|-----------------|
| **A** | Minimum accessibility | Basic requirements |
| **AA** | Recommended standard | Most organizations (legal requirement) |
| **AAA** | Enhanced accessibility | Specialized applications |

## Key Statistics

- 15% of world population has a disability
- 1 in 4 adults in the US has a disability
- 8% of men have color blindness
- By 2030, 1.4 billion people will be over 60

## Categories

### Fundamentals
Core accessibility concepts:
- **WCAG Overview** - Understanding the guidelines
- **Accessibility Principles** - POUR principles in detail
- **Disability Types** - Understanding user needs

### HTML
Semantic structure:
- **Semantic HTML** - Using proper elements
- **Landmarks** - Page regions for navigation
- **Headings** - Document structure
- **Forms** - Accessible form design

### ARIA
Accessible Rich Internet Applications:
- **ARIA Basics** - When and how to use ARIA
- **ARIA Roles** - Element roles
- **ARIA States** - Dynamic state attributes
- **Live Regions** - Announcing dynamic content

### Keyboard
Keyboard accessibility:
- **Keyboard Navigation** - Tab order and shortcuts
- **Focus Management** - Focus indicators and trapping
- **Skip Links** - Bypassing repeated content

### Visual
Visual accessibility:
- **Color Contrast** - Contrast ratios and tools
- **Text Sizing** - Responsive typography
- **Motion Reduction** - Respecting user preferences

### Media
Multimedia accessibility:
- **Images & Alt Text** - Descriptive alternatives
- **Video Captions** - Synchronized text
- **Audio Transcripts** - Text alternatives

### Testing
Accessibility testing:
- **Manual Testing** - Keyboard and visual testing
- **Automated Testing** - axe, Lighthouse, Pa11y
- **Screen Reader Testing** - NVDA, VoiceOver, JAWS

### Components
Accessible patterns:
- **Accessible Buttons** - Button best practices
- **Accessible Forms** - Form patterns
- **Accessible Modals** - Dialog accessibility
- **Accessible Tables** - Data table patterns

## Quick Reference

### Minimum Requirements (WCAG 2.1 AA)

| Requirement | Guideline | Check |
|-------------|-----------|-------|
| Color contrast (normal text) | 4.5:1 | Tools |
| Color contrast (large text) | 3:1 | Tools |
| Focus visible | 2.4.7 | Manual |
| Keyboard accessible | 2.1.1 | Manual |
| Alt text for images | 1.1.1 | Automated |
| Form labels | 1.3.1 | Automated |
| Error identification | 3.3.1 | Manual |
| Page titled | 2.4.2 | Automated |

### Testing Checklist

```markdown
- [ ] Can navigate with keyboard only
- [ ] Focus indicator is visible
- [ ] Color contrast meets requirements
- [ ] Images have alt text
- [ ] Forms have labels
- [ ] Headings are hierarchical
- [ ] Links are descriptive
- [ ] Errors are announced
- [ ] Works with screen reader
```

## Legal Requirements

| Region | Law | Standard |
|--------|-----|----------|
| USA | ADA, Section 508 | WCAG 2.1 AA |
| EU | European Accessibility Act | WCAG 2.1 AA |
| UK | Equality Act | WCAG 2.1 AA |
| Canada | AODA | WCAG 2.0 AA |

## Tools

| Tool | Purpose | Type |
|------|---------|------|
| axe DevTools | Browser testing | Extension |
| WAVE | Visual inspection | Extension |
| Lighthouse | Audit | Browser |
| Pa11y | CI integration | CLI |
| NVDA | Screen reader | Application |
| VoiceOver | Screen reader | macOS/iOS |

## Related Skills

- [Frontend Architecture](/skills/frontend-architecture/) - Component design
- [Testing](/skills/testing/) - Test automation
- [Code Quality](/skills/code-quality/) - ESLint a11y plugin
