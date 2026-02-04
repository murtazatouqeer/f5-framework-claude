---
name: laravel-migration
description: Template for Laravel Database Migrations
applies_to: laravel
type: template
---

# Laravel Migration Template

## Create Table Migration

```php
<?php
// database/migrations/{{timestamp}}_create_{{table_name}}_table.php
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
        Schema::create('{{table_name}}', function (Blueprint $table) {
            // Primary key (UUID)
            $table->uuid('id')->primary();

            // Foreign keys
            $table->foreignUuid('user_id')
                ->constrained()
                ->cascadeOnDelete();

            $table->foreignUuid('category_id')
                ->nullable()
                ->constrained()
                ->nullOnDelete();

            // Basic fields
            $table->string('name');
            $table->string('slug')->unique();
            $table->text('description')->nullable();
            $table->longText('content')->nullable();

            // Numeric fields
            $table->decimal('price', 10, 2)->default(0);
            $table->decimal('compare_price', 10, 2)->nullable();
            $table->integer('stock')->default(0);
            $table->integer('sort_order')->default(0);

            // Status/Type fields
            $table->string('status')->default('draft');
            $table->string('type')->nullable();

            // Boolean fields
            $table->boolean('is_active')->default(true);
            $table->boolean('is_featured')->default(false);

            // JSON fields
            $table->json('metadata')->nullable();
            $table->json('settings')->nullable();

            // Date fields
            $table->timestamp('published_at')->nullable();
            $table->timestamp('expires_at')->nullable();

            // Timestamps and soft deletes
            $table->timestamps();
            $table->softDeletes();

            // Indexes
            $table->index('status');
            $table->index('is_active');
            $table->index('published_at');
            $table->index(['status', 'is_active']);
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('{{table_name}}');
    }
};
```

## Pivot Table Migration

```php
<?php
// database/migrations/{{timestamp}}_create_{{entity_name}}_tag_table.php
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
        Schema::create('{{entity_name}}_tag', function (Blueprint $table) {
            $table->foreignUuid('{{entity_name}}_id')
                ->constrained()
                ->cascadeOnDelete();

            $table->foreignUuid('tag_id')
                ->constrained()
                ->cascadeOnDelete();

            $table->integer('order')->default(0);
            $table->timestamps();

            $table->primary(['{{entity_name}}_id', 'tag_id']);
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('{{entity_name}}_tag');
    }
};
```

## Add Column Migration

```php
<?php
// database/migrations/{{timestamp}}_add_column_to_{{table_name}}_table.php
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
        Schema::table('{{table_name}}', function (Blueprint $table) {
            $table->string('new_column')->nullable()->after('existing_column');
            $table->index('new_column');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('{{table_name}}', function (Blueprint $table) {
            $table->dropIndex(['new_column']);
            $table->dropColumn('new_column');
        });
    }
};
```

## Modify Column Migration

```php
<?php
// database/migrations/{{timestamp}}_modify_column_in_{{table_name}}_table.php
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
        Schema::table('{{table_name}}', function (Blueprint $table) {
            $table->string('name', 500)->change();
            $table->text('description')->nullable()->change();
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('{{table_name}}', function (Blueprint $table) {
            $table->string('name', 255)->change();
            $table->text('description')->nullable(false)->change();
        });
    }
};
```

## Full-Text Index Migration

```php
<?php
return new class extends Migration
{
    public function up(): void
    {
        Schema::table('{{table_name}}', function (Blueprint $table) {
            $table->fullText(['name', 'description', 'content']);
        });
    }

    public function down(): void
    {
        Schema::table('{{table_name}}', function (Blueprint $table) {
            $table->dropFullText(['name', 'description', 'content']);
        });
    }
};
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{timestamp}}` | Migration timestamp | `2024_01_15_120000` |
| `{{table_name}}` | snake_case plural table name | `products` |
| `{{entity_name}}` | snake_case entity name | `product` |
| `{{EntityName}}` | PascalCase entity name | `Product` |
