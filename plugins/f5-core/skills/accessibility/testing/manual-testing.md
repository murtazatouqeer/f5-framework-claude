---
name: manual-testing
description: Manual accessibility testing techniques
category: accessibility/testing
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# Manual Accessibility Testing

## Overview

Manual testing catches issues that automated tools miss. While automation can detect ~30% of accessibility issues, manual testing is essential for comprehensive coverage.

## Keyboard Testing

### Basic Navigation Test

```markdown
## Keyboard Navigation Checklist

1. [ ] Tab through all interactive elements
2. [ ] Shift+Tab navigates backwards
3. [ ] No keyboard traps
4. [ ] Focus indicator visible on all elements
5. [ ] Focus order matches visual order
6. [ ] Skip link works

## Testing Steps:
1. Unplug/disable mouse
2. Press Tab from top of page
3. Note each focused element
4. Verify you can reach all interactive elements
5. Verify you can tab away from all elements
```

### Interactive Element Testing

```markdown
## Element-Specific Tests

### Buttons
- [ ] Activated with Enter
- [ ] Activated with Space
- [ ] Focus visible

### Links
- [ ] Activated with Enter
- [ ] Focus visible
- [ ] Purpose clear from link text

### Forms
- [ ] Labels associated correctly
- [ ] Tab order logical
- [ ] Error messages accessible
- [ ] Required fields announced

### Dropdowns/Menus
- [ ] Opens with Enter/Space
- [ ] Arrow keys navigate options
- [ ] Escape closes
- [ ] Focus returns to trigger

### Dialogs/Modals
- [ ] Focus moves to dialog when opened
- [ ] Focus trapped in dialog
- [ ] Escape closes dialog
- [ ] Focus returns to trigger on close
```

### Keyboard Shortcuts

| Key | Expected Action |
|-----|-----------------|
| Tab | Next focusable element |
| Shift+Tab | Previous focusable element |
| Enter | Activate link/button |
| Space | Activate button, toggle checkbox |
| Arrow keys | Navigate within widgets |
| Escape | Close dialog/menu |
| Home/End | First/last item in list |

## Visual Testing

### Zoom Testing

```markdown
## Zoom Test (200%)

1. Set browser zoom to 200%
2. Navigate entire page
3. Check:
   - [ ] No horizontal scrolling
   - [ ] All content visible
   - [ ] No overlapping text
   - [ ] No cut-off content
   - [ ] Functionality works

## Steps by browser:
- Chrome: Ctrl/Cmd + Plus (or View > Zoom)
- Firefox: Ctrl/Cmd + Plus
- Safari: Cmd + Plus
```

### Text-Only Zoom

```markdown
## Text-Only Zoom Test

Firefox: View > Zoom > Zoom Text Only

1. Enable text-only zoom
2. Increase to 200%
3. Check:
   - [ ] Text doesn't overlap
   - [ ] Containers expand
   - [ ] No clipping
```

### Contrast Testing

```markdown
## Visual Contrast Test

1. Use browser extension (WAVE, axe)
2. Check text contrast ratios:
   - [ ] Normal text: 4.5:1 minimum
   - [ ] Large text: 3:1 minimum
   - [ ] UI components: 3:1 minimum

3. Check non-text contrast:
   - [ ] Form field borders
   - [ ] Icon meaning
   - [ ] Focus indicators
```

### Color Independence

```markdown
## Color-Only Information Test

1. View page in grayscale
   - Chrome DevTools > Rendering > Emulate vision deficiencies > Achromatopsia
   
2. Check that information conveyed by color has:
   - [ ] Text labels
   - [ ] Patterns/icons
   - [ ] Underlining (links)
   
3. Common failures:
   - Red/green only error states
   - Charts using color only
   - Links only distinguished by color
```

## Content Testing

### Heading Structure

```markdown
## Heading Audit

1. Install HeadingsMap extension
   - Or use: Accessibility Insights

2. Check:
   - [ ] Single h1 per page
   - [ ] No skipped levels (h1 → h3)
   - [ ] Headings describe content
   - [ ] Logical hierarchy

3. Extract heading outline:
   h1: Page Title
   ├── h2: Section 1
   │   ├── h3: Subsection 1.1
   │   └── h3: Subsection 1.2
   └── h2: Section 2
```

### Link Testing

```markdown
## Link Accessibility Test

1. Read links out of context
2. Check:
   - [ ] Purpose clear from link text
   - [ ] No "click here" or "read more"
   - [ ] Opens new window indicated
   - [ ] File type/size indicated

Examples:
❌ "Click here"
✅ "Download annual report (PDF, 2MB)"

❌ "Read more"
✅ "Read more about accessibility testing"
```

### Image Testing

```markdown
## Image Alt Text Audit

1. Disable images (Web Developer toolbar)
   - Or check alt text in DevTools

2. For each image, verify:
   - [ ] Alt attribute present
   - [ ] Alt text appropriate:
     - Informative: describes content
     - Functional: describes action
     - Decorative: alt=""
   - [ ] No redundant "image of"

3. Complex images have:
   - [ ] Brief alt text
   - [ ] Long description available
```

### Form Testing

```markdown
## Form Accessibility Test

1. Labels:
   - [ ] All inputs have labels
   - [ ] Labels properly associated
   - [ ] Labels visible

2. Instructions:
   - [ ] Format hints provided
   - [ ] Required fields indicated
   - [ ] Instructions before form

3. Errors:
   - [ ] Errors identified
   - [ ] Error location specified
   - [ ] Suggestions provided
   - [ ] Error summary available

4. Success:
   - [ ] Confirmation message accessible
   - [ ] Focus moves appropriately
```

## Responsive Testing

### Mobile Testing

```markdown
## Mobile/Touch Accessibility

1. Device or emulator testing:
   - [ ] Touch targets 44x44px minimum
   - [ ] Adequate spacing between targets
   - [ ] Pinch-to-zoom not disabled
   - [ ] Content reflows at 320px

2. Orientation:
   - [ ] Works in portrait and landscape
   - [ ] No content loss on rotate

3. Mobile screen readers:
   - iOS: VoiceOver
   - Android: TalkBack
```

### Reflow Testing

```markdown
## Reflow Test (320px width)

1. Set viewport to 320px width
   - Chrome DevTools > Toggle device toolbar
   - Width: 320px

2. Check:
   - [ ] No horizontal scrolling
   - [ ] Content readable
   - [ ] No two-dimensional scrolling
   - [ ] Images scale appropriately

Exceptions allowed:
- Data tables
- Maps
- Diagrams
- Video
```

## Testing Tools

### Browser Extensions

| Tool | Purpose |
|------|---------|
| axe DevTools | Automated + guided testing |
| WAVE | Visual accessibility feedback |
| Accessibility Insights | Guided manual tests |
| HeadingsMap | Heading structure |
| Web Developer | Disable images, CSS |

### DevTools Features

```markdown
## Chrome DevTools Accessibility Features

1. Accessibility panel:
   - Inspect element > Accessibility tab
   - View computed name and role
   - Check contrast ratios

2. Lighthouse:
   - Run accessibility audit
   - View detailed results

3. Rendering panel:
   - Emulate vision deficiencies
   - Emulate reduced motion

4. CSS Overview:
   - Check color contrast issues
```

## Testing Workflow

### Quick Test (5 minutes)

```markdown
1. Tab through page (keyboard traps?)
2. Check page zoom to 200%
3. Run axe DevTools quick scan
4. Verify h1 and heading order
5. Check a few images for alt text
```

### Standard Test (30 minutes)

```markdown
1. Keyboard navigation complete
2. Zoom testing (100%, 150%, 200%)
3. Color contrast check
4. Form testing (if applicable)
5. Automated tool scan
6. Screen reader spot check
7. Mobile/responsive check
```

### Comprehensive Test (2+ hours)

```markdown
1. Full keyboard audit
2. Complete visual testing
3. All content reviewed
4. All forms tested
5. Multiple automated tools
6. Full screen reader testing
7. Mobile device testing
8. User flow testing
9. Documentation review
```

## Reporting Issues

### Issue Template

```markdown
## Accessibility Issue Report

**Issue Title:** [Brief description]

**WCAG Criterion:** [e.g., 1.4.3 Contrast (Minimum)]

**Severity:** [Critical / Major / Minor]

**Location:** [Page URL + element location]

**Description:** 
[What the issue is]

**Steps to Reproduce:**
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Expected Behavior:**
[What should happen]

**Actual Behavior:**
[What actually happens]

**Recommendation:**
[How to fix]

**Screenshot/Recording:**
[Attach evidence]
```

## Summary

| Test Type | What It Catches |
|-----------|-----------------|
| Keyboard | Navigation issues, focus traps |
| Visual | Contrast, zoom, color-only info |
| Content | Alt text, headings, links |
| Forms | Labels, errors, instructions |
| Responsive | Reflow, touch targets |
