---
name: automated-testing
description: Automated accessibility testing tools and CI integration
category: accessibility/testing
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# Automated Accessibility Testing

## Overview

Automated testing catches approximately 30-50% of accessibility issues. Use it as a first line of defense, not a complete solution.

## What Automated Testing Catches

| Detectable | Not Detectable |
|------------|----------------|
| Missing alt text | Alt text quality |
| Low contrast ratios | Meaningful focus order |
| Missing form labels | Keyboard trap UX |
| Invalid ARIA | Content clarity |
| Duplicate IDs | Reading level |
| Missing lang attribute | Context appropriateness |

## axe-core

### Installation

```bash
npm install @axe-core/cli
npm install axe-core
npm install @axe-core/playwright  # For Playwright
npm install @axe-core/puppeteer   # For Puppeteer
npm install jest-axe              # For Jest
```

### CLI Usage

```bash
# Test a URL
npx axe https://example.com

# Test with specific rules
npx axe https://example.com --rules color-contrast,label

# Disable rules
npx axe https://example.com --disable scrollable-region-focusable

# Output formats
npx axe https://example.com --stdout
npx axe https://example.com --save results.json

# Test authenticated pages
npx axe https://example.com --load-delay 3000
```

### JavaScript Integration

```javascript
import axe from 'axe-core';

// Run axe on current page
axe.run().then(results => {
  console.log('Violations:', results.violations);
  console.log('Passes:', results.passes);
  console.log('Incomplete:', results.incomplete);
});

// Run on specific element
axe.run('#main-content').then(results => {
  console.log(results.violations);
});

// With configuration
axe.run(document, {
  runOnly: {
    type: 'tag',
    values: ['wcag2a', 'wcag2aa']
  },
  rules: {
    'color-contrast': { enabled: false }
  }
}).then(results => {
  console.log(results);
});
```

### Jest Integration

```javascript
// jest.setup.js
import { toHaveNoViolations } from 'jest-axe';
expect.extend(toHaveNoViolations);

// component.test.js
import { render } from '@testing-library/react';
import { axe } from 'jest-axe';
import MyComponent from './MyComponent';

describe('MyComponent accessibility', () => {
  it('should have no accessibility violations', async () => {
    const { container } = render(<MyComponent />);
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
  
  // With specific rules
  it('should have no color contrast violations', async () => {
    const { container } = render(<MyComponent />);
    const results = await axe(container, {
      rules: {
        'color-contrast': { enabled: true }
      }
    });
    expect(results).toHaveNoViolations();
  });
});
```

### Playwright Integration

```javascript
// playwright.config.js
import { expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

// tests/accessibility.spec.js
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.describe('Accessibility Tests', () => {
  test('homepage should be accessible', async ({ page }) => {
    await page.goto('/');
    
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa'])
      .analyze();
    
    expect(accessibilityScanResults.violations).toEqual([]);
  });
  
  test('login form should be accessible', async ({ page }) => {
    await page.goto('/login');
    
    const results = await new AxeBuilder({ page })
      .include('#login-form')
      .analyze();
    
    expect(results.violations).toEqual([]);
  });
  
  test('excludes third-party widgets', async ({ page }) => {
    await page.goto('/');
    
    const results = await new AxeBuilder({ page })
      .exclude('.third-party-widget')
      .analyze();
    
    expect(results.violations).toEqual([]);
  });
});
```

## Lighthouse

### CLI Usage

```bash
# Install
npm install -g lighthouse

# Run accessibility audit
lighthouse https://example.com --only-categories=accessibility

# Output formats
lighthouse https://example.com --output=json --output-path=./report.json
lighthouse https://example.com --output=html --output-path=./report.html

# With specific settings
lighthouse https://example.com \
  --preset=desktop \
  --only-categories=accessibility \
  --chrome-flags="--headless"
```

### Programmatic Usage

```javascript
import lighthouse from 'lighthouse';
import chromeLauncher from 'chrome-launcher';

async function runAccessibilityAudit(url) {
  const chrome = await chromeLauncher.launch({ chromeFlags: ['--headless'] });
  
  const options = {
    logLevel: 'info',
    output: 'json',
    onlyCategories: ['accessibility'],
    port: chrome.port
  };
  
  const runnerResult = await lighthouse(url, options);
  const accessibilityScore = runnerResult.lhr.categories.accessibility.score * 100;
  
  console.log(`Accessibility score: ${accessibilityScore}`);
  
  // Get individual audits
  const audits = runnerResult.lhr.audits;
  for (const [key, audit] of Object.entries(audits)) {
    if (audit.score !== null && audit.score < 1) {
      console.log(`${key}: ${audit.title} - ${audit.displayValue || 'Failed'}`);
    }
  }
  
  await chrome.kill();
  return runnerResult;
}
```

## Pa11y

### CLI Usage

```bash
# Install
npm install -g pa11y

# Basic test
pa11y https://example.com

# With specific standard
pa11y https://example.com --standard WCAG2AA

# Ignore specific issues
pa11y https://example.com --ignore "WCAG2AA.Principle1.Guideline1_4.1_4_3.G18.Fail"

# Output formats
pa11y https://example.com --reporter json > results.json
pa11y https://example.com --reporter html > results.html

# With actions (login first)
pa11y https://example.com/dashboard --config ./pa11y-config.json
```

### Configuration File

```json
{
  "defaults": {
    "timeout": 60000,
    "wait": 1000,
    "standard": "WCAG2AA",
    "runners": ["axe", "htmlcs"],
    "chromeLaunchConfig": {
      "args": ["--no-sandbox"]
    }
  },
  "urls": [
    {
      "url": "https://example.com/login",
      "actions": [
        "set field #email to test@example.com",
        "set field #password to password123",
        "click element #submit",
        "wait for url to be https://example.com/dashboard"
      ]
    },
    "https://example.com/dashboard",
    "https://example.com/profile"
  ]
}
```

### CI Dashboard (Pa11y-CI)

```bash
# Install
npm install -g pa11y-ci

# Run
pa11y-ci
```

```json
// .pa11yci
{
  "defaults": {
    "standard": "WCAG2AA",
    "timeout": 30000
  },
  "urls": [
    "https://example.com/",
    "https://example.com/about",
    "https://example.com/contact"
  ]
}
```

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/accessibility.yml
name: Accessibility Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  accessibility:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Build application
        run: npm run build
      
      - name: Start server
        run: npm start &
        env:
          CI: true
      
      - name: Wait for server
        run: npx wait-on http://localhost:3000
      
      - name: Run Pa11y
        run: npx pa11y-ci
      
      - name: Run Lighthouse
        uses: treosh/lighthouse-ci-action@v10
        with:
          urls: |
            http://localhost:3000/
            http://localhost:3000/about
          uploadArtifacts: true
```

### GitLab CI

```yaml
# .gitlab-ci.yml
accessibility:
  stage: test
  image: node:20
  services:
    - name: selenium/standalone-chrome
      alias: chrome
  script:
    - npm ci
    - npm run build
    - npm start &
    - npx wait-on http://localhost:3000
    - npx pa11y-ci
    - npx lighthouse http://localhost:3000 --chrome-flags="--headless" --output=json --output-path=./lighthouse.json
  artifacts:
    paths:
      - lighthouse.json
```

## ESLint Plugin

### Setup

```bash
npm install eslint-plugin-jsx-a11y --save-dev
```

### Configuration

```javascript
// .eslintrc.js
module.exports = {
  plugins: ['jsx-a11y'],
  extends: ['plugin:jsx-a11y/recommended'],
  rules: {
    // Customize rules
    'jsx-a11y/anchor-is-valid': ['error', {
      components: ['Link'],
      specialLink: ['to'],
      aspects: ['invalidHref', 'preferButton']
    }],
    'jsx-a11y/label-has-associated-control': ['error', {
      assert: 'either'
    }]
  }
};
```

### Common Rules

```javascript
// eslint-plugin-jsx-a11y rules
{
  'jsx-a11y/alt-text': 'error',              // Images need alt
  'jsx-a11y/anchor-has-content': 'error',    // Links need content
  'jsx-a11y/click-events-have-key-events': 'error',  // onClick needs keyboard
  'jsx-a11y/no-autofocus': 'warn',           // Avoid autofocus
  'jsx-a11y/no-static-element-interactions': 'error', // divs need roles
  'jsx-a11y/role-has-required-aria-props': 'error',  // Roles need ARIA
  'jsx-a11y/tabindex-no-positive': 'error'   // No positive tabindex
}
```

## Reporting

### Custom Reporter

```javascript
// accessibility-reporter.js
export function generateReport(results) {
  const report = {
    summary: {
      total: results.violations.length,
      critical: 0,
      serious: 0,
      moderate: 0,
      minor: 0
    },
    violations: []
  };
  
  results.violations.forEach(violation => {
    report.summary[violation.impact]++;
    
    report.violations.push({
      id: violation.id,
      impact: violation.impact,
      description: violation.description,
      help: violation.help,
      helpUrl: violation.helpUrl,
      nodes: violation.nodes.map(node => ({
        html: node.html,
        target: node.target,
        failureSummary: node.failureSummary
      }))
    });
  });
  
  return report;
}

// Usage
const results = await axe.run();
const report = generateReport(results);
console.log(JSON.stringify(report, null, 2));
```

### Dashboard Integration

```javascript
// Send results to monitoring service
async function reportToMonitoring(results) {
  await fetch('https://monitoring.example.com/api/accessibility', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      timestamp: new Date().toISOString(),
      url: window.location.href,
      violations: results.violations.length,
      passes: results.passes.length,
      details: results.violations
    })
  });
}
```

## Summary

| Tool | Best For | Integration |
|------|----------|-------------|
| axe-core | Comprehensive testing | Jest, Playwright, CI |
| Lighthouse | Audit reports | CLI, CI, Chrome |
| Pa11y | CI pipelines | CLI, CI |
| eslint-plugin-jsx-a11y | React linting | Build time |
| WAVE | Manual review | Browser extension |
