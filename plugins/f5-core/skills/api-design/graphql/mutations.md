---
name: mutations
description: GraphQL mutation design patterns
category: api-design/graphql
applies_to: [all]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# GraphQL Mutations

## Overview

Mutations are GraphQL operations that modify server-side data. Well-designed
mutations are predictable, provide useful feedback, and handle errors gracefully.

## Mutation Design Principles

```
┌─────────────────────────────────────────────────────────────────┐
│                  Mutation Design Principles                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Specific Over Generic                                       │
│     └── createUser, not saveEntity                              │
│                                                                  │
│  2. Return Modified Data                                        │
│     └── Return the created/updated object                       │
│                                                                  │
│  3. Use Input Types                                             │
│     └── Single input argument for clarity                       │
│                                                                  │
│  4. Return Payload Types                                        │
│     └── Include errors, success state, data                     │
│                                                                  │
│  5. Make Side Effects Explicit                                  │
│     └── Name mutations by their action                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Basic Mutation Patterns

### Simple CRUD Mutations

```graphql
type Mutation {
  # Create
  createUser(input: CreateUserInput!): User!
  createPost(input: CreatePostInput!): Post!

  # Update
  updateUser(id: ID!, input: UpdateUserInput!): User!
  updatePost(id: ID!, input: UpdatePostInput!): Post!

  # Delete
  deleteUser(id: ID!): Boolean!
  deletePost(id: ID!): Boolean!
}

input CreateUserInput {
  name: String!
  email: String!
  password: String!
  role: Role = USER
}

input UpdateUserInput {
  name: String
  email: String
  role: Role
}

input CreatePostInput {
  title: String!
  content: String!
  tags: [String!]
  published: Boolean = false
}

input UpdatePostInput {
  title: String
  content: String
  tags: [String!]
}
```

### Action-Based Mutations

```graphql
type Mutation {
  # User actions
  activateUser(id: ID!): User!
  deactivateUser(id: ID!): User!
  suspendUser(id: ID!, reason: String!): User!
  verifyEmail(token: String!): User!
  resetPassword(token: String!, newPassword: String!): Boolean!

  # Post actions
  publishPost(id: ID!): Post!
  unpublishPost(id: ID!): Post!
  archivePost(id: ID!): Post!

  # Order actions
  confirmOrder(id: ID!): Order!
  cancelOrder(id: ID!, reason: String): Order!
  refundOrder(id: ID!, amount: Float): Order!
  shipOrder(id: ID!, trackingNumber: String!): Order!

  # Social actions
  followUser(userId: ID!): User!
  unfollowUser(userId: ID!): User!
  likePost(postId: ID!): Post!
  unlikePost(postId: ID!): Post!
}
```

## Mutation Payload Pattern

Return a payload type instead of just the entity.

```graphql
# Payload type
type CreateUserPayload {
  success: Boolean!
  user: User
  errors: [Error!]!
}

type UpdateUserPayload {
  success: Boolean!
  user: User
  errors: [Error!]!
}

type DeleteUserPayload {
  success: Boolean!
  deletedId: ID
  errors: [Error!]!
}

type Error {
  field: String
  code: String!
  message: String!
}

type Mutation {
  createUser(input: CreateUserInput!): CreateUserPayload!
  updateUser(id: ID!, input: UpdateUserInput!): UpdateUserPayload!
  deleteUser(id: ID!): DeleteUserPayload!
}

# Usage
mutation CreateUser($input: CreateUserInput!) {
  createUser(input: $input) {
    success
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

# Response - success
{
  "data": {
    "createUser": {
      "success": true,
      "user": {
        "id": "usr_123",
        "name": "John Doe",
        "email": "john@example.com"
      },
      "errors": []
    }
  }
}

# Response - validation error
{
  "data": {
    "createUser": {
      "success": false,
      "user": null,
      "errors": [
        {
          "field": "email",
          "code": "ALREADY_EXISTS",
          "message": "This email is already registered"
        }
      ]
    }
  }
}
```

### Payload Implementation

```typescript
// types
interface MutationPayload<T> {
  success: boolean;
  data: T | null;
  errors: Error[];
}

interface Error {
  field?: string;
  code: string;
  message: string;
}

// Helper functions
function successPayload<T>(data: T): MutationPayload<T> {
  return { success: true, data, errors: [] };
}

function errorPayload<T>(errors: Error[]): MutationPayload<T> {
  return { success: false, data: null, errors };
}

function validationError(field: string, code: string, message: string): Error {
  return { field, code, message };
}

// Resolver
const Mutation = {
  createUser: async (_, { input }, context): Promise<MutationPayload<User>> => {
    // Validation
    const errors: Error[] = [];

    if (input.name.length < 2) {
      errors.push(validationError('name', 'TOO_SHORT', 'Name must be at least 2 characters'));
    }

    if (!isValidEmail(input.email)) {
      errors.push(validationError('email', 'INVALID_FORMAT', 'Invalid email format'));
    }

    if (errors.length > 0) {
      return errorPayload(errors);
    }

    // Check uniqueness
    const existing = await context.dataSources.users.findByEmail(input.email);
    if (existing) {
      return errorPayload([
        validationError('email', 'ALREADY_EXISTS', 'Email already registered')
      ]);
    }

    // Create user
    try {
      const user = await context.dataSources.users.create(input);
      return successPayload(user);
    } catch (error) {
      return errorPayload([
        { code: 'INTERNAL_ERROR', message: 'Failed to create user' }
      ]);
    }
  },
};
```

## Bulk Mutations

```graphql
# Input types
input BulkCreateUsersInput {
  users: [CreateUserInput!]!
}

input BulkUpdateUsersInput {
  updates: [UserUpdateItem!]!
}

input UserUpdateItem {
  id: ID!
  data: UpdateUserInput!
}

input BulkDeleteInput {
  ids: [ID!]!
}

# Payload types
type BulkCreateUsersPayload {
  success: Boolean!
  users: [User!]!
  errors: [BulkError!]!
  totalCreated: Int!
  totalFailed: Int!
}

type BulkUpdateUsersPayload {
  success: Boolean!
  users: [User!]!
  errors: [BulkError!]!
  totalUpdated: Int!
  totalFailed: Int!
}

type BulkDeletePayload {
  success: Boolean!
  deletedIds: [ID!]!
  errors: [BulkError!]!
  totalDeleted: Int!
  totalFailed: Int!
}

type BulkError {
  index: Int
  id: ID
  field: String
  code: String!
  message: String!
}

type Mutation {
  bulkCreateUsers(input: BulkCreateUsersInput!): BulkCreateUsersPayload!
  bulkUpdateUsers(input: BulkUpdateUsersInput!): BulkUpdateUsersPayload!
  bulkDeleteUsers(input: BulkDeleteInput!): BulkDeletePayload!
}
```

### Bulk Mutation Implementation

```typescript
const Mutation = {
  bulkCreateUsers: async (_, { input }, context) => {
    const users: User[] = [];
    const errors: BulkError[] = [];

    // Process in parallel with limit
    const results = await Promise.allSettled(
      input.users.map(async (userData, index) => {
        // Validate
        const validationErrors = validateUserInput(userData);
        if (validationErrors.length > 0) {
          throw { index, errors: validationErrors };
        }

        // Check uniqueness
        const existing = await context.dataSources.users.findByEmail(userData.email);
        if (existing) {
          throw {
            index,
            errors: [{ field: 'email', code: 'ALREADY_EXISTS', message: 'Email exists' }]
          };
        }

        return context.dataSources.users.create(userData);
      })
    );

    // Collect results
    results.forEach((result, index) => {
      if (result.status === 'fulfilled') {
        users.push(result.value);
      } else {
        const error = result.reason;
        if (error.errors) {
          error.errors.forEach((e: Error) => {
            errors.push({ index, ...e });
          });
        } else {
          errors.push({
            index,
            code: 'UNKNOWN_ERROR',
            message: error.message || 'Unknown error'
          });
        }
      }
    });

    return {
      success: errors.length === 0,
      users,
      errors,
      totalCreated: users.length,
      totalFailed: errors.length,
    };
  },

  bulkDeleteUsers: async (_, { input }, context) => {
    const deletedIds: string[] = [];
    const errors: BulkError[] = [];

    await Promise.all(
      input.ids.map(async (id) => {
        try {
          const deleted = await context.dataSources.users.delete(id);
          if (deleted) {
            deletedIds.push(id);
          } else {
            errors.push({
              id,
              code: 'NOT_FOUND',
              message: `User ${id} not found`
            });
          }
        } catch (error) {
          errors.push({
            id,
            code: 'DELETE_FAILED',
            message: error.message
          });
        }
      })
    );

    return {
      success: errors.length === 0,
      deletedIds,
      errors,
      totalDeleted: deletedIds.length,
      totalFailed: errors.length,
    };
  },
};
```

## Optimistic Locking

```graphql
input UpdatePostInput {
  title: String
  content: String
  version: Int!  # Required for optimistic locking
}

type UpdatePostPayload {
  success: Boolean!
  post: Post
  errors: [Error!]!
}

type Error {
  code: String!
  message: String!
}
```

### Implementation

```typescript
const Mutation = {
  updatePost: async (_, { id, input }, context) => {
    const { version, ...data } = input;

    // Check version
    const current = await context.dataSources.posts.findById(id);
    if (!current) {
      return errorPayload([{ code: 'NOT_FOUND', message: 'Post not found' }]);
    }

    if (current.version !== version) {
      return errorPayload([{
        code: 'CONFLICT',
        message: 'Post has been modified. Please refresh and try again.'
      }]);
    }

    // Update with version increment
    const updated = await context.dataSources.posts.update(id, {
      ...data,
      version: version + 1,
    });

    return successPayload(updated);
  },
};
```

## File Upload Mutations

```graphql
scalar Upload

input UploadFileInput {
  file: Upload!
  description: String
}

type File {
  id: ID!
  filename: String!
  mimetype: String!
  size: Int!
  url: String!
  description: String
  uploadedAt: DateTime!
}

type UploadFilePayload {
  success: Boolean!
  file: File
  errors: [Error!]!
}

type Mutation {
  uploadFile(input: UploadFileInput!): UploadFilePayload!
  uploadAvatar(file: Upload!): User!
  uploadPostImages(postId: ID!, files: [Upload!]!): Post!
}
```

### Implementation

```typescript
import { GraphQLUpload } from 'graphql-upload';

const resolvers = {
  Upload: GraphQLUpload,

  Mutation: {
    uploadFile: async (_, { input }, context) => {
      const { file, description } = input;

      // Wait for file upload
      const { createReadStream, filename, mimetype } = await file;

      // Validate
      const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'application/pdf'];
      if (!allowedTypes.includes(mimetype)) {
        return errorPayload([{
          code: 'INVALID_TYPE',
          message: 'File type not allowed'
        }]);
      }

      // Upload to storage
      const stream = createReadStream();
      const result = await context.storage.upload(stream, {
        filename,
        mimetype,
        userId: context.userId,
      });

      // Create file record
      const fileRecord = await context.dataSources.files.create({
        filename: result.filename,
        mimetype,
        size: result.size,
        url: result.url,
        description,
        uploadedBy: context.userId,
      });

      return successPayload(fileRecord);
    },

    uploadPostImages: async (_, { postId, files }, context) => {
      const uploadedUrls = await Promise.all(
        files.map(async (file) => {
          const { createReadStream, filename, mimetype } = await file;
          const stream = createReadStream();
          return context.storage.upload(stream, { filename, mimetype });
        })
      );

      const post = await context.dataSources.posts.update(postId, {
        images: uploadedUrls.map(u => u.url),
      });

      return post;
    },
  },
};
```

## Nested Mutations

```graphql
input CreateOrderInput {
  items: [CreateOrderItemInput!]!
  shippingAddress: AddressInput!
  billingAddress: AddressInput
  paymentMethod: PaymentMethodInput!
  couponCode: String
}

input CreateOrderItemInput {
  productId: ID!
  quantity: Int!
  options: JSON
}

input AddressInput {
  street: String!
  city: String!
  state: String!
  country: String!
  postalCode: String!
}

input PaymentMethodInput {
  type: PaymentType!
  token: String
  cardLast4: String
}

type CreateOrderPayload {
  success: Boolean!
  order: Order
  errors: [Error!]!
}

type Mutation {
  createOrder(input: CreateOrderInput!): CreateOrderPayload!
}
```

### Nested Mutation Implementation

```typescript
const Mutation = {
  createOrder: async (_, { input }, context) => {
    // Validate all items exist and have stock
    const productIds = input.items.map(i => i.productId);
    const products = await context.dataSources.products.findByIds(productIds);

    const errors: Error[] = [];

    // Check each item
    for (const item of input.items) {
      const product = products.find(p => p.id === item.productId);
      if (!product) {
        errors.push({
          field: `items.${item.productId}`,
          code: 'NOT_FOUND',
          message: `Product ${item.productId} not found`
        });
      } else if (product.stock < item.quantity) {
        errors.push({
          field: `items.${item.productId}`,
          code: 'INSUFFICIENT_STOCK',
          message: `Only ${product.stock} available`
        });
      }
    }

    if (errors.length > 0) {
      return errorPayload(errors);
    }

    // Apply coupon if provided
    let discount = 0;
    if (input.couponCode) {
      const coupon = await context.dataSources.coupons.validate(input.couponCode);
      if (!coupon) {
        return errorPayload([{
          field: 'couponCode',
          code: 'INVALID_COUPON',
          message: 'Coupon is invalid or expired'
        }]);
      }
      discount = coupon.discount;
    }

    // Calculate total
    const subtotal = input.items.reduce((sum, item) => {
      const product = products.find(p => p.id === item.productId);
      return sum + (product!.price * item.quantity);
    }, 0);

    const total = subtotal - discount;

    // Create order in transaction
    const order = await context.db.transaction(async (trx) => {
      // Create order
      const order = await context.dataSources.orders.create({
        userId: context.userId,
        subtotal,
        discount,
        total,
        status: 'PENDING',
        shippingAddress: input.shippingAddress,
        billingAddress: input.billingAddress || input.shippingAddress,
      }, trx);

      // Create order items
      await context.dataSources.orderItems.createMany(
        input.items.map(item => ({
          orderId: order.id,
          productId: item.productId,
          quantity: item.quantity,
          price: products.find(p => p.id === item.productId)!.price,
          options: item.options,
        })),
        trx
      );

      // Reserve stock
      for (const item of input.items) {
        await context.dataSources.products.decrementStock(
          item.productId,
          item.quantity,
          trx
        );
      }

      // Process payment
      const paymentResult = await context.payment.charge({
        amount: total,
        method: input.paymentMethod,
        orderId: order.id,
      });

      if (!paymentResult.success) {
        throw new Error('Payment failed');
      }

      // Update order with payment info
      return context.dataSources.orders.update(order.id, {
        paymentId: paymentResult.transactionId,
        status: 'CONFIRMED',
      }, trx);
    });

    return successPayload(order);
  },
};
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│                   Mutation Best Practices                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Use Input Types                                             │
│     └── Single input argument, clear structure                  │
│                                                                  │
│  2. Return Payload Types                                        │
│     └── Include success, data, and errors                       │
│                                                                  │
│  3. Validate Thoroughly                                         │
│     └── Check all business rules before modifying               │
│                                                                  │
│  4. Use Transactions                                            │
│     └── Atomic operations for complex mutations                 │
│                                                                  │
│  5. Return Updated Data                                         │
│     └── Let client update cache without refetch                 │
│                                                                  │
│  6. Name by Action                                              │
│     └── publishPost, not updatePostPublished                    │
│                                                                  │
│  7. Handle Errors Gracefully                                    │
│     └── Return structured errors, not exceptions                │
│                                                                  │
│  8. Implement Idempotency                                       │
│     └── For payment and critical operations                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```
