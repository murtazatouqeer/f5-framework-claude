# ActiveRecord Associations

Defining relationships between models in Rails.

## Association Types

### belongs_to

```ruby
class Order < ApplicationRecord
  # Basic belongs_to
  belongs_to :user

  # Optional association
  belongs_to :coupon, optional: true

  # Custom foreign key
  belongs_to :customer, class_name: 'User', foreign_key: 'customer_id'

  # Polymorphic
  belongs_to :payable, polymorphic: true

  # With counter cache
  belongs_to :user, counter_cache: true
  belongs_to :user, counter_cache: :orders_count

  # With touch (updates parent's updated_at)
  belongs_to :user, touch: true
  belongs_to :user, touch: :orders_updated_at

  # With default
  belongs_to :status, default: -> { Status.find_by(name: 'pending') }

  # Inverse of
  belongs_to :user, inverse_of: :orders
end
```

### has_many

```ruby
class User < ApplicationRecord
  # Basic has_many
  has_many :orders

  # With dependent option
  has_many :comments, dependent: :destroy
  has_many :posts, dependent: :nullify
  has_many :audit_logs, dependent: :delete_all
  has_many :orders, dependent: :restrict_with_error

  # Custom foreign key
  has_many :created_products, class_name: 'Product', foreign_key: 'created_by_id'

  # With scope
  has_many :published_posts, -> { where(status: 'published') }, class_name: 'Post'
  has_many :recent_orders, -> { order(created_at: :desc).limit(5) }, class_name: 'Order'

  # Polymorphic
  has_many :comments, as: :commentable

  # With conditions
  has_many :active_subscriptions, -> { where(active: true) }, class_name: 'Subscription'

  # Ordering
  has_many :posts, -> { order(created_at: :desc) }

  # Extending association
  has_many :orders do
    def total_revenue
      sum(:total)
    end

    def pending
      where(status: 'pending')
    end
  end

  # Source type for polymorphic through
  has_many :comments, through: :posts
end
```

### has_one

```ruby
class User < ApplicationRecord
  # Basic has_one
  has_one :profile

  # With dependent
  has_one :profile, dependent: :destroy

  # Custom foreign key
  has_one :account, class_name: 'BankAccount', foreign_key: 'owner_id'

  # With scope
  has_one :latest_order, -> { order(created_at: :desc) }, class_name: 'Order'

  # Through another association
  has_one :address, through: :profile
end
```

### has_many :through

```ruby
class User < ApplicationRecord
  has_many :user_roles
  has_many :roles, through: :user_roles

  has_many :orders
  has_many :ordered_products, through: :orders, source: :products

  # With conditions on through
  has_many :admin_roles, -> { where(name: 'admin') }, through: :user_roles, source: :role
end

class UserRole < ApplicationRecord
  belongs_to :user
  belongs_to :role
end

class Role < ApplicationRecord
  has_many :user_roles
  has_many :users, through: :user_roles
end
```

### has_and_belongs_to_many

```ruby
class Product < ApplicationRecord
  has_and_belongs_to_many :tags

  # With join table name
  has_and_belongs_to_many :categories,
    join_table: 'categorizations'

  # With scope
  has_and_belongs_to_many :tags, -> { distinct }
end

class Tag < ApplicationRecord
  has_and_belongs_to_many :products
end

# Migration for join table
class CreateProductsTags < ActiveRecord::Migration[7.1]
  def change
    create_table :products_tags, id: false do |t|
      t.references :product, null: false, foreign_key: true, type: :uuid
      t.references :tag, null: false, foreign_key: true, type: :uuid
    end

    add_index :products_tags, [:product_id, :tag_id], unique: true
  end
end
```

## Polymorphic Associations

```ruby
# Comment can belong to Post, Product, or User
class Comment < ApplicationRecord
  belongs_to :commentable, polymorphic: true
  belongs_to :user
end

class Post < ApplicationRecord
  has_many :comments, as: :commentable, dependent: :destroy
end

class Product < ApplicationRecord
  has_many :comments, as: :commentable, dependent: :destroy
end

# Migration
class CreateComments < ActiveRecord::Migration[7.1]
  def change
    create_table :comments, id: :uuid do |t|
      t.text :body, null: false
      t.references :user, null: false, foreign_key: true, type: :uuid
      t.references :commentable, polymorphic: true, null: false, type: :uuid

      t.timestamps
    end

    add_index :comments, [:commentable_type, :commentable_id]
  end
end
```

## Self-Referential Associations

```ruby
# Employee hierarchy
class Employee < ApplicationRecord
  belongs_to :manager, class_name: 'Employee', optional: true
  has_many :subordinates, class_name: 'Employee', foreign_key: 'manager_id'

  # All descendants (recursive)
  def all_subordinates
    subordinates.flat_map { |s| [s] + s.all_subordinates }
  end
end

# Category tree
class Category < ApplicationRecord
  belongs_to :parent, class_name: 'Category', optional: true
  has_many :children, class_name: 'Category', foreign_key: 'parent_id'

  scope :roots, -> { where(parent_id: nil) }

  def ancestors
    parent ? [parent] + parent.ancestors : []
  end

  def descendants
    children.flat_map { |c| [c] + c.descendants }
  end
end

# Friendship (many-to-many self-join)
class User < ApplicationRecord
  has_many :friendships
  has_many :friends, through: :friendships

  has_many :inverse_friendships, class_name: 'Friendship', foreign_key: 'friend_id'
  has_many :inverse_friends, through: :inverse_friendships, source: :user

  def all_friends
    friends + inverse_friends
  end
end

class Friendship < ApplicationRecord
  belongs_to :user
  belongs_to :friend, class_name: 'User'

  validates :user_id, uniqueness: { scope: :friend_id }
end
```

## Association Callbacks

```ruby
class User < ApplicationRecord
  has_many :orders,
    before_add: :check_credit_limit,
    after_add: :send_notification,
    before_remove: :validate_removal,
    after_remove: :log_removal

  private

  def check_credit_limit(order)
    raise 'Credit limit exceeded' if orders.sum(:total) + order.total > credit_limit
  end

  def send_notification(order)
    OrderMailer.new_order(order).deliver_later
  end

  def validate_removal(order)
    raise 'Cannot remove completed orders' if order.completed?
  end

  def log_removal(order)
    audit_logs.create!(action: 'order_removed', data: order.attributes)
  end
end
```

## Association Extensions

```ruby
class User < ApplicationRecord
  has_many :orders do
    def pending
      where(status: 'pending')
    end

    def completed
      where(status: 'completed')
    end

    def total_spent
      completed.sum(:total)
    end

    def average_order_value
      completed.average(:total)
    end

    def place_new(attributes)
      order = build(attributes)
      order.calculate_total
      order.save!
      order
    end
  end
end

# Usage
user.orders.pending
user.orders.total_spent
user.orders.place_new(items: [...])
```

## Eager Loading

```ruby
# Includes (separate queries)
User.includes(:orders, :profile)

# Preload (always separate queries)
User.preload(:orders)

# Eager load (single LEFT OUTER JOIN)
User.eager_load(:orders)

# Nested eager loading
User.includes(orders: [:items, :payments])
User.includes(orders: { items: :product })

# Conditional eager loading
User.includes(:orders).where(orders: { status: 'pending' })

# References (required when filtering on included association)
User.includes(:orders).where('orders.total > ?', 100).references(:orders)
```

## Association Options Summary

| Option | Description |
|--------|-------------|
| `class_name` | Specify the model class |
| `foreign_key` | Specify the foreign key column |
| `primary_key` | Specify the primary key column |
| `dependent` | What happens when parent is destroyed |
| `counter_cache` | Maintain count on parent |
| `touch` | Update parent's timestamp |
| `optional` | Allow nil association |
| `inverse_of` | Specify inverse association |
| `source` | For through associations |
| `source_type` | For polymorphic through |

## Best Practices

1. **Always specify `dependent`** for has_many/has_one
2. **Use `inverse_of`** for bidirectional associations
3. **Use `counter_cache`** for frequent counting
4. **Prefer has_many :through** over has_and_belongs_to_many
5. **Index foreign keys** in migrations
6. **Use eager loading** to avoid N+1 queries
7. **Consider `touch`** for cache invalidation
