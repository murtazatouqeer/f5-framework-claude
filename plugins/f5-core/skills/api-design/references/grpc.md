# gRPC Design Reference

## Overview

gRPC is a high-performance RPC framework using HTTP/2 and Protocol Buffers.

### gRPC vs REST

| Aspect | gRPC | REST |
|--------|------|------|
| Protocol | HTTP/2 | HTTP/1.1 or HTTP/2 |
| Format | Protocol Buffers (binary) | JSON (text) |
| Contract | Strict (.proto) | Loose (OpenAPI optional) |
| Streaming | Bidirectional | Limited |
| Browser | gRPC-Web needed | Native |
| Performance | High | Moderate |
| Type Safety | Strong (generated) | Manual |
| Use Case | Microservices, IoT | Web APIs, Public APIs |

## Service Definition

### Proto File Structure

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
  // Unary RPCs
  rpc GetUser(GetUserRequest) returns (GetUserResponse);
  rpc CreateUser(CreateUserRequest) returns (CreateUserResponse);
  rpc UpdateUser(UpdateUserRequest) returns (UpdateUserResponse);
  rpc DeleteUser(DeleteUserRequest) returns (google.protobuf.Empty);

  // Server streaming
  rpc WatchUsers(WatchUsersRequest) returns (stream UserEvent);

  // Client streaming
  rpc BatchCreateUsers(stream CreateUserRequest) returns (BatchCreateUsersResponse);

  // Bidirectional streaming
  rpc Chat(stream ChatMessage) returns (stream ChatMessage);
}
```

### Message Types

```protobuf
// Entity message
message User {
  string id = 1;
  string name = 2;
  string email = 3;
  UserStatus status = 4;
  UserRole role = 5;
  google.protobuf.Timestamp created_at = 6;
  google.protobuf.Timestamp updated_at = 7;
}

// Enums
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

message CreateUserRequest {
  string name = 1;
  string email = 2;
  string password = 3;
  UserRole role = 4;
}

message CreateUserResponse {
  User user = 1;
}

// Partial update with optional fields (proto3)
message UpdateUserRequest {
  string id = 1;
  optional string name = 2;
  optional string email = 3;
  optional UserStatus status = 4;
}

// Pagination
message ListUsersRequest {
  int32 page_size = 1;
  string page_token = 2;
  UserFilter filter = 3;
}

message ListUsersResponse {
  repeated User users = 1;
  string next_page_token = 2;
  int32 total_count = 3;
}

message UserFilter {
  repeated UserStatus statuses = 1;
  repeated UserRole roles = 2;
  string name_contains = 3;
}
```

## Streaming Patterns

### Server Streaming

```protobuf
// Definition
rpc WatchUsers(WatchUsersRequest) returns (stream UserEvent);

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
```

```go
// Server implementation (Go)
func (s *server) WatchUsers(req *pb.WatchUsersRequest, stream pb.UserService_WatchUsersServer) error {
    // Subscribe to user events
    events := s.eventBus.Subscribe("user.*")
    defer s.eventBus.Unsubscribe(events)

    for event := range events {
        if matchesFilter(event.User, req.Filter) {
            if err := stream.Send(event); err != nil {
                return err
            }
        }
    }
    return nil
}
```

### Client Streaming

```protobuf
// Definition
rpc BatchCreateUsers(stream CreateUserRequest) returns (BatchCreateUsersResponse);

message BatchCreateUsersResponse {
  repeated User users = 1;
  int32 failed_count = 2;
  repeated string errors = 3;
}
```

```go
// Server implementation (Go)
func (s *server) BatchCreateUsers(stream pb.UserService_BatchCreateUsersServer) error {
    var users []*pb.User
    var errors []string

    for {
        req, err := stream.Recv()
        if err == io.EOF {
            // Client finished sending
            return stream.SendAndClose(&pb.BatchCreateUsersResponse{
                Users:       users,
                FailedCount: int32(len(errors)),
                Errors:      errors,
            })
        }
        if err != nil {
            return err
        }

        user, err := s.createUser(req)
        if err != nil {
            errors = append(errors, err.Error())
        } else {
            users = append(users, user)
        }
    }
}
```

### Bidirectional Streaming

```protobuf
// Definition
rpc Chat(stream ChatMessage) returns (stream ChatMessage);

message ChatMessage {
  string user_id = 1;
  string content = 2;
  google.protobuf.Timestamp timestamp = 3;
}
```

```go
// Server implementation (Go)
func (s *server) Chat(stream pb.UserService_ChatServer) error {
    for {
        msg, err := stream.Recv()
        if err == io.EOF {
            return nil
        }
        if err != nil {
            return err
        }

        // Broadcast to other clients
        response := &pb.ChatMessage{
            UserId:    msg.UserId,
            Content:   fmt.Sprintf("Echo: %s", msg.Content),
            Timestamp: timestamppb.Now(),
        }

        if err := stream.Send(response); err != nil {
            return err
        }
    }
}
```

## Error Handling

### gRPC Status Codes

| Code | Description | HTTP Equivalent |
|------|-------------|-----------------|
| OK (0) | Success | 200 |
| CANCELLED (1) | Operation cancelled | 499 |
| UNKNOWN (2) | Unknown error | 500 |
| INVALID_ARGUMENT (3) | Invalid request | 400 |
| DEADLINE_EXCEEDED (4) | Timeout | 504 |
| NOT_FOUND (5) | Resource not found | 404 |
| ALREADY_EXISTS (6) | Resource exists | 409 |
| PERMISSION_DENIED (7) | No permission | 403 |
| RESOURCE_EXHAUSTED (8) | Rate limit | 429 |
| FAILED_PRECONDITION (9) | State mismatch | 400 |
| ABORTED (10) | Concurrency conflict | 409 |
| OUT_OF_RANGE (11) | Invalid range | 400 |
| UNIMPLEMENTED (12) | Not implemented | 501 |
| INTERNAL (13) | Internal error | 500 |
| UNAVAILABLE (14) | Service unavailable | 503 |
| DATA_LOSS (15) | Data corruption | 500 |
| UNAUTHENTICATED (16) | Auth required | 401 |

### Server-Side Errors

```go
import (
    "google.golang.org/grpc/codes"
    "google.golang.org/grpc/status"
)

func (s *server) GetUser(ctx context.Context, req *pb.GetUserRequest) (*pb.GetUserResponse, error) {
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
```

### Client-Side Error Handling

```go
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
            // Retry with backoff
            return getUser(client, id)
        default:
            return nil, fmt.Errorf("rpc error (%s): %s", st.Code(), st.Message())
        }
    }

    return resp.User, nil
}
```

## Interceptors

### Server Interceptors

```go
// Unary interceptor for logging
func loggingInterceptor(
    ctx context.Context,
    req interface{},
    info *grpc.UnaryServerInfo,
    handler grpc.UnaryHandler,
) (interface{}, error) {
    start := time.Now()
    resp, err := handler(ctx, req)
    duration := time.Since(start)

    log.Printf("method=%s duration=%v error=%v", info.FullMethod, duration, err)
    return resp, err
}

// Stream interceptor
func streamLoggingInterceptor(
    srv interface{},
    ss grpc.ServerStream,
    info *grpc.StreamServerInfo,
    handler grpc.StreamHandler,
) error {
    log.Printf("stream started: %s", info.FullMethod)
    err := handler(srv, ss)
    log.Printf("stream ended: %s error=%v", info.FullMethod, err)
    return err
}

// Apply interceptors
server := grpc.NewServer(
    grpc.UnaryInterceptor(loggingInterceptor),
    grpc.StreamInterceptor(streamLoggingInterceptor),
)
```

### Client Interceptors

```go
func clientLoggingInterceptor(
    ctx context.Context,
    method string,
    req, reply interface{},
    cc *grpc.ClientConn,
    invoker grpc.UnaryInvoker,
    opts ...grpc.CallOption,
) error {
    start := time.Now()
    err := invoker(ctx, method, req, reply, cc, opts...)
    log.Printf("RPC: %s duration=%v error=%v", method, time.Since(start), err)
    return err
}

// Apply interceptor
conn, err := grpc.Dial(
    address,
    grpc.WithUnaryInterceptor(clientLoggingInterceptor),
)
```

## Metadata (Headers)

### Sending Metadata

```go
// Client - outgoing metadata
ctx := metadata.AppendToOutgoingContext(ctx,
    "authorization", "Bearer token123",
    "x-request-id", "req-001",
)
resp, err := client.GetUser(ctx, req)

// Server - reading metadata
md, ok := metadata.FromIncomingContext(ctx)
if ok {
    if tokens := md.Get("authorization"); len(tokens) > 0 {
        token := tokens[0]
        // Validate token
    }
}

// Server - sending response metadata
header := metadata.Pairs("x-custom-header", "value")
grpc.SendHeader(ctx, header)
```

## Health Checks

### Health Check Service

```protobuf
// grpc.health.v1.Health service (standard)
service Health {
  rpc Check(HealthCheckRequest) returns (HealthCheckResponse);
  rpc Watch(HealthCheckRequest) returns (stream HealthCheckResponse);
}

message HealthCheckRequest {
  string service = 1;
}

message HealthCheckResponse {
  ServingStatus status = 1;

  enum ServingStatus {
    UNKNOWN = 0;
    SERVING = 1;
    NOT_SERVING = 2;
    SERVICE_UNKNOWN = 3;
  }
}
```

```go
import "google.golang.org/grpc/health/grpc_health_v1"

// Register health service
healthServer := health.NewServer()
grpc_health_v1.RegisterHealthServer(s, healthServer)

// Set service status
healthServer.SetServingStatus("user.v1.UserService", grpc_health_v1.HealthCheckResponse_SERVING)
```

## Best Practices

### Proto File Organization

```
proto/
├── google/
│   └── protobuf/
│       ├── timestamp.proto
│       └── empty.proto
├── common/
│   ├── pagination.proto
│   └── error.proto
├── user/
│   └── v1/
│       ├── user.proto
│       └── user_service.proto
└── order/
    └── v1/
        ├── order.proto
        └── order_service.proto
```

### Versioning

```protobuf
// Package versioning
package user.v1;

// API version in service name
service UserServiceV1 { ... }
service UserServiceV2 { ... }
```

### Design Guidelines

1. **Use Protocol Buffers Style Guide** - Follow Google conventions
2. **Version Your API** - Use package names like `user.v1`, `user.v2`
3. **Use Deadlines** - Always set context deadlines on client
4. **Implement Health Checks** - Use standard `grpc.health.v1`
5. **Use Interceptors** - For logging, auth, metrics, tracing
6. **Handle Errors Properly** - Use appropriate status codes
7. **Enable Compression** - Use gzip for large payloads
8. **Implement Retry Logic** - With exponential backoff
