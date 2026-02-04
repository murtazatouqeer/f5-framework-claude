# Authentication Module Example

Complete JWT authentication system with Devise for Rails API.

## Overview

This example demonstrates:
- Devise with JWT authentication
- User registration and login
- Token refresh mechanism
- Password reset flow
- Email confirmation
- Role-based access

## Directory Structure

```
app/
├── controllers/
│   └── api/
│       └── v1/
│           └── auth/
│               ├── sessions_controller.rb
│               ├── registrations_controller.rb
│               ├── passwords_controller.rb
│               ├── confirmations_controller.rb
│               └── users_controller.rb
├── models/
│   └── user.rb
├── serializers/
│   └── user_serializer.rb
├── mailers/
│   └── user_mailer.rb
└── services/
    └── auth/
        ├── token_service.rb
        └── password_reset_service.rb
```

## Gemfile

```ruby
# Authentication
gem 'devise'
gem 'devise-jwt'

# Optional: OAuth providers
gem 'omniauth-google-oauth2'
gem 'omniauth-github'
```

## User Model

```ruby
# app/models/user.rb
class User < ApplicationRecord
  include Devise::JWT::RevocationStrategies::JTIMatcher

  devise :database_authenticatable, :registerable,
         :recoverable, :rememberable, :validatable,
         :confirmable, :trackable,
         :jwt_authenticatable, jwt_revocation_strategy: self

  # Associations
  has_many :orders, dependent: :nullify
  has_one :profile, dependent: :destroy

  # Enums
  enum :role, {
    user: 'user',
    admin: 'admin',
    moderator: 'moderator'
  }, prefix: true, default: :user

  enum :status, {
    active: 'active',
    inactive: 'inactive',
    suspended: 'suspended'
  }, prefix: true, default: :active

  # Validations
  validates :email, presence: true, uniqueness: { case_sensitive: false }
  validates :name, presence: true, length: { maximum: 100 }

  # Callbacks
  after_create :create_default_profile
  after_create :send_welcome_email

  # Scopes
  scope :active, -> { where(status: :active) }
  scope :admins, -> { where(role: :admin) }

  def admin?
    role_admin?
  end

  def active_for_authentication?
    super && status_active?
  end

  def inactive_message
    status_active? ? super : :account_suspended
  end

  def jwt_payload
    {
      'user_id' => id,
      'email' => email,
      'role' => role,
      'exp' => 24.hours.from_now.to_i
    }
  end

  private

  def create_default_profile
    create_profile!
  end

  def send_welcome_email
    UserMailer.welcome_email(self).deliver_later
  end
end
```

## Migration

```ruby
# db/migrate/20240115100000_devise_create_users.rb
class DeviseCreateUsers < ActiveRecord::Migration[7.1]
  def change
    create_table :users, id: :uuid do |t|
      # Devise fields
      t.string :email, null: false, default: ''
      t.string :encrypted_password, null: false, default: ''
      t.string :reset_password_token
      t.datetime :reset_password_sent_at
      t.datetime :remember_created_at

      # Confirmable
      t.string :confirmation_token
      t.datetime :confirmed_at
      t.datetime :confirmation_sent_at
      t.string :unconfirmed_email

      # Trackable
      t.integer :sign_in_count, default: 0, null: false
      t.datetime :current_sign_in_at
      t.datetime :last_sign_in_at
      t.string :current_sign_in_ip
      t.string :last_sign_in_ip

      # JWT
      t.string :jti, null: false

      # Profile
      t.string :name, null: false
      t.string :role, default: 'user', null: false
      t.string :status, default: 'active', null: false
      t.string :avatar_url
      t.string :phone
      t.string :timezone, default: 'UTC'
      t.jsonb :preferences, default: {}

      t.timestamps null: false
    end

    add_index :users, :email, unique: true
    add_index :users, :reset_password_token, unique: true
    add_index :users, :confirmation_token, unique: true
    add_index :users, :jti, unique: true
    add_index :users, :role
    add_index :users, :status
  end
end
```

## Devise Configuration

```ruby
# config/initializers/devise.rb
Devise.setup do |config|
  config.mailer_sender = 'noreply@example.com'

  # JWT configuration
  config.jwt do |jwt|
    jwt.secret = Rails.application.credentials.devise_jwt_secret_key!
    jwt.dispatch_requests = [
      ['POST', %r{^/api/v1/auth/login$}],
      ['POST', %r{^/api/v1/auth/register$}]
    ]
    jwt.revocation_requests = [
      ['DELETE', %r{^/api/v1/auth/logout$}]
    ]
    jwt.expiration_time = 24.hours.to_i
  end

  # API-only settings
  config.navigational_formats = []
  config.sign_out_via = :delete

  # Password requirements
  config.password_length = 8..128
  config.email_regexp = /\A[^@\s]+@[^@\s]+\z/

  # Confirmable
  config.confirm_within = 3.days
  config.reconfirmable = true

  # Recoverable
  config.reset_password_within = 6.hours
end
```

## Routes

```ruby
# config/routes.rb
Rails.application.routes.draw do
  namespace :api do
    namespace :v1 do
      devise_for :users,
        path: 'auth',
        path_names: {
          sign_in: 'login',
          sign_out: 'logout',
          registration: 'register'
        },
        controllers: {
          sessions: 'api/v1/auth/sessions',
          registrations: 'api/v1/auth/registrations',
          passwords: 'api/v1/auth/passwords',
          confirmations: 'api/v1/auth/confirmations'
        }

      namespace :auth do
        get 'me', to: 'users#me'
        patch 'me', to: 'users#update'
        post 'refresh', to: 'sessions#refresh'
        delete 'me', to: 'users#destroy'
      end
    end
  end
end
```

## Sessions Controller

```ruby
# app/controllers/api/v1/auth/sessions_controller.rb
module Api
  module V1
    module Auth
      class SessionsController < Devise::SessionsController
        respond_to :json

        def create
          self.resource = warden.authenticate!(auth_options)
          sign_in(resource_name, resource)

          render json: {
            message: 'Logged in successfully',
            user: UserSerializer.new(resource).serializable_hash
          }
        end

        def destroy
          signed_out = (Devise.sign_out_all_scopes ? sign_out : sign_out(resource_name))

          render json: { message: 'Logged out successfully' }
        end

        def refresh
          current_user.update!(jti: SecureRandom.uuid)
          token = Warden::JWTAuth::UserEncoder.new.call(current_user, :user, nil).first

          render json: {
            token: token,
            user: UserSerializer.new(current_user).serializable_hash
          }
        end

        private

        def respond_with(resource, _opts = {})
          render json: {
            message: 'Logged in successfully',
            user: UserSerializer.new(resource).serializable_hash
          }
        end

        def respond_to_on_destroy
          head :no_content
        end
      end
    end
  end
end
```

## Registrations Controller

```ruby
# app/controllers/api/v1/auth/registrations_controller.rb
module Api
  module V1
    module Auth
      class RegistrationsController < Devise::RegistrationsController
        respond_to :json

        def create
          build_resource(sign_up_params)

          if resource.save
            if resource.active_for_authentication?
              sign_up(resource_name, resource)
              render json: {
                message: 'Signed up successfully',
                user: UserSerializer.new(resource).serializable_hash
              }, status: :created
            else
              render json: {
                message: 'Please confirm your email address',
                user: UserSerializer.new(resource).serializable_hash
              }, status: :created
            end
          else
            render json: {
              error: 'Registration failed',
              details: resource.errors.full_messages
            }, status: :unprocessable_entity
          end
        end

        def update
          if current_user.update_with_password(account_update_params)
            render json: {
              message: 'Account updated successfully',
              user: UserSerializer.new(current_user).serializable_hash
            }
          else
            render json: {
              error: 'Update failed',
              details: current_user.errors.full_messages
            }, status: :unprocessable_entity
          end
        end

        def destroy
          current_user.destroy!
          render json: { message: 'Account deleted successfully' }
        end

        private

        def sign_up_params
          params.require(:user).permit(:email, :password, :password_confirmation, :name)
        end

        def account_update_params
          params.require(:user).permit(
            :email, :password, :password_confirmation,
            :current_password, :name, :phone, :timezone
          )
        end
      end
    end
  end
end
```

## Passwords Controller

```ruby
# app/controllers/api/v1/auth/passwords_controller.rb
module Api
  module V1
    module Auth
      class PasswordsController < Devise::PasswordsController
        respond_to :json

        def create
          self.resource = resource_class.send_reset_password_instructions(resource_params)

          if successfully_sent?(resource)
            render json: { message: 'Reset password instructions sent' }
          else
            render json: {
              error: 'Unable to send reset instructions',
              details: resource.errors.full_messages
            }, status: :unprocessable_entity
          end
        end

        def update
          self.resource = resource_class.reset_password_by_token(resource_params)

          if resource.errors.empty?
            render json: { message: 'Password reset successfully' }
          else
            render json: {
              error: 'Password reset failed',
              details: resource.errors.full_messages
            }, status: :unprocessable_entity
          end
        end

        private

        def resource_params
          params.require(:user).permit(:email, :password, :password_confirmation, :reset_password_token)
        end
      end
    end
  end
end
```

## Users Controller

```ruby
# app/controllers/api/v1/auth/users_controller.rb
module Api
  module V1
    module Auth
      class UsersController < ApplicationController
        before_action :authenticate_user!

        def me
          render json: UserSerializer.new(
            current_user,
            include: [:profile]
          ).serializable_hash
        end

        def update
          if current_user.update(user_params)
            render json: UserSerializer.new(current_user).serializable_hash
          else
            render json: {
              error: 'Update failed',
              details: current_user.errors.full_messages
            }, status: :unprocessable_entity
          end
        end

        def destroy
          current_user.destroy!
          head :no_content
        end

        private

        def user_params
          params.require(:user).permit(:name, :phone, :timezone, :avatar, preferences: {})
        end
      end
    end
  end
end
```

## User Serializer

```ruby
# app/serializers/user_serializer.rb
class UserSerializer
  include JSONAPI::Serializer

  set_type :user
  set_id :id

  attributes :email, :name, :role, :status

  attribute :created_at do |user|
    user.created_at.iso8601
  end

  attribute :confirmed do |user|
    user.confirmed?
  end

  attribute :avatar_url do |user|
    user.avatar_url
  end

  attribute :phone, if: proc { |_record, params|
    params[:include_contact]
  }

  attribute :preferences do |user|
    user.preferences
  end

  has_one :profile, serializer: ProfileSerializer
end
```

## Application Controller

```ruby
# app/controllers/application_controller.rb
class ApplicationController < ActionController::API
  before_action :configure_permitted_parameters, if: :devise_controller?
  rescue_from ActiveRecord::RecordNotFound, with: :not_found

  private

  def configure_permitted_parameters
    devise_parameter_sanitizer.permit(:sign_up, keys: [:name])
    devise_parameter_sanitizer.permit(:account_update, keys: [:name, :phone, :timezone])
  end

  def current_user
    @current_user ||= warden.authenticate(scope: :user)
  end

  def authenticate_user!
    unless current_user
      render json: {
        error: 'You need to sign in or sign up before continuing.'
      }, status: :unauthorized
    end
  end

  def not_found
    render json: { error: 'Record not found' }, status: :not_found
  end
end
```

## Auth Helpers for Tests

```ruby
# spec/support/auth_helpers.rb
module AuthHelpers
  def auth_headers_for(user)
    token = Warden::JWTAuth::UserEncoder.new.call(user, :user, nil).first
    { 'Authorization' => "Bearer #{token}" }
  end
end

RSpec.configure do |config|
  config.include AuthHelpers, type: :request
end
```

## Request Specs

```ruby
# spec/requests/api/v1/auth/sessions_spec.rb
RSpec.describe 'Api::V1::Auth::Sessions', type: :request do
  describe 'POST /api/v1/auth/login' do
    let!(:user) { create(:user, email: 'test@example.com', password: 'password123') }

    context 'with valid credentials' do
      let(:params) { { user: { email: 'test@example.com', password: 'password123' } } }

      it 'returns success with JWT token' do
        post '/api/v1/auth/login', params: params

        expect(response).to have_http_status(:ok)
        expect(response.headers['Authorization']).to start_with('Bearer ')
        expect(json_response[:user][:data][:attributes][:email]).to eq('test@example.com')
      end

      it 'updates sign in tracking' do
        post '/api/v1/auth/login', params: params

        user.reload
        expect(user.sign_in_count).to eq(1)
        expect(user.current_sign_in_at).to be_present
      end
    end

    context 'with invalid credentials' do
      let(:params) { { user: { email: 'test@example.com', password: 'wrong' } } }

      it 'returns unauthorized' do
        post '/api/v1/auth/login', params: params

        expect(response).to have_http_status(:unauthorized)
      end
    end

    context 'with suspended user' do
      before { user.update!(status: :suspended) }
      let(:params) { { user: { email: 'test@example.com', password: 'password123' } } }

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

      expect(response).to have_http_status(:ok)
    end

    it 'invalidates token' do
      delete '/api/v1/auth/logout', headers: headers

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

        expect(response).to have_http_status(:created)
      end

      it 'returns JWT token' do
        post '/api/v1/auth/register', params: valid_params

        expect(response.headers['Authorization']).to be_present
      end

      it 'sends confirmation email' do
        expect {
          post '/api/v1/auth/register', params: valid_params
        }.to have_enqueued_mail(Devise::Mailer, :confirmation_instructions)
      end
    end

    context 'with existing email' do
      before { create(:user, email: 'new@example.com') }

      it 'returns unprocessable entity' do
        post '/api/v1/auth/register', params: valid_params

        expect(response).to have_http_status(:unprocessable_entity)
        expect(json_response[:details]).to include('Email has already been taken')
      end
    end
  end
end
```

## Factory

```ruby
# spec/factories/users.rb
FactoryBot.define do
  factory :user do
    email { Faker::Internet.unique.email }
    password { 'password123' }
    password_confirmation { password }
    name { Faker::Name.name }
    role { :user }
    status { :active }
    confirmed_at { Time.current }
    jti { SecureRandom.uuid }

    trait :admin do
      role { :admin }
    end

    trait :unconfirmed do
      confirmed_at { nil }
    end

    trait :suspended do
      status { :suspended }
    end

    trait :with_profile do
      after(:create) do |user|
        create(:profile, user: user)
      end
    end
  end
end
```

## API Usage Examples

```bash
# Register
curl -X POST http://localhost:3000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"user": {"email": "user@example.com", "password": "password123", "password_confirmation": "password123", "name": "John Doe"}}'

# Login
curl -X POST http://localhost:3000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"user": {"email": "user@example.com", "password": "password123"}}'

# Get current user
curl http://localhost:3000/api/v1/auth/me \
  -H "Authorization: Bearer <token>"

# Refresh token
curl -X POST http://localhost:3000/api/v1/auth/refresh \
  -H "Authorization: Bearer <token>"

# Request password reset
curl -X POST http://localhost:3000/api/v1/auth/password \
  -H "Content-Type: application/json" \
  -d '{"user": {"email": "user@example.com"}}'

# Reset password
curl -X PUT http://localhost:3000/api/v1/auth/password \
  -H "Content-Type: application/json" \
  -d '{"user": {"reset_password_token": "<token>", "password": "newpassword123", "password_confirmation": "newpassword123"}}'

# Logout
curl -X DELETE http://localhost:3000/api/v1/auth/logout \
  -H "Authorization: Bearer <token>"
```
