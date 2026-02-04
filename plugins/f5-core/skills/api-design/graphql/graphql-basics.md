---
name: graphql-basics
description: GraphQL fundamentals and core concepts
category: api-design/graphql
applies_to: [all]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# GraphQL Basics

## Overview

GraphQL is a query language for APIs that enables clients to request exactly
the data they need. It provides a complete description of your API's data
and gives clients the power to ask for what they need.

## Core Concepts

```
┌─────────────────────────────────────────────────────────────────┐
│                    GraphQL Core Concepts                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Schema                                                          │
│  └── Type system that defines your API                          │
│                                                                  │
│  Types                                                           │
│  ├── Object types (User, Post, Order)                           │
│  ├── Scalar types (String, Int, Boolean, ID)                    │
│  ├── Enum types (Status, Role)                                  │
│  └── Input types (for mutations)                                │
│                                                                  │
│  Operations                                                      │
│  ├── Query - Read data                                          │
│  ├── Mutation - Write data                                      │
│  └── Subscription - Real-time updates                           │
│                                                                  │
│  Resolvers                                                       │
│  └── Functions that fetch data for each field                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## GraphQL vs REST

```
┌─────────────────────────────────────────────────────────────────┐
│                    GraphQL vs REST Comparison                    │
├────────────────┬────────────────────────────────────────────────┤
│ Aspect         │ REST                  │ GraphQL               │
├────────────────┼───────────────────────┼───────────────────────┤
│ Endpoints      │ Multiple              │ Single                │
│ Data fetching  │ Fixed structure       │ Client specifies      │
│ Over-fetching  │ Common                │ Avoided               │
│ Under-fetching │ Common (N+1)          │ Avoided               │
│ Versioning     │ URL/Header based      │ Schema evolution      │
│ Caching        │ HTTP caching          │ Client-side           │
│ Real-time      │ Separate (WebSocket)  │ Built-in subscriptions│
│ Tooling        │ Mature                │ Growing               │
└────────────────┴───────────────────────┴───────────────────────┘
```

## Basic Schema

```graphql
# schema.graphql

# Scalar types
scalar DateTime
scalar JSON

# Enum types
enum UserStatus {
  ACTIVE
  INACTIVE
  SUSPENDED
}

enum Role {
  USER
  ADMIN
  MODERATOR
}

# Object types
type User {
  id: ID!
  name: String!
  email: String!
  status: UserStatus!
  role: Role!
  profile: Profile
  posts: [Post!]!
  createdAt: DateTime!
  updatedAt: DateTime!
}

type Profile {
  id: ID!
  bio: String
  avatar: String
  website: String
  user: User!
}

type Post {
  id: ID!
  title: String!
  content: String!
  published: Boolean!
  author: User!
  comments: [Comment!]!
  tags: [String!]!
  createdAt: DateTime!
}

type Comment {
  id: ID!
  content: String!
  author: User!
  post: Post!
  createdAt: DateTime!
}

# Query type (read operations)
type Query {
  # Users
  user(id: ID!): User
  users(
    limit: Int = 20
    offset: Int = 0
    status: UserStatus
  ): [User!]!
  me: User

  # Posts
  post(id: ID!): Post
  posts(
    limit: Int = 20
    offset: Int = 0
    authorId: ID
    published: Boolean
  ): [Post!]!
}

# Mutation type (write operations)
type Mutation {
  # Users
  createUser(input: CreateUserInput!): User!
  updateUser(id: ID!, input: UpdateUserInput!): User!
  deleteUser(id: ID!): Boolean!

  # Posts
  createPost(input: CreatePostInput!): Post!
  updatePost(id: ID!, input: UpdatePostInput!): Post!
  deletePost(id: ID!): Boolean!
  publishPost(id: ID!): Post!
}

# Subscription type (real-time)
type Subscription {
  postCreated: Post!
  postUpdated(id: ID): Post!
  commentAdded(postId: ID!): Comment!
}

# Input types (for mutations)
input CreateUserInput {
  name: String!
  email: String!
  password: String!
  role: Role = USER
}

input UpdateUserInput {
  name: String
  email: String
  status: UserStatus
}

input CreatePostInput {
  title: String!
  content: String!
  published: Boolean = false
  tags: [String!]
}

input UpdatePostInput {
  title: String
  content: String
  tags: [String!]
}
```

## Query Examples

### Basic Query

```graphql
# Query a single user
query GetUser {
  user(id: "usr_123") {
    id
    name
    email
    status
  }
}

# Response
{
  "data": {
    "user": {
      "id": "usr_123",
      "name": "John Doe",
      "email": "john@example.com",
      "status": "ACTIVE"
    }
  }
}
```

### Nested Query

```graphql
# Query user with related data
query GetUserWithPosts {
  user(id: "usr_123") {
    id
    name
    profile {
      bio
      avatar
    }
    posts {
      id
      title
      published
      comments {
        id
        content
        author {
          name
        }
      }
    }
  }
}
```

### Query with Variables

```graphql
# Query definition
query GetUsers($limit: Int!, $status: UserStatus) {
  users(limit: $limit, status: $status) {
    id
    name
    email
    status
  }
}

# Variables
{
  "limit": 10,
  "status": "ACTIVE"
}
```

### Multiple Queries

```graphql
query GetDashboardData {
  me {
    id
    name
    role
  }
  recentPosts: posts(limit: 5) {
    id
    title
    createdAt
  }
  allUsers: users(limit: 10) {
    id
    name
  }
}
```

## Mutation Examples

### Create

```graphql
mutation CreateUser($input: CreateUserInput!) {
  createUser(input: $input) {
    id
    name
    email
    createdAt
  }
}

# Variables
{
  "input": {
    "name": "Jane Doe",
    "email": "jane@example.com",
    "password": "SecurePass123!"
  }
}

# Response
{
  "data": {
    "createUser": {
      "id": "usr_456",
      "name": "Jane Doe",
      "email": "jane@example.com",
      "createdAt": "2024-01-15T10:00:00Z"
    }
  }
}
```

### Update

```graphql
mutation UpdateUser($id: ID!, $input: UpdateUserInput!) {
  updateUser(id: $id, input: $input) {
    id
    name
    status
  }
}

# Variables
{
  "id": "usr_123",
  "input": {
    "name": "John Smith",
    "status": "INACTIVE"
  }
}
```

### Delete

```graphql
mutation DeleteUser($id: ID!) {
  deleteUser(id: $id)
}

# Variables
{
  "id": "usr_123"
}

# Response
{
  "data": {
    "deleteUser": true
  }
}
```

## Fragments

Reusable field selections.

```graphql
# Define fragment
fragment UserBasicInfo on User {
  id
  name
  email
  status
}

fragment PostSummary on Post {
  id
  title
  published
  createdAt
}

# Use fragments
query GetData {
  me {
    ...UserBasicInfo
    posts {
      ...PostSummary
    }
  }
  users(limit: 5) {
    ...UserBasicInfo
  }
}
```

### Inline Fragments

```graphql
# For union types or interfaces
query SearchResults {
  search(query: "graphql") {
    ... on User {
      id
      name
      email
    }
    ... on Post {
      id
      title
      author {
        name
      }
    }
    ... on Comment {
      id
      content
    }
  }
}
```

## Directives

Control execution behavior.

```graphql
# Built-in directives
query GetUser($includeProfile: Boolean!, $skipPosts: Boolean!) {
  user(id: "usr_123") {
    id
    name
    # Conditionally include
    profile @include(if: $includeProfile) {
      bio
      avatar
    }
    # Conditionally skip
    posts @skip(if: $skipPosts) {
      id
      title
    }
  }
}

# Variables
{
  "includeProfile": true,
  "skipPosts": false
}
```

### Custom Directives

```graphql
# Schema definition
directive @auth(requires: Role!) on FIELD_DEFINITION
directive @deprecated(reason: String) on FIELD_DEFINITION

type Query {
  publicData: String
  sensitiveData: String @auth(requires: ADMIN)
  oldField: String @deprecated(reason: "Use newField instead")
  newField: String
}
```

## Error Handling

```graphql
# Query that might fail
query GetUser {
  user(id: "invalid") {
    id
    name
  }
}

# Response with error
{
  "data": {
    "user": null
  },
  "errors": [
    {
      "message": "User not found",
      "locations": [{"line": 2, "column": 3}],
      "path": ["user"],
      "extensions": {
        "code": "NOT_FOUND",
        "timestamp": "2024-01-15T10:00:00Z"
      }
    }
  ]
}
```

### Partial Success

```graphql
# Query multiple resources
query GetData {
  user(id: "usr_123") {
    id
    name
  }
  post(id: "invalid") {
    id
    title
  }
}

# Response (partial success)
{
  "data": {
    "user": {
      "id": "usr_123",
      "name": "John Doe"
    },
    "post": null
  },
  "errors": [
    {
      "message": "Post not found",
      "path": ["post"]
    }
  ]
}
```

## Introspection

Query the schema itself.

```graphql
# Get all types
query IntrospectionQuery {
  __schema {
    types {
      name
      kind
      description
    }
  }
}

# Get type details
query TypeDetails {
  __type(name: "User") {
    name
    fields {
      name
      type {
        name
        kind
      }
    }
  }
}

# Get available queries
query AvailableQueries {
  __schema {
    queryType {
      fields {
        name
        args {
          name
          type {
            name
          }
        }
      }
    }
  }
}
```

## Client Implementation

### Using fetch

```typescript
async function graphqlRequest<T>(
  query: string,
  variables?: Record<string, any>
): Promise<T> {
  const response = await fetch('https://api.example.com/graphql', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${getToken()}`,
    },
    body: JSON.stringify({ query, variables }),
  });

  const result = await response.json();

  if (result.errors) {
    throw new GraphQLError(result.errors);
  }

  return result.data;
}

// Usage
const { user } = await graphqlRequest<{ user: User }>(`
  query GetUser($id: ID!) {
    user(id: $id) {
      id
      name
      email
    }
  }
`, { id: 'usr_123' });
```

### Using Apollo Client

```typescript
import { ApolloClient, InMemoryCache, gql } from '@apollo/client';

const client = new ApolloClient({
  uri: 'https://api.example.com/graphql',
  cache: new InMemoryCache(),
});

// Query
const GET_USER = gql`
  query GetUser($id: ID!) {
    user(id: $id) {
      id
      name
      email
    }
  }
`;

const { data } = await client.query({
  query: GET_USER,
  variables: { id: 'usr_123' },
});

// In React component
function UserProfile({ userId }) {
  const { loading, error, data } = useQuery(GET_USER, {
    variables: { id: userId },
  });

  if (loading) return <Loading />;
  if (error) return <Error message={error.message} />;

  return <div>{data.user.name}</div>;
}
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│                   GraphQL Best Practices                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Design Schema First                                         │
│     └── Think about use cases before implementation             │
│                                                                  │
│  2. Use Meaningful Names                                        │
│     ├── Types: PascalCase (User, Post)                         │
│     ├── Fields: camelCase (createdAt, firstName)               │
│     └── Enums: SCREAMING_SNAKE_CASE                            │
│                                                                  │
│  3. Make Fields Non-Nullable When Possible                      │
│     └── Use ! for required fields                               │
│                                                                  │
│  4. Use Input Types for Mutations                               │
│     └── CreateUserInput, UpdateUserInput                        │
│                                                                  │
│  5. Implement Pagination                                        │
│     └── Connection pattern for lists                            │
│                                                                  │
│  6. Handle Errors Properly                                      │
│     └── Use extensions for error codes                          │
│                                                                  │
│  7. Optimize with DataLoader                                    │
│     └── Solve N+1 problem                                       │
│                                                                  │
│  8. Limit Query Depth and Complexity                            │
│     └── Prevent abuse                                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```
