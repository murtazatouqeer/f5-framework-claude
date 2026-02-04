---
name: protobuf
description: Protocol Buffers message definition and serialization
category: api-design/grpc
applies_to: [all]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Protocol Buffers

## Overview

Protocol Buffers (protobuf) is Google's language-neutral, platform-neutral
extensible mechanism for serializing structured data. It's smaller, faster,
and simpler than XML or JSON.

## Proto File Structure

```protobuf
// File: messages.proto
syntax = "proto3";  // Always specify syntax

// Package prevents naming conflicts
package mycompany.myproject.v1;

// Language-specific options
option go_package = "github.com/mycompany/myproject/v1;projectv1";
option java_package = "com.mycompany.myproject.v1";
option java_multiple_files = true;
option csharp_namespace = "MyCompany.MyProject.V1";

// Import other proto files
import "google/protobuf/timestamp.proto";
import "google/protobuf/duration.proto";
import "google/protobuf/wrappers.proto";
import "google/protobuf/any.proto";

// Message definitions follow...
```

## Scalar Types

```protobuf
message ScalarTypes {
  // Numeric types
  double double_val = 1;      // 64-bit float
  float float_val = 2;        // 32-bit float
  int32 int32_val = 3;        // Variable-length encoding (inefficient for negative)
  int64 int64_val = 4;        // Variable-length encoding
  uint32 uint32_val = 5;      // Variable-length unsigned
  uint64 uint64_val = 6;      // Variable-length unsigned
  sint32 sint32_val = 7;      // Variable-length signed (efficient for negative)
  sint64 sint64_val = 8;      // Variable-length signed
  fixed32 fixed32_val = 9;    // Always 4 bytes (efficient for > 2^28)
  fixed64 fixed64_val = 10;   // Always 8 bytes (efficient for > 2^56)
  sfixed32 sfixed32_val = 11; // Always 4 bytes, signed
  sfixed64 sfixed64_val = 12; // Always 8 bytes, signed

  // Other types
  bool bool_val = 13;         // Boolean
  string string_val = 14;     // UTF-8 or 7-bit ASCII text
  bytes bytes_val = 15;       // Arbitrary byte sequence
}
```

### Type Selection Guide

```
┌─────────────────────────────────────────────────────────────────┐
│                    Scalar Type Selection Guide                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Integer Types:                                                  │
│  ├── Positive numbers only → uint32/uint64                      │
│  ├── Mostly positive       → int32/int64                        │
│  ├── Positive & negative   → sint32/sint64                      │
│  ├── Large positive (>2^28)→ fixed32/fixed64                    │
│  └── Large signed          → sfixed32/sfixed64                  │
│                                                                  │
│  Floating Point:                                                 │
│  ├── Standard precision    → float (32-bit)                     │
│  └── High precision        → double (64-bit)                    │
│                                                                  │
│  Text/Binary:                                                    │
│  ├── Text data             → string (UTF-8)                     │
│  └── Binary data           → bytes                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Message Types

### Basic Messages

```protobuf
// Simple message
message User {
  string id = 1;
  string name = 2;
  string email = 3;
}

// Nested messages
message Address {
  string street = 1;
  string city = 2;
  string state = 3;
  string zip_code = 4;
  string country = 5;
}

message Person {
  string id = 1;
  string first_name = 2;
  string last_name = 3;
  Address home_address = 4;
  Address work_address = 5;
}

// Inline nested message
message Order {
  string id = 1;
  string customer_id = 2;

  message LineItem {
    string product_id = 1;
    int32 quantity = 2;
    int64 unit_price_cents = 3;
  }

  repeated LineItem items = 3;
  int64 total_cents = 4;
}
```

### Field Numbers

```protobuf
message FieldNumberBestPractices {
  // 1-15: Use for frequently used fields (1 byte encoding)
  string id = 1;
  string name = 2;
  string type = 3;

  // 16-2047: Use for less frequent fields (2 bytes encoding)
  string description = 16;
  string metadata = 17;

  // Reserved numbers: Mark removed fields
  reserved 4, 5, 6;
  reserved 100 to 199;

  // Reserved names: Prevent reuse of field names
  reserved "old_field", "deprecated_field";

  // Never use: 19000-19999 (reserved for protobuf implementation)
}
```

## Enumerations

```protobuf
// Basic enum
enum Status {
  STATUS_UNSPECIFIED = 0;  // Always have UNSPECIFIED as 0
  STATUS_ACTIVE = 1;
  STATUS_INACTIVE = 2;
  STATUS_DELETED = 3;
}

// Enum with aliases (not recommended)
enum Priority {
  option allow_alias = true;
  PRIORITY_UNSPECIFIED = 0;
  PRIORITY_LOW = 1;
  PRIORITY_NORMAL = 2;
  PRIORITY_MEDIUM = 2;      // Alias for NORMAL
  PRIORITY_HIGH = 3;
  PRIORITY_CRITICAL = 4;
  PRIORITY_URGENT = 4;      // Alias for CRITICAL
}

// Nested enum
message Task {
  string id = 1;
  string title = 2;

  enum TaskStatus {
    TASK_STATUS_UNSPECIFIED = 0;
    TASK_STATUS_TODO = 1;
    TASK_STATUS_IN_PROGRESS = 2;
    TASK_STATUS_DONE = 3;
  }

  TaskStatus status = 3;
}

// Usage in message
message Document {
  string id = 1;
  string title = 2;
  Status status = 3;
  Task.TaskStatus review_status = 4;
}
```

## Collections

### Repeated Fields (Arrays)

```protobuf
message RepeatedExamples {
  // Array of scalars
  repeated string tags = 1;
  repeated int32 scores = 2;

  // Array of messages
  repeated Address addresses = 3;

  // Packed encoding (default for scalar numerics in proto3)
  repeated int32 packed_numbers = 4 [packed = true];
}
```

### Maps

```protobuf
message MapExamples {
  // String to string map
  map<string, string> metadata = 1;

  // String to message map
  map<string, User> users_by_id = 2;

  // Integer key map
  map<int32, string> id_to_name = 3;

  // Note: Map keys can be any integral or string type
  // Map values can be any type except another map
}

// Maps are equivalent to:
message MapEntry {
  string key = 1;
  User value = 2;
}
message EquivalentMap {
  repeated MapEntry users_by_id = 1;
}
```

## Optional and Oneof

### Optional Fields (proto3)

```protobuf
message OptionalExample {
  // In proto3, all fields are optional by default
  // Use 'optional' keyword to track field presence
  string required_name = 1;
  optional string optional_nickname = 2;
  optional int32 age = 3;

  // Without 'optional', can't distinguish between:
  // - Field not set
  // - Field set to default value (0, "", false)
}
```

### Oneof (Union Types)

```protobuf
message Payment {
  string id = 1;
  int64 amount_cents = 2;

  // Only one of these can be set at a time
  oneof payment_method {
    CreditCard credit_card = 3;
    BankTransfer bank_transfer = 4;
    DigitalWallet digital_wallet = 5;
  }
}

message CreditCard {
  string number = 1;
  string expiry = 2;
  string cvv = 3;
}

message BankTransfer {
  string account_number = 1;
  string routing_number = 2;
}

message DigitalWallet {
  string provider = 1;  // "paypal", "applepay", etc.
  string token = 2;
}

// Usage patterns
message Notification {
  string id = 1;

  oneof channel {
    EmailNotification email = 2;
    SmsNotification sms = 3;
    PushNotification push = 4;
  }

  oneof urgency {
    bool is_urgent = 5;
    int32 priority_level = 6;
  }
}

message EmailNotification {
  string to = 1;
  string subject = 2;
  string body = 3;
}

message SmsNotification {
  string phone_number = 1;
  string message = 2;
}

message PushNotification {
  string device_token = 1;
  string title = 2;
  string body = 3;
}
```

## Well-Known Types

```protobuf
syntax = "proto3";

import "google/protobuf/timestamp.proto";
import "google/protobuf/duration.proto";
import "google/protobuf/wrappers.proto";
import "google/protobuf/any.proto";
import "google/protobuf/struct.proto";
import "google/protobuf/empty.proto";
import "google/protobuf/field_mask.proto";

message WellKnownTypesExample {
  // Timestamp - point in time
  google.protobuf.Timestamp created_at = 1;
  google.protobuf.Timestamp updated_at = 2;

  // Duration - span of time
  google.protobuf.Duration timeout = 3;
  google.protobuf.Duration retry_delay = 4;

  // Wrappers - nullable primitives
  google.protobuf.StringValue nullable_string = 5;
  google.protobuf.Int32Value nullable_int = 6;
  google.protobuf.BoolValue nullable_bool = 7;
  google.protobuf.DoubleValue nullable_double = 8;

  // Any - arbitrary message type
  google.protobuf.Any extension = 9;

  // Struct - dynamic JSON-like data
  google.protobuf.Struct metadata = 10;
  google.protobuf.Value dynamic_value = 11;
  google.protobuf.ListValue items = 12;

  // FieldMask - partial updates
  google.protobuf.FieldMask update_mask = 13;
}

// Service using well-known types
service ResourceService {
  // Empty request/response
  rpc Ping(google.protobuf.Empty) returns (google.protobuf.Empty);

  // Partial update with field mask
  rpc UpdateResource(UpdateResourceRequest) returns (Resource);
}

message UpdateResourceRequest {
  string id = 1;
  Resource resource = 2;
  google.protobuf.FieldMask update_mask = 3;
}

message Resource {
  string id = 1;
  string name = 2;
  string description = 3;
  google.protobuf.Struct attributes = 4;
  google.protobuf.Timestamp created_at = 5;
}
```

### Using Well-Known Types in Code

```go
package main

import (
    "time"

    "google.golang.org/protobuf/types/known/durationpb"
    "google.golang.org/protobuf/types/known/structpb"
    "google.golang.org/protobuf/types/known/timestamppb"
    "google.golang.org/protobuf/types/known/wrapperspb"
)

func createResource() *Resource {
    // Timestamp from time.Time
    now := timestamppb.Now()
    past := timestamppb.New(time.Now().Add(-24 * time.Hour))

    // Duration
    timeout := durationpb.New(30 * time.Second)

    // Wrappers for nullable values
    nullableString := wrapperspb.String("optional value")
    nullableInt := wrapperspb.Int32(42)

    // Struct from map
    metadata, _ := structpb.NewStruct(map[string]interface{}{
        "key":     "value",
        "nested":  map[string]interface{}{"a": 1, "b": 2},
        "numbers": []interface{}{1, 2, 3},
    })

    return &Resource{
        Id:          "res-001",
        Name:        "Example",
        Description: "Demo resource",
        Attributes:  metadata,
        CreatedAt:   now,
    }
}
```

```typescript
import { Timestamp } from 'google-protobuf/google/protobuf/timestamp_pb';
import { Duration } from 'google-protobuf/google/protobuf/duration_pb';
import { Struct } from 'google-protobuf/google/protobuf/struct_pb';

function createResource(): Resource {
  const resource = new Resource();

  // Timestamp
  const now = new Timestamp();
  now.fromDate(new Date());
  resource.setCreatedAt(now);

  // Duration (30 seconds)
  const timeout = new Duration();
  timeout.setSeconds(30);

  // Struct from object
  const metadata = Struct.fromJavaScript({
    key: 'value',
    nested: { a: 1, b: 2 },
    numbers: [1, 2, 3],
  });
  resource.setAttributes(metadata);

  return resource;
}
```

## Field Masks

```protobuf
import "google/protobuf/field_mask.proto";

message UpdateUserRequest {
  string id = 1;
  User user = 2;
  // Specifies which fields to update
  google.protobuf.FieldMask update_mask = 3;
}

// Example usage:
// update_mask: { paths: ["name", "email", "profile.bio"] }
// Only updates name, email, and profile.bio fields
```

```go
import (
    "google.golang.org/protobuf/types/known/fieldmaskpb"
)

func updateUser(client pb.UserServiceClient, req *pb.UpdateUserRequest) error {
    // Create field mask
    mask, err := fieldmaskpb.New(req.User, "name", "email")
    if err != nil {
        return err
    }
    req.UpdateMask = mask

    // Apply updates using mask
    _, err = client.UpdateUser(ctx, req)
    return err
}

// Server-side application
func (s *server) UpdateUser(ctx context.Context, req *pb.UpdateUserRequest) (*pb.User, error) {
    existing := s.getUser(req.Id)

    // Apply only masked fields
    for _, path := range req.UpdateMask.GetPaths() {
        switch path {
        case "name":
            existing.Name = req.User.Name
        case "email":
            existing.Email = req.User.Email
        case "profile.bio":
            if existing.Profile == nil {
                existing.Profile = &pb.Profile{}
            }
            existing.Profile.Bio = req.User.Profile.Bio
        }
    }

    return s.saveUser(existing)
}
```

## API Design Patterns

### Request/Response Pattern

```protobuf
// Standard CRUD operations
service UserService {
  rpc GetUser(GetUserRequest) returns (GetUserResponse);
  rpc ListUsers(ListUsersRequest) returns (ListUsersResponse);
  rpc CreateUser(CreateUserRequest) returns (CreateUserResponse);
  rpc UpdateUser(UpdateUserRequest) returns (UpdateUserResponse);
  rpc DeleteUser(DeleteUserRequest) returns (google.protobuf.Empty);
}

// Get - single resource
message GetUserRequest {
  string id = 1;
}
message GetUserResponse {
  User user = 1;
}

// List - paginated collection
message ListUsersRequest {
  int32 page_size = 1;
  string page_token = 2;
  UserFilter filter = 3;
  string order_by = 4;
}
message ListUsersResponse {
  repeated User users = 1;
  string next_page_token = 2;
  int32 total_size = 3;
}

// Create
message CreateUserRequest {
  User user = 1;
  string request_id = 2;  // For idempotency
}
message CreateUserResponse {
  User user = 1;
}

// Update with field mask
message UpdateUserRequest {
  User user = 1;
  google.protobuf.FieldMask update_mask = 2;
}
message UpdateUserResponse {
  User user = 1;
}

// Delete
message DeleteUserRequest {
  string id = 1;
  bool force = 2;  // Skip soft-delete
}
```

### Long-Running Operations

```protobuf
import "google/longrunning/operations.proto";

service DataProcessingService {
  // Returns operation that can be polled
  rpc ProcessData(ProcessDataRequest) returns (google.longrunning.Operation);

  // Cancel running operation
  rpc CancelProcessing(CancelProcessingRequest) returns (google.protobuf.Empty);
}

message ProcessDataRequest {
  string input_path = 1;
  string output_path = 2;
  ProcessingOptions options = 3;
}

message ProcessDataResponse {
  string output_path = 1;
  ProcessingStats stats = 2;
}

message ProcessDataMetadata {
  int32 progress_percent = 1;
  string current_step = 2;
  google.protobuf.Timestamp start_time = 3;
}
```

### Batch Operations

```protobuf
service BatchService {
  rpc BatchGetUsers(BatchGetUsersRequest) returns (BatchGetUsersResponse);
  rpc BatchCreateUsers(BatchCreateUsersRequest) returns (BatchCreateUsersResponse);
  rpc BatchUpdateUsers(BatchUpdateUsersRequest) returns (BatchUpdateUsersResponse);
  rpc BatchDeleteUsers(BatchDeleteUsersRequest) returns (BatchDeleteUsersResponse);
}

message BatchGetUsersRequest {
  repeated string ids = 1;
}

message BatchGetUsersResponse {
  // Map preserves order and handles missing items
  map<string, User> users = 1;
  repeated string not_found = 2;
}

message BatchCreateUsersRequest {
  repeated CreateUserRequest requests = 1;
}

message BatchCreateUsersResponse {
  repeated User users = 1;
  repeated BatchError errors = 2;
}

message BatchError {
  int32 index = 1;      // Which request failed
  int32 code = 2;       // Error code
  string message = 3;   // Error message
}
```

## Code Generation

### protoc Commands

```bash
# Go code generation
protoc --go_out=. --go_opt=paths=source_relative \
       --go-grpc_out=. --go-grpc_opt=paths=source_relative \
       proto/*.proto

# Python
protoc --python_out=. --grpc_python_out=. proto/*.proto

# TypeScript (using ts-proto)
protoc --plugin=./node_modules/.bin/protoc-gen-ts_proto \
       --ts_proto_out=./src/generated \
       --ts_proto_opt=outputServices=grpc-js \
       --ts_proto_opt=esModuleInterop=true \
       proto/*.proto

# Multiple languages at once
protoc --go_out=./go --go-grpc_out=./go \
       --python_out=./python --grpc_python_out=./python \
       --java_out=./java \
       proto/*.proto
```

### buf.yaml Configuration

```yaml
# buf.yaml
version: v1
name: buf.build/mycompany/myproject
deps:
  - buf.build/googleapis/googleapis
lint:
  use:
    - DEFAULT
  except:
    - FIELD_LOWER_SNAKE_CASE
breaking:
  use:
    - FILE
```

```yaml
# buf.gen.yaml
version: v1
plugins:
  - plugin: buf.build/protocolbuffers/go
    out: gen/go
    opt: paths=source_relative
  - plugin: buf.build/grpc/go
    out: gen/go
    opt: paths=source_relative
  - plugin: buf.build/community/timostamm-protobuf-ts
    out: gen/ts
    opt:
      - long_type_string
      - output_javascript
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│                Protocol Buffer Best Practices                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Field Numbers                                               │
│     ├── Use 1-15 for frequently accessed fields                 │
│     ├── Never reuse deleted field numbers                       │
│     └── Use reserved for removed fields                         │
│                                                                  │
│  2. Naming Conventions                                          │
│     ├── Messages: PascalCase (UserAccount)                      │
│     ├── Fields: snake_case (user_name)                          │
│     ├── Enums: SCREAMING_SNAKE_CASE                             │
│     └── Services: PascalCase (UserService)                      │
│                                                                  │
│  3. Enums                                                       │
│     ├── Always start with UNSPECIFIED = 0                       │
│     ├── Prefix values with enum name                            │
│     └── Don't use aliases unless necessary                      │
│                                                                  │
│  4. Versioning                                                  │
│     ├── Use package versioning (v1, v2)                         │
│     ├── Don't change field types                                │
│     └── Only add, never remove fields                           │
│                                                                  │
│  5. Documentation                                               │
│     ├── Comment all messages and fields                         │
│     ├── Document enum value meanings                            │
│     └── Include examples where helpful                          │
│                                                                  │
│  6. Organization                                                │
│     ├── One file per service                                    │
│     ├── Shared messages in separate files                       │
│     └── Use imports for dependencies                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```
