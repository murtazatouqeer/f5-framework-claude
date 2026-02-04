# Rails Controller Template

## API Controller Template

```ruby
# app/controllers/api/v1/{{resource_plural}}_controller.rb
module Api
  module V1
    class {{ResourcePlural}}Controller < BaseController
      before_action :set_{{resource}}, only: [:show, :update, :destroy]

      # GET /api/v1/{{resource_plural}}
      def index
        @{{resource_plural}} = policy_scope({{Resource}})
          .includes({{INCLUDES}})
          .page(params[:page])
          .per(params[:per_page] || 20)

        render json: {{Resource}}Serializer.new(
          @{{resource_plural}},
          meta: pagination_meta(@{{resource_plural}})
        )
      end

      # GET /api/v1/{{resource_plural}}/:id
      def show
        authorize @{{resource}}

        render json: {{Resource}}Serializer.new(
          @{{resource}},
          include: [:{{RELATIONSHIPS}}]
        )
      end

      # POST /api/v1/{{resource_plural}}
      def create
        @{{resource}} = {{Resource}}.new({{resource}}_params)
        @{{resource}}.created_by = current_user

        authorize @{{resource}}

        if @{{resource}}.save
          render json: {{Resource}}Serializer.new(@{{resource}}), status: :created
        else
          render json: { errors: @{{resource}}.errors.full_messages }, status: :unprocessable_entity
        end
      end

      # PATCH/PUT /api/v1/{{resource_plural}}/:id
      def update
        authorize @{{resource}}

        if @{{resource}}.update({{resource}}_params)
          render json: {{Resource}}Serializer.new(@{{resource}})
        else
          render json: { errors: @{{resource}}.errors.full_messages }, status: :unprocessable_entity
        end
      end

      # DELETE /api/v1/{{resource_plural}}/:id
      def destroy
        authorize @{{resource}}

        @{{resource}}.destroy!
        head :no_content
      end

      private

      def set_{{resource}}
        @{{resource}} = {{Resource}}.find(params[:id])
      end

      def {{resource}}_params
        params.require(:{{resource}}).permit({{PERMITTED_PARAMS}})
      end

      def pagination_meta(collection)
        {
          current_page: collection.current_page,
          total_pages: collection.total_pages,
          total_count: collection.total_count,
          per_page: collection.limit_value
        }
      end
    end
  end
end
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{resource}}` | Singular resource name (snake_case) | `product` |
| `{{resource_plural}}` | Plural resource name (snake_case) | `products` |
| `{{Resource}}` | Singular resource class (PascalCase) | `Product` |
| `{{ResourcePlural}}` | Plural resource class (PascalCase) | `Products` |
| `{{INCLUDES}}` | Associations to include | `:category, :tags` |
| `{{RELATIONSHIPS}}` | Serializer relationships | `category, tags` |
| `{{PERMITTED_PARAMS}}` | Permitted params | `:name, :description, :price` |

## Usage Example

For a `Product` resource:

```ruby
# app/controllers/api/v1/products_controller.rb
module Api
  module V1
    class ProductsController < BaseController
      before_action :set_product, only: [:show, :update, :destroy]

      def index
        @products = policy_scope(Product)
          .includes(:category, :tags)
          .page(params[:page])
          .per(params[:per_page] || 20)

        render json: ProductSerializer.new(
          @products,
          meta: pagination_meta(@products)
        )
      end

      def show
        authorize @product

        render json: ProductSerializer.new(
          @product,
          include: [:category, :tags, :reviews]
        )
      end

      def create
        @product = Product.new(product_params)
        @product.created_by = current_user

        authorize @product

        if @product.save
          render json: ProductSerializer.new(@product), status: :created
        else
          render json: { errors: @product.errors.full_messages }, status: :unprocessable_entity
        end
      end

      def update
        authorize @product

        if @product.update(product_params)
          render json: ProductSerializer.new(@product)
        else
          render json: { errors: @product.errors.full_messages }, status: :unprocessable_entity
        end
      end

      def destroy
        authorize @product

        @product.destroy!
        head :no_content
      end

      private

      def set_product
        @product = Product.find(params[:id])
      end

      def product_params
        params.require(:product).permit(:name, :description, :price, :category_id, tag_ids: [])
      end

      def pagination_meta(collection)
        {
          current_page: collection.current_page,
          total_pages: collection.total_pages,
          total_count: collection.total_count,
          per_page: collection.limit_value
        }
      end
    end
  end
end
```

## With Custom Actions

```ruby
# Additional custom actions
def publish
  authorize @{{resource}}, :publish?

  if @{{resource}}.publish!
    render json: {{Resource}}Serializer.new(@{{resource}})
  else
    render json: { error: 'Cannot publish' }, status: :unprocessable_entity
  end
end

def archive
  authorize @{{resource}}, :archive?

  @{{resource}}.archive!
  render json: {{Resource}}Serializer.new(@{{resource}})
end
```

## With Filtering

```ruby
def index
  @{{resource_plural}} = policy_scope({{Resource}})
  @{{resource_plural}} = @{{resource_plural}}.where(status: params[:status]) if params[:status].present?
  @{{resource_plural}} = @{{resource_plural}}.where(category_id: params[:category_id]) if params[:category_id].present?
  @{{resource_plural}} = @{{resource_plural}}.search(params[:q]) if params[:q].present?
  @{{resource_plural}} = @{{resource_plural}}.includes(:category, :tags).page(params[:page])

  render json: {{Resource}}Serializer.new(@{{resource_plural}}, meta: pagination_meta(@{{resource_plural}}))
end
```
