---
name: laravel-queues
description: Queue and job patterns for background processing in Laravel
applies_to: laravel
category: performance
---

# Laravel Queues

## Overview

Queues allow deferring time-consuming tasks like sending emails, processing uploads, or generating reports to improve request response times.

## Creating Jobs

```bash
php artisan make:job ProcessOrder
php artisan make:job SendWelcomeEmail --sync
```

## Basic Job Structure

```php
<?php
// app/Jobs/ProcessOrder.php
namespace App\Jobs;

use App\Models\Order;
use App\Services\PaymentService;
use App\Services\InventoryService;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Bus\Dispatchable;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Queue\SerializesModels;

class ProcessOrder implements ShouldQueue
{
    use Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    /**
     * Number of times the job may be attempted.
     */
    public int $tries = 3;

    /**
     * Number of seconds to wait before retrying.
     */
    public int $backoff = 60;

    /**
     * The number of seconds the job can run before timing out.
     */
    public int $timeout = 120;

    /**
     * Create a new job instance.
     */
    public function __construct(
        public Order $order
    ) {}

    /**
     * Execute the job.
     */
    public function handle(
        PaymentService $paymentService,
        InventoryService $inventoryService
    ): void {
        // Process payment
        $paymentService->charge($this->order);

        // Update inventory
        $inventoryService->decrementStock($this->order->items);

        // Update order status
        $this->order->update(['status' => 'processing']);
    }

    /**
     * Handle a job failure.
     */
    public function failed(\Throwable $exception): void
    {
        $this->order->update(['status' => 'failed']);

        // Notify admin
        Notification::route('mail', config('app.admin_email'))
            ->notify(new OrderFailedNotification($this->order, $exception));
    }
}
```

## Dispatching Jobs

```php
<?php
use App\Jobs\ProcessOrder;

// Dispatch to default queue
ProcessOrder::dispatch($order);

// Dispatch to specific queue
ProcessOrder::dispatch($order)->onQueue('orders');

// Dispatch to specific connection
ProcessOrder::dispatch($order)->onConnection('redis');

// Delayed dispatch
ProcessOrder::dispatch($order)->delay(now()->addMinutes(10));

// Dispatch after response
ProcessOrder::dispatchAfterResponse($order);

// Conditional dispatch
ProcessOrder::dispatchIf($condition, $order);
ProcessOrder::dispatchUnless($condition, $order);

// Synchronous dispatch (for testing)
ProcessOrder::dispatchSync($order);
```

## Job Middleware

```php
<?php
// app/Jobs/Middleware/RateLimited.php
namespace App\Jobs\Middleware;

use Illuminate\Support\Facades\Redis;

class RateLimited
{
    public function __construct(
        protected string $key,
        protected int $maxAttempts = 10,
        protected int $decaySeconds = 60
    ) {}

    public function handle(object $job, callable $next): void
    {
        Redis::throttle($this->key)
            ->block(0)
            ->allow($this->maxAttempts)
            ->every($this->decaySeconds)
            ->then(function () use ($job, $next) {
                $next($job);
            }, function () use ($job) {
                $job->release($this->decaySeconds);
            });
    }
}

// app/Jobs/Middleware/WithoutOverlapping.php
namespace App\Jobs\Middleware;

use Illuminate\Contracts\Cache\Repository;

class WithoutOverlapping
{
    public function __construct(
        protected string $key,
        protected int $releaseAfter = 60
    ) {}

    public function handle(object $job, callable $next): void
    {
        $lock = app(Repository::class)->lock($this->key, $this->releaseAfter);

        if ($lock->get()) {
            try {
                $next($job);
            } finally {
                $lock->release();
            }
        } else {
            $job->release($this->releaseAfter);
        }
    }
}

// Using middleware in job
class ProcessOrder implements ShouldQueue
{
    public function middleware(): array
    {
        return [
            new RateLimited('orders', 100, 60),
            new WithoutOverlapping("order:{$this->order->id}"),
        ];
    }
}
```

## Job Batching

```php
<?php
use Illuminate\Bus\Batch;
use Illuminate\Support\Facades\Bus;

// Create a batch
$batch = Bus::batch([
    new ProcessOrder($order1),
    new ProcessOrder($order2),
    new ProcessOrder($order3),
])
->then(function (Batch $batch) {
    // All jobs completed successfully
    Log::info('Batch completed', ['id' => $batch->id]);
})
->catch(function (Batch $batch, \Throwable $e) {
    // First batch job failure detected
    Log::error('Batch failed', ['id' => $batch->id, 'error' => $e->getMessage()]);
})
->finally(function (Batch $batch) {
    // Batch has finished executing (success or failure)
})
->name('Process Orders')
->onQueue('orders')
->dispatch();

// Check batch status
$batch = Bus::findBatch($batchId);

$batch->id;
$batch->name;
$batch->totalJobs;
$batch->pendingJobs;
$batch->failedJobs;
$batch->processedJobs();
$batch->progress(); // Percentage
$batch->finished();
$batch->cancelled();
```

## Adding Jobs to Batch

```php
<?php
class ProcessOrder implements ShouldQueue, ShouldBeUnique
{
    use Batchable;

    public function handle(): void
    {
        if ($this->batch()->cancelled()) {
            return;
        }

        // Process order...

        // Add more jobs to the batch
        $this->batch()->add([
            new SendOrderConfirmation($this->order),
            new UpdateInventory($this->order),
        ]);
    }
}
```

## Job Chains

```php
<?php
use Illuminate\Support\Facades\Bus;

// Chain jobs (executed in sequence)
Bus::chain([
    new ValidateOrder($order),
    new ProcessPayment($order),
    new UpdateInventory($order),
    new SendConfirmation($order),
])
->onQueue('orders')
->catch(function (\Throwable $e) use ($order) {
    // Handle chain failure
    $order->update(['status' => 'failed']);
})
->dispatch();

// Alternative syntax
ProcessPayment::withChain([
    new UpdateInventory($order),
    new SendConfirmation($order),
])->dispatch($order);
```

## Unique Jobs

```php
<?php
use Illuminate\Contracts\Queue\ShouldBeUnique;
use Illuminate\Contracts\Queue\ShouldBeUniqueUntilProcessing;

class ProcessOrder implements ShouldQueue, ShouldBeUnique
{
    /**
     * The number of seconds after which the job's unique lock will be released.
     */
    public int $uniqueFor = 3600;

    /**
     * The unique ID of the job.
     */
    public function uniqueId(): string
    {
        return $this->order->id;
    }

    /**
     * Get the cache driver for unique job lock.
     */
    public function uniqueVia(): Repository
    {
        return Cache::driver('redis');
    }
}

// Unique until processing starts (allows requeue after start)
class ImportProducts implements ShouldQueue, ShouldBeUniqueUntilProcessing
{
    // Job can be queued again once processing begins
}
```

## Job Events

```php
<?php
// app/Providers/AppServiceProvider.php
use Illuminate\Queue\Events\JobFailed;
use Illuminate\Queue\Events\JobProcessed;
use Illuminate\Queue\Events\JobProcessing;
use Illuminate\Support\Facades\Queue;

public function boot(): void
{
    Queue::before(function (JobProcessing $event) {
        // Job is about to be processed
        Log::info('Processing job', [
            'connection' => $event->connectionName,
            'job' => $event->job->resolveName(),
        ]);
    });

    Queue::after(function (JobProcessed $event) {
        // Job processed successfully
        Log::info('Job processed', [
            'job' => $event->job->resolveName(),
        ]);
    });

    Queue::failing(function (JobFailed $event) {
        // Job failed
        Log::error('Job failed', [
            'job' => $event->job->resolveName(),
            'exception' => $event->exception->getMessage(),
        ]);
    });
}
```

## Queue Workers

```bash
# Start worker
php artisan queue:work

# Specific queue
php artisan queue:work --queue=high,default,low

# Process single job
php artisan queue:work --once

# Stop after queue is empty
php artisan queue:work --stop-when-empty

# Memory limit
php artisan queue:work --memory=256

# Timeout
php artisan queue:work --timeout=60

# Sleep duration when no jobs
php artisan queue:work --sleep=3

# Maximum jobs before restarting
php artisan queue:work --max-jobs=1000

# Maximum time before restarting
php artisan queue:work --max-time=3600
```

## Supervisor Configuration

```ini
; /etc/supervisor/conf.d/laravel-worker.conf
[program:laravel-worker]
process_name=%(program_name)s_%(process_num)02d
command=php /var/www/app/artisan queue:work redis --sleep=3 --tries=3 --max-time=3600
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
user=www-data
numprocs=8
redirect_stderr=true
stdout_logfile=/var/www/app/storage/logs/worker.log
stopwaitsecs=3600
```

## Failed Jobs

```php
<?php
// Retry failed job
php artisan queue:retry 5

// Retry all failed jobs
php artisan queue:retry all

// Delete failed job
php artisan queue:forget 5

// Flush all failed jobs
php artisan queue:flush

// In job class
public function failed(\Throwable $exception): void
{
    // Send notification
    Notification::route('slack', config('services.slack.webhook'))
        ->notify(new JobFailedNotification($this, $exception));

    // Log details
    Log::error('Job failed', [
        'job' => static::class,
        'data' => $this->order->toArray(),
        'exception' => $exception->getMessage(),
        'trace' => $exception->getTraceAsString(),
    ]);
}
```

## Horizon (Redis Dashboard)

```bash
# Install Horizon
composer require laravel/horizon

# Publish config
php artisan horizon:install

# Run Horizon
php artisan horizon

# Pause/Continue
php artisan horizon:pause
php artisan horizon:continue

# Terminate gracefully
php artisan horizon:terminate
```

```php
<?php
// config/horizon.php
'environments' => [
    'production' => [
        'supervisor-1' => [
            'maxProcesses' => 10,
            'balanceMaxShift' => 1,
            'balanceCooldown' => 3,
        ],
    ],

    'local' => [
        'supervisor-1' => [
            'maxProcesses' => 3,
        ],
    ],
],
```

## Testing Jobs

```php
<?php
use Illuminate\Support\Facades\Queue;

class OrderTest extends TestCase
{
    public function test_order_dispatches_processing_job(): void
    {
        Queue::fake();

        // Create order...
        $order = Order::factory()->create();
        $this->orderService->process($order);

        Queue::assertPushed(ProcessOrder::class, function ($job) use ($order) {
            return $job->order->id === $order->id;
        });
    }

    public function test_job_on_correct_queue(): void
    {
        Queue::fake();

        ProcessOrder::dispatch($order);

        Queue::assertPushedOn('orders', ProcessOrder::class);
    }

    public function test_job_chained(): void
    {
        Queue::fake();

        Bus::chain([
            new ProcessPayment($order),
            new UpdateInventory($order),
        ])->dispatch();

        Queue::assertChain([
            ProcessPayment::class,
            UpdateInventory::class,
        ]);
    }

    public function test_batch_dispatched(): void
    {
        Queue::fake();

        Bus::batch([
            new ProcessOrder($order1),
            new ProcessOrder($order2),
        ])->dispatch();

        Queue::assertBatched(function ($batch) {
            return $batch->jobs->count() === 2;
        });
    }

    public function test_job_handles_correctly(): void
    {
        $order = Order::factory()->create();
        $job = new ProcessOrder($order);

        $job->handle(
            app(PaymentService::class),
            app(InventoryService::class)
        );

        $this->assertEquals('processing', $order->fresh()->status);
    }
}
```

## Best Practices

1. **Keep Jobs Small**: Single responsibility, one task per job
2. **Handle Failures**: Implement `failed()` method for cleanup
3. **Set Timeouts**: Prevent runaway jobs with proper timeouts
4. **Use Retries**: Configure retry attempts with backoff
5. **Monitor Queues**: Use Horizon or monitoring tools
6. **Graceful Shutdown**: Handle signals for clean restarts
7. **Batch Large Operations**: Use batching for bulk processing
8. **Test Jobs**: Write tests for job logic and dispatch
