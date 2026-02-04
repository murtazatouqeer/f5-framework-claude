---
name: laravel-request
description: Template for Laravel Form Requests
applies_to: laravel
type: template
---

# Laravel Request Template

## Create Request

```php
<?php
// app/Http/Requests/{{EntityName}}/Create{{EntityName}}Request.php
namespace App\Http\Requests\{{EntityName}};

use App\Enums\{{EntityName}}Status;
use Illuminate\Foundation\Http\FormRequest;
use Illuminate\Validation\Rule;
use Illuminate\Validation\Rules\Enum;

class Create{{EntityName}}Request extends FormRequest
{
    /**
     * Determine if the user is authorized to make this request.
     */
    public function authorize(): bool
    {
        return $this->user()->can('create', {{EntityName}}::class);
    }

    /**
     * Get the validation rules that apply to the request.
     *
     * @return array<string, \Illuminate\Contracts\Validation\ValidationRule|array<mixed>|string>
     */
    public function rules(): array
    {
        return [
            'name' => [
                'required',
                'string',
                'min:3',
                'max:255',
                Rule::unique('{{table_name}}', 'name'),
            ],
            'slug' => [
                'nullable',
                'string',
                'max:255',
                'alpha_dash',
                Rule::unique('{{table_name}}', 'slug'),
            ],
            'description' => [
                'nullable',
                'string',
                'max:5000',
            ],
            'status' => [
                'sometimes',
                new Enum({{EntityName}}Status::class),
            ],
            'category_id' => [
                'required',
                'uuid',
                Rule::exists('categories', 'id')->whereNull('deleted_at'),
            ],
            'price' => [
                'required',
                'numeric',
                'min:0',
                'max:999999.99',
            ],
            'is_active' => [
                'sometimes',
                'boolean',
            ],
            'tags' => [
                'nullable',
                'array',
                'max:10',
            ],
            'tags.*' => [
                'uuid',
                Rule::exists('tags', 'id'),
            ],
            'metadata' => [
                'nullable',
                'array',
            ],
            'published_at' => [
                'nullable',
                'date',
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
            'is_active' => 'active status',
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
            'name.required' => 'The {{entityName}} name is required.',
            'name.unique' => 'A {{entityName}} with this name already exists.',
            'category_id.exists' => 'The selected category does not exist.',
            'price.min' => 'The price cannot be negative.',
        ];
    }

    /**
     * Prepare the data for validation.
     */
    protected function prepareForValidation(): void
    {
        $this->merge([
            'name' => $this->name ? trim($this->name) : null,
            'slug' => $this->slug ?: \Str::slug($this->name),
            'is_active' => filter_var($this->is_active, FILTER_VALIDATE_BOOLEAN, FILTER_NULL_ON_FAILURE),
        ]);
    }
}
```

## Update Request

```php
<?php
// app/Http/Requests/{{EntityName}}/Update{{EntityName}}Request.php
namespace App\Http\Requests\{{EntityName}};

use App\Enums\{{EntityName}}Status;
use App\Models\{{EntityName}};
use Illuminate\Foundation\Http\FormRequest;
use Illuminate\Validation\Rule;
use Illuminate\Validation\Rules\Enum;

class Update{{EntityName}}Request extends FormRequest
{
    /**
     * Determine if the user is authorized to make this request.
     */
    public function authorize(): bool
    {
        return $this->user()->can('update', $this->route('{{entityName}}'));
    }

    /**
     * Get the validation rules that apply to the request.
     *
     * @return array<string, \Illuminate\Contracts\Validation\ValidationRule|array<mixed>|string>
     */
    public function rules(): array
    {
        ${{entityName}} = $this->route('{{entityName}}');

        return [
            'name' => [
                'sometimes',
                'required',
                'string',
                'min:3',
                'max:255',
                Rule::unique('{{table_name}}', 'name')->ignore(${{entityName}}->id),
            ],
            'slug' => [
                'sometimes',
                'nullable',
                'string',
                'max:255',
                'alpha_dash',
                Rule::unique('{{table_name}}', 'slug')->ignore(${{entityName}}->id),
            ],
            'description' => [
                'nullable',
                'string',
                'max:5000',
            ],
            'status' => [
                'sometimes',
                new Enum({{EntityName}}Status::class),
            ],
            'category_id' => [
                'sometimes',
                'uuid',
                Rule::exists('categories', 'id')->whereNull('deleted_at'),
            ],
            'price' => [
                'sometimes',
                'numeric',
                'min:0',
                'max:999999.99',
            ],
            'is_active' => [
                'sometimes',
                'boolean',
            ],
            'tags' => [
                'nullable',
                'array',
                'max:10',
            ],
            'tags.*' => [
                'uuid',
                Rule::exists('tags', 'id'),
            ],
            'metadata' => [
                'nullable',
                'array',
            ],
            'published_at' => [
                'nullable',
                'date',
            ],
        ];
    }

    /**
     * Configure the validator instance.
     */
    public function withValidator($validator): void
    {
        $validator->after(function ($validator) {
            ${{entityName}} = $this->route('{{entityName}}');

            // Validate status transitions
            if ($this->has('status')) {
                if (!$this->isValidTransition(${{entityName}}->status, $this->status)) {
                    $validator->errors()->add('status', 'Invalid status transition.');
                }
            }
        });
    }

    /**
     * Check if status transition is valid.
     */
    protected function isValidTransition({{EntityName}}Status $from, string $to): bool
    {
        $transitions = [
            {{EntityName}}Status::DRAFT->value => ['active', 'archived'],
            {{EntityName}}Status::ACTIVE->value => ['archived'],
            {{EntityName}}Status::ARCHIVED->value => ['draft'],
        ];

        return in_array($to, $transitions[$from->value] ?? []);
    }
}
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{EntityName}}` | PascalCase entity name | `Product` |
| `{{entityName}}` | camelCase entity name | `product` |
| `{{table_name}}` | snake_case plural table name | `products` |
