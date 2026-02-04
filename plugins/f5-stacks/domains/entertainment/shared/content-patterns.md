# Content Management Patterns

## Overview
Design patterns cho media content management systems.

## Key Patterns

### Pattern 1: Content Versioning
```typescript
interface ContentVersion {
  id: string;
  contentId: string;
  version: number;
  changes: Change[];
  createdAt: Date;
  createdBy: string;
}

class ContentVersioning {
  async createVersion(contentId: string, changes: Change[]): Promise<ContentVersion> {
    const current = await this.getCurrentVersion(contentId);
    return this.versionRepository.create({
      contentId,
      version: current.version + 1,
      changes,
      createdAt: new Date()
    });
  }

  async rollback(contentId: string, targetVersion: number): Promise<void> {
    const versions = await this.getVersions(contentId, targetVersion);
    const reversedChanges = this.reverseChanges(versions);
    await this.applyChanges(contentId, reversedChanges);
  }
}
```

### Pattern 2: Content Scheduling
```typescript
interface ScheduledContent {
  contentId: string;
  publishAt: Date;
  unpublishAt?: Date;
  territories: string[];
  platforms: string[];
}

class ContentScheduler {
  async schedulePublish(schedule: ScheduledContent): Promise<void> {
    await this.scheduleRepository.create(schedule);
    await this.queue.schedule('publish', schedule.contentId, schedule.publishAt);
  }

  async processScheduled(): Promise<void> {
    const due = await this.scheduleRepository.findDue();
    for (const item of due) {
      await this.contentService.publish(item.contentId);
    }
  }
}
```

### Pattern 3: Recommendation Engine
```typescript
interface RecommendationService {
  getPersonalized(userId: string, limit: number): Promise<Content[]>;
  getSimilar(contentId: string, limit: number): Promise<Content[]>;
  getTrending(category?: string, limit?: number): Promise<Content[]>;
}

class CollaborativeFiltering {
  async getRecommendations(userId: string): Promise<Content[]> {
    const userHistory = await this.getWatchHistory(userId);
    const similarUsers = await this.findSimilarUsers(userHistory);
    const recommendations = await this.aggregateRecommendations(similarUsers);
    return this.filterWatched(recommendations, userHistory);
  }
}
```

## Best Practices
- Implement content versioning for audit
- Use event sourcing for content changes
- Cache recommendations with short TTL
- Index metadata for fast search
