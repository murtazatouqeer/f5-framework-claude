---
name: laravel-exception-handling
description: Exception handling patterns in Laravel
applies_to: laravel
category: error-handling
---

# Laravel Exception Handling

## Exception Handler Configuration

```php
<?php
// app/Exceptions/Handler.php (Laravel 10)
namespace App\Exceptions;

use Illuminate\Foundation\Exceptions\Handler as ExceptionHandler;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Validation\ValidationException;
use Symfony\Component\HttpKernel\Exception\HttpException;
use Throwable;

class Handler extends ExceptionHandler
{
    /**
     * A list of exception types with their corresponding custom log levels.
     */
    protected $levels = [
        // \PDOException::class => LogLevel::CRITICAL,
    ];

    /**
     * A list of the exception types that are not reported.
     */
    protected $dontReport = [
        // \App\Exceptions\BusinessException::class,
    ];

    /**
     * A list of the inputs that are never flashed for validation exceptions.
     */
    protected $dontFlash = [
        'current_password',
        'password',
        'password_confirmation',
    ];

    /**
     * Register the exception handling callbacks for the application.
     */
    public function register(): void
    {
        $this->reportable(function (Throwable $e) {
            // Report to external service (Sentry, Bugsnag, etc.)
            if (app()->bound('sentry')) {
                app('sentry')->captureException($e);
            }
        });

        // Custom rendering for specific exceptions
        $this->renderable(function (ModelNotFoundException $e, Request $request) {
            if ($request->wantsJson()) {
                return response()->json([
                    'message' => 'Resource not found',
                ], 404);
            }
        });

        $this->renderable(function (AuthorizationException $e, Request $request) {
            if ($request->wantsJson()) {
                return response()->json([
                    'message' => $e->getMessage() ?: 'You are not authorized to perform this action.',
                ], 403);
            }
        });
    }

    /**
     * Render an exception into an HTTP response.
     */
    public function render($request, Throwable $e): JsonResponse|\Illuminate\Http\Response
    {
        if ($request->wantsJson()) {
            return $this->handleApiException($request, $e);
        }

        return parent::render($request, $e);
    }

    /**
     * Handle API exceptions.
     */
    protected function handleApiException(Request $request, Throwable $e): JsonResponse
    {
        $response = [
            'success' => false,
            'message' => $e->getMessage() ?: 'An error occurred',
        ];

        if (config('app.debug')) {
            $response['debug'] = [
                'exception' => get_class($e),
                'file' => $e->getFile(),
                'line' => $e->getLine(),
                'trace' => collect($e->getTrace())->take(5)->toArray(),
            ];
        }

        $statusCode = $this->getStatusCode($e);

        return response()->json($response, $statusCode);
    }

    /**
     * Get HTTP status code for exception.
     */
    protected function getStatusCode(Throwable $e): int
    {
        if ($e instanceof HttpException) {
            return $e->getStatusCode();
        }

        if ($e instanceof ValidationException) {
            return 422;
        }

        if ($e instanceof AuthenticationException) {
            return 401;
        }

        if ($e instanceof AuthorizationException) {
            return 403;
        }

        if ($e instanceof ModelNotFoundException) {
            return 404;
        }

        return 500;
    }
}
```

## Laravel 11 Exception Handler

```php
<?php
// bootstrap/app.php (Laravel 11)
use Illuminate\Foundation\Application;
use Illuminate\Foundation\Configuration\Exceptions;
use Illuminate\Foundation\Configuration\Middleware;

return Application::configure(basePath: dirname(__DIR__))
    ->withRouting(
        web: __DIR__.'/../routes/web.php',
        api: __DIR__.'/../routes/api.php',
    )
    ->withMiddleware(function (Middleware $middleware) {
        //
    })
    ->withExceptions(function (Exceptions $exceptions) {
        // Don't report certain exceptions
        $exceptions->dontReport([
            \App\Exceptions\BusinessException::class,
        ]);

        // Custom rendering
        $exceptions->render(function (ModelNotFoundException $e, Request $request) {
            if ($request->wantsJson()) {
                return response()->json(['message' => 'Resource not found'], 404);
            }
        });

        // Report to external service
        $exceptions->report(function (Throwable $e) {
            if (app()->bound('sentry')) {
                app('sentry')->captureException($e);
            }
        });
    })
    ->create();
```

## Custom Exception Classes

```php
<?php
// app/Exceptions/BusinessException.php
namespace App\Exceptions;

use Exception;

class BusinessException extends Exception
{
    protected string $errorCode;
    protected array $context;

    public function __construct(
        string $message,
        string $errorCode = 'BUSINESS_ERROR',
        array $context = [],
        int $code = 422,
        ?Exception $previous = null
    ) {
        parent::__construct($message, $code, $previous);
        $this->errorCode = $errorCode;
        $this->context = $context;
    }

    public function getErrorCode(): string
    {
        return $this->errorCode;
    }

    public function getContext(): array
    {
        return $this->context;
    }

    /**
     * Render the exception as an HTTP response.
     */
    public function render(Request $request): JsonResponse
    {
        return response()->json([
            'success' => false,
            'message' => $this->getMessage(),
            'error_code' => $this->errorCode,
            'context' => $this->context,
        ], $this->getCode());
    }

    /**
     * Report the exception.
     */
    public function report(): bool
    {
        // Return false to skip default reporting
        return false;
    }
}

// app/Exceptions/ResourceNotFoundException.php
namespace App\Exceptions;

class ResourceNotFoundException extends BusinessException
{
    public function __construct(string $resource, string|int $id)
    {
        parent::__construct(
            message: "{$resource} with ID {$id} not found",
            errorCode: 'RESOURCE_NOT_FOUND',
            context: ['resource' => $resource, 'id' => $id],
            code: 404
        );
    }
}

// app/Exceptions/InsufficientBalanceException.php
namespace App\Exceptions;

class InsufficientBalanceException extends BusinessException
{
    public function __construct(float $required, float $available)
    {
        parent::__construct(
            message: "Insufficient balance. Required: {$required}, Available: {$available}",
            errorCode: 'INSUFFICIENT_BALANCE',
            context: ['required' => $required, 'available' => $available],
            code: 422
        );
    }
}

// app/Exceptions/InvalidStateTransitionException.php
namespace App\Exceptions;

class InvalidStateTransitionException extends BusinessException
{
    public function __construct(string $entity, string $from, string $to)
    {
        parent::__construct(
            message: "Cannot transition {$entity} from '{$from}' to '{$to}'",
            errorCode: 'INVALID_STATE_TRANSITION',
            context: ['entity' => $entity, 'from' => $from, 'to' => $to],
            code: 422
        );
    }
}
```

## Using Custom Exceptions

```php
<?php
// In Service
class OrderService
{
    public function cancel(Order $order): void
    {
        if ($order->status !== 'pending') {
            throw new InvalidStateTransitionException(
                entity: 'Order',
                from: $order->status,
                to: 'cancelled'
            );
        }

        // Cancel order...
    }

    public function processPayment(Order $order): void
    {
        $user = $order->user;
        $total = $order->total;

        if ($user->balance < $total) {
            throw new InsufficientBalanceException(
                required: $total,
                available: $user->balance
            );
        }

        // Process payment...
    }
}

// In Controller
public function cancel(Order $order): JsonResponse
{
    try {
        $this->orderService->cancel($order);
        return response()->json(['message' => 'Order cancelled']);
    } catch (InvalidStateTransitionException $e) {
        // Exception will auto-render via render() method
        throw $e;
    }
}
```

## Contextual Exception Logging

```php
<?php
// app/Exceptions/Handler.php
public function register(): void
{
    $this->reportable(function (Throwable $e) {
        // Add context to all exceptions
        $this->context([
            'user_id' => auth()->id(),
            'url' => request()->fullUrl(),
            'method' => request()->method(),
            'ip' => request()->ip(),
        ]);
    });

    $this->reportable(function (BusinessException $e) {
        // Add business exception context
        Log::channel('business')->error($e->getMessage(), [
            'error_code' => $e->getErrorCode(),
            'context' => $e->getContext(),
            'user_id' => auth()->id(),
        ]);

        return false; // Skip default reporting
    });
}
```

## Exception Testing

```php
<?php
// tests/Feature/ExceptionTest.php
class ExceptionTest extends TestCase
{
    public function test_not_found_returns_404(): void
    {
        $response = $this->getJson('/api/products/non-existent-id');

        $response
            ->assertNotFound()
            ->assertJson(['message' => 'Resource not found']);
    }

    public function test_validation_returns_422(): void
    {
        $this->actingAs(User::factory()->create());

        $response = $this->postJson('/api/products', []);

        $response
            ->assertUnprocessable()
            ->assertJsonValidationErrors(['name', 'price']);
    }

    public function test_unauthorized_returns_401(): void
    {
        $response = $this->getJson('/api/products');

        $response->assertUnauthorized();
    }

    public function test_forbidden_returns_403(): void
    {
        $user = User::factory()->create();
        $product = Product::factory()->create(); // Owned by different user

        $this->actingAs($user);

        $response = $this->deleteJson("/api/products/{$product->id}");

        $response->assertForbidden();
    }
}
```

## Best Practices

1. **Custom Exceptions**: Create domain-specific exceptions
2. **Error Codes**: Use consistent error codes for API responses
3. **Context**: Include relevant context in exceptions
4. **Render Method**: Let exceptions render themselves
5. **Report Control**: Control what gets logged
6. **Test Exceptions**: Test exception responses
