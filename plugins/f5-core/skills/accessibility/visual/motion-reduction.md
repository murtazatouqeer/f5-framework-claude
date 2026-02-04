---
name: motion-reduction
description: Respecting user motion preferences
category: accessibility/visual
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# Motion Reduction

## Overview

Motion on screen can cause discomfort, dizziness, or nausea for users with vestibular disorders. Respecting motion preferences is essential for accessibility.

## WCAG Requirements

| Criterion | Requirement |
|-----------|-------------|
| 2.3.1 Three Flashes (A) | No content flashes > 3 times/second |
| 2.3.3 Animation from Interactions (AAA) | Motion can be disabled |
| Pause, Stop, Hide (A) | Auto-moving content can be paused |

## Prefers-Reduced-Motion

### Basic Implementation

```css
/* Default animations */
.element {
  transition: transform 0.3s ease;
}

.element:hover {
  transform: scale(1.05);
}

/* Disable for users who prefer reduced motion */
@media (prefers-reduced-motion: reduce) {
  .element {
    transition: none;
  }
  
  .element:hover {
    transform: none;
  }
}
```

### Global Reset

```css
/* Remove all animations for reduced motion preference */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

### Selective Approach

```css
/* Only essential animations */
@media (prefers-reduced-motion: reduce) {
  /* Keep functional transitions */
  .accordion-panel {
    transition: height 0.01ms;  /* Instant but smooth */
  }
  
  /* Remove decorative animations */
  .decorative-spinner {
    animation: none;
  }
  
  /* Replace slide with fade */
  .modal {
    animation: fadeIn 0.15s ease-out;
  }
  
  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }
}
```

## Animation Types

### Safe Animations

```css
/* Opacity changes are generally safe */
.fade-in {
  animation: fadeIn 0.3s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* Color transitions */
.button {
  transition: background-color 0.2s, color 0.2s;
}

.button:hover {
  background-color: #0052cc;
  color: white;
}
```

### Potentially Problematic

```css
/* Large movements can cause issues */
.slide-in {
  animation: slideIn 0.5s ease-out;
}

@keyframes slideIn {
  from { transform: translateX(-100%); }
  to { transform: translateX(0); }
}

/* Provide alternative */
@media (prefers-reduced-motion: reduce) {
  .slide-in {
    animation: fadeIn 0.15s ease-out;
  }
}
```

### Avoid Entirely

```css
/* ❌ Parallax scrolling */
.parallax {
  background-attachment: fixed;
  transform: translateZ(-1px) scale(2);
}

@media (prefers-reduced-motion: reduce) {
  .parallax {
    background-attachment: scroll;
    transform: none;
  }
}

/* ❌ Auto-playing carousels */
.carousel {
  animation: slideshow 10s infinite;
}

@media (prefers-reduced-motion: reduce) {
  .carousel {
    animation: none;
  }
}

/* ❌ Continuous animations */
.pulse {
  animation: pulse 1s infinite;
}

@media (prefers-reduced-motion: reduce) {
  .pulse {
    animation: none;
  }
}
```

## JavaScript Detection

### Check Preference

```javascript
// Check if user prefers reduced motion
const prefersReducedMotion = window.matchMedia(
  '(prefers-reduced-motion: reduce)'
).matches;

// Use in animation logic
function animate(element) {
  if (prefersReducedMotion) {
    // Instant or no animation
    element.style.opacity = 1;
  } else {
    // Full animation
    element.animate([
      { opacity: 0, transform: 'translateY(20px)' },
      { opacity: 1, transform: 'translateY(0)' }
    ], {
      duration: 300,
      easing: 'ease-out'
    });
  }
}
```

### Listen for Changes

```javascript
const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');

function handleMotionPreference(event) {
  if (event.matches) {
    // User prefers reduced motion
    disableAnimations();
  } else {
    // User allows motion
    enableAnimations();
  }
}

// Initial check
handleMotionPreference(mediaQuery);

// Listen for changes
mediaQuery.addEventListener('change', handleMotionPreference);
```

### Animation Library Integration

```javascript
// GSAP
gsap.defaults({
  duration: prefersReducedMotion ? 0 : 0.5
});

// Framer Motion (React)
const variants = {
  hidden: { opacity: 0 },
  visible: { 
    opacity: 1,
    transition: {
      duration: prefersReducedMotion ? 0 : 0.3
    }
  }
};

// CSS-in-JS
const animation = prefersReducedMotion
  ? {}
  : { transition: 'transform 0.3s ease' };
```

## Auto-Playing Content

### Video

```html
<!-- Avoid autoplay, or provide controls -->
<video autoplay muted loop playsinline>
  <source src="background.mp4" type="video/mp4">
</video>

<script>
const video = document.querySelector('video');

// Respect motion preference
if (prefersReducedMotion) {
  video.pause();
  video.currentTime = 0;
}

// Provide pause control
const pauseButton = document.querySelector('.pause-btn');
pauseButton.addEventListener('click', () => {
  if (video.paused) {
    video.play();
    pauseButton.textContent = 'Pause';
  } else {
    video.pause();
    pauseButton.textContent = 'Play';
  }
});
</script>
```

### Carousel

```html
<div class="carousel" role="region" aria-roledescription="carousel" aria-label="Featured content">
  <div class="carousel-controls">
    <button aria-label="Previous slide">←</button>
    <button aria-label="Pause auto-advance" id="pause-btn">⏸</button>
    <button aria-label="Next slide">→</button>
  </div>
  
  <div class="carousel-slides">
    <!-- slides -->
  </div>
</div>

<script>
class Carousel {
  constructor(element) {
    this.autoAdvance = !prefersReducedMotion;
    this.interval = null;
    
    if (this.autoAdvance) {
      this.startAutoAdvance();
    }
    
    // Pause on focus
    element.addEventListener('focusin', () => this.pause());
    element.addEventListener('focusout', () => {
      if (this.autoAdvance) this.startAutoAdvance();
    });
  }
  
  startAutoAdvance() {
    this.interval = setInterval(() => this.next(), 5000);
  }
  
  pause() {
    clearInterval(this.interval);
  }
}
</script>
```

### Loading Spinners

```css
/* Spinner that respects motion preference */
.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #0066cc;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@media (prefers-reduced-motion: reduce) {
  .spinner {
    /* Replace with pulsing opacity */
    animation: pulse 1s ease-in-out infinite;
  }
  
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
  }
}
```

## Framework Examples

### React

```jsx
import { useReducedMotion } from 'framer-motion';

function AnimatedComponent() {
  const shouldReduceMotion = useReducedMotion();
  
  const variants = {
    hidden: { opacity: 0, y: shouldReduceMotion ? 0 : 20 },
    visible: { 
      opacity: 1, 
      y: 0,
      transition: {
        duration: shouldReduceMotion ? 0 : 0.3
      }
    }
  };
  
  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={variants}
    >
      Content
    </motion.div>
  );
}
```

### Vue

```vue
<template>
  <transition :name="transitionName">
    <div v-if="show">Content</div>
  </transition>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';

const prefersReducedMotion = ref(false);

onMounted(() => {
  const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
  prefersReducedMotion.value = mediaQuery.matches;
  
  mediaQuery.addEventListener('change', (e) => {
    prefersReducedMotion.value = e.matches;
  });
});

const transitionName = computed(() => 
  prefersReducedMotion.value ? 'fade-instant' : 'fade-slide'
);
</script>

<style>
.fade-slide-enter-active {
  transition: all 0.3s ease;
}
.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.fade-instant-enter-active {
  transition: opacity 0.1s;
}
.fade-instant-enter-from {
  opacity: 0;
}
</style>
```

## Testing

### Manual Testing

```markdown
1. macOS: System Preferences → Accessibility → Display → Reduce motion
2. Windows: Settings → Ease of Access → Display → Show animations
3. iOS: Settings → Accessibility → Motion → Reduce Motion
4. Android: Settings → Accessibility → Remove animations
```

### DevTools Emulation

```markdown
Chrome DevTools:
1. Open DevTools (F12)
2. Open Command Menu (Ctrl+Shift+P)
3. Type "Reduce motion"
4. Select "Emulate CSS prefers-reduced-motion"
```

## Summary

| Animation Type | Default | Reduced Motion |
|----------------|---------|----------------|
| Page transitions | Slide/transform | Fade or instant |
| Hover effects | Scale/move | Color change only |
| Loading indicators | Spin | Pulse opacity |
| Carousels | Auto-advance | Manual only |
| Parallax | Enabled | Disabled |
| Background video | Autoplay | Paused |
