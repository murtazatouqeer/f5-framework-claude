# ARIA Reference

## Five Rules of ARIA

### 1. Don't Use ARIA If Native HTML Works

```html
<!-- ❌ ARIA checkbox -->
<div role="checkbox" aria-checked="false" tabindex="0">Agree</div>

<!-- ✅ Native checkbox -->
<input type="checkbox" id="agree">
<label for="agree">Agree</label>
```

### 2. Don't Change Native Semantics

```html
<!-- ❌ Changing button to heading -->
<button role="heading" aria-level="1">Title</button>

<!-- ✅ Use appropriate element -->
<h1>Title</h1>
```

### 3. Interactive ARIA Must Be Keyboard Accessible

```html
<div
  role="button"
  tabindex="0"
  onclick="doSomething()"
  onkeydown="handleKeyDown(event)"
>Click</div>

<script>
function handleKeyDown(e) {
  if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault();
    doSomething();
  }
}
</script>
```

### 4. Don't Hide Focusable Elements

```html
<!-- ❌ Hidden but focusable -->
<button aria-hidden="true">Click Me</button>

<!-- ✅ Properly hidden -->
<button hidden>Click Me</button>
```

### 5. Interactive Elements Must Have Names

```html
<!-- ❌ No accessible name -->
<button><svg>...</svg></button>

<!-- ✅ With accessible name -->
<button aria-label="Close">
  <svg aria-hidden="true">...</svg>
</button>
```

## Common ARIA Attributes

### Labeling

```html
<!-- aria-label: Provides label directly -->
<button aria-label="Close dialog">×</button>

<!-- aria-labelledby: References another element -->
<h2 id="dialog-title">Confirm Action</h2>
<div role="dialog" aria-labelledby="dialog-title">...</div>

<!-- aria-describedby: Additional description -->
<input type="password" id="password" aria-describedby="hint">
<span id="hint">Must be at least 8 characters</span>
```

### States

```html
<!-- aria-expanded: Expansion state -->
<button aria-expanded="false" aria-controls="menu">Menu</button>
<ul id="menu" hidden>...</ul>

<!-- aria-selected: Selection state -->
<li role="option" aria-selected="true">Option 1</li>

<!-- aria-checked: Checked state -->
<div role="checkbox" aria-checked="mixed">...</div>

<!-- aria-disabled: Disabled state -->
<button aria-disabled="true">Submit</button>

<!-- aria-hidden: Hide from AT -->
<span aria-hidden="true">★★★☆☆</span>
<span class="visually-hidden">3 out of 5 stars</span>
```

### Relationships

```html
<!-- aria-controls: Element controls another -->
<button aria-controls="content" aria-expanded="false">Toggle</button>
<div id="content">...</div>

<!-- aria-owns: Element owns another -->
<div role="listbox" aria-owns="option-1 option-2">
  <!-- Options might be elsewhere in DOM -->
</div>

<!-- aria-activedescendant: Current active child -->
<ul role="listbox" aria-activedescendant="option-2">
  <li id="option-1" role="option">One</li>
  <li id="option-2" role="option">Two</li>
</ul>
```

## Live Regions

```html
<!-- Polite: Announced when convenient -->
<div role="status" aria-live="polite">
  Items in cart: 3
</div>

<!-- Assertive: Announced immediately -->
<div role="alert" aria-live="assertive">
  Error: Form submission failed
</div>

<!-- Log: Sequential announcements -->
<div role="log" aria-live="polite">
  <!-- Chat messages appended here -->
</div>
```

## Common Widget Patterns

### Tab Panel

```html
<div role="tablist" aria-label="Settings">
  <button role="tab" aria-selected="true" aria-controls="panel1" id="tab1">
    General
  </button>
  <button role="tab" aria-selected="false" aria-controls="panel2" id="tab2">
    Security
  </button>
</div>
<div role="tabpanel" id="panel1" aria-labelledby="tab1">
  <!-- General content -->
</div>
<div role="tabpanel" id="panel2" aria-labelledby="tab2" hidden>
  <!-- Security content -->
</div>
```

### Menu

```html
<button aria-haspopup="menu" aria-expanded="false" id="menubutton">
  Options
</button>
<ul role="menu" aria-labelledby="menubutton" hidden>
  <li role="menuitem">Edit</li>
  <li role="menuitem">Delete</li>
  <li role="separator"></li>
  <li role="menuitem">Settings</li>
</ul>
```

### Combobox

```html
<label for="city">City</label>
<input
  type="text"
  id="city"
  role="combobox"
  aria-autocomplete="list"
  aria-expanded="false"
  aria-controls="city-list"
>
<ul role="listbox" id="city-list" hidden>
  <li role="option">New York</li>
  <li role="option">Los Angeles</li>
</ul>
```

## HTML5 Implicit Roles

| Element | Implicit Role | ARIA Needed? |
|---------|---------------|--------------|
| `<button>` | button | No |
| `<a href>` | link | No |
| `<nav>` | navigation | No |
| `<main>` | main | No |
| `<header>` | banner* | No |
| `<footer>` | contentinfo* | No |
| `<aside>` | complementary | No |
| `<article>` | article | No |
| `<section>` | region** | Sometimes |

\* When direct child of body
\** Only with accessible name
