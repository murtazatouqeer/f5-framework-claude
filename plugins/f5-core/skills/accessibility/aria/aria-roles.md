---
name: aria-roles
description: ARIA roles reference and usage patterns
category: accessibility/aria
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# ARIA Roles

## Overview

ARIA roles define what an element is or does. They tell assistive technologies how to interpret and interact with elements.

## Role Categories

| Category | Purpose | Examples |
|----------|---------|----------|
| Landmark | Page regions | banner, main, navigation |
| Widget | Interactive elements | button, checkbox, slider |
| Document Structure | Content organization | heading, list, table |
| Live Region | Dynamic content | alert, status, log |
| Window | Dialogs and overlays | dialog, alertdialog |

## Landmark Roles

```html
<!-- Banner: Site header (implicit on <header> at body level) -->
<div role="banner">
  <img src="logo.png" alt="Company">
  <nav>...</nav>
</div>

<!-- Navigation: Navigation links -->
<div role="navigation" aria-label="Main">
  <ul>
    <li><a href="/">Home</a></li>
  </ul>
</div>

<!-- Main: Primary content (only one per page) -->
<div role="main">
  <h1>Page Title</h1>
  <p>Content...</p>
</div>

<!-- Complementary: Supporting content -->
<div role="complementary" aria-label="Related articles">
  <h2>Related</h2>
  <ul>...</ul>
</div>

<!-- Contentinfo: Site footer (implicit on <footer> at body level) -->
<div role="contentinfo">
  <p>&copy; 2024 Company</p>
</div>

<!-- Search: Search functionality -->
<form role="search" aria-label="Site search">
  <input type="search" aria-label="Search">
  <button type="submit">Search</button>
</form>

<!-- Region: Generic landmark (requires accessible name) -->
<div role="region" aria-labelledby="features-heading">
  <h2 id="features-heading">Features</h2>
  <p>...</p>
</div>
```

## Widget Roles

### Button Roles

```html
<!-- Basic button -->
<div 
  role="button" 
  tabindex="0"
  onclick="handleClick()"
  onkeydown="handleKeyDown(event)"
>
  Click Me
</div>

<!-- Toggle button -->
<div 
  role="button" 
  tabindex="0"
  aria-pressed="false"
  onclick="toggle(this)"
>
  Toggle Feature
</div>

<script>
function toggle(el) {
  const pressed = el.getAttribute('aria-pressed') === 'true';
  el.setAttribute('aria-pressed', !pressed);
}
</script>
```

### Checkbox and Radio

```html
<!-- Custom checkbox -->
<div 
  role="checkbox" 
  tabindex="0"
  aria-checked="false"
  aria-labelledby="checkbox-label"
>
  <span class="checkbox-icon" aria-hidden="true"></span>
</div>
<span id="checkbox-label">Accept terms</span>

<!-- Checkbox with mixed state -->
<div role="checkbox" aria-checked="mixed">
  Select all (some selected)
</div>

<!-- Radio group -->
<div role="radiogroup" aria-labelledby="size-label">
  <span id="size-label">Size:</span>
  <div role="radio" tabindex="0" aria-checked="true">Small</div>
  <div role="radio" tabindex="-1" aria-checked="false">Medium</div>
  <div role="radio" tabindex="-1" aria-checked="false">Large</div>
</div>
```

### Tabs

```html
<div class="tabs">
  <!-- Tab list -->
  <div role="tablist" aria-label="Product information">
    <button 
      role="tab" 
      id="tab-1"
      aria-selected="true"
      aria-controls="panel-1"
    >
      Description
    </button>
    <button 
      role="tab" 
      id="tab-2"
      aria-selected="false"
      aria-controls="panel-2"
      tabindex="-1"
    >
      Reviews
    </button>
    <button 
      role="tab" 
      id="tab-3"
      aria-selected="false"
      aria-controls="panel-3"
      tabindex="-1"
    >
      Specifications
    </button>
  </div>
  
  <!-- Tab panels -->
  <div 
    role="tabpanel" 
    id="panel-1"
    aria-labelledby="tab-1"
  >
    <h2>Product Description</h2>
    <p>...</p>
  </div>
  <div 
    role="tabpanel" 
    id="panel-2"
    aria-labelledby="tab-2"
    hidden
  >
    <h2>Customer Reviews</h2>
    <p>...</p>
  </div>
  <div 
    role="tabpanel" 
    id="panel-3"
    aria-labelledby="tab-3"
    hidden
  >
    <h2>Technical Specifications</h2>
    <p>...</p>
  </div>
</div>
```

### Listbox and Options

```html
<!-- Single select listbox -->
<label id="color-label">Choose color:</label>
<div 
  role="listbox" 
  tabindex="0"
  aria-labelledby="color-label"
  aria-activedescendant="color-red"
>
  <div role="option" id="color-red" aria-selected="true">Red</div>
  <div role="option" id="color-blue" aria-selected="false">Blue</div>
  <div role="option" id="color-green" aria-selected="false">Green</div>
</div>

<!-- Multi-select listbox -->
<div 
  role="listbox" 
  aria-multiselectable="true"
  aria-labelledby="toppings-label"
>
  <div role="option" aria-selected="true">Cheese</div>
  <div role="option" aria-selected="true">Pepperoni</div>
  <div role="option" aria-selected="false">Mushrooms</div>
</div>
```

### Combobox

```html
<label for="city-input">City:</label>
<div class="combobox-container">
  <input 
    type="text" 
    id="city-input"
    role="combobox"
    aria-expanded="false"
    aria-autocomplete="list"
    aria-controls="city-listbox"
    aria-activedescendant=""
  >
  <ul 
    id="city-listbox"
    role="listbox"
    hidden
  >
    <li role="option" id="city-1">New York</li>
    <li role="option" id="city-2">Los Angeles</li>
    <li role="option" id="city-3">Chicago</li>
  </ul>
</div>
```

### Slider

```html
<label id="volume-label">Volume</label>
<div 
  role="slider"
  tabindex="0"
  aria-labelledby="volume-label"
  aria-valuenow="50"
  aria-valuemin="0"
  aria-valuemax="100"
  aria-valuetext="50 percent"
>
  <div class="slider-track">
    <div class="slider-thumb" style="left: 50%"></div>
  </div>
</div>

<!-- Range slider -->
<div 
  role="slider"
  aria-label="Price range minimum"
  aria-valuenow="100"
  aria-valuemin="0"
  aria-valuemax="1000"
  aria-valuetext="$100"
></div>
```

### Menu

```html
<button 
  aria-haspopup="menu"
  aria-expanded="false"
  aria-controls="user-menu"
>
  Account
</button>
<ul 
  id="user-menu"
  role="menu"
  aria-label="Account options"
  hidden
>
  <li role="menuitem"><a href="/profile">Profile</a></li>
  <li role="menuitem"><a href="/settings">Settings</a></li>
  <li role="separator"></li>
  <li role="menuitem"><button>Logout</button></li>
</ul>

<!-- Menubar -->
<nav role="menubar" aria-label="Main menu">
  <div role="menuitem" aria-haspopup="menu">
    File
    <ul role="menu">
      <li role="menuitem">New</li>
      <li role="menuitem">Open</li>
      <li role="menuitem">Save</li>
    </ul>
  </div>
  <div role="menuitem" aria-haspopup="menu">
    Edit
    <ul role="menu">
      <li role="menuitem">Undo</li>
      <li role="menuitem">Redo</li>
    </ul>
  </div>
</nav>
```

### Tree

```html
<div role="tree" aria-label="File browser">
  <div role="treeitem" aria-expanded="true" aria-level="1">
    Documents
    <div role="group">
      <div role="treeitem" aria-level="2">Resume.pdf</div>
      <div role="treeitem" aria-expanded="false" aria-level="2">
        Projects
        <div role="group">
          <div role="treeitem" aria-level="3">Project A</div>
          <div role="treeitem" aria-level="3">Project B</div>
        </div>
      </div>
    </div>
  </div>
  <div role="treeitem" aria-expanded="false" aria-level="1">
    Images
  </div>
</div>
```

## Document Structure Roles

```html
<!-- Heading -->
<div role="heading" aria-level="2">Section Title</div>

<!-- List -->
<div role="list">
  <div role="listitem">Item 1</div>
  <div role="listitem">Item 2</div>
</div>

<!-- Table -->
<div role="table" aria-label="Product comparison">
  <div role="rowgroup">
    <div role="row">
      <div role="columnheader">Feature</div>
      <div role="columnheader">Basic</div>
      <div role="columnheader">Pro</div>
    </div>
  </div>
  <div role="rowgroup">
    <div role="row">
      <div role="rowheader">Storage</div>
      <div role="cell">5 GB</div>
      <div role="cell">100 GB</div>
    </div>
  </div>
</div>

<!-- Figure -->
<div role="figure" aria-labelledby="fig-caption">
  <img src="chart.png" alt="Sales data visualization">
  <div id="fig-caption">Figure 1: Q4 Sales Performance</div>
</div>

<!-- Article -->
<div role="article" aria-labelledby="article-title">
  <h2 id="article-title">Article Title</h2>
  <p>Content...</p>
</div>
```

## Window Roles

```html
<!-- Dialog -->
<div 
  role="dialog"
  aria-modal="true"
  aria-labelledby="dialog-title"
  aria-describedby="dialog-desc"
>
  <h2 id="dialog-title">Confirm Delete</h2>
  <p id="dialog-desc">Are you sure you want to delete this item?</p>
  <button>Cancel</button>
  <button>Delete</button>
</div>

<!-- Alert dialog -->
<div 
  role="alertdialog"
  aria-modal="true"
  aria-labelledby="alert-title"
  aria-describedby="alert-desc"
>
  <h2 id="alert-title">Session Expiring</h2>
  <p id="alert-desc">Your session will expire in 5 minutes.</p>
  <button>Continue Session</button>
</div>

<!-- Tooltip -->
<button aria-describedby="tooltip">Help</button>
<div role="tooltip" id="tooltip">
  Click for more information
</div>
```

## Role Reference Table

| Role | Category | Required Attributes |
|------|----------|---------------------|
| `button` | Widget | - |
| `checkbox` | Widget | aria-checked |
| `radio` | Widget | aria-checked |
| `tab` | Widget | aria-selected |
| `tabpanel` | Widget | - |
| `slider` | Widget | aria-valuenow, aria-valuemin, aria-valuemax |
| `listbox` | Widget | - |
| `option` | Widget | aria-selected |
| `combobox` | Widget | aria-expanded |
| `menu` | Widget | - |
| `menuitem` | Widget | - |
| `tree` | Widget | - |
| `treeitem` | Widget | - |
| `dialog` | Window | aria-labelledby or aria-label |
| `alertdialog` | Window | aria-labelledby or aria-label |
| `alert` | Live Region | - |
| `status` | Live Region | - |
| `heading` | Structure | aria-level |
| `region` | Landmark | aria-labelledby or aria-label |
