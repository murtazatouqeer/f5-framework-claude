# ActiveRecord Scopes

Reusable query components for cleaner, more maintainable code.

## Basic Scopes

```ruby
class Product < ApplicationRecord
  # Simple scope
  scope :active, -> { where(status: 'active') }
  scope :featured, -> { where(is_featured: true) }
  scope :in_stock, -> { where('quantity > 0') }

  # Scope with ordering
  scope :recent, -> { order(created_at: :desc) }
  scope :by_name, -> { order(:name) }
  scope :cheapest_first, -> { order(price: :asc) }

  # Scope with limit
  scope :top_sellers, -> { order(sales_count: :desc).limit(10) }
  scope :newest, -> { order(created_at: :desc).limit(5) }
end
```

## Scopes with Arguments

```ruby
class Product < ApplicationRecord
  # Single argument
  scope :by_category, ->(category_id) { where(category_id: category_id) }
  scope :cheaper_than, ->(price) { where('price < ?', price) }
  scope :status, ->(status) { where(status: status) }

  # Multiple arguments
  scope :in_price_range, ->(min, max) { where(price: min..max) }

  # Hash argument
  scope :filter_by, ->(filters) {
    result = all
    result = result.where(status: filters[:status]) if filters[:status].present?
    result = result.where(category_id: filters[:category_id]) if filters[:category_id].present?
    result = result.where('price >= ?', filters[:min_price]) if filters[:min_price].present?
    result = result.where('price <= ?', filters[:max_price]) if filters[:max_price].present?
    result
  }

  # Optional argument with default
  scope :published_since, ->(date = 1.month.ago) { where('published_at >= ?', date) }

  # With nil handling (returns all if argument is nil)
  scope :by_category, ->(category_id) {
    category_id.present? ? where(category_id: category_id) : all
  }
end
```

## Chainable Scopes

```ruby
class Product < ApplicationRecord
  scope :active, -> { where(status: 'active') }
  scope :featured, -> { where(is_featured: true) }
  scope :by_category, ->(id) { where(category_id: id) if id.present? }
  scope :in_price_range, ->(min, max) { where(price: (min || 0)..(max || Float::INFINITY)) }
  scope :search, ->(term) { where('name ILIKE ?', "%#{term}%") if term.present? }
  scope :recent, -> { order(created_at: :desc) }
end

# Chaining in controller
@products = Product
  .active
  .featured
  .by_category(params[:category_id])
  .in_price_range(params[:min_price], params[:max_price])
  .search(params[:q])
  .recent
  .page(params[:page])
```

## Advanced Scopes

### Using Arel

```ruby
class Product < ApplicationRecord
  # Complex conditions with Arel
  scope :discounted, -> {
    where(arel_table[:compare_price].gt(arel_table[:price]))
  }

  # Case insensitive search
  scope :name_contains, ->(term) {
    where(arel_table[:name].matches("%#{term}%"))
  }

  # OR conditions
  scope :sale_or_featured, -> {
    where(is_featured: true).or(where.not(compare_price: nil))
  }
end
```

### Joins and Includes

```ruby
class Product < ApplicationRecord
  # With joins
  scope :with_category_name, ->(name) {
    joins(:category).where(categories: { name: name })
  }

  # With eager loading
  scope :with_associations, -> { includes(:category, :tags, :images) }

  # Complex join with conditions
  scope :bestsellers_in_category, ->(category_id) {
    joins(:order_items)
      .where(category_id: category_id)
      .group(:id)
      .order('COUNT(order_items.id) DESC')
  }

  # Subquery scope
  scope :popular, -> {
    where(id: OrderItem.select(:product_id)
                       .group(:product_id)
                       .having('COUNT(*) > 10'))
  }
end
```

### Date Scopes

```ruby
class Order < ApplicationRecord
  # Date ranges
  scope :today, -> { where(created_at: Time.current.all_day) }
  scope :this_week, -> { where(created_at: Time.current.all_week) }
  scope :this_month, -> { where(created_at: Time.current.all_month) }
  scope :this_year, -> { where(created_at: Time.current.all_year) }

  # Custom date range
  scope :between_dates, ->(start_date, end_date) {
    where(created_at: start_date.beginning_of_day..end_date.end_of_day)
  }

  # Recent
  scope :recent, ->(period = 7.days) { where('created_at > ?', period.ago) }

  # Future/Past
  scope :upcoming, -> { where('scheduled_at > ?', Time.current) }
  scope :past, -> { where('scheduled_at < ?', Time.current) }
end
```

### Status Scopes with Enum

```ruby
class Order < ApplicationRecord
  enum status: {
    pending: 'pending',
    processing: 'processing',
    shipped: 'shipped',
    delivered: 'delivered',
    cancelled: 'cancelled'
  }, _prefix: true

  # Rails automatically creates scopes for enums:
  # Order.status_pending
  # Order.status_processing
  # etc.

  # Additional status groupings
  scope :active, -> { where(status: [:pending, :processing, :shipped]) }
  scope :completed, -> { where(status: [:delivered, :cancelled]) }
  scope :in_transit, -> { where(status: [:processing, :shipped]) }
end
```

## Default Scope

```ruby
class Product < ApplicationRecord
  # Use with caution - applies to ALL queries
  default_scope { where(deleted_at: nil) }

  # Override with unscoped
  # Product.unscoped.all  # includes deleted products

  # Better: use explicit scope
  scope :active, -> { where(deleted_at: nil) }
end

# If you must use default_scope, make it orderly
class Comment < ApplicationRecord
  default_scope { order(created_at: :desc) }
end
```

## Query Objects (Alternative to Complex Scopes)

```ruby
# app/queries/products_query.rb
class ProductsQuery
  def initialize(relation = Product.all)
    @relation = relation
  end

  def call(params = {})
    @relation
      .then { |r| filter_by_status(r, params[:status]) }
      .then { |r| filter_by_category(r, params[:category_id]) }
      .then { |r| filter_by_price(r, params[:min_price], params[:max_price]) }
      .then { |r| search(r, params[:q]) }
      .then { |r| sort(r, params[:sort_by], params[:sort_order]) }
  end

  private

  def filter_by_status(relation, status)
    return relation if status.blank?
    relation.where(status: status)
  end

  def filter_by_category(relation, category_id)
    return relation if category_id.blank?
    relation.where(category_id: category_id)
  end

  def filter_by_price(relation, min, max)
    relation = relation.where('price >= ?', min) if min.present?
    relation = relation.where('price <= ?', max) if max.present?
    relation
  end

  def search(relation, term)
    return relation if term.blank?
    relation.where('name ILIKE ? OR description ILIKE ?', "%#{term}%", "%#{term}%")
  end

  def sort(relation, sort_by, sort_order)
    valid_columns = %w[name price created_at]
    sort_by = valid_columns.include?(sort_by) ? sort_by : 'created_at'
    sort_order = %w[asc desc].include?(sort_order) ? sort_order : 'desc'
    relation.order(sort_by => sort_order)
  end
end

# Usage
@products = ProductsQuery.new.call(params.permit(:status, :category_id, :min_price, :max_price, :q, :sort_by, :sort_order))
```

## Testing Scopes

```ruby
# spec/models/product_spec.rb
RSpec.describe Product, type: :model do
  describe 'scopes' do
    describe '.active' do
      it 'returns only active products' do
        active = create(:product, status: 'active')
        inactive = create(:product, status: 'inactive')

        expect(Product.active).to include(active)
        expect(Product.active).not_to include(inactive)
      end
    end

    describe '.by_category' do
      it 'filters by category when provided' do
        category = create(:category)
        in_category = create(:product, category: category)
        other = create(:product)

        expect(Product.by_category(category.id)).to include(in_category)
        expect(Product.by_category(category.id)).not_to include(other)
      end

      it 'returns all when category is nil' do
        products = create_list(:product, 3)
        expect(Product.by_category(nil)).to match_array(products)
      end
    end

    describe '.in_price_range' do
      it 'filters by price range' do
        cheap = create(:product, price: 10)
        medium = create(:product, price: 50)
        expensive = create(:product, price: 100)

        expect(Product.in_price_range(20, 80)).to include(medium)
        expect(Product.in_price_range(20, 80)).not_to include(cheap, expensive)
      end
    end
  end
end
```

## Best Practices

1. **Keep scopes simple** - Complex logic belongs in query objects
2. **Handle nil arguments** - Return `all` or handle gracefully
3. **Make scopes chainable** - Always return an ActiveRecord::Relation
4. **Avoid default_scope** - Use explicit scopes instead
5. **Name scopes clearly** - `active`, `recent`, `by_category`
6. **Test scopes** - They're part of your model's interface
7. **Use query objects** for complex filtering logic
