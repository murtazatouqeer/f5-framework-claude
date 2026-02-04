# Request Specs for Rails APIs

Integration testing patterns for Rails API endpoints.

## Setup

```ruby
# spec/support/request_helpers.rb
module RequestHelpers
  def json_response
    @json_response ||= JSON.parse(response.body, symbolize_names: true)
  end

  def json_data
    json_response[:data]
  end

  def json_errors
    json_response[:errors]
  end

  def json_meta
    json_response[:meta]
  end
end

# spec/support/auth_helpers.rb
module AuthHelpers
  def auth_headers_for(user)
    token = Warden::JWTAuth::UserEncoder.new.call(user, :user, nil).first
    { 'Authorization' => "Bearer #{token}" }
  end

  def auth_headers
    auth_headers_for(current_user)
  end
end

RSpec.configure do |config|
  config.include RequestHelpers, type: :request
  config.include AuthHelpers, type: :request
end
```

## Basic CRUD Specs

```ruby
# spec/requests/api/v1/products_spec.rb
RSpec.describe 'Api::V1::Products', type: :request do
  let(:current_user) { create(:user) }
  let(:headers) { auth_headers_for(current_user) }

  describe 'GET /api/v1/products' do
    let!(:products) { create_list(:product, 5) }

    it 'returns all products' do
      get '/api/v1/products', headers: headers

      expect(response).to have_http_status(:ok)
      expect(json_data.length).to eq(5)
    end

    it 'returns products in JSON:API format' do
      get '/api/v1/products', headers: headers

      expect(json_data.first).to include(:id, :type, :attributes)
      expect(json_data.first[:type]).to eq('product')
    end

    context 'with pagination' do
      let!(:products) { create_list(:product, 25) }

      it 'returns paginated results' do
        get '/api/v1/products', params: { page: 1, per_page: 10 }, headers: headers

        expect(json_data.length).to eq(10)
        expect(json_meta[:total_count]).to eq(25)
        expect(json_meta[:total_pages]).to eq(3)
      end
    end

    context 'with filtering' do
      let!(:active_products) { create_list(:product, 3, status: :active) }
      let!(:draft_products) { create_list(:product, 2, status: :draft) }

      it 'filters by status' do
        get '/api/v1/products', params: { status: 'active' }, headers: headers

        expect(json_data.length).to eq(3)
      end
    end

    context 'with sorting' do
      let!(:cheap_product) { create(:product, price: 10) }
      let!(:expensive_product) { create(:product, price: 100) }

      it 'sorts by price ascending' do
        get '/api/v1/products', params: { sort: 'price' }, headers: headers

        expect(json_data.first[:attributes][:price].to_f).to eq(10.0)
      end

      it 'sorts by price descending' do
        get '/api/v1/products', params: { sort: '-price' }, headers: headers

        expect(json_data.first[:attributes][:price].to_f).to eq(100.0)
      end
    end

    context 'without authentication' do
      it 'returns unauthorized' do
        get '/api/v1/products'

        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'GET /api/v1/products/:id' do
    let!(:product) { create(:product) }

    it 'returns the product' do
      get "/api/v1/products/#{product.id}", headers: headers

      expect(response).to have_http_status(:ok)
      expect(json_data[:id]).to eq(product.id.to_s)
    end

    it 'includes relationships' do
      get "/api/v1/products/#{product.id}", params: { include: 'category' }, headers: headers

      expect(json_response[:included]).to be_present
    end

    context 'with non-existent product' do
      it 'returns not found' do
        get '/api/v1/products/999999', headers: headers

        expect(response).to have_http_status(:not_found)
        expect(json_response[:error]).to be_present
      end
    end
  end

  describe 'POST /api/v1/products' do
    let(:category) { create(:category) }
    let(:valid_params) do
      {
        product: {
          name: 'New Product',
          description: 'Product description',
          price: 29.99,
          category_id: category.id
        }
      }
    end

    context 'with valid params' do
      it 'creates a product' do
        expect {
          post '/api/v1/products', params: valid_params, headers: headers
        }.to change(Product, :count).by(1)

        expect(response).to have_http_status(:created)
      end

      it 'returns the created product' do
        post '/api/v1/products', params: valid_params, headers: headers

        expect(json_data[:attributes][:name]).to eq('New Product')
      end

      it 'sets the creator' do
        post '/api/v1/products', params: valid_params, headers: headers

        expect(Product.last.created_by).to eq(current_user)
      end
    end

    context 'with invalid params' do
      let(:invalid_params) { { product: { name: '' } } }

      it 'does not create a product' do
        expect {
          post '/api/v1/products', params: invalid_params, headers: headers
        }.not_to change(Product, :count)
      end

      it 'returns unprocessable entity' do
        post '/api/v1/products', params: invalid_params, headers: headers

        expect(response).to have_http_status(:unprocessable_entity)
      end

      it 'returns validation errors' do
        post '/api/v1/products', params: invalid_params, headers: headers

        expect(json_errors).to include("Name can't be blank")
      end
    end
  end

  describe 'PATCH /api/v1/products/:id' do
    let!(:product) { create(:product, created_by: current_user) }
    let(:update_params) { { product: { name: 'Updated Name' } } }

    context 'with valid params' do
      it 'updates the product' do
        patch "/api/v1/products/#{product.id}", params: update_params, headers: headers

        expect(response).to have_http_status(:ok)
        expect(product.reload.name).to eq('Updated Name')
      end
    end

    context 'with invalid params' do
      let(:invalid_params) { { product: { price: -10 } } }

      it 'returns unprocessable entity' do
        patch "/api/v1/products/#{product.id}", params: invalid_params, headers: headers

        expect(response).to have_http_status(:unprocessable_entity)
      end
    end

    context 'when not owner' do
      let!(:product) { create(:product) }  # Different owner

      it 'returns forbidden' do
        patch "/api/v1/products/#{product.id}", params: update_params, headers: headers

        expect(response).to have_http_status(:forbidden)
      end
    end
  end

  describe 'DELETE /api/v1/products/:id' do
    let!(:product) { create(:product, created_by: current_user) }

    it 'deletes the product' do
      expect {
        delete "/api/v1/products/#{product.id}", headers: headers
      }.to change(Product, :count).by(-1)

      expect(response).to have_http_status(:no_content)
    end

    context 'when not owner' do
      let!(:product) { create(:product) }

      it 'returns forbidden' do
        delete "/api/v1/products/#{product.id}", headers: headers

        expect(response).to have_http_status(:forbidden)
      end
    end
  end
end
```

## Authentication Specs

```ruby
# spec/requests/api/v1/auth/sessions_spec.rb
RSpec.describe 'Api::V1::Auth::Sessions', type: :request do
  describe 'POST /api/v1/auth/login' do
    let!(:user) { create(:user, email: 'test@example.com', password: 'password123') }

    context 'with valid credentials' do
      let(:params) do
        { user: { email: 'test@example.com', password: 'password123' } }
      end

      it 'returns success' do
        post '/api/v1/auth/login', params: params

        expect(response).to have_http_status(:ok)
      end

      it 'returns JWT token in header' do
        post '/api/v1/auth/login', params: params

        expect(response.headers['Authorization']).to start_with('Bearer ')
      end

      it 'returns user data' do
        post '/api/v1/auth/login', params: params

        expect(json_response[:user][:email]).to eq('test@example.com')
      end
    end

    context 'with invalid credentials' do
      let(:params) do
        { user: { email: 'test@example.com', password: 'wrong' } }
      end

      it 'returns unauthorized' do
        post '/api/v1/auth/login', params: params

        expect(response).to have_http_status(:unauthorized)
      end

      it 'returns error message' do
        post '/api/v1/auth/login', params: params

        expect(json_response[:error]).to be_present
      end
    end

    context 'with non-existent user' do
      let(:params) do
        { user: { email: 'unknown@example.com', password: 'password123' } }
      end

      it 'returns unauthorized' do
        post '/api/v1/auth/login', params: params

        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'DELETE /api/v1/auth/logout' do
    let(:user) { create(:user) }
    let(:headers) { auth_headers_for(user) }

    it 'logs out user' do
      delete '/api/v1/auth/logout', headers: headers

      expect(response).to have_http_status(:no_content)
    end

    it 'invalidates token' do
      delete '/api/v1/auth/logout', headers: headers

      # Try to use same token
      get '/api/v1/auth/me', headers: headers
      expect(response).to have_http_status(:unauthorized)
    end
  end
end

# spec/requests/api/v1/auth/registrations_spec.rb
RSpec.describe 'Api::V1::Auth::Registrations', type: :request do
  describe 'POST /api/v1/auth/register' do
    let(:valid_params) do
      {
        user: {
          email: 'new@example.com',
          password: 'password123',
          password_confirmation: 'password123',
          name: 'New User'
        }
      }
    end

    context 'with valid params' do
      it 'creates a user' do
        expect {
          post '/api/v1/auth/register', params: valid_params
        }.to change(User, :count).by(1)
      end

      it 'returns created status' do
        post '/api/v1/auth/register', params: valid_params

        expect(response).to have_http_status(:created)
      end

      it 'returns JWT token' do
        post '/api/v1/auth/register', params: valid_params

        expect(response.headers['Authorization']).to be_present
      end
    end

    context 'with existing email' do
      before { create(:user, email: 'new@example.com') }

      it 'returns unprocessable entity' do
        post '/api/v1/auth/register', params: valid_params

        expect(response).to have_http_status(:unprocessable_entity)
      end

      it 'returns error' do
        post '/api/v1/auth/register', params: valid_params

        expect(json_response[:details]).to include('Email has already been taken')
      end
    end

    context 'with password mismatch' do
      let(:invalid_params) do
        valid_params.deep_merge(user: { password_confirmation: 'different' })
      end

      it 'returns unprocessable entity' do
        post '/api/v1/auth/register', params: invalid_params

        expect(response).to have_http_status(:unprocessable_entity)
      end
    end
  end
end
```

## Custom Action Specs

```ruby
# spec/requests/api/v1/products/publish_spec.rb
RSpec.describe 'Api::V1::Products#publish', type: :request do
  let(:current_user) { create(:user) }
  let(:headers) { auth_headers_for(current_user) }

  describe 'POST /api/v1/products/:id/publish' do
    context 'with draft product owned by user' do
      let!(:product) { create(:product, :draft, created_by: current_user) }

      it 'publishes the product' do
        post "/api/v1/products/#{product.id}/publish", headers: headers

        expect(response).to have_http_status(:ok)
        expect(product.reload).to be_active
      end

      it 'sets published_at timestamp' do
        freeze_time do
          post "/api/v1/products/#{product.id}/publish", headers: headers

          expect(product.reload.published_at).to eq(Time.current)
        end
      end
    end

    context 'with already published product' do
      let!(:product) { create(:product, :active, created_by: current_user) }

      it 'returns unprocessable entity' do
        post "/api/v1/products/#{product.id}/publish", headers: headers

        expect(response).to have_http_status(:unprocessable_entity)
        expect(json_response[:error]).to include('already published')
      end
    end

    context 'with product not owned by user' do
      let!(:product) { create(:product, :draft) }

      it 'returns forbidden' do
        post "/api/v1/products/#{product.id}/publish", headers: headers

        expect(response).to have_http_status(:forbidden)
      end
    end
  end
end
```

## Nested Resource Specs

```ruby
# spec/requests/api/v1/orders/items_spec.rb
RSpec.describe 'Api::V1::Orders::Items', type: :request do
  let(:current_user) { create(:user) }
  let(:headers) { auth_headers_for(current_user) }
  let!(:order) { create(:order, user: current_user) }

  describe 'GET /api/v1/orders/:order_id/items' do
    let!(:items) { create_list(:order_item, 3, order: order) }

    it 'returns order items' do
      get "/api/v1/orders/#{order.id}/items", headers: headers

      expect(response).to have_http_status(:ok)
      expect(json_data.length).to eq(3)
    end
  end

  describe 'POST /api/v1/orders/:order_id/items' do
    let(:product) { create(:product, price: 29.99) }
    let(:params) do
      { item: { product_id: product.id, quantity: 2 } }
    end

    context 'with pending order' do
      it 'adds item to order' do
        expect {
          post "/api/v1/orders/#{order.id}/items", params: params, headers: headers
        }.to change(order.items, :count).by(1)
      end

      it 'calculates subtotal' do
        post "/api/v1/orders/#{order.id}/items", params: params, headers: headers

        expect(json_data[:attributes][:subtotal].to_f).to eq(59.98)
      end
    end

    context 'with confirmed order' do
      let!(:order) { create(:order, :confirmed, user: current_user) }

      it 'returns unprocessable entity' do
        post "/api/v1/orders/#{order.id}/items", params: params, headers: headers

        expect(response).to have_http_status(:unprocessable_entity)
      end
    end
  end

  describe 'DELETE /api/v1/orders/:order_id/items/:id' do
    let!(:item) { create(:order_item, order: order) }

    it 'removes item from order' do
      expect {
        delete "/api/v1/orders/#{order.id}/items/#{item.id}", headers: headers
      }.to change(order.items, :count).by(-1)
    end
  end
end
```

## Error Handling Specs

```ruby
# spec/requests/api/v1/error_handling_spec.rb
RSpec.describe 'API Error Handling', type: :request do
  let(:current_user) { create(:user) }
  let(:headers) { auth_headers_for(current_user) }

  describe 'Record Not Found' do
    it 'returns 404 with message' do
      get '/api/v1/products/999999', headers: headers

      expect(response).to have_http_status(:not_found)
      expect(json_response[:error]).to eq('Record not found')
    end
  end

  describe 'Validation Errors' do
    it 'returns 422 with errors array' do
      post '/api/v1/products', params: { product: { name: '' } }, headers: headers

      expect(response).to have_http_status(:unprocessable_entity)
      expect(json_response[:errors]).to be_an(Array)
    end
  end

  describe 'Unauthorized Access' do
    it 'returns 401 without token' do
      get '/api/v1/products'

      expect(response).to have_http_status(:unauthorized)
      expect(json_response[:error]).to include('sign in')
    end

    it 'returns 401 with invalid token' do
      get '/api/v1/products', headers: { 'Authorization' => 'Bearer invalid' }

      expect(response).to have_http_status(:unauthorized)
    end
  end

  describe 'Forbidden Access' do
    let(:other_user_product) { create(:product) }

    it 'returns 403 for unauthorized actions' do
      delete "/api/v1/products/#{other_user_product.id}", headers: headers

      expect(response).to have_http_status(:forbidden)
      expect(json_response[:error]).to include('Not authorized')
    end
  end

  describe 'Internal Server Error' do
    before do
      allow(Product).to receive(:find).and_raise(StandardError, 'Something went wrong')
    end

    it 'returns 500 with generic message' do
      get '/api/v1/products/1', headers: headers

      expect(response).to have_http_status(:internal_server_error)
      expect(json_response[:error]).to eq('Internal server error')
    end
  end
end
```

## Rate Limiting Specs

```ruby
# spec/requests/api/v1/rate_limiting_spec.rb
RSpec.describe 'API Rate Limiting', type: :request do
  let(:current_user) { create(:user) }
  let(:headers) { auth_headers_for(current_user) }

  describe 'Login endpoint' do
    it 'allows 5 requests per minute' do
      5.times do
        post '/api/v1/auth/login', params: { user: { email: 'test@example.com', password: 'wrong' } }
      end

      post '/api/v1/auth/login', params: { user: { email: 'test@example.com', password: 'wrong' } }

      expect(response).to have_http_status(:too_many_requests)
      expect(json_response[:error]).to include('Rate limit')
    end
  end

  describe 'API endpoints' do
    it 'includes rate limit headers' do
      get '/api/v1/products', headers: headers

      expect(response.headers['X-RateLimit-Limit']).to be_present
      expect(response.headers['X-RateLimit-Remaining']).to be_present
    end
  end
end
```

## File Upload Specs

```ruby
# spec/requests/api/v1/products/images_spec.rb
RSpec.describe 'Api::V1::Products::Images', type: :request do
  let(:current_user) { create(:user) }
  let(:headers) { auth_headers_for(current_user) }
  let!(:product) { create(:product, created_by: current_user) }

  describe 'POST /api/v1/products/:id/images' do
    let(:image) { fixture_file_upload('spec/fixtures/test_image.png', 'image/png') }

    it 'uploads image' do
      expect {
        post "/api/v1/products/#{product.id}/images",
             params: { image: image },
             headers: headers
      }.to change(product.images, :count).by(1)

      expect(response).to have_http_status(:created)
    end

    it 'validates file type' do
      invalid_file = fixture_file_upload('spec/fixtures/test.txt', 'text/plain')

      post "/api/v1/products/#{product.id}/images",
           params: { image: invalid_file },
           headers: headers

      expect(response).to have_http_status(:unprocessable_entity)
    end

    it 'validates file size' do
      large_file = fixture_file_upload('spec/fixtures/large_image.png', 'image/png')

      post "/api/v1/products/#{product.id}/images",
           params: { image: large_file },
           headers: headers

      expect(response).to have_http_status(:unprocessable_entity)
    end
  end
end
```

## Versioned API Specs

```ruby
# spec/requests/api/v2/products_spec.rb
RSpec.describe 'Api::V2::Products', type: :request do
  let(:current_user) { create(:user) }
  let(:headers) { auth_headers_for(current_user) }

  describe 'GET /api/v2/products' do
    let!(:product) { create(:product, :with_tags, :with_category) }

    it 'includes additional fields' do
      get '/api/v2/products', headers: headers

      attributes = json_data.first[:attributes]
      expect(attributes).to include(:slug, :on_sale, :discount_percentage)
    end

    it 'includes relationships by default' do
      get '/api/v2/products', headers: headers

      expect(json_response[:included]).to be_present
    end
  end
end
```

## Best Practices

1. **Use let for test data** - Lazy evaluation, cleaner code
2. **Use shared contexts** - DRY authentication setup
3. **Test all response codes** - 200, 201, 401, 403, 404, 422
4. **Test edge cases** - Empty arrays, nil values, boundaries
5. **Use factories with traits** - Clear, readable test setup
6. **Group by endpoint** - describe blocks per action
7. **Test authorization** - Owner vs non-owner scenarios
8. **Include integration tests** - Full request/response cycle
