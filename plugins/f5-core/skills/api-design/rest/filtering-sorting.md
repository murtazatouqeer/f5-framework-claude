---
name: filtering-sorting
description: REST API filtering and sorting patterns
category: api-design/rest
applies_to: [all]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Filtering and Sorting

## Overview

Filtering and sorting allow clients to retrieve specific subsets of data
efficiently. Well-designed query parameters make APIs flexible and powerful.

## Filtering Patterns

### Simple Equality Filters

```http
# Single value
GET /api/v1/users?status=active

# Multiple values (OR)
GET /api/v1/users?status=active,pending

# Multiple filters (AND)
GET /api/v1/users?status=active&role=admin
```

### Comparison Operators

```http
# Greater than
GET /api/v1/products?price_gt=100

# Less than
GET /api/v1/products?price_lt=500

# Greater than or equal
GET /api/v1/orders?created_at_gte=2024-01-01

# Less than or equal
GET /api/v1/orders?created_at_lte=2024-12-31

# Between (range)
GET /api/v1/products?price_min=100&price_max=500
GET /api/v1/orders?created_after=2024-01-01&created_before=2024-12-31

# Not equal
GET /api/v1/users?status_ne=deleted
```

### Pattern Matching

```http
# Contains (case-insensitive)
GET /api/v1/users?name_contains=john

# Starts with
GET /api/v1/products?sku_starts_with=ELEC

# Ends with
GET /api/v1/files?filename_ends_with=.pdf

# Full-text search
GET /api/v1/articles?q=machine+learning
```

### Array/Set Operations

```http
# Value in array
GET /api/v1/products?category_in=electronics,clothing

# Value not in array
GET /api/v1/users?role_not_in=guest,banned

# Has any of (array field)
GET /api/v1/products?tags_any=sale,featured

# Has all of (array field)
GET /api/v1/products?tags_all=organic,vegan
```

### Null Checks

```http
# Is null
GET /api/v1/users?deleted_at_is_null=true

# Is not null
GET /api/v1/orders?shipped_at_is_null=false

# Alternative syntax
GET /api/v1/users?deleted_at=null
GET /api/v1/orders?shipped_at=!null
```

## Filter Syntax Styles

### Flat Style (Simple)

```http
GET /api/v1/products?status=active&price_min=100&price_max=500
```

### Bracket Style (JSON:API)

```http
GET /api/v1/products?filter[status]=active&filter[price][gte]=100&filter[price][lte]=500
```

### LHS Brackets

```http
GET /api/v1/products?status[eq]=active&price[gte]=100&price[lte]=500
```

### RHS Colon

```http
GET /api/v1/products?status=eq:active&price=gte:100,lte:500
```

## Filter Implementation

```typescript
interface FilterParams {
  [key: string]: string | string[] | undefined;
}

interface FilterConfig {
  allowed: string[];
  operators: Record<string, string>;
}

const filterConfig: FilterConfig = {
  allowed: ['status', 'role', 'name', 'email', 'created_at', 'price'],
  operators: {
    eq: '=',
    ne: '!=',
    gt: '>',
    gte: '>=',
    lt: '<',
    lte: '<=',
    like: 'LIKE',
    in: 'IN',
    not_in: 'NOT IN',
    is_null: 'IS NULL',
    is_not_null: 'IS NOT NULL',
  },
};

function parseFilters(params: FilterParams): QueryCondition[] {
  const conditions: QueryCondition[] = [];

  for (const [key, value] of Object.entries(params)) {
    if (!value) continue;

    // Parse key_operator format (e.g., price_gte)
    const match = key.match(/^(\w+)_(eq|ne|gt|gte|lt|lte|like|in|not_in|is_null|is_not_null)$/);

    if (match) {
      const [, field, operator] = match;

      if (!filterConfig.allowed.includes(field)) {
        throw new ApiError('INVALID_FILTER', `Filter on '${field}' not allowed`);
      }

      conditions.push({
        field,
        operator: filterConfig.operators[operator],
        value: operator === 'in' || operator === 'not_in'
          ? value.split(',')
          : value,
      });
    } else if (filterConfig.allowed.includes(key)) {
      // Simple equality
      const values = Array.isArray(value) ? value : value.split(',');

      if (values.length === 1) {
        conditions.push({ field: key, operator: '=', value: values[0] });
      } else {
        conditions.push({ field: key, operator: 'IN', value: values });
      }
    }
  }

  return conditions;
}

// SQL builder
function buildWhereClause(conditions: QueryCondition[]): { sql: string; params: any[] } {
  if (conditions.length === 0) {
    return { sql: '', params: [] };
  }

  const clauses: string[] = [];
  const params: any[] = [];

  for (const condition of conditions) {
    if (condition.operator === 'IN' || condition.operator === 'NOT IN') {
      const placeholders = condition.value.map(() => '?').join(', ');
      clauses.push(`${condition.field} ${condition.operator} (${placeholders})`);
      params.push(...condition.value);
    } else if (condition.operator === 'IS NULL' || condition.operator === 'IS NOT NULL') {
      clauses.push(`${condition.field} ${condition.operator}`);
    } else if (condition.operator === 'LIKE') {
      clauses.push(`${condition.field} LIKE ?`);
      params.push(`%${condition.value}%`);
    } else {
      clauses.push(`${condition.field} ${condition.operator} ?`);
      params.push(condition.value);
    }
  }

  return {
    sql: `WHERE ${clauses.join(' AND ')}`,
    params,
  };
}
```

## Sorting Patterns

### Single Field Sorting

```http
# Ascending (default)
GET /api/v1/users?sort=name

# Descending
GET /api/v1/users?sort=-created_at

# Explicit direction
GET /api/v1/users?sort=name&order=asc
GET /api/v1/users?sort=name&order=desc
```

### Multi-Field Sorting

```http
# Comma-separated
GET /api/v1/users?sort=-created_at,name

# Multiple parameters
GET /api/v1/users?sort[]=created_at&sort[]=-name

# With explicit directions
GET /api/v1/products?sort=category:asc,price:desc
```

### Sort Implementation

```typescript
interface SortParams {
  sort?: string;
  order?: 'asc' | 'desc';
}

interface SortConfig {
  allowed: string[];
  default: string;
  maxFields: number;
}

const sortConfig: SortConfig = {
  allowed: ['id', 'name', 'email', 'created_at', 'updated_at', 'price', 'status'],
  default: '-created_at',
  maxFields: 3,
};

interface SortField {
  field: string;
  direction: 'asc' | 'desc';
}

function parseSortParams(params: SortParams): SortField[] {
  const sortString = params.sort || sortConfig.default;
  const fields = sortString.split(',').slice(0, sortConfig.maxFields);

  return fields.map(field => {
    const descending = field.startsWith('-');
    const fieldName = descending ? field.slice(1) : field;

    if (!sortConfig.allowed.includes(fieldName)) {
      throw new ApiError('INVALID_SORT', `Sorting by '${fieldName}' not allowed`);
    }

    return {
      field: fieldName,
      direction: descending ? 'desc' : 'asc',
    };
  });
}

function buildOrderByClause(sortFields: SortField[]): string {
  if (sortFields.length === 0) {
    return '';
  }

  const clauses = sortFields.map(
    ({ field, direction }) => `${field} ${direction.toUpperCase()}`
  );

  return `ORDER BY ${clauses.join(', ')}`;
}

// Usage in Express
app.get('/users', async (req, res) => {
  const sortFields = parseSortParams(req.query);
  const orderBy = buildOrderByClause(sortFields);

  const users = await db.query(`SELECT * FROM users ${orderBy} LIMIT 20`);
  res.json({ data: users });
});
```

## Field Selection

### Sparse Fieldsets

```http
# Only return specific fields
GET /api/v1/users?fields=id,name,email

# JSON:API style
GET /api/v1/users?fields[users]=id,name,email&fields[orders]=id,total

# GraphQL-like
GET /api/v1/users?select=id,name,email,orders(id,total)
```

### Excluding Fields

```http
# Exclude specific fields
GET /api/v1/users?exclude=password,internal_notes
```

### Field Selection Implementation

```typescript
interface FieldSelectConfig {
  allowed: string[];
  default: string[];
  always: string[];  // Always included
  never: string[];   // Never exposed
}

const fieldConfig: FieldSelectConfig = {
  allowed: ['id', 'name', 'email', 'status', 'created_at', 'updated_at', 'profile'],
  default: ['id', 'name', 'email', 'status'],
  always: ['id'],
  never: ['password', 'internal_notes'],
};

function parseFields(params: { fields?: string }): string[] {
  if (!params.fields) {
    return fieldConfig.default;
  }

  const requested = params.fields.split(',');
  const fields = requested.filter(f =>
    fieldConfig.allowed.includes(f) && !fieldConfig.never.includes(f)
  );

  // Always include required fields
  return [...new Set([...fieldConfig.always, ...fields])];
}

function buildSelectClause(fields: string[]): string {
  return fields.join(', ');
}
```

## Include Related Resources

```http
# Include related resources
GET /api/v1/users?include=orders,profile

# Nested includes
GET /api/v1/orders?include=user,items.product

# JSON:API style
GET /api/v1/articles/1?include=author,comments.author
```

### Include Implementation

```typescript
interface IncludeConfig {
  allowed: Record<string, string[]>;  // Resource -> allowed includes
}

const includeConfig: IncludeConfig = {
  allowed: {
    users: ['orders', 'profile', 'settings'],
    orders: ['user', 'items', 'items.product', 'shipping'],
    products: ['category', 'variants', 'reviews'],
  },
};

async function loadIncludes(
  resource: string,
  data: any[],
  includes: string[]
): Promise<Record<string, any[]>> {
  const allowedIncludes = includeConfig.allowed[resource] || [];
  const validIncludes = includes.filter(i => allowedIncludes.includes(i));

  const result: Record<string, any[]> = {};

  for (const include of validIncludes) {
    if (include.includes('.')) {
      // Nested include (e.g., items.product)
      const [parent, child] = include.split('.');
      // Load parent first, then child
    } else {
      // Direct include
      const ids = data.map(item => item[`${include}_id`]).filter(Boolean);
      if (ids.length > 0) {
        result[include] = await loadRelation(include, ids);
      }
    }
  }

  return result;
}
```

## Search

### Simple Search

```http
# Query parameter
GET /api/v1/products?q=laptop

# Dedicated search endpoint
GET /api/v1/products/search?q=laptop+gaming
POST /api/v1/products/search
{
  "query": "laptop gaming",
  "filters": {"price_max": 1500}
}
```

### Advanced Search

```http
GET /api/v1/products?q=laptop&search_fields=name,description&match=any
```

### Search Implementation

```typescript
interface SearchParams {
  q?: string;
  search_fields?: string;
  match?: 'all' | 'any';
}

const searchConfig = {
  defaultFields: ['name', 'description'],
  allowedFields: ['name', 'description', 'sku', 'tags'],
};

function buildSearchQuery(params: SearchParams): QueryCondition | null {
  if (!params.q) return null;

  const fields = params.search_fields
    ? params.search_fields.split(',').filter(f => searchConfig.allowedFields.includes(f))
    : searchConfig.defaultFields;

  const terms = params.q.split(/\s+/).filter(Boolean);
  const matchAll = params.match !== 'any';

  // PostgreSQL full-text search
  if (matchAll) {
    return {
      sql: `to_tsvector('english', ${fields.join(" || ' ' || ")}) @@ plainto_tsquery('english', ?)`,
      value: terms.join(' & '),
    };
  } else {
    return {
      sql: `to_tsvector('english', ${fields.join(" || ' ' || ")}) @@ plainto_tsquery('english', ?)`,
      value: terms.join(' | '),
    };
  }
}
```

## Combined Example

```http
GET /api/v1/products?
  status=active&
  category_in=electronics,computers&
  price_gte=100&
  price_lte=2000&
  q=laptop&
  sort=-popularity,price&
  fields=id,name,price,rating&
  include=category,reviews&
  page=1&
  limit=20

HTTP/1.1 200 OK

{
  "data": [
    {
      "id": "prod_123",
      "name": "Gaming Laptop",
      "price": 1299.99,
      "rating": 4.5
    }
  ],
  "included": {
    "category": [{"id": "cat_1", "name": "Electronics"}],
    "reviews": [...]
  },
  "meta": {
    "total": 45,
    "page": 1,
    "limit": 20
  }
}
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│             Filtering & Sorting Best Practices                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Whitelist Allowed Fields                                    │
│     ├── Don't allow filtering on any field                      │
│     ├── Prevent SQL injection                                   │
│     └── Document allowed filters                                │
│                                                                  │
│  2. Index Filtered Columns                                      │
│     ├── Create indexes for commonly filtered fields             │
│     └── Composite indexes for combined filters                  │
│                                                                  │
│  3. Validate Input                                              │
│     ├── Type checking (dates, numbers)                          │
│     ├── Range limits                                            │
│     └── Sanitize strings                                        │
│                                                                  │
│  4. Set Sensible Defaults                                       │
│     ├── Default sort order                                      │
│     ├── Default fields returned                                 │
│     └── Default page size                                       │
│                                                                  │
│  5. Document Filter Syntax                                      │
│     ├── Available operators                                     │
│     ├── Field types and formats                                 │
│     └── Examples for common use cases                           │
│                                                                  │
│  6. Consider Performance                                        │
│     ├── Limit complexity of queries                             │
│     ├── Set maximum filters allowed                             │
│     └── Use caching for common queries                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```
