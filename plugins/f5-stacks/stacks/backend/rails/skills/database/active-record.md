# ActiveRecord Patterns

Best practices for working with ActiveRecord in Rails applications.

## Model Definition

```ruby
# app/models/product.rb
class Product < ApplicationRecord
  # 1. Concerns (first)
  include SoftDeletable
  include Searchable
  include Sluggable

  # 2. Constants
  STATUSES = %w[draft active inactive archived].freeze
  MAX_IMAGES = 10

  # 3. Associations
  belongs_to :category
  belongs_to :user, foreign_key: :created_by_id
  has_many :order_items, dependent: :restrict_with_error
  has_many :orders, through: :order_items
  has_many :images, as: :imageable, dependent: :destroy
  has_and_belongs_to_many :tags

  # 4. Delegations
  delegate :name, to: :category, prefix: true, allow_nil: true

  # 5. Enums
  enum status: {
    draft: 'draft',
    active: 'active',
    inactive: 'inactive',
    archived: 'archived'
  }, _prefix: true

  # 6. Validations
  validates :name, presence: true, length: { maximum: 255 }
  validates :slug, presence: true, uniqueness: true
  validates :price, presence: true, numericality: { greater_than_or_equal_to: 0 }
  validates :compare_price, numericality: { greater_than: :price }, allow_nil: true
  validates :status, inclusion: { in: STATUSES }
  validate :images_count_within_limit

  # 7. Callbacks
  before_validation :generate_slug, on: :create
  before_save :normalize_data
  after_create :notify_admin
  after_update :clear_cache
  before_destroy :check_orders

  # 8. Scopes
  scope :active, -> { where(status: :active) }
  scope :featured, -> { where(is_featured: true) }
  scope :by_category, ->(id) { where(category_id: id) if id.present? }
  scope :in_price_range, ->(min, max) {
    where(price: (min || 0)..(max || Float::INFINITY))
  }
  scope :recent, -> { order(created_at: :desc) }
  scope :with_associations, -> { includes(:category, :tags, :images) }

  # 9. Class Methods
  class << self
    def ransackable_attributes(auth_object = nil)
      %w[name status category_id price created_at]
    end

    def find_by_slug!(slug)
      find_by!(slug: slug)
    end
  end

  # 10. Instance Methods
  def on_sale?
    compare_price.present? && compare_price > price
  end

  def discount_percentage
    return 0 unless on_sale?
    ((1 - price / compare_price) * 100).round
  end

  def publish!
    raise StandardError, 'Only draft products can be published' unless status_draft?
    update!(status: :active, published_at: Time.current)
  end

  def archive!
    update!(status: :archived)
  end

  private

  def generate_slug
    self.slug = name.parameterize if name.present? && slug.blank?
  end

  def normalize_data
    self.name = name.strip if name.present?
  end

  def check_orders
    if order_items.exists?
      errors.add(:base, 'Cannot delete product with orders')
      throw :abort
    end
  end

  def notify_admin
    AdminMailer.new_product(self).deliver_later
  end

  def clear_cache
    Rails.cache.delete("product_#{id}")
    Rails.cache.delete('featured_products')
  end

  def images_count_within_limit
    return unless images.size > MAX_IMAGES
    errors.add(:images, "count must be less than #{MAX_IMAGES}")
  end
end
```

## Query Interface

### Basic Queries

```ruby
# Find by ID
user = User.find(1)
user = User.find_by(id: 1)  # Returns nil if not found
user = User.find_by!(id: 1) # Raises error if not found

# Where clauses
User.where(active: true)
User.where('created_at > ?', 1.week.ago)
User.where('name ILIKE ?', '%john%')
User.where(role: [:admin, :moderator])

# Ordering
Product.order(price: :asc)
Product.order(:name, created_at: :desc)
Product.order(Arel.sql('LOWER(name)'))

# Limiting
Product.limit(10)
Product.offset(20).limit(10)
Product.first(5)
Product.last(5)

# Selecting specific columns
User.select(:id, :name, :email)
User.select('id, name, CONCAT(first_name, last_name) as full_name')

# Distinct
Tag.distinct.pluck(:name)

# Grouping
Order.group(:status).count
Order.group(:user_id).sum(:total)
```

### Complex Queries

```ruby
# Subqueries
active_user_ids = User.active.select(:id)
Order.where(user_id: active_user_ids)

# Joins
Order.joins(:user).where(users: { active: true })
Product.joins(:category).where(categories: { name: 'Electronics' })

# Left outer joins
User.left_outer_joins(:orders)
    .select('users.*, COUNT(orders.id) as orders_count')
    .group('users.id')

# Eager loading (N+1 prevention)
User.includes(:orders, :profile)
User.eager_load(:orders)    # Uses LEFT OUTER JOIN
User.preload(:orders)       # Uses separate queries

# OR conditions
User.where(role: :admin).or(User.where(role: :moderator))

# NOT conditions
User.where.not(status: :banned)
User.where.not(deleted_at: nil)

# Exists
User.exists?(email: 'test@example.com')
user.orders.exists?

# Pluck
User.pluck(:id)
User.pluck(:id, :name)

# IDs
User.active.ids
```

### Aggregations

```ruby
# Count
User.count
User.where(active: true).count
User.group(:role).count

# Sum
Order.sum(:total)
Order.where(status: :completed).sum(:total)

# Average
Product.average(:price)

# Minimum/Maximum
Product.minimum(:price)
Product.maximum(:price)

# Multiple aggregations
Order.select(
  'COUNT(*) as total_orders',
  'SUM(total) as total_revenue',
  'AVG(total) as average_order'
).first
```

## Transactions

```ruby
# Basic transaction
ActiveRecord::Base.transaction do
  user.save!
  order.save!
  payment.process!
end

# Nested transactions (savepoints)
User.transaction do
  user.update!(name: 'New Name')

  User.transaction(requires_new: true) do
    # This creates a savepoint
    user.orders.update_all(status: :pending)
    raise ActiveRecord::Rollback # Only rolls back this block
  end
end

# Manual rollback
ActiveRecord::Base.transaction do
  user.save!
  raise ActiveRecord::Rollback if some_condition
end

# With lock
User.transaction do
  user = User.lock.find(id)
  user.update!(balance: user.balance - amount)
end
```

## Callbacks Best Practices

```ruby
class Order < ApplicationRecord
  # DO: Use callbacks for data consistency
  before_save :calculate_total
  after_create :generate_order_number

  # DON'T: Use callbacks for external services
  # after_create :send_confirmation_email  # Move to service object

  # DO: Use conditional callbacks
  after_update :notify_customer, if: :status_changed?

  # DO: Use around callbacks for wrapping behavior
  around_save :log_changes

  private

  def calculate_total
    self.total = items.sum { |item| item.price * item.quantity }
  end

  def generate_order_number
    update_column(:order_number, "ORD-#{id.to_s.rjust(8, '0')}")
  end

  def notify_customer
    # Only when status changes
    OrderMailer.status_update(self).deliver_later
  end

  def log_changes
    old_attributes = attributes.dup
    yield
    log_attribute_changes(old_attributes, attributes)
  end
end
```

## Validations

```ruby
class User < ApplicationRecord
  # Presence
  validates :name, presence: true
  validates :email, presence: { message: 'is required' }

  # Uniqueness
  validates :email, uniqueness: { case_sensitive: false, scope: :organization_id }
  validates :username, uniqueness: { conditions: -> { where(deleted_at: nil) } }

  # Format
  validates :email, format: { with: URI::MailTo::EMAIL_REGEXP }
  validates :phone, format: { with: /\A\+?[\d\s\-]+\z/, allow_blank: true }

  # Length
  validates :name, length: { minimum: 2, maximum: 100 }
  validates :bio, length: { maximum: 500 }

  # Numericality
  validates :age, numericality: { greater_than_or_equal_to: 0, only_integer: true }
  validates :price, numericality: { greater_than: 0 }

  # Inclusion/Exclusion
  validates :role, inclusion: { in: %w[user admin moderator] }
  validates :username, exclusion: { in: %w[admin root] }

  # Custom validation
  validate :password_complexity

  private

  def password_complexity
    return if password.blank?

    unless password.match?(/[A-Z]/) && password.match?(/[a-z]/) && password.match?(/\d/)
      errors.add(:password, 'must include uppercase, lowercase, and number')
    end
  end
end
```

## Best Practices

1. **Use scopes** for reusable queries
2. **Avoid N+1 queries** with eager loading
3. **Use transactions** for multi-record operations
4. **Keep callbacks simple** - move complex logic to services
5. **Validate at model level** - for data integrity
6. **Use database constraints** - as backup for validations
7. **Index foreign keys** - and frequently queried columns
