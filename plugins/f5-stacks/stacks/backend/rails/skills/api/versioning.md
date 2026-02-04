# Rails API Versioning

Strategies for versioning Rails APIs.

## URL Path Versioning (Recommended)

### Routes Setup

```ruby
# config/routes.rb
Rails.application.routes.draw do
  namespace :api do
    namespace :v1 do
      resources :products
      resources :users
      resources :orders
    end

    namespace :v2 do
      resources :products
      resources :users
      resources :orders
    end
  end
end
```

### Controller Structure

```
app/controllers/
├── api/
│   ├── v1/
│   │   ├── base_controller.rb
│   │   ├── products_controller.rb
│   │   └── users_controller.rb
│   └── v2/
│       ├── base_controller.rb
│       ├── products_controller.rb
│       └── users_controller.rb
```

### Base Controller per Version

```ruby
# app/controllers/api/v1/base_controller.rb
module Api
  module V1
    class BaseController < ApplicationController
      before_action :authenticate_user!

      private

      def api_version
        'v1'
      end
    end
  end
end

# app/controllers/api/v2/base_controller.rb
module Api
  module V2
    class BaseController < ApplicationController
      before_action :authenticate_user!

      private

      def api_version
        'v2'
      end
    end
  end
end
```

### Version-Specific Controllers

```ruby
# app/controllers/api/v1/products_controller.rb
module Api
  module V1
    class ProductsController < BaseController
      def index
        @products = Product.active.page(params[:page])
        render json: V1::ProductSerializer.new(@products)
      end

      def show
        @product = Product.find(params[:id])
        render json: V1::ProductSerializer.new(@product)
      end
    end
  end
end

# app/controllers/api/v2/products_controller.rb
module Api
  module V2
    class ProductsController < BaseController
      def index
        @products = Product.active.includes(:category, :tags).page(params[:page])
        # V2 returns more data by default
        render json: V2::ProductSerializer.new(@products, include: [:category, :tags])
      end

      def show
        @product = Product.find(params[:id])
        render json: V2::ProductSerializer.new(@product, include: [:category, :tags, :reviews])
      end
    end
  end
end
```

### Version-Specific Serializers

```ruby
# app/serializers/v1/product_serializer.rb
module V1
  class ProductSerializer
    include JSONAPI::Serializer

    attributes :name, :price, :status
    belongs_to :category, serializer: V1::CategorySerializer
  end
end

# app/serializers/v2/product_serializer.rb
module V2
  class ProductSerializer
    include JSONAPI::Serializer

    attributes :name, :slug, :description, :price, :compare_price, :status

    attribute :on_sale do |product|
      product.on_sale?
    end

    attribute :discount_percentage do |product|
      product.discount_percentage
    end

    belongs_to :category, serializer: V2::CategorySerializer
    has_many :tags, serializer: V2::TagSerializer
    has_many :reviews, serializer: V2::ReviewSerializer
  end
end
```

## Header-Based Versioning

### Custom Constraint

```ruby
# lib/api_version.rb
class ApiVersion
  def initialize(version)
    @version = version
  end

  def matches?(request)
    versioned_accept_header?(request) || default_version?(request)
  end

  private

  def versioned_accept_header?(request)
    accept_header = request.headers['Accept']
    accept_header&.include?("application/vnd.myapp.v#{@version}+json")
  end

  def default_version?(request)
    @version == Rails.configuration.x.default_api_version &&
      !request.headers['Accept']&.match?(/application\/vnd\.myapp\.v\d/)
  end
end

# config/application.rb
config.x.default_api_version = 1
```

### Routes with Header Constraint

```ruby
# config/routes.rb
Rails.application.routes.draw do
  namespace :api do
    scope module: :v2, constraints: ApiVersion.new(2) do
      resources :products
      resources :users
    end

    scope module: :v1, constraints: ApiVersion.new(1) do
      resources :products
      resources :users
    end
  end
end
```

### Client Request

```bash
# V1 (default)
curl -H "Accept: application/json" https://api.example.com/api/products

# V2 (explicit)
curl -H "Accept: application/vnd.myapp.v2+json" https://api.example.com/api/products
```

## Query Parameter Versioning

```ruby
# config/routes.rb
Rails.application.routes.draw do
  namespace :api do
    scope module: :v2, constraints: ->(req) { req.params[:version] == '2' } do
      resources :products
    end

    scope module: :v1 do
      resources :products
    end
  end
end

# Usage: GET /api/products?version=2
```

## Shared Code Between Versions

### Module Extraction

```ruby
# app/controllers/api/shared/products_concern.rb
module Api
  module Shared
    module ProductsConcern
      extend ActiveSupport::Concern

      included do
        before_action :set_product, only: [:show, :update, :destroy]
      end

      private

      def set_product
        @product = Product.find(params[:id])
      end

      def product_params
        params.require(:product).permit(:name, :description, :price, :category_id)
      end
    end
  end
end

# app/controllers/api/v1/products_controller.rb
module Api
  module V1
    class ProductsController < BaseController
      include Api::Shared::ProductsConcern

      def index
        # V1-specific implementation
      end
    end
  end
end
```

### Inheritance Pattern

```ruby
# app/controllers/api/base_products_controller.rb
module Api
  class BaseProductsController < ApplicationController
    before_action :set_product, only: [:show, :update, :destroy]

    def create
      @product = Product.new(product_params)
      @product.created_by = current_user

      if @product.save
        render_product(@product, status: :created)
      else
        render json: { errors: @product.errors }, status: :unprocessable_entity
      end
    end

    protected

    def render_product(product, options = {})
      raise NotImplementedError
    end

    private

    def set_product
      @product = Product.find(params[:id])
    end

    def product_params
      params.require(:product).permit(:name, :description, :price)
    end
  end
end

# app/controllers/api/v1/products_controller.rb
module Api
  module V1
    class ProductsController < Api::BaseProductsController
      def render_product(product, options = {})
        render json: V1::ProductSerializer.new(product), **options
      end
    end
  end
end
```

## Deprecation Strategy

```ruby
# app/controllers/api/v1/base_controller.rb
module Api
  module V1
    class BaseController < ApplicationController
      before_action :add_deprecation_warning

      private

      def add_deprecation_warning
        response.headers['X-Api-Deprecation'] = 'This API version is deprecated. Please migrate to v2.'
        response.headers['X-Api-Sunset'] = '2025-06-01'
      end
    end
  end
end

# For more control
module ApiDeprecation
  extend ActiveSupport::Concern

  included do
    after_action :add_deprecation_headers
  end

  private

  def add_deprecation_headers
    deprecation = api_deprecation_info
    return unless deprecation

    response.headers['Deprecation'] = deprecation[:date].httpdate
    response.headers['Sunset'] = deprecation[:sunset].httpdate
    response.headers['Link'] = "<#{deprecation[:migration_guide]}>; rel=\"deprecation\""
  end

  def api_deprecation_info
    # Override in specific controllers
    nil
  end
end
```

## Version Documentation

```ruby
# app/controllers/api/v1/docs_controller.rb
module Api
  module V1
    class DocsController < BaseController
      skip_before_action :authenticate_user!

      def index
        render json: {
          version: 'v1',
          status: 'deprecated',
          sunset_date: '2025-06-01',
          migration_guide: 'https://api.example.com/docs/migration/v1-to-v2',
          endpoints: [
            { path: '/api/v1/products', methods: ['GET', 'POST'] },
            { path: '/api/v1/products/:id', methods: ['GET', 'PATCH', 'DELETE'] }
          ]
        }
      end
    end
  end
end
```

## Testing Multiple Versions

```ruby
# spec/requests/api/v1/products_spec.rb
RSpec.describe 'Api::V1::Products', type: :request do
  describe 'GET /api/v1/products' do
    it 'returns v1 format' do
      product = create(:product)
      get '/api/v1/products', headers: auth_headers

      expect(response).to have_http_status(:ok)
      expect(json_response['data'].first['attributes'].keys).not_to include('slug')
    end
  end
end

# spec/requests/api/v2/products_spec.rb
RSpec.describe 'Api::V2::Products', type: :request do
  describe 'GET /api/v2/products' do
    it 'returns v2 format with more fields' do
      product = create(:product)
      get '/api/v2/products', headers: auth_headers

      expect(response).to have_http_status(:ok)
      expect(json_response['data'].first['attributes'].keys).to include('slug', 'on_sale')
    end
  end
end
```

## Best Practices

1. **Start with versioning** - Add it from day one
2. **Use URL path versioning** - Most explicit and cacheable
3. **Keep old versions minimal** - Only bug fixes, no new features
4. **Document migration paths** - Help clients upgrade
5. **Set sunset dates** - Communicate deprecation timeline
6. **Share code wisely** - Extract common logic, keep version-specific separate
7. **Test all versions** - Ensure backwards compatibility
8. **Version serializers too** - Response format may change between versions
