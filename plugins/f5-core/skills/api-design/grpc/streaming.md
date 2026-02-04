---
name: streaming
description: gRPC streaming patterns and implementation
category: api-design/grpc
applies_to: [all]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# gRPC Streaming

## Overview

gRPC supports four types of communication patterns: unary (request-response),
server streaming, client streaming, and bidirectional streaming. Streaming
enables efficient transfer of large data sets and real-time communication.

## Streaming Types

```
┌─────────────────────────────────────────────────────────────────┐
│                    gRPC Streaming Types                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Unary RPC (1:1)                                             │
│     Client ──request──> Server                                  │
│     Client <──response── Server                                 │
│                                                                  │
│  2. Server Streaming (1:N)                                      │
│     Client ──request──> Server                                  │
│     Client <──stream── Server (multiple responses)              │
│                                                                  │
│  3. Client Streaming (N:1)                                      │
│     Client ──stream──> Server (multiple requests)               │
│     Client <──response── Server                                 │
│                                                                  │
│  4. Bidirectional Streaming (N:N)                               │
│     Client <──stream──> Server (both directions)                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Service Definition

```protobuf
syntax = "proto3";

package streaming.v1;

import "google/protobuf/timestamp.proto";

service StreamingService {
  // Unary: Single request, single response
  rpc GetData(GetDataRequest) returns (GetDataResponse);

  // Server streaming: Single request, stream of responses
  rpc DownloadFile(DownloadRequest) returns (stream FileChunk);
  rpc WatchEvents(WatchRequest) returns (stream Event);
  rpc ListLargeDataset(ListRequest) returns (stream DataItem);

  // Client streaming: Stream of requests, single response
  rpc UploadFile(stream FileChunk) returns (UploadResponse);
  rpc CollectMetrics(stream Metric) returns (MetricsSummary);
  rpc BatchProcess(stream ProcessRequest) returns (ProcessResponse);

  // Bidirectional streaming: Stream both directions
  rpc Chat(stream ChatMessage) returns (stream ChatMessage);
  rpc SyncData(stream SyncRequest) returns (stream SyncResponse);
  rpc InteractiveQuery(stream QueryRequest) returns (stream QueryResponse);
}

// Messages
message FileChunk {
  bytes content = 1;
  int64 offset = 2;
  int64 total_size = 3;
  string filename = 4;
}

message DownloadRequest {
  string file_id = 1;
  int64 start_offset = 2;  // For resumable downloads
}

message UploadResponse {
  string file_id = 1;
  int64 size = 2;
  string checksum = 3;
}

message Event {
  string id = 1;
  string type = 2;
  bytes payload = 3;
  google.protobuf.Timestamp timestamp = 4;
}

message WatchRequest {
  repeated string event_types = 1;
  string filter = 2;
}

message ChatMessage {
  string user_id = 1;
  string room_id = 2;
  string content = 3;
  google.protobuf.Timestamp timestamp = 4;
}

message Metric {
  string name = 1;
  double value = 2;
  map<string, string> labels = 3;
  google.protobuf.Timestamp timestamp = 4;
}

message MetricsSummary {
  int64 total_count = 1;
  map<string, double> aggregates = 2;
}
```

## Server Streaming Implementation

### Go Server

```go
package main

import (
    "io"
    "log"
    "os"
    "time"

    pb "github.com/example/streaming/v1"
    "google.golang.org/grpc/codes"
    "google.golang.org/grpc/status"
)

// Server streaming: Download file in chunks
func (s *server) DownloadFile(req *pb.DownloadRequest, stream pb.StreamingService_DownloadFileServer) error {
    // Validate request
    if req.FileId == "" {
        return status.Error(codes.InvalidArgument, "file_id is required")
    }

    // Open file
    file, err := os.Open(s.getFilePath(req.FileId))
    if err != nil {
        if os.IsNotExist(err) {
            return status.Errorf(codes.NotFound, "file %s not found", req.FileId)
        }
        return status.Errorf(codes.Internal, "failed to open file: %v", err)
    }
    defer file.Close()

    // Get file info
    info, err := file.Stat()
    if err != nil {
        return status.Errorf(codes.Internal, "failed to stat file: %v", err)
    }

    // Seek to offset for resumable downloads
    if req.StartOffset > 0 {
        if _, err := file.Seek(req.StartOffset, 0); err != nil {
            return status.Errorf(codes.Internal, "failed to seek: %v", err)
        }
    }

    // Stream file in chunks
    chunkSize := 64 * 1024 // 64KB chunks
    buffer := make([]byte, chunkSize)
    offset := req.StartOffset

    for {
        // Check if client cancelled
        if err := stream.Context().Err(); err != nil {
            log.Printf("Client cancelled download: %v", err)
            return status.Error(codes.Canceled, "download cancelled")
        }

        n, err := file.Read(buffer)
        if err == io.EOF {
            break
        }
        if err != nil {
            return status.Errorf(codes.Internal, "failed to read file: %v", err)
        }

        chunk := &pb.FileChunk{
            Content:   buffer[:n],
            Offset:    offset,
            TotalSize: info.Size(),
            Filename:  info.Name(),
        }

        if err := stream.Send(chunk); err != nil {
            return status.Errorf(codes.Internal, "failed to send chunk: %v", err)
        }

        offset += int64(n)
    }

    return nil
}

// Server streaming: Watch for events
func (s *server) WatchEvents(req *pb.WatchRequest, stream pb.StreamingService_WatchEventsServer) error {
    // Subscribe to event channel
    eventCh := s.eventBus.Subscribe(req.EventTypes...)
    defer s.eventBus.Unsubscribe(eventCh)

    for {
        select {
        case <-stream.Context().Done():
            // Client disconnected
            return nil

        case event := <-eventCh:
            // Apply filter if specified
            if req.Filter != "" && !matchesFilter(event, req.Filter) {
                continue
            }

            if err := stream.Send(event); err != nil {
                return status.Errorf(codes.Internal, "failed to send event: %v", err)
            }
        }
    }
}

// Server streaming: Large dataset pagination via streaming
func (s *server) ListLargeDataset(req *pb.ListRequest, stream pb.StreamingService_ListLargeDatasetServer) error {
    cursor := req.StartCursor
    batchSize := 100

    for {
        // Check context
        if err := stream.Context().Err(); err != nil {
            return nil
        }

        // Fetch batch from database
        items, nextCursor, err := s.db.FetchBatch(stream.Context(), cursor, batchSize)
        if err != nil {
            return status.Errorf(codes.Internal, "database error: %v", err)
        }

        // Stream each item
        for _, item := range items {
            if err := stream.Send(item); err != nil {
                return err
            }
        }

        // Check if done
        if nextCursor == "" || len(items) < batchSize {
            break
        }
        cursor = nextCursor
    }

    return nil
}
```

### Go Client

```go
package main

import (
    "context"
    "io"
    "log"
    "os"
    "time"

    pb "github.com/example/streaming/v1"
    "google.golang.org/grpc"
)

// Client: Download file with progress
func downloadFile(client pb.StreamingServiceClient, fileID, outputPath string) error {
    ctx, cancel := context.WithTimeout(context.Background(), 10*time.Minute)
    defer cancel()

    // Start download stream
    stream, err := client.DownloadFile(ctx, &pb.DownloadRequest{
        FileId: fileID,
    })
    if err != nil {
        return err
    }

    // Create output file
    file, err := os.Create(outputPath)
    if err != nil {
        return err
    }
    defer file.Close()

    var totalReceived int64
    var totalSize int64

    for {
        chunk, err := stream.Recv()
        if err == io.EOF {
            break
        }
        if err != nil {
            return err
        }

        // Write chunk to file
        _, err = file.WriteAt(chunk.Content, chunk.Offset)
        if err != nil {
            return err
        }

        totalReceived += int64(len(chunk.Content))
        totalSize = chunk.TotalSize

        // Progress callback
        progress := float64(totalReceived) / float64(totalSize) * 100
        log.Printf("Download progress: %.2f%%", progress)
    }

    log.Printf("Download complete: %d bytes", totalReceived)
    return nil
}

// Client: Watch events with reconnection
func watchEvents(client pb.StreamingServiceClient, eventTypes []string) {
    for {
        ctx, cancel := context.WithCancel(context.Background())

        stream, err := client.WatchEvents(ctx, &pb.WatchRequest{
            EventTypes: eventTypes,
        })
        if err != nil {
            log.Printf("Failed to start watch: %v, retrying in 5s", err)
            cancel()
            time.Sleep(5 * time.Second)
            continue
        }

        log.Println("Watching for events...")

        for {
            event, err := stream.Recv()
            if err == io.EOF {
                log.Println("Stream ended")
                break
            }
            if err != nil {
                log.Printf("Stream error: %v", err)
                break
            }

            // Handle event
            log.Printf("Event received: type=%s, id=%s", event.Type, event.Id)
            handleEvent(event)
        }

        cancel()
        log.Println("Reconnecting in 5s...")
        time.Sleep(5 * time.Second)
    }
}
```

## Client Streaming Implementation

### Go Server

```go
// Client streaming: Upload file
func (s *server) UploadFile(stream pb.StreamingService_UploadFileServer) error {
    var filename string
    var totalSize int64
    var file *os.File
    var hash = sha256.New()

    for {
        chunk, err := stream.Recv()
        if err == io.EOF {
            // Client finished sending
            break
        }
        if err != nil {
            return status.Errorf(codes.Internal, "failed to receive chunk: %v", err)
        }

        // Initialize file on first chunk
        if file == nil {
            filename = chunk.Filename
            var err error
            file, err = os.Create(s.getUploadPath(filename))
            if err != nil {
                return status.Errorf(codes.Internal, "failed to create file: %v", err)
            }
            defer file.Close()
        }

        // Write chunk
        n, err := file.WriteAt(chunk.Content, chunk.Offset)
        if err != nil {
            return status.Errorf(codes.Internal, "failed to write chunk: %v", err)
        }

        hash.Write(chunk.Content)
        totalSize += int64(n)
    }

    // Generate file ID and checksum
    fileID := generateFileID()
    checksum := fmt.Sprintf("%x", hash.Sum(nil))

    // Send response
    return stream.SendAndClose(&pb.UploadResponse{
        FileId:   fileID,
        Size:     totalSize,
        Checksum: checksum,
    })
}

// Client streaming: Collect metrics
func (s *server) CollectMetrics(stream pb.StreamingService_CollectMetricsServer) error {
    var count int64
    aggregates := make(map[string]float64)

    for {
        metric, err := stream.Recv()
        if err == io.EOF {
            break
        }
        if err != nil {
            return err
        }

        // Process metric
        count++
        key := metric.Name
        if prev, exists := aggregates[key]; exists {
            aggregates[key] = prev + metric.Value
        } else {
            aggregates[key] = metric.Value
        }

        // Store metric asynchronously
        s.metricsStore.Store(metric)
    }

    // Return summary
    return stream.SendAndClose(&pb.MetricsSummary{
        TotalCount: count,
        Aggregates: aggregates,
    })
}
```

### Go Client

```go
// Client: Upload file in chunks
func uploadFile(client pb.StreamingServiceClient, filePath string) (*pb.UploadResponse, error) {
    ctx, cancel := context.WithTimeout(context.Background(), 10*time.Minute)
    defer cancel()

    // Open file
    file, err := os.Open(filePath)
    if err != nil {
        return nil, err
    }
    defer file.Close()

    info, err := file.Stat()
    if err != nil {
        return nil, err
    }

    // Start upload stream
    stream, err := client.UploadFile(ctx)
    if err != nil {
        return nil, err
    }

    // Send chunks
    chunkSize := 64 * 1024
    buffer := make([]byte, chunkSize)
    var offset int64

    for {
        n, err := file.Read(buffer)
        if err == io.EOF {
            break
        }
        if err != nil {
            return nil, err
        }

        chunk := &pb.FileChunk{
            Content:   buffer[:n],
            Offset:    offset,
            TotalSize: info.Size(),
            Filename:  info.Name(),
        }

        if err := stream.Send(chunk); err != nil {
            return nil, err
        }

        offset += int64(n)

        // Progress
        progress := float64(offset) / float64(info.Size()) * 100
        log.Printf("Upload progress: %.2f%%", progress)
    }

    // Close and receive response
    return stream.CloseAndRecv()
}

// Client: Send metrics stream
func sendMetrics(client pb.StreamingServiceClient, metrics <-chan *pb.Metric) (*pb.MetricsSummary, error) {
    ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
    defer cancel()

    stream, err := client.CollectMetrics(ctx)
    if err != nil {
        return nil, err
    }

    for metric := range metrics {
        if err := stream.Send(metric); err != nil {
            return nil, err
        }
    }

    return stream.CloseAndRecv()
}
```

## Bidirectional Streaming Implementation

### Go Server

```go
// Bidirectional streaming: Chat
func (s *server) Chat(stream pb.StreamingService_ChatServer) error {
    // Get user context
    ctx := stream.Context()
    userID, _ := getUserFromContext(ctx)

    // Create message channels
    incoming := make(chan *pb.ChatMessage, 100)
    outgoing := make(chan *pb.ChatMessage, 100)

    // Handle incoming messages
    go func() {
        defer close(incoming)
        for {
            msg, err := stream.Recv()
            if err == io.EOF {
                return
            }
            if err != nil {
                log.Printf("Receive error: %v", err)
                return
            }
            incoming <- msg
        }
    }()

    // Join room and get room channel
    roomCh := s.chatRooms.Join("general", userID)
    defer s.chatRooms.Leave("general", userID)

    for {
        select {
        case <-ctx.Done():
            return nil

        case msg := <-incoming:
            // Broadcast to room
            msg.UserId = userID
            msg.Timestamp = timestamppb.Now()
            s.chatRooms.Broadcast("general", msg)

        case msg := <-roomCh:
            // Send to this client
            if err := stream.Send(msg); err != nil {
                return err
            }
        }
    }
}

// Bidirectional streaming: Interactive query
func (s *server) InteractiveQuery(stream pb.StreamingService_InteractiveQueryServer) error {
    for {
        req, err := stream.Recv()
        if err == io.EOF {
            return nil
        }
        if err != nil {
            return err
        }

        // Process query and stream results
        results, err := s.queryEngine.Execute(stream.Context(), req.Query)
        if err != nil {
            // Send error response
            stream.Send(&pb.QueryResponse{
                Error: err.Error(),
            })
            continue
        }

        // Stream results
        for result := range results {
            if err := stream.Send(&pb.QueryResponse{
                Data: result,
            }); err != nil {
                return err
            }
        }

        // Send completion marker
        stream.Send(&pb.QueryResponse{
            Complete: true,
        })
    }
}
```

### Go Client

```go
// Client: Bidirectional chat
func chat(client pb.StreamingServiceClient, roomID string) error {
    ctx, cancel := context.WithCancel(context.Background())
    defer cancel()

    stream, err := client.Chat(ctx)
    if err != nil {
        return err
    }

    // Handle incoming messages
    go func() {
        for {
            msg, err := stream.Recv()
            if err == io.EOF {
                log.Println("Chat ended")
                return
            }
            if err != nil {
                log.Printf("Receive error: %v", err)
                cancel()
                return
            }

            fmt.Printf("[%s] %s: %s\n",
                msg.Timestamp.AsTime().Format("15:04:05"),
                msg.UserId,
                msg.Content,
            )
        }
    }()

    // Send messages from stdin
    scanner := bufio.NewScanner(os.Stdin)
    for scanner.Scan() {
        text := scanner.Text()
        if text == "/quit" {
            break
        }

        err := stream.Send(&pb.ChatMessage{
            RoomId:  roomID,
            Content: text,
        })
        if err != nil {
            return err
        }
    }

    return stream.CloseSend()
}

// Client: Interactive query session
func interactiveQuery(client pb.StreamingServiceClient) error {
    ctx, cancel := context.WithCancel(context.Background())
    defer cancel()

    stream, err := client.InteractiveQuery(ctx)
    if err != nil {
        return err
    }

    // Response handler
    responses := make(chan *pb.QueryResponse, 100)
    go func() {
        for {
            resp, err := stream.Recv()
            if err == io.EOF {
                close(responses)
                return
            }
            if err != nil {
                log.Printf("Receive error: %v", err)
                close(responses)
                return
            }
            responses <- resp
        }
    }()

    // Query loop
    scanner := bufio.NewScanner(os.Stdin)
    fmt.Print("> ")

    for scanner.Scan() {
        query := scanner.Text()
        if query == "exit" {
            break
        }

        // Send query
        err := stream.Send(&pb.QueryRequest{Query: query})
        if err != nil {
            return err
        }

        // Read results until complete
        for resp := range responses {
            if resp.Error != "" {
                fmt.Printf("Error: %s\n", resp.Error)
                break
            }
            if resp.Complete {
                break
            }
            fmt.Println(resp.Data)
        }

        fmt.Print("> ")
    }

    return stream.CloseSend()
}
```

## Node.js Implementation

### Server

```typescript
import * as grpc from '@grpc/grpc-js';
import { createReadStream, createWriteStream, statSync } from 'fs';

const streamingService = {
  // Server streaming
  downloadFile(call: grpc.ServerWritableStream<any, any>) {
    const { file_id: fileId } = call.request;
    const filePath = getFilePath(fileId);

    try {
      const stat = statSync(filePath);
      const stream = createReadStream(filePath, { highWaterMark: 64 * 1024 });
      let offset = 0;

      stream.on('data', (chunk: Buffer) => {
        call.write({
          content: chunk,
          offset,
          total_size: stat.size,
          filename: fileId,
        });
        offset += chunk.length;
      });

      stream.on('end', () => {
        call.end();
      });

      stream.on('error', (err) => {
        call.destroy(err);
      });
    } catch (err) {
      call.destroy({
        code: grpc.status.NOT_FOUND,
        message: `File ${fileId} not found`,
      } as any);
    }
  },

  // Client streaming
  uploadFile(
    call: grpc.ServerReadableStream<any, any>,
    callback: grpc.sendUnaryData<any>
  ) {
    let filename = '';
    let totalSize = 0;
    let writeStream: NodeJS.WritableStream | null = null;

    call.on('data', (chunk) => {
      if (!writeStream) {
        filename = chunk.filename;
        writeStream = createWriteStream(getUploadPath(filename));
      }
      writeStream.write(chunk.content);
      totalSize += chunk.content.length;
    });

    call.on('end', () => {
      if (writeStream) {
        writeStream.end();
      }
      callback(null, {
        file_id: generateFileId(),
        size: totalSize,
        checksum: calculateChecksum(filename),
      });
    });

    call.on('error', (err) => {
      callback(err);
    });
  },

  // Bidirectional streaming
  chat(call: grpc.ServerDuplexStream<any, any>) {
    const userId = getUserFromMetadata(call.metadata);

    call.on('data', (message) => {
      // Broadcast to all connected clients
      message.user_id = userId;
      message.timestamp = { seconds: Math.floor(Date.now() / 1000), nanos: 0 };

      broadcastToRoom(message.room_id, message);
    });

    // Subscribe to room messages
    const unsubscribe = subscribeToRoom('general', (message) => {
      call.write(message);
    });

    call.on('end', () => {
      unsubscribe();
      call.end();
    });

    call.on('error', () => {
      unsubscribe();
    });
  },
};
```

### Client

```typescript
import * as grpc from '@grpc/grpc-js';
import { createWriteStream } from 'fs';

// Server streaming client
async function downloadFile(
  client: any,
  fileId: string,
  outputPath: string
): Promise<void> {
  return new Promise((resolve, reject) => {
    const call = client.downloadFile({ file_id: fileId });
    const writeStream = createWriteStream(outputPath);
    let totalReceived = 0;

    call.on('data', (chunk: any) => {
      writeStream.write(chunk.content);
      totalReceived += chunk.content.length;

      const progress = (totalReceived / chunk.total_size) * 100;
      console.log(`Download progress: ${progress.toFixed(2)}%`);
    });

    call.on('end', () => {
      writeStream.end();
      console.log(`Download complete: ${totalReceived} bytes`);
      resolve();
    });

    call.on('error', (err: Error) => {
      writeStream.destroy();
      reject(err);
    });
  });
}

// Client streaming client
async function uploadFile(client: any, filePath: string): Promise<any> {
  return new Promise((resolve, reject) => {
    const call = client.uploadFile((err: any, response: any) => {
      if (err) reject(err);
      else resolve(response);
    });

    const readStream = createReadStream(filePath, { highWaterMark: 64 * 1024 });
    const stat = statSync(filePath);
    let offset = 0;

    readStream.on('data', (chunk: Buffer) => {
      call.write({
        content: chunk,
        offset,
        total_size: stat.size,
        filename: path.basename(filePath),
      });
      offset += chunk.length;
    });

    readStream.on('end', () => {
      call.end();
    });
  });
}

// Bidirectional streaming client
function chat(client: any, roomId: string): void {
  const call = client.chat();

  // Receive messages
  call.on('data', (message: any) => {
    console.log(`[${message.user_id}]: ${message.content}`);
  });

  call.on('end', () => {
    console.log('Chat ended');
  });

  // Send messages from readline
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  rl.on('line', (input) => {
    if (input === '/quit') {
      call.end();
      rl.close();
      return;
    }

    call.write({
      room_id: roomId,
      content: input,
    });
  });
}
```

## Flow Control and Backpressure

```go
// Server with flow control
func (s *server) StreamLargeData(req *pb.StreamRequest, stream pb.Service_StreamLargeDataServer) error {
    for i := 0; i < 1000000; i++ {
        // Check context for cancellation
        if err := stream.Context().Err(); err != nil {
            return status.FromContextError(err).Err()
        }

        data := &pb.DataItem{
            Id:   int64(i),
            Data: generateLargePayload(),
        }

        // Send will block if buffer is full (backpressure)
        if err := stream.Send(data); err != nil {
            return err
        }

        // Optional: Add small delay to prevent overwhelming
        if i%1000 == 0 {
            time.Sleep(time.Millisecond)
        }
    }
    return nil
}

// Client with flow control
func receiveWithFlowControl(stream pb.Service_StreamLargeDataClient) error {
    for {
        data, err := stream.Recv()
        if err == io.EOF {
            break
        }
        if err != nil {
            return err
        }

        // Process data (this naturally provides backpressure)
        if err := processData(data); err != nil {
            // Can cancel stream if processing fails
            return err
        }
    }
    return nil
}
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│                Streaming Best Practices                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Always Check Context                                        │
│     └── Handle cancellation and timeouts properly               │
│                                                                  │
│  2. Implement Backpressure                                      │
│     └── Don't overwhelm slow consumers                          │
│                                                                  │
│  3. Use Appropriate Chunk Sizes                                 │
│     └── 16KB-64KB for file transfers                            │
│                                                                  │
│  4. Handle Reconnection                                         │
│     └── Client should reconnect on stream errors                │
│                                                                  │
│  5. Clean Up Resources                                          │
│     └── Close files, channels on stream end                     │
│                                                                  │
│  6. Implement Heartbeats                                        │
│     └── Keep long-lived connections alive                       │
│                                                                  │
│  7. Use Deadlines Wisely                                        │
│     └── Longer timeouts for streaming operations                │
│                                                                  │
│  8. Log Stream Events                                           │
│     └── Track start, messages, errors, completion               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```
