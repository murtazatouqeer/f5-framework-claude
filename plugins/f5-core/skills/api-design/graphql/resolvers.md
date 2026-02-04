---
name: resolvers
description: GraphQL resolver patterns and implementation
category: api-design/graphql
applies_to: [all]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# GraphQL Resolvers

## Overview

Resolvers are functions that return data for GraphQL fields. They form the
bridge between your schema and your data sources.

## Resolver Signature

```typescript
// Standard resolver signature
type Resolver<TParent, TArgs, TContext, TResult> = (
  parent: TParent,      // Result from parent resolver
  args: TArgs,          // Arguments passed to field
  context: TContext,    // Shared context (auth, dataloaders, etc.)
  info: GraphQLResolveInfo  // Query information
) => TResult | Promise<TResult>;

// Example
const userResolver: Resolver<any, { id: string }, Context, User> = async (
  parent,
  args,
  context,
  info
) => {
  return context.dataSources.users.findById(args.id);
};
```

## Basic Resolvers

### Query Resolvers

```typescript
// resolvers/query.ts
import { QueryResolvers } from '../generated/graphql';

export const Query: QueryResolvers = {
  // Simple query
  user: async (_, { id }, context) => {
    return context.dataSources.users.findById(id);
  },

  // Query with filtering and pagination
  users: async (_, { filter, pagination }, context) => {
    const { first = 20, after } = pagination || {};
    const { status, role, search } = filter || {};

    return context.dataSources.users.findMany({
      where: { status, role },
      search,
      first,
      after,
    });
  },

  // Authenticated query
  me: async (_, __, context) => {
    if (!context.userId) {
      return null;
    }
    return context.dataSources.users.findById(context.userId);
  },

  // Search across types
  search: async (_, { query, type }, context) => {
    const results = [];

    if (!type || type === 'USER') {
      const users = await context.dataSources.users.search(query);
      results.push(...users.map(u => ({ ...u, __typename: 'User' })));
    }

    if (!type || type === 'POST') {
      const posts = await context.dataSources.posts.search(query);
      results.push(...posts.map(p => ({ ...p, __typename: 'Post' })));
    }

    return results;
  },
};
```

### Mutation Resolvers

```typescript
// resolvers/mutation.ts
import { MutationResolvers } from '../generated/graphql';
import { AuthenticationError, UserInputError } from 'apollo-server';

export const Mutation: MutationResolvers = {
  createUser: async (_, { input }, context) => {
    // Validate input
    const existingUser = await context.dataSources.users.findByEmail(input.email);
    if (existingUser) {
      throw new UserInputError('Email already registered', {
        field: 'email',
      });
    }

    // Hash password
    const hashedPassword = await hashPassword(input.password);

    // Create user
    const user = await context.dataSources.users.create({
      ...input,
      password: hashedPassword,
    });

    return user;
  },

  updateUser: async (_, { id, input }, context) => {
    // Check authorization
    if (context.userId !== id && !context.isAdmin) {
      throw new AuthenticationError('Not authorized to update this user');
    }

    const user = await context.dataSources.users.update(id, input);
    if (!user) {
      throw new UserInputError('User not found');
    }

    return user;
  },

  deleteUser: async (_, { id }, context) => {
    // Admin only
    if (!context.isAdmin) {
      throw new AuthenticationError('Admin access required');
    }

    const deleted = await context.dataSources.users.delete(id);
    return deleted;
  },

  createPost: async (_, { input }, context) => {
    if (!context.userId) {
      throw new AuthenticationError('Must be logged in to create posts');
    }

    const post = await context.dataSources.posts.create({
      ...input,
      authorId: context.userId,
    });

    // Publish subscription event
    context.pubsub.publish('POST_CREATED', { postCreated: post });

    return post;
  },
};
```

### Type Resolvers

```typescript
// resolvers/user.ts
import { UserResolvers } from '../generated/graphql';

export const User: UserResolvers = {
  // Resolve related profile
  profile: async (user, _, context) => {
    return context.dataSources.profiles.findByUserId(user.id);
  },

  // Resolve related posts with pagination
  posts: async (user, { first, after }, context) => {
    return context.dataSources.posts.findByAuthor(user.id, { first, after });
  },

  // Computed field
  fullName: (user) => {
    return `${user.firstName} ${user.lastName}`;
  },

  // Computed field with context
  postCount: async (user, _, context) => {
    return context.dataSources.posts.countByAuthor(user.id);
  },

  // Field requiring authentication
  email: (user, _, context) => {
    // Only show email to self or admin
    if (context.userId === user.id || context.isAdmin) {
      return user.email;
    }
    return null;
  },

  // Field with arguments
  isFollowedByMe: async (user, _, context) => {
    if (!context.userId) return false;
    return context.dataSources.follows.exists(context.userId, user.id);
  },
};
```

## N+1 Problem and DataLoader

### The Problem

```graphql
# This query causes N+1 database calls
query {
  posts(first: 10) {
    edges {
      node {
        id
        title
        author {        # 1 query per post = 10 extra queries
          id
          name
        }
      }
    }
  }
}
```

### DataLoader Solution

```typescript
// dataloaders/index.ts
import DataLoader from 'dataloader';
import { User, Post } from '../models';

export function createLoaders(db: Database) {
  return {
    // Batch load users by ID
    userLoader: new DataLoader<string, User>(async (ids) => {
      const users = await db.users.findMany({
        where: { id: { in: ids as string[] } },
      });

      // Return in same order as requested ids
      const userMap = new Map(users.map(u => [u.id, u]));
      return ids.map(id => userMap.get(id) || null);
    }),

    // Batch load posts by author ID
    postsByAuthorLoader: new DataLoader<string, Post[]>(async (authorIds) => {
      const posts = await db.posts.findMany({
        where: { authorId: { in: authorIds as string[] } },
      });

      // Group by author ID
      const postsByAuthor = new Map<string, Post[]>();
      for (const post of posts) {
        const existing = postsByAuthor.get(post.authorId) || [];
        existing.push(post);
        postsByAuthor.set(post.authorId, existing);
      }

      return authorIds.map(id => postsByAuthor.get(id) || []);
    }),

    // With caching options
    userByEmailLoader: new DataLoader<string, User>(
      async (emails) => {
        const users = await db.users.findMany({
          where: { email: { in: emails as string[] } },
        });
        const userMap = new Map(users.map(u => [u.email, u]));
        return emails.map(email => userMap.get(email) || null);
      },
      {
        cache: true,        // Enable caching (default)
        maxBatchSize: 100,  // Limit batch size
      }
    ),
  };
}

// Context setup
interface Context {
  userId: string | null;
  loaders: ReturnType<typeof createLoaders>;
}

const server = new ApolloServer({
  typeDefs,
  resolvers,
  context: ({ req }): Context => ({
    userId: getUserFromToken(req.headers.authorization),
    loaders: createLoaders(db),  // New loaders per request
  }),
});

// Usage in resolver
export const Post: PostResolvers = {
  author: (post, _, context) => {
    return context.loaders.userLoader.load(post.authorId);
  },
};

export const User: UserResolvers = {
  posts: (user, _, context) => {
    return context.loaders.postsByAuthorLoader.load(user.id);
  },
};
```

### Advanced DataLoader Patterns

```typescript
// Loader with arguments (cache key function)
const postsLoader = new DataLoader<
  { authorId: string; status?: PostStatus },
  Post[]
>(
  async (keys) => {
    // Group by unique combinations
    const posts = await db.posts.findMany({
      where: {
        OR: keys.map(k => ({
          authorId: k.authorId,
          ...(k.status && { status: k.status }),
        })),
      },
    });

    // Match back to keys
    return keys.map(key =>
      posts.filter(
        p => p.authorId === key.authorId &&
             (!key.status || p.status === key.status)
      )
    );
  },
  {
    // Custom cache key for objects
    cacheKeyFn: (key) => `${key.authorId}:${key.status || 'all'}`,
  }
);

// Clearing cache
context.loaders.userLoader.clear(userId);     // Clear specific
context.loaders.userLoader.clearAll();        // Clear all

// Priming cache
const user = await db.users.create(data);
context.loaders.userLoader.prime(user.id, user);
```

## Error Handling

```typescript
import {
  ApolloError,
  AuthenticationError,
  ForbiddenError,
  UserInputError,
} from 'apollo-server';

// Custom error classes
export class NotFoundError extends ApolloError {
  constructor(resource: string, id: string) {
    super(`${resource} with ID '${id}' not found`, 'NOT_FOUND', {
      resource,
      id,
    });
  }
}

export class ValidationError extends ApolloError {
  constructor(errors: Array<{ field: string; message: string }>) {
    super('Validation failed', 'VALIDATION_ERROR', { errors });
  }
}

// Usage in resolvers
export const Query: QueryResolvers = {
  user: async (_, { id }, context) => {
    const user = await context.dataSources.users.findById(id);
    if (!user) {
      throw new NotFoundError('User', id);
    }
    return user;
  },
};

export const Mutation: MutationResolvers = {
  createUser: async (_, { input }, context) => {
    // Validation
    const errors: Array<{ field: string; message: string }> = [];

    if (input.name.length < 2) {
      errors.push({ field: 'name', message: 'Name must be at least 2 characters' });
    }

    if (!isValidEmail(input.email)) {
      errors.push({ field: 'email', message: 'Invalid email format' });
    }

    if (errors.length > 0) {
      throw new ValidationError(errors);
    }

    // Check uniqueness
    const existing = await context.dataSources.users.findByEmail(input.email);
    if (existing) {
      throw new UserInputError('Email already registered', {
        field: 'email',
      });
    }

    return context.dataSources.users.create(input);
  },

  updatePost: async (_, { id, input }, context) => {
    // Authentication
    if (!context.userId) {
      throw new AuthenticationError('Must be logged in');
    }

    const post = await context.dataSources.posts.findById(id);
    if (!post) {
      throw new NotFoundError('Post', id);
    }

    // Authorization
    if (post.authorId !== context.userId && !context.isAdmin) {
      throw new ForbiddenError('Not authorized to edit this post');
    }

    return context.dataSources.posts.update(id, input);
  },
};

// Error formatting
const server = new ApolloServer({
  typeDefs,
  resolvers,
  formatError: (error) => {
    // Log internal errors
    if (error.extensions?.code === 'INTERNAL_SERVER_ERROR') {
      console.error('Internal error:', error.originalError);

      // Don't expose internal details to client
      return {
        message: 'An unexpected error occurred',
        extensions: {
          code: 'INTERNAL_SERVER_ERROR',
        },
      };
    }

    return error;
  },
});
```

## Middleware and Field-Level Auth

```typescript
import { shield, rule, and, or, not } from 'graphql-shield';

// Define rules
const isAuthenticated = rule({ cache: 'contextual' })(
  async (parent, args, context) => {
    return context.userId !== null;
  }
);

const isAdmin = rule({ cache: 'contextual' })(
  async (parent, args, context) => {
    return context.isAdmin === true;
  }
);

const isOwner = rule({ cache: 'strict' })(
  async (parent, args, context) => {
    return parent.authorId === context.userId;
  }
);

// Build permissions
const permissions = shield({
  Query: {
    users: isAdmin,
    me: isAuthenticated,
  },
  Mutation: {
    createPost: isAuthenticated,
    updatePost: and(isAuthenticated, or(isOwner, isAdmin)),
    deletePost: and(isAuthenticated, or(isOwner, isAdmin)),
    deleteUser: isAdmin,
  },
  User: {
    email: or(isOwner, isAdmin),
  },
}, {
  allowExternalErrors: true,
  fallbackError: new AuthenticationError('Not authorized'),
});

// Apply to schema
import { applyMiddleware } from 'graphql-middleware';

const schemaWithPermissions = applyMiddleware(schema, permissions);
```

## Subscription Resolvers

```typescript
import { PubSub, withFilter } from 'graphql-subscriptions';

const pubsub = new PubSub();

export const Subscription = {
  postCreated: {
    subscribe: () => pubsub.asyncIterator(['POST_CREATED']),
  },

  // Filtered subscription
  postUpdated: {
    subscribe: withFilter(
      () => pubsub.asyncIterator(['POST_UPDATED']),
      (payload, variables) => {
        // Only send to subscribers of this specific post
        return variables.postId
          ? payload.postUpdated.id === variables.postId
          : true;
      }
    ),
  },

  // With authentication
  notificationReceived: {
    subscribe: withFilter(
      (_, __, context) => {
        if (!context.userId) {
          throw new AuthenticationError('Must be logged in');
        }
        return pubsub.asyncIterator(['NOTIFICATION']);
      },
      (payload, _, context) => {
        // Only send to the target user
        return payload.notificationReceived.userId === context.userId;
      }
    ),
  },
};

// Publishing from mutations
export const Mutation = {
  createPost: async (_, { input }, context) => {
    const post = await context.dataSources.posts.create(input);

    pubsub.publish('POST_CREATED', { postCreated: post });

    return post;
  },
};
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│                   Resolver Best Practices                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Use DataLoader for Related Data                             │
│     └── Prevent N+1 queries                                     │
│                                                                  │
│  2. Keep Resolvers Thin                                         │
│     └── Move business logic to services                         │
│                                                                  │
│  3. Handle Errors Explicitly                                    │
│     └── Use typed errors with codes                             │
│                                                                  │
│  4. Implement Authorization Consistently                        │
│     └── Use middleware like graphql-shield                      │
│                                                                  │
│  5. Return Null for Optional Fields                             │
│     └── Throw errors for required fields                        │
│                                                                  │
│  6. Type Your Resolvers                                         │
│     └── Use generated types from schema                         │
│                                                                  │
│  7. Log Performance Metrics                                     │
│     └── Track resolver execution time                           │
│                                                                  │
│  8. Test Resolvers Independently                                │
│     └── Mock context and data sources                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```
