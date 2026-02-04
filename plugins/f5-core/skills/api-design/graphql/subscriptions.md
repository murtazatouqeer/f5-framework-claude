---
name: subscriptions
description: GraphQL subscriptions for real-time updates
category: api-design/graphql
applies_to: [all]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# GraphQL Subscriptions

## Overview

Subscriptions enable real-time data updates in GraphQL. Clients subscribe to
events and receive updates when relevant data changes on the server.

## How Subscriptions Work

```
┌─────────────────────────────────────────────────────────────────┐
│                   Subscription Flow                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Client sends subscription query                             │
│     subscription { postCreated { id title } }                   │
│                        │                                         │
│                        ▼                                         │
│  2. Server establishes WebSocket connection                     │
│     ←─────────────────────────────────────────→                 │
│     Client                                Server                 │
│                        │                                         │
│                        ▼                                         │
│  3. Server publishes event when data changes                    │
│     pubsub.publish('POST_CREATED', { postCreated: post })      │
│                        │                                         │
│                        ▼                                         │
│  4. Server sends data to subscribed clients                     │
│     { data: { postCreated: { id: "1", title: "New Post" } } }  │
│                        │                                         │
│                        ▼                                         │
│  5. Repeat step 4 for each new event                            │
│     (Connection stays open)                                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Basic Subscription Schema

```graphql
type Subscription {
  # Simple subscription
  postCreated: Post!

  # Filtered subscription
  postUpdated(postId: ID): Post!

  # Subscription with payload
  commentAdded(postId: ID!): CommentAddedPayload!

  # Notification subscription
  notificationReceived: Notification!

  # Status updates
  orderStatusChanged(orderId: ID!): Order!

  # Presence
  userPresenceChanged(channelId: ID!): UserPresence!
}

type CommentAddedPayload {
  comment: Comment!
  post: Post!
}

type UserPresence {
  user: User!
  status: PresenceStatus!
  lastSeen: DateTime
}

enum PresenceStatus {
  ONLINE
  AWAY
  OFFLINE
}
```

## Server Implementation

### PubSub Setup

```typescript
import { PubSub } from 'graphql-subscriptions';
import { RedisPubSub } from 'graphql-redis-subscriptions';
import Redis from 'ioredis';

// In-memory PubSub (development only)
const pubsub = new PubSub();

// Redis PubSub (production)
const options = {
  host: process.env.REDIS_HOST,
  port: parseInt(process.env.REDIS_PORT || '6379'),
  retryStrategy: (times: number) => Math.min(times * 50, 2000),
};

const redisPubsub = new RedisPubSub({
  publisher: new Redis(options),
  subscriber: new Redis(options),
});

// Event names
export const EVENTS = {
  POST_CREATED: 'POST_CREATED',
  POST_UPDATED: 'POST_UPDATED',
  COMMENT_ADDED: 'COMMENT_ADDED',
  NOTIFICATION: 'NOTIFICATION',
  ORDER_STATUS_CHANGED: 'ORDER_STATUS_CHANGED',
  USER_PRESENCE: 'USER_PRESENCE',
} as const;
```

### Subscription Resolvers

```typescript
import { withFilter } from 'graphql-subscriptions';

export const Subscription = {
  // Simple subscription - all events
  postCreated: {
    subscribe: () => pubsub.asyncIterator([EVENTS.POST_CREATED]),
  },

  // Filtered subscription - optional filter
  postUpdated: {
    subscribe: withFilter(
      () => pubsub.asyncIterator([EVENTS.POST_UPDATED]),
      (payload, variables) => {
        // If postId is provided, only send matching events
        if (variables.postId) {
          return payload.postUpdated.id === variables.postId;
        }
        // Otherwise, send all events
        return true;
      }
    ),
  },

  // Required filter
  commentAdded: {
    subscribe: withFilter(
      () => pubsub.asyncIterator([EVENTS.COMMENT_ADDED]),
      (payload, variables) => {
        return payload.commentAdded.post.id === variables.postId;
      }
    ),
    resolve: (payload) => payload.commentAdded,
  },

  // Authenticated subscription
  notificationReceived: {
    subscribe: withFilter(
      (_, __, context) => {
        // Check authentication
        if (!context.userId) {
          throw new AuthenticationError('Must be logged in');
        }
        return pubsub.asyncIterator([EVENTS.NOTIFICATION]);
      },
      (payload, _, context) => {
        // Only send to the target user
        return payload.notificationReceived.userId === context.userId;
      }
    ),
  },

  // Order status changes
  orderStatusChanged: {
    subscribe: withFilter(
      (_, { orderId }, context) => {
        if (!context.userId) {
          throw new AuthenticationError('Must be logged in');
        }
        return pubsub.asyncIterator([EVENTS.ORDER_STATUS_CHANGED]);
      },
      async (payload, { orderId }, context) => {
        // Verify user owns the order
        const order = payload.orderStatusChanged;
        if (order.id !== orderId) return false;
        return order.userId === context.userId || context.isAdmin;
      }
    ),
  },
};
```

### Publishing Events

```typescript
// In mutations
export const Mutation = {
  createPost: async (_, { input }, context) => {
    const post = await context.dataSources.posts.create({
      ...input,
      authorId: context.userId,
    });

    // Publish subscription event
    pubsub.publish(EVENTS.POST_CREATED, {
      postCreated: post,
    });

    return post;
  },

  updatePost: async (_, { id, input }, context) => {
    const post = await context.dataSources.posts.update(id, input);

    pubsub.publish(EVENTS.POST_UPDATED, {
      postUpdated: post,
    });

    return post;
  },

  addComment: async (_, { postId, input }, context) => {
    const comment = await context.dataSources.comments.create({
      ...input,
      postId,
      authorId: context.userId,
    });

    const post = await context.dataSources.posts.findById(postId);

    pubsub.publish(EVENTS.COMMENT_ADDED, {
      commentAdded: {
        comment,
        post,
      },
    });

    // Also notify post author
    if (post.authorId !== context.userId) {
      pubsub.publish(EVENTS.NOTIFICATION, {
        notificationReceived: {
          id: generateId(),
          userId: post.authorId,
          type: 'NEW_COMMENT',
          message: `${context.user.name} commented on your post`,
          data: { postId, commentId: comment.id },
          createdAt: new Date(),
        },
      });
    }

    return comment;
  },

  updateOrderStatus: async (_, { id, status }, context) => {
    const order = await context.dataSources.orders.update(id, { status });

    pubsub.publish(EVENTS.ORDER_STATUS_CHANGED, {
      orderStatusChanged: order,
    });

    // Notify user
    pubsub.publish(EVENTS.NOTIFICATION, {
      notificationReceived: {
        id: generateId(),
        userId: order.userId,
        type: 'ORDER_STATUS',
        message: `Your order #${id} is now ${status}`,
        data: { orderId: id, status },
        createdAt: new Date(),
      },
    });

    return order;
  },
};
```

## Apollo Server Setup

```typescript
import { ApolloServer } from 'apollo-server-express';
import { createServer } from 'http';
import { execute, subscribe } from 'graphql';
import { SubscriptionServer } from 'subscriptions-transport-ws';
import { makeExecutableSchema } from '@graphql-tools/schema';

// Create schema
const schema = makeExecutableSchema({ typeDefs, resolvers });

// Create HTTP server
const app = express();
const httpServer = createServer(app);

// Create subscription server
const subscriptionServer = SubscriptionServer.create(
  {
    schema,
    execute,
    subscribe,
    // Connection handling
    onConnect: async (connectionParams, webSocket, context) => {
      // Authenticate WebSocket connection
      const token = connectionParams.authToken;
      if (token) {
        try {
          const user = await verifyToken(token);
          return { userId: user.id, user };
        } catch (error) {
          throw new Error('Invalid token');
        }
      }
      return {};
    },
    onDisconnect: (webSocket, context) => {
      // Clean up on disconnect
      if (context.userId) {
        pubsub.publish(EVENTS.USER_PRESENCE, {
          userPresenceChanged: {
            userId: context.userId,
            status: 'OFFLINE',
            lastSeen: new Date(),
          },
        });
      }
    },
  },
  {
    server: httpServer,
    path: '/graphql',
  }
);

// Create Apollo Server
const server = new ApolloServer({
  schema,
  plugins: [
    {
      async serverWillStart() {
        return {
          async drainServer() {
            subscriptionServer.close();
          },
        };
      },
    },
  ],
  context: ({ req }) => ({
    userId: getUserFromRequest(req),
    dataSources: createDataSources(),
  }),
});

await server.start();
server.applyMiddleware({ app });

httpServer.listen(4000);
```

## Client Implementation

### Apollo Client

```typescript
import {
  ApolloClient,
  InMemoryCache,
  split,
  HttpLink,
} from '@apollo/client';
import { GraphQLWsLink } from '@apollo/client/link/subscriptions';
import { createClient } from 'graphql-ws';
import { getMainDefinition } from '@apollo/client/utilities';

// HTTP link for queries and mutations
const httpLink = new HttpLink({
  uri: 'http://localhost:4000/graphql',
  headers: {
    authorization: `Bearer ${getToken()}`,
  },
});

// WebSocket link for subscriptions
const wsLink = new GraphQLWsLink(
  createClient({
    url: 'ws://localhost:4000/graphql',
    connectionParams: {
      authToken: getToken(),
    },
  })
);

// Split based on operation type
const splitLink = split(
  ({ query }) => {
    const definition = getMainDefinition(query);
    return (
      definition.kind === 'OperationDefinition' &&
      definition.operation === 'subscription'
    );
  },
  wsLink,
  httpLink
);

const client = new ApolloClient({
  link: splitLink,
  cache: new InMemoryCache(),
});
```

### React Hook Usage

```typescript
import { useSubscription, gql } from '@apollo/client';

const POST_CREATED = gql`
  subscription PostCreated {
    postCreated {
      id
      title
      content
      author {
        id
        name
      }
      createdAt
    }
  }
`;

const COMMENT_ADDED = gql`
  subscription CommentAdded($postId: ID!) {
    commentAdded(postId: $postId) {
      comment {
        id
        content
        author {
          id
          name
        }
      }
      post {
        id
        commentCount
      }
    }
  }
`;

// In component
function PostFeed() {
  const { data, loading, error } = useSubscription(POST_CREATED);

  useEffect(() => {
    if (data?.postCreated) {
      // Add new post to feed
      console.log('New post:', data.postCreated);
    }
  }, [data]);

  return /* render feed */;
}

function PostComments({ postId }) {
  const { data } = useSubscription(COMMENT_ADDED, {
    variables: { postId },
  });

  useEffect(() => {
    if (data?.commentAdded) {
      // Add new comment to list
      console.log('New comment:', data.commentAdded.comment);
    }
  }, [data]);

  return /* render comments */;
}
```

### Updating Cache on Subscription

```typescript
import { useQuery, useSubscription, gql } from '@apollo/client';

const GET_POSTS = gql`
  query GetPosts {
    posts(first: 10) {
      edges {
        node {
          id
          title
        }
      }
    }
  }
`;

const POST_CREATED = gql`
  subscription PostCreated {
    postCreated {
      id
      title
    }
  }
`;

function PostList() {
  const { data: postsData } = useQuery(GET_POSTS);

  useSubscription(POST_CREATED, {
    onData: ({ client, data }) => {
      if (data.data?.postCreated) {
        // Update cache with new post
        client.cache.modify({
          fields: {
            posts(existingPosts = { edges: [] }) {
              const newPostRef = client.cache.writeFragment({
                data: data.data.postCreated,
                fragment: gql`
                  fragment NewPost on Post {
                    id
                    title
                  }
                `,
              });

              return {
                ...existingPosts,
                edges: [
                  { node: newPostRef, __typename: 'PostEdge' },
                  ...existingPosts.edges,
                ],
              };
            },
          },
        });
      }
    },
  });

  return /* render posts */;
}
```

## Advanced Patterns

### Presence System

```typescript
// Schema
type Subscription {
  userPresenceChanged(channelId: ID!): UserPresence!
}

type UserPresence {
  user: User!
  status: PresenceStatus!
  lastSeen: DateTime
}

// Resolver with heartbeat
const Subscription = {
  userPresenceChanged: {
    subscribe: async function* (_, { channelId }, context) {
      // Check authorization
      const canAccess = await context.dataSources.channels.canAccess(
        context.userId,
        channelId
      );
      if (!canAccess) {
        throw new ForbiddenError('Cannot access this channel');
      }

      // Mark user as online
      await context.dataSources.presence.setOnline(context.userId, channelId);

      // Send initial presence list
      const onlineUsers = await context.dataSources.presence.getOnline(channelId);
      for (const presence of onlineUsers) {
        yield { userPresenceChanged: presence };
      }

      // Subscribe to changes
      const iterator = pubsub.asyncIterator([EVENTS.USER_PRESENCE]);

      try {
        for await (const event of iterator) {
          if (event.userPresenceChanged.channelId === channelId) {
            yield event;
          }
        }
      } finally {
        // Mark user as offline when subscription ends
        await context.dataSources.presence.setOffline(context.userId, channelId);
      }
    },
  },
};
```

### Live Queries Pattern

```typescript
// Schema
type Query {
  livePost(id: ID!): Post @live
}

// Implementation using subscriptions
const Subscription = {
  livePost: {
    subscribe: async function* (_, { id }, context) {
      // Send initial data
      const post = await context.dataSources.posts.findById(id);
      yield { livePost: post };

      // Subscribe to updates
      const iterator = pubsub.asyncIterator([EVENTS.POST_UPDATED]);

      for await (const event of iterator) {
        if (event.postUpdated.id === id) {
          yield { livePost: event.postUpdated };
        }
      }
    },
  },
};
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│                Subscription Best Practices                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Use Redis PubSub in Production                              │
│     └── In-memory PubSub doesn't scale                          │
│                                                                  │
│  2. Authenticate Connections                                    │
│     └── Validate token in onConnect                             │
│                                                                  │
│  3. Filter Events Server-Side                                   │
│     └── Don't send unnecessary data to clients                  │
│                                                                  │
│  4. Handle Reconnection                                         │
│     └── Clients should reconnect and resubscribe                │
│                                                                  │
│  5. Limit Subscription Scope                                    │
│     └── Require specific IDs when possible                      │
│                                                                  │
│  6. Consider Rate Limiting                                      │
│     └── Throttle high-frequency events                          │
│                                                                  │
│  7. Clean Up on Disconnect                                      │
│     └── Release resources, update presence                      │
│                                                                  │
│  8. Monitor Connection Health                                   │
│     └── Track active subscriptions and errors                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```
