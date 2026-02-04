---
name: schema-design
description: GraphQL schema design patterns and best practices
category: api-design/graphql
applies_to: [all]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# GraphQL Schema Design

## Overview

The schema is the contract between your API and clients. Good schema design
makes your API intuitive, efficient, and evolvable.

## Type System

### Scalar Types

```graphql
# Built-in scalars
type Example {
  id: ID!           # Unique identifier
  name: String!     # UTF-8 string
  age: Int          # 32-bit integer
  price: Float      # Double-precision float
  active: Boolean!  # true or false
}

# Custom scalars
scalar DateTime     # ISO 8601 date-time
scalar Date         # ISO 8601 date
scalar Time         # ISO 8601 time
scalar JSON         # Arbitrary JSON
scalar URL          # Valid URL
scalar Email        # Valid email address
scalar UUID         # UUID format
scalar BigInt       # Arbitrary precision integer
scalar Decimal      # Decimal number (for money)
```

### Custom Scalar Implementation

```typescript
import { GraphQLScalarType, Kind } from 'graphql';

export const DateTimeScalar = new GraphQLScalarType({
  name: 'DateTime',
  description: 'ISO 8601 date-time string',

  // Value sent to client
  serialize(value: Date): string {
    return value.toISOString();
  },

  // Value from client (variables)
  parseValue(value: string): Date {
    const date = new Date(value);
    if (isNaN(date.getTime())) {
      throw new Error('Invalid DateTime format');
    }
    return date;
  },

  // Value from client (inline)
  parseLiteral(ast): Date {
    if (ast.kind === Kind.STRING) {
      return new Date(ast.value);
    }
    throw new Error('DateTime must be a string');
  },
});

export const EmailScalar = new GraphQLScalarType({
  name: 'Email',
  description: 'Valid email address',

  serialize(value: string): string {
    return value;
  },

  parseValue(value: string): string {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(value)) {
      throw new Error('Invalid email format');
    }
    return value.toLowerCase();
  },

  parseLiteral(ast): string {
    if (ast.kind === Kind.STRING) {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(ast.value)) {
        throw new Error('Invalid email format');
      }
      return ast.value.toLowerCase();
    }
    throw new Error('Email must be a string');
  },
});
```

### Object Types

```graphql
# Basic object type
type User {
  id: ID!
  name: String!
  email: Email!
  createdAt: DateTime!
}

# With relationships
type User {
  id: ID!
  name: String!
  email: Email!

  # One-to-one
  profile: Profile

  # One-to-many
  posts: [Post!]!
  comments: [Comment!]!

  # Many-to-many
  followers: [User!]!
  following: [User!]!

  # Computed fields
  fullName: String!
  postCount: Int!
  isFollowedByMe: Boolean!
}
```

### Enum Types

```graphql
enum UserStatus {
  ACTIVE
  INACTIVE
  SUSPENDED
  DELETED
}

enum OrderStatus {
  PENDING
  CONFIRMED
  PROCESSING
  SHIPPED
  DELIVERED
  CANCELLED
  REFUNDED
}

enum SortDirection {
  ASC
  DESC
}

# Usage
type User {
  id: ID!
  status: UserStatus!
}

type Query {
  users(status: UserStatus, sortDirection: SortDirection): [User!]!
}
```

### Interface Types

```graphql
# Shared fields interface
interface Node {
  id: ID!
}

interface Timestamped {
  createdAt: DateTime!
  updatedAt: DateTime!
}

# Implementing interfaces
type User implements Node & Timestamped {
  id: ID!
  name: String!
  email: String!
  createdAt: DateTime!
  updatedAt: DateTime!
}

type Post implements Node & Timestamped {
  id: ID!
  title: String!
  content: String!
  createdAt: DateTime!
  updatedAt: DateTime!
}

# Query by interface
type Query {
  node(id: ID!): Node
  timestampedItems(after: DateTime!): [Timestamped!]!
}
```

### Union Types

```graphql
# Search results can be different types
union SearchResult = User | Post | Comment | Product

type Query {
  search(query: String!): [SearchResult!]!
}

# Client query
query Search {
  search(query: "graphql") {
    ... on User {
      id
      name
      email
    }
    ... on Post {
      id
      title
      author { name }
    }
    ... on Comment {
      id
      content
    }
    ... on Product {
      id
      name
      price
    }
  }
}
```

### Input Types

```graphql
# Input for creating
input CreateUserInput {
  name: String!
  email: Email!
  password: String!
  role: Role = USER
  profile: CreateProfileInput
}

input CreateProfileInput {
  bio: String
  avatar: URL
  website: URL
}

# Input for updating (all optional)
input UpdateUserInput {
  name: String
  email: Email
  status: UserStatus
  profile: UpdateProfileInput
}

input UpdateProfileInput {
  bio: String
  avatar: URL
  website: URL
}

# Input for filtering
input UserFilterInput {
  status: UserStatus
  role: Role
  createdAfter: DateTime
  createdBefore: DateTime
  search: String
}

# Input for pagination
input PaginationInput {
  first: Int
  after: String
  last: Int
  before: String
}

# Usage
type Mutation {
  createUser(input: CreateUserInput!): User!
  updateUser(id: ID!, input: UpdateUserInput!): User!
}

type Query {
  users(filter: UserFilterInput, pagination: PaginationInput): UserConnection!
}
```

## Relay Connection Pattern

Standard pattern for paginated lists.

```graphql
# Connection type
type UserConnection {
  edges: [UserEdge!]!
  pageInfo: PageInfo!
  totalCount: Int!
}

# Edge type
type UserEdge {
  node: User!
  cursor: String!
}

# Page info
type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String
  endCursor: String
}

# Query
type Query {
  users(
    first: Int
    after: String
    last: Int
    before: String
    filter: UserFilterInput
  ): UserConnection!
}

# Client usage
query GetUsers {
  users(first: 10, after: "cursor123") {
    edges {
      node {
        id
        name
        email
      }
      cursor
    }
    pageInfo {
      hasNextPage
      endCursor
    }
    totalCount
  }
}
```

### Connection Implementation

```typescript
interface ConnectionArgs {
  first?: number;
  after?: string;
  last?: number;
  before?: string;
}

interface Edge<T> {
  node: T;
  cursor: string;
}

interface Connection<T> {
  edges: Edge<T>[];
  pageInfo: {
    hasNextPage: boolean;
    hasPreviousPage: boolean;
    startCursor: string | null;
    endCursor: string | null;
  };
  totalCount: number;
}

function encodeCursor(id: string): string {
  return Buffer.from(`cursor:${id}`).toString('base64');
}

function decodeCursor(cursor: string): string {
  const decoded = Buffer.from(cursor, 'base64').toString('utf8');
  return decoded.replace('cursor:', '');
}

async function paginate<T extends { id: string }>(
  query: QueryBuilder,
  args: ConnectionArgs
): Promise<Connection<T>> {
  const { first, after, last, before } = args;

  // Determine pagination direction
  const isForward = first != null;
  const limit = first || last || 20;

  // Apply cursor
  if (after) {
    const id = decodeCursor(after);
    query = query.where('id', '>', id);
  }
  if (before) {
    const id = decodeCursor(before);
    query = query.where('id', '<', id);
  }

  // Fetch one extra to determine hasMore
  const items = await query
    .orderBy('id', isForward ? 'asc' : 'desc')
    .limit(limit + 1)
    .execute();

  const hasMore = items.length > limit;
  const nodes = items.slice(0, limit);

  if (!isForward) {
    nodes.reverse();
  }

  const totalCount = await query.count();

  return {
    edges: nodes.map(node => ({
      node,
      cursor: encodeCursor(node.id),
    })),
    pageInfo: {
      hasNextPage: isForward ? hasMore : !!before,
      hasPreviousPage: isForward ? !!after : hasMore,
      startCursor: nodes.length > 0 ? encodeCursor(nodes[0].id) : null,
      endCursor: nodes.length > 0 ? encodeCursor(nodes[nodes.length - 1].id) : null,
    },
    totalCount,
  };
}
```

## Naming Conventions

```
┌─────────────────────────────────────────────────────────────────┐
│                   GraphQL Naming Conventions                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Types (PascalCase)                                             │
│  ├── User, Post, OrderItem                                      │
│  ├── UserConnection, PostEdge                                   │
│  └── CreateUserInput, UpdatePostInput                           │
│                                                                  │
│  Fields (camelCase)                                             │
│  ├── id, name, email                                            │
│  ├── createdAt, updatedAt                                       │
│  └── firstName, lastName, postCount                             │
│                                                                  │
│  Enums (SCREAMING_SNAKE_CASE)                                   │
│  ├── ACTIVE, INACTIVE                                           │
│  └── PENDING_APPROVAL, IN_PROGRESS                              │
│                                                                  │
│  Arguments (camelCase)                                          │
│  ├── id, input, filter                                          │
│  └── first, after, orderBy                                      │
│                                                                  │
│  Mutations (verbNoun)                                           │
│  ├── createUser, updatePost, deleteComment                      │
│  └── publishArticle, approveOrder, sendNotification             │
│                                                                  │
│  Queries (noun or getNoun)                                      │
│  ├── user, users, post, posts                                   │
│  └── me, currentUser, viewer                                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Schema Organization

### Modular Schema

```
graphql/
├── schema.graphql          # Root schema
├── types/
│   ├── user.graphql
│   ├── post.graphql
│   ├── comment.graphql
│   └── common.graphql
├── queries/
│   ├── user.graphql
│   ├── post.graphql
│   └── search.graphql
├── mutations/
│   ├── user.graphql
│   ├── post.graphql
│   └── auth.graphql
└── subscriptions/
    ├── post.graphql
    └── notification.graphql
```

### Root Schema

```graphql
# schema.graphql
type Query {
  # User queries
  user(id: ID!): User
  users(filter: UserFilterInput, pagination: PaginationInput): UserConnection!
  me: User

  # Post queries
  post(id: ID!): Post
  posts(filter: PostFilterInput, pagination: PaginationInput): PostConnection!

  # Search
  search(query: String!, type: SearchType): [SearchResult!]!
}

type Mutation {
  # Auth
  login(email: String!, password: String!): AuthPayload!
  logout: Boolean!
  register(input: RegisterInput!): AuthPayload!

  # Users
  updateMe(input: UpdateUserInput!): User!
  updateUser(id: ID!, input: UpdateUserInput!): User!
  deleteUser(id: ID!): Boolean!

  # Posts
  createPost(input: CreatePostInput!): Post!
  updatePost(id: ID!, input: UpdatePostInput!): Post!
  deletePost(id: ID!): Boolean!
  publishPost(id: ID!): Post!
}

type Subscription {
  postCreated: Post!
  postUpdated: Post!
  notificationReceived: Notification!
}
```

## Nullability Guidelines

```graphql
# Non-null (!) means:
# - Field will always have a value
# - Error if resolver returns null

type User {
  id: ID!            # Always has ID
  name: String!      # Always has name
  email: String!     # Always has email
  bio: String        # Optional, may be null
  avatar: String     # Optional, may be null
  posts: [Post!]!    # Always returns array, no null items
  friends: [User!]   # May be null array, but no null items
  comments: [Comment]! # Always returns array, items may be null (rare)
}

# Input types
input CreateUserInput {
  name: String!           # Required
  email: String!          # Required
  bio: String             # Optional
  role: Role = USER       # Optional with default
}

input UpdateUserInput {
  name: String            # All optional for partial updates
  email: String
  bio: String
}
```

## Field Arguments

```graphql
type User {
  id: ID!
  name: String!

  # Paginated relationship
  posts(first: Int = 10, after: String): PostConnection!

  # Filtered relationship
  comments(
    postId: ID
    since: DateTime
    limit: Int = 20
  ): [Comment!]!

  # Formatted field
  createdAt(format: String = "ISO"): String!

  # Computed with arguments
  totalRevenue(
    startDate: DateTime
    endDate: DateTime
    currency: Currency = USD
  ): Money!
}

type Query {
  # Required argument
  user(id: ID!): User

  # Optional arguments with defaults
  users(
    filter: UserFilterInput
    orderBy: UserOrderBy = CREATED_AT_DESC
    first: Int = 20
    after: String
  ): UserConnection!

  # Enum argument
  postsByStatus(status: PostStatus!): [Post!]!
}
```

## Schema Documentation

```graphql
"""
Represents a user in the system.
Users can create posts, comments, and interact with other users.
"""
type User {
  "Unique identifier for the user"
  id: ID!

  "User's display name"
  name: String!

  """
  User's email address.
  Must be unique across all users.
  """
  email: Email!

  "User's account status"
  status: UserStatus!

  """
  Posts authored by this user.
  Returns paginated results ordered by creation date (newest first).
  """
  posts(
    "Maximum number of posts to return"
    first: Int = 10
    "Cursor for pagination"
    after: String
  ): PostConnection!

  "When the user account was created"
  createdAt: DateTime!
}

"""
Input for creating a new user.
All required fields must be provided.
"""
input CreateUserInput {
  "User's full name (2-100 characters)"
  name: String!

  "Valid email address (must be unique)"
  email: Email!

  "Password (minimum 8 characters, must contain number and special char)"
  password: String!
}
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│                Schema Design Best Practices                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Start with Use Cases                                        │
│     └── Design for how clients will use the API                 │
│                                                                  │
│  2. Be Explicit with Nullability                                │
│     └── Non-null by default, nullable when needed               │
│                                                                  │
│  3. Use Custom Scalars                                          │
│     └── DateTime, Email, URL for validation                     │
│                                                                  │
│  4. Implement Relay Connections                                 │
│     └── Standard pagination for lists                           │
│                                                                  │
│  5. Version Through Evolution                                   │
│     ├── Add fields (non-breaking)                               │
│     ├── Deprecate with @deprecated                              │
│     └── Remove after deprecation period                         │
│                                                                  │
│  6. Document Everything                                         │
│     └── Types, fields, arguments, enums                         │
│                                                                  │
│  7. Keep Types Focused                                          │
│     └── Single responsibility                                   │
│                                                                  │
│  8. Use Interfaces for Common Fields                            │
│     └── Node, Timestamped, etc.                                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```
