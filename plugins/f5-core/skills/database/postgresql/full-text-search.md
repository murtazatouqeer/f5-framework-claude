---
name: full-text-search
description: PostgreSQL full-text search capabilities
category: database/postgresql
applies_to: postgresql
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Full-Text Search in PostgreSQL

## Overview

PostgreSQL provides powerful built-in full-text search (FTS)
capabilities without requiring external tools like Elasticsearch
for many use cases.

## Core Concepts

```
┌─────────────────────────────────────────────────────────────────┐
│                   Full-Text Search Pipeline                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Document Text                                                   │
│       │                                                          │
│       ▼                                                          │
│  ┌─────────────┐                                                │
│  │   Parser    │  → Tokenize into words                         │
│  └─────────────┘                                                │
│       │                                                          │
│       ▼                                                          │
│  ┌─────────────┐                                                │
│  │ Dictionaries│  → Normalize tokens (stem, remove stopwords)   │
│  └─────────────┘                                                │
│       │                                                          │
│       ▼                                                          │
│  ┌─────────────┐                                                │
│  │  tsvector   │  → Sorted list of lexemes                      │
│  └─────────────┘                                                │
│                                                                  │
│  Search Query                                                    │
│       │                                                          │
│       ▼                                                          │
│  ┌─────────────┐                                                │
│  │  tsquery    │  → Normalized query terms + operators          │
│  └─────────────┘                                                │
│       │                                                          │
│       ▼                                                          │
│  ┌─────────────┐                                                │
│  │   Match     │  → tsvector @@ tsquery                         │
│  └─────────────┘                                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Basic Usage

### tsvector and tsquery

```sql
-- Create tsvector from text
SELECT to_tsvector('english', 'The quick brown fox jumps over the lazy dog');
-- Result: 'brown':3 'dog':9 'fox':4 'jump':5 'lazi':8 'quick':2

-- Create tsquery
SELECT to_tsquery('english', 'quick & brown');
-- Result: 'quick' & 'brown'

-- Match operator
SELECT to_tsvector('english', 'The quick brown fox')
    @@ to_tsquery('english', 'quick & brown');
-- Result: true

SELECT to_tsvector('english', 'The quick brown fox')
    @@ to_tsquery('english', 'quick & red');
-- Result: false
```

### tsquery Operators

```sql
-- AND: both terms required
SELECT to_tsquery('english', 'cat & dog');

-- OR: either term
SELECT to_tsquery('english', 'cat | dog');

-- NOT: exclude term
SELECT to_tsquery('english', 'cat & !dog');

-- Phrase (followed by): terms in order
SELECT to_tsquery('english', 'quick <-> brown');  -- Adjacent
SELECT to_tsquery('english', 'quick <2> fox');    -- Within 2 words

-- Grouping
SELECT to_tsquery('english', '(cat | dog) & !bird');

-- Prefix matching
SELECT to_tsquery('english', 'post:*');  -- Matches 'post', 'posts', 'posting'
```

### plainto_tsquery and phraseto_tsquery

```sql
-- plainto_tsquery: Simple query, ANDs terms
SELECT plainto_tsquery('english', 'quick brown fox');
-- Result: 'quick' & 'brown' & 'fox'

-- phraseto_tsquery: Phrase search
SELECT phraseto_tsquery('english', 'quick brown fox');
-- Result: 'quick' <-> 'brown' <-> 'fox'

-- websearch_to_tsquery (PostgreSQL 11+): Google-like syntax
SELECT websearch_to_tsquery('english', 'quick brown -lazy "exact phrase"');
-- Result: 'quick' & 'brown' & !'lazi' & 'exact' <-> 'phrase'
```

## Practical Implementation

### Basic Search Table

```sql
-- Create table with search column
CREATE TABLE articles (
  id SERIAL PRIMARY KEY,
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  author TEXT,
  published_at TIMESTAMPTZ DEFAULT NOW(),
  -- Stored tsvector for performance
  search_vector TSVECTOR
);

-- Function to generate search vector
CREATE OR REPLACE FUNCTION articles_search_vector(title TEXT, content TEXT, author TEXT)
RETURNS TSVECTOR AS $$
BEGIN
  RETURN
    setweight(to_tsvector('english', COALESCE(title, '')), 'A') ||
    setweight(to_tsvector('english', COALESCE(content, '')), 'B') ||
    setweight(to_tsvector('english', COALESCE(author, '')), 'C');
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Trigger to auto-update search vector
CREATE OR REPLACE FUNCTION articles_search_trigger()
RETURNS TRIGGER AS $$
BEGIN
  NEW.search_vector := articles_search_vector(NEW.title, NEW.content, NEW.author);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER articles_search_update
  BEFORE INSERT OR UPDATE OF title, content, author ON articles
  FOR EACH ROW
  EXECUTE FUNCTION articles_search_trigger();

-- Create GIN index
CREATE INDEX idx_articles_search ON articles USING GIN(search_vector);
```

### Search Queries

```sql
-- Basic search
SELECT id, title, author
FROM articles
WHERE search_vector @@ to_tsquery('english', 'postgresql & performance');

-- With ranking
SELECT
  id,
  title,
  ts_rank(search_vector, query) as rank
FROM articles,
  to_tsquery('english', 'postgresql & performance') query
WHERE search_vector @@ query
ORDER BY rank DESC;

-- With relevance highlighting
SELECT
  id,
  title,
  ts_headline('english', content, query,
    'StartSel=<mark>, StopSel=</mark>, MaxWords=35, MinWords=15'
  ) as snippet
FROM articles,
  websearch_to_tsquery('english', 'postgresql performance') query
WHERE search_vector @@ query
ORDER BY ts_rank(search_vector, query) DESC
LIMIT 10;
```

### Weighted Search

```sql
-- Weights: A (highest) > B > C > D (lowest)
-- Default weights: {0.1, 0.2, 0.4, 1.0} for D, C, B, A

-- Custom weights
SELECT
  id,
  title,
  ts_rank(
    '{0.1, 0.2, 0.4, 1.0}'::float4[],  -- D, C, B, A
    search_vector,
    query
  ) as rank
FROM articles,
  to_tsquery('english', 'postgresql') query
WHERE search_vector @@ query
ORDER BY rank DESC;

-- ts_rank_cd: Cover density ranking (considers proximity)
SELECT
  id,
  title,
  ts_rank_cd(search_vector, query) as rank
FROM articles,
  to_tsquery('english', 'postgresql & performance') query
WHERE search_vector @@ query
ORDER BY rank DESC;
```

## Text Search Configurations

### Available Configurations

```sql
-- List available configurations
SELECT cfgname FROM pg_ts_config;
-- simple, english, spanish, german, french, etc.

-- Check current default
SHOW default_text_search_config;
-- Result: 'pg_catalog.english'

-- Set session default
SET default_text_search_config = 'english';
```

### Configuration Details

```sql
-- View configuration details
SELECT
  alias,
  description
FROM ts_debug('english', 'The quick 123 test@email.com');

-- Result shows how each token is processed:
-- alias       | description
-- ------------|-------------
-- asciiword   | quick, test
-- blank       | (spaces)
-- numword     | 123
-- email       | test@email.com
```

### Custom Configuration

```sql
-- Create custom configuration
CREATE TEXT SEARCH CONFIGURATION my_english (COPY = english);

-- Add custom dictionary mappings
-- Example: Keep emails as single tokens
ALTER TEXT SEARCH CONFIGURATION my_english
  ALTER MAPPING FOR email WITH simple;

-- Create synonym dictionary
CREATE TEXT SEARCH DICTIONARY my_synonyms (
  TEMPLATE = synonym,
  SYNONYMS = my_synonyms  -- Points to file in $SHAREDIR/tsearch_data/
);

-- Example synonym file (my_synonyms.syn):
-- postgres postgresql pg
-- db database
```

## Advanced Features

### Generated Columns (PostgreSQL 12+)

```sql
-- Automatically maintained search column
CREATE TABLE products (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT,
  search_vector TSVECTOR GENERATED ALWAYS AS (
    setweight(to_tsvector('english', COALESCE(name, '')), 'A') ||
    setweight(to_tsvector('english', COALESCE(description, '')), 'B')
  ) STORED
);

CREATE INDEX idx_products_search ON products USING GIN(search_vector);
```

### Combining with Other Filters

```sql
-- Full-text search with additional filters
SELECT
  p.id,
  p.name,
  p.price,
  ts_rank(p.search_vector, query) as rank
FROM products p,
  websearch_to_tsquery('english', 'laptop gaming') query
WHERE p.search_vector @@ query
  AND p.price BETWEEN 500 AND 2000
  AND p.in_stock = true
  AND p.category_id IN (1, 2, 3)
ORDER BY rank DESC, p.rating DESC
LIMIT 20;
```

### Multi-Table Search

```sql
-- Search across multiple tables
WITH combined_search AS (
  SELECT
    'article' as type,
    id,
    title as name,
    search_vector
  FROM articles

  UNION ALL

  SELECT
    'product' as type,
    id,
    name,
    search_vector
  FROM products
)
SELECT
  type,
  id,
  name,
  ts_rank(search_vector, query) as rank
FROM combined_search,
  websearch_to_tsquery('english', 'search term') query
WHERE search_vector @@ query
ORDER BY rank DESC
LIMIT 20;
```

### Fuzzy Matching with pg_trgm

```sql
-- Enable trigram extension
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Create trigram index
CREATE INDEX idx_products_name_trgm ON products USING GIN(name gin_trgm_ops);

-- Similarity search (typo-tolerant)
SELECT name, similarity(name, 'laptpo') as sim
FROM products
WHERE name % 'laptpo'  -- Similarity above threshold
ORDER BY sim DESC;

-- Word similarity (better for partial matches)
SELECT name, word_similarity('lap', name) as sim
FROM products
WHERE 'lap' <% name
ORDER BY sim DESC;

-- Combined: Full-text + fuzzy
SELECT
  id,
  name,
  COALESCE(ts_rank(search_vector, query), 0) +
  similarity(name, 'laptop gaming') as combined_score
FROM products,
  websearch_to_tsquery('english', 'laptop gaming') query
WHERE search_vector @@ query
   OR name % 'laptop gaming'
ORDER BY combined_score DESC;
```

### Autocomplete

```sql
-- Prefix search for autocomplete
CREATE TABLE search_suggestions (
  id SERIAL PRIMARY KEY,
  term TEXT UNIQUE NOT NULL,
  frequency INT DEFAULT 1
);

CREATE INDEX idx_suggestions_trgm ON search_suggestions
  USING GIN(term gin_trgm_ops);

-- Query for autocomplete
SELECT term, frequency
FROM search_suggestions
WHERE term LIKE 'post%'  -- Prefix match
   OR term % 'post'      -- Fuzzy match
ORDER BY
  term LIKE 'post%' DESC,  -- Exact prefix first
  frequency DESC,          -- Then by popularity
  similarity(term, 'post') DESC
LIMIT 10;

-- Alternative: Using tsvector for prefix
SELECT DISTINCT title
FROM articles
WHERE search_vector @@ to_tsquery('english', 'post:*')
LIMIT 10;
```

## Performance Optimization

### Index Strategies

```sql
-- GIN index (recommended for most cases)
CREATE INDEX idx_articles_search ON articles USING GIN(search_vector);

-- GiST index (smaller, but slower)
CREATE INDEX idx_articles_search_gist ON articles USING GIST(search_vector);

-- Partial index for active content
CREATE INDEX idx_active_articles_search ON articles USING GIN(search_vector)
  WHERE status = 'published';

-- Expression index (no stored column)
CREATE INDEX idx_articles_search_expr ON articles
  USING GIN(to_tsvector('english', title || ' ' || content));
```

### Query Optimization

```sql
-- Check query plan
EXPLAIN ANALYZE
SELECT id, title
FROM articles
WHERE search_vector @@ to_tsquery('english', 'postgresql');

-- Limit before ranking (faster)
WITH matches AS (
  SELECT id, title, search_vector
  FROM articles
  WHERE search_vector @@ to_tsquery('english', 'postgresql')
  LIMIT 1000
)
SELECT id, title, ts_rank(search_vector, query) as rank
FROM matches,
  to_tsquery('english', 'postgresql') query
ORDER BY rank DESC
LIMIT 10;
```

### Maintenance

```sql
-- Update statistics
ANALYZE articles;

-- Check index size
SELECT
  indexname,
  pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_stat_user_indexes
WHERE tablename = 'articles';

-- Reindex if bloated
REINDEX INDEX CONCURRENTLY idx_articles_search;
```

## Common Patterns

### Search with Facets

```sql
-- Get search results with category counts
WITH search_results AS (
  SELECT id, category_id, search_vector
  FROM products
  WHERE search_vector @@ websearch_to_tsquery('english', 'laptop')
)
SELECT
  c.name as category,
  COUNT(*) as count
FROM search_results sr
JOIN categories c ON sr.category_id = c.id
GROUP BY c.id, c.name
ORDER BY count DESC;
```

### Recent + Relevance Hybrid

```sql
SELECT
  id,
  title,
  published_at,
  -- Combine relevance and recency
  ts_rank(search_vector, query) *
    (1 + 1.0 / (EXTRACT(epoch FROM NOW() - published_at) / 86400 + 1)) as score
FROM articles,
  websearch_to_tsquery('english', 'technology trends') query
WHERE search_vector @@ query
  AND published_at > NOW() - INTERVAL '1 year'
ORDER BY score DESC
LIMIT 20;
```

### Multilingual Search

```sql
-- Store language with content
CREATE TABLE documents (
  id SERIAL PRIMARY KEY,
  content TEXT NOT NULL,
  language TEXT NOT NULL DEFAULT 'english',
  search_vector TSVECTOR
);

-- Trigger for multi-language
CREATE OR REPLACE FUNCTION update_document_search()
RETURNS TRIGGER AS $$
BEGIN
  NEW.search_vector := to_tsvector(NEW.language::regconfig, NEW.content);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Query with language
SELECT * FROM documents
WHERE search_vector @@ to_tsquery(language::regconfig, 'search term');
```
