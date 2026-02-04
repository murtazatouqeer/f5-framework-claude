---
name: semantic-html
description: Using semantic HTML elements for accessible structure
category: accessibility/html
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# Semantic HTML

## Overview

Semantic HTML uses elements that clearly describe their meaning to browsers and assistive technologies. Using the right element for the right purpose is the foundation of accessibility.

## Why Semantic HTML Matters

| Aspect | Non-Semantic | Semantic |
|--------|--------------|----------|
| Structure | `<div class="header">` | `<header>` |
| Navigation | `<div class="nav">` | `<nav>` |
| Main content | `<div class="content">` | `<main>` |
| AT support | Requires ARIA | Built-in |

## Structural Elements

### Document Structure

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Page Title - Site Name</title>
</head>
<body>
  <header>
    <nav aria-label="Main">...</nav>
  </header>
  
  <main>
    <article>
      <h1>Article Title</h1>
      <section>...</section>
    </article>
    <aside>...</aside>
  </main>
  
  <footer>...</footer>
</body>
</html>
```

### Header Element

```html
<!-- Page header -->
<header>
  <a href="/" aria-label="Home">
    <img src="logo.svg" alt="Company Name">
  </a>
  <nav aria-label="Main navigation">
    <ul>
      <li><a href="/">Home</a></li>
      <li><a href="/about">About</a></li>
      <li><a href="/contact">Contact</a></li>
    </ul>
  </nav>
</header>

<!-- Article header -->
<article>
  <header>
    <h1>Article Title</h1>
    <p>By <a href="/author/jane">Jane Doe</a></p>
    <time datetime="2024-01-15">January 15, 2024</time>
  </header>
  <p>Article content...</p>
</article>
```

### Main Element

```html
<!-- Only one <main> per page -->
<main id="main-content">
  <h1>Page Title</h1>
  <p>Primary content goes here...</p>
</main>

<!-- Skip link target -->
<a href="#main-content" class="skip-link">Skip to main content</a>
```

### Footer Element

```html
<footer>
  <nav aria-label="Footer navigation">
    <ul>
      <li><a href="/privacy">Privacy Policy</a></li>
      <li><a href="/terms">Terms of Service</a></li>
    </ul>
  </nav>
  <p>&copy; 2024 Company Name. All rights reserved.</p>
</footer>
```

## Content Elements

### Article vs Section

```html
<!-- Article: Self-contained, independently distributable -->
<article>
  <h2>Blog Post Title</h2>
  <p>This content makes sense on its own...</p>
</article>

<!-- Section: Thematic grouping within content -->
<section aria-labelledby="features-heading">
  <h2 id="features-heading">Features</h2>
  <p>Features of our product...</p>
</section>

<!-- Combined usage -->
<article>
  <h1>Complete Guide to Accessibility</h1>
  <section>
    <h2>Introduction</h2>
    <p>...</p>
  </section>
  <section>
    <h2>Getting Started</h2>
    <p>...</p>
  </section>
</article>
```

### Aside Element

```html
<!-- Related but not essential content -->
<main>
  <article>
    <h1>Main Article</h1>
    <p>Primary content...</p>
    
    <!-- Aside within article: related to article -->
    <aside>
      <h2>Did You Know?</h2>
      <p>Interesting related fact...</p>
    </aside>
  </article>
</main>

<!-- Sidebar aside: related to page -->
<aside aria-label="Sidebar">
  <h2>Related Articles</h2>
  <ul>
    <li><a href="/article-1">Related Article 1</a></li>
    <li><a href="/article-2">Related Article 2</a></li>
  </ul>
</aside>
```

## Text Elements

### Headings

```html
<!-- Proper heading hierarchy -->
<h1>Page Title</h1>
  <h2>Section 1</h2>
    <h3>Subsection 1.1</h3>
    <h3>Subsection 1.2</h3>
  <h2>Section 2</h2>
    <h3>Subsection 2.1</h3>

<!-- ❌ Skip levels -->
<h1>Title</h1>
<h3>Subsection</h3> <!-- Missing h2 -->
```

### Paragraphs and Text

```html
<!-- Emphasis -->
<p>This is <em>emphasized</em> text (stress emphasis).</p>
<p>This is <strong>strong</strong> text (importance).</p>

<!-- Citations and quotes -->
<blockquote cite="https://example.com/source">
  <p>A meaningful quote from an external source.</p>
  <footer>— <cite>Author Name</cite></footer>
</blockquote>

<p>As <cite>The Accessibility Handbook</cite> states...</p>

<!-- Abbreviations -->
<p>The <abbr title="World Wide Web Consortium">W3C</abbr> develops web standards.</p>

<!-- Code -->
<p>Use the <code>alt</code> attribute for images.</p>
<pre><code>function hello() {
  console.log("Hello");
}</code></pre>

<!-- Time -->
<p>Published on <time datetime="2024-01-15T09:00:00Z">January 15, 2024</time></p>
```

### Lists

```html
<!-- Unordered list -->
<ul>
  <li>First item</li>
  <li>Second item</li>
  <li>Third item</li>
</ul>

<!-- Ordered list -->
<ol>
  <li>Step one</li>
  <li>Step two</li>
  <li>Step three</li>
</ol>

<!-- Description list -->
<dl>
  <dt>Term 1</dt>
  <dd>Definition of term 1</dd>
  
  <dt>Term 2</dt>
  <dd>Definition of term 2</dd>
</dl>

<!-- Nested navigation -->
<nav aria-label="Main">
  <ul>
    <li>
      <a href="/products">Products</a>
      <ul>
        <li><a href="/products/widgets">Widgets</a></li>
        <li><a href="/products/gadgets">Gadgets</a></li>
      </ul>
    </li>
  </ul>
</nav>
```

## Interactive Elements

### Buttons vs Links

```html
<!-- Link: Navigation to another page/resource -->
<a href="/about">About Us</a>
<a href="#section">Jump to Section</a>
<a href="document.pdf" download>Download PDF</a>

<!-- Button: Actions on current page -->
<button type="button" onclick="toggleMenu()">Menu</button>
<button type="submit">Submit Form</button>
<button type="reset">Reset Form</button>

<!-- ❌ Wrong: Div as button -->
<div onclick="doSomething()">Click me</div>

<!-- ❌ Wrong: Link as button -->
<a href="#" onclick="doSomething()">Click me</a>

<!-- ✅ Right: Button for actions -->
<button type="button" onclick="doSomething()">Click me</button>
```

### Details and Summary

```html
<!-- Native disclosure widget -->
<details>
  <summary>Frequently Asked Questions</summary>
  <div>
    <h3>Question 1?</h3>
    <p>Answer to question 1...</p>
    
    <h3>Question 2?</h3>
    <p>Answer to question 2...</p>
  </div>
</details>

<!-- Styled accordion -->
<details class="accordion">
  <summary>
    <span class="accordion-title">Section Title</span>
    <span class="accordion-icon" aria-hidden="true">▼</span>
  </summary>
  <div class="accordion-content">
    <p>Expandable content...</p>
  </div>
</details>
```

### Dialog Element

```html
<!-- Native modal dialog -->
<dialog id="confirm-dialog">
  <h2>Confirm Action</h2>
  <p>Are you sure you want to proceed?</p>
  <form method="dialog">
    <button value="cancel">Cancel</button>
    <button value="confirm">Confirm</button>
  </form>
</dialog>

<button onclick="document.getElementById('confirm-dialog').showModal()">
  Open Dialog
</button>
```

## Media Elements

### Images

```html
<!-- Informative image -->
<img src="chart.png" alt="Sales chart showing 25% growth in Q4">

<!-- Decorative image -->
<img src="decoration.png" alt="" role="presentation">

<!-- Figure with caption -->
<figure>
  <img src="photo.jpg" alt="Team members at company retreat">
  <figcaption>The engineering team at our 2024 retreat</figcaption>
</figure>

<!-- Responsive images -->
<picture>
  <source media="(min-width: 800px)" srcset="large.jpg">
  <source media="(min-width: 400px)" srcset="medium.jpg">
  <img src="small.jpg" alt="Product photo">
</picture>
```

### Audio and Video

```html
<!-- Video with captions -->
<video controls>
  <source src="video.mp4" type="video/mp4">
  <track kind="captions" src="captions.vtt" srclang="en" label="English" default>
  <track kind="descriptions" src="descriptions.vtt" srclang="en" label="Audio Descriptions">
  <p>Your browser doesn't support video. <a href="video.mp4">Download video</a>.</p>
</video>

<!-- Audio with transcript -->
<figure>
  <audio controls>
    <source src="podcast.mp3" type="audio/mpeg">
    <p>Your browser doesn't support audio. <a href="podcast.mp3">Download audio</a>.</p>
  </audio>
  <figcaption>
    <details>
      <summary>View Transcript</summary>
      <p>Full transcript of the audio...</p>
    </details>
  </figcaption>
</figure>
```

## Semantic Element Reference

| Element | Purpose | When to Use |
|---------|---------|-------------|
| `<header>` | Introductory content | Page/section headers |
| `<nav>` | Navigation links | Primary/secondary navigation |
| `<main>` | Primary content | One per page |
| `<article>` | Self-contained content | Blog posts, news articles |
| `<section>` | Thematic grouping | Chapters, tabs |
| `<aside>` | Tangentially related | Sidebars, callouts |
| `<footer>` | Footer content | Page/section footers |
| `<figure>` | Self-contained media | Images, diagrams, code |
| `<figcaption>` | Figure caption | Describes figure |
| `<address>` | Contact information | Author/owner contact |
| `<time>` | Date/time | Dates, times, durations |
| `<mark>` | Highlighted text | Search results highlight |
| `<details>` | Disclosure widget | Expandable content |
| `<summary>` | Details label | Toggle for details |

## Anti-Patterns to Avoid

```html
<!-- ❌ Div soup -->
<div class="header">
  <div class="nav">
    <div class="nav-item">Home</div>
  </div>
</div>

<!-- ✅ Semantic structure -->
<header>
  <nav>
    <ul>
      <li><a href="/">Home</a></li>
    </ul>
  </nav>
</header>

<!-- ❌ Misusing elements for styling -->
<br><br><br> <!-- For spacing -->
<b>Important</b> <!-- For bold styling only -->

<!-- ✅ Use CSS for styling -->
<p class="spaced">Content</p>
<strong>Important</strong> <!-- For importance -->
```
