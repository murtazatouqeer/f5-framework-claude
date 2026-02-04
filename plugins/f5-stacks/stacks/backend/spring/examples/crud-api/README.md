# CRUD API Example

Complete Spring Boot REST API example with all layers implemented.

## Structure

```
crud-api/
├── entity/
│   └── Product.java
├── repository/
│   └── ProductRepository.java
├── service/
│   └── ProductService.java
├── controller/
│   └── ProductController.java
├── dto/
│   ├── ProductRequest.java
│   ├── ProductResponse.java
│   └── ProductFilter.java
├── mapper/
│   └── ProductMapper.java
├── specification/
│   └── ProductSpecification.java
└── migration/
    └── V1__create_products_table.sql
```

## Features Demonstrated

- Full CRUD operations with REST endpoints
- Pagination and sorting
- Dynamic filtering with JPA Specifications
- DTO pattern with Java records
- MapStruct mapping
- Bean Validation
- Soft delete
- Auditing (created/updated timestamps and users)
- Optimistic locking
- OpenAPI/Swagger documentation
- Spring Security integration

## Usage

1. Copy files to your project's appropriate packages
2. Replace `com.example.app` with your base package
3. Update entity fields as needed
4. Run the Flyway migration
5. Test with Swagger UI at `/swagger-ui.html`

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/products` | List all products (paginated) |
| GET | `/api/v1/products/{id}` | Get product by ID |
| POST | `/api/v1/products` | Create new product |
| PUT | `/api/v1/products/{id}` | Update product |
| PATCH | `/api/v1/products/{id}` | Partial update |
| DELETE | `/api/v1/products/{id}` | Delete product |

## Query Parameters

- `search` - Full-text search across name and description
- `categoryId` - Filter by category
- `status` - Filter by status (DRAFT, ACTIVE, INACTIVE, ARCHIVED)
- `minPrice` / `maxPrice` - Price range filter
- `page` - Page number (0-based)
- `size` - Page size (default: 20)
- `sort` - Sort field and direction (e.g., `createdAt,desc`)
