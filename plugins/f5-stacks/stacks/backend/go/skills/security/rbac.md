# Role-Based Access Control (RBAC)

Implementing RBAC in Go applications.

## RBAC Model

```go
// internal/domain/auth/rbac.go
package auth

type Role string

const (
    RoleAdmin     Role = "admin"
    RoleModerator Role = "moderator"
    RoleUser      Role = "user"
    RoleGuest     Role = "guest"
)

type Permission string

const (
    // User permissions
    PermUserRead   Permission = "user:read"
    PermUserCreate Permission = "user:create"
    PermUserUpdate Permission = "user:update"
    PermUserDelete Permission = "user:delete"

    // Post permissions
    PermPostRead   Permission = "post:read"
    PermPostCreate Permission = "post:create"
    PermPostUpdate Permission = "post:update"
    PermPostDelete Permission = "post:delete"

    // Admin permissions
    PermAdminPanel Permission = "admin:panel"
    PermAdminUsers Permission = "admin:users"
)

// RolePermissions maps roles to their permissions
var RolePermissions = map[Role][]Permission{
    RoleAdmin: {
        PermUserRead, PermUserCreate, PermUserUpdate, PermUserDelete,
        PermPostRead, PermPostCreate, PermPostUpdate, PermPostDelete,
        PermAdminPanel, PermAdminUsers,
    },
    RoleModerator: {
        PermUserRead,
        PermPostRead, PermPostCreate, PermPostUpdate, PermPostDelete,
    },
    RoleUser: {
        PermUserRead, PermUserUpdate,
        PermPostRead, PermPostCreate,
    },
    RoleGuest: {
        PermPostRead,
    },
}

func HasPermission(role Role, permission Permission) bool {
    permissions, ok := RolePermissions[role]
    if !ok {
        return false
    }

    for _, p := range permissions {
        if p == permission {
            return true
        }
    }
    return false
}

func GetPermissions(role Role) []Permission {
    return RolePermissions[role]
}
```

## Authorization Middleware

```go
// internal/middleware/authorization.go
package middleware

import (
    "net/http"

    "github.com/gin-gonic/gin"

    "myproject/internal/domain/auth"
    "myproject/pkg/response"
)

// RequireRole checks if user has required role
func RequireRole(roles ...auth.Role) gin.HandlerFunc {
    return func(c *gin.Context) {
        userRole := auth.Role(c.GetString("role"))

        for _, role := range roles {
            if userRole == role {
                c.Next()
                return
            }
        }

        response.Error(c, http.StatusForbidden, "FORBIDDEN", "Insufficient role")
        c.Abort()
    }
}

// RequirePermission checks if user has required permission
func RequirePermission(permissions ...auth.Permission) gin.HandlerFunc {
    return func(c *gin.Context) {
        userRole := auth.Role(c.GetString("role"))

        for _, perm := range permissions {
            if !auth.HasPermission(userRole, perm) {
                response.Error(c, http.StatusForbidden, "FORBIDDEN", "Insufficient permissions")
                c.Abort()
                return
            }
        }

        c.Next()
    }
}

// RequireOwnership checks if user owns the resource
func RequireOwnership(getOwnerID func(*gin.Context) string) gin.HandlerFunc {
    return func(c *gin.Context) {
        userID := c.GetString("user_id")
        ownerID := getOwnerID(c)

        // Admin can access all
        if auth.Role(c.GetString("role")) == auth.RoleAdmin {
            c.Next()
            return
        }

        if userID != ownerID {
            response.Error(c, http.StatusForbidden, "FORBIDDEN", "Access denied")
            c.Abort()
            return
        }

        c.Next()
    }
}
```

## Resource-Based Authorization

```go
// internal/middleware/resource_auth.go
package middleware

import (
    "net/http"

    "github.com/gin-gonic/gin"

    "myproject/internal/domain/auth"
    "myproject/internal/domain/post"
    "myproject/pkg/response"
)

type ResourceAuthorizer struct {
    postRepo post.Repository
}

func NewResourceAuthorizer(postRepo post.Repository) *ResourceAuthorizer {
    return &ResourceAuthorizer{postRepo: postRepo}
}

// CanAccessPost checks if user can access the post
func (a *ResourceAuthorizer) CanAccessPost(action auth.Permission) gin.HandlerFunc {
    return func(c *gin.Context) {
        userID := c.GetString("user_id")
        userRole := auth.Role(c.GetString("role"))
        postID := c.Param("id")

        // Check role permission first
        if !auth.HasPermission(userRole, action) {
            response.Error(c, http.StatusForbidden, "FORBIDDEN", "Permission denied")
            c.Abort()
            return
        }

        // For read, allow if has permission
        if action == auth.PermPostRead {
            c.Next()
            return
        }

        // For write operations, check ownership
        p, err := a.postRepo.GetByID(c.Request.Context(), postID)
        if err != nil {
            if err == post.ErrNotFound {
                response.Error(c, http.StatusNotFound, "NOT_FOUND", "Post not found")
            } else {
                response.Error(c, http.StatusInternalServerError, "INTERNAL_ERROR", "Server error")
            }
            c.Abort()
            return
        }

        // Admin can modify any post
        if userRole == auth.RoleAdmin {
            c.Set("post", p)
            c.Next()
            return
        }

        // Check ownership
        if p.AuthorID.String() != userID {
            response.Error(c, http.StatusForbidden, "FORBIDDEN", "Not authorized to modify this post")
            c.Abort()
            return
        }

        c.Set("post", p)
        c.Next()
    }
}
```

## Policy-Based Authorization

```go
// internal/auth/policy.go
package auth

import (
    "context"

    "myproject/internal/domain/user"
    "myproject/internal/domain/post"
)

type Policy interface {
    CanCreate(ctx context.Context, actor *user.User) bool
    CanRead(ctx context.Context, actor *user.User, resource interface{}) bool
    CanUpdate(ctx context.Context, actor *user.User, resource interface{}) bool
    CanDelete(ctx context.Context, actor *user.User, resource interface{}) bool
}

// PostPolicy defines authorization rules for posts
type PostPolicy struct{}

func (p *PostPolicy) CanCreate(ctx context.Context, actor *user.User) bool {
    return actor != nil && actor.Status == user.StatusActive
}

func (p *PostPolicy) CanRead(ctx context.Context, actor *user.User, resource interface{}) bool {
    post := resource.(*post.Post)

    // Published posts are public
    if post.Status == post.StatusPublished {
        return true
    }

    // Draft posts only visible to author or admin
    if actor == nil {
        return false
    }

    return actor.ID == post.AuthorID || actor.Role == user.RoleAdmin
}

func (p *PostPolicy) CanUpdate(ctx context.Context, actor *user.User, resource interface{}) bool {
    if actor == nil {
        return false
    }

    post := resource.(*post.Post)

    // Admin can update any post
    if actor.Role == user.RoleAdmin {
        return true
    }

    // Author can update own post
    return actor.ID == post.AuthorID
}

func (p *PostPolicy) CanDelete(ctx context.Context, actor *user.User, resource interface{}) bool {
    if actor == nil {
        return false
    }

    // Only admin can delete
    if actor.Role == user.RoleAdmin {
        return true
    }

    post := resource.(*post.Post)

    // Or author can delete own post
    return actor.ID == post.AuthorID
}

// Usage in service
func (s *PostService) Update(ctx context.Context, id string, input UpdatePostInput) (*post.Post, error) {
    actor := GetUserFromContext(ctx)

    p, err := s.repo.GetByID(ctx, id)
    if err != nil {
        return nil, err
    }

    policy := &PostPolicy{}
    if !policy.CanUpdate(ctx, actor, p) {
        return nil, ErrUnauthorized
    }

    // Proceed with update
    p.Title = input.Title
    p.Content = input.Content
    // ...

    return p, s.repo.Update(ctx, p)
}
```

## Route Configuration

```go
// internal/handler/router.go
package handler

import (
    "github.com/gin-gonic/gin"

    "myproject/internal/domain/auth"
    "myproject/internal/middleware"
)

func SetupRoutes(r *gin.Engine, h *Handlers, m *Middlewares) {
    // Public routes
    public := r.Group("/api/v1")
    {
        public.POST("/auth/register", h.Auth.Register)
        public.POST("/auth/login", h.Auth.Login)
        public.POST("/auth/refresh", h.Auth.Refresh)

        public.GET("/posts", h.Post.List)
        public.GET("/posts/:id", h.Post.Get)
    }

    // Authenticated routes
    authenticated := r.Group("/api/v1")
    authenticated.Use(m.Auth.Authenticate())
    {
        authenticated.POST("/auth/logout", h.Auth.Logout)
        authenticated.GET("/auth/me", h.Auth.Me)

        // User routes
        authenticated.GET("/users/:id", h.User.Get)
        authenticated.PUT("/users/:id",
            middleware.RequireOwnership(func(c *gin.Context) string {
                return c.Param("id")
            }),
            h.User.Update,
        )

        // Post routes
        authenticated.POST("/posts",
            middleware.RequirePermission(auth.PermPostCreate),
            h.Post.Create,
        )
        authenticated.PUT("/posts/:id",
            m.ResourceAuth.CanAccessPost(auth.PermPostUpdate),
            h.Post.Update,
        )
        authenticated.DELETE("/posts/:id",
            m.ResourceAuth.CanAccessPost(auth.PermPostDelete),
            h.Post.Delete,
        )
    }

    // Admin routes
    admin := r.Group("/api/v1/admin")
    admin.Use(m.Auth.Authenticate())
    admin.Use(middleware.RequireRole(auth.RoleAdmin))
    {
        admin.GET("/users", h.Admin.ListUsers)
        admin.PUT("/users/:id", h.Admin.UpdateUser)
        admin.DELETE("/users/:id", h.Admin.DeleteUser)
        admin.GET("/dashboard", h.Admin.Dashboard)
    }
}
```

## Best Practices

1. **Least Privilege**: Grant minimum required permissions
2. **Role Hierarchy**: Define clear role hierarchy
3. **Resource Ownership**: Check resource ownership for mutations
4. **Policy Objects**: Encapsulate authorization logic
5. **Audit Trail**: Log authorization decisions
6. **Defense in Depth**: Check permissions at multiple layers
