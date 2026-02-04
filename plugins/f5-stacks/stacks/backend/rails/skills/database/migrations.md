# Rails Migrations

Database schema management with ActiveRecord migrations.

## Creating Migrations

```bash
# Generate migration
rails generate migration CreateProducts
rails generate migration AddStatusToProducts status:string
rails generate migration AddUserRefToProducts user:references
rails generate migration RemoveDescriptionFromProducts description:text
rails generate migration CreateJoinTableProductsCategories products categories
```

## Migration Structure

```ruby
# db/migrate/YYYYMMDDHHMMSS_create_products.rb
class CreateProducts < ActiveRecord::Migration[7.1]
  def change
    create_table :products, id: :uuid do |t|
      # String columns
      t.string :name, null: false
      t.string :slug, null: false
      t.string :sku, limit: 50
      t.string :status, null: false, default: 'draft'

      # Text columns
      t.text :description
      t.text :short_description

      # Numeric columns
      t.decimal :price, precision: 10, scale: 2, null: false
      t.decimal :compare_price, precision: 10, scale: 2
      t.integer :quantity, null: false, default: 0
      t.bigint :views_count, null: false, default: 0

      # Boolean columns
      t.boolean :is_featured, null: false, default: false
      t.boolean :is_active, null: false, default: true

      # Date/Time columns
      t.datetime :published_at
      t.date :available_from

      # JSON columns (PostgreSQL)
      t.jsonb :metadata, null: false, default: {}
      t.jsonb :settings

      # References (foreign keys)
      t.references :category, null: false, foreign_key: true, type: :uuid
      t.references :created_by, null: false, foreign_key: { to_table: :users }, type: :uuid

      # Timestamps
      t.timestamps

      # Soft delete
      t.datetime :deleted_at
    end

    # Indexes
    add_index :products, :slug, unique: true
    add_index :products, :sku, unique: true, where: 'deleted_at IS NULL'
    add_index :products, :status
    add_index :products, :deleted_at
    add_index :products, [:status, :is_featured]
    add_index :products, :metadata, using: :gin
  end
end
```

## Common Operations

### Adding Columns

```ruby
class AddFieldsToProducts < ActiveRecord::Migration[7.1]
  def change
    # Single column
    add_column :products, :weight, :decimal, precision: 8, scale: 2

    # Multiple columns
    change_table :products do |t|
      t.string :color
      t.string :size
      t.integer :rating, default: 0
    end

    # With index
    add_column :products, :barcode, :string
    add_index :products, :barcode, unique: true
  end
end
```

### Removing Columns

```ruby
class RemoveFieldsFromProducts < ActiveRecord::Migration[7.1]
  def change
    # Reversible removal
    remove_column :products, :old_field, :string

    # Multiple columns
    remove_columns :products, :field1, :field2, :field3, type: :string
  end
end
```

### Changing Columns

```ruby
class ChangeProductColumns < ActiveRecord::Migration[7.1]
  def up
    # Change type
    change_column :products, :price, :decimal, precision: 12, scale: 2

    # Change null constraint
    change_column_null :products, :description, false

    # Change default
    change_column_default :products, :status, from: 'draft', to: 'pending'

    # Rename
    rename_column :products, :old_name, :new_name
  end

  def down
    change_column :products, :price, :decimal, precision: 10, scale: 2
    change_column_null :products, :description, true
    change_column_default :products, :status, from: 'pending', to: 'draft'
    rename_column :products, :new_name, :old_name
  end
end
```

### References and Foreign Keys

```ruby
class AddReferencesToProducts < ActiveRecord::Migration[7.1]
  def change
    # Add reference with foreign key
    add_reference :products, :brand, null: true, foreign_key: true, type: :uuid

    # Add reference with custom foreign key name
    add_reference :products, :updated_by, null: true,
                  foreign_key: { to_table: :users }, type: :uuid

    # Add foreign key to existing column
    add_foreign_key :products, :categories

    # Remove foreign key
    remove_foreign_key :products, :categories
  end
end
```

### Indexes

```ruby
class AddIndexesToProducts < ActiveRecord::Migration[7.1]
  def change
    # Single column index
    add_index :products, :name

    # Composite index
    add_index :products, [:category_id, :status]

    # Unique index
    add_index :products, :email, unique: true

    # Partial index (PostgreSQL)
    add_index :products, :email,
              unique: true,
              where: 'deleted_at IS NULL',
              name: 'index_products_on_email_active'

    # Expression index (PostgreSQL)
    add_index :products, 'LOWER(name)', name: 'index_products_on_lower_name'

    # GIN index for JSONB (PostgreSQL)
    add_index :products, :metadata, using: :gin

    # Remove index
    remove_index :products, :name
    remove_index :products, name: 'index_products_on_lower_name'
  end
end
```

## Data Migrations

```ruby
class PopulateProductSlugs < ActiveRecord::Migration[7.1]
  def up
    # Safe data migration
    Product.find_each do |product|
      product.update_column(:slug, product.name.parameterize)
    end
  end

  def down
    # Optional: revert logic
  end
end

# Better: Use reversible with SQL
class PopulateProductSlugs < ActiveRecord::Migration[7.1]
  def up
    execute <<-SQL
      UPDATE products
      SET slug = LOWER(REGEXP_REPLACE(name, '[^a-zA-Z0-9]+', '-', 'g'))
      WHERE slug IS NULL
    SQL
  end

  def down
    # Data migration usually not reversible
  end
end
```

## Safe Migrations

```ruby
# Use safety_assured for dangerous operations (with strong_migrations gem)
class AddIndexSafely < ActiveRecord::Migration[7.1]
  disable_ddl_transaction!

  def change
    add_index :products, :category_id, algorithm: :concurrently
  end
end

# Avoid exclusive locks on large tables
class AddColumnSafely < ActiveRecord::Migration[7.1]
  def change
    # This is safe - doesn't lock table
    add_column :products, :new_field, :string

    # This locks table - avoid on large tables
    # change_column :products, :description, :text, null: false
  end
end
```

## PostgreSQL-Specific Features

```ruby
class CreateAdvancedTable < ActiveRecord::Migration[7.1]
  def change
    # Enable extensions
    enable_extension 'uuid-ossp'
    enable_extension 'pgcrypto'

    create_table :documents, id: :uuid do |t|
      # UUID with auto-generation
      t.uuid :public_id, null: false, default: -> { 'gen_random_uuid()' }

      # Array columns
      t.string :tags, array: true, default: []

      # JSONB with default
      t.jsonb :metadata, null: false, default: {}

      # Date range
      t.daterange :valid_period

      # Full text search
      t.tsvector :searchable

      t.timestamps
    end

    # GIN indexes for arrays and JSONB
    add_index :documents, :tags, using: :gin
    add_index :documents, :metadata, using: :gin
    add_index :documents, :searchable, using: :gin

    # Trigger for search vector
    execute <<-SQL
      CREATE TRIGGER documents_searchable_update
      BEFORE INSERT OR UPDATE ON documents
      FOR EACH ROW EXECUTE FUNCTION
      tsvector_update_trigger(searchable, 'pg_catalog.english', title, content);
    SQL
  end
end
```

## Running Migrations

```bash
# Run all pending migrations
rails db:migrate

# Run migrations in specific environment
RAILS_ENV=production rails db:migrate

# Rollback last migration
rails db:rollback

# Rollback multiple steps
rails db:rollback STEP=3

# Migrate to specific version
rails db:migrate VERSION=20240101000000

# Check migration status
rails db:migrate:status

# Redo last migration (rollback + migrate)
rails db:migrate:redo

# Reset database (drop + create + migrate)
rails db:reset

# Setup database (create + schema:load + seed)
rails db:setup
```

## Best Practices

1. **Never edit existing migrations** after they've been committed
2. **Use reversible migrations** when possible
3. **Add indexes** for foreign keys and frequently queried columns
4. **Use `null: false`** with defaults for new columns
5. **Test migrations** both up and down
6. **Use transactions** for data migrations (or disable for large tables)
7. **Separate schema and data migrations**
8. **Use `change_column_null` + `change_column_default`** separately
