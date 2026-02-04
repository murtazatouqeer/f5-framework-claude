# Property Search Patterns

## Overview
Search patterns and best practices for property listing search systems.

## Key Patterns

### Pattern 1: Geospatial Search
**When to use:** Location-based property discovery
**Description:** Search properties by location using various geographic criteria
**Example:**
```typescript
interface GeoSearchService {
  // Radius search
  searchByRadius(
    center: { lat: number; lng: number },
    radiusMiles: number,
    filters?: PropertyFilters
  ): Promise<PropertyListing[]>;

  // Polygon/boundary search
  searchByPolygon(
    points: { lat: number; lng: number }[],
    filters?: PropertyFilters
  ): Promise<PropertyListing[]>;

  // Neighborhood/area search
  searchByArea(
    areaType: 'neighborhood' | 'school_district' | 'zip' | 'city',
    areaId: string,
    filters?: PropertyFilters
  ): Promise<PropertyListing[]>;

  // Map viewport search
  searchByBounds(
    bounds: {
      north: number;
      south: number;
      east: number;
      west: number;
    },
    filters?: PropertyFilters
  ): Promise<PropertyListing[]>;
}

// PostGIS implementation
const searchByRadius = async (center, radius, filters) => {
  return db.query(`
    SELECT * FROM properties
    WHERE ST_DWithin(
      coordinates::geography,
      ST_MakePoint($1, $2)::geography,
      $3 * 1609.34  -- Convert miles to meters
    )
    AND status = 'active'
    ${buildFilterClause(filters)}
    ORDER BY ST_Distance(coordinates, ST_MakePoint($1, $2))
    LIMIT 100
  `, [center.lng, center.lat, radius]);
};
```

### Pattern 2: Faceted Search with Elasticsearch
**When to use:** Complex filtering with aggregations
**Description:** Multi-faceted property search with real-time counts
**Example:**
```typescript
interface FacetedSearchResult {
  properties: PropertyListing[];
  facets: {
    propertyTypes: { value: string; count: number }[];
    priceRanges: { min: number; max: number; count: number }[];
    bedrooms: { value: number; count: number }[];
    amenities: { value: string; count: number }[];
  };
  total: number;
}

const buildElasticsearchQuery = (search: PropertySearch) => ({
  query: {
    bool: {
      must: [
        search.query ? {
          multi_match: {
            query: search.query,
            fields: ['address^3', 'description', 'amenities']
          }
        } : { match_all: {} }
      ],
      filter: [
        search.priceRange && {
          range: {
            listPrice: {
              gte: search.priceRange.min,
              lte: search.priceRange.max
            }
          }
        },
        search.bedrooms && {
          range: { bedrooms: { gte: search.bedrooms.min } }
        },
        search.propertyTypes && {
          terms: { propertyType: search.propertyTypes }
        },
        search.location && {
          geo_distance: {
            distance: `${search.location.radius}mi`,
            coordinates: search.location.center
          }
        }
      ].filter(Boolean)
    }
  },
  aggs: {
    propertyTypes: { terms: { field: 'propertyType' } },
    priceRanges: {
      range: {
        field: 'listPrice',
        ranges: [
          { to: 200000 },
          { from: 200000, to: 400000 },
          { from: 400000, to: 600000 },
          { from: 600000 }
        ]
      }
    },
    bedrooms: { terms: { field: 'bedrooms' } },
    amenities: { terms: { field: 'amenities', size: 20 } }
  }
});
```

### Pattern 3: Saved Searches with Alerts
**When to use:** User engagement and lead generation
**Description:** Save search criteria and notify users of new matches
**Example:**
```typescript
interface SavedSearch {
  id: string;
  userId: string;
  name: string;
  criteria: PropertySearch;
  alertFrequency: 'instant' | 'daily' | 'weekly';
  alertChannels: ('email' | 'push' | 'sms')[];
  lastExecuted?: Date;
  matchCount: number;
  isActive: boolean;
  createdAt: Date;
}

class SavedSearchService {
  async saveSearch(userId: string, search: PropertySearch, options: SaveOptions): Promise<SavedSearch> {
    const savedSearch = await this.repository.create({
      userId,
      criteria: search,
      ...options
    });

    // Execute immediately to get initial count
    const results = await this.searchService.search(search);
    await this.repository.update(savedSearch.id, { matchCount: results.total });

    return savedSearch;
  }

  async executeAlerts(): Promise<void> {
    const searches = await this.repository.findDueForExecution();

    for (const search of searches) {
      const newListings = await this.findNewMatches(search);

      if (newListings.length > 0) {
        await this.sendAlerts(search, newListings);
      }

      await this.repository.update(search.id, { lastExecuted: new Date() });
    }
  }

  private async findNewMatches(search: SavedSearch): Promise<PropertyListing[]> {
    const criteria = {
      ...search.criteria,
      listedAfter: search.lastExecuted
    };
    const results = await this.searchService.search(criteria);
    return results.properties;
  }
}
```

### Pattern 4: Similar Property Recommendations
**When to use:** Property detail pages, user engagement
**Description:** Find similar properties based on multiple factors
**Example:**
```typescript
interface SimilarityFactors {
  location: number;      // Geographic proximity weight
  price: number;         // Price similarity weight
  specs: number;         // Beds/baths/sqft weight
  features: number;      // Amenities overlap weight
  propertyType: number;  // Same type bonus
}

class SimilarPropertyService {
  private readonly DEFAULT_WEIGHTS: SimilarityFactors = {
    location: 0.3,
    price: 0.25,
    specs: 0.25,
    features: 0.15,
    propertyType: 0.05
  };

  async findSimilar(
    listingId: string,
    limit: number = 10,
    weights?: Partial<SimilarityFactors>
  ): Promise<PropertyListing[]> {
    const listing = await this.repository.findById(listingId);
    const factors = { ...this.DEFAULT_WEIGHTS, ...weights };

    // Build similarity query
    const candidates = await this.getCandidates(listing);

    // Score and rank
    const scored = candidates.map(candidate => ({
      listing: candidate,
      score: this.calculateSimilarity(listing, candidate, factors)
    }));

    return scored
      .sort((a, b) => b.score - a.score)
      .slice(0, limit)
      .map(s => s.listing);
  }

  private calculateSimilarity(
    source: PropertyListing,
    target: PropertyListing,
    weights: SimilarityFactors
  ): number {
    let score = 0;

    // Location similarity (inverse of distance)
    const distance = this.calculateDistance(source.coordinates, target.coordinates);
    score += weights.location * Math.max(0, 1 - distance / 10); // 10 mile max

    // Price similarity
    const priceDiff = Math.abs(source.listPrice - target.listPrice) / source.listPrice;
    score += weights.price * Math.max(0, 1 - priceDiff);

    // Specs similarity
    const specScore = this.calculateSpecSimilarity(source, target);
    score += weights.specs * specScore;

    // Features overlap
    const featureScore = this.calculateFeatureOverlap(source.amenities, target.amenities);
    score += weights.features * featureScore;

    // Property type match
    if (source.propertyType === target.propertyType) {
      score += weights.propertyType;
    }

    return score;
  }
}
```

## Best Practices
- Index geospatial data with PostGIS or Elasticsearch
- Cache popular search results with short TTL
- Use pagination with cursor-based navigation
- Implement search analytics for optimization
- Pre-compute aggregations for common filters

## Anti-Patterns to Avoid
- Loading all properties into memory for filtering
- Using LIKE queries for full-text search
- Ignoring search performance monitoring
- Not normalizing address data
