---
name: images-alt-text
description: Writing effective alt text for images
category: accessibility/media
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# Images & Alt Text

## Overview

Alt text (alternative text) describes images for users who cannot see them. Good alt text conveys the same information or function as the image.

## Alt Text Basics

### When Alt Text is Required

| Image Type | Alt Text | Example |
|------------|----------|---------|
| Informative | Describes content | Photo, diagram |
| Functional | Describes action | Button, link |
| Decorative | Empty (alt="") | Background, spacer |
| Complex | Brief + long description | Chart, infographic |

### Basic Syntax

```html
<!-- Informative image -->
<img src="dog.jpg" alt="Golden retriever playing fetch in a park">

<!-- Decorative image (empty alt) -->
<img src="decorative-line.png" alt="">

<!-- Background/decorative via CSS -->
<div class="hero" role="img" aria-label="Mountain landscape at sunset">
</div>
```

## Writing Good Alt Text

### Be Specific and Concise

```html
<!-- ❌ Too vague -->
<img src="team.jpg" alt="Photo">
<img src="team.jpg" alt="Image">
<img src="team.jpg" alt="Team photo">

<!-- ✅ Descriptive but concise -->
<img src="team.jpg" alt="Five team members gathered around a whiteboard during a brainstorming session">

<!-- ❌ Too long -->
<img src="logo.png" alt="The official logo of Acme Corporation which was founded in 1985 and has been serving customers worldwide with quality products and services">

<!-- ✅ Concise -->
<img src="logo.png" alt="Acme Corporation logo">
```

### Describe Function, Not Appearance

```html
<!-- For functional images, describe what it does -->

<!-- ❌ Describes appearance -->
<a href="/search">
  <img src="magnifying-glass.svg" alt="Magnifying glass icon">
</a>

<!-- ✅ Describes function -->
<a href="/search">
  <img src="magnifying-glass.svg" alt="Search">
</a>

<!-- ❌ Describes appearance -->
<button>
  <img src="x-icon.svg" alt="X">
</button>

<!-- ✅ Describes function -->
<button>
  <img src="x-icon.svg" alt="Close dialog">
</button>
```

### Context Matters

```html
<!-- Same image, different contexts -->

<!-- On a pet adoption site -->
<img src="dog.jpg" alt="Max, a 3-year-old golden retriever available for adoption">

<!-- On a photography portfolio -->
<img src="dog.jpg" alt="Portrait of a golden retriever in soft natural light">

<!-- On a veterinary site -->
<img src="dog.jpg" alt="Healthy adult golden retriever showing ideal weight and coat condition">
```

## Image Types

### Informative Images

```html
<!-- Photos that convey information -->
<img 
  src="product.jpg" 
  alt="Blue wireless headphones with silver accents and cushioned ear pads"
>

<!-- Diagrams -->
<img 
  src="workflow.png" 
  alt="Three-step workflow: Design, Develop, Deploy"
>

<!-- Screenshots -->
<img 
  src="settings-screen.png" 
  alt="Settings screen showing notification preferences with email alerts enabled"
>
```

### Functional Images

```html
<!-- Linked logo -->
<a href="/">
  <img src="logo.png" alt="Acme Corp - Home">
</a>

<!-- Image button -->
<button type="submit">
  <img src="search.svg" alt="Search">
</button>

<!-- Image as only content of link -->
<a href="https://twitter.com/company">
  <img src="twitter.svg" alt="Follow us on Twitter">
</a>
```

### Decorative Images

```html
<!-- Pure decoration - empty alt -->
<img src="decorative-divider.png" alt="">

<!-- Icon with adjacent text -->
<button>
  <img src="download.svg" alt=""> <!-- Empty, text provides meaning -->
  Download PDF
</button>

<!-- Background images via CSS (preferred) -->
<style>
.hero {
  background-image: url('hero-bg.jpg');
}
</style>

<!-- Or use role="presentation" -->
<img src="decorative.png" alt="" role="presentation">
```

### Complex Images

```html
<!-- Charts and graphs need detailed descriptions -->
<figure>
  <img 
    src="sales-chart.png" 
    alt="Bar chart showing quarterly sales"
    aria-describedby="chart-description"
  >
  <figcaption id="chart-description">
    Quarterly sales for 2024: Q1 $1.2M, Q2 $1.5M, Q3 $1.8M, Q4 $2.1M.
    Sales increased 75% over the year.
  </figcaption>
</figure>

<!-- Infographic with detailed description -->
<figure>
  <img 
    src="infographic.png" 
    alt="COVID-19 safety guidelines infographic"
  >
  <details>
    <summary>Full description of infographic</summary>
    <p>The infographic shows five safety guidelines:</p>
    <ol>
      <li>Wear a mask in indoor public spaces</li>
      <li>Maintain 6 feet distance from others</li>
      <!-- ... -->
    </ol>
  </details>
</figure>
```

### Image Maps

```html
<img 
  src="map.png" 
  alt="Office floor plan" 
  usemap="#floorplan"
>
<map name="floorplan">
  <area 
    shape="rect" 
    coords="0,0,100,100" 
    href="/room-a" 
    alt="Conference Room A"
  >
  <area 
    shape="rect" 
    coords="100,0,200,100" 
    href="/room-b" 
    alt="Conference Room B"
  >
</map>
```

## Figure and Figcaption

```html
<!-- Image with visible caption -->
<figure>
  <img 
    src="team-retreat.jpg" 
    alt="Team members hiking on a mountain trail"
  >
  <figcaption>
    Annual team retreat at Mount Rainier, September 2024
  </figcaption>
</figure>

<!-- Caption doesn't replace alt text -->
<!-- Alt describes image; caption provides context -->

<!-- Multiple images in figure -->
<figure>
  <img src="before.jpg" alt="Office space with cluttered desks and poor lighting">
  <img src="after.jpg" alt="Same office space with organized desks and natural light">
  <figcaption>Office renovation: before and after</figcaption>
</figure>
```

## SVG Accessibility

```html
<!-- Decorative SVG -->
<svg aria-hidden="true" focusable="false">
  <!-- decorative icon -->
</svg>

<!-- Informative SVG -->
<svg role="img" aria-labelledby="svg-title">
  <title id="svg-title">Company Logo</title>
  <!-- SVG content -->
</svg>

<!-- SVG with description -->
<svg role="img" aria-labelledby="chart-title chart-desc">
  <title id="chart-title">Monthly Revenue</title>
  <desc id="chart-desc">Bar chart showing revenue increased from $10K to $50K over 6 months</desc>
  <!-- SVG content -->
</svg>

<!-- Interactive SVG -->
<svg role="img" aria-label="Interactive map of United States">
  <g role="list" aria-label="States">
    <path role="listitem" aria-label="California" tabindex="0" />
    <path role="listitem" aria-label="Texas" tabindex="0" />
  </g>
</svg>
```

## Responsive Images

```html
<!-- srcset with alt text -->
<img 
  src="hero-small.jpg"
  srcset="hero-small.jpg 400w, hero-medium.jpg 800w, hero-large.jpg 1200w"
  sizes="(max-width: 600px) 400px, (max-width: 1000px) 800px, 1200px"
  alt="Developer working at a standing desk with multiple monitors"
>

<!-- Picture element -->
<picture>
  <source media="(min-width: 1200px)" srcset="hero-desktop.jpg">
  <source media="(min-width: 768px)" srcset="hero-tablet.jpg">
  <img src="hero-mobile.jpg" alt="Team collaboration in modern office">
</picture>
```

## Common Mistakes

```html
<!-- ❌ Starting with "Image of" or "Picture of" -->
<img src="sunset.jpg" alt="Image of a sunset">

<!-- ✅ Describe directly -->
<img src="sunset.jpg" alt="Orange and purple sunset over the ocean">

<!-- ❌ File name as alt text -->
<img src="IMG_3847.jpg" alt="IMG_3847.jpg">

<!-- ✅ Meaningful description -->
<img src="IMG_3847.jpg" alt="Product packaging showing front label">

<!-- ❌ Missing alt attribute entirely -->
<img src="photo.jpg">

<!-- ✅ Always include alt (empty if decorative) -->
<img src="photo.jpg" alt="">

<!-- ❌ Alt text too long (screen reader reads all) -->
<img src="chart.png" alt="This comprehensive chart illustrates our company's quarterly performance metrics including revenue growth of 25% in Q1, followed by 32% in Q2, then 28% in Q3, and finally 45% in Q4, with additional breakdowns by product line showing widgets at 40%, gadgets at 35%, and services at 25% of total revenue...">

<!-- ✅ Brief alt with separate description -->
<img src="chart.png" alt="Quarterly performance chart" aria-describedby="chart-details">
<div id="chart-details">Detailed description...</div>
```

## Testing Alt Text

### Screen Reader Announcement

```markdown
Test that screen readers announce:
1. Informative images: Alt text is read
2. Functional images: Purpose is clear
3. Decorative images: Nothing is read
4. Complex images: Brief description + access to details
```

### Automated Testing

```javascript
// Check for missing alt attributes
document.querySelectorAll('img').forEach(img => {
  if (!img.hasAttribute('alt')) {
    console.error('Missing alt:', img.src);
  }
});

// Check for suspicious alt text
document.querySelectorAll('img[alt]').forEach(img => {
  const alt = img.alt.toLowerCase();
  if (alt.includes('image of') || alt.includes('picture of')) {
    console.warn('Redundant alt text:', alt);
  }
  if (alt.match(/\.(jpg|png|gif|svg)$/)) {
    console.warn('File name in alt:', alt);
  }
});
```

## Summary

| Image Type | Alt Text Approach |
|------------|-------------------|
| Informative | Describe content/meaning |
| Functional | Describe action/destination |
| Decorative | Empty alt="" |
| Complex | Brief + long description |
| Logo link | "Company Name - Home" |
| Icon + text | Empty alt="" (text suffices) |
| Icon only | Describe function |
