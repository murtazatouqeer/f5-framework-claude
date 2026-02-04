# Rails Model Generator Agent

Agent for generating ActiveRecord models with best practices.

## Capabilities

- Generate ActiveRecord models
- Define associations
- Add validations
- Create scopes
- Apply concerns
- Generate migrations

## Input Schema

```yaml
model_name: string       # Model name (e.g., "Product")
table_name: string       # Optional custom table name
attributes: array        # Model attributes with types
associations: array      # belongs_to, has_many, etc.
validations: array       # Validation rules
scopes: array           # Query scopes
concerns: array         # Concerns to include
enums: array            # Enum definitions
callbacks: array        # Lifecycle callbacks
indexes: array          # Database indexes
```

## Attribute Types

```yaml
types:
  - string
  - text
  - integer
  - bigint
  - float
  - decimal
  - boolean
  - date
  - datetime
  - timestamp
  - uuid
  - json
  - jsonb
  - references
```

## Example Usage

```yaml
model_name: Product
attributes:
  - name: name
    type: string
    null: false
  - name: description
    type: text
  - name: price
    type: decimal
    precision: 10
    scale: 2
  - name: status
    type: string
    default: 'draft'
  - name: is_featured
    type: boolean
    default: false
associations:
  - type: belongs_to
    model: Category
  - type: belongs_to
    model: User
    foreign_key: created_by_id
  - type: has_many
    model: OrderItem
    dependent: restrict_with_error
  - type: has_and_belongs_to_many
    model: Tag
validations:
  - attribute: name
    rules: [presence, { length: { maximum: 255 } }]
  - attribute: price
    rules: [presence, { numericality: { greater_than_or_equal_to: 0 } }]
enums:
  - name: status
    values: [draft, active, inactive, archived]
    prefix: true
scopes:
  - name: active
    query: "where(status: :active)"
  - name: featured
    query: "where(is_featured: true)"
concerns:
  - SoftDeletable
  - Searchable
```

## Generated Code Template

```ruby
# app/models/{{model_name_lower}}.rb
class {{ModelName}} < ApplicationRecord
  # Concerns
  include SoftDeletable
  include Searchable

  # Associations
  belongs_to :category
  belongs_to :user, foreign_key: :created_by_id
  has_many :order_items, dependent: :restrict_with_error
  has_many :orders, through: :order_items
  has_and_belongs_to_many :tags

  # Enums
  enum status: {
    draft: 'draft',
    active: 'active',
    inactive: 'inactive',
    archived: 'archived'
  }, _prefix: true

  # Validations
  validates :name, presence: true, length: { maximum: 255 }
  validates :slug, presence: true, uniqueness: true
  validates :price, presence: true, numericality: { greater_than_or_equal_to: 0 }

  # Callbacks
  before_validation :generate_slug, on: :create
  after_create :notify_admin
  after_update :clear_cache

  # Scopes
  scope :active, -> { where(status: :active) }
  scope :featured, -> { where(is_featured: true) }
  scope :by_category, ->(category_id) { where(category_id: category_id) if category_id }
  scope :search, ->(term) {
    where("name ILIKE :term OR description ILIKE :term", term: "%#{term}%") if term.present?
  }

  # Class Methods
  def self.ransackable_attributes(auth_object = nil)
    %w[name status category_id price created_at]
  end

  # Instance Methods
  def on_sale?
    compare_price.present? && compare_price > price
  end

  def publish!
    raise StandardError, "Only draft products can be published" unless status_draft?
    update!(status: :active, published_at: Time.current)
  end

  private

  def generate_slug
    self.slug = name.parameterize if name.present? && slug.blank?
  end

  def notify_admin
    AdminMailer.new_product(self).deliver_later
  end

  def clear_cache
    Rails.cache.delete("product_#{id}")
  end
end
```

## Migration Template

```ruby
# db/migrate/YYYYMMDDHHMMSS_create_{{table_name}}.rb
class Create{{TableName}} < ActiveRecord::Migration[7.1]
  def change
    create_table :{{table_name}}, id: :uuid do |t|
      t.string :name, null: false
      t.text :description
      t.decimal :price, precision: 10, scale: 2, null: false
      t.decimal :compare_price, precision: 10, scale: 2
      t.string :status, null: false, default: 'draft'
      t.boolean :is_featured, null: false, default: false
      t.string :slug, null: false
      t.datetime :published_at

      t.references :category, null: false, foreign_key: true, type: :uuid
      t.references :created_by, null: false, foreign_key: { to_table: :users }, type: :uuid

      t.timestamps
      t.datetime :deleted_at

      t.index :slug, unique: true
      t.index :status
      t.index :deleted_at
      t.index [:status, :is_featured]
    end
  end
end
```

## Related Files Generated

1. `app/models/{{model_name_lower}}.rb` - Model file
2. `db/migrate/YYYYMMDDHHMMSS_create_{{table_name}}.rb` - Migration
3. `spec/models/{{model_name_lower}}_spec.rb` - Model specs
4. `spec/factories/{{table_name}}.rb` - Factory

## Conventions

- Use UUIDs for primary keys
- Include `deleted_at` for soft deletes
- Add indexes for foreign keys and commonly queried columns
- Use enums with string values for portability
- Prefix enum scopes to avoid method name conflicts

## Best Practices Applied

- Single responsibility - models focus on data and associations
- Use concerns for shared behavior
- Validate at the model level
- Use scopes for reusable queries
- Implement soft deletes for important data
