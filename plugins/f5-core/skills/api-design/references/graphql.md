# GraphQL Design Reference

## Core Concepts

### Schema Definition Language (SDL)

```graphql
type User {
  id: ID!
  name: String!
  email: String!
  status: UserStatus!
  posts: [Post!]!
  createdAt: DateTime!
}

enum UserStatus {
  ACTIVE
  INACTIVE
  SUSPENDED
}

type Post {
  id: ID!
  title: String!
  content: String!
  author: User!
  comments: [Comment!]!
  createdAt: DateTime!
}

type Query {
  user(id: ID!): User
  users(filter: UserFilter, first: Int, after: String): UserConnection!
  post(id: ID!): Post
}

type Mutation {
  createUser(input: CreateUserInput!): CreateUserPayload!
  updateUser(id: ID!, input: UpdateUserInput!): UpdateUserPayload!
  deleteUser(id: ID!): DeleteUserPayload!
}

type Subscription {
  postCreated: Post!
  userStatusChanged(userId: ID!): User!
}
```

### Input and Payload Types

```graphql
input CreateUserInput {
  name: String!
  email: String!
  password: String!
  role: UserRole
}

type CreateUserPayload {
  user: User
  errors: [Error!]
}

type Error {
  field: String
  code: String!
  message: String!
}

input UserFilter {
  status: [UserStatus!]
  role: UserRole
  searchTerm: String
}
```

## Queries

### Basic Queries

```graphql
# Simple query
query GetUser {
  user(id: "usr_123") {
    id
    name
    email
  }
}

# Query with variables
query GetUser($id: ID!) {
  user(id: $id) {
    id
    name
    email
    posts {
      id
      title
    }
  }
}

# Multiple queries in one request
query Dashboard($userId: ID!) {
  user(id: $userId) {
    name
    email
  }
  recentPosts: posts(first: 5) {
    edges {
      node {
        title
        createdAt
      }
    }
  }
}
```

### Fragments

```graphql
fragment UserBasic on User {
  id
  name
  email
}

fragment UserFull on User {
  ...UserBasic
  status
  role
  createdAt
  posts {
    id
    title
  }
}

query GetUsers {
  users(first: 10) {
    edges {
      node {
        ...UserFull
      }
    }
  }
}
```

### Directives

```graphql
query GetUser($id: ID!, $includeEmail: Boolean!, $skipPosts: Boolean!) {
  user(id: $id) {
    id
    name
    email @include(if: $includeEmail)
    posts @skip(if: $skipPosts) {
      title
    }
  }
}

# Custom directives
directive @auth(requires: Role!) on FIELD_DEFINITION
directive @deprecated(reason: String) on FIELD_DEFINITION

type Query {
  users: [User!]! @auth(requires: ADMIN)
  legacyField: String @deprecated(reason: "Use newField instead")
}
```

## Mutations

### Mutation Patterns

```graphql
mutation CreateUser($input: CreateUserInput!) {
  createUser(input: $input) {
    user {
      id
      name
      email
    }
    errors {
      field
      code
      message
    }
  }
}

mutation UpdateUser($id: ID!, $input: UpdateUserInput!) {
  updateUser(id: $id, input: $input) {
    user {
      id
      name
      status
    }
    errors {
      field
      code
      message
    }
  }
}

mutation DeleteUser($id: ID!) {
  deleteUser(id: $id) {
    deletedId
    errors {
      code
      message
    }
  }
}
```

### Mutation Response Pattern

```typescript
// Always return payload type, never throw for business errors
const resolvers = {
  Mutation: {
    createUser: async (_, { input }, context) => {
      // Validation
      const errors = validateInput(input);
      if (errors.length > 0) {
        return { user: null, errors };
      }

      // Check for existing user
      const existing = await context.db.users.findByEmail(input.email);
      if (existing) {
        return {
          user: null,
          errors: [{
            field: 'email',
            code: 'ALREADY_EXISTS',
            message: 'Email already registered',
          }],
        };
      }

      // Create user
      const user = await context.db.users.create(input);
      return { user, errors: [] };
    },
  },
};
```

## Subscriptions

### Subscription Schema

```graphql
type Subscription {
  postCreated: Post!
  postUpdated(id: ID!): Post!
  userOnlineStatusChanged: UserOnlineStatus!
}

type UserOnlineStatus {
  userId: ID!
  isOnline: Boolean!
  lastSeen: DateTime
}
```

### Subscription Implementation

```typescript
import { PubSub } from 'graphql-subscriptions';

const pubsub = new PubSub();

const resolvers = {
  Mutation: {
    createPost: async (_, { input }, context) => {
      const post = await context.db.posts.create(input);

      // Publish to subscribers
      pubsub.publish('POST_CREATED', { postCreated: post });

      return { post, errors: [] };
    },
  },

  Subscription: {
    postCreated: {
      subscribe: () => pubsub.asyncIterator(['POST_CREATED']),
    },

    postUpdated: {
      subscribe: (_, { id }) => ({
        [Symbol.asyncIterator]: () =>
          pubsub.asyncIterator([`POST_UPDATED_${id}`]),
      }),
    },
  },
};
```

## Pagination (Connections)

### Relay-Style Connections

```graphql
type UserConnection {
  edges: [UserEdge!]!
  pageInfo: PageInfo!
  totalCount: Int!
}

type UserEdge {
  node: User!
  cursor: String!
}

type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String
  endCursor: String
}

type Query {
  users(
    first: Int
    after: String
    last: Int
    before: String
    filter: UserFilter
  ): UserConnection!
}
```

### Connection Resolver

```typescript
async function resolveUserConnection(_, args, context) {
  const { first, after, last, before, filter } = args;

  // Decode cursor
  const afterCursor = after ? decodeCursor(after) : null;
  const beforeCursor = before ? decodeCursor(before) : null;

  // Build query
  let query = context.db.users;

  if (filter) {
    query = applyFilter(query, filter);
  }

  if (afterCursor) {
    query = query.where('id', '>', afterCursor.id);
  }

  // Fetch one extra to determine hasNextPage
  const limit = first || last || 20;
  const users = await query.limit(limit + 1).execute();

  const hasNextPage = users.length > limit;
  const nodes = users.slice(0, limit);

  return {
    edges: nodes.map((node) => ({
      node,
      cursor: encodeCursor({ id: node.id }),
    })),
    pageInfo: {
      hasNextPage,
      hasPreviousPage: !!afterCursor,
      startCursor: nodes[0] ? encodeCursor({ id: nodes[0].id }) : null,
      endCursor: nodes.length > 0
        ? encodeCursor({ id: nodes[nodes.length - 1].id })
        : null,
    },
    totalCount: await context.db.users.count(filter),
  };
}
```

## N+1 Problem and DataLoader

### The Problem

```graphql
query {
  users(first: 10) {
    edges {
      node {
        id
        name
        posts {  # N+1 queries!
          title
        }
      }
    }
  }
}
```

### DataLoader Solution

```typescript
import DataLoader from 'dataloader';

// Create loaders per request
function createLoaders(db) {
  return {
    users: new DataLoader(async (ids) => {
      const users = await db.users.findByIds(ids);
      // Return in same order as ids
      return ids.map((id) => users.find((u) => u.id === id));
    }),

    postsByUser: new DataLoader(async (userIds) => {
      const posts = await db.posts.findByUserIds(userIds);
      // Group by userId
      return userIds.map((userId) =>
        posts.filter((p) => p.userId === userId)
      );
    }),
  };
}

// Use in resolvers
const resolvers = {
  User: {
    posts: (user, _, { loaders }) => {
      return loaders.postsByUser.load(user.id);
    },
  },
};
```

## Error Handling

### Error Response Pattern

```graphql
type MutationPayload {
  success: Boolean!
  errors: [Error!]!
}

type Error {
  path: [String!]           # Field path
  code: ErrorCode!          # Machine-readable code
  message: String!          # Human-readable message
  extensions: JSONObject    # Additional context
}

enum ErrorCode {
  VALIDATION_ERROR
  NOT_FOUND
  UNAUTHORIZED
  FORBIDDEN
  CONFLICT
  INTERNAL_ERROR
}
```

### Throwing vs Returning Errors

```typescript
// ❌ Throwing - for unexpected errors only
throw new Error('Database connection failed');

// ✅ Returning - for business logic errors
return {
  user: null,
  errors: [{
    code: 'VALIDATION_ERROR',
    message: 'Email format is invalid',
    path: ['input', 'email'],
  }],
};
```

### Error Formatting

```typescript
import { GraphQLError } from 'graphql';

// Custom error with extensions
class AuthenticationError extends GraphQLError {
  constructor(message: string) {
    super(message, {
      extensions: {
        code: 'UNAUTHENTICATED',
        http: { status: 401 },
      },
    });
  }
}

// Error formatter
function formatError(error: GraphQLError) {
  // Log internal errors
  if (error.extensions?.code === 'INTERNAL_SERVER_ERROR') {
    console.error('Internal error:', error);
    return {
      message: 'An unexpected error occurred',
      extensions: { code: 'INTERNAL_ERROR' },
    };
  }

  return error;
}
```

## Schema Design Best Practices

### 1. Use Input Types for Mutations

```graphql
# ✅ Good
mutation CreateUser($input: CreateUserInput!) {
  createUser(input: $input) { ... }
}

# ❌ Avoid
mutation CreateUser($name: String!, $email: String!, $password: String!) {
  createUser(name: $name, email: $email, password: $password) { ... }
}
```

### 2. Return Payloads, Not Entities

```graphql
# ✅ Good
type CreateUserPayload {
  user: User
  errors: [Error!]!
}

# ❌ Avoid
type Mutation {
  createUser(input: CreateUserInput!): User!  # Can't return errors
}
```

### 3. Use Connections for Lists

```graphql
# ✅ Good - Supports pagination
users(first: Int, after: String): UserConnection!

# ❌ Avoid - No pagination info
users: [User!]!
```

### 4. Make IDs Opaque

```graphql
# ✅ Good - Client doesn't know internal format
type User {
  id: ID!  # Could be "VXNlcjoxMjM=" (base64)
}

# ❌ Avoid - Exposes internal details
type User {
  databaseId: Int!
}
```

### 5. Design for the Client

```graphql
# ✅ Good - Client-focused
type Query {
  viewer: User!           # Current authenticated user
  node(id: ID!): Node     # Refetch any node
}

# Instead of just:
type Query {
  user(id: ID!): User
}
```

## Performance Optimization

### Query Complexity Analysis

```typescript
import { createComplexityRule, simpleEstimator } from 'graphql-query-complexity';

const complexityRule = createComplexityRule({
  maximumComplexity: 1000,
  estimators: [
    simpleEstimator({ defaultComplexity: 1 }),
  ],
  onComplete: (complexity) => {
    console.log('Query complexity:', complexity);
  },
});
```

### Query Depth Limiting

```typescript
import depthLimit from 'graphql-depth-limit';

const server = new ApolloServer({
  schema,
  validationRules: [depthLimit(10)],
});
```

### Persisted Queries

```typescript
// Client sends hash instead of full query
const link = createPersistedQueryLink().concat(httpLink);

// Server validates against allowed queries
const server = new ApolloServer({
  persistedQueries: {
    cache: new RedisCache(),
  },
});
```
