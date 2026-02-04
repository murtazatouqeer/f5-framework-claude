# Rails Model Template

## Model Template

```ruby
# app/models/{{resource}}.rb
class {{Resource}} < ApplicationRecord
  # === Includes ===
  include Sluggable
  include SoftDeletable

  # === Associations ===
  belongs_to :{{parent}}, optional: false
  belongs_to :created_by, class_name: 'User', optional: true

  has_many :{{children}}, dependent: :destroy
  has_many :{{through_association}}, through: :{{join_table}}

  has_one_attached :{{attachment}}
  has_many_attached :{{attachments}}

  # === Enums ===
  enum :status, {
    draft: 'draft',
    active: 'active',
    archived: 'archived'
  }, prefix: true, default: :draft

  # === Validations ===
  validates :name, presence: true, length: { maximum: 255 }
  validates :slug, presence: true, uniqueness: true
  validates :{{unique_field}}, uniqueness: { scope: :{{scope_field}} }
  validates :{{numeric_field}}, numericality: { greater_than_or_equal_to: 0 }
  validates :email, format: { with: URI::MailTo::EMAIL_REGEXP }, allow_blank: true

  # === Scopes ===
  scope :active, -> { where(status: :active) }
  scope :recent, -> { order(created_at: :desc) }
  scope :by_{{field}}, ->(value) { where({{field}}: value) }
  scope :search, ->(query) {
    where('name ILIKE :q OR description ILIKE :q', q: "%#{query}%")
  }

  # === Callbacks ===
  before_validation :generate_slug, on: :create
  before_save :normalize_data
  after_create :send_notification
  after_commit :invalidate_cache

  # === Class Methods ===
  def self.find_by_identifier(identifier)
    find_by(id: identifier) || find_by(slug: identifier)
  end

  # === Instance Methods ===
  def display_name
    name.presence || "{{Resource}} ##{id}"
  end

  def active?
    status_active?
  end

  def can_be_published?
    draft? && valid?
  end

  def publish!
    return false unless can_be_published?

    update!(status: :active, published_at: Time.current)
  end

  private

  def generate_slug
    self.slug ||= name&.parameterize
  end

  def normalize_data
    self.name = name&.strip
    self.email = email&.downcase&.strip
  end

  def send_notification
    {{Resource}}NotificationJob.perform_async(id)
  end

  def invalidate_cache
    Rails.cache.delete("{{resource_plural}}/#{id}")
    Rails.cache.delete('{{resource_plural}}/all')
  end
end
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{resource}}` | Singular resource name (snake_case) | `product` |
| `{{resource_plural}}` | Plural resource name | `products` |
| `{{Resource}}` | Class name (PascalCase) | `Product` |
| `{{parent}}` | Parent association name | `category` |
| `{{children}}` | Child association name | `reviews` |

## Usage Example

For a `Product` model:

```ruby
# app/models/product.rb
class Product < ApplicationRecord
  # === Includes ===
  include Sluggable
  include SoftDeletable
  include Searchable

  # === Associations ===
  belongs_to :category, optional: false
  belongs_to :created_by, class_name: 'User', optional: true

  has_many :reviews, dependent: :destroy
  has_many :order_items, dependent: :restrict_with_error
  has_many :orders, through: :order_items
  has_many :product_tags, dependent: :destroy
  has_many :tags, through: :product_tags

  has_one_attached :featured_image
  has_many_attached :gallery_images

  # === Enums ===
  enum :status, {
    draft: 'draft',
    active: 'active',
    archived: 'archived'
  }, prefix: true, default: :draft

  # === Validations ===
  validates :name, presence: true, length: { maximum: 255 }
  validates :slug, presence: true, uniqueness: true
  validates :sku, presence: true, uniqueness: { scope: :category_id }
  validates :price, presence: true, numericality: { greater_than_or_equal_to: 0 }
  validates :compare_price, numericality: { greater_than: :price }, allow_nil: true

  # === Scopes ===
  scope :active, -> { where(status: :active) }
  scope :featured, -> { where(featured: true) }
  scope :recent, -> { order(created_at: :desc) }
  scope :by_category, ->(category_id) { where(category_id: category_id) }
  scope :price_range, ->(min, max) { where(price: min..max) }
  scope :on_sale, -> { where('compare_price IS NOT NULL AND compare_price > price') }

  searchable_on :name, :description, :sku

  # === Callbacks ===
  before_validation :generate_slug, on: :create
  before_validation :generate_sku, on: :create
  before_save :calculate_discount
  after_commit :invalidate_cache

  # === Class Methods ===
  def self.find_by_identifier(identifier)
    find_by(id: identifier) || find_by(slug: identifier)
  end

  # === Instance Methods ===
  def display_name
    name.presence || "Product ##{id}"
  end

  def on_sale?
    compare_price.present? && compare_price > price
  end

  def discount_percentage
    return 0 unless on_sale?

    ((compare_price - price) / compare_price * 100).round
  end

  def in_stock?
    stock_quantity.to_i > 0
  end

  def can_be_published?
    status_draft? && valid? && featured_image.attached?
  end

  def publish!
    return false unless can_be_published?

    update!(status: :active, published_at: Time.current)
  end

  def archive!
    update!(status: :archived, archived_at: Time.current)
  end

  private

  def generate_slug
    self.slug ||= name&.parameterize
    ensure_unique_slug if slug_changed?
  end

  def generate_sku
    self.sku ||= "#{category&.code || 'GEN'}-#{SecureRandom.hex(4).upcase}"
  end

  def ensure_unique_slug
    return unless self.class.exists?(slug: slug)

    self.slug = "#{slug}-#{SecureRandom.hex(3)}"
  end

  def calculate_discount
    self.discount_amount = on_sale? ? (compare_price - price) : 0
  end

  def invalidate_cache
    Rails.cache.delete("products/#{id}")
    Rails.cache.delete('products/featured')
    Rails.cache.delete("categories/#{category_id}/products") if saved_change_to_category_id?
  end
end
```

## Model with STI

```ruby
# app/models/notification.rb
class Notification < ApplicationRecord
  belongs_to :user
  belongs_to :notifiable, polymorphic: true

  scope :unread, -> { where(read_at: nil) }

  def mark_as_read!
    update!(read_at: Time.current)
  end
end

# app/models/notifications/order_notification.rb
class Notifications::OrderNotification < Notification
  def message
    "Your order ##{notifiable.order_number} has been #{notifiable.status}"
  end
end

# app/models/notifications/comment_notification.rb
class Notifications::CommentNotification < Notification
  def message
    "#{notifiable.user.name} commented on your post"
  end
end
```
