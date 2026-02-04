# Route Optimization Patterns

## Overview
Algorithms and strategies for route optimization in logistics.

## Key Algorithms

### Vehicle Routing Problem (VRP)
**When to use:** Optimizing delivery routes with multiple vehicles
**Description:** Classic optimization problem for logistics
**Approaches:**
- Exact algorithms (Branch and Bound) - small instances
- Heuristics (Clarke-Wright Savings) - medium instances
- Metaheuristics (Genetic Algorithm, Simulated Annealing) - large instances

### Traveling Salesman Problem (TSP)
**When to use:** Single vehicle, visit all points once
**Description:** Find shortest route visiting all stops
**Example:**
```typescript
// Nearest Neighbor Heuristic
const nearestNeighbor = (depot: Location, stops: Location[]) => {
  const route = [depot];
  const remaining = [...stops];

  while (remaining.length > 0) {
    const current = route[route.length - 1];
    const nearest = findNearest(current, remaining);
    route.push(nearest);
    remaining.splice(remaining.indexOf(nearest), 1);
  }

  route.push(depot); // Return to depot
  return route;
};
```

### Time Window Constraints
**When to use:** Deliveries with specific time slots
**Description:** Route optimization respecting delivery windows
**Example:**
```typescript
interface TimeWindowStop {
  location: Location;
  timeWindow: {
    earliest: Date;
    latest: Date;
  };
  serviceDuration: number;
}

const isTimeWindowFeasible = (
  arrivalTime: Date,
  stop: TimeWindowStop
): boolean => {
  const departureTime = new Date(
    arrivalTime.getTime() + stop.serviceDuration * 60000
  );

  return arrivalTime <= stop.timeWindow.latest &&
         departureTime >= stop.timeWindow.earliest;
};
```

## Optimization Strategies

### Clustering First, Route Second
```typescript
// 1. Cluster stops by geography
const clusters = kMeansClustering(stops, numVehicles);

// 2. Optimize route within each cluster
const routes = clusters.map(cluster =>
  solveTSP(depot, cluster.stops)
);
```

### Dynamic Re-optimization
```typescript
// Triggered by:
// - New order added
// - Traffic delay detected
// - Driver deviation
// - Failed delivery

const reoptimize = async (currentRoutes, trigger) => {
  const remainingStops = getRemainingStops(currentRoutes);
  const newRoutes = await optimize(remainingStops, {
    respectCurrentProgress: true,
    trigger
  });
  return newRoutes;
};
```

## Integration with Maps APIs

### Google Maps Platform
```typescript
const getRouteMatrix = async (origins: Location[], destinations: Location[]) => {
  const response = await fetch(
    `https://maps.googleapis.com/maps/api/distancematrix/json?` +
    `origins=${formatLocations(origins)}&` +
    `destinations=${formatLocations(destinations)}&` +
    `departure_time=now&` +
    `traffic_model=best_guess&` +
    `key=${API_KEY}`
  );
  return response.json();
};
```

### OR-Tools Integration
```typescript
// Using Google OR-Tools for VRP
import { RoutingIndexManager, RoutingModel } from 'ortools';

const solveVRP = (distanceMatrix, numVehicles, depot) => {
  const manager = new RoutingIndexManager(
    distanceMatrix.length,
    numVehicles,
    depot
  );
  const routing = new RoutingModel(manager);

  // Add distance callback
  const distanceCallback = routing.registerTransitCallback(
    (fromIndex, toIndex) => {
      const fromNode = manager.indexToNode(fromIndex);
      const toNode = manager.indexToNode(toIndex);
      return distanceMatrix[fromNode][toNode];
    }
  );

  routing.setArcCostEvaluatorOfAllVehicles(distanceCallback);

  return routing.solveWithParameters(searchParameters);
};
```

## Best Practices
- Pre-compute distance matrices
- Use traffic-aware routing for urban areas
- Consider service time in optimization
- Implement real-time re-routing
- Cache frequently used routes

## Anti-Patterns to Avoid
- Ignoring traffic patterns
- Not accounting for service time
- Over-optimizing (diminishing returns)
- Using straight-line distance instead of road distance
