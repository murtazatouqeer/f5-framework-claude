# CRUD API Example

Complete example of a RESTful CRUD API in Go using Gin and PostgreSQL.

## Project Structure

```
crud-api/
├── cmd/
│   └── server/
│       └── main.go
├── internal/
│   ├── config/
│   │   └── config.go
│   ├── domain/
│   │   └── product/
│   │       ├── product.go
│   │       ├── repository.go
│   │       └── errors.go
│   ├── dto/
│   │   └── product_dto.go
│   ├── handler/
│   │   └── product_handler.go
│   ├── repository/
│   │   └── postgres/
│   │       └── product_repository.go
│   ├── service/
│   │   └── product_service.go
│   └── middleware/
│       └── middleware.go
├── pkg/
│   ├── database/
│   │   └── postgres.go
│   └── response/
│       └── response.go
├── migrations/
│   ├── 001_create_products.up.sql
│   └── 001_create_products.down.sql
├── config/
│   └── config.yaml
├── go.mod
└── Makefile
```

## Domain Layer

```go
// internal/domain/product/product.go
package product

import (
    "time"

    "github.com/google/uuid"
    "github.com/shopspring/decimal"
)

type Status string

const (
    StatusActive   Status = "active"
    StatusInactive Status = "inactive"
    StatusDraft    Status = "draft"
)

type Product struct {
    ID          uuid.UUID       `json:"id"`
    Name        string          `json:"name"`
    Description string          `json:"description"`
    Price       decimal.Decimal `json:"price"`
    Stock       int             `json:"stock"`
    Status      Status          `json:"status"`
    CategoryID  uuid.UUID       `json:"category_id"`
    CreatedAt   time.Time       `json:"created_at"`
    UpdatedAt   time.Time       `json:"updated_at"`
    DeletedAt   *time.Time      `json:"deleted_at,omitempty"`
}

func New(name, description string, price decimal.Decimal, stock int, categoryID uuid.UUID) (*Product, error) {
    now := time.Now()

    p := &Product{
        ID:          uuid.New(),
        Name:        name,
        Description: description,
        Price:       price,
        Stock:       stock,
        Status:      StatusDraft,
        CategoryID:  categoryID,
        CreatedAt:   now,
        UpdatedAt:   now,
    }

    if err := p.Validate(); err != nil {
        return nil, err
    }

    return p, nil
}

func (p *Product) Validate() error {
    if p.Name == "" {
        return ErrInvalidName
    }
    if p.Price.IsNegative() {
        return ErrInvalidPrice
    }
    if p.Stock < 0 {
        return ErrInvalidStock
    }
    return nil
}

func (p *Product) Activate() {
    p.Status = StatusActive
    p.UpdatedAt = time.Now()
}

func (p *Product) Deactivate() {
    p.Status = StatusInactive
    p.UpdatedAt = time.Now()
}

func (p *Product) UpdateStock(quantity int) error {
    newStock := p.Stock + quantity
    if newStock < 0 {
        return ErrInsufficientStock
    }
    p.Stock = newStock
    p.UpdatedAt = time.Now()
    return nil
}

// internal/domain/product/errors.go
package product

import "errors"

var (
    ErrNotFound          = errors.New("product not found")
    ErrInvalidName       = errors.New("invalid product name")
    ErrInvalidPrice      = errors.New("price must be non-negative")
    ErrInvalidStock      = errors.New("stock must be non-negative")
    ErrInsufficientStock = errors.New("insufficient stock")
    ErrAlreadyExists     = errors.New("product already exists")
)

// internal/domain/product/repository.go
package product

import (
    "context"

    "github.com/google/uuid"
)

type Repository interface {
    Create(ctx context.Context, product *Product) error
    GetByID(ctx context.Context, id uuid.UUID) (*Product, error)
    Update(ctx context.Context, product *Product) error
    Delete(ctx context.Context, id uuid.UUID) error
    List(ctx context.Context, filter Filter) ([]*Product, int64, error)
}

type Filter struct {
    Search     *string
    CategoryID *uuid.UUID
    Status     *Status
    MinPrice   *decimal.Decimal
    MaxPrice   *decimal.Decimal
    Limit      int
    Offset     int
    SortBy     string
    Order      string
}
```

## DTO Layer

```go
// internal/dto/product_dto.go
package dto

import (
    "time"

    "github.com/shopspring/decimal"

    "myproject/internal/domain/product"
)

type CreateProductRequest struct {
    Name        string          `json:"name" validate:"required,min=2,max=200"`
    Description string          `json:"description" validate:"max=2000"`
    Price       decimal.Decimal `json:"price" validate:"required"`
    Stock       int             `json:"stock" validate:"gte=0"`
    CategoryID  string          `json:"category_id" validate:"required,uuid"`
}

type UpdateProductRequest struct {
    Name        *string          `json:"name" validate:"omitempty,min=2,max=200"`
    Description *string          `json:"description" validate:"omitempty,max=2000"`
    Price       *decimal.Decimal `json:"price"`
    Stock       *int             `json:"stock" validate:"omitempty,gte=0"`
    Status      *string          `json:"status" validate:"omitempty,oneof=active inactive draft"`
}

type ProductFilter struct {
    Search     *string `form:"search"`
    CategoryID *string `form:"category_id" validate:"omitempty,uuid"`
    Status     *string `form:"status" validate:"omitempty,oneof=active inactive draft"`
    MinPrice   *string `form:"min_price"`
    MaxPrice   *string `form:"max_price"`
    Page       int     `form:"page" validate:"gte=1"`
    PerPage    int     `form:"per_page" validate:"gte=1,lte=100"`
    SortBy     string  `form:"sort_by" validate:"omitempty,oneof=created_at updated_at name price"`
    Order      string  `form:"order" validate:"omitempty,oneof=asc desc"`
}

func (f *ProductFilter) SetDefaults() {
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

type ProductResponse struct {
    ID          string          `json:"id"`
    Name        string          `json:"name"`
    Description string          `json:"description"`
    Price       decimal.Decimal `json:"price"`
    Stock       int             `json:"stock"`
    Status      string          `json:"status"`
    CategoryID  string          `json:"category_id"`
    CreatedAt   time.Time       `json:"created_at"`
    UpdatedAt   time.Time       `json:"updated_at"`
}

func NewProductResponse(p *product.Product) *ProductResponse {
    return &ProductResponse{
        ID:          p.ID.String(),
        Name:        p.Name,
        Description: p.Description,
        Price:       p.Price,
        Stock:       p.Stock,
        Status:      string(p.Status),
        CategoryID:  p.CategoryID.String(),
        CreatedAt:   p.CreatedAt,
        UpdatedAt:   p.UpdatedAt,
    }
}

type ProductListResponse struct {
    Items      []*ProductResponse `json:"items"`
    Total      int64              `json:"total"`
    Page       int                `json:"page"`
    PerPage    int                `json:"per_page"`
    TotalPages int                `json:"total_pages"`
}

func NewProductListResponse(products []*product.Product, total int64, filter *ProductFilter) *ProductListResponse {
    items := make([]*ProductResponse, len(products))
    for i, p := range products {
        items[i] = NewProductResponse(p)
    }

    totalPages := int(total) / filter.PerPage
    if int(total)%filter.PerPage > 0 {
        totalPages++
    }

    return &ProductListResponse{
        Items:      items,
        Total:      total,
        Page:       filter.Page,
        PerPage:    filter.PerPage,
        TotalPages: totalPages,
    }
}
```

## Service Layer

```go
// internal/service/product_service.go
package service

import (
    "context"
    "fmt"

    "github.com/google/uuid"
    "github.com/shopspring/decimal"

    "myproject/internal/domain/product"
    "myproject/internal/dto"
    "myproject/pkg/errors"
)

type ProductService struct {
    repo product.Repository
}

func NewProductService(repo product.Repository) *ProductService {
    return &ProductService{repo: repo}
}

func (s *ProductService) Create(ctx context.Context, req dto.CreateProductRequest) (*product.Product, error) {
    categoryID, err := uuid.Parse(req.CategoryID)
    if err != nil {
        return nil, errors.ErrInvalidInput.WithMessage("invalid category ID")
    }

    p, err := product.New(req.Name, req.Description, req.Price, req.Stock, categoryID)
    if err != nil {
        return nil, errors.Wrap(err, "creating product")
    }

    if err := s.repo.Create(ctx, p); err != nil {
        return nil, errors.Wrap(err, "saving product")
    }

    return p, nil
}

func (s *ProductService) GetByID(ctx context.Context, id string) (*product.Product, error) {
    uid, err := uuid.Parse(id)
    if err != nil {
        return nil, errors.ErrInvalidInput.WithMessage("invalid product ID")
    }

    p, err := s.repo.GetByID(ctx, uid)
    if err != nil {
        if errors.Is(err, product.ErrNotFound) {
            return nil, errors.ErrNotFound.WithMessagef("product %s not found", id)
        }
        return nil, errors.Wrap(err, "getting product")
    }

    return p, nil
}

func (s *ProductService) Update(ctx context.Context, id string, req dto.UpdateProductRequest) (*product.Product, error) {
    p, err := s.GetByID(ctx, id)
    if err != nil {
        return nil, err
    }

    if req.Name != nil {
        p.Name = *req.Name
    }
    if req.Description != nil {
        p.Description = *req.Description
    }
    if req.Price != nil {
        p.Price = *req.Price
    }
    if req.Stock != nil {
        p.Stock = *req.Stock
    }
    if req.Status != nil {
        p.Status = product.Status(*req.Status)
    }

    if err := p.Validate(); err != nil {
        return nil, errors.Wrap(err, "validating product")
    }

    if err := s.repo.Update(ctx, p); err != nil {
        return nil, errors.Wrap(err, "updating product")
    }

    return p, nil
}

func (s *ProductService) Delete(ctx context.Context, id string) error {
    uid, err := uuid.Parse(id)
    if err != nil {
        return errors.ErrInvalidInput.WithMessage("invalid product ID")
    }

    if err := s.repo.Delete(ctx, uid); err != nil {
        if errors.Is(err, product.ErrNotFound) {
            return errors.ErrNotFound.WithMessagef("product %s not found", id)
        }
        return errors.Wrap(err, "deleting product")
    }

    return nil
}

func (s *ProductService) List(ctx context.Context, filter dto.ProductFilter) (*dto.ProductListResponse, error) {
    filter.SetDefaults()

    domainFilter := product.Filter{
        Search: filter.Search,
        Limit:  filter.PerPage,
        Offset: (filter.Page - 1) * filter.PerPage,
        SortBy: filter.SortBy,
        Order:  filter.Order,
    }

    if filter.CategoryID != nil {
        id, _ := uuid.Parse(*filter.CategoryID)
        domainFilter.CategoryID = &id
    }
    if filter.Status != nil {
        status := product.Status(*filter.Status)
        domainFilter.Status = &status
    }

    products, total, err := s.repo.List(ctx, domainFilter)
    if err != nil {
        return nil, errors.Wrap(err, "listing products")
    }

    return dto.NewProductListResponse(products, total, &filter), nil
}
```

## Handler Layer

```go
// internal/handler/product_handler.go
package handler

import (
    "net/http"

    "github.com/gin-gonic/gin"

    "myproject/internal/dto"
    "myproject/internal/service"
    "myproject/pkg/response"
    "myproject/pkg/validator"
)

type ProductHandler struct {
    service *service.ProductService
}

func NewProductHandler(service *service.ProductService) *ProductHandler {
    return &ProductHandler{service: service}
}

func (h *ProductHandler) Create(c *gin.Context) {
    var req dto.CreateProductRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        response.Error(c, http.StatusBadRequest, "INVALID_JSON", err.Error())
        return
    }

    if err := validator.Struct(&req); err != nil {
        response.ValidationError(c, validator.FormatErrors(err))
        return
    }

    product, err := h.service.Create(c.Request.Context(), req)
    if err != nil {
        response.HandleError(c, err)
        return
    }

    response.Success(c, http.StatusCreated, dto.NewProductResponse(product))
}

func (h *ProductHandler) GetByID(c *gin.Context) {
    id := c.Param("id")

    product, err := h.service.GetByID(c.Request.Context(), id)
    if err != nil {
        response.HandleError(c, err)
        return
    }

    response.Success(c, http.StatusOK, dto.NewProductResponse(product))
}

func (h *ProductHandler) Update(c *gin.Context) {
    id := c.Param("id")

    var req dto.UpdateProductRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        response.Error(c, http.StatusBadRequest, "INVALID_JSON", err.Error())
        return
    }

    if err := validator.Struct(&req); err != nil {
        response.ValidationError(c, validator.FormatErrors(err))
        return
    }

    product, err := h.service.Update(c.Request.Context(), id, req)
    if err != nil {
        response.HandleError(c, err)
        return
    }

    response.Success(c, http.StatusOK, dto.NewProductResponse(product))
}

func (h *ProductHandler) Delete(c *gin.Context) {
    id := c.Param("id")

    if err := h.service.Delete(c.Request.Context(), id); err != nil {
        response.HandleError(c, err)
        return
    }

    response.Success(c, http.StatusOK, gin.H{"message": "product deleted"})
}

func (h *ProductHandler) List(c *gin.Context) {
    var filter dto.ProductFilter
    if err := c.ShouldBindQuery(&filter); err != nil {
        response.Error(c, http.StatusBadRequest, "INVALID_QUERY", err.Error())
        return
    }

    result, err := h.service.List(c.Request.Context(), filter)
    if err != nil {
        response.HandleError(c, err)
        return
    }

    response.Success(c, http.StatusOK, result)
}

// RegisterRoutes registers all product routes
func (h *ProductHandler) RegisterRoutes(r *gin.RouterGroup) {
    products := r.Group("/products")
    {
        products.POST("", h.Create)
        products.GET("", h.List)
        products.GET("/:id", h.GetByID)
        products.PUT("/:id", h.Update)
        products.DELETE("/:id", h.Delete)
    }
}
```

## Main Entry Point

```go
// cmd/server/main.go
package main

import (
    "context"
    "net/http"
    "os"
    "os/signal"
    "syscall"
    "time"

    "github.com/gin-gonic/gin"
    "go.uber.org/zap"

    "myproject/internal/config"
    "myproject/internal/handler"
    "myproject/internal/middleware"
    "myproject/internal/repository/postgres"
    "myproject/internal/service"
    "myproject/pkg/database"
)

func main() {
    // Load config
    cfg, err := config.Load("")
    if err != nil {
        panic(err)
    }

    // Setup logger
    logger, _ := zap.NewProduction()
    defer logger.Sync()

    // Setup database
    db, err := database.NewPostgres(cfg.Database)
    if err != nil {
        logger.Fatal("Failed to connect to database", zap.Error(err))
    }
    defer db.Close()

    // Setup repositories
    productRepo := postgres.NewProductRepository(db)

    // Setup services
    productService := service.NewProductService(productRepo)

    // Setup handlers
    productHandler := handler.NewProductHandler(productService)

    // Setup router
    router := gin.New()
    router.Use(middleware.Recovery(logger))
    router.Use(middleware.RequestID())
    router.Use(middleware.Logger(logger))

    // Register routes
    api := router.Group("/api/v1")
    productHandler.RegisterRoutes(api)

    // Start server
    server := &http.Server{
        Addr:         cfg.Server.Addr(),
        Handler:      router,
        ReadTimeout:  cfg.Server.ReadTimeout,
        WriteTimeout: cfg.Server.WriteTimeout,
    }

    go func() {
        logger.Info("Starting server", zap.String("addr", server.Addr))
        if err := server.ListenAndServe(); err != http.ErrServerClosed {
            logger.Fatal("Server error", zap.Error(err))
        }
    }()

    // Graceful shutdown
    quit := make(chan os.Signal, 1)
    signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
    <-quit

    ctx, cancel := context.WithTimeout(context.Background(), cfg.Server.ShutdownTimeout)
    defer cancel()

    if err := server.Shutdown(ctx); err != nil {
        logger.Error("Server shutdown error", zap.Error(err))
    }

    logger.Info("Server stopped")
}
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/products | Create a new product |
| GET | /api/v1/products | List products with filters |
| GET | /api/v1/products/:id | Get product by ID |
| PUT | /api/v1/products/:id | Update product |
| DELETE | /api/v1/products/:id | Delete product |
