# Rails Serializer Generator Agent

Agent for generating JSON serializers for Rails API responses.

## Capabilities

- Generate JSON:API compliant serializers
- Generate Blueprinter serializers
- Define attributes and relationships
- Create conditional attributes
- Support nested serialization
- Generate multiple views

## Input Schema

```yaml
model_name: string       # Model to serialize (e.g., "Product")
serializer_type: string  # "jsonapi" or "blueprinter"
attributes: array        # Attributes to include
computed: array         # Computed/virtual attributes
relationships: array    # Associated models to include
views: array            # Different serialization views
conditional: array      # Conditional attributes
links: boolean          # Include self links
```

## Example Usage

```yaml
model_name: Product
serializer_type: jsonapi
attributes:
  - name
  - slug
  - description
  - price
  - compare_price
  - status
  - is_featured
computed:
  - name: on_sale
    method: "object.on_sale?"
  - name: discount_percentage
    method: "object.discount_percentage"
  - name: created_at
    method: "object.created_at.iso8601"
relationships:
  - name: category
    serializer: CategorySerializer
  - name: tags
    serializer: TagSerializer
    type: has_many
conditional:
  - name: metadata
    condition: "params[:current_user]&.admin?"
links: true
```

## Generated Code - JSON:API Serializer

```ruby
# app/serializers/{{model_name_lower}}_serializer.rb
class {{ModelName}}Serializer
  include JSONAPI::Serializer

  set_type :{{model_name_lower}}
  set_id :id

  # Basic attributes
  attributes :name,
             :slug,
             :description,
             :price,
             :compare_price,
             :status,
             :is_featured

  # Computed attributes
  attribute :on_sale do |object|
    object.on_sale?
  end

  attribute :discount_percentage do |object|
    object.discount_percentage
  end

  attribute :created_at do |object|
    object.created_at.iso8601
  end

  attribute :updated_at do |object|
    object.updated_at.iso8601
  end

  # Relationships
  belongs_to :category, serializer: CategorySerializer
  belongs_to :user, serializer: UserSerializer, id_method_name: :created_by_id
  has_many :tags, serializer: TagSerializer

  # Conditional attributes (admin only)
  attribute :metadata, if: proc { |record, params|
    params[:current_user]&.admin?
  }

  attribute :internal_notes, if: proc { |record, params|
    params[:current_user]&.admin?
  }

  # Links
  link :self do |object|
    Rails.application.routes.url_helpers.api_v1_{{model_name_lower}}_path(object)
  end

  link :category do |object|
    Rails.application.routes.url_helpers.api_v1_category_path(object.category) if object.category
  end
end
```

## Generated Code - Blueprinter

```ruby
# app/blueprints/{{model_name_lower}}_blueprint.rb
class {{ModelName}}Blueprint < Blueprinter::Base
  identifier :id

  # Basic fields
  fields :name,
         :slug,
         :description,
         :price,
         :compare_price,
         :status,
         :is_featured

  # Computed fields
  field :on_sale do |{{model_name_lower}}|
    {{model_name_lower}}.on_sale?
  end

  field :discount_percentage do |{{model_name_lower}}|
    {{model_name_lower}}.discount_percentage
  end

  field :created_at do |{{model_name_lower}}|
    {{model_name_lower}}.created_at.iso8601
  end

  field :updated_at do |{{model_name_lower}}|
    {{model_name_lower}}.updated_at.iso8601
  end

  # Associations
  association :category, blueprint: CategoryBlueprint
  association :tags, blueprint: TagBlueprint

  # Views
  view :minimal do
    fields :name, :slug, :price
  end

  view :extended do
    include_view :default
    association :user, blueprint: UserBlueprint, name: :created_by
    field :metadata
    field :internal_notes
  end

  view :with_orders do
    include_view :default
    association :order_items, blueprint: OrderItemBlueprint
  end
end
```

## Collection Serialization

```ruby
# Controller usage - JSON:API
render json: ProductSerializer.new(
  @products,
  {
    include: [:category, :tags],
    params: { current_user: current_user },
    meta: {
      total: @products.total_count,
      pages: @products.total_pages,
      page: @products.current_page
    },
    links: {
      self: api_v1_products_url(page: @products.current_page),
      next: @products.next_page ? api_v1_products_url(page: @products.next_page) : nil,
      prev: @products.prev_page ? api_v1_products_url(page: @products.prev_page) : nil
    }
  }
)

# Controller usage - Blueprinter
render json: ProductBlueprint.render(
  @products,
  view: :extended,
  root: :data,
  meta: {
    total: @products.total_count,
    pages: @products.total_pages
  }
)
```

## Related Files Generated

1. `app/serializers/{{model_name_lower}}_serializer.rb` - JSON:API serializer
2. `app/blueprints/{{model_name_lower}}_blueprint.rb` - Blueprinter (if chosen)
3. `spec/serializers/{{model_name_lower}}_serializer_spec.rb` - Serializer specs

## Best Practices Applied

- Use consistent serialization format across API
- Include only necessary data (minimize payload)
- Use computed attributes for derived values
- Format dates as ISO8601
- Support conditional attributes for role-based data
- Include pagination metadata for collections
- Use views for different contexts
