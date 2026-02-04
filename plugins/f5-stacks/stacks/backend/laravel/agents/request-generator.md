---
name: laravel-request-generator
description: Agent for generating Laravel Form Request validation classes
applies_to: laravel
category: agent
---

# Laravel Request Generator Agent

## Purpose

Generate production-ready Laravel Form Request classes with validation rules, authorization, and custom messages.

## Input Requirements

```yaml
required:
  - entity_name: string          # e.g., "Product"
  - action: string               # "create" or "update"

optional:
  - fields: object               # Field definitions with rules
  - authorization: boolean       # Include authorization (default: true)
  - custom_messages: boolean     # Include custom messages (default: true)
  - custom_attributes: boolean   # Include custom attributes (default: true)
  - prepare_validation: boolean  # Include prepareForValidation (default: true)
```

## Generation Process

### Step 1: Analyze Model and Schema

```php
// Get validation requirements from model and migration
$model = app("App\\Models\\{$entityName}");
$table = $model->getTable();
$columns = Schema::getColumnListing($table);
$fillable = $model->getFillable();
```

### Step 2: Generate Create Request

```php
<?php
// app/Http/Requests/{{Entity}}/Create{{Entity}}Request.php
namespace App\Http\Requests\{{Entity}};

use App\Enums\{{Entity}}Status;
use App\Models\{{Entity}};
use Illuminate\Foundation\Http\FormRequest;
use Illuminate\Validation\Rule;
use Illuminate\Validation\Rules\Enum;

class Create{{Entity}}Request extends FormRequest
{
    /**
     * Determine if the user is authorized to make this request.
     */
    public function authorize(): bool
    {
        return $this->user()->can('create', {{Entity}}::class);
    }

    /**
     * Get the validation rules that apply to the request.
     *
     * @return array<string, \Illuminate\Contracts\Validation\ValidationRule|array|string>
     */
    public function rules(): array
    {
        return [
            // Required string fields
            'name' => [
                'required',
                'string',
                'min:3',
                'max:255',
                Rule::unique('{{entities}}', 'name'),
            ],

            // Optional text fields
            'description' => [
                'nullable',
                'string',
                'max:5000',
            ],

            // Numeric fields
            'price' => [
                'required',
                'numeric',
                'min:0',
                'max:999999.99',
            ],
            'compare_price' => [
                'nullable',
                'numeric',
                'min:0',
                'gt:price',
            ],

            // Foreign key references
            'category_id' => [
                'required',
                'uuid',
                Rule::exists('categories', 'id')->whereNull('deleted_at'),
            ],

            // Enum fields
            'status' => [
                'sometimes',
                new Enum({{Entity}}Status::class),
            ],

            // Boolean fields
            'is_featured' => [
                'sometimes',
                'boolean',
            ],

            // Array fields
            'tags' => [
                'nullable',
                'array',
                'max:10',
            ],
            'tags.*' => [
                'string',
                'max:50',
                Rule::exists('tags', 'id'),
            ],

            // JSON/Object fields
            'metadata' => [
                'nullable',
                'array',
            ],
            'metadata.key' => [
                'sometimes',
                'string',
                'max:100',
            ],

            // File uploads
            'image' => [
                'nullable',
                'image',
                'mimes:jpeg,png,webp',
                'max:2048', // 2MB
                'dimensions:min_width=100,min_height=100,max_width=4000,max_height=4000',
            ],

            // Date fields
            'published_at' => [
                'nullable',
                'date',
                'after_or_equal:today',
            ],
        ];
    }

    /**
     * Get custom attributes for validator errors.
     *
     * @return array<string, string>
     */
    public function attributes(): array
    {
        return [
            'category_id' => 'category',
            'compare_price' => 'compare price',
            'is_featured' => 'featured status',
            'published_at' => 'publication date',
        ];
    }

    /**
     * Get the error messages for the defined validation rules.
     *
     * @return array<string, string>
     */
    public function messages(): array
    {
        return [
            'name.required' => 'The {{entity}} name is required.',
            'name.unique' => 'A {{entity}} with this name already exists.',
            'price.required' => 'Please specify a price for the {{entity}}.',
            'price.min' => 'The price cannot be negative.',
            'compare_price.gt' => 'The compare price must be greater than the regular price.',
            'category_id.exists' => 'The selected category does not exist.',
            'tags.max' => 'You can only add up to 10 tags.',
            'image.max' => 'The image must not exceed 2MB.',
        ];
    }

    /**
     * Prepare the data for validation.
     */
    protected function prepareForValidation(): void
    {
        // Trim string fields
        if ($this->has('name')) {
            $this->merge([
                'name' => trim($this->name),
            ]);
        }

        // Normalize boolean fields
        if ($this->has('is_featured')) {
            $this->merge([
                'is_featured' => filter_var($this->is_featured, FILTER_VALIDATE_BOOLEAN),
            ]);
        }

        // Set defaults
        if (!$this->has('status')) {
            $this->merge([
                'status' => {{Entity}}Status::Draft->value,
            ]);
        }
    }

    /**
     * Handle a passed validation attempt.
     */
    protected function passedValidation(): void
    {
        // Additional processing after validation passes
        // e.g., generate slug from name
    }
}
```

### Step 3: Generate Update Request

```php
<?php
// app/Http/Requests/{{Entity}}/Update{{Entity}}Request.php
namespace App\Http\Requests\{{Entity}};

use App\Enums\{{Entity}}Status;
use Illuminate\Foundation\Http\FormRequest;
use Illuminate\Validation\Rule;
use Illuminate\Validation\Rules\Enum;

class Update{{Entity}}Request extends FormRequest
{
    /**
     * Determine if the user is authorized to make this request.
     */
    public function authorize(): bool
    {
        return $this->user()->can('update', $this->route('{{entity}}'));
    }

    /**
     * Get the validation rules that apply to the request.
     *
     * @return array<string, \Illuminate\Contracts\Validation\ValidationRule|array|string>
     */
    public function rules(): array
    {
        ${{entity}} = $this->route('{{entity}}');

        return [
            'name' => [
                'sometimes',
                'required',
                'string',
                'min:3',
                'max:255',
                Rule::unique('{{entities}}', 'name')->ignore(${{entity}}->id),
            ],

            'description' => [
                'nullable',
                'string',
                'max:5000',
            ],

            'price' => [
                'sometimes',
                'required',
                'numeric',
                'min:0',
                'max:999999.99',
            ],

            'compare_price' => [
                'nullable',
                'numeric',
                'min:0',
            ],

            'category_id' => [
                'sometimes',
                'required',
                'uuid',
                Rule::exists('categories', 'id')->whereNull('deleted_at'),
            ],

            'status' => [
                'sometimes',
                new Enum({{Entity}}Status::class),
            ],

            'is_featured' => [
                'sometimes',
                'boolean',
            ],

            'tags' => [
                'nullable',
                'array',
                'max:10',
            ],
            'tags.*' => [
                'string',
                'max:50',
            ],
        ];
    }

    /**
     * Configure the validator instance.
     *
     * @param \Illuminate\Validation\Validator $validator
     */
    public function withValidator($validator): void
    {
        $validator->after(function ($validator) {
            // Cross-field validation
            if ($this->compare_price && $this->price) {
                if ($this->compare_price <= $this->price) {
                    $validator->errors()->add(
                        'compare_price',
                        'The compare price must be greater than the regular price.'
                    );
                }
            }

            // Status transition validation
            ${{entity}} = $this->route('{{entity}}');
            if ($this->status && !$this->isValidStatusTransition(${{entity}}->status, $this->status)) {
                $validator->errors()->add(
                    'status',
                    'Invalid status transition.'
                );
            }
        });
    }

    /**
     * Check if status transition is valid.
     */
    protected function isValidStatusTransition(?{{Entity}}Status $current, string $new): bool
    {
        $transitions = [
            'draft' => ['active', 'archived'],
            'active' => ['archived'],
            'archived' => ['draft'],
        ];

        return in_array($new, $transitions[$current?->value] ?? []);
    }
}
```

### Step 4: Generate Query Request

```php
<?php
// app/Http/Requests/{{Entity}}/Query{{Entity}}Request.php
namespace App\Http\Requests\{{Entity}};

use App\Enums\{{Entity}}Status;
use Illuminate\Foundation\Http\FormRequest;
use Illuminate\Validation\Rules\Enum;

class Query{{Entity}}Request extends FormRequest
{
    /**
     * Determine if the user is authorized to make this request.
     */
    public function authorize(): bool
    {
        return true;
    }

    /**
     * Get the validation rules that apply to the request.
     *
     * @return array<string, \Illuminate\Contracts\Validation\ValidationRule|array|string>
     */
    public function rules(): array
    {
        return [
            // Pagination
            'page' => ['sometimes', 'integer', 'min:1'],
            'per_page' => ['sometimes', 'integer', 'min:1', 'max:100'],

            // Search
            'search' => ['nullable', 'string', 'max:100'],

            // Filters
            'status' => ['nullable', new Enum({{Entity}}Status::class)],
            'category_id' => ['nullable', 'uuid'],
            'is_featured' => ['nullable', 'boolean'],
            'min_price' => ['nullable', 'numeric', 'min:0'],
            'max_price' => ['nullable', 'numeric', 'min:0', 'gte:min_price'],

            // Date filters
            'created_from' => ['nullable', 'date'],
            'created_to' => ['nullable', 'date', 'after_or_equal:created_from'],

            // Sorting
            'sort_by' => ['nullable', 'string', 'in:name,price,created_at,updated_at'],
            'sort_order' => ['nullable', 'string', 'in:asc,desc'],

            // Include relations
            'include' => ['nullable', 'string'],
        ];
    }

    /**
     * Prepare the data for validation.
     */
    protected function prepareForValidation(): void
    {
        // Set default pagination
        $this->merge([
            'per_page' => $this->per_page ?? 15,
            'sort_by' => $this->sort_by ?? 'created_at',
            'sort_order' => $this->sort_order ?? 'desc',
        ]);
    }
}
```

## Output Files

```
app/Http/Requests/{{Entity}}/
├── Create{{Entity}}Request.php   # Create validation
├── Update{{Entity}}Request.php   # Update validation
└── Query{{Entity}}Request.php    # Query/filter validation
```

## Usage Example

```bash
# Generate request via agent
@laravel:request-generator {
  "entity_name": "Product",
  "action": "create",
  "fields": {
    "name": "required|string|max:255",
    "price": "required|numeric|min:0"
  },
  "authorization": true,
  "custom_messages": true
}
```

## Validation Checklist

- [ ] All required fields have 'required' rule
- [ ] Unique rules ignore current record on update
- [ ] Foreign key rules check record existence
- [ ] Enum rules use Enum class
- [ ] File rules include size and type limits
- [ ] Custom messages are user-friendly
- [ ] Authorization checks correct ability
