---
name: video-captions
description: Adding captions and subtitles to video content
category: accessibility/media
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# Video Captions

## Overview

Captions make video content accessible to deaf and hard-of-hearing users. They also benefit users in noisy environments, non-native speakers, and those who prefer reading.

## Types of Text Tracks

| Type | Purpose | Audience |
|------|---------|----------|
| Captions | Dialogue + sounds | Deaf/hard of hearing |
| Subtitles | Dialogue only | Foreign language speakers |
| Descriptions | Visual content narrated | Blind users |
| Chapters | Navigation points | All users |

## Basic Implementation

### HTML5 Video with Captions

```html
<video controls>
  <source src="video.mp4" type="video/mp4">
  <source src="video.webm" type="video/webm">
  
  <!-- Captions -->
  <track 
    kind="captions" 
    src="captions-en.vtt" 
    srclang="en" 
    label="English"
    default
  >
  
  <!-- Multiple languages -->
  <track 
    kind="captions" 
    src="captions-es.vtt" 
    srclang="es" 
    label="Español"
  >
  
  <!-- Subtitles (no sound descriptions) -->
  <track 
    kind="subtitles" 
    src="subtitles-fr.vtt" 
    srclang="fr" 
    label="Français"
  >
  
  <!-- Audio descriptions -->
  <track 
    kind="descriptions" 
    src="descriptions-en.vtt" 
    srclang="en" 
    label="Audio Descriptions"
  >
  
  <!-- Chapters for navigation -->
  <track 
    kind="chapters" 
    src="chapters.vtt" 
    srclang="en"
  >
  
  <!-- Fallback for no video support -->
  <p>Your browser doesn't support video. 
     <a href="video.mp4">Download video</a>
  </p>
</video>
```

## WebVTT Format

### Basic Caption File

```vtt
WEBVTT

00:00:00.000 --> 00:00:03.000
Welcome to our accessibility tutorial.

00:00:03.500 --> 00:00:07.000
Today we'll learn about creating
accessible web content.

00:00:08.000 --> 00:00:12.000
[upbeat music playing]

00:00:12.500 --> 00:00:16.000
Let's start with the basics
of semantic HTML.
```

### Styled Captions

```vtt
WEBVTT

STYLE
::cue {
  background-color: rgba(0, 0, 0, 0.8);
  color: white;
  font-family: sans-serif;
}

::cue(.speaker1) {
  color: #ff9;
}

::cue(.speaker2) {
  color: #9ff;
}

00:00:00.000 --> 00:00:03.000
<c.speaker1>Hi, I'm Sarah from the design team.</c>

00:00:03.500 --> 00:00:06.000
<c.speaker2>And I'm Mike from engineering.</c>
```

### Positioning

```vtt
WEBVTT

00:00:00.000 --> 00:00:03.000 line:0 position:50% align:center
[Title Card: Chapter 1]

00:00:03.500 --> 00:00:07.000 line:-3
Person on left of screen speaking.

00:00:08.000 --> 00:00:12.000 line:-3 position:80%
Person on right of screen speaking.
```

### Sound Descriptions

```vtt
WEBVTT

00:00:00.000 --> 00:00:02.000
[Door creaks open]

00:00:02.500 --> 00:00:05.000
[Footsteps approaching]

00:00:05.500 --> 00:00:08.000
JOHN: Hello? Is anyone here?

00:00:08.500 --> 00:00:10.000
[Thunder rumbles in distance]

00:00:10.500 --> 00:00:14.000
[Dramatic music intensifies]
```

## Caption Guidelines

### What to Include

```vtt
WEBVTT

-- Dialogue with speaker identification --
00:00:00.000 --> 00:00:03.000
SARAH: Welcome to the meeting.

00:00:03.500 --> 00:00:06.000
MIKE: Thanks for having me.

-- Sound effects that matter to plot --
00:00:07.000 --> 00:00:08.500
[phone rings]

00:00:09.000 --> 00:00:11.000
SARAH: Excuse me, I need to take this.

-- Music descriptions --
00:00:15.000 --> 00:00:18.000
[soft piano music playing]

-- Emotional tone when not obvious --
00:00:20.000 --> 00:00:23.000
MIKE: [sarcastically] Oh, that's just great.

-- Off-screen dialogue --
00:00:25.000 --> 00:00:28.000
VOICE (off-screen): Can someone help me?
```

### Best Practices

```vtt
WEBVTT

-- Keep lines short (32-42 characters max) --
00:00:00.000 --> 00:00:03.000
This is a good length
for a caption line.

-- 1-3 seconds per caption --
00:00:04.000 --> 00:00:07.000
Captions should stay on screen
long enough to read.

-- Don't spoil with captions --
00:00:10.000 --> 00:00:12.000
[dramatic sound]

-- Not: [gunshot] if person is about to be shot --

-- Verbatim vs. edited --
-- Verbatim for accuracy, light editing for readability --
00:00:15.000 --> 00:00:18.000
So, um, what I wanted to say is...

-- Can become --
00:00:15.000 --> 00:00:18.000
What I wanted to say is...
```

## Audio Descriptions

### Description Track

```vtt
WEBVTT

00:00:00.000 --> 00:00:05.000
A woman in a red dress walks through a crowded marketplace.

00:00:08.000 --> 00:00:12.000
She stops at a fruit stand and picks up an apple.

00:00:15.000 --> 00:00:18.000
The vendor, an elderly man with a white beard, smiles.
```

### Extended Audio Descriptions

```html
<!-- For complex visual content that needs more time -->
<video controls>
  <source src="video-extended.mp4" type="video/mp4">
  <!-- Video has pauses for extended descriptions -->
  <track 
    kind="descriptions" 
    src="extended-descriptions.vtt" 
    srclang="en" 
    label="Extended Audio Descriptions"
  >
</video>
```

## JavaScript Caption Control

### Custom Caption Toggle

```html
<video id="myVideo" controls>
  <source src="video.mp4" type="video/mp4">
  <track kind="captions" src="captions.vtt" srclang="en" label="English">
</video>
<button id="ccToggle">Toggle Captions</button>

<script>
const video = document.getElementById('myVideo');
const toggle = document.getElementById('ccToggle');

// Get text track
const track = video.textTracks[0];
track.mode = 'hidden'; // Start hidden

toggle.addEventListener('click', () => {
  if (track.mode === 'showing') {
    track.mode = 'hidden';
    toggle.textContent = 'Show Captions';
    toggle.setAttribute('aria-pressed', 'false');
  } else {
    track.mode = 'showing';
    toggle.textContent = 'Hide Captions';
    toggle.setAttribute('aria-pressed', 'true');
  }
});
</script>
```

### Caption Styling

```css
/* Style the video captions */
video::cue {
  background-color: rgba(0, 0, 0, 0.8);
  color: white;
  font-size: 1.2em;
  font-family: Arial, sans-serif;
}

/* Different speakers */
video::cue(.speaker-a) {
  color: #ffff00;
}

video::cue(.speaker-b) {
  color: #00ffff;
}

/* Sound descriptions */
video::cue(.sound) {
  color: #aaaaaa;
  font-style: italic;
}
```

### Reading Cues in JavaScript

```javascript
const video = document.getElementById('myVideo');
const track = video.textTracks[0];

// Listen for cue changes
track.addEventListener('cuechange', () => {
  const activeCues = track.activeCues;
  if (activeCues.length > 0) {
    console.log('Current caption:', activeCues[0].text);
  }
});

// Access all cues
track.addEventListener('load', () => {
  for (let i = 0; i < track.cues.length; i++) {
    console.log(track.cues[i].text);
  }
});
```

## Third-Party Players

### YouTube

```html
<!-- YouTube with captions enabled -->
<iframe 
  width="560" 
  height="315" 
  src="https://www.youtube.com/embed/VIDEO_ID?cc_load_policy=1"
  title="Video title for accessibility"
  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
  allowfullscreen
></iframe>
```

### Vimeo

```html
<iframe 
  src="https://player.vimeo.com/video/VIDEO_ID?texttrack=en"
  width="640" 
  height="360" 
  title="Video title for accessibility"
  allow="autoplay; fullscreen; picture-in-picture"
  allowfullscreen
></iframe>
```

## Automated Captioning

### Process

```markdown
1. Generate automatic captions (YouTube, Rev, Otter.ai)
2. Download/export caption file
3. Review and edit for accuracy
4. Fix speaker identification
5. Add sound descriptions
6. Format timing and line breaks
7. Upload corrected captions
```

### Common Errors to Fix

```vtt
WEBVTT

-- Auto-generated (errors) --
00:00:00.000 --> 00:00:03.000
lets look at the sequel statement

-- Corrected --
00:00:00.000 --> 00:00:03.000
Let's look at the SQL statement.

-- Auto-generated (errors) --
00:00:05.000 --> 00:00:08.000
the aria label attribute

-- Corrected --
00:00:05.000 --> 00:00:08.000
the ARIA-label attribute
```

## Testing Captions

### Manual Testing

```markdown
1. Play video with captions on
2. Verify dialogue accuracy
3. Check sound descriptions are present
4. Confirm speaker identification
5. Test timing synchronization
6. Verify readability (line length, duration)
7. Test with screen reader
```

### Automated Validation

```javascript
// Validate VTT file structure
function validateVTT(content) {
  const lines = content.split('\n');
  const issues = [];
  
  // Check header
  if (!lines[0].startsWith('WEBVTT')) {
    issues.push('Missing WEBVTT header');
  }
  
  // Check timestamp format
  const timestampRegex = /^\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}/;
  let inCue = false;
  
  lines.forEach((line, i) => {
    if (timestampRegex.test(line)) {
      inCue = true;
    } else if (inCue && line.trim() === '') {
      inCue = false;
    }
  });
  
  return issues;
}
```

## Summary

| Requirement | Implementation |
|-------------|----------------|
| Captions | `<track kind="captions">` |
| Multiple languages | Multiple track elements |
| Sound descriptions | [brackets] in captions |
| Audio descriptions | `<track kind="descriptions">` |
| Styling | CSS ::cue pseudo-element |
| Fallback | Transcript link |
