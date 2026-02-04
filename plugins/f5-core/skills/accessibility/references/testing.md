# Accessibility Testing Reference

## Automated Testing

### axe-core with Playwright

```typescript
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.describe('Accessibility', () => {
  test('home page has no violations', async ({ page }) => {
    await page.goto('/');

    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
      .analyze();

    expect(results.violations).toEqual([]);
  });

  test('form has no violations', async ({ page }) => {
    await page.goto('/contact');

    const results = await new AxeBuilder({ page })
      .include('#contact-form')
      .exclude('.third-party-widget')
      .analyze();

    expect(results.violations).toEqual([]);
  });
});
```

### jest-axe

```typescript
import { render } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';

expect.extend(toHaveNoViolations);

describe('Button', () => {
  it('has no accessibility violations', async () => {
    const { container } = render(<Button>Click me</Button>);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
```

### Lighthouse CI

```yaml
# lighthouserc.js
module.exports = {
  ci: {
    collect: {
      url: ['http://localhost:3000/', 'http://localhost:3000/contact'],
      numberOfRuns: 3,
    },
    assert: {
      assertions: {
        'categories:accessibility': ['error', { minScore: 0.9 }],
      },
    },
    upload: {
      target: 'temporary-public-storage',
    },
  },
};
```

## Manual Testing

### Keyboard Testing Checklist

```markdown
## Navigation
- [ ] Tab through all interactive elements
- [ ] Shift+Tab navigates backwards
- [ ] Focus order is logical
- [ ] Focus is visible on all elements
- [ ] No keyboard traps

## Interactions
- [ ] Enter activates buttons and links
- [ ] Space activates checkboxes and buttons
- [ ] Arrow keys navigate within components
- [ ] Escape closes modals/dropdowns

## Forms
- [ ] All fields reachable by keyboard
- [ ] Submit works with Enter
- [ ] Error messages announced
```

### Screen Reader Testing

#### VoiceOver (macOS)

```markdown
## Basic Commands
- VO + Cmd + F5: Toggle VoiceOver
- VO + A: Read from cursor
- VO + Right/Left: Navigate items
- VO + Space: Activate item
- VO + Cmd + H: Navigate headings
- VO + U: Open rotor

## Testing Checklist
- [ ] Page title announced on load
- [ ] Headings structure navigable
- [ ] Images have alt text read
- [ ] Forms labels announced
- [ ] Live regions announce updates
```

#### NVDA (Windows)

```markdown
## Basic Commands
- Ins + Q: Quit NVDA
- Ins + Down: Read from cursor
- Tab/Shift+Tab: Navigate focusable
- H/Shift+H: Navigate headings
- Ins + F7: Elements list

## Testing Checklist
- [ ] Virtual cursor navigation works
- [ ] Browse/Focus mode switches correctly
- [ ] Tables read with headers
- [ ] ARIA live regions work
```

### Color Contrast Tools

```bash
# Browser DevTools
# Chrome: Inspect element → Styles → Color contrast ratio

# CLI tool
npm install -g pa11y
pa11y https://example.com

# Contrast checking function
function checkContrast(foreground: string, background: string): number {
  // Returns contrast ratio
}
```

## Testing Checklist by Role

### Developer Testing

```markdown
## Before PR
- [ ] Run axe DevTools extension
- [ ] Keyboard test new features
- [ ] Check color contrast
- [ ] Verify ARIA usage
- [ ] Test focus management

## Automated Checks
- [ ] axe-core in unit tests
- [ ] Lighthouse in CI
- [ ] pa11y for regression
```

### QA Testing

```markdown
## Manual Testing
- [ ] Full keyboard navigation
- [ ] Screen reader walkthrough
- [ ] Zoom to 200%
- [ ] High contrast mode
- [ ] Reduced motion setting

## Cross-browser
- [ ] Chrome + VoiceOver
- [ ] Firefox + NVDA
- [ ] Safari + VoiceOver
- [ ] Edge + Narrator
```

## Common Issues

### Heading Hierarchy

```html
<!-- ❌ Bad: Skipped levels -->
<h1>Page Title</h1>
<h3>Section</h3>

<!-- ✅ Good: Sequential levels -->
<h1>Page Title</h1>
<h2>Section</h2>
<h3>Subsection</h3>
```

### Form Labels

```html
<!-- ❌ Bad: No label association -->
<label>Email</label>
<input type="email">

<!-- ✅ Good: Associated label -->
<label for="email">Email</label>
<input type="email" id="email">
```

### Focus Management

```typescript
// ❌ Bad: No focus management after dynamic content
modal.open();

// ✅ Good: Move focus to modal
modal.open();
modal.querySelector('button')?.focus();
```

### Image Alt Text

```html
<!-- ❌ Bad: Missing or redundant -->
<img src="logo.png">
<img src="logo.png" alt="image">

<!-- ✅ Good: Descriptive -->
<img src="logo.png" alt="Company Name">

<!-- ✅ Good: Decorative -->
<img src="decoration.png" alt="" role="presentation">
```

## Tools Summary

| Tool | Type | Use For |
|------|------|---------|
| axe DevTools | Browser extension | Quick audits |
| WAVE | Browser extension | Visual feedback |
| Lighthouse | CLI/Browser | CI integration |
| pa11y | CLI | Automated testing |
| VoiceOver | Screen reader | macOS testing |
| NVDA | Screen reader | Windows testing |
| Colour Contrast Analyser | Desktop app | Color checking |
