---
name: f5-test-e2e
description: End-to-end testing with Playwright
argument-hint: <journey|critical|page|smoke|visual> [target]
mcp-servers: playwright
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: true
---

# /f5-test-e2e - End-to-End & Visual Testing

> **Version**: 1.4.0
> **Category**: Testing
> **MCP Required**: Playwright

E2E testing và visual regression testing sử dụng MCP Playwright cho browser automation.

## ARGUMENTS
The user's request is: $ARGUMENTS

---

## MCP PRE-FLIGHT CHECK

| MCP Server | Required | Purpose |
|------------|----------|---------|
| Playwright | ✅ Yes | Browser automation, screenshots |

**If MCP unavailable:**
- ⚠️ Playwright not available
- Fallback: Manual testing instructions provided
- Run `/f5-mcp status` to check

---

## SUBCOMMANDS

| Subcommand | Description | Example |
|------------|-------------|---------|
| `journey <name>` | Full user journey test | `/f5-test-e2e journey user-registration` |
| `critical <path>` | Critical business path | `/f5-test-e2e critical checkout` |
| `page <name>` | Single page test | `/f5-test-e2e page login` |
| `smoke` | Quick sanity check | `/f5-test-e2e smoke` |
| `regression` | Full regression suite | `/f5-test-e2e regression` |
| `visual [options]` | Visual regression testing | `/f5-test-e2e visual --compare-figma` |
| `generate-from-design` | Design → E2E | `/f5-test-e2e generate-from-design login` |

---

## FLAGS

| Flag | Description | Default |
|------|-------------|---------|
| `--screenshot` | Capture screenshots at each step | false |
| `--video` | Record video of test | false |
| `--headless` | Run in headless mode | true |
| `--browser <type>` | chromium, firefox, webkit | chromium |
| `--fix` | Auto-fix UI issues found | false |
| `--report` | Generate E2E report | false |

---

## JOURNEY TESTING

```bash
/f5-test-e2e journey user-registration
```

### Journey Definition Format

```yaml
name: user-registration
description: "Complete user registration flow"
steps:
  1. Navigate to homepage
  2. Click "Sign Up" button
  3. Fill registration form
  4. Submit form
  5. Verify confirmation page
```

### Execution Output

```markdown
## 🎬 E2E Journey Test: user-registration

### Step 1: Navigate to Homepage
**Action:** `browser_navigate`
**URL:** http://localhost:3000
**Assertions:** Title visible ✅, Logo visible ✅
**Result:** ✅ PASS

### Step 2: Click Sign Up
**Action:** `browser_click`
**Selector:** `button[data-testid="signup-btn"]`
**Result:** ✅ PASS

### Step 3: Fill Registration Form
**Actions:**
- Fill email: `test@example.com` ✅
- Fill password: `SecureP@ss123` ✅
- Check terms: ✅
**Result:** ✅ PASS

### Journey Summary
| Step | Duration | Result |
|------|----------|--------|
| Navigate | 1.2s | ✅ |
| Click Sign Up | 0.8s | ✅ |
| Fill Form | 2.1s | ✅ |
| Submit | 1.5s | ✅ |

**Result:** ✅ JOURNEY PASSED
```

---

## CRITICAL PATH TESTING

```bash
/f5-test-e2e critical checkout
```

Business-critical flows với higher scrutiny:

```markdown
## 🔥 Critical Path Test: checkout

**Business Impact:** HIGH
**Must Pass:** 100%

| Step | Status | Duration |
|------|--------|----------|
| Add to cart | ✅ | 0.8s |
| View cart | ✅ | 0.5s |
| Enter shipping | ✅ | 1.2s |
| Payment | ✅ | 2.1s |
| Confirm | ✅ | 1.0s |

**Result:** ✅ CRITICAL PATH PASSED
```

---

## PAGE TESTING

```bash
/f5-test-e2e page login
```

Single page với element và functionality checks:

```markdown
## 📄 Page Test: login

### Elements Check
| Element | Selector | Status |
|---------|----------|--------|
| Email input | `#email` | ✅ Found |
| Password input | `#password` | ✅ Found |
| Submit button | `button[type="submit"]` | ✅ Found |

### Functionality Tests
| Test | Expected | Actual | Result |
|------|----------|--------|--------|
| Valid login | Redirect to /dashboard | ✅ | ✅ |
| Invalid login | Error message | ✅ | ✅ |
| Empty submit | Validation errors | ✅ | ✅ |

### Accessibility Check
| Check | Status |
|-------|--------|
| Form labels | ✅ |
| Tab order | ✅ |
| Color contrast | ✅ |

**Result:** ✅ PAGE PASSED
```

---

## SMOKE TESTING

```bash
/f5-test-e2e smoke
```

Quick sanity check for critical pages:

```markdown
## 💨 Smoke Test

| Page | URL | Status | Load Time |
|------|-----|--------|-----------|
| Home | / | ✅ | 1.2s |
| Login | /login | ✅ | 0.8s |
| Register | /register | ✅ | 0.9s |
| Dashboard | /dashboard | ✅ | 1.5s |

**Result:** ✅ ALL SYSTEMS GO
```

---

## VISUAL TESTING

```bash
/f5-test-e2e visual [options]
```

### Visual Testing Options

| Option | Description |
|--------|-------------|
| `--compare-figma` | Compare with Figma reference images |
| `--update-baseline` | Update baseline screenshots |
| `--apply-fixes` | Apply suggested CSS fixes |
| `--suggest-fixes` | Show suggested fixes (preview) |
| `--threshold <n>` | Max diff percentage (default: 5) |
| `--pages <list>` | Comma-separated pages |
| `--viewports <list>` | desktop, tablet, mobile |
| `--ci` | CI mode - fail if threshold exceeded |

### Configuration

File: `.f5/visual/config.yaml`

```yaml
visual_testing:
  enabled: true
  threshold: 5  # % difference allowed
  mcp_tool: playwright

  viewports:
    desktop: { width: 1920, height: 1080 }
    tablet: { width: 768, height: 1024 }
    mobile: { width: 375, height: 812 }

  ignore_areas:
    - selector: ".dynamic-content"
    - selector: ".timestamp"
```

### Figma Mapping

File: `.f5/input/figma/mapping.yaml`

```yaml
pages:
  - url: "/"
    figma: "homepage.jpg"
    viewport: { width: 1920, height: 3000 }

  - url: "/login"
    figma: "login.jpg"
    viewport: { width: 1920, height: 1080 }
```

### Visual Test Output

```markdown
## 👁️ Visual Regression Report

**Date:** [timestamp]
**Pages Tested:** 4
**Threshold:** 5%

### Summary
| Page | Diff % | Threshold | Status |
|------|--------|-----------|--------|
| /services/transport | 12.5% | 5% | ❌ FAIL |
| /services/urban | 3.2% | 5% | ✅ PASS |
| /login | 1.1% | 5% | ✅ PASS |

**Pass Rate:** 2/3 (67%)

### Failed: /services/transport

| Area | Issue | Suggested Fix |
|------|-------|---------------|
| Hero Section | Height differs 50px | `h-[350px]` → `h-[400px]` |
| Font size | Smaller than design | `text-lg` → `text-xl` |

**Files to Fix:**
- `ServicePage.tsx:45` - Hero height
- `ProjectCard.tsx:12` - Font size
```

### Auto-Fix Mode

```bash
/f5-test-e2e visual --apply-fixes
```

```markdown
## 🔧 Auto-Fix Applied

| Fix | File | Confidence | Status |
|-----|------|------------|--------|
| Hero height | ServicePage.tsx:45 | 95% | ✅ Applied |
| Font size | ProjectCard.tsx:12 | 88% | ✅ Applied |
| Color | Button.tsx:8 | 65% | ⏭️ Skipped |

**Applied:** 2 fixes
**Skipped:** 1 (below 80% confidence)

Re-running visual test...

| Page | Before | After | Status |
|------|--------|-------|--------|
| /services/transport | 12.5% | 2.1% | ✅ Fixed |
```

### Update Baseline

```bash
/f5-test-e2e visual --update-baseline
```

```markdown
## 📸 Baseline Updated

| Page | Previous Diff | Action |
|------|---------------|--------|
| /login | 2.1% | ✅ Updated |
| /dashboard | 0.5% | ✅ Updated |

New baseline: `.f5/visual/baseline/`
```

---

## DESIGN → E2E MAPPING

```bash
/f5-test-e2e generate-from-design login-screen
```

Auto-generate E2E tests from design documents:

```markdown
## 🎨 Design → E2E Generation

**Source:** `.f5/specs/detail-design/screens/login-screen.yaml`

### Mapping Applied
| Design Element | E2E Action |
|----------------|------------|
| Input `email` | `fill('[name="email"]', ...)` |
| Input `password` | `fill('[name="password"]', ...)` |
| Submit button | `click('[type="submit"]')` |
| Success redirect | `expect(page).toHaveURL('/dashboard')` |

### Generated Test
```typescript
// tests/e2e/login.e2e-spec.ts
test('login flow', async ({ page }) => {
  await page.goto('/login');
  await page.fill('[name="email"]', 'test@example.com');
  await page.fill('[name="password"]', 'password123');
  await page.click('[type="submit"]');
  await expect(page).toHaveURL('/dashboard');
});
```
```

---

## PLAYWRIGHT ACTIONS

### Available MCP Commands

| Action | Command | Description |
|--------|---------|-------------|
| Navigate | `browser_navigate` | Go to URL |
| Click | `browser_click` | Click element |
| Fill | `browser_type` | Input text |
| Screenshot | `browser_take_screenshot` | Capture screen |
| Snapshot | `browser_snapshot` | A11y tree snapshot |
| Wait | `browser_wait_for` | Wait for element |
| Evaluate | `browser_evaluate` | Run JS |

---

## OUTPUT FORMAT

```markdown
## 🎬 E2E Test Report

**Date:** [timestamp]
**Browser:** Chromium
**Viewport:** 1280x720

### Summary
| Type | Tests | Pass | Fail |
|------|-------|------|------|
| Journey | 3 | 3 | 0 |
| Critical | 2 | 2 | 0 |
| Page | 5 | 4 | 1 |
| Visual | 4 | 3 | 1 |

**Pass Rate:** 92%

### Artifacts
- Screenshots: `.f5/testing/e2e/screenshots/`
- Videos: `.f5/testing/e2e/videos/`
- Visual Diffs: `.f5/visual/diff/`
```

---

## CONFIGURATION

### `.f5/testing/e2e-config.yaml`

```yaml
e2e:
  browser: chromium
  headless: true
  viewport:
    width: 1280
    height: 720

  timeouts:
    navigation: 30000
    action: 10000

  screenshots:
    on_failure: true
    full_page: true

  base_url: "http://localhost:3000"
```

---

## EXAMPLES

```bash
# Journey tests
/f5-test-e2e journey user-registration
/f5-test-e2e journey user-registration --screenshot --video

# Critical paths
/f5-test-e2e critical checkout

# Page tests
/f5-test-e2e page login

# Smoke test
/f5-test-e2e smoke

# Regression suite
/f5-test-e2e regression --report

# Visual testing
/f5-test-e2e visual                      # Basic
/f5-test-e2e visual --compare-figma      # Compare with Figma
/f5-test-e2e visual --apply-fixes        # Auto-fix CSS
/f5-test-e2e visual --update-baseline    # Update baseline
/f5-test-e2e visual --ci --threshold 5   # CI mode

# Generate from design
/f5-test-e2e generate-from-design login

# Browser options
/f5-test-e2e journey checkout --browser firefox
/f5-test-e2e page login --headed  # Non-headless
```

---

## G3 GATE INTEGRATION

Visual testing runs at both G2.5 and G3 gates:

| Gate | Command | Purpose |
|------|---------|---------|
| G2.5 | `/f5-test-e2e visual --compare-figma` | Compare with design |
| G3 | `/f5-test-e2e visual --ci` | Regression testing |

---

## SEE ALSO

- `/f5-test` - Master test command
- `/f5-test-unit` - Unit testing
- `/f5-test-it` - Integration testing
- `/f5-tdd` - TDD workflow
- `/f5-mcp` - MCP management (Playwright)
- `/f5-gate` - Quality gates (G3)
- `_test-shared.md` - Stack detection, MCP patterns, G3 integration
