---
name: mongodb-basics
description: MongoDB fundamentals and document modeling
category: database/nosql
applies_to: mongodb
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# MongoDB Basics

## Overview

MongoDB is a document-oriented NoSQL database that stores data in
flexible, JSON-like documents. It's designed for scalability,
flexibility, and developer productivity.

## Core Concepts

```
┌─────────────────────────────────────────────────────────────────┐
│                    MongoDB Hierarchy                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Database                                                        │
│  └── Collection (like a table)                                  │
│      └── Document (like a row, but flexible JSON)               │
│          └── Field (like a column)                              │
│                                                                  │
│  Example:                                                        │
│  myapp (database)                                               │
│  └── users (collection)                                         │
│      └── { _id: ..., name: "John", email: "john@..." }         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Basic Operations

### Database and Collection

```javascript
// Connect
const { MongoClient } = require('mongodb');
const client = new MongoClient('mongodb://localhost:27017');
await client.connect();

// Select database
const db = client.db('myapp');

// Select collection (created automatically on first insert)
const users = db.collection('users');

// List databases
const dbs = await client.db().admin().listDatabases();

// List collections
const collections = await db.listCollections().toArray();

// Create collection with options
await db.createCollection('logs', {
  capped: true,
  size: 1000000,  // 1MB
  max: 1000       // Max documents
});
```

### Insert Operations

```javascript
// Insert one
const result = await users.insertOne({
  name: 'John Doe',
  email: 'john@example.com',
  age: 30,
  tags: ['developer', 'nodejs'],
  address: {
    city: 'New York',
    country: 'USA'
  },
  createdAt: new Date()
});
console.log(result.insertedId);

// Insert many
const result = await users.insertMany([
  { name: 'Alice', email: 'alice@example.com', age: 28 },
  { name: 'Bob', email: 'bob@example.com', age: 35 },
  { name: 'Carol', email: 'carol@example.com', age: 25 }
]);
console.log(result.insertedIds);

// Insert with custom _id
await users.insertOne({
  _id: 'custom-id-123',
  name: 'Custom ID User'
});
```

### Query Operations

```javascript
// Find one
const user = await users.findOne({ email: 'john@example.com' });

// Find all (returns cursor)
const cursor = users.find({ age: { $gte: 25 } });
const allUsers = await cursor.toArray();

// Find with projection (select specific fields)
const user = await users.findOne(
  { email: 'john@example.com' },
  { projection: { name: 1, email: 1, _id: 0 } }
);

// Find with sort, limit, skip
const results = await users
  .find({ age: { $gte: 18 } })
  .sort({ age: -1 })          // -1 = descending
  .skip(10)                   // Pagination offset
  .limit(5)                   // Max results
  .toArray();

// Count documents
const count = await users.countDocuments({ age: { $gte: 25 } });
const estimated = await users.estimatedDocumentCount();

// Distinct values
const cities = await users.distinct('address.city');
```

### Update Operations

```javascript
// Update one
await users.updateOne(
  { email: 'john@example.com' },
  { $set: { age: 31, updatedAt: new Date() } }
);

// Update many
await users.updateMany(
  { age: { $lt: 18 } },
  { $set: { status: 'minor' } }
);

// Replace entire document
await users.replaceOne(
  { email: 'john@example.com' },
  { name: 'John Smith', email: 'john@example.com', age: 31 }
);

// Upsert (insert if not exists)
await users.updateOne(
  { email: 'new@example.com' },
  { $set: { name: 'New User', age: 25 } },
  { upsert: true }
);

// Find and update (returns document)
const user = await users.findOneAndUpdate(
  { email: 'john@example.com' },
  { $inc: { loginCount: 1 } },
  { returnDocument: 'after' }  // 'before' or 'after'
);
```

### Delete Operations

```javascript
// Delete one
await users.deleteOne({ email: 'john@example.com' });

// Delete many
await users.deleteMany({ status: 'inactive' });

// Find and delete
const deleted = await users.findOneAndDelete({ email: 'john@example.com' });
```

## Query Operators

### Comparison Operators

```javascript
// Equal (implicit)
{ age: 25 }

// Comparison
{ age: { $eq: 25 } }    // Equal
{ age: { $ne: 25 } }    // Not equal
{ age: { $gt: 25 } }    // Greater than
{ age: { $gte: 25 } }   // Greater than or equal
{ age: { $lt: 25 } }    // Less than
{ age: { $lte: 25 } }   // Less than or equal

// In array of values
{ status: { $in: ['active', 'pending'] } }
{ status: { $nin: ['deleted', 'banned'] } }
```

### Logical Operators

```javascript
// AND (implicit)
{ status: 'active', age: { $gte: 18 } }

// AND (explicit)
{
  $and: [
    { status: 'active' },
    { age: { $gte: 18 } }
  ]
}

// OR
{
  $or: [
    { status: 'active' },
    { role: 'admin' }
  ]
}

// NOR (not any)
{
  $nor: [
    { status: 'deleted' },
    { status: 'banned' }
  ]
}

// NOT
{ age: { $not: { $lt: 18 } } }
```

### Element Operators

```javascript
// Field exists
{ phone: { $exists: true } }
{ deletedAt: { $exists: false } }

// Type check
{ age: { $type: 'number' } }
{ tags: { $type: 'array' } }
```

### Array Operators

```javascript
// Contains element
{ tags: 'mongodb' }  // tags array contains 'mongodb'

// Contains all elements
{ tags: { $all: ['mongodb', 'nodejs'] } }

// Array size
{ tags: { $size: 3 } }

// Element match (subdocument in array)
{
  orders: {
    $elemMatch: {
      product: 'laptop',
      quantity: { $gte: 1 }
    }
  }
}
```

### Text Search

```javascript
// Create text index
await users.createIndex({ name: 'text', bio: 'text' });

// Text search
const results = await users.find({
  $text: { $search: 'developer javascript' }
}).toArray();

// With score
const results = await users.find(
  { $text: { $search: 'developer' } },
  { projection: { score: { $meta: 'textScore' } } }
).sort({ score: { $meta: 'textScore' } }).toArray();
```

## Update Operators

### Field Operators

```javascript
// Set field value
{ $set: { name: 'New Name', 'address.city': 'Boston' } }

// Unset field (remove)
{ $unset: { temporaryField: '' } }

// Rename field
{ $rename: { oldName: 'newName' } }

// Increment/decrement
{ $inc: { views: 1, balance: -10 } }

// Multiply
{ $mul: { price: 1.1 } }  // 10% increase

// Min (set if less than)
{ $min: { lowestScore: 50 } }

// Max (set if greater than)
{ $max: { highestScore: 100 } }

// Set on insert only
{ $setOnInsert: { createdAt: new Date() } }

// Current date
{ $currentDate: { updatedAt: true, lastModified: { $type: 'timestamp' } } }
```

### Array Operators

```javascript
// Push to array
{ $push: { tags: 'newTag' } }

// Push multiple
{ $push: { tags: { $each: ['tag1', 'tag2'] } } }

// Push with limit (keep last N)
{
  $push: {
    recentLogins: {
      $each: [new Date()],
      $slice: -10  // Keep last 10
    }
  }
}

// Add to set (no duplicates)
{ $addToSet: { tags: 'uniqueTag' } }
{ $addToSet: { tags: { $each: ['tag1', 'tag2'] } } }

// Pull (remove) from array
{ $pull: { tags: 'oldTag' } }
{ $pull: { orders: { status: 'cancelled' } } }

// Pull all
{ $pullAll: { tags: ['tag1', 'tag2'] } }

// Pop (remove first/last)
{ $pop: { queue: 1 } }   // Remove last
{ $pop: { queue: -1 } }  // Remove first

// Update array element by index
{ $set: { 'tags.0': 'firstTag' } }

// Update first matching element
await users.updateOne(
  { 'orders.id': 'order-1' },
  { $set: { 'orders.$.status': 'shipped' } }
);

// Update all matching elements
await users.updateOne(
  { 'orders.status': 'pending' },
  { $set: { 'orders.$[elem].status': 'processing' } },
  { arrayFilters: [{ 'elem.status': 'pending' }] }
);
```

## Aggregation Pipeline

```javascript
// Basic aggregation
const results = await users.aggregate([
  // Stage 1: Filter
  { $match: { status: 'active' } },

  // Stage 2: Group
  {
    $group: {
      _id: '$department',
      count: { $sum: 1 },
      avgAge: { $avg: '$age' },
      totalSalary: { $sum: '$salary' }
    }
  },

  // Stage 3: Sort
  { $sort: { totalSalary: -1 } },

  // Stage 4: Limit
  { $limit: 10 }
]).toArray();

// Project (reshape documents)
{
  $project: {
    fullName: { $concat: ['$firstName', ' ', '$lastName'] },
    year: { $year: '$createdAt' },
    isAdult: { $gte: ['$age', 18] }
  }
}

// Lookup (join)
{
  $lookup: {
    from: 'orders',
    localField: '_id',
    foreignField: 'userId',
    as: 'userOrders'
  }
}

// Unwind (flatten array)
{ $unwind: '$tags' }
{ $unwind: { path: '$orders', preserveNullAndEmptyArrays: true } }

// Add fields
{
  $addFields: {
    totalPrice: { $multiply: ['$price', '$quantity'] }
  }
}

// Bucket (group into ranges)
{
  $bucket: {
    groupBy: '$age',
    boundaries: [0, 18, 30, 50, 100],
    default: 'Other',
    output: {
      count: { $sum: 1 },
      names: { $push: '$name' }
    }
  }
}
```

## Indexes

```javascript
// Create single field index
await users.createIndex({ email: 1 });  // 1 = ascending

// Compound index
await users.createIndex({ status: 1, createdAt: -1 });

// Unique index
await users.createIndex({ email: 1 }, { unique: true });

// Sparse index (skip null values)
await users.createIndex({ phone: 1 }, { sparse: true });

// TTL index (auto-delete after time)
await sessions.createIndex({ createdAt: 1 }, { expireAfterSeconds: 3600 });

// Text index
await articles.createIndex({ title: 'text', content: 'text' });

// Geospatial index
await places.createIndex({ location: '2dsphere' });

// List indexes
const indexes = await users.indexes();

// Drop index
await users.dropIndex('email_1');
```

## Transactions (MongoDB 4.0+)

```javascript
const session = client.startSession();

try {
  session.startTransaction({
    readConcern: { level: 'snapshot' },
    writeConcern: { w: 'majority' }
  });

  await accounts.updateOne(
    { _id: fromAccountId },
    { $inc: { balance: -amount } },
    { session }
  );

  await accounts.updateOne(
    { _id: toAccountId },
    { $inc: { balance: amount } },
    { session }
  );

  await session.commitTransaction();
} catch (error) {
  await session.abortTransaction();
  throw error;
} finally {
  await session.endSession();
}
```

## Document Design Patterns

### Embedding vs Referencing

```javascript
// Embedding (denormalized) - for 1:few relationships
{
  _id: ObjectId('...'),
  name: 'John Doe',
  addresses: [
    { type: 'home', city: 'New York' },
    { type: 'work', city: 'Boston' }
  ]
}

// Referencing (normalized) - for 1:many or many:many
// User document
{
  _id: ObjectId('user1'),
  name: 'John Doe'
}

// Order documents
{
  _id: ObjectId('order1'),
  userId: ObjectId('user1'),  // Reference
  total: 99.99
}
```

### Bucket Pattern

```javascript
// Store time-series data efficiently
{
  sensorId: 'sensor-1',
  date: ISODate('2024-01-15'),
  readings: [
    { time: ISODate('2024-01-15T00:00:00'), value: 23.5 },
    { time: ISODate('2024-01-15T00:01:00'), value: 23.6 },
    // ... more readings
  ],
  count: 1440,
  avg: 24.2,
  min: 22.1,
  max: 26.3
}
```

### Polymorphic Pattern

```javascript
// Different types in same collection
{
  type: 'book',
  title: 'MongoDB Guide',
  isbn: '123-456',
  pages: 500
}

{
  type: 'movie',
  title: 'Database Documentary',
  duration: 120,
  director: 'John Smith'
}
```
