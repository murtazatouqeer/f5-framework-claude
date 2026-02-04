---
name: laravel-migrations
description: Database migrations best practices in Laravel
applies_to: laravel
category: database
---

# Laravel Migrations

## Creating Migrations

```bash
# Create migration
php artisan make:migration create_products_table

# Create with model
php artisan make:model Product -m

# Create for modification
php artisan make:migration add_status_to_products_table --table=products
```

## Migration Structure

```php
<?php
// database/migrations/2024_01_01_000001_create_products_table.php
use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::create('products', function (Blueprint $table) {
            // Primary key
            $table->uuid('id')->primary();

            // Basic columns
            $table->string('name');
            $table->string('slug')->unique();
            $table->text('description')->nullable();

            // Numeric columns
            $table->decimal('price', 10, 2);
            $table->decimal('compare_price', 10, 2)->nullable();
            $table->integer('stock')->default(0);
            $table->unsignedInteger('sort_order')->default(0);

            // Boolean columns
            $table->boolean('is_active')->default(false);
            $table->boolean('is_featured')->default(false);

            // Enum/Status columns
            $table->enum('status', ['draft', 'active', 'archived'])->default('draft');
            // Or use string for more flexibility
            // $table->string('status', 20)->default('draft');

            // JSON columns
            $table->json('metadata')->nullable();
            $table->json('attributes')->nullable();

            // Foreign keys
            $table->foreignUuid('category_id')
                ->constrained('categories')
                ->cascadeOnDelete();

            $table->foreignUuid('user_id')
                ->constrained('users')
                ->cascadeOnDelete();

            // Timestamps
            $table->timestamp('published_at')->nullable();
            $table->timestamps();
            $table->softDeletes();

            // Indexes
            $table->index('status');
            $table->index('is_featured');
            $table->index(['status', 'is_active']);
            $table->fullText(['name', 'description']); // MySQL/PostgreSQL
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('products');
    }
};
```

## Common Column Types

```php
<?php
// String types
$table->string('title', 100);      // VARCHAR(100)
$table->text('content');            // TEXT
$table->mediumText('body');         // MEDIUMTEXT
$table->longText('data');           // LONGTEXT
$table->char('code', 2);            // CHAR(2)

// Numeric types
$table->integer('count');           // INT
$table->unsignedInteger('views');   // UNSIGNED INT
$table->bigInteger('population');   // BIGINT
$table->tinyInteger('priority');    // TINYINT
$table->decimal('price', 10, 2);    // DECIMAL(10,2)
$table->float('rate');              // FLOAT
$table->double('amount');           // DOUBLE

// Boolean
$table->boolean('is_active');       // TINYINT(1)

// Date/Time
$table->date('birth_date');         // DATE
$table->time('start_time');         // TIME
$table->datetime('event_at');       // DATETIME
$table->timestamp('logged_at');     // TIMESTAMP
$table->year('graduation_year');    // YEAR

// Binary
$table->binary('data');             // BLOB

// UUID
$table->uuid('id');                 // UUID
$table->foreignUuid('user_id');     // UUID foreign key
$table->uuidMorphs('taggable');     // UUID polymorphic

// Special
$table->json('options');            // JSON
$table->ipAddress('visitor_ip');    // IP address
$table->macAddress('device');       // MAC address
$table->enum('status', ['a', 'b']); // ENUM
```

## Indexes

```php
<?php
// Primary key
$table->uuid('id')->primary();

// Unique
$table->string('email')->unique();
$table->unique(['email', 'tenant_id']);

// Index
$table->index('status');
$table->index(['category_id', 'status']);

// Full-text (MySQL/PostgreSQL)
$table->fullText(['title', 'description']);

// Spatial (MySQL)
$table->spatialIndex('location');

// Named indexes
$table->index('status', 'products_status_index');
```

## Foreign Keys

```php
<?php
// Shorthand (Laravel 9+)
$table->foreignUuid('category_id')
    ->constrained('categories')
    ->cascadeOnDelete()
    ->cascadeOnUpdate();

// Explicit definition
$table->uuid('user_id');
$table->foreign('user_id')
    ->references('id')
    ->on('users')
    ->onDelete('cascade')
    ->onUpdate('cascade');

// Nullable foreign key
$table->foreignUuid('parent_id')
    ->nullable()
    ->constrained('categories')
    ->nullOnDelete();

// Polymorphic columns
$table->uuidMorphs('commentable'); // commentable_type, commentable_id
$table->nullableUuidMorphs('taggable');
```

## Modifying Tables

```php
<?php
// Add columns
Schema::table('products', function (Blueprint $table) {
    $table->string('sku')->after('name');
    $table->boolean('is_new')->default(false)->after('is_featured');
});

// Rename column
Schema::table('products', function (Blueprint $table) {
    $table->renameColumn('description', 'short_description');
});

// Change column
Schema::table('products', function (Blueprint $table) {
    $table->string('name', 200)->change();
    $table->decimal('price', 12, 2)->change();
    $table->text('description')->nullable()->change();
});

// Drop columns
Schema::table('products', function (Blueprint $table) {
    $table->dropColumn(['temporary_field', 'legacy_id']);
});

// Drop indexes
Schema::table('products', function (Blueprint $table) {
    $table->dropIndex(['status']); // Drop by columns
    $table->dropIndex('products_status_index'); // Drop by name
    $table->dropUnique(['email']);
    $table->dropForeign(['category_id']);
});
```

## Pivot Table Migration

```php
<?php
// database/migrations/2024_01_02_000001_create_product_tag_table.php
return new class extends Migration
{
    public function up(): void
    {
        Schema::create('product_tag', function (Blueprint $table) {
            $table->foreignUuid('product_id')
                ->constrained()
                ->cascadeOnDelete();

            $table->foreignUuid('tag_id')
                ->constrained()
                ->cascadeOnDelete();

            $table->unsignedInteger('sort_order')->default(0);
            $table->boolean('is_primary')->default(false);
            $table->timestamps();

            $table->primary(['product_id', 'tag_id']);
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('product_tag');
    }
};
```

## Safe Migration Patterns

### Adding Column with Default

```php
<?php
// For large tables, avoid DEFAULT in production
public function up(): void
{
    Schema::table('products', function (Blueprint $table) {
        $table->boolean('is_verified')->nullable();
    });

    // Update existing rows in batches
    DB::table('products')
        ->whereNull('is_verified')
        ->chunkById(1000, function ($products) {
            foreach ($products as $product) {
                DB::table('products')
                    ->where('id', $product->id)
                    ->update(['is_verified' => false]);
            }
        });

    Schema::table('products', function (Blueprint $table) {
        $table->boolean('is_verified')->default(false)->nullable(false)->change();
    });
}
```

### Zero-Downtime Index Creation

```php
<?php
// MySQL: Add index concurrently (requires pt-online-schema-change)
// PostgreSQL: Use CONCURRENTLY
public function up(): void
{
    // For PostgreSQL
    DB::statement('CREATE INDEX CONCURRENTLY products_status_idx ON products(status)');
}

public function down(): void
{
    DB::statement('DROP INDEX CONCURRENTLY products_status_idx');
}
```

### Rename Table Safely

```php
<?php
public function up(): void
{
    // Step 1: Create new table
    Schema::create('items', function (Blueprint $table) {
        // ... same as products
    });

    // Step 2: Copy data
    DB::statement('INSERT INTO items SELECT * FROM products');

    // Step 3: Drop old table (after verifying)
    Schema::dropIfExists('products');
}
```

## Running Migrations

```bash
# Run pending migrations
php artisan migrate

# Rollback last batch
php artisan migrate:rollback

# Rollback specific steps
php artisan migrate:rollback --step=3

# Rollback all
php artisan migrate:reset

# Reset and re-run
php artisan migrate:refresh

# Drop all tables and re-run
php artisan migrate:fresh

# With seeding
php artisan migrate:fresh --seed

# Check status
php artisan migrate:status

# Generate SQL (for review)
php artisan schema:dump
```

## Best Practices

1. **One Migration per Change**: Don't combine unrelated changes
2. **Meaningful Names**: `add_status_to_products_table`
3. **Always Include Down**: Make migrations reversible
4. **Test Rollbacks**: Ensure down() works correctly
5. **Avoid Raw SQL**: Use Schema builder when possible
6. **Index Foreign Keys**: Add indexes for foreign keys
7. **Use Transactions**: For complex migrations
8. **Chunk Large Updates**: Avoid memory issues
