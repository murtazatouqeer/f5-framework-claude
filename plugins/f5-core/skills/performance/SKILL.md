---
name: performance
description: Performance optimization strategies and techniques
category: skill
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: true
context: inject
version: 1.0.0
---

# Performance Skills

## Overview

Performance optimization knowledge for building fast, scalable applications
that provide excellent user experience.

## Key Metrics

| Metric | Target | Description |
|--------|--------|-------------|
| **TTFB** | < 200ms | Time to First Byte |
| **FCP** | < 1.8s | First Contentful Paint |
| **LCP** | < 2.5s | Largest Contentful Paint |
| **FID** | < 100ms | First Input Delay |
| **CLS** | < 0.1 | Cumulative Layout Shift |
| **API Response** | < 200ms | P95 response time |
| **Database Query** | < 50ms | P95 query time |
| **Memory Usage** | < 80% | Application memory threshold |

## Categories

### Fundamentals
- Performance metrics and measurement
- Bottleneck analysis techniques
- Benchmarking methodologies

### Caching
- Application caching strategies
- Redis/Memcached implementation
- HTTP caching headers
- CDN configuration
- Cache invalidation patterns

### Database Performance
- Query optimization
- Indexing strategies
- Connection pooling
- N+1 query prevention
- Read replicas

### API Performance
- Pagination strategies
- Response compression
- Batch operations
- Async processing
- Rate limiting

### Frontend Performance
- Bundle optimization
- Code splitting
- Lazy loading
- Image optimization
- Core Web Vitals

### Profiling & Monitoring
- CPU profiling
- Memory analysis
- APM tools
- Performance testing

### Scaling
- Horizontal vs vertical
- Load balancing
- Auto-scaling
- Caching layers

## Performance Pyramid

```
         ╱╲
        ╱  ╲         CDN / Edge
       ╱────╲
      ╱      ╲       Application Cache
     ╱────────╲
    ╱          ╲     Database Optimization
   ╱────────────╲
  ╱              ╲   Code Optimization
 ╱________________╲  Infrastructure
```

## Quick Reference

### Response Time Targets

| Operation Type | Target | Maximum |
|---------------|--------|---------|
| Static assets | < 50ms | 100ms |
| API read | < 100ms | 200ms |
| API write | < 200ms | 500ms |
| Search | < 200ms | 500ms |
| Report generation | < 2s | 5s |
| File upload | < 5s | 30s |

### Caching Strategy by Data Type

| Data Type | Cache Location | TTL |
|-----------|---------------|-----|
| Static assets | CDN | 1 year |
| User session | Redis | 30 min |
| User profile | Redis | 1 hour |
| Product catalog | Redis + CDN | 6 hours |
| Search results | Redis | 5 min |
| Config | Memory | 24 hours |

## Skill Files

### Fundamentals
- [Performance Metrics](fundamentals/performance-metrics.md)
- [Bottleneck Analysis](fundamentals/bottleneck-analysis.md)
- [Benchmarking](fundamentals/benchmarking.md)

### Caching
- [Caching Strategies](caching/caching-strategies.md)
- [Redis Caching](caching/redis-caching.md)
- [HTTP Caching](caching/http-caching.md)
- [CDN Caching](caching/cdn-caching.md)
- [Cache Invalidation](caching/cache-invalidation.md)

### Database
- [Query Optimization](database/query-optimization.md)
- [Indexing Strategies](database/indexing-strategies.md)
- [Connection Pooling](database/connection-pooling.md)
- [N+1 Problem](database/n-plus-one.md)

### API
- [Pagination](api/pagination.md)
- [Response Compression](api/response-compression.md)
- [Batch Operations](api/batch-operations.md)
- [Async Processing](api/async-processing.md)

### Frontend
- [Bundle Optimization](frontend/bundle-optimization.md)
- [Lazy Loading](frontend/lazy-loading.md)
- [Image Optimization](frontend/image-optimization.md)
- [Core Web Vitals](frontend/core-web-vitals.md)

### Profiling
- [CPU Profiling](profiling/cpu-profiling.md)
- [Memory Profiling](profiling/memory-profiling.md)
- [APM Tools](profiling/apm-tools.md)

### Scaling
- [Horizontal Scaling](scaling/horizontal-scaling.md)
- [Vertical Scaling](scaling/vertical-scaling.md)
- [Load Balancing](scaling/load-balancing.md)
- [Auto Scaling](scaling/auto-scaling.md)

## Integration with F5 Framework

### Quality Gate Integration

Performance requirements should be defined in quality gates:

```yaml
# .f5/quality/gates-status.yaml
gates:
  G2:
    performance:
      api_p95_response: "< 200ms"
      database_p95_query: "< 50ms"
      memory_usage: "< 80%"
```

### Traceability

Performance requirements should be traceable:

```typescript
// NFR-PERF-001: API response time must be under 200ms at P95
export async function getUser(id: string): Promise<User> {
  // implementation
}
```
