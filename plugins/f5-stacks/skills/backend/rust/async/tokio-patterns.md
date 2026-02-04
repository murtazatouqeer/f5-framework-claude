---
name: rust-tokio-patterns
description: Tokio async runtime patterns and best practices
applies_to: rust
---

# Tokio Patterns in Rust

## Overview

Tokio is Rust's most popular async runtime, providing:
- Async I/O primitives
- Task scheduling and spawning
- Synchronization primitives
- Timers and intervals

## Runtime Setup

```rust
// Cargo.toml
[dependencies]
tokio = { version = "1", features = ["full"] }

// For minimal:
tokio = { version = "1", features = ["rt-multi-thread", "macros", "net", "time", "sync"] }
```

### Basic Runtime

```rust
// Using the macro
#[tokio::main]
async fn main() {
    println!("Hello from Tokio!");
}

// With configuration
#[tokio::main(flavor = "multi_thread", worker_threads = 4)]
async fn main() {
    run_server().await;
}

// Single-threaded runtime
#[tokio::main(flavor = "current_thread")]
async fn main() {
    // Single-threaded execution
}

// Manual runtime construction
fn main() {
    let runtime = tokio::runtime::Builder::new_multi_thread()
        .worker_threads(4)
        .enable_all()
        .build()
        .expect("Failed to create runtime");

    runtime.block_on(async {
        run_server().await;
    });
}
```

## Task Spawning

```rust
use tokio::task::{self, JoinHandle};

// Spawn a task
async fn spawn_example() {
    let handle: JoinHandle<i32> = tokio::spawn(async {
        // Task work
        42
    });

    // Wait for result
    let result = handle.await.expect("Task panicked");
    println!("Result: {}", result);
}

// Spawn multiple tasks
async fn spawn_many() {
    let mut handles = Vec::new();

    for i in 0..10 {
        let handle = tokio::spawn(async move {
            process_item(i).await
        });
        handles.push(handle);
    }

    // Wait for all
    for handle in handles {
        let result = handle.await.expect("Task failed");
        println!("Completed: {:?}", result);
    }
}

// Using JoinSet for better management
use tokio::task::JoinSet;

async fn spawn_with_joinset() {
    let mut set = JoinSet::new();

    for i in 0..10 {
        set.spawn(async move {
            process_item(i).await
        });
    }

    while let Some(result) = set.join_next().await {
        match result {
            Ok(value) => println!("Got: {:?}", value),
            Err(e) => eprintln!("Task failed: {:?}", e),
        }
    }
}

// Spawn blocking (for CPU-bound work)
async fn spawn_blocking_example() {
    let result = task::spawn_blocking(|| {
        // Expensive computation that would block
        heavy_computation()
    }).await.expect("Blocking task failed");

    println!("Computation result: {:?}", result);
}
```

## Channels

### MPSC (Multi-producer, single-consumer)

```rust
use tokio::sync::mpsc;

async fn mpsc_example() {
    // Bounded channel
    let (tx, mut rx) = mpsc::channel::<String>(100);

    // Producer
    let producer = tokio::spawn(async move {
        for i in 0..10 {
            tx.send(format!("Message {}", i)).await.expect("Send failed");
        }
    });

    // Consumer
    let consumer = tokio::spawn(async move {
        while let Some(msg) = rx.recv().await {
            println!("Received: {}", msg);
        }
    });

    producer.await.unwrap();
    consumer.await.unwrap();
}

// Unbounded channel (use with caution)
async fn unbounded_example() {
    let (tx, mut rx) = mpsc::unbounded_channel::<i32>();

    tx.send(1).expect("Send failed");
    tx.send(2).expect("Send failed");

    while let Some(value) = rx.recv().await {
        println!("Got: {}", value);
    }
}
```

### Oneshot (Single value)

```rust
use tokio::sync::oneshot;

async fn oneshot_example() {
    let (tx, rx) = oneshot::channel::<String>();

    tokio::spawn(async move {
        // Simulate work
        tokio::time::sleep(tokio::time::Duration::from_secs(1)).await;
        tx.send("Done!".to_string()).expect("Send failed");
    });

    // Wait for response
    let result = rx.await.expect("Receiver dropped");
    println!("Received: {}", result);
}

// Request-response pattern
async fn request_response() {
    struct Request {
        data: String,
        response_tx: oneshot::Sender<String>,
    }

    let (tx, mut rx) = mpsc::channel::<Request>(10);

    // Processor
    tokio::spawn(async move {
        while let Some(req) = rx.recv().await {
            let response = format!("Processed: {}", req.data);
            let _ = req.response_tx.send(response);
        }
    });

    // Send request and wait for response
    let (resp_tx, resp_rx) = oneshot::channel();
    tx.send(Request {
        data: "Hello".to_string(),
        response_tx: resp_tx,
    }).await.expect("Send failed");

    let response = resp_rx.await.expect("No response");
    println!("Response: {}", response);
}
```

### Broadcast (Multi-consumer)

```rust
use tokio::sync::broadcast;

async fn broadcast_example() {
    let (tx, mut rx1) = broadcast::channel::<String>(16);
    let mut rx2 = tx.subscribe();

    tokio::spawn(async move {
        tx.send("Hello everyone!".to_string()).expect("Send failed");
    });

    // Multiple receivers
    let h1 = tokio::spawn(async move {
        let msg = rx1.recv().await.expect("Recv failed");
        println!("Receiver 1: {}", msg);
    });

    let h2 = tokio::spawn(async move {
        let msg = rx2.recv().await.expect("Recv failed");
        println!("Receiver 2: {}", msg);
    });

    h1.await.unwrap();
    h2.await.unwrap();
}
```

### Watch (Latest value)

```rust
use tokio::sync::watch;

async fn watch_example() {
    let (tx, mut rx) = watch::channel("initial");

    tokio::spawn(async move {
        tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;
        tx.send("updated").expect("Send failed");
    });

    // Get current value
    println!("Current: {}", *rx.borrow());

    // Wait for change
    rx.changed().await.expect("Sender dropped");
    println!("Changed to: {}", *rx.borrow());
}
```

## Synchronization Primitives

### Mutex

```rust
use tokio::sync::Mutex;
use std::sync::Arc;

async fn mutex_example() {
    let data = Arc::new(Mutex::new(0));

    let mut handles = vec![];

    for _ in 0..10 {
        let data = Arc::clone(&data);
        handles.push(tokio::spawn(async move {
            let mut lock = data.lock().await;
            *lock += 1;
        }));
    }

    for handle in handles {
        handle.await.unwrap();
    }

    println!("Final value: {}", *data.lock().await);
}

// With timeout
use tokio::time::{timeout, Duration};

async fn mutex_with_timeout() {
    let data = Arc::new(Mutex::new(0));

    match timeout(Duration::from_secs(5), data.lock()).await {
        Ok(guard) => {
            println!("Got lock: {}", *guard);
        }
        Err(_) => {
            eprintln!("Timeout waiting for lock");
        }
    }
}
```

### RwLock

```rust
use tokio::sync::RwLock;
use std::sync::Arc;

async fn rwlock_example() {
    let data = Arc::new(RwLock::new(vec![1, 2, 3]));

    // Multiple readers
    let readers: Vec<_> = (0..3).map(|i| {
        let data = Arc::clone(&data);
        tokio::spawn(async move {
            let read = data.read().await;
            println!("Reader {}: {:?}", i, *read);
        })
    }).collect();

    // Single writer
    let data_writer = Arc::clone(&data);
    let writer = tokio::spawn(async move {
        let mut write = data_writer.write().await;
        write.push(4);
        println!("Writer added 4");
    });

    for r in readers {
        r.await.unwrap();
    }
    writer.await.unwrap();
}
```

### Semaphore

```rust
use tokio::sync::Semaphore;
use std::sync::Arc;

async fn semaphore_example() {
    // Limit concurrent operations to 3
    let semaphore = Arc::new(Semaphore::new(3));

    let mut handles = vec![];

    for i in 0..10 {
        let permit = semaphore.clone().acquire_owned().await.unwrap();
        handles.push(tokio::spawn(async move {
            println!("Task {} started", i);
            tokio::time::sleep(Duration::from_millis(100)).await;
            println!("Task {} completed", i);
            drop(permit); // Release permit
        }));
    }

    for handle in handles {
        handle.await.unwrap();
    }
}

// Connection pool pattern
struct ConnectionPool {
    semaphore: Semaphore,
}

impl ConnectionPool {
    fn new(max_connections: usize) -> Self {
        Self {
            semaphore: Semaphore::new(max_connections),
        }
    }

    async fn get_connection(&self) -> PooledConnection<'_> {
        let permit = self.semaphore.acquire().await.unwrap();
        PooledConnection { _permit: permit }
    }
}

struct PooledConnection<'a> {
    _permit: tokio::sync::SemaphorePermit<'a>,
}
```

## Timers and Intervals

```rust
use tokio::time::{sleep, interval, timeout, Duration, Instant};

async fn timer_examples() {
    // Sleep
    sleep(Duration::from_secs(1)).await;
    println!("Slept for 1 second");

    // Interval
    let mut interval = interval(Duration::from_millis(100));
    for _ in 0..5 {
        interval.tick().await;
        println!("Tick at {:?}", Instant::now());
    }

    // Timeout
    let result = timeout(Duration::from_secs(5), async {
        // Long operation
        sleep(Duration::from_secs(1)).await;
        "Completed"
    }).await;

    match result {
        Ok(value) => println!("Got: {}", value),
        Err(_) => println!("Timed out"),
    }
}

// Periodic task
async fn periodic_task() {
    let mut interval = interval(Duration::from_secs(60));

    loop {
        interval.tick().await;

        if let Err(e) = do_periodic_work().await {
            eprintln!("Periodic work failed: {:?}", e);
        }
    }
}
```

## Select and Race

```rust
use tokio::select;

async fn select_example() {
    let (tx1, mut rx1) = mpsc::channel::<i32>(10);
    let (tx2, mut rx2) = mpsc::channel::<i32>(10);

    // Wait for first message from either channel
    select! {
        Some(val) = rx1.recv() => {
            println!("Got from rx1: {}", val);
        }
        Some(val) = rx2.recv() => {
            println!("Got from rx2: {}", val);
        }
    }
}

// With timeout
async fn select_with_timeout() {
    let mut rx = get_receiver();

    loop {
        select! {
            Some(msg) = rx.recv() => {
                handle_message(msg).await;
            }
            _ = sleep(Duration::from_secs(30)) => {
                println!("No message for 30 seconds");
                send_heartbeat().await;
            }
        }
    }
}

// Graceful shutdown pattern
async fn graceful_shutdown() {
    let (shutdown_tx, mut shutdown_rx) = broadcast::channel::<()>(1);

    let server = tokio::spawn(async move {
        loop {
            select! {
                _ = handle_request() => {}
                _ = shutdown_rx.recv() => {
                    println!("Shutting down...");
                    break;
                }
            }
        }
    });

    // Wait for shutdown signal (e.g., Ctrl+C)
    tokio::signal::ctrl_c().await.expect("Failed to listen for ctrl-c");

    let _ = shutdown_tx.send(());
    server.await.unwrap();
}
```

## Streams

```rust
use tokio_stream::{self as stream, StreamExt};

async fn stream_examples() {
    // Create stream from iterator
    let mut stream = stream::iter(vec![1, 2, 3, 4, 5]);

    while let Some(value) = stream.next().await {
        println!("Got: {}", value);
    }

    // Stream with interval
    let interval = tokio::time::interval(Duration::from_millis(100));
    let mut stream = tokio_stream::wrappers::IntervalStream::new(interval);

    for _ in 0..5 {
        stream.next().await;
        println!("Tick");
    }
}

// Custom stream
use std::pin::Pin;
use std::task::{Context, Poll};
use futures::Stream;

struct CounterStream {
    count: u32,
    max: u32,
}

impl Stream for CounterStream {
    type Item = u32;

    fn poll_next(mut self: Pin<&mut Self>, _cx: &mut Context<'_>) -> Poll<Option<Self::Item>> {
        if self.count < self.max {
            self.count += 1;
            Poll::Ready(Some(self.count))
        } else {
            Poll::Ready(None)
        }
    }
}
```

## I/O Operations

```rust
use tokio::io::{self, AsyncReadExt, AsyncWriteExt, BufReader, BufWriter};
use tokio::fs::File;
use tokio::net::TcpStream;

async fn io_examples() -> io::Result<()> {
    // File read
    let mut file = File::open("input.txt").await?;
    let mut contents = String::new();
    file.read_to_string(&mut contents).await?;

    // File write
    let mut file = File::create("output.txt").await?;
    file.write_all(b"Hello, world!").await?;

    // Buffered I/O
    let file = File::open("large.txt").await?;
    let mut reader = BufReader::new(file);
    let mut line = String::new();
    reader.read_line(&mut line).await?;

    Ok(())
}

// TCP client
async fn tcp_client() -> io::Result<()> {
    let mut stream = TcpStream::connect("127.0.0.1:8080").await?;

    stream.write_all(b"Hello").await?;

    let mut buf = [0; 1024];
    let n = stream.read(&mut buf).await?;
    println!("Received: {}", String::from_utf8_lossy(&buf[..n]));

    Ok(())
}

// TCP server
async fn tcp_server() -> io::Result<()> {
    let listener = tokio::net::TcpListener::bind("127.0.0.1:8080").await?;

    loop {
        let (socket, addr) = listener.accept().await?;
        println!("New connection from: {}", addr);

        tokio::spawn(async move {
            handle_connection(socket).await;
        });
    }
}
```

## Best Practices

1. **Use spawn_blocking for CPU-bound work**: Keep async tasks non-blocking
2. **Prefer bounded channels**: Prevent unbounded memory growth
3. **Use JoinSet for task management**: Better control over spawned tasks
4. **Graceful shutdown**: Handle shutdown signals properly
5. **Timeout everything**: Add timeouts to external operations
6. **Avoid holding locks across await points**: Use std::sync for quick operations
7. **Use structured concurrency**: Manage task lifetimes explicitly
