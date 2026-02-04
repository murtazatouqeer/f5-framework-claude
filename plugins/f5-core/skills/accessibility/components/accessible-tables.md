---
name: accessible-tables
description: Creating accessible data tables
category: accessibility/components
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# Accessible Tables

## Overview

Tables present structured data in rows and columns. Proper table markup enables screen reader users to understand relationships between cells and navigate efficiently.

## When to Use Tables

### Use Tables For
- Tabular data with row/column relationships
- Spreadsheet-like data
- Comparison matrices
- Schedules and timetables

### Don't Use Tables For
- Page layout
- Visual alignment only
- Single-column lists

## Basic Table Structure

### Simple Table

```html
<table>
  <caption>Monthly Sales Report</caption>
  <thead>
    <tr>
      <th scope="col">Month</th>
      <th scope="col">Sales</th>
      <th scope="col">Revenue</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th scope="row">January</th>
      <td>150</td>
      <td>$15,000</td>
    </tr>
    <tr>
      <th scope="row">February</th>
      <td>200</td>
      <td>$20,000</td>
    </tr>
  </tbody>
</table>
```

### Table Elements

| Element | Purpose |
|---------|---------|
| `<table>` | Container for tabular data |
| `<caption>` | Table title/description |
| `<thead>` | Header row group |
| `<tbody>` | Body row group |
| `<tfoot>` | Footer row group |
| `<tr>` | Table row |
| `<th>` | Header cell |
| `<td>` | Data cell |

## Headers and Scope

### Column Headers

```html
<table>
  <thead>
    <tr>
      <th scope="col">Product</th>
      <th scope="col">Price</th>
      <th scope="col">Quantity</th>
    </tr>
  </thead>
  <!-- ... -->
</table>
```

### Row Headers

```html
<table>
  <tbody>
    <tr>
      <th scope="row">Apples</th>
      <td>$2.00</td>
      <td>50</td>
    </tr>
    <tr>
      <th scope="row">Oranges</th>
      <td>$1.50</td>
      <td>75</td>
    </tr>
  </tbody>
</table>
```

### Both Column and Row Headers

```html
<table>
  <caption>Quarterly Sales by Region</caption>
  <thead>
    <tr>
      <th scope="col">Region</th>
      <th scope="col">Q1</th>
      <th scope="col">Q2</th>
      <th scope="col">Q3</th>
      <th scope="col">Q4</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th scope="row">North</th>
      <td>$10,000</td>
      <td>$12,000</td>
      <td>$15,000</td>
      <td>$18,000</td>
    </tr>
    <tr>
      <th scope="row">South</th>
      <td>$8,000</td>
      <td>$9,500</td>
      <td>$11,000</td>
      <td>$14,000</td>
    </tr>
  </tbody>
</table>
```

## Complex Tables

### Multi-level Headers

```html
<table>
  <caption>Student Grades by Subject</caption>
  <thead>
    <tr>
      <th rowspan="2" scope="col">Student</th>
      <th colspan="2" scope="colgroup">Math</th>
      <th colspan="2" scope="colgroup">Science</th>
    </tr>
    <tr>
      <th scope="col">Midterm</th>
      <th scope="col">Final</th>
      <th scope="col">Midterm</th>
      <th scope="col">Final</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th scope="row">Alice</th>
      <td>85</td>
      <td>90</td>
      <td>88</td>
      <td>92</td>
    </tr>
    <tr>
      <th scope="row">Bob</th>
      <td>78</td>
      <td>82</td>
      <td>80</td>
      <td>85</td>
    </tr>
  </tbody>
</table>
```

### Using headers Attribute

```html
<table>
  <caption>Expenses by Department</caption>
  <thead>
    <tr>
      <td></td>
      <th id="q1" scope="col">Q1</th>
      <th id="q2" scope="col">Q2</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th id="marketing" scope="row">Marketing</th>
      <td headers="marketing q1">$5,000</td>
      <td headers="marketing q2">$6,000</td>
    </tr>
    <tr>
      <th id="sales" scope="row">Sales</th>
      <td headers="sales q1">$8,000</td>
      <td headers="sales q2">$9,500</td>
    </tr>
  </tbody>
</table>
```

## Captions and Summaries

### Table Caption

```html
<table>
  <caption>
    Employee Directory
    <span class="table-description">
      Contact information for all departments
    </span>
  </caption>
  <!-- ... -->
</table>
```

### Alternative: aria-labelledby

```html
<h2 id="table-title">Employee Directory</h2>
<p id="table-desc">Contact information for all departments</p>
<table aria-labelledby="table-title" aria-describedby="table-desc">
  <!-- ... -->
</table>
```

## Sortable Tables

### Indicating Sort State

```html
<table>
  <thead>
    <tr>
      <th scope="col">
        <button 
          aria-sort="ascending"
          onclick="sortTable('name')"
        >
          Name
          <span aria-hidden="true">▲</span>
        </button>
      </th>
      <th scope="col">
        <button 
          aria-sort="none"
          onclick="sortTable('date')"
        >
          Date
          <span aria-hidden="true">⇅</span>
        </button>
      </th>
    </tr>
  </thead>
  <!-- ... -->
</table>
```

### Sort Implementation

```javascript
function sortTable(column) {
  const table = document.querySelector('table');
  const headers = table.querySelectorAll('th button');
  const currentHeader = table.querySelector(`[onclick="sortTable('${column}')"]`);
  const currentSort = currentHeader.getAttribute('aria-sort');
  
  // Reset all headers
  headers.forEach(header => {
    header.setAttribute('aria-sort', 'none');
    header.querySelector('span').textContent = '⇅';
  });
  
  // Set new sort direction
  const newSort = currentSort === 'ascending' ? 'descending' : 'ascending';
  currentHeader.setAttribute('aria-sort', newSort);
  currentHeader.querySelector('span').textContent = newSort === 'ascending' ? '▲' : '▼';
  
  // Announce to screen readers
  announceSort(column, newSort);
  
  // Perform actual sort...
}

function announceSort(column, direction) {
  const announcement = document.getElementById('sort-announcement');
  announcement.textContent = `Table sorted by ${column}, ${direction}`;
}
```

```html
<div aria-live="polite" id="sort-announcement" class="visually-hidden"></div>
```

## Selectable Rows

### Checkbox Selection

```html
<table role="grid" aria-label="File list">
  <thead>
    <tr>
      <th scope="col">
        <input 
          type="checkbox" 
          aria-label="Select all files"
          onchange="toggleAll(this)"
        >
      </th>
      <th scope="col">File Name</th>
      <th scope="col">Size</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>
        <input 
          type="checkbox" 
          aria-label="Select document.pdf"
        >
      </td>
      <td>document.pdf</td>
      <td>2.5 MB</td>
    </tr>
    <tr>
      <td>
        <input 
          type="checkbox" 
          aria-label="Select image.png"
        >
      </td>
      <td>image.png</td>
      <td>1.2 MB</td>
    </tr>
  </tbody>
</table>
```

### Selection Status

```html
<p aria-live="polite" id="selection-status">
  2 of 10 items selected
</p>
```

## Responsive Tables

### Horizontal Scroll

```html
<div class="table-container" tabindex="0" role="region" aria-labelledby="table-caption">
  <table>
    <caption id="table-caption">Wide Data Table</caption>
    <!-- ... -->
  </table>
</div>

<style>
.table-container {
  overflow-x: auto;
  max-width: 100%;
}

.table-container:focus {
  outline: 2px solid #005fcc;
}
</style>
```

### Stacked Layout

```html
<table class="responsive-table">
  <thead>
    <tr>
      <th scope="col">Name</th>
      <th scope="col">Email</th>
      <th scope="col">Phone</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td data-label="Name">John Smith</td>
      <td data-label="Email">john@example.com</td>
      <td data-label="Phone">(555) 123-4567</td>
    </tr>
  </tbody>
</table>

<style>
@media (max-width: 600px) {
  .responsive-table thead {
    position: absolute;
    left: -9999px;
  }
  
  .responsive-table tr {
    display: block;
    margin-bottom: 1rem;
    border: 1px solid #ccc;
  }
  
  .responsive-table td {
    display: block;
    padding: 0.5rem;
  }
  
  .responsive-table td::before {
    content: attr(data-label) ": ";
    font-weight: bold;
  }
}
</style>
```

## Data Grids

### Interactive Grid Pattern

```html
<table role="grid" aria-label="Spreadsheet">
  <thead>
    <tr>
      <th scope="col" role="columnheader">A</th>
      <th scope="col" role="columnheader">B</th>
      <th scope="col" role="columnheader">C</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td role="gridcell" tabindex="0">Cell A1</td>
      <td role="gridcell" tabindex="-1">Cell B1</td>
      <td role="gridcell" tabindex="-1">Cell C1</td>
    </tr>
    <tr>
      <td role="gridcell" tabindex="-1">Cell A2</td>
      <td role="gridcell" tabindex="-1">Cell B2</td>
      <td role="gridcell" tabindex="-1">Cell C2</td>
    </tr>
  </tbody>
</table>
```

### Grid Navigation

```javascript
const grid = document.querySelector('[role="grid"]');
let currentRow = 0;
let currentCol = 0;

grid.addEventListener('keydown', (event) => {
  const rows = grid.querySelectorAll('tbody tr');
  const cells = rows[currentRow].querySelectorAll('[role="gridcell"]');
  
  switch(event.key) {
    case 'ArrowRight':
      if (currentCol < cells.length - 1) {
        currentCol++;
        focusCell(currentRow, currentCol);
      }
      break;
    case 'ArrowLeft':
      if (currentCol > 0) {
        currentCol--;
        focusCell(currentRow, currentCol);
      }
      break;
    case 'ArrowDown':
      if (currentRow < rows.length - 1) {
        currentRow++;
        focusCell(currentRow, currentCol);
      }
      break;
    case 'ArrowUp':
      if (currentRow > 0) {
        currentRow--;
        focusCell(currentRow, currentCol);
      }
      break;
    case 'Home':
      currentCol = 0;
      focusCell(currentRow, currentCol);
      break;
    case 'End':
      currentCol = cells.length - 1;
      focusCell(currentRow, currentCol);
      break;
  }
});

function focusCell(row, col) {
  // Update tabindex
  grid.querySelectorAll('[tabindex="0"]').forEach(cell => {
    cell.setAttribute('tabindex', '-1');
  });
  
  const targetCell = grid.querySelectorAll('tbody tr')[row]
    .querySelectorAll('[role="gridcell"]')[col];
  targetCell.setAttribute('tabindex', '0');
  targetCell.focus();
}
```

## CSS Styling

```css
/* Basic table styling */
table {
  width: 100%;
  border-collapse: collapse;
  margin: 1rem 0;
}

caption {
  font-weight: bold;
  text-align: left;
  padding: 0.5rem 0;
}

th, td {
  padding: 0.75rem;
  text-align: left;
  border-bottom: 1px solid #ddd;
}

th {
  background-color: #f5f5f5;
  font-weight: bold;
}

/* Row hover */
tbody tr:hover {
  background-color: #f9f9f9;
}

/* Focus styles */
th:focus-within,
td:focus-within {
  outline: 2px solid #005fcc;
  outline-offset: -2px;
}

/* Sortable header buttons */
th button {
  background: none;
  border: none;
  font: inherit;
  cursor: pointer;
  width: 100%;
  text-align: left;
  padding: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

th button:focus-visible {
  outline: 2px solid #005fcc;
}

/* Zebra striping */
tbody tr:nth-child(even) {
  background-color: #fafafa;
}

/* High contrast mode */
@media (forced-colors: active) {
  th, td {
    border: 1px solid CanvasText;
  }
}
```

## Testing Checklist

```markdown
## Table Accessibility Checklist

### Structure
- [ ] Table used for tabular data only
- [ ] Caption or aria-label present
- [ ] Headers use <th> elements
- [ ] scope attribute on headers

### Headers
- [ ] Column headers have scope="col"
- [ ] Row headers have scope="row"
- [ ] Complex tables use headers attribute
- [ ] Multi-level headers properly grouped

### Screen Reader
- [ ] Table purpose announced
- [ ] Headers read with data cells
- [ ] Navigation between cells works
- [ ] Sort state announced

### Keyboard
- [ ] Interactive elements focusable
- [ ] Arrow key navigation (for grids)
- [ ] Focus indicator visible

### Responsive
- [ ] Scrollable container focusable
- [ ] Data accessible at all sizes
- [ ] Labels visible in stacked layout
```

## Common Issues

### Missing Headers

```html
<!-- Problem: No scope -->
<th>Name</th>

<!-- Solution: Add scope -->
<th scope="col">Name</th>
```

### Missing Caption

```html
<!-- Problem: No table description -->
<table>
  <tr><th>Name</th></tr>
</table>

<!-- Solution: Add caption -->
<table>
  <caption>Employee List</caption>
  <tr><th scope="col">Name</th></tr>
</table>
```

### Layout Tables

```html
<!-- Problem: Table for layout -->
<table>
  <tr>
    <td>Navigation</td>
    <td>Content</td>
  </tr>
</table>

<!-- Solution: Use CSS Grid/Flexbox -->
<div class="layout">
  <nav>Navigation</nav>
  <main>Content</main>
</div>
```

## Summary

| Requirement | Implementation |
|-------------|----------------|
| Caption | `<caption>` or `aria-labelledby` |
| Headers | `<th>` with `scope` attribute |
| Complex headers | `headers` attribute with IDs |
| Sort indication | `aria-sort` on sortable columns |
| Responsive | Scrollable container or stacked |
| Grid pattern | `role="grid"` with keyboard nav |
