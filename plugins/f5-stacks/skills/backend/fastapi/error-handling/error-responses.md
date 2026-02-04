---
name: fastapi-error-responses
description: Standardized error response patterns for FastAPI
applies_to: fastapi
category: skill
---

# Error Response Patterns

## Standard Response Structure

```python
# app/schemas/response.py
from typing import TypeVar, Generic, Optional, Any, List
from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """Individual error detail for validation errors."""
    loc: List[str] = Field(description="Error location (field path)")
    msg: str = Field(description="Error message")
    type: str = Field(description="Error type")


class ErrorBody(BaseModel):
    """Error information body."""
    code: str = Field(description="Error code for programmatic handling")
    message: str = Field(description="Human-readable error message")
    details: Optional[dict[str, Any]] = Field(
        None,
        description="Additional error details"
    )
    errors: Optional[List[ErrorDetail]] = Field(
        None,
        description="Validation errors list"
    )


class APIResponse(BaseModel, Generic[T]):
    """Standard API response wrapper."""
    success: bool = True
    data: Optional[T] = None
    error: Optional[ErrorBody] = None
    meta: Optional[dict[str, Any]] = None


class PaginatedMeta(BaseModel):
    """Pagination metadata."""
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""
    success: bool = True
    data: List[T]
    meta: PaginatedMeta
    error: Optional[ErrorBody] = None
```

## Error Codes Catalog

```python
# app/core/error_codes.py
from enum import Enum


class ErrorCode(str, Enum):
    """Standardized error codes."""

    # Authentication errors (1xxx)
    AUTH_REQUIRED = "AUTH_1001"
    AUTH_INVALID_CREDENTIALS = "AUTH_1002"
    AUTH_TOKEN_EXPIRED = "AUTH_1003"
    AUTH_TOKEN_INVALID = "AUTH_1004"
    AUTH_INSUFFICIENT_PERMISSIONS = "AUTH_1005"

    # Validation errors (2xxx)
    VALIDATION_ERROR = "VAL_2001"
    INVALID_FORMAT = "VAL_2002"
    MISSING_REQUIRED_FIELD = "VAL_2003"
    INVALID_VALUE = "VAL_2004"

    # Resource errors (3xxx)
    RESOURCE_NOT_FOUND = "RES_3001"
    RESOURCE_ALREADY_EXISTS = "RES_3002"
    RESOURCE_CONFLICT = "RES_3003"
    RESOURCE_DELETED = "RES_3004"

    # Business logic errors (4xxx)
    BUSINESS_RULE_VIOLATION = "BUS_4001"
    INSUFFICIENT_BALANCE = "BUS_4002"
    INVALID_OPERATION = "BUS_4003"
    QUOTA_EXCEEDED = "BUS_4004"

    # Rate limiting errors (5xxx)
    RATE_LIMIT_EXCEEDED = "RATE_5001"
    TOO_MANY_REQUESTS = "RATE_5002"

    # External service errors (6xxx)
    EXTERNAL_SERVICE_ERROR = "EXT_6001"
    EXTERNAL_TIMEOUT = "EXT_6002"
    EXTERNAL_UNAVAILABLE = "EXT_6003"

    # Internal errors (9xxx)
    INTERNAL_ERROR = "INT_9001"
    DATABASE_ERROR = "INT_9002"
    CONFIGURATION_ERROR = "INT_9003"


# Error messages mapping
ERROR_MESSAGES = {
    ErrorCode.AUTH_REQUIRED: "Authentication required",
    ErrorCode.AUTH_INVALID_CREDENTIALS: "Invalid email or password",
    ErrorCode.AUTH_TOKEN_EXPIRED: "Token has expired",
    ErrorCode.AUTH_TOKEN_INVALID: "Invalid token",
    ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS: "Insufficient permissions",

    ErrorCode.VALIDATION_ERROR: "Validation failed",
    ErrorCode.INVALID_FORMAT: "Invalid format",
    ErrorCode.MISSING_REQUIRED_FIELD: "Required field is missing",
    ErrorCode.INVALID_VALUE: "Invalid value",

    ErrorCode.RESOURCE_NOT_FOUND: "Resource not found",
    ErrorCode.RESOURCE_ALREADY_EXISTS: "Resource already exists",
    ErrorCode.RESOURCE_CONFLICT: "Resource conflict",
    ErrorCode.RESOURCE_DELETED: "Resource has been deleted",

    ErrorCode.RATE_LIMIT_EXCEEDED: "Rate limit exceeded",

    ErrorCode.INTERNAL_ERROR: "An unexpected error occurred",
}
```

## Response Helpers

```python
# app/core/responses.py
from typing import TypeVar, Optional, Any, List
from fastapi import status
from fastapi.responses import JSONResponse

from app.schemas.response import APIResponse, ErrorBody, PaginatedResponse, PaginatedMeta
from app.core.error_codes import ErrorCode, ERROR_MESSAGES

T = TypeVar("T")


def success_response(
    data: Any = None,
    message: Optional[str] = None,
    meta: Optional[dict] = None,
    status_code: int = status.HTTP_200_OK,
) -> JSONResponse:
    """Create a success response."""
    response = APIResponse(
        success=True,
        data=data,
        meta=meta,
    )
    return JSONResponse(
        status_code=status_code,
        content=response.model_dump(exclude_none=True),
    )


def error_response(
    code: ErrorCode,
    message: Optional[str] = None,
    details: Optional[dict] = None,
    errors: Optional[List[dict]] = None,
    status_code: int = status.HTTP_400_BAD_REQUEST,
) -> JSONResponse:
    """Create an error response."""
    response = APIResponse(
        success=False,
        error=ErrorBody(
            code=code.value,
            message=message or ERROR_MESSAGES.get(code, "Error"),
            details=details,
            errors=errors,
        ),
    )
    return JSONResponse(
        status_code=status_code,
        content=response.model_dump(exclude_none=True),
    )


def paginated_response(
    items: List[Any],
    total: int,
    page: int,
    page_size: int,
) -> JSONResponse:
    """Create a paginated response."""
    total_pages = (total + page_size - 1) // page_size

    response = PaginatedResponse(
        success=True,
        data=items,
        meta=PaginatedMeta(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1,
        ),
    )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=response.model_dump(),
    )


# Specific error responses
def not_found_response(
    resource: str,
    resource_id: Optional[str] = None,
) -> JSONResponse:
    """Create a not found response."""
    details = {"resource": resource}
    if resource_id:
        details["id"] = resource_id

    return error_response(
        code=ErrorCode.RESOURCE_NOT_FOUND,
        message=f"{resource.capitalize()} not found",
        details=details,
        status_code=status.HTTP_404_NOT_FOUND,
    )


def validation_error_response(
    errors: List[dict],
) -> JSONResponse:
    """Create a validation error response."""
    return error_response(
        code=ErrorCode.VALIDATION_ERROR,
        message="Request validation failed",
        errors=errors,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )


def unauthorized_response(
    message: str = "Authentication required",
) -> JSONResponse:
    """Create an unauthorized response."""
    return error_response(
        code=ErrorCode.AUTH_REQUIRED,
        message=message,
        status_code=status.HTTP_401_UNAUTHORIZED,
    )


def forbidden_response(
    message: str = "Access forbidden",
) -> JSONResponse:
    """Create a forbidden response."""
    return error_response(
        code=ErrorCode.AUTH_INSUFFICIENT_PERMISSIONS,
        message=message,
        status_code=status.HTTP_403_FORBIDDEN,
    )
```

## OpenAPI Documentation

```python
# app/core/openapi.py
from typing import Any, Dict


def error_responses(
    *status_codes: int,
) -> Dict[int, Dict[str, Any]]:
    """Generate OpenAPI error response documentation."""

    responses = {}

    error_schemas = {
        400: {
            "description": "Bad Request",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": "VAL_2001",
                            "message": "Validation error",
                            "details": {},
                        },
                    },
                },
            },
        },
        401: {
            "description": "Unauthorized",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": "AUTH_1001",
                            "message": "Authentication required",
                        },
                    },
                },
            },
        },
        403: {
            "description": "Forbidden",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": "AUTH_1005",
                            "message": "Insufficient permissions",
                        },
                    },
                },
            },
        },
        404: {
            "description": "Not Found",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": "RES_3001",
                            "message": "Resource not found",
                            "details": {"resource": "product"},
                        },
                    },
                },
            },
        },
        409: {
            "description": "Conflict",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": "RES_3002",
                            "message": "Resource already exists",
                        },
                    },
                },
            },
        },
        422: {
            "description": "Validation Error",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": "VAL_2001",
                            "message": "Request validation failed",
                            "errors": [
                                {
                                    "loc": ["body", "email"],
                                    "msg": "Invalid email format",
                                    "type": "value_error",
                                },
                            ],
                        },
                    },
                },
            },
        },
        429: {
            "description": "Too Many Requests",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": "RATE_5001",
                            "message": "Rate limit exceeded",
                            "details": {"retry_after": 60},
                        },
                    },
                },
            },
        },
        500: {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": "INT_9001",
                            "message": "An unexpected error occurred",
                        },
                    },
                },
            },
        },
    }

    for code in status_codes:
        if code in error_schemas:
            responses[code] = error_schemas[code]

    return responses


# Usage in endpoints
from fastapi import APIRouter

router = APIRouter()


@router.get(
    "/{id}",
    responses=error_responses(401, 403, 404),
)
async def get_product(id: UUID):
    """Get product by ID."""
    ...
```

## Consistent Error Usage

```python
# app/api/v1/endpoints/products.py
from fastapi import APIRouter, Depends, status
from typing import Annotated

from app.api.deps import CurrentUser, ProductServiceDep
from app.schemas.product import ProductCreate, ProductResponse
from app.schemas.response import APIResponse
from app.core.openapi import error_responses
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.post(
    "/",
    response_model=APIResponse[ProductResponse],
    status_code=status.HTTP_201_CREATED,
    responses=error_responses(401, 403, 409, 422),
)
async def create_product(
    data: ProductCreate,
    current_user: CurrentUser,
    service: ProductServiceDep,
):
    """Create a new product.

    Returns:
        Created product data wrapped in standard response.

    Raises:
        ConflictError: If product with same slug exists.
        ValidationError: If request data is invalid.
    """
    product = await service.create(data, current_user)
    return APIResponse(success=True, data=ProductResponse.model_validate(product))


@router.get(
    "/{id}",
    response_model=APIResponse[ProductResponse],
    responses=error_responses(401, 404),
)
async def get_product(
    id: UUID,
    service: ProductServiceDep,
):
    """Get product by ID.

    Returns:
        Product data wrapped in standard response.

    Raises:
        NotFoundError: If product not found.
    """
    product = await service.get_by_id(id)
    return APIResponse(success=True, data=ProductResponse.model_validate(product))
```

## Client-Side Error Handling

```typescript
// Example TypeScript client error handling
interface APIError {
  code: string;
  message: string;
  details?: Record<string, any>;
  errors?: Array<{
    loc: string[];
    msg: string;
    type: string;
  }>;
}

interface APIResponse<T> {
  success: boolean;
  data?: T;
  error?: APIError;
}

async function handleAPIResponse<T>(response: Response): Promise<T> {
  const json: APIResponse<T> = await response.json();

  if (!json.success && json.error) {
    // Handle specific error codes
    switch (json.error.code) {
      case 'AUTH_1003':
        // Token expired - refresh and retry
        await refreshToken();
        throw new RetryableError();

      case 'VAL_2001':
        // Validation error - show field errors
        throw new ValidationError(json.error.errors);

      case 'RATE_5001':
        // Rate limited - show retry message
        const retryAfter = json.error.details?.retry_after || 60;
        throw new RateLimitError(retryAfter);

      default:
        throw new APIError(json.error.message, json.error.code);
    }
  }

  return json.data as T;
}
```

## Best Practices

1. **Use consistent response wrapper** for all endpoints
2. **Define error codes** for programmatic handling
3. **Include error details** for debugging
4. **Document errors in OpenAPI** for each endpoint
5. **Provide actionable messages** for users
6. **Log error context** server-side
7. **Never expose internal errors** in production
8. **Include request ID** for support/debugging
