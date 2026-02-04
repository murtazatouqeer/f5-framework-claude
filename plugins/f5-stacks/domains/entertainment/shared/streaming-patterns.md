# Streaming Patterns

## Overview
Design patterns cho video/audio streaming systems.

## Key Patterns

### Pattern 1: Adaptive Bitrate Selection
```typescript
class ABRController {
  private bandwidthEstimate: number = 0;
  private bufferLevel: number = 0;

  selectQuality(variants: StreamVariant[]): StreamVariant {
    const sorted = variants.sort((a, b) => b.bitrate - a.bitrate);

    for (const variant of sorted) {
      if (variant.bitrate <= this.bandwidthEstimate * 0.8) {
        return variant;
      }
    }

    return sorted[sorted.length - 1]; // Lowest quality fallback
  }

  updateBandwidth(downloadTime: number, bytes: number) {
    const measured = (bytes * 8) / downloadTime;
    this.bandwidthEstimate = this.bandwidthEstimate * 0.7 + measured * 0.3;
  }
}
```

### Pattern 2: Token-Based CDN Authentication
```typescript
const generatePlaybackToken = (contentId: string, userId: string): string => {
  const payload = {
    contentId,
    userId,
    exp: Math.floor(Date.now() / 1000) + 3600,
    ip: getClientIP()
  };
  return jwt.sign(payload, CDN_SECRET);
};

const validateCDNRequest = (token: string, request: Request): boolean => {
  const decoded = jwt.verify(token, CDN_SECRET);
  return decoded.ip === request.ip && decoded.exp > Date.now() / 1000;
};
```

### Pattern 3: Live Streaming with DVR
```typescript
interface LiveStreamConfig {
  streamKey: string;
  dvrWindow: number; // seconds
  lowLatency: boolean;
  transcodeProfiles: string[];
}

class LiveStreamManager {
  async startStream(config: LiveStreamConfig): Promise<LiveStream> {
    const stream = await this.createStream(config);
    await this.provisionEncoder(stream);
    return stream;
  }

  async getDVRWindow(streamId: string, start: number, end: number) {
    return this.segmentStore.getSegments(streamId, start, end);
  }
}
```

## Best Practices
- Use chunked transfer for large segments
- Implement bandwidth estimation smoothing
- Cache manifests at edge
- Monitor Quality of Experience (QoE) metrics
