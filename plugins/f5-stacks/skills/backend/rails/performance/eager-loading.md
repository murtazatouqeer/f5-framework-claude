# Eager Loading and N+1 Prevention

Optimizing database queries in Rails applications.

## The N+1 Problem

```ruby
# N+1 Problem - BAD
def index
  @products = Product.all

  # This creates 1 + N queries:
  # 1 query for products
  # N queries for each product's category
  @products.each do |product|
    puts product.category.name  # Triggers query for each product
  end
end

# Solution with includes - GOOD
def index
  @products = Product.includes(:category).all
  # 2 queries total:
  # SELECT * FROM products
  # SELECT * FROM categories WHERE id IN (1, 2, 3, ...)
end
```

## Eager Loading Methods

### includes

```ruby
# Basic includes
Product.includes(:category)

# Multiple associations
Product.includes(:category, :tags)

# Nested associations
Product.includes(category: :parent_category)

# Deep nesting
Product.includes(orders: { user: :profile })

# Multiple nested
Product.includes(:category, reviews: :user)
```

### preload

```ruby
# Always uses separate queries
Product.preload(:category)

# Produces:
# SELECT * FROM products
# SELECT * FROM categories WHERE id IN (...)

# Use when you need separate queries
# or when includes generates inefficient SQL
```

### eager_load

```ruby
# Always uses LEFT OUTER JOIN
Product.eager_load(:category)

# Produces:
# SELECT products.*, categories.*
# FROM products
# LEFT OUTER JOIN categories ON categories.id = products.category_id

# Use when you need to filter by associated records
Product.eager_load(:category).where(categories: { active: true })
```

### Comparison

| Method | Query Type | When to Use |
|--------|-----------|-------------|
| `includes` | Smart (preload or eager_load) | Default choice |
| `preload` | Separate queries | Large datasets, no filtering |
| `eager_load` | JOIN | Filtering by association |

## Detecting N+1 Queries

### Bullet Gem

```ruby
# Gemfile
group :development do
  gem 'bullet'
end

# config/environments/development.rb
config.after_initialize do
  Bullet.enable = true
  Bullet.alert = true
  Bullet.bullet_logger = true
  Bullet.console = true
  Bullet.rails_logger = true
  Bullet.add_footer = true

  # Raise error in test
  Bullet.raise = false

  # Track counter cache
  Bullet.counter_cache_enable = true
end
```

### Prosopite (Alternative)

```ruby
# Gemfile
gem 'prosopite'

# config/environments/development.rb
config.after_initialize do
  Prosopite.rails_logger = true
  Prosopite.raise = false
end

# In application_controller.rb
around_action :prosopite_scan

private

def prosopite_scan
  Prosopite.scan
  yield
ensure
  Prosopite.finish
end
```

## Common Patterns

### Controller with Eager Loading

```ruby
class ProductsController < ApplicationController
  def index
    @products = Product
      .includes(:category, :tags, images_attachments: :blob)
      .active
      .page(params[:page])
  end

  def show
    @product = Product
      .includes(:category, :tags, reviews: :user)
      .find(params[:id])
  end
end
```

### Serializer with Includes

```ruby
# Without optimization - N+1 in serializer
class ProductSerializer
  include JSONAPI::Serializer

  attributes :name, :price

  attribute :category_name do |product|
    product.category.name  # N+1!
  end
end

# With optimization
class ProductsController < ApplicationController
  def index
    @products = Product.includes(:category)
    render json: ProductSerializer.new(@products)
  end
end

class ProductSerializer
  include JSONAPI::Serializer

  attributes :name, :price

  attribute :category_name do |product|
    product.category.name  # No N+1, already loaded
  end
end
```

### Scope with Eager Loading

```ruby
class Product < ApplicationRecord
  scope :with_details, -> {
    includes(:category, :tags, :reviews)
  }

  scope :for_listing, -> {
    includes(:category, images_attachments: :blob)
    .select(:id, :name, :slug, :price, :category_id)
  }

  scope :for_show, -> {
    includes(
      :category,
      :tags,
      reviews: :user,
      images_attachments: :blob
    )
  }
end

# Usage
Product.for_listing.active.page(1)
Product.for_show.find(params[:id])
```

### has_many :through

```ruby
class Product < ApplicationRecord
  has_many :order_items
  has_many :orders, through: :order_items
  has_many :buyers, through: :orders, source: :user
end

# Loading through associations
Product.includes(orders: :user)
Product.includes(:buyers)  # Direct through association
```

## Advanced Patterns

### Conditional Eager Loading

```ruby
class ProductsController < ApplicationController
  def index
    @products = Product.all

    # Add includes based on params
    @products = @products.includes(:category) if include_category?
    @products = @products.includes(:reviews) if include_reviews?
    @products = @products.includes(:tags) if include_tags?
  end

  private

  def include_category?
    params[:include]&.include?('category')
  end
end
```

### GraphQL-like Includes

```ruby
# app/services/includes_builder.rb
class IncludesBuilder
  ALLOWED_INCLUDES = {
    category: {},
    tags: {},
    reviews: { user: {} },
    images: {}
  }.freeze

  def self.build(include_params)
    return [] if include_params.blank?

    requested = include_params.split(',').map(&:strip)
    filter_includes(requested, ALLOWED_INCLUDES)
  end

  private

  def self.filter_includes(requested, allowed)
    allowed.keys.select { |key| requested.include?(key.to_s) }
  end
end

# Controller
def index
  includes = IncludesBuilder.build(params[:include])
  @products = Product.includes(includes).page(params[:page])
end
```

### Preloading in Batches

```ruby
class ProductExporter
  def export_all
    Product.find_each(batch_size: 100) do |product|
      # Each batch automatically preloads
      export_product(product)
    end
  end

  def export_with_associations
    Product.includes(:category, :tags).find_each do |product|
      export_product(product)
    end
  end
end
```

### Strict Loading (Rails 6.1+)

```ruby
# Model level
class Product < ApplicationRecord
  self.strict_loading_by_default = true
end

# Query level
Product.strict_loading.all

# Instance level
product = Product.find(1)
product.strict_loading!
product.category  # Raises StrictLoadingViolationError

# Disable for specific query
Product.strict_loading(false).includes(:category)

# In development/test
# config/environments/development.rb
config.active_record.strict_loading_by_default = true
```

### Preload Manually

```ruby
class ProductsController < ApplicationController
  def index
    @products = Product.active.page(params[:page])

    # Manual preload after query
    ActiveRecord::Associations::Preloader.new(
      records: @products,
      associations: [:category, :tags]
    ).call
  end
end
```

## Polymorphic Associations

```ruby
class Comment < ApplicationRecord
  belongs_to :commentable, polymorphic: true
end

class Product < ApplicationRecord
  has_many :comments, as: :commentable
end

class Article < ApplicationRecord
  has_many :comments, as: :commentable
end

# Loading polymorphic - more complex
comments = Comment.includes(:commentable)
# This loads all types: Product, Article, etc.

# If you know the type
Comment.where(commentable_type: 'Product')
       .includes(:commentable)
```

## Counter Caches

```ruby
# Migration
add_column :products, :reviews_count, :integer, default: 0

# Model
class Review < ApplicationRecord
  belongs_to :product, counter_cache: true
end

# Usage - no query needed
product.reviews_count  # Instead of product.reviews.count

# Custom counter cache name
belongs_to :product, counter_cache: :total_reviews
```

## Aggregate Queries

```ruby
# Instead of loading all and counting in Ruby
Product.all.count  # Loads all records first

# Use database count
Product.count

# With grouping
Product.group(:category_id).count

# Pluck specific columns
Product.pluck(:id, :name)  # Returns array of arrays

# Select specific columns
Product.select(:id, :name, :price)  # Returns AR objects with only those columns
```

## Testing for N+1

```ruby
# spec/controllers/products_controller_spec.rb
RSpec.describe ProductsController, type: :controller do
  describe 'GET #index' do
    it 'does not have N+1 queries' do
      create_list(:product, 5, :with_category, :with_tags)

      expect {
        get :index
      }.to make_database_queries(count: 3)  # products, categories, tags
    end
  end
end

# With Bullet
RSpec.configure do |config|
  config.before(:each) do
    Bullet.start_request
  end

  config.after(:each) do
    Bullet.perform_out_of_channel_notifications if Bullet.notification?
    Bullet.end_request
  end
end
```

## Performance Monitoring

```ruby
# Log slow queries
# config/environments/production.rb
config.active_record.warn_on_records_fetched_greater_than = 1000

# Custom instrumentation
ActiveSupport::Notifications.subscribe('sql.active_record') do |*args|
  event = ActiveSupport::Notifications::Event.new(*args)

  if event.duration > 100  # ms
    Rails.logger.warn "Slow query (#{event.duration.round(2)}ms): #{event.payload[:sql]}"
  end
end
```

## Best Practices

1. **Always check for N+1** - Use Bullet in development
2. **Default to includes** - Let Rails choose preload vs eager_load
3. **Scope common patterns** - `scope :for_listing, -> { includes(:category) }`
4. **Use counter caches** - For counts on associations
5. **Select only needed columns** - `select(:id, :name)` for large tables
6. **Use strict_loading in dev** - Catch missing includes early
7. **Test query counts** - Prevent regression
8. **Profile in production** - Monitor real query patterns
