---
name: dynamodb-modeling
description: DynamoDB single-table design and access patterns
category: database/nosql
applies_to: dynamodb
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# DynamoDB Modeling

## Overview

DynamoDB is a fully managed NoSQL database that provides single-digit
millisecond performance at any scale. Effective modeling requires
understanding access patterns upfront.

## Core Concepts

```
┌─────────────────────────────────────────────────────────────────┐
│                    DynamoDB Structure                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Table                                                           │
│  └── Item (like a row)                                          │
│      └── Attributes (like columns, but flexible)                │
│                                                                  │
│  Primary Key Options:                                            │
│  1. Partition Key (PK) only - Simple                            │
│  2. Partition Key + Sort Key (SK) - Composite                   │
│                                                                  │
│  Secondary Indexes:                                              │
│  - GSI: Global Secondary Index (different PK/SK)                │
│  - LSI: Local Secondary Index (same PK, different SK)           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Single-Table Design

### Why Single Table?

```
┌─────────────────────────────────────────────────────────────────┐
│              Single Table vs Multiple Tables                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Multiple Tables:                                                │
│  - Multiple API calls for related data                          │
│  - Higher latency                                                │
│  - More complex application logic                                │
│                                                                  │
│  Single Table:                                                   │
│  - Fetch related data in one query                              │
│  - Lower latency                                                 │
│  - Complex design, simpler application                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Generic Key Design

```javascript
// Common pattern: Generic PK/SK attributes
const table = {
  TableName: 'MyApp',
  KeySchema: [
    { AttributeName: 'PK', KeyType: 'HASH' },   // Partition key
    { AttributeName: 'SK', KeyType: 'RANGE' }   // Sort key
  ],
  AttributeDefinitions: [
    { AttributeName: 'PK', AttributeType: 'S' },
    { AttributeName: 'SK', AttributeType: 'S' },
    { AttributeName: 'GSI1PK', AttributeType: 'S' },
    { AttributeName: 'GSI1SK', AttributeType: 'S' }
  ],
  GlobalSecondaryIndexes: [
    {
      IndexName: 'GSI1',
      KeySchema: [
        { AttributeName: 'GSI1PK', KeyType: 'HASH' },
        { AttributeName: 'GSI1SK', KeyType: 'RANGE' }
      ],
      Projection: { ProjectionType: 'ALL' }
    }
  ]
};
```

## Access Patterns to Schema

### Step 1: List Access Patterns

```
┌─────────────────────────────────────────────────────────────────┐
│                    E-Commerce Example                            │
├─────────────────────────────────────────────────────────────────┤
│  Access Pattern                  │ Key Design                   │
├──────────────────────────────────┼──────────────────────────────┤
│  Get user by ID                  │ PK=USER#<id>                 │
│  Get user's orders               │ PK=USER#<id>, SK=ORDER#      │
│  Get order details               │ PK=ORDER#<id>                │
│  Get order items                 │ PK=ORDER#<id>, SK=ITEM#      │
│  Get orders by date (user)       │ GSI: GSI1PK=USER#<id>,       │
│                                  │      GSI1SK=<date>           │
│  Get product by ID               │ PK=PRODUCT#<id>              │
│  Get products by category        │ GSI: GSI1PK=CAT#<cat>,       │
│                                  │      GSI1SK=PRODUCT#         │
└─────────────────────────────────────────────────────────────────┘
```

### Step 2: Design Items

```javascript
// User item
const user = {
  PK: 'USER#user123',
  SK: 'USER#user123',
  Type: 'User',
  Email: 'john@example.com',
  Name: 'John Doe',
  GSI1PK: 'EMAIL#john@example.com',
  GSI1SK: 'USER#user123',
  CreatedAt: '2024-01-15T10:30:00Z'
};

// Order item
const order = {
  PK: 'USER#user123',
  SK: 'ORDER#2024-01-15#ord456',
  Type: 'Order',
  OrderId: 'ord456',
  Status: 'pending',
  Total: 99.99,
  GSI1PK: 'ORDER#ord456',
  GSI1SK: 'ORDER#ord456',
  CreatedAt: '2024-01-15T10:30:00Z'
};

// Order item (line item)
const orderItem = {
  PK: 'ORDER#ord456',
  SK: 'ITEM#prod789',
  Type: 'OrderItem',
  ProductId: 'prod789',
  ProductName: 'Widget',
  Quantity: 2,
  Price: 49.99
};

// Product item
const product = {
  PK: 'PRODUCT#prod789',
  SK: 'PRODUCT#prod789',
  Type: 'Product',
  Name: 'Widget',
  Category: 'Electronics',
  Price: 49.99,
  GSI1PK: 'CAT#Electronics',
  GSI1SK: 'PRODUCT#prod789'
};
```

## Query Patterns

### Basic Operations

```javascript
const { DynamoDBClient } = require('@aws-sdk/client-dynamodb');
const { DynamoDBDocumentClient, GetCommand, PutCommand, QueryCommand, UpdateCommand, DeleteCommand } = require('@aws-sdk/lib-dynamodb');

const client = DynamoDBDocumentClient.from(new DynamoDBClient({}));

// Get single item
const getUser = async (userId) => {
  const { Item } = await client.send(new GetCommand({
    TableName: 'MyApp',
    Key: {
      PK: `USER#${userId}`,
      SK: `USER#${userId}`
    }
  }));
  return Item;
};

// Put item
const createUser = async (user) => {
  await client.send(new PutCommand({
    TableName: 'MyApp',
    Item: {
      PK: `USER#${user.id}`,
      SK: `USER#${user.id}`,
      Type: 'User',
      ...user,
      GSI1PK: `EMAIL#${user.email}`,
      GSI1SK: `USER#${user.id}`
    },
    ConditionExpression: 'attribute_not_exists(PK)'  // Don't overwrite
  }));
};

// Query user's orders
const getUserOrders = async (userId, limit = 20) => {
  const { Items } = await client.send(new QueryCommand({
    TableName: 'MyApp',
    KeyConditionExpression: 'PK = :pk AND begins_with(SK, :sk)',
    ExpressionAttributeValues: {
      ':pk': `USER#${userId}`,
      ':sk': 'ORDER#'
    },
    ScanIndexForward: false,  // Newest first
    Limit: limit
  }));
  return Items;
};

// Query with filter
const getPendingOrders = async (userId) => {
  const { Items } = await client.send(new QueryCommand({
    TableName: 'MyApp',
    KeyConditionExpression: 'PK = :pk AND begins_with(SK, :sk)',
    FilterExpression: '#status = :status',
    ExpressionAttributeNames: {
      '#status': 'Status'  // Status is reserved word
    },
    ExpressionAttributeValues: {
      ':pk': `USER#${userId}`,
      ':sk': 'ORDER#',
      ':status': 'pending'
    }
  }));
  return Items;
};
```

### GSI Queries

```javascript
// Get user by email (GSI1)
const getUserByEmail = async (email) => {
  const { Items } = await client.send(new QueryCommand({
    TableName: 'MyApp',
    IndexName: 'GSI1',
    KeyConditionExpression: 'GSI1PK = :pk',
    ExpressionAttributeValues: {
      ':pk': `EMAIL#${email}`
    }
  }));
  return Items[0];
};

// Get products by category (GSI1)
const getProductsByCategory = async (category) => {
  const { Items } = await client.send(new QueryCommand({
    TableName: 'MyApp',
    IndexName: 'GSI1',
    KeyConditionExpression: 'GSI1PK = :pk AND begins_with(GSI1SK, :sk)',
    ExpressionAttributeValues: {
      ':pk': `CAT#${category}`,
      ':sk': 'PRODUCT#'
    }
  }));
  return Items;
};
```

### Update Operations

```javascript
// Update with condition
const updateOrderStatus = async (orderId, newStatus) => {
  await client.send(new UpdateCommand({
    TableName: 'MyApp',
    Key: {
      PK: `ORDER#${orderId}`,
      SK: `ORDER#${orderId}`
    },
    UpdateExpression: 'SET #status = :newStatus, UpdatedAt = :now',
    ConditionExpression: '#status <> :newStatus',
    ExpressionAttributeNames: {
      '#status': 'Status'
    },
    ExpressionAttributeValues: {
      ':newStatus': newStatus,
      ':now': new Date().toISOString()
    }
  }));
};

// Atomic counter
const incrementViewCount = async (productId) => {
  const { Attributes } = await client.send(new UpdateCommand({
    TableName: 'MyApp',
    Key: {
      PK: `PRODUCT#${productId}`,
      SK: `PRODUCT#${productId}`
    },
    UpdateExpression: 'SET ViewCount = if_not_exists(ViewCount, :zero) + :inc',
    ExpressionAttributeValues: {
      ':zero': 0,
      ':inc': 1
    },
    ReturnValues: 'UPDATED_NEW'
  }));
  return Attributes.ViewCount;
};

// Add to set
const addTag = async (productId, tag) => {
  await client.send(new UpdateCommand({
    TableName: 'MyApp',
    Key: {
      PK: `PRODUCT#${productId}`,
      SK: `PRODUCT#${productId}`
    },
    UpdateExpression: 'ADD Tags :tag',
    ExpressionAttributeValues: {
      ':tag': new Set([tag])
    }
  }));
};
```

### Transactions

```javascript
const { TransactWriteCommand, TransactGetCommand } = require('@aws-sdk/lib-dynamodb');

// Transactional write (all or nothing)
const createOrder = async (order, items) => {
  const transactItems = [
    // Create order
    {
      Put: {
        TableName: 'MyApp',
        Item: {
          PK: `USER#${order.userId}`,
          SK: `ORDER#${order.date}#${order.id}`,
          Type: 'Order',
          ...order
        }
      }
    },
    // Create order items
    ...items.map(item => ({
      Put: {
        TableName: 'MyApp',
        Item: {
          PK: `ORDER#${order.id}`,
          SK: `ITEM#${item.productId}`,
          Type: 'OrderItem',
          ...item
        }
      }
    })),
    // Decrement inventory for each item
    ...items.map(item => ({
      Update: {
        TableName: 'MyApp',
        Key: {
          PK: `PRODUCT#${item.productId}`,
          SK: `PRODUCT#${item.productId}`
        },
        UpdateExpression: 'SET Inventory = Inventory - :qty',
        ConditionExpression: 'Inventory >= :qty',
        ExpressionAttributeValues: {
          ':qty': item.quantity
        }
      }
    }))
  ];

  await client.send(new TransactWriteCommand({
    TransactItems: transactItems
  }));
};
```

## Advanced Patterns

### Adjacency List (Graph)

```javascript
// Social network: followers/following
// PK: USER#<userId>
// SK: FOLLOWS#<targetUserId> or FOLLOWER#<followerId>

// Follow user
const followUser = async (userId, targetUserId) => {
  await client.send(new TransactWriteCommand({
    TransactItems: [
      // User follows target
      {
        Put: {
          TableName: 'MyApp',
          Item: {
            PK: `USER#${userId}`,
            SK: `FOLLOWS#${targetUserId}`,
            Type: 'Following',
            TargetId: targetUserId,
            CreatedAt: new Date().toISOString()
          }
        }
      },
      // Target has follower
      {
        Put: {
          TableName: 'MyApp',
          Item: {
            PK: `USER#${targetUserId}`,
            SK: `FOLLOWER#${userId}`,
            Type: 'Follower',
            FollowerId: userId,
            CreatedAt: new Date().toISOString()
          }
        }
      },
      // Increment follower count
      {
        Update: {
          TableName: 'MyApp',
          Key: {
            PK: `USER#${targetUserId}`,
            SK: `USER#${targetUserId}`
          },
          UpdateExpression: 'ADD FollowerCount :one',
          ExpressionAttributeValues: {
            ':one': 1
          }
        }
      }
    ]
  }));
};

// Get following
const getFollowing = async (userId) => {
  const { Items } = await client.send(new QueryCommand({
    TableName: 'MyApp',
    KeyConditionExpression: 'PK = :pk AND begins_with(SK, :sk)',
    ExpressionAttributeValues: {
      ':pk': `USER#${userId}`,
      ':sk': 'FOLLOWS#'
    }
  }));
  return Items;
};
```

### Time-Series Data

```javascript
// IoT sensor readings with time-based partitioning
// PK: SENSOR#<sensorId>#<YYYY-MM-DD>
// SK: <ISO timestamp>

const addReading = async (sensorId, value) => {
  const now = new Date();
  const dateKey = now.toISOString().split('T')[0];

  await client.send(new PutCommand({
    TableName: 'MyApp',
    Item: {
      PK: `SENSOR#${sensorId}#${dateKey}`,
      SK: now.toISOString(),
      Type: 'Reading',
      SensorId: sensorId,
      Value: value
    }
  }));
};

// Get readings for time range
const getReadings = async (sensorId, startDate, endDate) => {
  const dateKey = startDate.toISOString().split('T')[0];

  const { Items } = await client.send(new QueryCommand({
    TableName: 'MyApp',
    KeyConditionExpression: 'PK = :pk AND SK BETWEEN :start AND :end',
    ExpressionAttributeValues: {
      ':pk': `SENSOR#${sensorId}#${dateKey}`,
      ':start': startDate.toISOString(),
      ':end': endDate.toISOString()
    }
  }));
  return Items;
};
```

### Hierarchical Data

```javascript
// Org chart with path enumeration
// PK: ORG#<orgId>
// SK: EMP#<path> where path = /ceo/vp-sales/manager1/emp1

const addEmployee = async (orgId, employee, managerPath) => {
  const path = managerPath ? `${managerPath}/${employee.id}` : `/${employee.id}`;

  await client.send(new PutCommand({
    TableName: 'MyApp',
    Item: {
      PK: `ORG#${orgId}`,
      SK: `EMP#${path}`,
      Type: 'Employee',
      Path: path,
      Depth: path.split('/').length - 1,
      ...employee
    }
  }));
};

// Get all reports (direct and indirect)
const getAllReports = async (orgId, managerPath) => {
  const { Items } = await client.send(new QueryCommand({
    TableName: 'MyApp',
    KeyConditionExpression: 'PK = :pk AND begins_with(SK, :sk)',
    ExpressionAttributeValues: {
      ':pk': `ORG#${orgId}`,
      ':sk': `EMP#${managerPath}/`
    }
  }));
  return Items;
};
```

## Best Practices

```javascript
// 1. Use consistent attribute names
const KEYS = {
  user: (id) => ({ PK: `USER#${id}`, SK: `USER#${id}` }),
  order: (userId, date, orderId) => ({
    PK: `USER#${userId}`,
    SK: `ORDER#${date}#${orderId}`
  })
};

// 2. Include entity type
{ Type: 'User', ... }
{ Type: 'Order', ... }

// 3. Use ISO timestamps for sorting
{ CreatedAt: new Date().toISOString() }

// 4. Handle pagination
const getAllOrders = async (userId, lastKey = null) => {
  const { Items, LastEvaluatedKey } = await client.send(new QueryCommand({
    TableName: 'MyApp',
    KeyConditionExpression: 'PK = :pk AND begins_with(SK, :sk)',
    ExpressionAttributeValues: {
      ':pk': `USER#${userId}`,
      ':sk': 'ORDER#'
    },
    Limit: 25,
    ExclusiveStartKey: lastKey
  }));

  return {
    items: Items,
    nextKey: LastEvaluatedKey
  };
};

// 5. Use sparse indexes
// Only items with GSI1PK attribute appear in GSI1
// Don't add GSI1PK to items that don't need the index
```
