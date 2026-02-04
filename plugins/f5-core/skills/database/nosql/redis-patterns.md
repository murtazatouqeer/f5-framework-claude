---
name: redis-patterns
description: Redis data structures and common patterns
category: database/nosql
applies_to: redis
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Redis Patterns

## Overview

Redis is an in-memory data structure store used as database, cache,
message broker, and streaming engine. Its power comes from rich data
structures and atomic operations.

## Data Structures

```
┌─────────────────────────────────────────────────────────────────┐
│                    Redis Data Structures                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  String     │ Simple key-value, numbers, binary                 │
│  List       │ Ordered collection, queue/stack                   │
│  Set        │ Unordered unique values                           │
│  Sorted Set │ Unique values with score (ranking)                │
│  Hash       │ Object-like field-value pairs                     │
│  Stream     │ Append-only log (event sourcing)                  │
│  HyperLogLog│ Probabilistic cardinality                         │
│  Bitmap     │ Bit-level operations                              │
│  Geospatial │ Location-based queries                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## String Operations

```javascript
const redis = require('redis');
const client = redis.createClient();

// Basic string operations
await client.set('key', 'value');
await client.get('key');  // 'value'

// With expiration
await client.setEx('session:123', 3600, 'user-data');  // 1 hour TTL
await client.set('key', 'value', { EX: 3600 });        // Alternative

// Only set if not exists
await client.setNX('lock:resource', 'locked');

// Only set if exists
await client.set('key', 'new-value', { XX: true });

// Get and set
const oldValue = await client.getSet('counter', '0');

// Increment/Decrement
await client.set('counter', '10');
await client.incr('counter');        // 11
await client.incrBy('counter', 5);   // 16
await client.decr('counter');        // 15
await client.incrByFloat('price', 0.5);

// Multiple operations
await client.mSet(['key1', 'val1', 'key2', 'val2']);
const values = await client.mGet(['key1', 'key2']);

// String manipulation
await client.append('key', '-suffix');
const length = await client.strLen('key');
const substring = await client.getRange('key', 0, 4);
```

## Hash Operations

```javascript
// Object-like storage
await client.hSet('user:1001', {
  name: 'John Doe',
  email: 'john@example.com',
  age: '30',
  active: 'true'
});

// Get single field
const name = await client.hGet('user:1001', 'name');

// Get multiple fields
const [name, email] = await client.hmGet('user:1001', ['name', 'email']);

// Get all fields
const user = await client.hGetAll('user:1001');
// { name: 'John Doe', email: 'john@example.com', ... }

// Check field exists
const exists = await client.hExists('user:1001', 'phone');

// Increment field
await client.hIncrBy('user:1001', 'loginCount', 1);
await client.hIncrByFloat('user:1001', 'balance', 10.50);

// Delete field
await client.hDel('user:1001', 'temporaryField');

// Get all keys/values
const fields = await client.hKeys('user:1001');
const values = await client.hVals('user:1001');

// Set only if field not exists
await client.hSetNX('user:1001', 'createdAt', Date.now());
```

## List Operations

```javascript
// Add to list
await client.lPush('queue', 'item1');  // Add to left (front)
await client.rPush('queue', 'item2');  // Add to right (back)

// Remove from list
const item = await client.lPop('queue');   // Remove from left
const item = await client.rPop('queue');   // Remove from right

// Blocking pop (wait for item)
const [key, item] = await client.blPop('queue', 5);  // 5 sec timeout

// Get range (0-indexed, -1 is last)
const items = await client.lRange('queue', 0, -1);   // All items
const items = await client.lRange('queue', 0, 9);    // First 10

// Get by index
const item = await client.lIndex('queue', 0);  // First item

// Get length
const length = await client.lLen('queue');

// Trim list (keep range)
await client.lTrim('recent:views', 0, 99);  // Keep first 100

// Insert
await client.lInsert('list', 'BEFORE', 'pivot', 'value');
await client.lInsert('list', 'AFTER', 'pivot', 'value');

// Set by index
await client.lSet('list', 0, 'new-value');

// Remove by value
await client.lRem('list', 2, 'value');   // Remove 2 occurrences
await client.lRem('list', -2, 'value');  // From right
await client.lRem('list', 0, 'value');   // All occurrences
```

## Set Operations

```javascript
// Add members
await client.sAdd('tags:article:1', ['tech', 'redis', 'database']);

// Remove member
await client.sRem('tags:article:1', 'old-tag');

// Check membership
const isMember = await client.sIsMember('tags:article:1', 'tech');

// Get all members
const tags = await client.sMembers('tags:article:1');

// Get random member(s)
const random = await client.sRandMember('tags:article:1');
const randoms = await client.sRandMember('tags:article:1', 3);

// Pop random member
const popped = await client.sPop('tags:article:1');

// Count members
const count = await client.sCard('tags:article:1');

// Set operations
const union = await client.sUnion(['set1', 'set2']);
const inter = await client.sInter(['set1', 'set2']);
const diff = await client.sDiff(['set1', 'set2']);  // In set1 but not set2

// Store result of set operation
await client.sUnionStore('result', ['set1', 'set2']);

// Move member between sets
await client.sMove('source', 'destination', 'member');
```

## Sorted Set Operations

```javascript
// Add with scores
await client.zAdd('leaderboard', [
  { score: 100, value: 'player1' },
  { score: 85, value: 'player2' },
  { score: 92, value: 'player3' }
]);

// Increment score
await client.zIncrBy('leaderboard', 5, 'player2');  // 85 + 5 = 90

// Get rank (0-indexed, lowest score = 0)
const rank = await client.zRank('leaderboard', 'player1');
const revRank = await client.zRevRank('leaderboard', 'player1');  // Highest first

// Get score
const score = await client.zScore('leaderboard', 'player1');

// Get range by rank
const top10 = await client.zRevRange('leaderboard', 0, 9);  // Highest first
const top10WithScores = await client.zRevRange('leaderboard', 0, 9, { WITHSCORES: true });

// Get range by score
const highScorers = await client.zRangeByScore('leaderboard', 90, 100);

// Count in score range
const count = await client.zCount('leaderboard', 50, 100);

// Remove by rank
await client.zRemRangeByRank('leaderboard', 0, 9);  // Remove bottom 10

// Remove by score
await client.zRemRangeByScore('leaderboard', 0, 50);  // Remove low scores

// Remove member
await client.zRem('leaderboard', 'player1');

// Get cardinality
const total = await client.zCard('leaderboard');
```

## Common Patterns

### Caching

```javascript
// Cache-aside pattern
async function getUser(userId) {
  const cacheKey = `user:${userId}`;

  // Try cache first
  let user = await client.get(cacheKey);
  if (user) {
    return JSON.parse(user);
  }

  // Cache miss - fetch from database
  user = await database.getUser(userId);

  // Store in cache with TTL
  await client.setEx(cacheKey, 3600, JSON.stringify(user));

  return user;
}

// Write-through pattern
async function updateUser(userId, data) {
  const cacheKey = `user:${userId}`;

  // Update database
  await database.updateUser(userId, data);

  // Update cache
  await client.setEx(cacheKey, 3600, JSON.stringify(data));
}

// Cache invalidation
async function deleteUser(userId) {
  await database.deleteUser(userId);
  await client.del(`user:${userId}`);
}
```

### Session Storage

```javascript
// Store session
async function createSession(userId, sessionData) {
  const sessionId = crypto.randomUUID();
  const sessionKey = `session:${sessionId}`;

  await client.hSet(sessionKey, {
    userId,
    ...sessionData,
    createdAt: Date.now()
  });

  // Expire in 24 hours
  await client.expire(sessionKey, 86400);

  return sessionId;
}

// Get session
async function getSession(sessionId) {
  const session = await client.hGetAll(`session:${sessionId}`);
  return Object.keys(session).length ? session : null;
}

// Extend session
async function touchSession(sessionId) {
  await client.expire(`session:${sessionId}`, 86400);
}

// Destroy session
async function destroySession(sessionId) {
  await client.del(`session:${sessionId}`);
}
```

### Rate Limiting

```javascript
// Fixed window rate limiter
async function checkRateLimit(userId, limit = 100, windowSecs = 60) {
  const key = `ratelimit:${userId}:${Math.floor(Date.now() / (windowSecs * 1000))}`;

  const count = await client.incr(key);

  if (count === 1) {
    await client.expire(key, windowSecs);
  }

  return {
    allowed: count <= limit,
    remaining: Math.max(0, limit - count),
    resetIn: await client.ttl(key)
  };
}

// Sliding window rate limiter
async function slidingWindowRateLimit(userId, limit = 100, windowSecs = 60) {
  const key = `ratelimit:${userId}`;
  const now = Date.now();
  const windowStart = now - (windowSecs * 1000);

  const multi = client.multi();

  // Remove old entries
  multi.zRemRangeByScore(key, 0, windowStart);

  // Count current window
  multi.zCard(key);

  // Add current request
  multi.zAdd(key, { score: now, value: `${now}:${Math.random()}` });

  // Set expiry
  multi.expire(key, windowSecs);

  const results = await multi.exec();
  const count = results[1];

  return {
    allowed: count < limit,
    remaining: Math.max(0, limit - count - 1)
  };
}
```

### Leaderboard

```javascript
// Add/update score
async function updateScore(gameId, playerId, score) {
  await client.zAdd(`leaderboard:${gameId}`, { score, value: playerId });
}

// Increment score
async function addScore(gameId, playerId, points) {
  return await client.zIncrBy(`leaderboard:${gameId}`, points, playerId);
}

// Get top players
async function getTopPlayers(gameId, count = 10) {
  return await client.zRevRange(`leaderboard:${gameId}`, 0, count - 1, {
    WITHSCORES: true
  });
}

// Get player rank
async function getPlayerRank(gameId, playerId) {
  const rank = await client.zRevRank(`leaderboard:${gameId}`, playerId);
  const score = await client.zScore(`leaderboard:${gameId}`, playerId);
  return { rank: rank !== null ? rank + 1 : null, score };
}

// Get players around a player
async function getPlayersAround(gameId, playerId, range = 5) {
  const rank = await client.zRevRank(`leaderboard:${gameId}`, playerId);
  if (rank === null) return [];

  const start = Math.max(0, rank - range);
  const end = rank + range;

  return await client.zRevRange(`leaderboard:${gameId}`, start, end, {
    WITHSCORES: true
  });
}
```

### Pub/Sub Messaging

```javascript
// Publisher
async function publishMessage(channel, message) {
  await client.publish(channel, JSON.stringify(message));
}

// Subscriber
const subscriber = client.duplicate();
await subscriber.connect();

await subscriber.subscribe('notifications', (message) => {
  const data = JSON.parse(message);
  console.log('Received:', data);
});

// Pattern subscription
await subscriber.pSubscribe('events:*', (message, channel) => {
  console.log(`${channel}: ${message}`);
});
```

### Distributed Lock

```javascript
// Acquire lock with automatic expiry
async function acquireLock(resource, ttlMs = 10000) {
  const lockKey = `lock:${resource}`;
  const lockValue = crypto.randomUUID();

  const acquired = await client.set(lockKey, lockValue, {
    NX: true,  // Only if not exists
    PX: ttlMs  // Milliseconds TTL
  });

  return acquired ? lockValue : null;
}

// Release lock (only if we own it)
async function releaseLock(resource, lockValue) {
  const lockKey = `lock:${resource}`;

  // Lua script for atomic check-and-delete
  const script = `
    if redis.call("get", KEYS[1]) == ARGV[1] then
      return redis.call("del", KEYS[1])
    else
      return 0
    end
  `;

  return await client.eval(script, {
    keys: [lockKey],
    arguments: [lockValue]
  });
}

// Usage
async function doExclusiveWork(resource) {
  const lockValue = await acquireLock(resource);
  if (!lockValue) {
    throw new Error('Could not acquire lock');
  }

  try {
    // Do exclusive work...
  } finally {
    await releaseLock(resource, lockValue);
  }
}
```

### Queue (Producer/Consumer)

```javascript
// Producer: Add jobs to queue
async function enqueue(queueName, job) {
  await client.rPush(queueName, JSON.stringify({
    id: crypto.randomUUID(),
    data: job,
    createdAt: Date.now()
  }));
}

// Consumer: Process jobs
async function processQueue(queueName, handler) {
  while (true) {
    // Blocking pop with timeout
    const result = await client.blPop(queueName, 5);

    if (result) {
      const job = JSON.parse(result.element);
      try {
        await handler(job);
      } catch (error) {
        // Move to dead letter queue
        await client.rPush(`${queueName}:failed`, JSON.stringify({
          ...job,
          error: error.message,
          failedAt: Date.now()
        }));
      }
    }
  }
}

// Reliable queue (with processing list)
async function reliableDequeue(queueName) {
  const processingKey = `${queueName}:processing`;

  // Move from queue to processing
  const job = await client.rPopLPush(queueName, processingKey);
  return job ? JSON.parse(job) : null;
}

async function ackJob(queueName, job) {
  await client.lRem(`${queueName}:processing`, 1, JSON.stringify(job));
}
```

### Recent Activity Feed

```javascript
// Add activity
async function addActivity(userId, activity) {
  const key = `feed:${userId}`;

  // Add to front of list
  await client.lPush(key, JSON.stringify({
    ...activity,
    timestamp: Date.now()
  }));

  // Trim to last 100 items
  await client.lTrim(key, 0, 99);
}

// Get recent activity
async function getActivity(userId, limit = 20) {
  const items = await client.lRange(`feed:${userId}`, 0, limit - 1);
  return items.map(JSON.parse);
}
```
