---
name: laravel-form-requests
description: Laravel Form Request validation patterns
applies_to: laravel
category: validation
---

# Laravel Form Requests

## Creating Form Requests

```bash
php artisan make:request CreateProductRequest
php artisan make:request UpdateProductRequest
```

## Basic Form Request

```php
<?php
// app/Http/Requests/Product/CreateProductRequest.php
namespace App\Http\Requests\Product;

use App\Enums\ProductStatus;
use Illuminate\Foundation\Http\FormRequest;
use Illuminate\Validation\Rule;
use Illuminate\Validation\Rules\Enum;

class CreateProductRequest extends FormRequest
{
    /**
     * Determine if the user is authorized to make this request.
     */
    public function authorize(): bool
    {
        return $this->user()->can('create', Product::class);
    }

    /**
     * Get the validation rules that apply to the request.
     */
    public function rules(): array
    {
        return [
            'name' => [
                'required',
                'string',
                'min:3',
                'max:255',
                Rule::unique('products', 'name'),
            ],
            'description' => ['nullable', 'string', 'max:5000'],
            'price' => ['required', 'numeric', 'min:0', 'max:999999.99'],
            'compare_price' => ['nullable', 'numeric', 'min:0', 'gt:price'],
            'category_id' => [
                'required',
                'uuid',
                Rule::exists('categories', 'id')->whereNull('deleted_at'),
            ],
            'status' => ['sometimes', new Enum(ProductStatus::class)],
            'is_featured' => ['sometimes', 'boolean'],
            'tags' => ['nullable', 'array', 'max:10'],
            'tags.*' => ['uuid', Rule::exists('tags', 'id')],
        ];
    }

    /**
     * Get custom attributes for validator errors.
     */
    public function attributes(): array
    {
        return [
            'category_id' => 'category',
            'compare_price' => 'compare price',
            'is_featured' => 'featured status',
        ];
    }

    /**
     * Get custom error messages.
     */
    public function messages(): array
    {
        return [
            'name.required' => 'The product name is required.',
            'name.unique' => 'A product with this name already exists.',
            'price.min' => 'The price cannot be negative.',
            'compare_price.gt' => 'The compare price must be greater than the regular price.',
            'category_id.exists' => 'The selected category does not exist.',
        ];
    }
}
```

## Data Preparation

```php
<?php
class CreateProductRequest extends FormRequest
{
    /**
     * Prepare the data for validation.
     */
    protected function prepareForValidation(): void
    {
        $this->merge([
            // Trim strings
            'name' => $this->name ? trim($this->name) : null,

            // Normalize booleans
            'is_featured' => filter_var($this->is_featured, FILTER_VALIDATE_BOOLEAN, FILTER_NULL_ON_FAILURE),

            // Convert empty strings to null
            'description' => $this->description ?: null,

            // Generate slug
            'slug' => $this->slug ?: \Str::slug($this->name),
        ]);
    }

    /**
     * Handle a passed validation attempt.
     */
    protected function passedValidation(): void
    {
        // Additional processing after validation passes
        $this->replace([
            ...$this->validated(),
            'processed_at' => now(),
        ]);
    }
}
```

## Update Request with Route Model

```php
<?php
// app/Http/Requests/Product/UpdateProductRequest.php
namespace App\Http\Requests\Product;

use Illuminate\Foundation\Http\FormRequest;
use Illuminate\Validation\Rule;

class UpdateProductRequest extends FormRequest
{
    public function authorize(): bool
    {
        return $this->user()->can('update', $this->route('product'));
    }

    public function rules(): array
    {
        $product = $this->route('product');

        return [
            'name' => [
                'sometimes',
                'required',
                'string',
                'max:255',
                Rule::unique('products', 'name')->ignore($product->id),
            ],
            'description' => ['nullable', 'string', 'max:5000'],
            'price' => ['sometimes', 'required', 'numeric', 'min:0'],
            'compare_price' => ['nullable', 'numeric', 'min:0'],
            'category_id' => [
                'sometimes',
                'uuid',
                Rule::exists('categories', 'id')->whereNull('deleted_at'),
            ],
        ];
    }

    /**
     * Configure the validator instance.
     */
    public function withValidator($validator): void
    {
        $validator->after(function ($validator) {
            // Cross-field validation
            if ($this->compare_price && $this->price) {
                if ($this->compare_price <= $this->price) {
                    $validator->errors()->add(
                        'compare_price',
                        'Compare price must be greater than price.'
                    );
                }
            }

            // Status transition validation
            $product = $this->route('product');
            if ($this->status && !$this->isValidTransition($product->status, $this->status)) {
                $validator->errors()->add('status', 'Invalid status transition.');
            }
        });
    }

    protected function isValidTransition(string $from, string $to): bool
    {
        $transitions = [
            'draft' => ['active', 'archived'],
            'active' => ['archived'],
            'archived' => ['draft'],
        ];

        return in_array($to, $transitions[$from] ?? []);
    }
}
```

## Common Validation Rules

```php
<?php
public function rules(): array
{
    return [
        // String rules
        'name' => ['required', 'string', 'min:3', 'max:255'],
        'email' => ['required', 'email:rfc,dns', 'max:255'],
        'password' => ['required', 'string', 'min:8', 'confirmed'],
        'slug' => ['required', 'string', 'alpha_dash', 'max:100'],

        // Numeric rules
        'price' => ['required', 'numeric', 'min:0', 'max:999999.99'],
        'quantity' => ['required', 'integer', 'min:1', 'max:1000'],
        'discount' => ['nullable', 'numeric', 'between:0,100'],

        // Date rules
        'start_date' => ['required', 'date', 'after:today'],
        'end_date' => ['required', 'date', 'after:start_date'],
        'birth_date' => ['required', 'date', 'before:today', 'after:1900-01-01'],

        // File rules
        'avatar' => ['nullable', 'image', 'mimes:jpeg,png,webp', 'max:2048'],
        'document' => ['required', 'file', 'mimes:pdf,doc,docx', 'max:10240'],
        'images' => ['nullable', 'array', 'max:5'],
        'images.*' => ['image', 'max:2048'],

        // Array rules
        'tags' => ['nullable', 'array', 'max:10'],
        'tags.*' => ['string', 'max:50'],
        'options' => ['required', 'array', 'min:1'],
        'options.*.name' => ['required', 'string'],
        'options.*.value' => ['required', 'string'],

        // Conditional rules
        'phone' => ['required_if:contact_method,phone'],
        'company' => ['required_with:position'],
        'state' => ['required_unless:country,international'],

        // Unique with conditions
        'email' => [
            'required',
            Rule::unique('users')->where(function ($query) {
                return $query->where('account_id', $this->account_id);
            }),
        ],

        // Exists with conditions
        'category_id' => [
            'required',
            Rule::exists('categories', 'id')
                ->where('status', 'active')
                ->whereNull('deleted_at'),
        ],
    ];
}
```

## Conditional Validation

```php
<?php
public function rules(): array
{
    return [
        'payment_method' => ['required', 'in:card,bank,crypto'],

        // Rules when payment_method is 'card'
        'card_number' => ['required_if:payment_method,card', 'string', 'size:16'],
        'card_expiry' => ['required_if:payment_method,card', 'date_format:m/y'],
        'card_cvv' => ['required_if:payment_method,card', 'string', 'size:3'],

        // Rules when payment_method is 'bank'
        'bank_account' => ['required_if:payment_method,bank', 'string'],
        'bank_routing' => ['required_if:payment_method,bank', 'string'],
    ];
}

// Or use sometimes()
public function withValidator($validator): void
{
    $validator->sometimes('card_number', ['required', 'size:16'], function ($input) {
        return $input->payment_method === 'card';
    });
}
```

## Failed Validation Response

```php
<?php
use Illuminate\Contracts\Validation\Validator;
use Illuminate\Http\Exceptions\HttpResponseException;

class CreateProductRequest extends FormRequest
{
    /**
     * Handle a failed validation attempt.
     */
    protected function failedValidation(Validator $validator): void
    {
        throw new HttpResponseException(response()->json([
            'success' => false,
            'message' => 'Validation failed',
            'errors' => $validator->errors(),
        ], 422));
    }

    /**
     * Handle a failed authorization attempt.
     */
    protected function failedAuthorization(): void
    {
        throw new HttpResponseException(response()->json([
            'success' => false,
            'message' => 'You are not authorized to perform this action.',
        ], 403));
    }
}
```

## Using in Controller

```php
<?php
class ProductController extends Controller
{
    public function store(CreateProductRequest $request): JsonResponse
    {
        // Validation already passed
        $validated = $request->validated();

        // Or get specific fields
        $name = $request->validated('name');
        $tags = $request->validated('tags', []);

        // Create product
        $product = Product::create($validated);

        return ProductResource::make($product)
            ->response()
            ->setStatusCode(201);
    }
}
```

## Best Practices

1. **Authorize in Request**: Keep authorization in Form Request
2. **Meaningful Messages**: Provide user-friendly error messages
3. **Prepare Data**: Use prepareForValidation() for normalization
4. **Cross-Field Validation**: Use withValidator() for complex logic
5. **Type Safety**: Use validated() to get only validated data
6. **Organize by Entity**: Group requests in entity folders
