---
name: laravel-custom-rules
description: Creating custom validation rules in Laravel
applies_to: laravel
category: validation
---

# Laravel Custom Validation Rules

## Creating Custom Rules

```bash
php artisan make:rule ValidSlug
php artisan make:rule UniqueInTenant --implicit
```

## Object-Based Rule

```php
<?php
// app/Rules/ValidSlug.php
namespace App\Rules;

use Closure;
use Illuminate\Contracts\Validation\ValidationRule;

class ValidSlug implements ValidationRule
{
    /**
     * Run the validation rule.
     */
    public function validate(string $attribute, mixed $value, Closure $fail): void
    {
        // Check format
        if (!preg_match('/^[a-z0-9]+(?:-[a-z0-9]+)*$/', $value)) {
            $fail('The :attribute must be a valid slug (lowercase letters, numbers, and hyphens only).');
            return;
        }

        // Check length
        if (strlen($value) < 3 || strlen($value) > 100) {
            $fail('The :attribute must be between 3 and 100 characters.');
            return;
        }

        // Check reserved words
        $reserved = ['admin', 'api', 'auth', 'login', 'logout'];
        if (in_array($value, $reserved)) {
            $fail('The :attribute cannot be a reserved word.');
        }
    }
}

// Usage
public function rules(): array
{
    return [
        'slug' => ['required', 'string', new ValidSlug],
    ];
}
```

## Rule with Constructor Parameters

```php
<?php
// app/Rules/UniqueInTenant.php
namespace App\Rules;

use Closure;
use Illuminate\Contracts\Validation\ValidationRule;
use Illuminate\Support\Facades\DB;

class UniqueInTenant implements ValidationRule
{
    public function __construct(
        protected string $table,
        protected string $column = 'id',
        protected ?string $ignoreId = null
    ) {}

    public function validate(string $attribute, mixed $value, Closure $fail): void
    {
        $query = DB::table($this->table)
            ->where($this->column, $value)
            ->where('tenant_id', auth()->user()->tenant_id);

        if ($this->ignoreId) {
            $query->where('id', '!=', $this->ignoreId);
        }

        if ($query->exists()) {
            $fail("The :attribute has already been taken in your organization.");
        }
    }
}

// Usage
public function rules(): array
{
    return [
        'email' => [
            'required',
            'email',
            new UniqueInTenant('users', 'email', $this->route('user')?->id),
        ],
    ];
}
```

## Data Aware Rule

```php
<?php
// app/Rules/ValidPriceRange.php
namespace App\Rules;

use Closure;
use Illuminate\Contracts\Validation\DataAwareRule;
use Illuminate\Contracts\Validation\ValidationRule;

class ValidPriceRange implements DataAwareRule, ValidationRule
{
    protected array $data = [];

    public function setData(array $data): static
    {
        $this->data = $data;
        return $this;
    }

    public function validate(string $attribute, mixed $value, Closure $fail): void
    {
        $minPrice = $this->data['min_price'] ?? null;
        $maxPrice = $this->data['max_price'] ?? null;

        if ($minPrice && $maxPrice && $minPrice > $maxPrice) {
            $fail('The minimum price must be less than or equal to the maximum price.');
        }

        if ($value < ($minPrice ?? 0)) {
            $fail('The :attribute must be at least :min.', ['min' => $minPrice]);
        }

        if ($maxPrice && $value > $maxPrice) {
            $fail('The :attribute must not exceed :max.', ['max' => $maxPrice]);
        }
    }
}
```

## Validator Aware Rule

```php
<?php
// app/Rules/PasswordHistory.php
namespace App\Rules;

use Closure;
use Illuminate\Contracts\Validation\ValidatorAwareRule;
use Illuminate\Contracts\Validation\ValidationRule;
use Illuminate\Support\Facades\Hash;
use Illuminate\Validation\Validator;

class PasswordHistory implements ValidatorAwareRule, ValidationRule
{
    protected Validator $validator;
    protected int $count;

    public function __construct(int $count = 5)
    {
        $this->count = $count;
    }

    public function setValidator(Validator $validator): static
    {
        $this->validator = $validator;
        return $this;
    }

    public function validate(string $attribute, mixed $value, Closure $fail): void
    {
        $user = auth()->user();

        if (!$user) {
            return;
        }

        $recentPasswords = $user->passwordHistory()
            ->latest()
            ->take($this->count)
            ->pluck('password');

        foreach ($recentPasswords as $oldPassword) {
            if (Hash::check($value, $oldPassword)) {
                $fail("You cannot reuse your last {$this->count} passwords.");
                return;
            }
        }
    }
}
```

## Implicit Rule (Validates Even If Empty)

```php
<?php
// app/Rules/RequiredIfSibling.php
namespace App\Rules;

use Closure;
use Illuminate\Contracts\Validation\DataAwareRule;
use Illuminate\Contracts\Validation\ValidationRule;

class RequiredIfSibling implements DataAwareRule, ValidationRule
{
    protected array $data = [];

    public function __construct(
        protected string $siblingField,
        protected mixed $siblingValue = null
    ) {}

    public function setData(array $data): static
    {
        $this->data = $data;
        return $this;
    }

    public function validate(string $attribute, mixed $value, Closure $fail): void
    {
        $siblingActualValue = data_get($this->data, $this->siblingField);

        $shouldBeRequired = $this->siblingValue === null
            ? !empty($siblingActualValue)
            : $siblingActualValue == $this->siblingValue;

        if ($shouldBeRequired && empty($value)) {
            $fail("The :attribute field is required.");
        }
    }
}
```

## Closure-Based Rules

```php
<?php
public function rules(): array
{
    return [
        'username' => [
            'required',
            'string',
            function (string $attribute, mixed $value, Closure $fail) {
                // Custom inline validation
                if (str_starts_with($value, 'admin')) {
                    $fail("The {$attribute} cannot start with 'admin'.");
                }

                if (preg_match('/[^a-z0-9_]/', $value)) {
                    $fail("The {$attribute} can only contain lowercase letters, numbers, and underscores.");
                }
            },
        ],
    ];
}
```

## Extending Validator

```php
<?php
// app/Providers/AppServiceProvider.php
use Illuminate\Support\Facades\Validator;

public function boot(): void
{
    // Simple extension
    Validator::extend('phone', function ($attribute, $value, $parameters, $validator) {
        return preg_match('/^[0-9]{10,15}$/', preg_replace('/[\s\-\(\)]/', '', $value));
    });

    Validator::replacer('phone', function ($message, $attribute, $rule, $parameters) {
        return str_replace(':attribute', $attribute, 'The :attribute must be a valid phone number.');
    });

    // Extension with parameters
    Validator::extend('max_words', function ($attribute, $value, $parameters, $validator) {
        $maxWords = (int) ($parameters[0] ?? 100);
        $wordCount = str_word_count($value);
        return $wordCount <= $maxWords;
    });

    Validator::replacer('max_words', function ($message, $attribute, $rule, $parameters) {
        return str_replace([':attribute', ':max'], [$attribute, $parameters[0]],
            'The :attribute must not exceed :max words.');
    });

    // Implicit extension (runs even if empty)
    Validator::extendImplicit('required_active', function ($attribute, $value, $parameters, $validator) {
        $data = $validator->getData();
        if (($data['status'] ?? null) === 'active') {
            return !empty($value);
        }
        return true;
    });
}

// Usage
public function rules(): array
{
    return [
        'phone' => ['required', 'phone'],
        'bio' => ['nullable', 'string', 'max_words:500'],
        'email' => ['required_active', 'email'],
    ];
}
```

## Reusable Rule Macros

```php
<?php
// app/Providers/AppServiceProvider.php
use Illuminate\Validation\Rule;

public function boot(): void
{
    Rule::macro('existsInTenant', function (string $table, string $column = 'id') {
        return Rule::exists($table, $column)
            ->where('tenant_id', auth()->user()?->tenant_id);
    });

    Rule::macro('uniqueInTenant', function (string $table, string $column, ?string $ignore = null) {
        $rule = Rule::unique($table, $column)
            ->where('tenant_id', auth()->user()?->tenant_id);

        if ($ignore) {
            $rule->ignore($ignore);
        }

        return $rule;
    });
}

// Usage
public function rules(): array
{
    return [
        'category_id' => ['required', Rule::existsInTenant('categories')],
        'name' => ['required', Rule::uniqueInTenant('products', 'name', $this->product?->id)],
    ];
}
```

## Testing Custom Rules

```php
<?php
// tests/Unit/Rules/ValidSlugTest.php
namespace Tests\Unit\Rules;

use App\Rules\ValidSlug;
use Tests\TestCase;

class ValidSlugTest extends TestCase
{
    protected ValidSlug $rule;

    protected function setUp(): void
    {
        parent::setUp();
        $this->rule = new ValidSlug();
    }

    public function test_valid_slug_passes(): void
    {
        $failed = false;
        $this->rule->validate('slug', 'valid-slug-123', function () use (&$failed) {
            $failed = true;
        });

        $this->assertFalse($failed);
    }

    public function test_slug_with_uppercase_fails(): void
    {
        $message = null;
        $this->rule->validate('slug', 'Invalid-Slug', function ($msg) use (&$message) {
            $message = $msg;
        });

        $this->assertNotNull($message);
        $this->assertStringContains('valid slug', $message);
    }

    public function test_reserved_slug_fails(): void
    {
        $message = null;
        $this->rule->validate('slug', 'admin', function ($msg) use (&$message) {
            $message = $msg;
        });

        $this->assertNotNull($message);
        $this->assertStringContains('reserved', $message);
    }
}
```

## Best Practices

1. **Single Responsibility**: One rule, one concern
2. **Descriptive Messages**: Clear error messages
3. **Data Awareness**: Use DataAwareRule for cross-field validation
4. **Test Thoroughly**: Unit test all custom rules
5. **Reuse**: Create rule macros for common patterns
6. **Document**: Add PHPDoc for rule parameters
