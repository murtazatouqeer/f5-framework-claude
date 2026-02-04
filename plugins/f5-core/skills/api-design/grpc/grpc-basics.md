---
name: grpc-basics
description: gRPC fundamentals and core concepts
category: api-design/grpc
applies_to: [all]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# gRPC Basics

## Overview

gRPC is a high-performance, open-source RPC framework developed by Google. It uses
HTTP/2 for transport, Protocol Buffers for serialization, and provides features
like authentication, streaming, and load balancing.

## gRPC vs REST

```
┌─────────────────────────────────────────────────────────────────┐
│                    gRPC vs REST Comparison                       │
├────────────────┬──────────────────────┬─────────────────────────┤
│ Aspect         │ gRPC                 │ REST                    │
├────────────────┼──────────────────────┼─────────────────────────┤
│ Protocol       │ HTTP/2               │ HTTP/1.1 or HTTP/2      │
│ Format         │ Protocol Buffers     │ JSON, XML               │
│ Contract       │ Strict (.proto)      │ Loose (OpenAPI optional)│
│ Streaming      │ Bidirectional        │ Limited                 │
│ Browser        │ gRPC-Web needed      │ Native                  │
│ Performance    │ High (binary)        │ Moderate (text)         │
│ Type Safety    │ Strong (generated)   │ Manual                  │
│ Learning Curve │ Steeper              │ Gentler                 │
│ Tooling        │ Code generation      │ Flexible                │
│ Use Case       │ Microservices, IoT   │ Web APIs, Public APIs   │
└────────────────┴──────────────────────┴─────────────────────────┘
```

## Core Concepts

```
┌─────────────────────────────────────────────────────────────────┐
│                    gRPC Architecture                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────┐                         ┌────────────┐          │
│  │   Client   │                         │   Server   │          │
│  │            │                         │            │          │
│  │ ┌────────┐ │    Protocol Buffers     │ ┌────────┐ │          │
│  │ │  Stub  │─┼─────────────────────────┼─│ Service│ │          │
│  │ └────────┘ │                         │ └────────┘ │          │
│  │     │      │                         │     │      │          │
│  │ ┌────────┐ │       HTTP/2            │ ┌────────┐ │          │
│  │ │Channel │─┼─────────────────────────┼─│ Server │ │          │
│  │ └────────┘ │                         │ └────────┘ │          │
│  └────────────┘                         └────────────┘          │
│                                                                  │
│  Flow:                                                          │
│  1. Define service in .proto file                               │
│  2. Generate client/server code (protoc)                        │
│  3. Implement server handlers                                    │
│  4. Create client stub                                          │
│  5. Make RPC calls                                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Service Definition

```protobuf
// user_service.proto
syntax = "proto3";

package user.v1;

option go_package = "github.com/example/user/v1;userv1";
option java_package = "com.example.user.v1";

import "google/protobuf/timestamp.proto";
import "google/protobuf/empty.proto";

// User service for managing user accounts
service UserService {
  // Get a single user by ID
  rpc GetUser(GetUserRequest) returns (GetUserResponse);

  // List users with pagination
  rpc ListUsers(ListUsersRequest) returns (ListUsersResponse);

  // Create a new user
  rpc CreateUser(CreateUserRequest) returns (CreateUserResponse);

  // Update an existing user
  rpc UpdateUser(UpdateUserRequest) returns (UpdateUserResponse);

  // Delete a user
  rpc DeleteUser(DeleteUserRequest) returns (google.protobuf.Empty);

  // Stream user updates (server streaming)
  rpc WatchUsers(WatchUsersRequest) returns (stream UserEvent);

  // Batch create users (client streaming)
  rpc BatchCreateUsers(stream CreateUserRequest) returns (BatchCreateUsersResponse);

  // Real-time chat (bidirectional streaming)
  rpc Chat(stream ChatMessage) returns (stream ChatMessage);
}

// User entity
message User {
  string id = 1;
  string name = 2;
  string email = 3;
  UserStatus status = 4;
  UserRole role = 5;
  google.protobuf.Timestamp created_at = 6;
  google.protobuf.Timestamp updated_at = 7;
}

enum UserStatus {
  USER_STATUS_UNSPECIFIED = 0;
  USER_STATUS_ACTIVE = 1;
  USER_STATUS_INACTIVE = 2;
  USER_STATUS_SUSPENDED = 3;
}

enum UserRole {
  USER_ROLE_UNSPECIFIED = 0;
  USER_ROLE_USER = 1;
  USER_ROLE_ADMIN = 2;
  USER_ROLE_MODERATOR = 3;
}

// Request/Response messages
message GetUserRequest {
  string id = 1;
}

message GetUserResponse {
  User user = 1;
}

message ListUsersRequest {
  int32 page_size = 1;
  string page_token = 2;
  UserFilter filter = 3;
}

message UserFilter {
  repeated UserStatus statuses = 1;
  repeated UserRole roles = 2;
  string name_contains = 3;
}

message ListUsersResponse {
  repeated User users = 1;
  string next_page_token = 2;
  int32 total_count = 3;
}

message CreateUserRequest {
  string name = 1;
  string email = 2;
  string password = 3;
  UserRole role = 4;
}

message CreateUserResponse {
  User user = 1;
}

message UpdateUserRequest {
  string id = 1;
  optional string name = 2;
  optional string email = 3;
  optional UserStatus status = 4;
  optional UserRole role = 5;
}

message UpdateUserResponse {
  User user = 1;
}

message DeleteUserRequest {
  string id = 1;
}

message WatchUsersRequest {
  UserFilter filter = 1;
}

message UserEvent {
  EventType type = 1;
  User user = 2;
  google.protobuf.Timestamp timestamp = 3;

  enum EventType {
    EVENT_TYPE_UNSPECIFIED = 0;
    EVENT_TYPE_CREATED = 1;
    EVENT_TYPE_UPDATED = 2;
    EVENT_TYPE_DELETED = 3;
  }
}

message BatchCreateUsersResponse {
  repeated User users = 1;
  int32 failed_count = 2;
  repeated string errors = 3;
}

message ChatMessage {
  string user_id = 1;
  string content = 2;
  google.protobuf.Timestamp timestamp = 3;
}
```

## Server Implementation

### Go Server

```go
package main

import (
    "context"
    "log"
    "net"
    "sync"

    "google.golang.org/grpc"
    "google.golang.org/grpc/codes"
    "google.golang.org/grpc/status"
    "google.golang.org/protobuf/types/known/emptypb"
    "google.golang.org/protobuf/types/known/timestamppb"

    pb "github.com/example/user/v1"
)

type userServer struct {
    pb.UnimplementedUserServiceServer
    mu    sync.RWMutex
    users map[string]*pb.User
}

func NewUserServer() *userServer {
    return &userServer{
        users: make(map[string]*pb.User),
    }
}

// Unary RPC - Get single user
func (s *userServer) GetUser(ctx context.Context, req *pb.GetUserRequest) (*pb.GetUserResponse, error) {
    // Validate request
    if req.Id == "" {
        return nil, status.Error(codes.InvalidArgument, "user id is required")
    }

    s.mu.RLock()
    user, exists := s.users[req.Id]
    s.mu.RUnlock()

    if !exists {
        return nil, status.Errorf(codes.NotFound, "user %s not found", req.Id)
    }

    return &pb.GetUserResponse{User: user}, nil
}

// Unary RPC - List users with pagination
func (s *userServer) ListUsers(ctx context.Context, req *pb.ListUsersRequest) (*pb.ListUsersResponse, error) {
    s.mu.RLock()
    defer s.mu.RUnlock()

    pageSize := int(req.PageSize)
    if pageSize <= 0 {
        pageSize = 20
    }
    if pageSize > 100 {
        pageSize = 100
    }

    var users []*pb.User
    for _, user := range s.users {
        if matchesFilter(user, req.Filter) {
            users = append(users, user)
        }
    }

    // Implement pagination
    start := 0
    if req.PageToken != "" {
        // Decode page token to get start index
        start = decodePageToken(req.PageToken)
    }

    end := start + pageSize
    if end > len(users) {
        end = len(users)
    }

    var nextPageToken string
    if end < len(users) {
        nextPageToken = encodePageToken(end)
    }

    return &pb.ListUsersResponse{
        Users:         users[start:end],
        NextPageToken: nextPageToken,
        TotalCount:    int32(len(users)),
    }, nil
}

// Unary RPC - Create user
func (s *userServer) CreateUser(ctx context.Context, req *pb.CreateUserRequest) (*pb.CreateUserResponse, error) {
    // Validate
    if req.Name == "" {
        return nil, status.Error(codes.InvalidArgument, "name is required")
    }
    if req.Email == "" {
        return nil, status.Error(codes.InvalidArgument, "email is required")
    }

    user := &pb.User{
        Id:        generateID(),
        Name:      req.Name,
        Email:     req.Email,
        Status:    pb.UserStatus_USER_STATUS_ACTIVE,
        Role:      req.Role,
        CreatedAt: timestamppb.Now(),
        UpdatedAt: timestamppb.Now(),
    }

    s.mu.Lock()
    s.users[user.Id] = user
    s.mu.Unlock()

    return &pb.CreateUserResponse{User: user}, nil
}

// Unary RPC - Update user
func (s *userServer) UpdateUser(ctx context.Context, req *pb.UpdateUserRequest) (*pb.UpdateUserResponse, error) {
    if req.Id == "" {
        return nil, status.Error(codes.InvalidArgument, "user id is required")
    }

    s.mu.Lock()
    defer s.mu.Unlock()

    user, exists := s.users[req.Id]
    if !exists {
        return nil, status.Errorf(codes.NotFound, "user %s not found", req.Id)
    }

    // Apply partial updates
    if req.Name != nil {
        user.Name = *req.Name
    }
    if req.Email != nil {
        user.Email = *req.Email
    }
    if req.Status != nil {
        user.Status = *req.Status
    }
    if req.Role != nil {
        user.Role = *req.Role
    }
    user.UpdatedAt = timestamppb.Now()

    return &pb.UpdateUserResponse{User: user}, nil
}

// Unary RPC - Delete user
func (s *userServer) DeleteUser(ctx context.Context, req *pb.DeleteUserRequest) (*emptypb.Empty, error) {
    if req.Id == "" {
        return nil, status.Error(codes.InvalidArgument, "user id is required")
    }

    s.mu.Lock()
    defer s.mu.Unlock()

    if _, exists := s.users[req.Id]; !exists {
        return nil, status.Errorf(codes.NotFound, "user %s not found", req.Id)
    }

    delete(s.users, req.Id)
    return &emptypb.Empty{}, nil
}

func main() {
    lis, err := net.Listen("tcp", ":50051")
    if err != nil {
        log.Fatalf("failed to listen: %v", err)
    }

    // Create gRPC server with interceptors
    s := grpc.NewServer(
        grpc.UnaryInterceptor(loggingInterceptor),
        grpc.StreamInterceptor(streamLoggingInterceptor),
    )

    pb.RegisterUserServiceServer(s, NewUserServer())

    log.Println("gRPC server listening on :50051")
    if err := s.Serve(lis); err != nil {
        log.Fatalf("failed to serve: %v", err)
    }
}

// Unary interceptor for logging
func loggingInterceptor(
    ctx context.Context,
    req interface{},
    info *grpc.UnaryServerInfo,
    handler grpc.UnaryHandler,
) (interface{}, error) {
    log.Printf("gRPC call: %s", info.FullMethod)
    resp, err := handler(ctx, req)
    if err != nil {
        log.Printf("gRPC error: %s - %v", info.FullMethod, err)
    }
    return resp, err
}

// Stream interceptor for logging
func streamLoggingInterceptor(
    srv interface{},
    ss grpc.ServerStream,
    info *grpc.StreamServerInfo,
    handler grpc.StreamHandler,
) error {
    log.Printf("gRPC stream: %s", info.FullMethod)
    return handler(srv, ss)
}
```

### Node.js Server

```typescript
import * as grpc from '@grpc/grpc-js';
import * as protoLoader from '@grpc/proto-loader';
import { v4 as uuidv4 } from 'uuid';

// Load proto definition
const packageDefinition = protoLoader.loadSync('user_service.proto', {
  keepCase: true,
  longs: String,
  enums: String,
  defaults: true,
  oneofs: true,
});

const userProto = grpc.loadPackageDefinition(packageDefinition).user.v1;

// In-memory storage
const users = new Map<string, User>();

interface User {
  id: string;
  name: string;
  email: string;
  status: string;
  role: string;
  created_at: { seconds: number; nanos: number };
  updated_at: { seconds: number; nanos: number };
}

// Service implementation
const userService = {
  // Unary RPC
  getUser(
    call: grpc.ServerUnaryCall<any, any>,
    callback: grpc.sendUnaryData<any>
  ) {
    const { id } = call.request;

    if (!id) {
      return callback({
        code: grpc.status.INVALID_ARGUMENT,
        message: 'user id is required',
      });
    }

    const user = users.get(id);
    if (!user) {
      return callback({
        code: grpc.status.NOT_FOUND,
        message: `user ${id} not found`,
      });
    }

    callback(null, { user });
  },

  // Unary RPC with pagination
  listUsers(
    call: grpc.ServerUnaryCall<any, any>,
    callback: grpc.sendUnaryData<any>
  ) {
    const { page_size = 20, page_token, filter } = call.request;

    const allUsers = Array.from(users.values()).filter((user) =>
      matchesFilter(user, filter)
    );

    const start = page_token ? parseInt(page_token, 10) : 0;
    const end = Math.min(start + page_size, allUsers.length);
    const paginatedUsers = allUsers.slice(start, end);

    const nextPageToken = end < allUsers.length ? String(end) : '';

    callback(null, {
      users: paginatedUsers,
      next_page_token: nextPageToken,
      total_count: allUsers.length,
    });
  },

  // Create user
  createUser(
    call: grpc.ServerUnaryCall<any, any>,
    callback: grpc.sendUnaryData<any>
  ) {
    const { name, email, role } = call.request;

    if (!name) {
      return callback({
        code: grpc.status.INVALID_ARGUMENT,
        message: 'name is required',
      });
    }

    const now = { seconds: Math.floor(Date.now() / 1000), nanos: 0 };
    const user: User = {
      id: uuidv4(),
      name,
      email,
      status: 'USER_STATUS_ACTIVE',
      role: role || 'USER_ROLE_USER',
      created_at: now,
      updated_at: now,
    };

    users.set(user.id, user);
    callback(null, { user });
  },

  // Update user
  updateUser(
    call: grpc.ServerUnaryCall<any, any>,
    callback: grpc.sendUnaryData<any>
  ) {
    const { id, name, email, status, role } = call.request;

    if (!id) {
      return callback({
        code: grpc.status.INVALID_ARGUMENT,
        message: 'user id is required',
      });
    }

    const user = users.get(id);
    if (!user) {
      return callback({
        code: grpc.status.NOT_FOUND,
        message: `user ${id} not found`,
      });
    }

    // Partial update
    if (name !== undefined) user.name = name;
    if (email !== undefined) user.email = email;
    if (status !== undefined) user.status = status;
    if (role !== undefined) user.role = role;
    user.updated_at = { seconds: Math.floor(Date.now() / 1000), nanos: 0 };

    callback(null, { user });
  },

  // Delete user
  deleteUser(
    call: grpc.ServerUnaryCall<any, any>,
    callback: grpc.sendUnaryData<any>
  ) {
    const { id } = call.request;

    if (!id) {
      return callback({
        code: grpc.status.INVALID_ARGUMENT,
        message: 'user id is required',
      });
    }

    if (!users.has(id)) {
      return callback({
        code: grpc.status.NOT_FOUND,
        message: `user ${id} not found`,
      });
    }

    users.delete(id);
    callback(null, {});
  },
};

function matchesFilter(user: User, filter: any): boolean {
  if (!filter) return true;

  if (filter.statuses?.length && !filter.statuses.includes(user.status)) {
    return false;
  }
  if (filter.roles?.length && !filter.roles.includes(user.role)) {
    return false;
  }
  if (
    filter.name_contains &&
    !user.name.toLowerCase().includes(filter.name_contains.toLowerCase())
  ) {
    return false;
  }

  return true;
}

// Start server
const server = new grpc.Server();
server.addService(userProto.UserService.service, userService);

server.bindAsync(
  '0.0.0.0:50051',
  grpc.ServerCredentials.createInsecure(),
  (err, port) => {
    if (err) {
      console.error('Failed to bind server:', err);
      return;
    }
    console.log(`gRPC server running on port ${port}`);
    server.start();
  }
);
```

## Client Implementation

### Go Client

```go
package main

import (
    "context"
    "log"
    "time"

    "google.golang.org/grpc"
    "google.golang.org/grpc/credentials/insecure"
    "google.golang.org/grpc/metadata"

    pb "github.com/example/user/v1"
)

func main() {
    // Create connection
    conn, err := grpc.Dial(
        "localhost:50051",
        grpc.WithTransportCredentials(insecure.NewCredentials()),
        grpc.WithUnaryInterceptor(clientInterceptor),
    )
    if err != nil {
        log.Fatalf("failed to connect: %v", err)
    }
    defer conn.Close()

    // Create client
    client := pb.NewUserServiceClient(conn)

    // Context with timeout and metadata
    ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
    defer cancel()

    // Add metadata (like headers)
    ctx = metadata.AppendToOutgoingContext(ctx,
        "authorization", "Bearer token123",
        "x-request-id", "req-001",
    )

    // Create user
    createResp, err := client.CreateUser(ctx, &pb.CreateUserRequest{
        Name:  "John Doe",
        Email: "john@example.com",
        Role:  pb.UserRole_USER_ROLE_USER,
    })
    if err != nil {
        log.Fatalf("CreateUser failed: %v", err)
    }
    log.Printf("Created user: %s", createResp.User.Id)

    // Get user
    getResp, err := client.GetUser(ctx, &pb.GetUserRequest{
        Id: createResp.User.Id,
    })
    if err != nil {
        log.Fatalf("GetUser failed: %v", err)
    }
    log.Printf("Got user: %s", getResp.User.Name)

    // List users with pagination
    listResp, err := client.ListUsers(ctx, &pb.ListUsersRequest{
        PageSize: 10,
        Filter: &pb.UserFilter{
            Statuses: []pb.UserStatus{pb.UserStatus_USER_STATUS_ACTIVE},
        },
    })
    if err != nil {
        log.Fatalf("ListUsers failed: %v", err)
    }
    log.Printf("Found %d users (total: %d)", len(listResp.Users), listResp.TotalCount)

    // Update user
    newName := "John Smith"
    updateResp, err := client.UpdateUser(ctx, &pb.UpdateUserRequest{
        Id:   createResp.User.Id,
        Name: &newName,
    })
    if err != nil {
        log.Fatalf("UpdateUser failed: %v", err)
    }
    log.Printf("Updated user: %s", updateResp.User.Name)

    // Delete user
    _, err = client.DeleteUser(ctx, &pb.DeleteUserRequest{
        Id: createResp.User.Id,
    })
    if err != nil {
        log.Fatalf("DeleteUser failed: %v", err)
    }
    log.Println("Deleted user")
}

// Client interceptor for logging
func clientInterceptor(
    ctx context.Context,
    method string,
    req, reply interface{},
    cc *grpc.ClientConn,
    invoker grpc.UnaryInvoker,
    opts ...grpc.CallOption,
) error {
    start := time.Now()
    err := invoker(ctx, method, req, reply, cc, opts...)
    log.Printf("RPC: %s, Duration: %v, Error: %v", method, time.Since(start), err)
    return err
}
```

### Node.js Client

```typescript
import * as grpc from '@grpc/grpc-js';
import * as protoLoader from '@grpc/proto-loader';

// Load proto
const packageDefinition = protoLoader.loadSync('user_service.proto', {
  keepCase: true,
  longs: String,
  enums: String,
  defaults: true,
  oneofs: true,
});

const userProto = grpc.loadPackageDefinition(packageDefinition).user.v1 as any;

// Create client
const client = new userProto.UserService(
  'localhost:50051',
  grpc.credentials.createInsecure()
);

// Promisify for async/await
function promisify<T>(
  method: Function
): (request: any, metadata?: grpc.Metadata) => Promise<T> {
  return (request: any, metadata?: grpc.Metadata) => {
    return new Promise((resolve, reject) => {
      method.call(
        client,
        request,
        metadata || new grpc.Metadata(),
        (error: grpc.ServiceError | null, response: T) => {
          if (error) reject(error);
          else resolve(response);
        }
      );
    });
  };
}

// Typed client methods
const userClient = {
  getUser: promisify<any>(client.getUser),
  listUsers: promisify<any>(client.listUsers),
  createUser: promisify<any>(client.createUser),
  updateUser: promisify<any>(client.updateUser),
  deleteUser: promisify<any>(client.deleteUser),
};

// Usage
async function main() {
  try {
    // Add metadata
    const metadata = new grpc.Metadata();
    metadata.add('authorization', 'Bearer token123');
    metadata.add('x-request-id', 'req-001');

    // Create user
    const createResponse = await userClient.createUser(
      {
        name: 'Jane Doe',
        email: 'jane@example.com',
        role: 'USER_ROLE_USER',
      },
      metadata
    );
    console.log('Created user:', createResponse.user.id);

    // Get user
    const getResponse = await userClient.getUser(
      { id: createResponse.user.id },
      metadata
    );
    console.log('Got user:', getResponse.user.name);

    // List users
    const listResponse = await userClient.listUsers(
      {
        page_size: 10,
        filter: {
          statuses: ['USER_STATUS_ACTIVE'],
        },
      },
      metadata
    );
    console.log(
      `Found ${listResponse.users.length} users (total: ${listResponse.total_count})`
    );

    // Update user
    const updateResponse = await userClient.updateUser(
      {
        id: createResponse.user.id,
        name: 'Jane Smith',
      },
      metadata
    );
    console.log('Updated user:', updateResponse.user.name);

    // Delete user
    await userClient.deleteUser({ id: createResponse.user.id }, metadata);
    console.log('Deleted user');
  } catch (error) {
    console.error('Error:', error);
  }
}

main();
```

## Error Handling

### gRPC Status Codes

```
┌─────────────────────────────────────────────────────────────────┐
│                    gRPC Status Codes                             │
├────────────┬─────────────────────────────────────────────────────┤
│ Code       │ Description                                         │
├────────────┼─────────────────────────────────────────────────────┤
│ OK (0)     │ Success                                             │
│ CANCELLED  │ Operation cancelled by caller                       │
│ UNKNOWN    │ Unknown error                                       │
│ INVALID_ARGUMENT │ Invalid request argument                      │
│ DEADLINE_EXCEEDED │ Timeout                                      │
│ NOT_FOUND  │ Resource not found                                  │
│ ALREADY_EXISTS │ Resource already exists                         │
│ PERMISSION_DENIED │ No permission for operation                  │
│ RESOURCE_EXHAUSTED │ Rate limit or quota exceeded               │
│ FAILED_PRECONDITION │ Operation rejected (state mismatch)       │
│ ABORTED    │ Concurrency conflict                                │
│ OUT_OF_RANGE │ Value out of valid range                          │
│ UNIMPLEMENTED │ Method not implemented                           │
│ INTERNAL   │ Internal server error                               │
│ UNAVAILABLE │ Service temporarily unavailable                    │
│ DATA_LOSS  │ Unrecoverable data loss                             │
│ UNAUTHENTICATED │ Missing or invalid credentials                 │
└────────────┴─────────────────────────────────────────────────────┘
```

### Error Handling Best Practices

```go
// Server-side error handling
func (s *userServer) GetUser(ctx context.Context, req *pb.GetUserRequest) (*pb.GetUserResponse, error) {
    // Validation error
    if req.Id == "" {
        return nil, status.Error(codes.InvalidArgument, "user id is required")
    }

    // Not found error
    user, err := s.repo.FindByID(ctx, req.Id)
    if err != nil {
        if errors.Is(err, ErrNotFound) {
            return nil, status.Errorf(codes.NotFound, "user %s not found", req.Id)
        }
        // Internal error - don't expose details
        log.Printf("internal error: %v", err)
        return nil, status.Error(codes.Internal, "internal server error")
    }

    // Permission check
    if !hasPermission(ctx, user) {
        return nil, status.Error(codes.PermissionDenied, "access denied")
    }

    return &pb.GetUserResponse{User: user}, nil
}

// Client-side error handling
func getUser(client pb.UserServiceClient, id string) (*pb.User, error) {
    ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
    defer cancel()

    resp, err := client.GetUser(ctx, &pb.GetUserRequest{Id: id})
    if err != nil {
        st, ok := status.FromError(err)
        if !ok {
            return nil, fmt.Errorf("unknown error: %v", err)
        }

        switch st.Code() {
        case codes.InvalidArgument:
            return nil, fmt.Errorf("invalid request: %s", st.Message())
        case codes.NotFound:
            return nil, fmt.Errorf("user not found: %s", id)
        case codes.DeadlineExceeded:
            return nil, fmt.Errorf("request timeout")
        case codes.Unavailable:
            // Retry logic
            return getUser(client, id) // with backoff
        default:
            return nil, fmt.Errorf("rpc error (%s): %s", st.Code(), st.Message())
        }
    }

    return resp.User, nil
}
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│                    gRPC Best Practices                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Use Protocol Buffers Style Guide                            │
│     └── Follow Google's .proto style conventions                │
│                                                                  │
│  2. Version Your API                                            │
│     └── Use package names like user.v1, user.v2                 │
│                                                                  │
│  3. Use Deadlines (Timeouts)                                    │
│     └── Always set context deadlines on client                  │
│                                                                  │
│  4. Implement Health Checks                                     │
│     └── Use grpc.health.v1 standard                             │
│                                                                  │
│  5. Use Interceptors                                            │
│     └── For logging, auth, metrics, tracing                     │
│                                                                  │
│  6. Handle Errors Properly                                      │
│     └── Use appropriate status codes                            │
│                                                                  │
│  7. Enable Compression                                          │
│     └── Use gzip for large payloads                             │
│                                                                  │
│  8. Implement Retry Logic                                       │
│     └── With exponential backoff for transient errors           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```
