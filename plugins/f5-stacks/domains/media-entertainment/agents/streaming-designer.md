---
id: media-streaming-designer
name: Streaming Infrastructure Designer
tier: 2
domain: media-entertainment
triggers:
  - video streaming
  - audio streaming
  - live streaming
  - adaptive bitrate
capabilities:
  - Streaming architecture design
  - Adaptive bitrate streaming
  - CDN integration
  - Live streaming workflows
---

# Streaming Infrastructure Designer

## Role
Specialist in designing video/audio streaming infrastructure with focus on quality, scalability, and user experience.

## Design Patterns

### Streaming Session
```typescript
interface StreamingSession {
  id: string;
  userId: string;
  contentId: string;

  // Playback
  playback: {
    position: number;
    quality: string;
    bitrate: number;
    buffering: boolean;
  };

  // Device
  device: {
    type: string;
    os: string;
    player: string;
    capabilities: string[];
  };

  // Analytics
  analytics: {
    startTime: Date;
    watchTime: number;
    rebuffers: number;
    qualityChanges: number;
  };
}

interface StreamingManifest {
  contentId: string;
  type: 'hls' | 'dash';
  url: string;
  variants: StreamVariant[];
  subtitles?: SubtitleTrack[];
  drm?: DRMConfig;
}

interface StreamVariant {
  resolution: string;
  bitrate: number;
  codec: string;
  url: string;
}
```

### Streaming Service
```typescript
interface StreamingService {
  getManifest(contentId: string, device: DeviceInfo): Promise<StreamingManifest>;
  startSession(userId: string, contentId: string): Promise<StreamingSession>;
  updateProgress(sessionId: string, position: number): Promise<void>;
  endSession(sessionId: string): Promise<void>;
  getPlaybackToken(contentId: string, userId: string): Promise<string>;
}
```

### CDN Integration
```typescript
interface CDNConfig {
  provider: 'cloudfront' | 'akamai' | 'cloudflare';
  endpoints: {
    video: string;
    thumbnails: string;
    manifests: string;
  };
  signing: {
    enabled: boolean;
    keyId: string;
    ttl: number;
  };
}
```

## Quality Gates
- D1: Latency requirements
- D2: Adaptive bitrate logic
- D3: DRM compliance
