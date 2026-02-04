# Delivery Flow Template

## Last-Mile Delivery Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Dispatch  │────▶│   En Route  │────▶│   Arrival   │────▶│  Delivery   │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
      │                   │                   │                   │
      ▼                   ▼                   ▼                   ▼
  Route assign        GPS tracking       ETA update         POD capture
  Load vehicle        Traffic update     Customer notify    Signature
  Driver accept       Exception alert    Arrival scan       Photo proof
```

## Delivery States

```typescript
type DeliveryStatus =
  | 'pending'           // Order received
  | 'assigned'          // Assigned to driver
  | 'picked_up'         // Picked up from warehouse
  | 'in_transit'        // On the way
  | 'out_for_delivery'  // Last leg
  | 'arrived'           // At delivery location
  | 'delivered'         // Successfully delivered
  | 'failed_attempt'    // Delivery attempted but failed
  | 'returned'          // Returned to sender
  | 'cancelled';        // Cancelled
```

## Proof of Delivery (POD)

```typescript
interface ProofOfDelivery {
  deliveryId: string;
  timestamp: Date;

  // Location verification
  coordinates: {
    latitude: number;
    longitude: number;
    accuracy: number;
  };
  geofenceVerified: boolean;

  // Recipient
  recipientName: string;
  recipientType: 'addressee' | 'household_member' | 'neighbor' | 'concierge';

  // Signature
  signature?: {
    image: string; // base64
    capturedAt: Date;
  };

  // Photos
  photos: {
    type: 'package' | 'location' | 'damage';
    image: string;
    capturedAt: Date;
  }[];

  // Notes
  notes?: string;

  // Verification
  verificationMethod: 'signature' | 'photo' | 'pin' | 'otp';
}
```

## Route Optimization

```typescript
interface RouteOptimization {
  // Input
  depot: Location;
  stops: DeliveryStop[];
  vehicles: Vehicle[];
  constraints: RouteConstraints;

  // Output
  routes: OptimizedRoute[];
  totalDistance: number;
  totalTime: number;
  unassignedStops: DeliveryStop[];
}

interface RouteConstraints {
  maxStopsPerRoute: number;
  maxRouteTime: number; // minutes
  maxRouteDistance: number; // km
  timeWindows: boolean;
  vehicleCapacity: boolean;
  trafficAware: boolean;
}

interface DeliveryStop {
  id: string;
  location: Location;
  timeWindow?: {
    start: Date;
    end: Date;
  };
  serviceDuration: number; // minutes
  priority: number;
  packageCount: number;
  weight: number;
}
```

## Notification Templates

### Status Update
```json
{
  "type": "status_update",
  "template": "Your package {{tracking_number}} is now {{status}}",
  "channels": ["sms", "push", "email"]
}
```

### ETA Update
```json
{
  "type": "eta_update",
  "template": "Your delivery is {{eta_minutes}} minutes away",
  "channels": ["push"]
}
```

### Delivery Attempt
```json
{
  "type": "failed_delivery",
  "template": "We missed you! Reschedule your delivery: {{reschedule_link}}",
  "channels": ["sms", "email"]
}
```
