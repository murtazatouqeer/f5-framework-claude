# Rails Migration Template

## Create Table Migration Template

```ruby
# db/migrate/YYYYMMDDHHMMSS_create_{{resource_plural}}.rb
class Create{{ResourcePlural}} < ActiveRecord::Migration[7.1]
  def change
    create_table :{{resource_plural}}, id: :uuid do |t|
      # === Foreign Keys ===
      t.references :{{parent}}, null: false, foreign_key: true, type: :uuid
      t.references :created_by, foreign_key: { to_table: :users }, type: :uuid

      # === Required Fields ===
      t.string :name, null: false
      t.string :slug, null: false

      # === Optional Fields ===
      t.text :description
      t.decimal :price, precision: 10, scale: 2
      t.integer :quantity, default: 0
      t.boolean :active, default: true, null: false

      # === Enum Fields ===
      t.string :status, default: '{{DEFAULT_STATUS}}', null: false

      # === JSON Fields ===
      t.jsonb :metadata, default: {}
      t.jsonb :settings, default: {}

      # === Soft Delete ===
      t.datetime :deleted_at

      # === Timestamps ===
      t.timestamps
    end

    # === Indexes ===
    add_index :{{resource_plural}}, :slug, unique: true
    add_index :{{resource_plural}}, :status
    add_index :{{resource_plural}}, :deleted_at
    add_index :{{resource_plural}}, [:{{parent}}_id, :name], unique: true
    add_index :{{resource_plural}}, :metadata, using: :gin
  end
end
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{resource_plural}}` | Table name (plural snake_case) | `products` |
| `{{ResourcePlural}}` | Class name (PascalCase) | `Products` |
| `{{parent}}` | Parent reference | `category` |
| `{{DEFAULT_STATUS}}` | Default enum value | `draft` |

## Usage Example

For a `Product` migration:

```ruby
# db/migrate/20240115120000_create_products.rb
class CreateProducts < ActiveRecord::Migration[7.1]
  def change
    create_table :products, id: :uuid do |t|
      # === Foreign Keys ===
      t.references :category, null: false, foreign_key: true, type: :uuid
      t.references :created_by, foreign_key: { to_table: :users }, type: :uuid

      # === Required Fields ===
      t.string :name, null: false, limit: 255
      t.string :slug, null: false, limit: 255
      t.string :sku, null: false, limit: 50

      # === Optional Fields ===
      t.text :description
      t.text :short_description
      t.decimal :price, precision: 10, scale: 2, null: false
      t.decimal :compare_price, precision: 10, scale: 2
      t.decimal :cost_price, precision: 10, scale: 2
      t.integer :stock_quantity, default: 0, null: false
      t.integer :low_stock_threshold, default: 10

      # === Boolean Flags ===
      t.boolean :featured, default: false, null: false
      t.boolean :taxable, default: true, null: false
      t.boolean :track_inventory, default: true, null: false

      # === Enum Fields ===
      t.string :status, default: 'draft', null: false

      # === JSON Fields ===
      t.jsonb :metadata, default: {}
      t.jsonb :dimensions, default: {}  # { width, height, length, weight }
      t.jsonb :seo, default: {}  # { title, description, keywords }

      # === Counters (Cache) ===
      t.integer :reviews_count, default: 0, null: false
      t.integer :views_count, default: 0, null: false
      t.decimal :average_rating, precision: 3, scale: 2

      # === Dates ===
      t.datetime :published_at
      t.datetime :archived_at

      # === Soft Delete ===
      t.datetime :deleted_at

      # === Timestamps ===
      t.timestamps
    end

    # === Indexes ===
    add_index :products, :slug, unique: true
    add_index :products, :sku, unique: true
    add_index :products, :status
    add_index :products, :featured
    add_index :products, :deleted_at
    add_index :products, :published_at
    add_index :products, [:category_id, :status]
    add_index :products, [:status, :featured]
    add_index :products, :metadata, using: :gin
    add_index :products, :price
    add_index :products, "((metadata->>'brand'))", name: 'index_products_on_brand'
  end
end
```

## Add Columns Migration

```ruby
# db/migrate/YYYYMMDDHHMMSS_add_fields_to_{{resource_plural}}.rb
class AddFieldsTo{{ResourcePlural}} < ActiveRecord::Migration[7.1]
  def change
    # Add single column
    add_column :{{resource_plural}}, :{{column}}, :{{type}}, {{OPTIONS}}

    # Add reference
    add_reference :{{resource_plural}}, :{{reference}}, foreign_key: true, type: :uuid

    # Add index
    add_index :{{resource_plural}}, :{{column}}
  end
end

# Example
class AddPublishedAtToProducts < ActiveRecord::Migration[7.1]
  def change
    add_column :products, :published_at, :datetime
    add_column :products, :publisher_id, :uuid
    add_foreign_key :products, :users, column: :publisher_id

    add_index :products, :published_at
    add_index :products, :publisher_id
  end
end
```

## Change Column Migration

```ruby
# db/migrate/YYYYMMDDHHMMSS_change_{{column}}_in_{{resource_plural}}.rb
class Change{{Column}}In{{ResourcePlural}} < ActiveRecord::Migration[7.1]
  def up
    change_column :{{resource_plural}}, :{{column}}, :{{new_type}}, {{OPTIONS}}
  end

  def down
    change_column :{{resource_plural}}, :{{column}}, :{{old_type}}, {{OLD_OPTIONS}}
  end
end

# Example with null change
class ChangeDescriptionInProducts < ActiveRecord::Migration[7.1]
  def up
    change_column_null :products, :description, false
    change_column_default :products, :status, from: nil, to: 'draft'
  end

  def down
    change_column_null :products, :description, true
    change_column_default :products, :status, from: 'draft', to: nil
  end
end
```

## Join Table Migration

```ruby
# db/migrate/YYYYMMDDHHMMSS_create_{{join_table}}.rb
class Create{{JoinTable}} < ActiveRecord::Migration[7.1]
  def change
    create_table :{{join_table}}, id: :uuid do |t|
      t.references :{{resource1}}, null: false, foreign_key: true, type: :uuid
      t.references :{{resource2}}, null: false, foreign_key: true, type: :uuid

      t.timestamps
    end

    add_index :{{join_table}}, [:{{resource1}}_id, :{{resource2}}_id], unique: true
  end
end

# Example: products_tags
class CreateProductTags < ActiveRecord::Migration[7.1]
  def change
    create_table :product_tags, id: :uuid do |t|
      t.references :product, null: false, foreign_key: true, type: :uuid
      t.references :tag, null: false, foreign_key: true, type: :uuid
      t.integer :position

      t.timestamps
    end

    add_index :product_tags, [:product_id, :tag_id], unique: true
    add_index :product_tags, [:product_id, :position]
  end
end
```

## Data Migration

```ruby
# db/migrate/YYYYMMDDHHMMSS_migrate_{{description}}.rb
class Migrate{{Description}} < ActiveRecord::Migration[7.1]
  disable_ddl_transaction!

  def up
    {{Resource}}.find_each(batch_size: 1000) do |record|
      record.update_columns(
        new_field: transform_value(record.old_field)
      )
    end
  end

  def down
    {{Resource}}.find_each(batch_size: 1000) do |record|
      record.update_columns(
        old_field: reverse_transform(record.new_field)
      )
    end
  end

  private

  def transform_value(value)
    # Transform logic
  end

  def reverse_transform(value)
    # Reverse transform logic
  end
end

# Example: Migrate status from integer to string
class MigrateProductStatusToString < ActiveRecord::Migration[7.1]
  disable_ddl_transaction!

  STATUS_MAP = {
    0 => 'draft',
    1 => 'active',
    2 => 'archived'
  }.freeze

  def up
    add_column :products, :status_string, :string

    Product.find_each(batch_size: 1000) do |product|
      product.update_columns(status_string: STATUS_MAP[product.status_integer])
    end

    safety_assured do
      remove_column :products, :status_integer
      rename_column :products, :status_string, :status
      change_column_default :products, :status, 'draft'
      change_column_null :products, :status, false
    end

    add_index :products, :status
  end

  def down
    # Reverse migration
  end
end
```

## Index-Only Migration

```ruby
# db/migrate/YYYYMMDDHHMMSS_add_indexes_to_{{resource_plural}}.rb
class AddIndexesTo{{ResourcePlural}} < ActiveRecord::Migration[7.1]
  disable_ddl_transaction!

  def change
    add_index :{{resource_plural}}, :{{column}}, algorithm: :concurrently
    add_index :{{resource_plural}}, [:{{column1}}, :{{column2}}], algorithm: :concurrently
    add_index :{{resource_plural}}, :{{column}}, where: '{{condition}}', algorithm: :concurrently
  end
end

# Example
class AddIndexesToProducts < ActiveRecord::Migration[7.1]
  disable_ddl_transaction!

  def change
    # Simple index
    add_index :products, :created_at, algorithm: :concurrently

    # Composite index
    add_index :products, [:category_id, :created_at], algorithm: :concurrently

    # Partial index
    add_index :products, :published_at,
              where: "status = 'active'",
              algorithm: :concurrently,
              name: 'index_active_products_on_published_at'

    # Expression index
    add_index :products, 'lower(name)',
              algorithm: :concurrently,
              name: 'index_products_on_lower_name'
  end
end
```

## PostgreSQL-Specific Features

```ruby
class AddAdvancedFeaturesToProducts < ActiveRecord::Migration[7.1]
  def change
    # Enable extensions
    enable_extension 'uuid-ossp'
    enable_extension 'pg_trgm'  # For fuzzy search

    # Array column
    add_column :products, :tag_names, :string, array: true, default: []

    # Full-text search
    add_column :products, :search_vector, :tsvector
    add_index :products, :search_vector, using: :gin

    # GIN index for array
    add_index :products, :tag_names, using: :gin

    # Trigram index for fuzzy search
    add_index :products, :name, using: :gin, opclass: :gin_trgm_ops
  end
end
```
