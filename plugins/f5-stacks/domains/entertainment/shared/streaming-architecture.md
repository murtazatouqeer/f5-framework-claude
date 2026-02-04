# Streaming Architecture Template

## Adaptive Bitrate Streaming

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Origin    │────▶│     CDN     │────▶│   Player    │
└─────────────┘     └─────────────┘     └─────────────┘
      │                   │                   │
      ▼                   ▼                   ▼
  HLS/DASH           Edge caching       ABR logic
  Manifests          Token auth         Quality switch
  DRM keys           Geo routing        Analytics
```

## HLS Manifest Structure

```
#EXTM3U
#EXT-X-VERSION:4
#EXT-X-STREAM-INF:BANDWIDTH=800000,RESOLUTION=640x360
360p/playlist.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=1400000,RESOLUTION=842x480
480p/playlist.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=2800000,RESOLUTION=1280x720
720p/playlist.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=5000000,RESOLUTION=1920x1080
1080p/playlist.m3u8
```

## Streaming Service Architecture

```typescript
interface StreamingConfig {
  // Protocols
  protocols: ('hls' | 'dash')[];
  segmentDuration: number;

  // CDN
  cdn: {
    provider: string;
    origins: string[];
    cacheRules: CacheRule[];
  };

  // Security
  security: {
    tokenAuth: boolean;
    tokenTTL: number;
    drm: DRMConfig[];
    geoRestrictions: GeoRule[];
  };

  // Quality
  quality: {
    maxBitrate: number;
    minBitrate: number;
    startQuality: string;
  };
}

interface DRMConfig {
  system: 'widevine' | 'fairplay' | 'playready';
  licenseUrl: string;
  certificateUrl?: string;
}
```

## Playback Analytics

```typescript
interface PlaybackEvent {
  sessionId: string;
  eventType: PlaybackEventType;
  timestamp: Date;
  data: Record<string, any>;
}

type PlaybackEventType =
  | 'play_start'
  | 'play_pause'
  | 'play_resume'
  | 'play_seek'
  | 'play_complete'
  | 'quality_change'
  | 'buffer_start'
  | 'buffer_end'
  | 'error';
```
