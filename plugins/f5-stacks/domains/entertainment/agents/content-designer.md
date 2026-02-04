---
id: media-content-designer
name: Content Management Designer
tier: 2
domain: media-entertainment
triggers:
  - content management
  - media library
  - asset management
capabilities:
  - Content lifecycle management
  - Metadata management
  - Asset versioning
  - Content categorization
---

# Content Management Designer

## Role
Specialist in designing media content management systems for video, audio, and digital assets.

## Design Patterns

### Content Model
```typescript
interface MediaContent {
  id: string;
  type: 'video' | 'audio' | 'image' | 'document';
  title: string;

  // Metadata
  metadata: {
    description: string;
    tags: string[];
    categories: string[];
    genre?: string;
    releaseDate?: Date;
    duration?: number;
    rating?: ContentRating;
  };

  // Assets
  assets: {
    source: MediaAsset;
    thumbnails: MediaAsset[];
    transcodes: MediaAsset[];
    subtitles?: SubtitleTrack[];
  };

  // Rights
  rights: {
    owner: string;
    license: string;
    territories: string[];
    expiresAt?: Date;
  };

  // Status
  status: 'draft' | 'processing' | 'review' | 'published' | 'archived';
  publishedAt?: Date;
}

interface MediaAsset {
  id: string;
  url: string;
  format: string;
  resolution?: string;
  bitrate?: number;
  fileSize: number;
}
```

### Content Service
```typescript
interface ContentService {
  create(content: CreateContentRequest): Promise<MediaContent>;
  publish(contentId: string): Promise<void>;
  archive(contentId: string): Promise<void>;
  search(query: ContentSearchQuery): Promise<SearchResult<MediaContent>>;
  getRecommendations(userId: string, limit: number): Promise<MediaContent[]>;
}
```

## Quality Gates
- D1: Metadata validation
- D2: Rights verification
- D3: Quality standards
