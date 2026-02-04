# Flyway Database Migrations

Database migration strategies and patterns with Flyway for Spring Boot.

## Setup

### Dependencies (Gradle)

```groovy
dependencies {
    implementation 'org.flywaydb:flyway-core'
    implementation 'org.flywaydb:flyway-database-postgresql'  // For PostgreSQL
}
```

### Configuration

```yaml
# application.yml
spring:
  flyway:
    enabled: true
    locations: classpath:db/migration
    baseline-on-migrate: true
    baseline-version: 0
    validate-on-migrate: true
    out-of-order: false
    clean-disabled: true  # Prevent accidental clean in production

  datasource:
    url: jdbc:postgresql://localhost:5432/myapp
    username: ${DB_USERNAME}
    password: ${DB_PASSWORD}
```

### Environment-Specific Config

```yaml
# application-dev.yml
spring:
  flyway:
    clean-disabled: false
    locations: classpath:db/migration,classpath:db/testdata

# application-prod.yml
spring:
  flyway:
    clean-disabled: true
    validate-on-migrate: true
```

## Migration File Naming

```
db/migration/
├── V1__create_users_table.sql
├── V2__create_products_table.sql
├── V3__add_category_to_products.sql
├── V4__create_orders_table.sql
├── V5__add_index_to_products.sql
├── R__refresh_materialized_views.sql  # Repeatable
└── U1__undo_create_users.sql          # Undo (Flyway Teams)
```

### Naming Convention

```
V<version>__<description>.sql     # Versioned migrations
R__<description>.sql              # Repeatable migrations
U<version>__<description>.sql     # Undo migrations (Teams)

Examples:
V1__create_users_table.sql
V1.1__add_email_to_users.sql
V2__create_products.sql
V2.0.1__fix_product_constraint.sql
R__create_views.sql
```

## Migration Examples

### Create Table

```sql
-- V1__create_users_table.sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by VARCHAR(255),
    updated_by VARCHAR(255),
    version BIGINT NOT NULL DEFAULT 0
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_created_at ON users(created_at);

COMMENT ON TABLE users IS 'User accounts table';
COMMENT ON COLUMN users.email IS 'User email address, used for login';
```

### Create Table with Foreign Key

```sql
-- V2__create_products_table.sql
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    parent_id UUID REFERENCES categories(id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    sku VARCHAR(50) NOT NULL UNIQUE,
    price DECIMAL(19, 4) NOT NULL,
    stock INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'DRAFT',
    category_id UUID REFERENCES categories(id),
    image_url VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    version BIGINT NOT NULL DEFAULT 0,

    CONSTRAINT chk_price_positive CHECK (price >= 0),
    CONSTRAINT chk_stock_positive CHECK (stock >= 0),
    CONSTRAINT chk_status CHECK (status IN ('DRAFT', 'ACTIVE', 'INACTIVE', 'DISCONTINUED'))
);

CREATE INDEX idx_products_sku ON products(sku);
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_products_status ON products(status) WHERE deleted = FALSE;
CREATE INDEX idx_products_name ON products(name);
```

### Add Column

```sql
-- V3__add_brand_to_products.sql
ALTER TABLE products ADD COLUMN brand_id UUID;

CREATE TABLE brands (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    logo_url VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

ALTER TABLE products
    ADD CONSTRAINT fk_products_brand
    FOREIGN KEY (brand_id) REFERENCES brands(id);

CREATE INDEX idx_products_brand ON products(brand_id);
```

### Modify Column

```sql
-- V4__modify_product_price_precision.sql
ALTER TABLE products
    ALTER COLUMN price TYPE DECIMAL(19, 2);
```

### Add Index

```sql
-- V5__add_product_search_index.sql
-- Full text search index for PostgreSQL
CREATE INDEX idx_products_fulltext ON products
    USING GIN (to_tsvector('english', name || ' ' || COALESCE(description, '')));
```

### Create Many-to-Many

```sql
-- V6__create_product_tags.sql
CREATE TABLE tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE TABLE product_tags (
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    tag_id UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (product_id, tag_id)
);

CREATE INDEX idx_product_tags_tag ON product_tags(tag_id);
```

### Data Migration

```sql
-- V7__migrate_legacy_categories.sql
-- Migrate data from old structure to new

-- Insert default category for products without one
INSERT INTO categories (id, name, description)
VALUES ('00000000-0000-0000-0000-000000000001', 'Uncategorized', 'Default category');

-- Update products without category
UPDATE products
SET category_id = '00000000-0000-0000-0000-000000000001'
WHERE category_id IS NULL;

-- Make category required
ALTER TABLE products
    ALTER COLUMN category_id SET NOT NULL;
```

### Create View

```sql
-- V8__create_product_summary_view.sql
CREATE OR REPLACE VIEW product_summary AS
SELECT
    p.id,
    p.name,
    p.sku,
    p.price,
    p.stock,
    p.status,
    c.name AS category_name,
    b.name AS brand_name,
    p.created_at,
    p.updated_at
FROM products p
LEFT JOIN categories c ON p.category_id = c.id
LEFT JOIN brands b ON p.brand_id = b.id
WHERE p.deleted = FALSE;
```

### Repeatable Migration

```sql
-- R__refresh_materialized_views.sql
-- Runs on every change

DROP MATERIALIZED VIEW IF EXISTS product_stats;

CREATE MATERIALIZED VIEW product_stats AS
SELECT
    c.id AS category_id,
    c.name AS category_name,
    COUNT(p.id) AS product_count,
    AVG(p.price) AS avg_price,
    SUM(p.stock) AS total_stock
FROM categories c
LEFT JOIN products p ON c.id = p.category_id AND p.deleted = FALSE
GROUP BY c.id, c.name;

CREATE UNIQUE INDEX ON product_stats(category_id);
```

## Java-Based Migrations

```java
package db.migration;

import org.flywaydb.core.api.migration.BaseJavaMigration;
import org.flywaydb.core.api.migration.Context;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.SingleConnectionDataSource;

public class V9__complex_data_migration extends BaseJavaMigration {

    @Override
    public void migrate(Context context) throws Exception {
        JdbcTemplate jdbcTemplate = new JdbcTemplate(
            new SingleConnectionDataSource(context.getConnection(), true));

        // Complex migration logic
        jdbcTemplate.query(
            "SELECT id, legacy_data FROM products WHERE legacy_data IS NOT NULL",
            (rs, rowNum) -> {
                UUID id = UUID.fromString(rs.getString("id"));
                String legacyData = rs.getString("legacy_data");

                // Transform legacy data
                Map<String, Object> transformed = transformLegacyData(legacyData);

                // Update with new format
                jdbcTemplate.update(
                    "UPDATE products SET metadata = ?::jsonb WHERE id = ?",
                    toJson(transformed), id
                );

                return null;
            }
        );
    }

    private Map<String, Object> transformLegacyData(String legacyData) {
        // Complex transformation logic
        return new HashMap<>();
    }

    private String toJson(Map<String, Object> data) {
        // Convert to JSON string
        return "{}";
    }
}
```

## Callbacks

```java
@Component
public class FlywayCallback implements Callback {

    private static final Logger log = LoggerFactory.getLogger(FlywayCallback.class);

    @Override
    public boolean supports(Event event, Context context) {
        return event == Event.AFTER_MIGRATE || event == Event.AFTER_MIGRATE_ERROR;
    }

    @Override
    public boolean canHandleInTransaction(Event event, Context context) {
        return true;
    }

    @Override
    public void handle(Event event, Context context) {
        if (event == Event.AFTER_MIGRATE) {
            log.info("Migration completed successfully. Applied {} migrations",
                context.getMigrationInfo().applied().length);
        } else if (event == Event.AFTER_MIGRATE_ERROR) {
            log.error("Migration failed!");
        }
    }

    @Override
    public String getCallbackName() {
        return "Migration Logger";
    }
}
```

## Testing Migrations

```java
@SpringBootTest
@Testcontainers
class FlywayMigrationTest {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:15-alpine");

    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
    }

    @Autowired
    private Flyway flyway;

    @Autowired
    private JdbcTemplate jdbcTemplate;

    @Test
    void migrationsRunSuccessfully() {
        MigrationInfoService info = flyway.info();

        assertThat(info.applied()).isNotEmpty();
        assertThat(info.pending()).isEmpty();

        for (MigrationInfo migration : info.applied()) {
            assertThat(migration.getState()).isEqualTo(MigrationState.SUCCESS);
        }
    }

    @Test
    void tablesCreatedCorrectly() {
        List<String> tables = jdbcTemplate.queryForList(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'",
            String.class
        );

        assertThat(tables).contains("users", "products", "categories", "orders");
    }

    @Test
    void indexesCreatedCorrectly() {
        List<String> indexes = jdbcTemplate.queryForList(
            "SELECT indexname FROM pg_indexes WHERE schemaname = 'public'",
            String.class
        );

        assertThat(indexes).contains(
            "idx_products_sku",
            "idx_products_category",
            "idx_users_email"
        );
    }
}
```

## Production Best Practices

### Lock Timeout

```sql
-- V10__add_column_safely.sql
-- Set lock timeout to prevent blocking
SET lock_timeout = '5s';

ALTER TABLE products ADD COLUMN metadata JSONB;

-- Reset
RESET lock_timeout;
```

### Concurrent Index Creation

```sql
-- V11__create_index_concurrently.sql
-- Doesn't block reads/writes
CREATE INDEX CONCURRENTLY idx_products_metadata ON products USING GIN (metadata);
```

### Large Table Migration

```sql
-- V12__migrate_large_table.sql
-- Batch update to avoid locking

DO $$
DECLARE
    batch_size INT := 1000;
    rows_updated INT;
BEGIN
    LOOP
        UPDATE products
        SET new_column = compute_value(old_column)
        WHERE id IN (
            SELECT id FROM products
            WHERE new_column IS NULL
            LIMIT batch_size
        );

        GET DIAGNOSTICS rows_updated = ROW_COUNT;
        EXIT WHEN rows_updated = 0;

        COMMIT;
        PERFORM pg_sleep(0.1);  -- Brief pause
    END LOOP;
END $$;
```

## Rollback Strategy

```sql
-- For simple changes, create forward-only migrations
-- V13__add_feature_flag.sql
ALTER TABLE products ADD COLUMN feature_enabled BOOLEAN DEFAULT FALSE;

-- V14__remove_feature_flag.sql (if needed to rollback)
ALTER TABLE products DROP COLUMN feature_enabled;
```

## Best Practices

1. **Never modify applied migrations** - Create new ones
2. **Use descriptive names** - Describe what migration does
3. **Make migrations idempotent** when possible
4. **Test migrations** on copy of production data
5. **Use transactions** - Flyway wraps in transaction by default
6. **Create indexes CONCURRENTLY** in production
7. **Set lock timeouts** for ALTER TABLE
8. **Batch large data migrations**
9. **Version control migrations** with application code
10. **Review migrations** before deployment
