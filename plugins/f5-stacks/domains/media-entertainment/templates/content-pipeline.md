# Content Pipeline Template

## Content Ingestion Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Upload    │────▶│  Transcode  │────▶│   Review    │────▶│   Publish   │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
      │                   │                   │                   │
      ▼                   ▼                   ▼                   ▼
  Validate file      Multi-bitrate       QC check            CDN deploy
  Extract meta       Thumbnails          Rights verify       Index search
  Store source       DRM packaging       Metadata            Notify users
```

## Content States

```typescript
type ContentStatus =
  | 'uploading'
  | 'uploaded'
  | 'processing'
  | 'transcoding'
  | 'review'
  | 'approved'
  | 'published'
  | 'scheduled'
  | 'archived'
  | 'deleted';
```

## Transcoding Pipeline

```typescript
interface TranscodingJob {
  id: string;
  contentId: string;
  sourceAsset: string;

  // Outputs
  outputs: TranscodeOutput[];

  // Progress
  status: 'queued' | 'processing' | 'completed' | 'failed';
  progress: number;
  startedAt?: Date;
  completedAt?: Date;
  error?: string;
}

interface TranscodeOutput {
  profile: string;
  resolution: string;
  bitrate: number;
  codec: string;
  container: string;
  url?: string;
}

const transcodeProfiles = {
  '4k': { resolution: '3840x2160', bitrate: 15000, codec: 'h264' },
  '1080p': { resolution: '1920x1080', bitrate: 8000, codec: 'h264' },
  '720p': { resolution: '1280x720', bitrate: 5000, codec: 'h264' },
  '480p': { resolution: '854x480', bitrate: 2500, codec: 'h264' },
  '360p': { resolution: '640x360', bitrate: 1000, codec: 'h264' }
};
```

## Metadata Schema

```typescript
interface ContentMetadata {
  // Basic
  title: string;
  description: string;
  shortDescription?: string;

  // Classification
  genre: string[];
  categories: string[];
  tags: string[];
  keywords: string[];

  // Ratings
  contentRating: ContentRating;
  advisories: string[];

  // Credits
  credits: {
    role: string;
    name: string;
    character?: string;
  }[];

  // Technical
  duration: number;
  releaseYear: number;
  language: string;
  subtitleLanguages: string[];
  audioTracks: string[];
}
```
