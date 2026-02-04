# RSpec Testing Patterns

Best practices and patterns for testing Rails applications with RSpec.

## Setup

```ruby
# Gemfile
group :development, :test do
  gem 'rspec-rails'
  gem 'factory_bot_rails'
  gem 'faker'
  gem 'shoulda-matchers'
end

group :test do
  gem 'database_cleaner-active_record'
  gem 'webmock'
  gem 'vcr'
  gem 'simplecov', require: false
end
```

### Installation

```bash
rails generate rspec:install
```

### Configuration

```ruby
# spec/rails_helper.rb
require 'spec_helper'
ENV['RAILS_ENV'] ||= 'test'
require_relative '../config/environment'

abort("The Rails environment is running in production mode!") if Rails.env.production?
require 'rspec/rails'

Dir[Rails.root.join('spec', 'support', '**', '*.rb')].sort.each { |f| require f }

begin
  ActiveRecord::Migration.maintain_test_schema!
rescue ActiveRecord::PendingMigrationError => e
  abort e.to_s.strip
end

RSpec.configure do |config|
  config.fixture_path = Rails.root.join('spec/fixtures')
  config.use_transactional_fixtures = true
  config.infer_spec_type_from_file_location!
  config.filter_rails_from_backtrace!

  # Include helpers
  config.include FactoryBot::Syntax::Methods
  config.include Devise::Test::IntegrationHelpers, type: :request
  config.include AuthHelpers, type: :request
end
```

## Model Specs

```ruby
# spec/models/user_spec.rb
RSpec.describe User, type: :model do
  describe 'validations' do
    subject { build(:user) }

    it { is_expected.to validate_presence_of(:email) }
    it { is_expected.to validate_uniqueness_of(:email).case_insensitive }
    it { is_expected.to validate_length_of(:name).is_at_most(100) }
    it { is_expected.to allow_value('user@example.com').for(:email) }
    it { is_expected.not_to allow_value('invalid').for(:email) }
  end

  describe 'associations' do
    it { is_expected.to have_many(:orders).dependent(:nullify) }
    it { is_expected.to have_one(:profile).dependent(:destroy) }
    it { is_expected.to belong_to(:organization).optional }
  end

  describe 'enums' do
    it { is_expected.to define_enum_for(:role).with_values(user: 'user', admin: 'admin') }
    it { is_expected.to define_enum_for(:status).with_values(active: 0, inactive: 1) }
  end

  describe 'scopes' do
    describe '.active' do
      let!(:active_user) { create(:user, status: :active) }
      let!(:inactive_user) { create(:user, status: :inactive) }

      it 'returns only active users' do
        expect(described_class.active).to contain_exactly(active_user)
      end
    end

    describe '.admins' do
      let!(:admin) { create(:user, :admin) }
      let!(:regular) { create(:user) }

      it 'returns only admins' do
        expect(described_class.admins).to contain_exactly(admin)
      end
    end
  end

  describe 'callbacks' do
    describe 'before_create' do
      it 'generates a UUID' do
        user = create(:user)
        expect(user.uuid).to be_present
        expect(user.uuid).to match(/\A[0-9a-f-]{36}\z/)
      end
    end

    describe 'after_create' do
      it 'sends welcome email' do
        expect {
          create(:user)
        }.to have_enqueued_job(ActionMailer::MailDeliveryJob)
      end
    end
  end

  describe 'instance methods' do
    describe '#full_name' do
      it 'returns first and last name' do
        user = build(:user, first_name: 'John', last_name: 'Doe')
        expect(user.full_name).to eq('John Doe')
      end

      it 'handles missing last name' do
        user = build(:user, first_name: 'John', last_name: nil)
        expect(user.full_name).to eq('John')
      end
    end

    describe '#admin?' do
      it 'returns true for admin role' do
        expect(build(:user, :admin)).to be_admin
      end

      it 'returns false for regular user' do
        expect(build(:user)).not_to be_admin
      end
    end
  end

  describe 'class methods' do
    describe '.find_by_credentials' do
      let!(:user) { create(:user, email: 'test@example.com', password: 'password123') }

      it 'returns user with valid credentials' do
        result = described_class.find_by_credentials('test@example.com', 'password123')
        expect(result).to eq(user)
      end

      it 'returns nil with invalid password' do
        result = described_class.find_by_credentials('test@example.com', 'wrong')
        expect(result).to be_nil
      end

      it 'returns nil with unknown email' do
        result = described_class.find_by_credentials('unknown@example.com', 'password123')
        expect(result).to be_nil
      end
    end
  end
end
```

## Shared Examples

```ruby
# spec/support/shared_examples/soft_deletable.rb
RSpec.shared_examples 'soft deletable' do
  describe 'soft delete' do
    let(:record) { create(described_class.model_name.singular.to_sym) }

    describe '#soft_delete' do
      it 'sets deleted_at timestamp' do
        expect { record.soft_delete }.to change { record.deleted_at }.from(nil)
      end

      it 'does not destroy the record' do
        record.soft_delete
        expect(described_class.unscoped.find(record.id)).to be_present
      end
    end

    describe '#restore' do
      before { record.soft_delete }

      it 'clears deleted_at timestamp' do
        expect { record.restore }.to change { record.deleted_at }.to(nil)
      end
    end

    describe '.active' do
      let!(:active_record) { create(described_class.model_name.singular.to_sym) }
      let!(:deleted_record) { create(described_class.model_name.singular.to_sym, deleted_at: Time.current) }

      it 'excludes soft deleted records' do
        expect(described_class.active).to include(active_record)
        expect(described_class.active).not_to include(deleted_record)
      end
    end
  end
end

# Usage
RSpec.describe Article, type: :model do
  it_behaves_like 'soft deletable'
end
```

```ruby
# spec/support/shared_examples/sluggable.rb
RSpec.shared_examples 'sluggable' do |source_attribute|
  describe 'slug generation' do
    it 'generates slug from source attribute' do
      record = build(described_class.model_name.singular.to_sym, source_attribute => 'Hello World')
      record.valid?
      expect(record.slug).to eq('hello-world')
    end

    it 'handles special characters' do
      record = build(described_class.model_name.singular.to_sym, source_attribute => 'Test & Demo!')
      record.valid?
      expect(record.slug).to eq('test-demo')
    end

    it 'ensures uniqueness' do
      create(described_class.model_name.singular.to_sym, source_attribute => 'Same Title')
      record = build(described_class.model_name.singular.to_sym, source_attribute => 'Same Title')
      record.valid?
      expect(record.slug).to match(/same-title-\w+/)
    end
  end
end
```

## Shared Contexts

```ruby
# spec/support/shared_contexts/authenticated.rb
RSpec.shared_context 'authenticated user' do
  let(:current_user) { create(:user) }
  let(:auth_headers) { auth_headers_for(current_user) }
end

RSpec.shared_context 'authenticated admin' do
  let(:current_user) { create(:user, :admin) }
  let(:auth_headers) { auth_headers_for(current_user) }
end

# Usage
RSpec.describe 'Admin Products API', type: :request do
  include_context 'authenticated admin'

  describe 'DELETE /api/v1/products/:id' do
    let!(:product) { create(:product) }

    it 'deletes the product' do
      expect {
        delete "/api/v1/products/#{product.id}", headers: auth_headers
      }.to change(Product, :count).by(-1)
    end
  end
end
```

## Custom Matchers

```ruby
# spec/support/matchers/have_json_api_attributes.rb
RSpec::Matchers.define :have_json_api_attributes do |expected_attributes|
  match do |response|
    json = JSON.parse(response.body)
    attributes = json.dig('data', 'attributes') || {}
    expected_attributes.all? { |attr| attributes.key?(attr.to_s) }
  end

  failure_message do |response|
    json = JSON.parse(response.body)
    attributes = json.dig('data', 'attributes')&.keys || []
    "expected response to have attributes #{expected_attributes}, but had #{attributes}"
  end
end

# Usage
expect(response).to have_json_api_attributes(:name, :email, :created_at)
```

```ruby
# spec/support/matchers/be_valid_json.rb
RSpec::Matchers.define :be_valid_json do
  match do |response|
    JSON.parse(response.body)
    true
  rescue JSON::ParserError
    false
  end

  failure_message do
    'expected response body to be valid JSON'
  end
end
```

## Testing Concerns

```ruby
# spec/models/concerns/searchable_spec.rb
RSpec.describe Searchable do
  let(:test_class) do
    Class.new(ApplicationRecord) do
      self.table_name = 'products'
      include Searchable
      searchable_on :name, :description
    end
  end

  describe '.search' do
    before do
      test_class.create!(name: 'Ruby Programming', description: 'Learn Ruby')
      test_class.create!(name: 'Python Guide', description: 'Python basics')
      test_class.create!(name: 'JavaScript', description: 'Modern JS')
    end

    it 'finds records matching query' do
      results = test_class.search('ruby')
      expect(results.count).to eq(1)
      expect(results.first.name).to eq('Ruby Programming')
    end

    it 'searches across multiple columns' do
      results = test_class.search('python')
      expect(results.count).to eq(1)
    end

    it 'returns all records for blank query' do
      expect(test_class.search('')).to eq(test_class.all)
      expect(test_class.search(nil)).to eq(test_class.all)
    end
  end
end
```

## Mocking and Stubbing

```ruby
# spec/services/payment_service_spec.rb
RSpec.describe PaymentService do
  describe '#process' do
    let(:order) { create(:order, total: 100.00) }
    let(:service) { described_class.new(order) }

    context 'with successful payment' do
      before do
        allow(StripeClient).to receive(:charge).and_return(
          OpenStruct.new(id: 'ch_123', status: 'succeeded')
        )
      end

      it 'returns success result' do
        result = service.process
        expect(result).to be_success
        expect(result.data[:charge_id]).to eq('ch_123')
      end

      it 'updates order status' do
        service.process
        expect(order.reload.status).to eq('paid')
      end
    end

    context 'with failed payment' do
      before do
        allow(StripeClient).to receive(:charge).and_raise(
          Stripe::CardError.new('Card declined', 'card_error')
        )
      end

      it 'returns failure result' do
        result = service.process
        expect(result).to be_failure
        expect(result.errors).to include('Card declined')
      end

      it 'does not update order status' do
        service.process
        expect(order.reload.status).to eq('pending')
      end
    end
  end
end
```

## Time-Dependent Tests

```ruby
# spec/models/subscription_spec.rb
RSpec.describe Subscription do
  describe '#active?' do
    let(:subscription) { build(:subscription, expires_at: expires_at) }

    context 'when not expired' do
      let(:expires_at) { 1.day.from_now }

      it 'returns true' do
        expect(subscription).to be_active
      end
    end

    context 'when expired' do
      let(:expires_at) { 1.day.ago }

      it 'returns false' do
        expect(subscription).not_to be_active
      end
    end
  end

  describe '.expiring_soon' do
    it 'returns subscriptions expiring within 7 days' do
      travel_to Time.zone.local(2024, 1, 15, 12, 0, 0) do
        expiring = create(:subscription, expires_at: 5.days.from_now)
        not_expiring = create(:subscription, expires_at: 30.days.from_now)

        expect(described_class.expiring_soon).to include(expiring)
        expect(described_class.expiring_soon).not_to include(not_expiring)
      end
    end
  end
end
```

## Testing Jobs

```ruby
# spec/jobs/send_notification_job_spec.rb
RSpec.describe SendNotificationJob, type: :job do
  describe '#perform' do
    let(:user) { create(:user) }

    it 'sends notification to user' do
      expect(NotificationService).to receive(:send).with(user, 'Hello')

      described_class.perform_now(user.id, 'Hello')
    end

    it 'logs error for missing user' do
      expect(Rails.logger).to receive(:error).with(/User not found/)

      described_class.perform_now(-1, 'Hello')
    end
  end

  describe 'enqueuing' do
    it 'enqueues the job' do
      expect {
        described_class.perform_later(1, 'message')
      }.to have_enqueued_job(described_class)
        .with(1, 'message')
        .on_queue('default')
    end
  end
end
```

## Testing Mailers

```ruby
# spec/mailers/user_mailer_spec.rb
RSpec.describe UserMailer, type: :mailer do
  describe '#welcome_email' do
    let(:user) { create(:user, email: 'test@example.com', name: 'John') }
    let(:mail) { described_class.welcome_email(user) }

    it 'renders the headers' do
      expect(mail.subject).to eq('Welcome to MyApp')
      expect(mail.to).to eq(['test@example.com'])
      expect(mail.from).to eq(['noreply@myapp.com'])
    end

    it 'renders the body' do
      expect(mail.body.encoded).to include('John')
      expect(mail.body.encoded).to include('Welcome')
    end

    it 'is delivered' do
      expect { mail.deliver_now }.to change { ActionMailer::Base.deliveries.count }.by(1)
    end
  end
end
```

## Aggregate Failures

```ruby
# spec/models/product_spec.rb
RSpec.describe Product, type: :model do
  describe 'validations', :aggregate_failures do
    it 'validates required fields' do
      product = Product.new
      product.valid?

      expect(product.errors[:name]).to include("can't be blank")
      expect(product.errors[:price]).to include("can't be blank")
      expect(product.errors[:sku]).to include("can't be blank")
    end
  end
end
```

## Best Practices

1. **One assertion per test** - Each test should verify one thing
2. **Descriptive test names** - Use context and it blocks meaningfully
3. **Use let over instance variables** - Lazy evaluation and cleaner syntax
4. **Use build over create when possible** - Faster tests without database
5. **Shared examples for common behavior** - DRY up repeated patterns
6. **Clean database between tests** - Use database cleaner or transactions
7. **Mock external services** - Use WebMock, VCR for HTTP calls
8. **Test edge cases** - Nil values, empty arrays, boundaries
