# Property Listing Flow Template

## Listing Creation Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Draft     │────▶│   Review    │────▶│   Active    │────▶│   Pending   │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
      │                   │                   │                   │
      ▼                   ▼                   ▼                   ▼
  Enter details      Verify info        Publish to MLS      Under contract
  Upload photos      Check photos       Syndicate           Contingent
  Set pricing        Compliance         Accept showings     Negotiations
```

## Listing States

```typescript
type ListingStatus =
  | 'draft'           // Being created
  | 'review'          // Awaiting approval
  | 'active'          // On market
  | 'pending'         // Under contract
  | 'contingent'      // Contract with contingencies
  | 'sold'            // Closed
  | 'withdrawn'       // Removed by seller
  | 'expired'         // Listing period ended
  | 'off_market';     // Temporarily unavailable
```

## Property Data Structure

```typescript
interface PropertyListing {
  // Identification
  id: string;
  mlsNumber: string;
  source: 'manual' | 'mls_feed' | 'import';

  // Property Info
  propertyType: PropertyType;
  listingType: 'sale' | 'rent' | 'auction';
  address: {
    street: string;
    unit?: string;
    city: string;
    state: string;
    zipCode: string;
    county?: string;
  };
  coordinates: {
    latitude: number;
    longitude: number;
  };

  // Specifications
  specs: {
    bedrooms: number;
    bathrooms: number;
    halfBaths?: number;
    squareFeet: number;
    lotSize?: number;
    lotSizeUnit: 'sqft' | 'acres';
    yearBuilt: number;
    stories?: number;
    parkingSpaces?: number;
    garageSpaces?: number;
  };

  // Pricing
  pricing: {
    listPrice: number;
    currency: string;
    pricePerSqFt: number;
    priceHistory: {
      date: Date;
      price: number;
      event: 'listed' | 'reduced' | 'increased';
    }[];
  };

  // Features
  features: {
    interior: string[];
    exterior: string[];
    amenities: string[];
    appliances: string[];
    heating: string[];
    cooling: string[];
    flooring: string[];
  };

  // Media
  media: {
    photos: PropertyPhoto[];
    virtualTourUrl?: string;
    videoUrl?: string;
    floorPlans: Document[];
    brochure?: Document;
  };

  // Listing Info
  listing: {
    status: ListingStatus;
    listedDate: Date;
    expirationDate?: Date;
    daysOnMarket: number;
    agent: AgentInfo;
    brokerage: BrokerageInfo;
    showingInstructions?: string;
    remarks: string;
    privateRemarks?: string;
  };
}

type PropertyType =
  | 'single_family'
  | 'condo'
  | 'townhouse'
  | 'multi_family'
  | 'apartment'
  | 'land'
  | 'commercial'
  | 'industrial';
```

## MLS Integration

```typescript
interface MLSIntegration {
  // Feed Processing
  syncFeed(feedConfig: FeedConfig): Promise<SyncResult>;
  processUpdate(update: MLSUpdate): Promise<void>;

  // Data Mapping
  mapMLSToListing(mlsData: MLSRecord): PropertyListing;
  mapListingToMLS(listing: PropertyListing): MLSRecord;

  // Syndication
  publishToMLS(listing: PropertyListing): Promise<string>;
  updateMLSListing(mlsNumber: string, changes: Partial<PropertyListing>): Promise<void>;
  withdrawFromMLS(mlsNumber: string): Promise<void>;
}

interface FeedConfig {
  feedType: 'RETS' | 'RESO_WebAPI' | 'IDX';
  endpoint: string;
  credentials: Credentials;
  resourceTypes: string[];
  syncInterval: number;
}
```

## Search Implementation

```typescript
interface PropertySearch {
  // Query Builder
  query: {
    // Location
    location?: {
      city?: string;
      state?: string;
      zipCode?: string;
      radius?: { center: GeoPoint; miles: number };
      polygon?: GeoPoint[];
      neighborhood?: string;
    };

    // Price
    priceRange?: {
      min?: number;
      max?: number;
    };

    // Specs
    bedrooms?: { min?: number; max?: number };
    bathrooms?: { min?: number; max?: number };
    squareFeet?: { min?: number; max?: number };
    yearBuilt?: { min?: number; max?: number };

    // Type
    propertyTypes?: PropertyType[];
    listingTypes?: ('sale' | 'rent')[];

    // Features
    mustHave?: string[];
    niceToHave?: string[];

    // Status
    statuses?: ListingStatus[];
  };

  // Sort
  sortBy: 'price_asc' | 'price_desc' | 'date_newest' | 'date_oldest' | 'sqft' | 'relevance';

  // Pagination
  page: number;
  limit: number;
}
```

## Photo Management

```typescript
interface PropertyPhoto {
  id: string;
  url: string;
  thumbnailUrl: string;
  caption?: string;
  order: number;
  isPrimary: boolean;
  room?: string;
  dimensions: {
    width: number;
    height: number;
  };
  uploadedAt: Date;
}

interface PhotoService {
  uploadPhoto(listingId: string, file: File, metadata: PhotoMetadata): Promise<PropertyPhoto>;
  reorderPhotos(listingId: string, photoIds: string[]): Promise<void>;
  setPrimaryPhoto(listingId: string, photoId: string): Promise<void>;
  deletePhoto(listingId: string, photoId: string): Promise<void>;
  optimizePhoto(photoId: string): Promise<PropertyPhoto>;
}
```
