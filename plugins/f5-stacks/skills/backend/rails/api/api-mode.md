# Rails API Mode

Building JSON APIs with Rails API-only applications.

## Creating API-Only Application

```bash
# New API-only application
rails new myapp --api

# With specific options
rails new myapp --api -d postgresql -T  # PostgreSQL, skip test-unit
```

## Configuration

```ruby
# config/application.rb
module MyApp
  class Application < Rails::Application
    config.load_defaults 7.1

    # API-only mode
    config.api_only = true

    # Enable cookies if needed (for session-based auth)
    # config.middleware.use ActionDispatch::Cookies
    # config.middleware.use ActionDispatch::Session::CookieStore

    # Configure allowed hosts
    config.hosts << 'api.myapp.com'
    config.hosts << /.*\.myapp\.com/

    # Configure CORS (with rack-cors gem)
    config.middleware.insert_before 0, Rack::Cors do
      allow do
        origins '*'
        resource '*',
          headers: :any,
          methods: [:get, :post, :put, :patch, :delete, :options, :head],
          expose: ['Authorization']
      end
    end

    # Custom middleware
    config.middleware.use Rack::Attack

    # Time zone
    config.time_zone = 'UTC'
    config.active_record.default_timezone = :utc
  end
end
```

## Application Controller

```ruby
# app/controllers/application_controller.rb
class ApplicationController < ActionController::API
  include ActionController::MimeResponds
  include Pundit::Authorization

  # Error handling
  rescue_from StandardError, with: :handle_internal_error
  rescue_from ActiveRecord::RecordNotFound, with: :handle_not_found
  rescue_from ActiveRecord::RecordInvalid, with: :handle_validation_error
  rescue_from Pundit::NotAuthorizedError, with: :handle_forbidden
  rescue_from ActionController::ParameterMissing, with: :handle_bad_request

  private

  def handle_internal_error(error)
    log_error(error)
    render json: { error: 'Internal server error' }, status: :internal_server_error
  end

  def handle_not_found(error)
    render json: { error: 'Resource not found' }, status: :not_found
  end

  def handle_validation_error(error)
    render json: {
      error: 'Validation failed',
      details: error.record.errors.full_messages
    }, status: :unprocessable_entity
  end

  def handle_forbidden(error)
    render json: { error: 'Not authorized' }, status: :forbidden
  end

  def handle_bad_request(error)
    render json: { error: "Missing parameter: #{error.param}" }, status: :bad_request
  end

  def log_error(error)
    Rails.logger.error("#{error.class}: #{error.message}")
    Rails.logger.error(error.backtrace.first(10).join("\n"))
    Sentry.capture_exception(error) if defined?(Sentry)
  end
end
```

## API Base Controller

```ruby
# app/controllers/api/v1/base_controller.rb
module Api
  module V1
    class BaseController < ApplicationController
      before_action :authenticate_user!
      before_action :set_default_format

      private

      def set_default_format
        request.format = :json
      end

      def current_user
        @current_user ||= authenticate_with_token
      end

      def authenticate_user!
        render json: { error: 'Unauthorized' }, status: :unauthorized unless current_user
      end

      def authenticate_with_token
        token = request.headers['Authorization']&.split(' ')&.last
        return nil unless token

        payload = JWT.decode(token, Rails.application.credentials.secret_key_base).first
        User.find_by(id: payload['user_id'])
      rescue JWT::DecodeError
        nil
      end

      # Pagination helpers
      def paginate(collection)
        collection.page(params[:page]).per(per_page)
      end

      def per_page
        [(params[:per_page] || 20).to_i, 100].min
      end

      def pagination_meta(collection)
        {
          meta: {
            current_page: collection.current_page,
            next_page: collection.next_page,
            prev_page: collection.prev_page,
            total_pages: collection.total_pages,
            total_count: collection.total_count
          }
        }
      end
    end
  end
end
```

## Resource Controller

```ruby
# app/controllers/api/v1/products_controller.rb
module Api
  module V1
    class ProductsController < BaseController
      before_action :set_product, only: [:show, :update, :destroy]

      # GET /api/v1/products
      def index
        @products = paginate(
          ProductsQuery.new(Product.active).call(filter_params)
        )

        render json: ProductSerializer.new(
          @products,
          pagination_meta(@products).merge(include: [:category])
        )
      end

      # GET /api/v1/products/:id
      def show
        render json: ProductSerializer.new(@product, include: [:category, :tags])
      end

      # POST /api/v1/products
      def create
        result = Products::CreateProduct.new(
          params: product_params,
          current_user: current_user
        ).call

        if result.success?
          render json: ProductSerializer.new(result.data), status: :created
        else
          render json: { errors: result.errors }, status: :unprocessable_entity
        end
      end

      # PATCH/PUT /api/v1/products/:id
      def update
        authorize @product

        result = Products::UpdateProduct.new(
          product: @product,
          params: product_params
        ).call

        if result.success?
          render json: ProductSerializer.new(result.data)
        else
          render json: { errors: result.errors }, status: :unprocessable_entity
        end
      end

      # DELETE /api/v1/products/:id
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
        params.require(:product).permit(
          :name, :description, :price, :compare_price,
          :category_id, :status, tag_ids: []
        )
      end

      def filter_params
        params.permit(:q, :status, :category_id, :min_price, :max_price, :sort_by, :sort_order)
      end
    end
  end
end
```

## Routes

```ruby
# config/routes.rb
Rails.application.routes.draw do
  # Health check endpoint
  get '/health', to: proc { [200, {}, ['OK']] }

  namespace :api do
    namespace :v1 do
      # Resources
      resources :products do
        resources :reviews, only: [:index, :create]
        collection do
          get :featured
          get :search
        end
        member do
          post :publish
          post :archive
        end
      end

      resources :categories, only: [:index, :show]
      resources :orders do
        member do
          post :confirm
          post :cancel
        end
      end

      # Auth routes (custom)
      post 'auth/login', to: 'auth#login'
      post 'auth/register', to: 'auth#register'
      delete 'auth/logout', to: 'auth#logout'
      post 'auth/refresh', to: 'auth#refresh'
      get 'auth/me', to: 'auth#me'
    end
  end
end
```

## JSON Response Format

### Success Response

```json
{
  "data": {
    "id": "uuid",
    "type": "product",
    "attributes": {
      "name": "Product Name",
      "price": 99.99,
      "status": "active"
    },
    "relationships": {
      "category": {
        "data": { "id": "uuid", "type": "category" }
      }
    }
  },
  "included": [
    {
      "id": "uuid",
      "type": "category",
      "attributes": { "name": "Category Name" }
    }
  ],
  "meta": {
    "current_page": 1,
    "total_pages": 10,
    "total_count": 100
  }
}
```

### Error Response

```json
{
  "error": "Validation failed",
  "details": [
    "Name can't be blank",
    "Price must be greater than 0"
  ]
}
```

## Request Specs

```ruby
# spec/requests/api/v1/products_spec.rb
RSpec.describe 'Api::V1::Products', type: :request do
  let(:user) { create(:user) }
  let(:headers) { auth_headers(user) }

  describe 'GET /api/v1/products' do
    before { create_list(:product, 5, status: :active) }

    it 'returns products' do
      get '/api/v1/products', headers: headers

      expect(response).to have_http_status(:ok)
      expect(json_response['data'].size).to eq(5)
    end

    it 'includes pagination meta' do
      get '/api/v1/products', headers: headers

      expect(json_response['meta']).to include(
        'current_page', 'total_pages', 'total_count'
      )
    end
  end
end
```

## Best Practices

1. **Use namespaces** for API versioning
2. **Return consistent JSON format** across all endpoints
3. **Include pagination meta** for collection responses
4. **Handle errors gracefully** with appropriate status codes
5. **Use serializers** for JSON formatting
6. **Implement proper authentication** (JWT, OAuth)
7. **Add rate limiting** with Rack::Attack
8. **Enable CORS** for cross-origin requests
9. **Document API** with OpenAPI/Swagger
