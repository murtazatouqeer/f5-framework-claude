# Rails Spec Template

## Model Spec Template

```ruby
# spec/models/{{resource}}_spec.rb
RSpec.describe {{Resource}}, type: :model do
  # === Factory ===
  subject { build(:{{resource}}) }

  # === Associations ===
  describe 'associations' do
    it { is_expected.to belong_to(:{{parent}}) }
    it { is_expected.to belong_to(:created_by).class_name('User').optional }
    it { is_expected.to have_many(:{{children}}).dependent(:destroy) }
    it { is_expected.to have_many(:{{through}}).through(:{{join_table}}) }
  end

  # === Validations ===
  describe 'validations' do
    it { is_expected.to validate_presence_of(:name) }
    it { is_expected.to validate_uniqueness_of(:slug) }
    it { is_expected.to validate_length_of(:name).is_at_most(255) }
    it { is_expected.to validate_numericality_of(:{{numeric_field}}).is_greater_than_or_equal_to(0) }
  end

  # === Enums ===
  describe 'enums' do
    it { is_expected.to define_enum_for(:status).with_values({{ENUM_VALUES}}) }
  end

  # === Scopes ===
  describe 'scopes' do
    describe '.{{scope_name}}' do
      let!(:matching) { create(:{{resource}}, {{MATCHING_ATTRS}}) }
      let!(:non_matching) { create(:{{resource}}, {{NON_MATCHING_ATTRS}}) }

      it 'returns matching records' do
        expect(described_class.{{scope_name}}).to include(matching)
        expect(described_class.{{scope_name}}).not_to include(non_matching)
      end
    end
  end

  # === Instance Methods ===
  describe '#{{method_name}}' do
    it 'returns expected value' do
      {{resource}} = build(:{{resource}}, {{ATTRS}})
      expect({{resource}}.{{method_name}}).to eq({{EXPECTED}})
    end
  end

  # === Callbacks ===
  describe 'callbacks' do
    describe 'before_validation' do
      it 'generates slug' do
        {{resource}} = build(:{{resource}}, name: 'Test Name', slug: nil)
        {{resource}}.valid?
        expect({{resource}}.slug).to eq('test-name')
      end
    end
  end
end
```

## Request Spec Template

```ruby
# spec/requests/api/v1/{{resource_plural}}_spec.rb
RSpec.describe 'Api::V1::{{ResourcePlural}}', type: :request do
  let(:current_user) { create(:user) }
  let(:headers) { auth_headers_for(current_user) }

  describe 'GET /api/v1/{{resource_plural}}' do
    let!(:{{resource_plural}}) { create_list(:{{resource}}, 3) }

    it 'returns all {{resource_plural}}' do
      get '/api/v1/{{resource_plural}}', headers: headers

      expect(response).to have_http_status(:ok)
      expect(json_data.length).to eq(3)
    end

    context 'without authentication' do
      it 'returns unauthorized' do
        get '/api/v1/{{resource_plural}}'
        expect(response).to have_http_status(:unauthorized)
      end
    end
  end

  describe 'GET /api/v1/{{resource_plural}}/:id' do
    let!(:{{resource}}) { create(:{{resource}}) }

    it 'returns the {{resource}}' do
      get "/api/v1/{{resource_plural}}/#{{{resource}}.id}", headers: headers

      expect(response).to have_http_status(:ok)
      expect(json_data[:id]).to eq({{resource}}.id.to_s)
    end

    context 'with non-existent {{resource}}' do
      it 'returns not found' do
        get '/api/v1/{{resource_plural}}/invalid-id', headers: headers
        expect(response).to have_http_status(:not_found)
      end
    end
  end

  describe 'POST /api/v1/{{resource_plural}}' do
    let(:valid_params) { { {{resource}}: attributes_for(:{{resource}}) } }

    context 'with valid params' do
      it 'creates a {{resource}}' do
        expect {
          post '/api/v1/{{resource_plural}}', params: valid_params, headers: headers
        }.to change({{Resource}}, :count).by(1)

        expect(response).to have_http_status(:created)
      end
    end

    context 'with invalid params' do
      let(:invalid_params) { { {{resource}}: { name: '' } } }

      it 'returns unprocessable entity' do
        post '/api/v1/{{resource_plural}}', params: invalid_params, headers: headers
        expect(response).to have_http_status(:unprocessable_entity)
      end
    end
  end

  describe 'PATCH /api/v1/{{resource_plural}}/:id' do
    let!(:{{resource}}) { create(:{{resource}}, created_by: current_user) }
    let(:update_params) { { {{resource}}: { name: 'Updated' } } }

    it 'updates the {{resource}}' do
      patch "/api/v1/{{resource_plural}}/#{{{resource}}.id}", params: update_params, headers: headers

      expect(response).to have_http_status(:ok)
      expect({{resource}}.reload.name).to eq('Updated')
    end

    context 'when not owner' do
      let!(:{{resource}}) { create(:{{resource}}) }

      it 'returns forbidden' do
        patch "/api/v1/{{resource_plural}}/#{{{resource}}.id}", params: update_params, headers: headers
        expect(response).to have_http_status(:forbidden)
      end
    end
  end

  describe 'DELETE /api/v1/{{resource_plural}}/:id' do
    let!(:{{resource}}) { create(:{{resource}}, created_by: current_user) }

    it 'deletes the {{resource}}' do
      expect {
        delete "/api/v1/{{resource_plural}}/#{{{resource}}.id}", headers: headers
      }.to change({{Resource}}, :count).by(-1)

      expect(response).to have_http_status(:no_content)
    end
  end
end
```

## Service Spec Template

```ruby
# spec/services/{{resource}}_service_spec.rb
RSpec.describe {{Resource}}Service do
  let(:user) { create(:user) }
  let(:{{resource}}) { create(:{{resource}}) }

  describe '#{{action}}' do
    subject { described_class.new({{resource}}, current_user: user) }

    context 'with valid {{resource}}' do
      it 'returns success' do
        result = subject.{{action}}
        expect(result).to be_success
      end

      it '{{EXPECTED_BEHAVIOR}}' do
        subject.{{action}}
        expect({{resource}}.reload.{{FIELD}}).to eq({{EXPECTED}})
      end
    end

    context 'with invalid {{resource}}' do
      let(:{{resource}}) { nil }

      it 'returns failure' do
        result = subject.{{action}}
        expect(result).to be_failure
        expect(result.errors).to include('{{EXPECTED_ERROR}}')
      end
    end
  end
end
```

## Policy Spec Template

```ruby
# spec/policies/{{resource}}_policy_spec.rb
RSpec.describe {{Resource}}Policy, type: :policy do
  let(:user) { create(:user) }
  let(:admin) { create(:user, :admin) }
  let(:{{resource}}) { create(:{{resource}}, created_by: user) }
  let(:other_{{resource}}) { create(:{{resource}}) }

  subject { described_class }

  permissions :show? do
    it 'permits everyone for active {{resource}}' do
      {{resource}}.update!(status: :active)
      expect(subject).to permit(nil, {{resource}})
      expect(subject).to permit(user, {{resource}})
    end

    it 'denies guest for draft {{resource}}' do
      expect(subject).not_to permit(nil, {{resource}})
    end

    it 'permits owner for draft {{resource}}' do
      expect(subject).to permit(user, {{resource}})
    end

    it 'permits admin for any {{resource}}' do
      expect(subject).to permit(admin, other_{{resource}})
    end
  end

  permissions :update? do
    it 'permits owner' do
      expect(subject).to permit(user, {{resource}})
    end

    it 'permits admin' do
      expect(subject).to permit(admin, other_{{resource}})
    end

    it 'denies non-owner' do
      expect(subject).not_to permit(create(:user), {{resource}})
    end
  end

  permissions :destroy? do
    it 'permits admin' do
      expect(subject).to permit(admin, {{resource}})
    end

    context '{{resource}} without dependencies' do
      it 'permits owner' do
        expect(subject).to permit(user, {{resource}})
      end
    end

    context '{{resource}} with dependencies' do
      before { create(:{{dependent}}, {{resource}}: {{resource}}) }

      it 'denies owner' do
        expect(subject).not_to permit(user, {{resource}})
      end

      it 'permits admin' do
        expect(subject).to permit(admin, {{resource}})
      end
    end
  end

  describe '{{Resource}}Policy::Scope' do
    let!(:active_{{resource}}) { create(:{{resource}}, status: :active) }
    let!(:draft_{{resource}}) { create(:{{resource}}, status: :draft, created_by: user) }
    let!(:other_draft) { create(:{{resource}}, status: :draft) }

    context 'as regular user' do
      subject { described_class::Scope.new(user, {{Resource}}).resolve }

      it 'includes active {{resource_plural}}' do
        expect(subject).to include(active_{{resource}})
      end

      it 'includes own drafts' do
        expect(subject).to include(draft_{{resource}})
      end

      it 'excludes other drafts' do
        expect(subject).not_to include(other_draft)
      end
    end

    context 'as admin' do
      subject { described_class::Scope.new(admin, {{Resource}}).resolve }

      it 'includes all {{resource_plural}}' do
        expect(subject).to include(active_{{resource}}, draft_{{resource}}, other_draft)
      end
    end
  end
end
```

## Factory Template

```ruby
# spec/factories/{{resource_plural}}.rb
FactoryBot.define do
  factory :{{resource}} do
    {{parent}}
    name { Faker::Commerce.product_name }
    description { Faker::Lorem.paragraph }
    status { :draft }

    # === Traits ===
    trait :active do
      status { :active }
      published_at { Time.current }
    end

    trait :archived do
      status { :archived }
      archived_at { Time.current }
    end

    trait :with_{{association}} do
      after(:create) do |{{resource}}|
        create(:{{association}}, {{resource}}: {{resource}})
      end
    end

    trait :with_{{associations}} do
      transient do
        {{associations}}_count { 3 }
      end

      after(:create) do |{{resource}}, evaluator|
        create_list(:{{association}}, evaluator.{{associations}}_count, {{resource}}: {{resource}})
      end
    end

    # === Child Factories ===
    factory :published_{{resource}} do
      active
      association :created_by, factory: :user
    end
  end
end
```

## Job Spec Template

```ruby
# spec/jobs/{{resource}}_job_spec.rb
RSpec.describe {{Resource}}Job, type: :job do
  let(:{{resource}}) { create(:{{resource}}) }

  describe '#perform' do
    it '{{EXPECTED_BEHAVIOR}}' do
      expect {
        described_class.perform_now({{resource}}.id)
      }.to change { {{CHANGE_EXPRESSION}} }.by({{CHANGE_VALUE}})
    end

    it 'handles missing {{resource}}' do
      expect {
        described_class.perform_now(-1)
      }.not_to raise_error
    end
  end

  describe 'enqueueing' do
    it 'enqueues the job' do
      expect {
        described_class.perform_async({{resource}}.id)
      }.to change(described_class.jobs, :size).by(1)
    end

    it 'enqueues on correct queue' do
      described_class.perform_async({{resource}}.id)
      expect(described_class.jobs.last['queue']).to eq('{{QUEUE_NAME}}')
    end
  end
end
```

## Mailer Spec Template

```ruby
# spec/mailers/{{resource}}_mailer_spec.rb
RSpec.describe {{Resource}}Mailer, type: :mailer do
  let(:user) { create(:user) }
  let(:{{resource}}) { create(:{{resource}}) }

  describe '#{{action}}_email' do
    let(:mail) { described_class.{{action}}_email(user, {{resource}}) }

    it 'renders the headers' do
      expect(mail.subject).to eq('{{EXPECTED_SUBJECT}}')
      expect(mail.to).to eq([user.email])
      expect(mail.from).to eq(['noreply@example.com'])
    end

    it 'renders the body' do
      expect(mail.body.encoded).to include({{resource}}.name)
      expect(mail.body.encoded).to include(user.name)
    end

    it 'is delivered' do
      expect { mail.deliver_now }.to change { ActionMailer::Base.deliveries.count }.by(1)
    end
  end
end
```
