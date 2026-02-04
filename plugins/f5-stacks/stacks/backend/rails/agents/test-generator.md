# Rails Test Generator Agent

Agent for generating RSpec tests for Rails applications.

## Capabilities

- Generate model specs with validations and associations
- Generate request specs for API endpoints
- Generate service specs with mocking
- Generate factory definitions
- Generate shared examples

## Input Schema

```yaml
test_type: string        # "model", "request", "service", "job"
target: string          # Class or endpoint to test
factory: boolean        # Generate factory (default: true)
shared_examples: array  # Shared examples to use
coverage_focus: array   # Areas to focus testing on
```

## Test Types

### Model Spec

```yaml
test_type: model
target: Product
coverage_focus:
  - validations
  - associations
  - scopes
  - callbacks
  - instance_methods
```

### Request Spec

```yaml
test_type: request
target: Api::V1::ProductsController
coverage_focus:
  - authentication
  - authorization
  - success_cases
  - error_cases
  - pagination
```

### Service Spec

```yaml
test_type: service
target: Orders::ProcessOrder
coverage_focus:
  - success_path
  - failure_cases
  - side_effects
  - error_handling
```

## Generated Model Spec

```ruby
# spec/models/{{model_name_lower}}_spec.rb
require 'rails_helper'

RSpec.describe {{ModelName}}, type: :model do
  describe 'factory' do
    it 'has a valid factory' do
      expect(build(:{{model_name_lower}})).to be_valid
    end
  end

  describe 'associations' do
    it { is_expected.to belong_to(:category) }
    it { is_expected.to belong_to(:user).with_foreign_key(:created_by_id) }
    it { is_expected.to have_many(:order_items).dependent(:restrict_with_error) }
    it { is_expected.to have_many(:orders).through(:order_items) }
    it { is_expected.to have_and_belong_to_many(:tags) }
  end

  describe 'validations' do
    subject { build(:{{model_name_lower}}) }

    it { is_expected.to validate_presence_of(:name) }
    it { is_expected.to validate_length_of(:name).is_at_most(255) }
    it { is_expected.to validate_presence_of(:price) }
    it { is_expected.to validate_numericality_of(:price).is_greater_than_or_equal_to(0) }
    it { is_expected.to validate_uniqueness_of(:slug) }

    context 'compare_price validation' do
      it 'allows compare_price greater than price' do
        {{model_name_lower}} = build(:{{model_name_lower}}, price: 100, compare_price: 150)
        expect({{model_name_lower}}).to be_valid
      end

      it 'does not allow compare_price less than price' do
        {{model_name_lower}} = build(:{{model_name_lower}}, price: 100, compare_price: 50)
        expect({{model_name_lower}}).not_to be_valid
        expect({{model_name_lower}}.errors[:compare_price]).to be_present
      end
    end
  end

  describe 'enums' do
    it { is_expected.to define_enum_for(:status).with_values(draft: 'draft', active: 'active', inactive: 'inactive', archived: 'archived').with_prefix }
  end

  describe 'scopes' do
    describe '.active' do
      it 'returns only active {{model_name_lower}}s' do
        active = create(:{{model_name_lower}}, status: :active)
        draft = create(:{{model_name_lower}}, status: :draft)

        expect(described_class.active).to include(active)
        expect(described_class.active).not_to include(draft)
      end
    end

    describe '.featured' do
      it 'returns only featured {{model_name_lower}}s' do
        featured = create(:{{model_name_lower}}, is_featured: true)
        regular = create(:{{model_name_lower}}, is_featured: false)

        expect(described_class.featured).to include(featured)
        expect(described_class.featured).not_to include(regular)
      end
    end

    describe '.search' do
      it 'searches by name' do
        matching = create(:{{model_name_lower}}, name: 'Special Product')
        other = create(:{{model_name_lower}}, name: 'Regular Item')

        expect(described_class.search('Special')).to include(matching)
        expect(described_class.search('Special')).not_to include(other)
      end
    end
  end

  describe 'callbacks' do
    describe 'before_validation' do
      it 'generates slug from name' do
        {{model_name_lower}} = build(:{{model_name_lower}}, name: 'Test Product', slug: nil)
        {{model_name_lower}}.valid?
        expect({{model_name_lower}}.slug).to eq('test-product')
      end
    end
  end

  describe 'instance methods' do
    describe '#on_sale?' do
      it 'returns true when compare_price is greater than price' do
        {{model_name_lower}} = build(:{{model_name_lower}}, price: 100, compare_price: 150)
        expect({{model_name_lower}}.on_sale?).to be true
      end

      it 'returns false when compare_price is nil' do
        {{model_name_lower}} = build(:{{model_name_lower}}, price: 100, compare_price: nil)
        expect({{model_name_lower}}.on_sale?).to be false
      end
    end

    describe '#discount_percentage' do
      it 'calculates discount percentage' do
        {{model_name_lower}} = build(:{{model_name_lower}}, price: 75, compare_price: 100)
        expect({{model_name_lower}}.discount_percentage).to eq(25)
      end
    end

    describe '#publish!' do
      it 'publishes a draft {{model_name_lower}}' do
        {{model_name_lower}} = create(:{{model_name_lower}}, status: :draft)

        expect { {{model_name_lower}}.publish! }
          .to change { {{model_name_lower}}.status }
          .from('draft')
          .to('active')
      end

      it 'raises error for non-draft {{model_name_lower}}' do
        {{model_name_lower}} = create(:{{model_name_lower}}, status: :active)

        expect { {{model_name_lower}}.publish! }.to raise_error(StandardError)
      end
    end
  end
end
```

## Generated Request Spec

```ruby
# spec/requests/api/v1/{{entities}}_spec.rb
require 'rails_helper'

RSpec.describe 'Api::V1::{{Entities}}', type: :request do
  let(:user) { create(:user) }
  let(:admin) { create(:user, :admin) }
  let(:headers) { auth_headers(user) }
  let(:admin_headers) { auth_headers(admin) }

  let(:category) { create(:category) }
  let(:{{entity}}) { create(:{{entity}}, category: category, created_by: user) }

  describe 'GET /api/v1/{{entities}}' do
    before { create_list(:{{entity}}, 5, status: :active) }

    context 'when authenticated' do
      it 'returns paginated {{entities}}' do
        get '/api/v1/{{entities}}', headers: headers

        expect(response).to have_http_status(:ok)
        expect(json_response['data'].size).to eq(5)
        expect(json_response['meta']).to include('total', 'pages')
      end

      it 'filters by status' do
        create(:{{entity}}, status: :draft)

        get '/api/v1/{{entities}}', params: { status: 'active' }, headers: headers

        expect(response).to have_http_status(:ok)
        statuses = json_response['data'].pluck('attributes', 'status').flatten
        expect(statuses).to all(eq('active'))
      end

      it 'paginates results' do
        get '/api/v1/{{entities}}', params: { page: 1, per_page: 2 }, headers: headers

        expect(response).to have_http_status(:ok)
        expect(json_response['data'].size).to eq(2)
        expect(json_response['meta']['pages']).to eq(3)
      end
    end

    context 'when unauthenticated' do
      it 'returns unauthorized' do
        get '/api/v1/{{entities}}'

        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'GET /api/v1/{{entities}}/:id' do
    it 'returns the {{entity}}' do
      get "/api/v1/{{entities}}/#{{{entity}}.id}", headers: headers

      expect(response).to have_http_status(:ok)
      expect(json_response['data']['id']).to eq({{entity}}.id)
      expect(json_response['data']['attributes']['name']).to eq({{entity}}.name)
    end

    it 'includes relationships' do
      get "/api/v1/{{entities}}/#{{{entity}}.id}", headers: headers

      expect(json_response['data']['relationships']).to include('category')
    end

    it 'returns not found for invalid id' do
      get '/api/v1/{{entities}}/invalid-id', headers: headers

      expect(response).to have_http_status(:not_found)
    end
  end

  describe 'POST /api/v1/{{entities}}' do
    let(:valid_params) do
      {
        {{entity}}: {
          name: 'New {{Entity}}',
          description: 'Description',
          price: 99.99,
          category_id: category.id
        }
      }
    end

    context 'with valid params' do
      it 'creates a {{entity}}' do
        expect {
          post '/api/v1/{{entities}}', params: valid_params, headers: headers
        }.to change({{Entity}}, :count).by(1)

        expect(response).to have_http_status(:created)
      end

      it 'returns the created {{entity}}' do
        post '/api/v1/{{entities}}', params: valid_params, headers: headers

        expect(json_response['data']['attributes']['name']).to eq('New {{Entity}}')
      end
    end

    context 'with invalid params' do
      let(:invalid_params) { { {{entity}}: { name: '' } } }

      it 'does not create a {{entity}}' do
        expect {
          post '/api/v1/{{entities}}', params: invalid_params, headers: headers
        }.not_to change({{Entity}}, :count)
      end

      it 'returns validation errors' do
        post '/api/v1/{{entities}}', params: invalid_params, headers: headers

        expect(response).to have_http_status(:unprocessable_entity)
        expect(json_response['errors']).to be_present
      end
    end
  end

  describe 'PATCH /api/v1/{{entities}}/:id' do
    let(:update_params) { { {{entity}}: { name: 'Updated Name' } } }

    context 'as owner' do
      it 'updates the {{entity}}' do
        patch "/api/v1/{{entities}}/#{{{entity}}.id}", params: update_params, headers: headers

        expect(response).to have_http_status(:ok)
        expect({{entity}}.reload.name).to eq('Updated Name')
      end
    end

    context 'as non-owner' do
      let(:other_user) { create(:user) }
      let(:other_headers) { auth_headers(other_user) }

      it 'returns forbidden' do
        patch "/api/v1/{{entities}}/#{{{entity}}.id}", params: update_params, headers: other_headers

        expect(response).to have_http_status(:forbidden)
      end
    end
  end

  describe 'DELETE /api/v1/{{entities}}/:id' do
    it 'deletes the {{entity}}' do
      {{entity}} # create

      expect {
        delete "/api/v1/{{entities}}/#{{{entity}}.id}", headers: headers
      }.to change({{Entity}}, :count).by(-1)

      expect(response).to have_http_status(:no_content)
    end

    context 'with associated orders' do
      before { create(:order_item, {{entity}}: {{entity}}) }

      it 'returns unprocessable entity' do
        delete "/api/v1/{{entities}}/#{{{entity}}.id}", headers: headers

        expect(response).to have_http_status(:unprocessable_entity)
      end
    end
  end
end
```

## Generated Factory

```ruby
# spec/factories/{{entities}}.rb
FactoryBot.define do
  factory :{{entity}} do
    name { Faker::Commerce.product_name }
    description { Faker::Lorem.paragraph }
    price { Faker::Commerce.price(range: 10..1000) }
    slug { name.parameterize }
    status { :active }
    is_featured { false }

    association :category
    association :created_by, factory: :user

    trait :draft do
      status { :draft }
    end

    trait :inactive do
      status { :inactive }
    end

    trait :archived do
      status { :archived }
    end

    trait :featured do
      is_featured { true }
    end

    trait :on_sale do
      compare_price { price * 1.5 }
    end

    trait :with_tags do
      after(:create) do |{{entity}}|
        {{entity}}.tags = create_list(:tag, 3)
      end
    end

    trait :with_orders do
      after(:create) do |{{entity}}|
        create_list(:order_item, 3, {{entity}}: {{entity}})
      end
    end
  end
end
```

## Test Support Helpers

```ruby
# spec/support/auth_helpers.rb
module AuthHelpers
  def auth_headers(user)
    token = Warden::JWTAuth::UserEncoder.new.call(user, :user, nil).first
    { 'Authorization' => "Bearer #{token}" }
  end

  def json_response
    JSON.parse(response.body)
  end
end

RSpec.configure do |config|
  config.include AuthHelpers, type: :request
end
```

## Related Files Generated

1. `spec/models/{{model_name_lower}}_spec.rb` - Model specs
2. `spec/requests/api/v1/{{entities}}_spec.rb` - Request specs
3. `spec/services/{{domain_lower}}/{{action_lower}}_spec.rb` - Service specs
4. `spec/factories/{{entities}}.rb` - Factories
5. `spec/support/auth_helpers.rb` - Test helpers

## Best Practices Applied

- Use factories over fixtures
- Test behavior, not implementation
- Use shoulda-matchers for one-liners
- Write request specs over controller specs
- Test happy path and edge cases
- Use shared examples for common patterns
- Keep factories minimal with traits
