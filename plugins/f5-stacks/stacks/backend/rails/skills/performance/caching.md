# Rails Caching Strategies

Performance optimization through caching in Rails applications.

## Cache Configuration

### Development

```ruby
# config/environments/development.rb
if Rails.root.join('tmp/caching-dev.txt').exist?
  config.action_controller.perform_caching = true
  config.cache_store = :memory_store
  config.public_file_server.headers = {
    'Cache-Control' => "public, max-age=#{2.days.to_i}"
  }
else
  config.action_controller.perform_caching = false
  config.cache_store = :null_store
end
```

### Production with Redis

```ruby
# config/environments/production.rb
config.cache_store = :redis_cache_store, {
  url: ENV.fetch('REDIS_URL', 'redis://localhost:6379/0'),
  namespace: 'cache',
  expires_in: 1.day,
  compress: true,
  compress_threshold: 1.kilobyte,
  pool_size: ENV.fetch('RAILS_MAX_THREADS', 5).to_i,
  pool_timeout: 5,
  error_handler: -> (method:, returning:, exception:) {
    Rails.logger.error "Redis cache error: #{exception}"
    Sentry.capture_exception(exception)
  }
}

# Alternative: Memcached
config.cache_store = :mem_cache_store, ENV['MEMCACHED_URL'],
  { namespace: 'myapp', expires_in: 1.day, compress: true }
```

## Low-Level Caching

### Basic Cache Operations

```ruby
# Write to cache
Rails.cache.write('user_count', User.count, expires_in: 1.hour)

# Read from cache
count = Rails.cache.read('user_count')

# Delete from cache
Rails.cache.delete('user_count')

# Check existence
Rails.cache.exist?('user_count')

# Fetch with block (read or write)
count = Rails.cache.fetch('user_count', expires_in: 1.hour) do
  User.count
end

# Force refresh
count = Rails.cache.fetch('user_count', expires_in: 1.hour, force: true) do
  User.count
end
```

### Cache Keys

```ruby
# Model-based cache keys
class Product < ApplicationRecord
  def cache_key_with_version
    "products/#{id}-#{updated_at.to_i}"
  end
end

# Custom cache keys
def cache_key_for_products
  max_updated_at = Product.maximum(:updated_at).try(:to_i)
  "products/all-#{max_updated_at}"
end

# Collection cache key
products = Product.active
cache_key = products.cache_key_with_version  # Built-in Rails method
```

## Fragment Caching (Views)

```erb
<%# app/views/products/show.html.erb %>
<% cache @product do %>
  <div class="product">
    <h1><%= @product.name %></h1>
    <p><%= @product.description %></p>
    <%= render @product.reviews %>
  </div>
<% end %>

<%# With explicit key %>
<% cache ['v1', @product] do %>
  ...
<% end %>

<%# With expiration %>
<% cache @product, expires_in: 1.hour do %>
  ...
<% end %>
```

### Collection Caching

```erb
<%# Renders each product with caching %>
<%= render partial: 'product', collection: @products, cached: true %>

<%# app/views/products/_product.html.erb %>
<% cache product do %>
  <div class="product">
    <%= product.name %> - <%= product.price %>
  </div>
<% end %>
```

## Russian Doll Caching

```erb
<%# app/views/products/show.html.erb %>
<% cache @product do %>
  <article>
    <h1><%= @product.name %></h1>

    <%# Nested cache %>
    <% cache @product.category do %>
      <div class="category">
        <%= @product.category.name %>
      </div>
    <% end %>

    <%# Another nested cache %>
    <div class="reviews">
      <%= render @product.reviews %>
    </div>
  </article>
<% end %>

<%# app/views/reviews/_review.html.erb %>
<% cache review do %>
  <div class="review">
    <%= review.body %>
    <span><%= review.user.name %></span>
  </div>
<% end %>
```

### Touch for Cache Invalidation

```ruby
class Review < ApplicationRecord
  belongs_to :product, touch: true
  belongs_to :user
end

class Product < ApplicationRecord
  belongs_to :category, touch: true
  has_many :reviews
end

# When review is updated, product's updated_at is touched
# Which invalidates product cache
# And also touches category, invalidating category cache
```

## HTTP Caching

### ETags and Last-Modified

```ruby
class ProductsController < ApplicationController
  def show
    @product = Product.find(params[:id])

    # ETag based on product
    if stale?(@product)
      render json: ProductSerializer.new(@product)
    end
  end

  def index
    @products = Product.active

    # Last-modified header
    if stale?(last_modified: @products.maximum(:updated_at))
      render json: ProductSerializer.new(@products)
    end
  end
end
```

### Strong ETags

```ruby
def show
  @product = Product.find(params[:id])

  # Strong ETag - exact match required
  fresh_when(@product, strong_etag: true)
end

# Custom ETag
def show
  @product = Product.find(params[:id])

  fresh_when(
    etag: [@product, current_user.role],
    last_modified: @product.updated_at
  )
end
```

### Cache-Control Headers

```ruby
class ProductsController < ApplicationController
  def index
    @products = Product.active

    # Public cache (CDN cacheable)
    expires_in 1.hour, public: true

    render json: ProductSerializer.new(@products)
  end

  def show
    @product = Product.find(params[:id])

    # Private cache (user-specific)
    expires_in 5.minutes, public: false

    render json: ProductSerializer.new(@product)
  end
end
```

## Query Caching

### Automatic Query Cache

```ruby
# Rails automatically caches identical queries within a request
class ProductsController < ApplicationController
  def show
    @product = Product.find(params[:id])  # First query
    @related = Product.where(category_id: @product.category_id)  # Second query

    # If @product is accessed again, it's served from query cache
    render json: @product  # No new query
  end
end
```

### Manual Cache Wrapping

```ruby
# Cache expensive queries
class Product < ApplicationRecord
  def self.featured
    Rails.cache.fetch('products/featured', expires_in: 1.hour) do
      where(featured: true)
        .includes(:category, :images)
        .order(created_at: :desc)
        .limit(10)
        .to_a  # Execute and cache array
    end
  end

  def self.categories_with_counts
    Rails.cache.fetch('products/category_counts', expires_in: 30.minutes) do
      joins(:category)
        .group('categories.name')
        .count
    end
  end
end
```

## Counter Caches

```ruby
# Migration
class AddProductsCountToCategories < ActiveRecord::Migration[7.1]
  def change
    add_column :categories, :products_count, :integer, default: 0

    # Backfill existing counts
    Category.find_each do |category|
      Category.reset_counters(category.id, :products)
    end
  end
end

# Model
class Product < ApplicationRecord
  belongs_to :category, counter_cache: true
end

class Category < ApplicationRecord
  has_many :products
end

# Usage - no query needed
category.products_count  # Instead of category.products.count
```

## Caching Services

```ruby
# app/services/cached_product_service.rb
class CachedProductService
  CACHE_TTL = 1.hour

  def self.featured_products
    Rails.cache.fetch(cache_key(:featured), expires_in: CACHE_TTL) do
      Product.featured.includes(:category, :images).to_a
    end
  end

  def self.product_stats
    Rails.cache.fetch(cache_key(:stats), expires_in: 15.minutes) do
      {
        total: Product.count,
        active: Product.active.count,
        by_category: Product.group(:category_id).count,
        average_price: Product.average(:price)
      }
    end
  end

  def self.invalidate_featured
    Rails.cache.delete(cache_key(:featured))
  end

  def self.invalidate_all
    Rails.cache.delete_matched('products/*')
  end

  private

  def self.cache_key(suffix)
    "products/#{suffix}"
  end
end
```

## Cache Invalidation Patterns

### Model Callbacks

```ruby
class Product < ApplicationRecord
  after_commit :invalidate_cache

  private

  def invalidate_cache
    Rails.cache.delete("products/#{id}")
    Rails.cache.delete('products/featured') if featured?
    CachedProductService.invalidate_all
  end
end
```

### Observer Pattern

```ruby
# app/observers/cache_invalidation_observer.rb
class CacheInvalidationObserver
  def self.product_updated(product)
    Rails.cache.delete("products/#{product.id}")
    Rails.cache.delete("categories/#{product.category_id}/products")
  end

  def self.category_updated(category)
    Rails.cache.delete("categories/#{category.id}")
    Rails.cache.delete_matched("categories/#{category.id}/*")
  end
end

# Usage
after_commit -> { CacheInvalidationObserver.product_updated(self) }, on: [:create, :update, :destroy]
```

### Versioned Cache Keys

```ruby
class Product < ApplicationRecord
  # Automatic versioning via updated_at
  def serializer_cache_key
    "#{cache_key_with_version}/serialized"
  end
end

# In serializer
def cached_serialization(product)
  Rails.cache.fetch(product.serializer_cache_key) do
    ProductSerializer.new(product).serializable_hash
  end
end
```

## API Response Caching

```ruby
# app/controllers/api/v1/products_controller.rb
module Api
  module V1
    class ProductsController < BaseController
      def index
        @products = cached_products

        expires_in 5.minutes, public: true
        render json: cached_response
      end

      def show
        @product = Product.find(params[:id])

        if stale?(@product)
          render json: cached_product_response(@product)
        end
      end

      private

      def cached_products
        Rails.cache.fetch(products_cache_key, expires_in: 5.minutes) do
          Product.active.includes(:category).to_a
        end
      end

      def products_cache_key
        ['products', Product.maximum(:updated_at)].join('/')
      end

      def cached_response
        Rails.cache.fetch([products_cache_key, 'serialized']) do
          ProductSerializer.new(@products).serializable_hash
        end
      end

      def cached_product_response(product)
        Rails.cache.fetch(product.serializer_cache_key) do
          ProductSerializer.new(product).serializable_hash
        end
      end
    end
  end
end
```

## Caching with Pagination

```ruby
class ProductsController < ApplicationController
  def index
    page = params[:page] || 1
    per_page = params[:per_page] || 20

    @products = Rails.cache.fetch(page_cache_key(page, per_page), expires_in: 5.minutes) do
      Product.active
        .page(page)
        .per(per_page)
        .to_a
    end

    render json: ProductSerializer.new(@products)
  end

  private

  def page_cache_key(page, per_page)
    max_updated = Product.active.maximum(:updated_at).to_i
    "products/page/#{page}/#{per_page}/#{max_updated}"
  end
end
```

## Cache Warming

```ruby
# lib/tasks/cache.rake
namespace :cache do
  desc 'Warm up cache'
  task warm: :environment do
    puts 'Warming product cache...'
    CachedProductService.featured_products
    CachedProductService.product_stats

    puts 'Warming category cache...'
    Category.find_each do |category|
      Rails.cache.fetch("categories/#{category.id}/products") do
        category.products.active.to_a
      end
    end

    puts 'Cache warmed!'
  end

  desc 'Clear all cache'
  task clear: :environment do
    Rails.cache.clear
    puts 'Cache cleared!'
  end
end
```

## Best Practices

1. **Cache at the right level** - Start with HTTP caching, then fragment, then low-level
2. **Use versioned cache keys** - Include updated_at or version numbers
3. **Set appropriate TTLs** - Balance freshness vs performance
4. **Use touch for associations** - Automatic cache invalidation
5. **Cache serialized responses** - Avoid repeated serialization
6. **Monitor cache hit rates** - Use Redis INFO or similar
7. **Warm cache after deploys** - Pre-populate important caches
8. **Handle cache failures gracefully** - Fallback to database queries
