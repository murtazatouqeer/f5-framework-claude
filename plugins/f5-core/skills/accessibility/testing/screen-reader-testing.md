---
name: screen-reader-testing
description: Testing with screen readers (NVDA, VoiceOver, JAWS)
category: accessibility/testing
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# Screen Reader Testing

## Overview

Screen readers convert digital content to speech or braille. Testing with screen readers is essential to verify that content is accessible to blind and low-vision users.

## Popular Screen Readers

| Screen Reader | Platform | Cost |
|---------------|----------|------|
| NVDA | Windows | Free |
| VoiceOver | macOS/iOS | Built-in |
| JAWS | Windows | Paid |
| TalkBack | Android | Built-in |
| Narrator | Windows | Built-in |
| Orca | Linux | Free |

## NVDA (Windows)

### Installation & Setup

```markdown
1. Download from nvaccess.org
2. Install (standard or portable)
3. Start NVDA: Ctrl+Alt+N

Key settings:
- Preferences > Settings > Speech
- Preferences > Settings > Browse Mode
```

### Essential Commands

| Action | Shortcut |
|--------|----------|
| Start/Stop speech | Ctrl |
| Read from current position | NVDA+Down Arrow |
| Read current line | NVDA+Up Arrow |
| Read current word | NVDA+Numpad5 |
| Read current character | Numpad2 |
| Next heading | H |
| Next link | K |
| Next form field | F |
| Next landmark | D |
| Next table | T |
| Elements list | NVDA+F7 |
| Toggle browse/focus mode | NVDA+Space |

### Browse Mode vs Focus Mode

```markdown
## Browse Mode (virtual cursor)
- Navigate with arrow keys
- Use single letter navigation (H, K, F)
- Default for reading content

## Focus Mode (application mode)
- Direct keyboard input
- For typing in forms
- NVDA+Space to switch

## Automatic switching
- Entering form field: auto-focus mode
- Leaving form: auto-browse mode
```

### Testing Checklist

```markdown
## NVDA Testing Checklist

### Page Load
- [ ] Page title announced
- [ ] Main heading (h1) found easily
- [ ] Skip link works

### Navigation
- [ ] All links reachable with K
- [ ] All headings reachable with H
- [ ] Heading hierarchy correct
- [ ] Landmarks navigable with D

### Forms
- [ ] All fields have labels announced
- [ ] Required fields identified
- [ ] Error messages announced
- [ ] Instructions available

### Interactive Elements
- [ ] Button purpose clear
- [ ] Menu announced correctly
- [ ] Tab panels work
- [ ] Dialogs trap focus

### Dynamic Content
- [ ] Live regions announce updates
- [ ] Loading states announced
- [ ] Error alerts announced
```

## VoiceOver (macOS)

### Getting Started

```markdown
1. Enable: System Preferences > Accessibility > VoiceOver
2. Start/Stop: Cmd+F5
3. VoiceOver key (VO): Ctrl+Option

Quick settings:
- VO+Cmd+Right Arrow: Open rotor
- VO+H: Help menu
```

### Essential Commands

| Action | Shortcut |
|--------|----------|
| Start/Stop VoiceOver | Cmd+F5 |
| Read all | VO+A |
| Stop speaking | Ctrl |
| Next item | VO+Right Arrow |
| Previous item | VO+Left Arrow |
| Interact with element | VO+Shift+Down Arrow |
| Stop interacting | VO+Shift+Up Arrow |
| Web rotor | VO+U |
| Next heading | VO+Cmd+H |
| Next link | VO+Cmd+L |
| Next form control | VO+Cmd+J |

### Web Rotor

```markdown
## Using the Web Rotor (VO+U)

The rotor provides quick access to:
- Headings (navigate by level)
- Links
- Form controls
- Landmarks
- Tables
- Web spots (custom bookmarks)

Navigate rotor:
- Left/Right: Switch category
- Up/Down: Navigate within category
- Enter: Go to item
- Escape: Close rotor
```

### Testing Checklist

```markdown
## VoiceOver macOS Testing Checklist

### Initial Load
- [ ] Page title announced
- [ ] Can navigate to main content

### Rotor Navigation
- [ ] Headings list complete and accurate
- [ ] Links list meaningful
- [ ] Forms list shows all fields
- [ ] Landmarks present

### Content Reading
- [ ] All content accessible
- [ ] Images have alt text (or skipped if decorative)
- [ ] Tables readable (headers announced)

### Interactions
- [ ] All buttons operable
- [ ] Forms completable
- [ ] Menus navigable
- [ ] Dialogs accessible
```

## VoiceOver (iOS)

### Essential Gestures

| Action | Gesture |
|--------|---------|
| Toggle VoiceOver | Triple-click home/side |
| Read item | Tap |
| Move to next item | Swipe right |
| Move to previous item | Swipe left |
| Activate item | Double-tap |
| Scroll | Three-finger swipe |
| Open rotor | Two-finger rotate |
| Change rotor setting | One-finger swipe up/down |

### Rotor Settings

```markdown
## iOS Rotor Navigation

1. Two-finger rotate to open rotor
2. Rotate to select: Headings, Links, Form Controls
3. Swipe up/down to navigate within category

Essential rotor options:
- Headings
- Links
- Form Controls
- Landmarks
- Characters/Words/Lines (in text)
```

## JAWS (Windows)

### Essential Commands

| Action | Shortcut |
|--------|----------|
| Start JAWS | Windows+J |
| Stop speech | Ctrl |
| Read all | Insert+Down Arrow |
| Virtual cursor | PC Cursor vs JAWS Cursor |
| Elements list | Insert+F3 |
| Next heading | H |
| Heading level | 1-6 |
| Next link | Tab (unvisited) / V (visited) |
| Next form field | F |
| Forms mode | Enter on field |

### Settings

```markdown
## JAWS Settings

1. Verbosity: Adjust announcements level
   - Settings > Speech and Sounds

2. Browse mode settings:
   - Settings > Virtual PC Options

3. Web settings:
   - Settings > Speech and Sounds > Web Settings
```

## TalkBack (Android)

### Essential Gestures

| Action | Gesture |
|--------|---------|
| Read item | Tap |
| Next item | Swipe right |
| Previous item | Swipe left |
| Activate | Double-tap |
| Scroll | Two-finger swipe |
| Local context menu | Swipe up then right |
| Global context menu | Swipe down then right |

### Reading Controls

```markdown
## TalkBack Reading Controls

Swipe up/down to change:
- Characters
- Words
- Lines
- Paragraphs
- Headings
- Links
- Controls

Then swipe right/left to navigate.
```

## Testing Workflow

### Basic Test Script

```markdown
## Screen Reader Testing Script

### 1. Page Load (2 min)
- Start screen reader
- Navigate to page
- Verify: Title, main heading, skip link

### 2. Structure Navigation (5 min)
- List all headings (NVDA+F7 / VO+U)
- Check hierarchy and completeness
- Navigate landmarks
- Verify page structure

### 3. Content Reading (5 min)
- Read through main content
- Verify images have appropriate alt text
- Check lists are properly formatted
- Verify tables have headers

### 4. Interactive Elements (5 min)
- Tab through all interactive elements
- Verify button/link purpose clear
- Test form completion
- Test any custom widgets

### 5. Dynamic Content (3 min)
- Trigger dynamic updates
- Verify announcements
- Test error states
- Check loading indicators
```

### Issue Documentation

```markdown
## Screen Reader Issue Template

**Screen Reader:** [NVDA 2024.1 / VoiceOver 14.0 / etc.]
**Browser:** [Chrome 120 / Safari 17 / Firefox 120]
**OS:** [Windows 11 / macOS 14 / iOS 17]

**Issue:** [Brief description]

**Steps to Reproduce:**
1. Start [screen reader]
2. Navigate to [page/element]
3. Perform [action]

**Expected:** [What should be announced]

**Actual:** [What was announced]

**Recording:** [Optional audio/video]
```

## Common Issues

### Issue: Nothing Announced

```html
<!-- Problem: Custom element not announced -->
<div onclick="doSomething()">Click me</div>

<!-- Solution: Add role and keyboard support -->
<div 
  role="button" 
  tabindex="0" 
  onclick="doSomething()"
  onkeydown="handleKey(event)"
>
  Click me
</div>
```

### Issue: Redundant Announcements

```html
<!-- Problem: Icon described + visible text -->
<button>
  <img src="search.svg" alt="Search">
  Search
</button>
<!-- Announces: "Search Search button" -->

<!-- Solution: Hide decorative icon -->
<button>
  <img src="search.svg" alt="" aria-hidden="true">
  Search
</button>
<!-- Announces: "Search button" -->
```

### Issue: Missing Context

```html
<!-- Problem: Link text not descriptive -->
<p>Learn about our services. <a href="/services">Click here</a></p>
<!-- Announces: "Click here link" (no context) -->

<!-- Solution: Descriptive link text -->
<p>Learn about <a href="/services">our services</a>.</p>
<!-- Announces: "our services link" -->
```

## Testing Matrix

| Test | NVDA | VoiceOver | JAWS | TalkBack |
|------|------|-----------|------|----------|
| Headings | H | VO+Cmd+H | H | Rotor |
| Links | K | VO+Cmd+L | Tab/V | Rotor |
| Forms | F | VO+Cmd+J | F | Rotor |
| Landmarks | D | Rotor | R | Rotor |
| Tables | T | VO+Cmd+T | T | Rotor |
| Lists | L | Rotor | L | Rotor |
| Elements list | NVDA+F7 | VO+U | Insert+F3 | Menu |

## Summary

| Screen Reader | Primary Use | Key Skill |
|---------------|-------------|-----------|
| NVDA | Primary Windows testing | Browse/Focus mode |
| VoiceOver macOS | Primary Mac testing | Rotor navigation |
| VoiceOver iOS | Mobile testing | Gesture navigation |
| JAWS | Enterprise testing | Virtual cursor |
| TalkBack | Android testing | Gesture + rotor |
