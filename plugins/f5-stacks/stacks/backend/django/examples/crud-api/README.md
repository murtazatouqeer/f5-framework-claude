# CRUD API Example

Complete example of a Django REST Framework CRUD API with best practices.

## Structure

```
crud-api/
├── README.md
├── models.py          # Product model with soft delete
├── serializers.py     # Multiple serializers per action
├── views.py           # ViewSet with custom actions
├── urls.py            # Router configuration
├── filters.py         # Django-filter integration
├── admin.py           # Admin configuration
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── factories.py
│   └── test_api.py
└── migrations/
    └── 0001_initial.py
```

## Features Demonstrated

- ✅ UUID primary keys
- ✅ Soft delete pattern
- ✅ Action-specific serializers
- ✅ Custom QuerySet with managers
- ✅ Filtering, search, ordering
- ✅ Pagination
- ✅ Custom actions (activate, bulk-delete)
- ✅ Admin with color badges
- ✅ Comprehensive tests with factories

## Usage

1. Copy files to your Django app
2. Add app to `INSTALLED_APPS`
3. Run migrations: `python manage.py migrate`
4. Register URLs in main `urls.py`

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/products/` | List products |
| POST | `/api/products/` | Create product |
| GET | `/api/products/{id}/` | Get product |
| PUT | `/api/products/{id}/` | Update product |
| PATCH | `/api/products/{id}/` | Partial update |
| DELETE | `/api/products/{id}/` | Soft delete |
| POST | `/api/products/{id}/activate/` | Activate product |
| POST | `/api/products/bulk-delete/` | Bulk delete |
| GET | `/api/products/stats/` | Get statistics |

## Query Parameters

```
GET /api/products/?status=active&search=widget&ordering=-price&page_size=10
```
