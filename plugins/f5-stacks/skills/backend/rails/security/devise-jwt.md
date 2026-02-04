# Devise JWT Authentication

JWT authentication for Rails APIs using Devise and devise-jwt.

## Setup

### Gemfile

```ruby
gem 'devise'
gem 'devise-jwt'
```

### Installation

```bash
rails generate devise:install
rails generate devise User
rails db:migrate
```

### User Model

```ruby
# app/models/user.rb
class User < ApplicationRecord
  include Devise::JWT::RevocationStrategies::JTIMatcher

  devise :database_authenticatable, :registerable,
         :recoverable, :validatable,
         :jwt_authenticatable, jwt_revocation_strategy: self

  # Associations
  has_many :orders, dependent: :nullify
  has_one :profile, dependent: :destroy

  # Enums
  enum role: { user: 'user', admin: 'admin', moderator: 'moderator' }, _prefix: true

  # Validations
  validates :email, presence: true, uniqueness: { case_sensitive: false }
  validates :name, presence: true, length: { maximum: 100 }

  # Callbacks
  after_create :create_default_profile

  def admin?
    role_admin?
  end

  def jwt_payload
    {
      'user_id' => id,
      'email' => email,
      'role' => role
    }
  end

  private

  def create_default_profile
    create_profile!
  end
end
```

### Migration for JWT

```ruby
# db/migrate/YYYYMMDDHHMMSS_add_jti_to_users.rb
class AddJtiToUsers < ActiveRecord::Migration[7.1]
  def change
    add_column :users, :jti, :string, null: false
    add_index :users, :jti, unique: true
  end
end
```

### Devise Configuration

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
    jwt.expiration_time = 1.day.to_i
  end

  # Navigational formats (empty for API)
  config.navigational_formats = []

  # Sign out via DELETE
  config.sign_out_via = :delete
end
```

### Routes

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
          registrations: 'api/v1/auth/registrations'
        }

      # Additional auth routes
      namespace :auth do
        get 'me', to: 'users#me'
        post 'refresh', to: 'sessions#refresh'
        post 'forgot_password', to: 'passwords#create'
        put 'reset_password', to: 'passwords#update'
      end
    end
  end
end
```

### Sessions Controller

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
          yield resource if block_given?

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
          # Token refresh logic
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

### Registrations Controller

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
            sign_up(resource_name, resource)

            render json: {
              message: 'Signed up successfully',
              user: UserSerializer.new(resource).serializable_hash
            }, status: :created
          else
            render json: {
              error: 'Registration failed',
              details: resource.errors.full_messages
            }, status: :unprocessable_entity
          end
        end

        private

        def sign_up_params
          params.require(:user).permit(:email, :password, :password_confirmation, :name)
        end
      end
    end
  end
end
```

### Current User Controller

```ruby
# app/controllers/api/v1/auth/users_controller.rb
module Api
  module V1
    module Auth
      class UsersController < ApplicationController
        before_action :authenticate_user!

        def me
          render json: UserSerializer.new(current_user).serializable_hash
        end
      end
    end
  end
end
```

### Application Controller

```ruby
# app/controllers/application_controller.rb
class ApplicationController < ActionController::API
  before_action :configure_permitted_parameters, if: :devise_controller?

  private

  def configure_permitted_parameters
    devise_parameter_sanitizer.permit(:sign_up, keys: [:name])
    devise_parameter_sanitizer.permit(:account_update, keys: [:name])
  end

  def current_user
    @current_user ||= warden.authenticate(scope: :user)
  end

  def authenticate_user!
    unless current_user
      render json: { error: 'You need to sign in or sign up before continuing.' }, status: :unauthorized
    end
  end
end
```

## Token Blacklisting (Alternative Strategy)

```ruby
# app/models/jwt_blacklist.rb
class JwtBlacklist < ApplicationRecord
  include Devise::JWT::RevocationStrategies::Denylist

  self.table_name = 'jwt_blacklist'
end

# Migration
class CreateJwtBlacklist < ActiveRecord::Migration[7.1]
  def change
    create_table :jwt_blacklist do |t|
      t.string :jti, null: false
      t.datetime :exp, null: false
    end
    add_index :jwt_blacklist, :jti
  end
end

# User model
class User < ApplicationRecord
  devise :database_authenticatable, :registerable,
         :jwt_authenticatable, jwt_revocation_strategy: JwtBlacklist
end
```

## Request Examples

```bash
# Register
curl -X POST http://localhost:3000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"user": {"email": "user@example.com", "password": "password123", "name": "John Doe"}}'

# Login
curl -X POST http://localhost:3000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"user": {"email": "user@example.com", "password": "password123"}}'

# Response includes JWT in Authorization header
# Authorization: Bearer eyJhbGciOiJIUzI1NiJ9...

# Authenticated request
curl http://localhost:3000/api/v1/auth/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9..."

# Logout
curl -X DELETE http://localhost:3000/api/v1/auth/logout \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9..."
```

## Testing

```ruby
# spec/support/auth_helpers.rb
module AuthHelpers
  def auth_headers(user)
    token = Warden::JWTAuth::UserEncoder.new.call(user, :user, nil).first
    { 'Authorization' => "Bearer #{token}" }
  end
end

RSpec.configure do |config|
  config.include AuthHelpers, type: :request
end

# spec/requests/api/v1/auth/sessions_spec.rb
RSpec.describe 'Api::V1::Auth::Sessions', type: :request do
  let(:user) { create(:user, password: 'password123') }

  describe 'POST /api/v1/auth/login' do
    it 'returns JWT token on successful login' do
      post '/api/v1/auth/login', params: {
        user: { email: user.email, password: 'password123' }
      }

      expect(response).to have_http_status(:ok)
      expect(response.headers['Authorization']).to be_present
    end

    it 'returns error on invalid credentials' do
      post '/api/v1/auth/login', params: {
        user: { email: user.email, password: 'wrong' }
      }

      expect(response).to have_http_status(:unauthorized)
    end
  end
end
```

## Best Practices

1. **Use strong secrets** - Generate secure keys for JWT
2. **Set appropriate expiration** - Balance security and UX
3. **Implement token refresh** - For long-lived sessions
4. **Use HTTPS** - Always in production
5. **Blacklist on logout** - Invalidate tokens properly
6. **Include minimal claims** - Only necessary data in payload
7. **Handle expired tokens** - Return appropriate errors
