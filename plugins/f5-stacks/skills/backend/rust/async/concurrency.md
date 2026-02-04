---
name: rust-concurrency
description: Concurrency patterns and parallel processing in Rust
applies_to: rust
---

# Concurrency Patterns in Rust

## Overview

Rust provides powerful concurrency primitives with compile-time safety guarantees.
This guide covers patterns for parallel processing, concurrent data structures,
and synchronization strategies.

## Parallel Iteration with Rayon

```toml
# Cargo.toml
[dependencies]
rayon = "1.8"
```

```rust
use rayon::prelude::*;

fn parallel_processing() {
    let numbers: Vec<i32> = (0..1000000).collect();

    // Parallel map
    let squares: Vec<i32> = numbers
        .par_iter()
        .map(|n| n * n)
        .collect();

    // Parallel filter
    let evens: Vec<i32> = numbers
        .par_iter()
        .filter(|n| *n % 2 == 0)
        .cloned()
        .collect();

    // Parallel reduce
    let sum: i32 = numbers
        .par_iter()
        .sum();

    // Parallel fold
    let product: i64 = numbers
        .par_iter()
        .map(|n| *n as i64)
        .fold(|| 1i64, |a, b| a * b)
        .reduce(|| 1, |a, b| a * b);
}

// Parallel chunks
fn process_in_chunks(data: &[u8]) -> Vec<u32> {
    data.par_chunks(1024)
        .map(|chunk| process_chunk(chunk))
        .collect()
}

// Custom parallel iterator
fn custom_parallel() {
    let data: Vec<Item> = load_items();

    data.into_par_iter()
        .for_each(|item| {
            process_item(item);
        });
}

// Parallel sort
fn parallel_sort(mut data: Vec<i32>) -> Vec<i32> {
    data.par_sort();
    data
}

// Parallel sort by key
fn parallel_sort_by_key(mut users: Vec<User>) -> Vec<User> {
    users.par_sort_by_key(|u| u.name.clone());
    users
}
```

## Thread Pool Management

```rust
use rayon::ThreadPoolBuilder;

fn custom_thread_pool() {
    // Create custom pool
    let pool = ThreadPoolBuilder::new()
        .num_threads(4)
        .thread_name(|i| format!("worker-{}", i))
        .build()
        .expect("Failed to create thread pool");

    // Use the pool
    pool.install(|| {
        let result: Vec<_> = (0..100)
            .into_par_iter()
            .map(|i| expensive_computation(i))
            .collect();

        println!("Processed {} items", result.len());
    });
}

// Scoped threads
use std::thread;

fn scoped_threads() {
    let data = vec![1, 2, 3, 4, 5];

    thread::scope(|s| {
        for item in &data {
            s.spawn(|| {
                println!("Processing: {}", item);
            });
        }
    });
    // All threads join here automatically
}
```

## Concurrent Data Structures

### DashMap (Concurrent HashMap)

```toml
[dependencies]
dashmap = "5"
```

```rust
use dashmap::DashMap;
use std::sync::Arc;

async fn concurrent_map() {
    let map: Arc<DashMap<String, i32>> = Arc::new(DashMap::new());

    let mut handles = vec![];

    // Concurrent writes
    for i in 0..10 {
        let map = Arc::clone(&map);
        handles.push(tokio::spawn(async move {
            map.insert(format!("key_{}", i), i);
        }));
    }

    // Concurrent reads
    for i in 0..10 {
        let map = Arc::clone(&map);
        handles.push(tokio::spawn(async move {
            if let Some(value) = map.get(&format!("key_{}", i)) {
                println!("Got: {}", *value);
            }
        }));
    }

    for handle in handles {
        handle.await.unwrap();
    }

    // Iterate
    for entry in map.iter() {
        println!("{}: {}", entry.key(), entry.value());
    }
}

// With entry API
fn dashmap_entry() {
    let map: DashMap<String, Vec<i32>> = DashMap::new();

    map.entry("key".to_string())
        .or_insert_with(Vec::new)
        .push(42);

    // Modify existing
    map.alter("key", |_, mut v| {
        v.push(43);
        v
    });
}
```

### Crossbeam Channel

```toml
[dependencies]
crossbeam-channel = "0.5"
```

```rust
use crossbeam_channel::{bounded, unbounded, select, Receiver, Sender};
use std::thread;

fn crossbeam_examples() {
    // Bounded channel
    let (tx, rx) = bounded::<i32>(10);

    // Unbounded channel
    let (tx_u, rx_u) = unbounded::<String>();

    // Producer-consumer
    thread::spawn(move || {
        for i in 0..100 {
            tx.send(i).expect("Send failed");
        }
    });

    for received in rx {
        println!("Got: {}", received);
    }
}

// Select over multiple channels
fn select_example() {
    let (tx1, rx1) = bounded::<i32>(1);
    let (tx2, rx2) = bounded::<i32>(1);

    thread::spawn(move || {
        tx1.send(1).unwrap();
    });
    thread::spawn(move || {
        tx2.send(2).unwrap();
    });

    crossbeam_channel::select! {
        recv(rx1) -> msg => println!("rx1: {:?}", msg),
        recv(rx2) -> msg => println!("rx2: {:?}", msg),
    }
}

// Timeout and try operations
fn timeout_example() {
    use std::time::Duration;

    let (tx, rx) = bounded::<i32>(1);

    // Try send (non-blocking)
    match tx.try_send(42) {
        Ok(()) => println!("Sent"),
        Err(e) => println!("Failed: {:?}", e),
    }

    // Receive with timeout
    match rx.recv_timeout(Duration::from_secs(5)) {
        Ok(val) => println!("Got: {}", val),
        Err(e) => println!("Timeout: {:?}", e),
    }
}
```

### Lock-Free Data Structures

```toml
[dependencies]
crossbeam-queue = "0.3"
crossbeam-deque = "0.8"
```

```rust
use crossbeam_queue::{ArrayQueue, SegQueue};
use crossbeam_deque::{Injector, Stealer, Worker};

// Lock-free bounded queue
fn array_queue_example() {
    let queue = ArrayQueue::new(100);

    queue.push(42).expect("Queue full");

    if let Some(value) = queue.pop() {
        println!("Got: {}", value);
    }
}

// Lock-free unbounded queue
fn seg_queue_example() {
    let queue = SegQueue::new();

    queue.push(1);
    queue.push(2);
    queue.push(3);

    while let Some(value) = queue.pop() {
        println!("Got: {}", value);
    }
}

// Work-stealing deque
fn work_stealing() {
    let injector = Injector::new();
    let workers: Vec<Worker<i32>> = (0..4).map(|_| Worker::new_fifo()).collect();
    let stealers: Vec<Stealer<i32>> = workers.iter().map(|w| w.stealer()).collect();

    // Inject tasks
    for i in 0..100 {
        injector.push(i);
    }

    // Workers steal from injector and each other
    std::thread::scope(|s| {
        for (id, worker) in workers.into_iter().enumerate() {
            let injector = &injector;
            let stealers = &stealers;

            s.spawn(move || {
                loop {
                    // Try local queue first
                    if let Some(task) = worker.pop() {
                        process_task(task);
                        continue;
                    }

                    // Try stealing from injector
                    if let crossbeam_deque::Steal::Success(task) = injector.steal() {
                        process_task(task);
                        continue;
                    }

                    // Try stealing from others
                    let stolen = stealers
                        .iter()
                        .enumerate()
                        .filter(|(i, _)| *i != id)
                        .find_map(|(_, s)| match s.steal() {
                            crossbeam_deque::Steal::Success(task) => Some(task),
                            _ => None,
                        });

                    if let Some(task) = stolen {
                        process_task(task);
                    } else {
                        break; // No more work
                    }
                }
            });
        }
    });
}
```

## Atomic Operations

```rust
use std::sync::atomic::{AtomicUsize, AtomicBool, Ordering};
use std::sync::Arc;

fn atomic_examples() {
    let counter = Arc::new(AtomicUsize::new(0));
    let running = Arc::new(AtomicBool::new(true));

    let mut handles = vec![];

    for _ in 0..10 {
        let counter = Arc::clone(&counter);
        let running = Arc::clone(&running);

        handles.push(std::thread::spawn(move || {
            while running.load(Ordering::Relaxed) {
                counter.fetch_add(1, Ordering::SeqCst);
                std::thread::sleep(std::time::Duration::from_millis(1));
            }
        }));
    }

    std::thread::sleep(std::time::Duration::from_secs(1));
    running.store(false, Ordering::SeqCst);

    for handle in handles {
        handle.join().unwrap();
    }

    println!("Final count: {}", counter.load(Ordering::SeqCst));
}

// Compare and swap
fn cas_example() {
    let value = AtomicUsize::new(5);

    // Only update if current value is 5
    let result = value.compare_exchange(
        5,              // expected
        10,             // new value
        Ordering::SeqCst,
        Ordering::Relaxed,
    );

    match result {
        Ok(old) => println!("Updated from {} to 10", old),
        Err(actual) => println!("Failed, actual value: {}", actual),
    }
}

// Atomic pointer
use std::sync::atomic::AtomicPtr;

fn atomic_ptr_example() {
    let data = Box::new(42);
    let ptr = AtomicPtr::new(Box::into_raw(data));

    // Swap atomically
    let old = ptr.swap(Box::into_raw(Box::new(100)), Ordering::SeqCst);

    // Clean up old value
    unsafe { drop(Box::from_raw(old)); }
}
```

## Concurrent Patterns

### Fan-Out/Fan-In

```rust
use tokio::sync::mpsc;

async fn fan_out_fan_in<T, R>(
    items: Vec<T>,
    worker_count: usize,
    process: impl Fn(T) -> R + Send + Sync + Clone + 'static,
) -> Vec<R>
where
    T: Send + 'static,
    R: Send + 'static,
{
    let (tx, mut rx) = mpsc::channel(worker_count * 2);
    let (result_tx, mut result_rx) = mpsc::channel(items.len());

    // Spawn workers
    for _ in 0..worker_count {
        let tx = result_tx.clone();
        let process = process.clone();

        tokio::spawn(async move {
            while let Some(item) = rx.recv().await {
                let result = process(item);
                let _ = tx.send(result).await;
            }
        });
    }

    drop(result_tx); // Close when workers done

    // Fan out items
    let item_count = items.len();
    for item in items {
        tx.send(item).await.expect("Send failed");
    }
    drop(tx);

    // Fan in results
    let mut results = Vec::with_capacity(item_count);
    while let Some(result) = result_rx.recv().await {
        results.push(result);
    }

    results
}
```

### Pipeline Pattern

```rust
use tokio::sync::mpsc;

async fn pipeline_example() {
    // Stage 1: Generate
    let (tx1, rx1) = mpsc::channel::<i32>(100);
    tokio::spawn(async move {
        for i in 0..1000 {
            tx1.send(i).await.unwrap();
        }
    });

    // Stage 2: Transform
    let (tx2, rx2) = mpsc::channel::<i32>(100);
    let mut rx1 = rx1;
    tokio::spawn(async move {
        while let Some(n) = rx1.recv().await {
            tx2.send(n * 2).await.unwrap();
        }
    });

    // Stage 3: Filter
    let (tx3, rx3) = mpsc::channel::<i32>(100);
    let mut rx2 = rx2;
    tokio::spawn(async move {
        while let Some(n) = rx2.recv().await {
            if n % 4 == 0 {
                tx3.send(n).await.unwrap();
            }
        }
    });

    // Collect results
    let mut rx3 = rx3;
    let mut results = vec![];
    while let Some(n) = rx3.recv().await {
        results.push(n);
    }

    println!("Processed {} items", results.len());
}
```

### Worker Pool

```rust
use std::sync::Arc;
use tokio::sync::{mpsc, Semaphore};

struct WorkerPool {
    semaphore: Arc<Semaphore>,
    sender: mpsc::Sender<BoxedTask>,
}

type BoxedTask = Box<dyn FnOnce() + Send + 'static>;

impl WorkerPool {
    fn new(size: usize) -> Self {
        let semaphore = Arc::new(Semaphore::new(size));
        let (sender, mut receiver) = mpsc::channel::<BoxedTask>(100);

        // Spawn worker manager
        tokio::spawn(async move {
            while let Some(task) = receiver.recv().await {
                task();
            }
        });

        Self { semaphore, sender }
    }

    async fn execute<F>(&self, f: F)
    where
        F: FnOnce() + Send + 'static,
    {
        let permit = self.semaphore.clone().acquire_owned().await.unwrap();
        let sender = self.sender.clone();

        tokio::spawn(async move {
            let _ = sender.send(Box::new(move || {
                f();
                drop(permit);
            })).await;
        });
    }
}
```

### Rate Limiter

```rust
use std::sync::Arc;
use tokio::sync::Semaphore;
use tokio::time::{interval, Duration};

struct RateLimiter {
    semaphore: Arc<Semaphore>,
}

impl RateLimiter {
    fn new(permits_per_second: usize) -> Self {
        let semaphore = Arc::new(Semaphore::new(permits_per_second));

        // Replenish permits
        let sem_clone = Arc::clone(&semaphore);
        tokio::spawn(async move {
            let mut interval = interval(Duration::from_secs(1));
            loop {
                interval.tick().await;
                sem_clone.add_permits(permits_per_second);
            }
        });

        Self { semaphore }
    }

    async fn acquire(&self) {
        self.semaphore.acquire().await.unwrap().forget();
    }
}

// Token bucket rate limiter
struct TokenBucket {
    tokens: Arc<tokio::sync::Mutex<f64>>,
    max_tokens: f64,
    refill_rate: f64, // tokens per second
}

impl TokenBucket {
    fn new(max_tokens: f64, refill_rate: f64) -> Self {
        let tokens = Arc::new(tokio::sync::Mutex::new(max_tokens));

        // Refill task
        let tokens_clone = Arc::clone(&tokens);
        tokio::spawn(async move {
            let mut interval = interval(Duration::from_millis(100));
            loop {
                interval.tick().await;
                let mut t = tokens_clone.lock().await;
                *t = (*t + refill_rate * 0.1).min(max_tokens);
            }
        });

        Self {
            tokens,
            max_tokens,
            refill_rate,
        }
    }

    async fn acquire(&self, tokens: f64) -> bool {
        let mut t = self.tokens.lock().await;
        if *t >= tokens {
            *t -= tokens;
            true
        } else {
            false
        }
    }
}
```

## Error Handling in Concurrent Code

```rust
use std::sync::Arc;
use tokio::sync::mpsc;

#[derive(Debug)]
struct TaskError {
    task_id: usize,
    error: String,
}

async fn concurrent_with_errors() -> Result<Vec<i32>, Vec<TaskError>> {
    let (result_tx, mut result_rx) = mpsc::channel::<Result<i32, TaskError>>(100);

    let tasks = vec![1, 2, 3, 4, 5];

    for (id, task) in tasks.into_iter().enumerate() {
        let tx = result_tx.clone();
        tokio::spawn(async move {
            let result = process_task(id, task).await;
            let _ = tx.send(result.map_err(|e| TaskError {
                task_id: id,
                error: e,
            })).await;
        });
    }

    drop(result_tx);

    let mut successes = vec![];
    let mut errors = vec![];

    while let Some(result) = result_rx.recv().await {
        match result {
            Ok(value) => successes.push(value),
            Err(err) => errors.push(err),
        }
    }

    if errors.is_empty() {
        Ok(successes)
    } else {
        Err(errors)
    }
}
```

## Best Practices

1. **Prefer message passing over shared state**: Use channels when possible
2. **Use Rayon for CPU-bound parallelism**: Data parallelism over task parallelism
3. **Limit concurrency**: Use semaphores to prevent resource exhaustion
4. **Handle errors gracefully**: Propagate errors from concurrent tasks
5. **Avoid deadlocks**: Always acquire locks in consistent order
6. **Use appropriate orderings**: SeqCst for safety, Relaxed for performance
7. **Benchmark**: Parallel isn't always faster for small workloads
8. **Test thoroughly**: Use loom or similar tools for concurrency testing
