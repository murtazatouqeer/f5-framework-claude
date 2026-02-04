---
name: audio-transcripts
description: Creating accessible transcripts for audio content
category: accessibility/media
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# Audio Transcripts

## Overview

Transcripts provide a text alternative to audio content, making it accessible to deaf and hard-of-hearing users, and beneficial for all users who prefer reading or need to search content.

## When Transcripts Are Required

| Content Type | WCAG Requirement |
|--------------|------------------|
| Audio-only (podcasts) | Level A: Transcript required |
| Video with audio | Level A: Captions OR transcript |
| Live audio | Level AA: Real-time captions |
| Prerecorded multimedia | Level AA: Captions required |

## Basic Implementation

### Simple Transcript

```html
<figure>
  <audio controls>
    <source src="podcast.mp3" type="audio/mpeg">
    <source src="podcast.ogg" type="audio/ogg">
    Your browser doesn't support audio.
    <a href="podcast.mp3">Download podcast</a>
  </audio>
  <figcaption>Episode 10: Accessibility Best Practices</figcaption>
</figure>

<details>
  <summary>View Transcript</summary>
  <div class="transcript">
    <p><strong>Host:</strong> Welcome to episode 10 of our podcast. 
       Today we're discussing accessibility best practices.</p>
    <p><strong>Guest:</strong> Thanks for having me. I'm excited 
       to share some practical tips.</p>
    <!-- ... rest of transcript -->
  </div>
</details>
```

### Linked Transcript

```html
<div class="audio-player">
  <audio controls aria-describedby="audio-info">
    <source src="interview.mp3" type="audio/mpeg">
  </audio>
  <p id="audio-info">
    Interview with Jane Smith, CEO (45 minutes)
  </p>
  <a href="transcript-interview.html">Read full transcript</a>
  <a href="transcript-interview.txt" download>Download transcript (TXT)</a>
</div>
```

### Synchronized Transcript

```html
<div class="media-container">
  <audio id="podcast" controls>
    <source src="podcast.mp3" type="audio/mpeg">
  </audio>
  
  <div id="transcript" class="transcript">
    <p data-start="0" data-end="5">
      Welcome to the show.
    </p>
    <p data-start="5.5" data-end="12">
      Today we're talking about web accessibility.
    </p>
    <p data-start="12.5" data-end="20">
      Let's start with the basics.
    </p>
  </div>
</div>

<script>
const audio = document.getElementById('podcast');
const transcript = document.getElementById('transcript');
const paragraphs = transcript.querySelectorAll('p[data-start]');

audio.addEventListener('timeupdate', () => {
  const currentTime = audio.currentTime;
  
  paragraphs.forEach(p => {
    const start = parseFloat(p.dataset.start);
    const end = parseFloat(p.dataset.end);
    
    if (currentTime >= start && currentTime < end) {
      p.classList.add('active');
    } else {
      p.classList.remove('active');
    }
  });
});

// Click to jump to position
paragraphs.forEach(p => {
  p.addEventListener('click', () => {
    audio.currentTime = parseFloat(p.dataset.start);
    audio.play();
  });
});
</script>

<style>
.transcript p {
  padding: 0.5em;
  cursor: pointer;
  border-left: 3px solid transparent;
}

.transcript p:hover {
  background: #f5f5f5;
}

.transcript p.active {
  background: #e3f2fd;
  border-left-color: #1976d2;
}
</style>
```

## Transcript Content

### What to Include

```html
<div class="transcript">
  <!-- Speaker identification -->
  <p><strong>Host (Sarah):</strong> Welcome to the show.</p>
  
  <!-- Sound descriptions when relevant -->
  <p><em>[Intro music plays]</em></p>
  
  <!-- Timestamps for navigation -->
  <p><span class="timestamp">[00:01:30]</span> 
     <strong>Guest (Mike):</strong> Thanks for having me.</p>
  
  <!-- Non-verbal sounds that convey meaning -->
  <p><strong>Sarah:</strong> Did you enjoy your trip? 
     <em>[laughs]</em></p>
  
  <!-- Significant pauses -->
  <p><strong>Mike:</strong> Well... <em>[long pause]</em> 
     ...it's complicated.</p>
  
  <!-- Unclear audio -->
  <p><strong>Sarah:</strong> I heard you went to 
     <em>[inaudible, 00:05:23]</em>.</p>
</div>
```

### Formatting Best Practices

```html
<div class="transcript">
  <h2>Transcript: Accessibility in 2024</h2>
  
  <dl class="transcript-meta">
    <dt>Duration:</dt>
    <dd>45 minutes</dd>
    <dt>Speakers:</dt>
    <dd>Sarah Chen (Host), Mike Johnson (Guest)</dd>
    <dt>Recorded:</dt>
    <dd>January 15, 2024</dd>
  </dl>
  
  <section>
    <h3>Introduction <span class="timestamp">[00:00:00]</span></h3>
    
    <p><strong>Sarah:</strong> Hello and welcome to Tech Talk. 
       I'm your host, Sarah Chen.</p>
    
    <p><strong>Sarah:</strong> Today, I'm joined by Mike Johnson, 
       a web accessibility expert with over 15 years of experience.</p>
  </section>
  
  <section>
    <h3>Main Discussion <span class="timestamp">[00:02:30]</span></h3>
    
    <p><strong>Sarah:</strong> Let's dive into the topic. 
       What are the biggest accessibility challenges in 2024?</p>
    
    <p><strong>Mike:</strong> Great question. I'd say the top three are:
       <br>First, complex single-page applications.
       <br>Second, mobile accessibility.
       <br>Third, cognitive accessibility considerations.</p>
  </section>
</div>
```

### Searchable Transcript

```html
<div class="transcript-container">
  <input 
    type="search" 
    id="transcript-search"
    aria-label="Search transcript"
    placeholder="Search transcript..."
  >
  
  <div id="search-results" aria-live="polite"></div>
  
  <div id="transcript" class="transcript">
    <!-- Transcript content -->
  </div>
</div>

<script>
const search = document.getElementById('transcript-search');
const results = document.getElementById('search-results');
const transcript = document.getElementById('transcript');

search.addEventListener('input', (e) => {
  const query = e.target.value.toLowerCase();
  
  if (query.length < 3) {
    results.textContent = '';
    return;
  }
  
  const paragraphs = transcript.querySelectorAll('p');
  const matches = [];
  
  paragraphs.forEach(p => {
    if (p.textContent.toLowerCase().includes(query)) {
      matches.push(p);
    }
  });
  
  results.textContent = `Found ${matches.length} matches`;
  
  // Highlight matches
  paragraphs.forEach(p => p.classList.remove('highlight'));
  matches.forEach(p => p.classList.add('highlight'));
});
</script>
```

## Multiple Formats

### Offering Download Options

```html
<div class="transcript-options">
  <h3>Transcript</h3>
  
  <p>Choose your preferred format:</p>
  
  <ul>
    <li>
      <a href="transcript.html">
        View online transcript
      </a>
    </li>
    <li>
      <a href="transcript.txt" download>
        Download as plain text (.txt)
      </a>
    </li>
    <li>
      <a href="transcript.pdf" download>
        Download as PDF
      </a>
    </li>
    <li>
      <a href="transcript.docx" download>
        Download as Word document (.docx)
      </a>
    </li>
    <li>
      <a href="transcript.vtt" download>
        Download timed captions (.vtt)
      </a>
    </li>
  </ul>
</div>
```

### Machine-Readable Format

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "PodcastEpisode",
  "name": "Accessibility Best Practices",
  "datePublished": "2024-01-15",
  "duration": "PT45M",
  "transcript": {
    "@type": "CreativeWork",
    "text": "Full transcript text...",
    "url": "https://example.com/transcript.html"
  },
  "audio": {
    "@type": "AudioObject",
    "contentUrl": "https://example.com/podcast.mp3"
  }
}
</script>
```

## Creating Transcripts

### Manual Transcription

```markdown
## Tips for Manual Transcription

1. **Listen in short segments** (15-30 seconds)
2. **Type what you hear** - don't paraphrase
3. **Include speaker names** at each change
4. **Note significant sounds** [laughter], [applause]
5. **Mark unclear sections** [inaudible]
6. **Add timestamps** at regular intervals or topic changes
7. **Proofread** by listening again while reading
```

### Automated Transcription

```markdown
## Using Automated Services

Popular services:
- Otter.ai
- Rev.com
- Descript
- YouTube auto-captions
- Amazon Transcribe
- Google Cloud Speech-to-Text

## Workflow:
1. Upload audio to service
2. Download auto-generated transcript
3. Review and correct errors
4. Add speaker identification
5. Insert sound descriptions
6. Format for readability
7. Add timestamps
```

### Correction Checklist

```markdown
## Transcript Review Checklist

- [ ] All speakers identified correctly
- [ ] Technical terms spelled correctly
- [ ] Proper nouns capitalized
- [ ] Acronyms expanded on first use
- [ ] Sound descriptions added
- [ ] Unclear sections marked [inaudible]
- [ ] Timestamps accurate
- [ ] Formatting consistent
- [ ] Paragraph breaks at topic changes
- [ ] Links/references included
```

## Styling Transcripts

```css
.transcript {
  max-width: 65ch;
  line-height: 1.6;
  font-size: 1rem;
}

.transcript p {
  margin-bottom: 1em;
}

.transcript strong {
  color: #1976d2;
}

.transcript em {
  color: #666;
  font-style: italic;
}

.timestamp {
  font-family: monospace;
  font-size: 0.85em;
  color: #888;
  background: #f5f5f5;
  padding: 0.1em 0.3em;
  border-radius: 3px;
}

.transcript .highlight {
  background-color: #fff59d;
}

/* Print styles */
@media print {
  .transcript {
    max-width: 100%;
  }
  
  .timestamp {
    color: #000;
    background: none;
  }
}
```

## Testing

### Accessibility Testing

```markdown
1. **Screen reader test**: 
   - Navigate transcript with NVDA/VoiceOver
   - Verify speakers are announced
   - Check timestamps are readable

2. **Keyboard test**:
   - Tab through interactive elements
   - Search functionality works
   - Links are accessible

3. **Content test**:
   - Compare transcript to audio
   - Verify completeness
   - Check accuracy
```

### Quality Checklist

```markdown
- [ ] Transcript matches audio content
- [ ] All speakers identifiable
- [ ] Sound descriptions present
- [ ] Searchable and navigable
- [ ] Multiple format options
- [ ] Properly linked from audio player
- [ ] Good contrast and readability
- [ ] Works with screen readers
```

## Summary

| Element | Implementation |
|---------|----------------|
| Basic transcript | `<details>` with transcript |
| Downloadable | Multiple format links |
| Synchronized | JavaScript time tracking |
| Searchable | Search input + highlighting |
| Structured | Headings, timestamps, speakers |
| Accessible | Semantic HTML, keyboard nav |
