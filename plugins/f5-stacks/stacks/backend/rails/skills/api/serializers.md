# Rails API Serializers

JSON serialization patterns for Rails APIs.

## JSON:API Serializer (jsonapi-serializer gem)

### Basic Setup

```ruby
# Gemfile
gem 'jsonapi-serializer'
```

### Basic Serializer

```ruby
# app/serializers/product_serializer.rb
class ProductSerializer
  include JSONAPI::Serializer

  # Set type (defaults to class name)
  set_type :product

  # Set ID method (defaults to :id)
  set_id :id

  # Basic attributes
  attributes :name, :slug, :description, :price, :status

  # Computed attributes
  attribute :on_sale do |product|
    product.on_sale?
  end

  attribute :discount_percentage do |product|
    product.discount_percentage
  end

  # Formatted attributes
  attribute :created_at do |product|
    product.created_at.iso8601
  end

  attribute :formatted_price do |product|
    "$%.2f" % product.price
  end

  # Conditional attributes
  attribute :internal_notes, if: proc { |record, params|
    params[:current_user]&.admin?
  }

  # Relationships
  belongs_to :category, serializer: CategorySerializer
  belongs_to :created_by, serializer: UserSerializer, id_method_name: :created_by_id
  has_many :tags, serializer: TagSerializer
  has_many :images, serializer: ImageSerializer

  # Links
  link :self do |product|
    Rails.application.routes.url_helpers.api_v1_product_path(product)
  end

  # Meta
  meta do |product|
    { views_count: product.views_count }
  end
end
```

### Controller Usage

```ruby
# Single record
render json: ProductSerializer.new(product).serializable_hash

# With options
render json: ProductSerializer.new(
  product,
  include: [:category, :tags],
  params: { current_user: current_user }
).serializable_hash

# Collection with pagination
render json: ProductSerializer.new(
  products,
  include: [:category],
  meta: {
    current_page: products.current_page,
    total_pages: products.total_pages,
    total_count: products.total_count
  },
  links: {
    self: request.url,
    next: products.next_page ? url_for(page: products.next_page) : nil,
    prev: products.prev_page ? url_for(page: products.prev_page) : nil
  }
).serializable_hash

# Or render directly
render json: ProductSerializer.new(product), status: :created
```

## Blueprinter (Alternative)

### Basic Setup

```ruby
# Gemfile
gem 'blueprinter'

# config/initializers/blueprinter.rb
Blueprinter.configure do |config|
  config.generator = Oj # Use Oj for faster JSON generation
  config.datetime_format = ->(datetime) { datetime&.iso8601 }
end
```

### Basic Blueprint

```ruby
# app/blueprints/product_blueprint.rb
class ProductBlueprint < Blueprinter::Base
  identifier :id

  # Basic fields
  fields :name, :slug, :description, :price, :status

  # Computed fields
  field :on_sale do |product|
    product.on_sale?
  end

  field :created_at do |product|
    product.created_at.iso8601
  end

  # Associations
  association :category, blueprint: CategoryBlueprint
  association :tags, blueprint: TagBlueprint

  # Views for different contexts
  view :minimal do
    fields :name, :slug, :price
  end

  view :normal do
    include_view :minimal
    fields :description, :status
    association :category, blueprint: CategoryBlueprint
  end

  view :extended do
    include_view :normal
    association :tags, blueprint: TagBlueprint
    association :images, blueprint: ImageBlueprint

    field :internal_notes do |product, options|
      product.internal_notes if options[:current_user]&.admin?
    end
  end
end
```

### Controller Usage

```ruby
# Default view
render json: ProductBlueprint.render(product)

# Specific view
render json: ProductBlueprint.render(product, view: :extended)

# With options
render json: ProductBlueprint.render(
  product,
  view: :extended,
  current_user: current_user
)

# Collection with root
render json: ProductBlueprint.render(
  products,
  view: :normal,
  root: :data,
  meta: { total: products.count }
)
```

## Custom Serializer Pattern

```ruby
# app/serializers/base_serializer.rb
class BaseSerializer
  def initialize(resource, options = {})
    @resource = resource
    @options = options
  end

  def as_json
    if @resource.respond_to?(:map)
      { data: @resource.map { |r| serialize_resource(r) } }
    else
      { data: serialize_resource(@resource) }
    end.merge(meta_data)
  end

  def to_json
    as_json.to_json
  end

  private

  def serialize_resource(resource)
    raise NotImplementedError
  end

  def meta_data
    @options[:meta] ? { meta: @options[:meta] } : {}
  end

  def current_user
    @options[:current_user]
  end
end

# app/serializers/product_serializer.rb
class ProductSerializer < BaseSerializer
  private

  def serialize_resource(product)
    {
      id: product.id,
      type: 'product',
      attributes: {
        name: product.name,
        slug: product.slug,
        description: product.description,
        price: product.price,
        status: product.status,
        on_sale: product.on_sale?,
        discount_percentage: product.discount_percentage,
        created_at: product.created_at.iso8601
      },
      relationships: serialize_relationships(product)
    }
  end

  def serialize_relationships(product)
    {
      category: {
        data: product.category ? { id: product.category.id, type: 'category' } : nil
      },
      tags: {
        data: product.tags.map { |t| { id: t.id, type: 'tag' } }
      }
    }
  end
end
```

## Nested Serializers

```ruby
# app/serializers/order_serializer.rb
class OrderSerializer
  include JSONAPI::Serializer

  attributes :order_number, :status, :total

  attribute :created_at do |order|
    order.created_at.iso8601
  end

  # Nested items with inline serializer
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

  # Or use separate serializer
  has_many :items, serializer: OrderItemSerializer
  belongs_to :user, serializer: UserSerializer
end

class OrderItemSerializer
  include JSONAPI::Serializer

  attributes :quantity, :unit_price, :subtotal

  belongs_to :product, serializer: ProductSerializer
end
```

## Response Helpers

```ruby
# app/controllers/concerns/response_handler.rb
module ResponseHandler
  extend ActiveSupport::Concern

  def render_resource(resource, options = {})
    serializer = options.delete(:serializer) || default_serializer(resource)
    status = options.delete(:status) || :ok

    render json: serializer.new(
      resource,
      options.merge(params: { current_user: current_user })
    ), status: status
  end

  def render_collection(collection, options = {})
    serializer = options.delete(:serializer) || default_serializer(collection)

    render json: serializer.new(
      collection,
      options.merge(
        params: { current_user: current_user },
        meta: pagination_meta(collection)
      )
    )
  end

  def render_error(message, status: :unprocessable_entity)
    render json: { error: message }, status: status
  end

  def render_errors(errors, status: :unprocessable_entity)
    render json: { errors: Array(errors) }, status: status
  end

  private

  def default_serializer(resource)
    model_class = resource.is_a?(ActiveRecord::Relation) ? resource.klass : resource.class
    "#{model_class.name}Serializer".constantize
  end
end
```

## Testing Serializers

```ruby
# spec/serializers/product_serializer_spec.rb
RSpec.describe ProductSerializer do
  let(:product) { create(:product, :with_category, :with_tags) }
  let(:serialized) { described_class.new(product).serializable_hash }

  describe 'attributes' do
    it 'includes basic attributes' do
      expect(serialized[:data][:attributes]).to include(
        :name, :slug, :description, :price, :status
      )
    end

    it 'includes computed attributes' do
      expect(serialized[:data][:attributes]).to include(
        :on_sale, :discount_percentage
      )
    end

    it 'formats dates as ISO8601' do
      expect(serialized[:data][:attributes][:created_at]).to match(/\d{4}-\d{2}-\d{2}T/)
    end
  end

  describe 'relationships' do
    it 'includes category relationship' do
      expect(serialized[:data][:relationships][:category][:data]).to include(
        id: product.category.id,
        type: :category
      )
    end

    it 'includes tags relationship' do
      expect(serialized[:data][:relationships][:tags][:data].size).to eq(product.tags.size)
    end
  end

  describe 'conditional attributes' do
    context 'as admin' do
      let(:serialized) do
        described_class.new(product, params: { current_user: create(:user, :admin) }).serializable_hash
      end

      it 'includes internal_notes' do
        expect(serialized[:data][:attributes]).to have_key(:internal_notes)
      end
    end

    context 'as regular user' do
      let(:serialized) do
        described_class.new(product, params: { current_user: create(:user) }).serializable_hash
      end

      it 'excludes internal_notes' do
        expect(serialized[:data][:attributes]).not_to have_key(:internal_notes)
      end
    end
  end
end
```

## Best Practices

1. **Use consistent serializer library** across the project
2. **Keep serializers focused** - one per resource
3. **Use views/scopes** for different contexts
4. **Format dates consistently** (ISO8601)
5. **Include relationships** only when needed
6. **Pass context via params** (current_user, etc.)
7. **Test serializers** separately from controllers
8. **Document response format** in API docs
