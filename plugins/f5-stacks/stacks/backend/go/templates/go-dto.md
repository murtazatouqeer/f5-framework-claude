# Go DTO Template

Template for creating Data Transfer Objects in Go applications.

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{entity_name}}` | Entity name (PascalCase) | User |
| `{{entity_name_lower}}` | Entity name (lowercase) | user |
| `{{package_name}}` | Package name | dto |
| `{{fields}}` | DTO fields | Email, Name |

## Request DTO Template

```go
// internal/dto/{{entity_name_lower}}_dto.go
package dto

type Create{{entity_name}}Request struct {
    {{#create_fields}}
    {{field_name}} {{field_type}} `json:"{{field_json}}" validate:"{{validation_tags}}"`
    {{/create_fields}}
}

type Update{{entity_name}}Request struct {
    {{#update_fields}}
    {{field_name}} *{{field_type}} `json:"{{field_json}}" validate:"{{validation_tags}}"`
    {{/update_fields}}
}

type {{entity_name}}Filter struct {
    {{#filter_fields}}
    {{field_name}} *{{field_type}} `json:"{{field_json}}" form:"{{field_form}}"`
    {{/filter_fields}}
    Page    int    `json:"page" form:"page" validate:"gte=1"`
    PerPage int    `json:"per_page" form:"per_page" validate:"gte=1,lte=100"`
    SortBy  string `json:"sort_by" form:"sort_by" validate:"omitempty,oneof={{sort_fields}}"`
    Order   string `json:"order" form:"order" validate:"omitempty,oneof=asc desc"`
}

func (f *{{entity_name}}Filter) SetDefaults() {
    if f.Page == 0 {
        f.Page = 1
    }
    if f.PerPage == 0 {
        f.PerPage = 20
    }
    if f.SortBy == "" {
        f.SortBy = "created_at"
    }
    if f.Order == "" {
        f.Order = "desc"
    }
}

func (f *{{entity_name}}Filter) Offset() int {
    return (f.Page - 1) * f.PerPage
}
```

## Response DTO Template

```go
// internal/dto/{{entity_name_lower}}_response.go
package dto

import (
    "time"

    "{{module_path}}/internal/domain/{{entity_name_lower}}"
)

type {{entity_name}}Response struct {
    ID        string    `json:"id"`
    {{#response_fields}}
    {{field_name}} {{field_type}} `json:"{{field_json}}"`
    {{/response_fields}}
    CreatedAt time.Time `json:"created_at"`
    UpdatedAt time.Time `json:"updated_at"`
}

func New{{entity_name}}Response(e *{{entity_name_lower}}.{{entity_name}}) *{{entity_name}}Response {
    return &{{entity_name}}Response{
        ID:        e.ID.String(),
        {{#response_mappings}}
        {{field_name}}: {{field_mapping}},
        {{/response_mappings}}
        CreatedAt: e.CreatedAt,
        UpdatedAt: e.UpdatedAt,
    }
}

type {{entity_name}}ListResponse struct {
    Items      []*{{entity_name}}Response `json:"items"`
    Total      int64                       `json:"total"`
    Page       int                         `json:"page"`
    PerPage    int                         `json:"per_page"`
    TotalPages int                         `json:"total_pages"`
}

func New{{entity_name}}ListResponse(items []*{{entity_name_lower}}.{{entity_name}}, total int64, filter *{{entity_name}}Filter) *{{entity_name}}ListResponse {
    responses := make([]*{{entity_name}}Response, len(items))
    for i, item := range items {
        responses[i] = New{{entity_name}}Response(item)
    }

    totalPages := int(total) / filter.PerPage
    if int(total)%filter.PerPage > 0 {
        totalPages++
    }

    return &{{entity_name}}ListResponse{
        Items:      responses,
        Total:      total,
        Page:       filter.Page,
        PerPage:    filter.PerPage,
        TotalPages: totalPages,
    }
}
```

## Example: User DTO

```go
// internal/dto/user_dto.go
package dto

import (
    "time"

    "myproject/internal/domain/user"
)

// Request DTOs
type CreateUserRequest struct {
    Email    string `json:"email" validate:"required,email,max=255"`
    Name     string `json:"name" validate:"required,min=2,max=100"`
    Password string `json:"password" validate:"required,min=8,max=72"`
    Role     string `json:"role" validate:"omitempty,oneof=admin user"`
}

type UpdateUserRequest struct {
    Name   *string `json:"name" validate:"omitempty,min=2,max=100"`
    Status *string `json:"status" validate:"omitempty,oneof=active inactive"`
    Role   *string `json:"role" validate:"omitempty,oneof=admin user"`
}

type UserFilter struct {
    Search *string `json:"search" form:"search"`
    Status *string `json:"status" form:"status" validate:"omitempty,oneof=active inactive banned"`
    Role   *string `json:"role" form:"role" validate:"omitempty,oneof=admin user guest"`
    Page    int    `json:"page" form:"page" validate:"gte=1"`
    PerPage int    `json:"per_page" form:"per_page" validate:"gte=1,lte=100"`
    SortBy  string `json:"sort_by" form:"sort_by" validate:"omitempty,oneof=created_at updated_at name email"`
    Order   string `json:"order" form:"order" validate:"omitempty,oneof=asc desc"`
}

func (f *UserFilter) SetDefaults() {
    if f.Page == 0 {
        f.Page = 1
    }
    if f.PerPage == 0 {
        f.PerPage = 20
    }
    if f.SortBy == "" {
        f.SortBy = "created_at"
    }
    if f.Order == "" {
        f.Order = "desc"
    }
}

func (f *UserFilter) Offset() int {
    return (f.Page - 1) * f.PerPage
}

func (f *UserFilter) ToDomain() user.Filter {
    return user.Filter{
        Search: f.Search,
        Status: (*user.Status)(f.Status),
        Role:   f.Role,
        Limit:  f.PerPage,
        Offset: f.Offset(),
        SortBy: f.SortBy,
        Order:  f.Order,
    }
}

// Response DTOs
type UserResponse struct {
    ID        string    `json:"id"`
    Email     string    `json:"email"`
    Name      string    `json:"name"`
    Status    string    `json:"status"`
    Role      string    `json:"role"`
    CreatedAt time.Time `json:"created_at"`
    UpdatedAt time.Time `json:"updated_at"`
}

func NewUserResponse(u *user.User) *UserResponse {
    return &UserResponse{
        ID:        u.ID.String(),
        Email:     string(u.Email),
        Name:      u.Name,
        Status:    string(u.Status),
        Role:      string(u.Role),
        CreatedAt: u.CreatedAt,
        UpdatedAt: u.UpdatedAt,
    }
}

type UserListResponse struct {
    Items      []*UserResponse `json:"items"`
    Total      int64           `json:"total"`
    Page       int             `json:"page"`
    PerPage    int             `json:"per_page"`
    TotalPages int             `json:"total_pages"`
}

func NewUserListResponse(users []*user.User, total int64, filter *UserFilter) *UserListResponse {
    items := make([]*UserResponse, len(users))
    for i, u := range users {
        items[i] = NewUserResponse(u)
    }

    totalPages := int(total) / filter.PerPage
    if int(total)%filter.PerPage > 0 {
        totalPages++
    }

    return &UserListResponse{
        Items:      items,
        Total:      total,
        Page:       filter.Page,
        PerPage:    filter.PerPage,
        TotalPages: totalPages,
    }
}
```

## Usage

```bash
# Generate user DTOs
f5 generate dto User --create-fields "email,name,password" \
  --update-fields "name,status" \
  --filter-fields "search,status,role"
```
