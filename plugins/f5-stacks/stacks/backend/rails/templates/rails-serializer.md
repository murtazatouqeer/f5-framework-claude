# Rails Serializer Template

## JSON:API Serializer Template

```ruby
# app/serializers/{{resource}}_serializer.rb
class {{Resource}}Serializer
  include JSONAPI::Serializer

  # Set resource type
  set_type :{{resource}}
  set_id :id

  # === Attributes ===
  attributes :{{ATTRIBUTES}}

  # === Computed Attributes ===
  attribute :created_at do |object|
    object.created_at.iso8601
  end

  attribute :updated_at do |object|
    object.updated_at.iso8601
  end

  attribute :{{computed_field}} do |object|
    object.{{computed_method}}
  end

  # === Conditional Attributes ===
  attribute :{{admin_field}}, if: proc { |record, params|
    params[:current_user]&.admin?
  }

  # === Relationships ===
  belongs_to :{{parent}}, serializer: {{Parent}}Serializer
  has_many :{{children}}, serializer: {{Child}}Serializer

  # === Links ===
  link :self do |object|
    Rails.application.routes.url_helpers.api_v1_{{resource}}_path(object)
  end

  # === Meta ===
  meta do |object|
    {
      {{meta_field}}: object.{{meta_value}}
    }
  end
end
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{resource}}` | Resource name (snake_case) | `product` |
| `{{Resource}}` | Class name (PascalCase) | `Product` |
| `{{ATTRIBUTES}}` | Basic attributes | `:name, :slug, :description` |
| `{{parent}}` | Parent relationship | `category` |
| `{{children}}` | Children relationship | `reviews` |

## Usage Example

For a `Product` serializer:

```ruby
# app/serializers/product_serializer.rb
class ProductSerializer
  include JSONAPI::Serializer

  set_type :product
  set_id :id

  # === Basic Attributes ===
  attributes :name, :slug, :description, :price, :compare_price, :status, :sku

  # === Formatted Dates ===
  attribute :created_at do |product|
    product.created_at.iso8601
  end

  attribute :updated_at do |product|
    product.updated_at.iso8601
  end

  attribute :published_at do |product|
    product.published_at&.iso8601
  end

  # === Computed Attributes ===
  attribute :on_sale do |product|
    product.on_sale?
  end

  attribute :discount_percentage do |product|
    product.discount_percentage
  end

  attribute :in_stock do |product|
    product.in_stock?
  end

  attribute :formatted_price do |product|
    "$%.2f" % product.price
  end

  attribute :image_url do |product|
    if product.featured_image.attached?
      Rails.application.routes.url_helpers.rails_blob_url(product.featured_image, only_path: true)
    end
  end

  # === Conditional Attributes (Admin Only) ===
  attribute :internal_notes, if: proc { |_record, params|
    params[:current_user]&.admin?
  }

  attribute :cost_price, if: proc { |_record, params|
    params[:current_user]&.admin?
  }

  attribute :profit_margin, if: proc { |_record, params|
    params[:current_user]&.admin?
  } do |product|
    return nil unless product.cost_price

    ((product.price - product.cost_price) / product.price * 100).round(2)
  end

  # === Relationships ===
  belongs_to :category, serializer: CategorySerializer
  belongs_to :created_by, serializer: UserSerializer, id_method_name: :created_by_id

  has_many :tags, serializer: TagSerializer
  has_many :reviews, serializer: ReviewSerializer
  has_many :gallery_images, serializer: ImageSerializer

  # === Links ===
  link :self do |product|
    Rails.application.routes.url_helpers.api_v1_product_path(product)
  end

  link :category do |product|
    Rails.application.routes.url_helpers.api_v1_category_path(product.category_id) if product.category_id
  end

  # === Meta ===
  meta do |product|
    {
      reviews_count: product.reviews_count,
      average_rating: product.average_rating,
      views_count: product.views_count
    }
  end
end
```

## Blueprinter Template

```ruby
# app/blueprints/{{resource}}_blueprint.rb
class {{Resource}}Blueprint < Blueprinter::Base
  identifier :id

  # === Basic Fields ===
  fields :{{FIELDS}}

  # === Computed Fields ===
  field :created_at do |object|
    object.created_at.iso8601
  end

  field :{{computed_field}} do |object|
    object.{{computed_method}}
  end

  # === Associations ===
  association :{{parent}}, blueprint: {{Parent}}Blueprint
  association :{{children}}, blueprint: {{Child}}Blueprint

  # === Views ===
  view :minimal do
    fields :name, :slug
  end

  view :normal do
    include_view :minimal
    fields :description, :price, :status
    association :category, blueprint: CategoryBlueprint
  end

  view :extended do
    include_view :normal
    association :tags, blueprint: TagBlueprint
    association :reviews, blueprint: ReviewBlueprint

    field :admin_notes do |object, options|
      object.admin_notes if options[:current_user]&.admin?
    end
  end
end
```

## Blueprinter Example

```ruby
# app/blueprints/product_blueprint.rb
class ProductBlueprint < Blueprinter::Base
  identifier :id

  # === Basic Fields ===
  fields :name, :slug, :description, :price, :compare_price, :status, :sku

  # === Formatted Dates ===
  field :created_at do |product|
    product.created_at.iso8601
  end

  field :updated_at do |product|
    product.updated_at.iso8601
  end

  # === Computed Fields ===
  field :on_sale do |product|
    product.on_sale?
  end

  field :discount_percentage do |product|
    product.discount_percentage
  end

  field :in_stock do |product|
    product.in_stock?
  end

  field :image_url do |product|
    product.featured_image.attached? ? product.featured_image.url : nil
  end

  # === Views ===
  view :minimal do
    fields :name, :slug, :price
    field :image_url
  end

  view :listing do
    include_view :minimal
    fields :description, :status, :compare_price
    field :on_sale
    field :discount_percentage
    association :category, blueprint: CategoryBlueprint, view: :minimal
  end

  view :detail do
    include_view :listing
    fields :sku, :stock_quantity
    field :in_stock
    association :tags, blueprint: TagBlueprint
    association :reviews, blueprint: ReviewBlueprint, view: :with_user
  end

  view :admin do
    include_view :detail
    fields :internal_notes, :cost_price, :created_by_id

    field :profit_margin do |product|
      return nil unless product.cost_price

      ((product.price - product.cost_price) / product.price * 100).round(2)
    end

    association :created_by, blueprint: UserBlueprint, view: :minimal
  end
end

# Controller usage
render json: ProductBlueprint.render(@product, view: :detail)
render json: ProductBlueprint.render(@products, view: :listing, root: :data)
```

## Nested Serializer

```ruby
# app/serializers/order_serializer.rb
class OrderSerializer
  include JSONAPI::Serializer

  set_type :order

  attributes :order_number, :status

  # Inline nested serialization
  attribute :items do |order|
    order.items.map do |item|
      {
        id: item.id,
        product_name: item.product.name,
        quantity: item.quantity,
        unit_price: item.unit_price,
        subtotal: item.subtotal
      }
    end
  end

  attribute :totals do |order|
    {
      subtotal: order.subtotal,
      tax: order.tax,
      shipping: order.shipping,
      discount: order.discount,
      total: order.total
    }
  end

  belongs_to :user, serializer: UserSerializer
  has_many :items, serializer: OrderItemSerializer
end
```
