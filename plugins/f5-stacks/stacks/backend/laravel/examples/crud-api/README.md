# Laravel CRUD API Example

Complete example of a Laravel CRUD API implementation following F5 Framework patterns.

## Structure

```
crud-api/
├── README.md
├── app/
│   ├── Http/
│   │   ├── Controllers/Api/
│   │   │   └── ProductController.php
│   │   ├── Requests/Product/
│   │   │   ├── CreateProductRequest.php
│   │   │   └── UpdateProductRequest.php
│   │   └── Resources/
│   │       └── ProductResource.php
│   ├── Models/
│   │   └── Product.php
│   ├── Policies/
│   │   └── ProductPolicy.php
│   ├── Repositories/
│   │   └── ProductRepository.php
│   ├── Services/
│   │   └── ProductService.php
│   └── Traits/
│       └── ApiResponse.php
├── database/
│   ├── factories/
│   │   └── ProductFactory.php
│   └── migrations/
│       └── create_products_table.php
├── routes/
│   └── api.php
└── tests/
    └── Feature/Api/
        └── ProductTest.php
```

## Key Patterns

### 1. Controller Pattern
- Inject Service layer
- Use Form Requests for validation
- Use API Resources for transformation
- Use Policy authorization
- Use ApiResponse trait for consistent responses

### 2. Service Pattern
- Business logic encapsulation
- Transaction handling
- Event dispatching
- Cache management

### 3. Repository Pattern
- Database abstraction
- Query building
- Filter application
- Eager loading

### 4. Resource Pattern
- JSON transformation
- Conditional attributes
- Relationship handling
- Pagination support

### 5. Request Pattern
- Authorization in request
- Validation rules
- Custom messages
- Data preparation

### 6. Policy Pattern
- Model authorization
- Ability-based access
- Owner checks
- Role-based access

## Usage

This example demonstrates a complete Product API with:
- List with pagination, filtering, and search
- Create with validation
- Read single resource
- Update with partial updates
- Delete with soft deletes
- Authorization at all levels
- Consistent API responses
- Full test coverage

## API Endpoints

```
GET    /api/products        - List products
POST   /api/products        - Create product
GET    /api/products/{id}   - Get product
PUT    /api/products/{id}   - Update product
DELETE /api/products/{id}   - Delete product
```

## Related Skills

- `skills/architecture/service-pattern.md`
- `skills/architecture/repository-pattern.md`
- `skills/validation/form-requests.md`
- `skills/security/policies.md`
- `skills/error-handling/api-responses.md`
- `skills/testing/feature-tests.md`

## Related Templates

- `templates/laravel-controller.md`
- `templates/laravel-model.md`
- `templates/laravel-service.md`
- `templates/laravel-repository.md`
- `templates/laravel-request.md`
- `templates/laravel-resource.md`
- `templates/laravel-policy.md`
- `templates/laravel-test.md`
