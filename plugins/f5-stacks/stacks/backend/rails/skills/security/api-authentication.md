# API Authentication Patterns

Various authentication strategies for Rails APIs.

## Custom JWT Authentication (Without Devise)

### JWT Service

```ruby
# app/services/jwt_service.rb
class JwtService
  SECRET_KEY = Rails.application.credentials.secret_key_base
  ALGORITHM = 'HS256'

  class << self
    def encode(payload, exp = 24.hours.from_now)
      payload[:exp] = exp.to_i
      payload[:iat] = Time.current.to_i
      payload[:jti] = SecureRandom.uuid

      JWT.encode(payload, SECRET_KEY, ALGORITHM)
    end

    def decode(token)
      decoded = JWT.decode(token, SECRET_KEY, true, { algorithm: ALGORITHM })
      HashWithIndifferentAccess.new(decoded.first)
    rescue JWT::ExpiredSignature
      raise AuthenticationError, 'Token has expired'
    rescue JWT::DecodeError => e
      raise AuthenticationError, "Invalid token: #{e.message}"
    end

    def generate_tokens(user)
      access_token = encode(
        { user_id: user.id, type: 'access' },
        15.minutes.from_now
      )

      refresh_token = encode(
        { user_id: user.id, type: 'refresh', jti: SecureRandom.uuid },
        7.days.from_now
      )

      # Store refresh token JTI for revocation
      user.update!(refresh_token_jti: JWT.decode(refresh_token, SECRET_KEY, true).first['jti'])

      { access_token: access_token, refresh_token: refresh_token }
    end

    def refresh_access_token(refresh_token)
      payload = decode(refresh_token)

      raise AuthenticationError, 'Invalid token type' unless payload[:type] == 'refresh'

      user = User.find(payload[:user_id])

      raise AuthenticationError, 'Token revoked' unless user.refresh_token_jti == payload[:jti]

      encode({ user_id: user.id, type: 'access' }, 15.minutes.from_now)
    end
  end

  class AuthenticationError < StandardError; end
end
```

### Authentication Controller

```ruby
# app/controllers/api/v1/auth_controller.rb
module Api
  module V1
    class AuthController < ApplicationController
      skip_before_action :authenticate_user!, only: [:login, :register, :refresh]

      def register
        user = User.new(register_params)

        if user.save
          tokens = JwtService.generate_tokens(user)
          render json: {
            user: UserSerializer.new(user).serializable_hash,
            tokens: tokens
          }, status: :created
        else
          render json: { errors: user.errors.full_messages }, status: :unprocessable_entity
        end
      end

      def login
        user = User.find_by(email: login_params[:email])

        if user&.authenticate(login_params[:password])
          tokens = JwtService.generate_tokens(user)
          render json: {
            user: UserSerializer.new(user).serializable_hash,
            tokens: tokens
          }
        else
          render json: { error: 'Invalid email or password' }, status: :unauthorized
        end
      end

      def logout
        current_user.update!(refresh_token_jti: nil)
        head :no_content
      end

      def refresh
        access_token = JwtService.refresh_access_token(params[:refresh_token])
        render json: { access_token: access_token }
      rescue JwtService::AuthenticationError => e
        render json: { error: e.message }, status: :unauthorized
      end

      def me
        render json: UserSerializer.new(current_user).serializable_hash
      end

      private

      def register_params
        params.require(:user).permit(:email, :password, :password_confirmation, :name)
      end

      def login_params
        params.require(:user).permit(:email, :password)
      end
    end
  end
end
```

### Authentication Concern

```ruby
# app/controllers/concerns/authenticatable.rb
module Authenticatable
  extend ActiveSupport::Concern

  included do
    before_action :authenticate_user!
  end

  private

  def authenticate_user!
    render json: { error: 'Unauthorized' }, status: :unauthorized unless current_user
  end

  def current_user
    return @current_user if defined?(@current_user)

    @current_user = authenticate_with_token
  end

  def authenticate_with_token
    token = extract_token_from_header
    return nil unless token

    payload = JwtService.decode(token)
    return nil unless payload[:type] == 'access'

    User.find_by(id: payload[:user_id])
  rescue JwtService::AuthenticationError
    nil
  end

  def extract_token_from_header
    header = request.headers['Authorization']
    return nil unless header&.start_with?('Bearer ')

    header.split(' ').last
  end
end
```

## API Key Authentication

### API Key Model

```ruby
# app/models/api_key.rb
class ApiKey < ApplicationRecord
  belongs_to :user

  before_create :generate_key

  scope :active, -> { where(revoked_at: nil) }

  def revoke!
    update!(revoked_at: Time.current)
  end

  def revoked?
    revoked_at.present?
  end

  private

  def generate_key
    self.key = SecureRandom.hex(32)
    self.key_digest = Digest::SHA256.hexdigest(key)
  end
end

# Migration
class CreateApiKeys < ActiveRecord::Migration[7.1]
  def change
    create_table :api_keys, id: :uuid do |t|
      t.references :user, null: false, foreign_key: true, type: :uuid
      t.string :name, null: false
      t.string :key_digest, null: false
      t.datetime :last_used_at
      t.datetime :revoked_at
      t.timestamps
    end

    add_index :api_keys, :key_digest, unique: true
  end
end
```

### API Key Authentication

```ruby
# app/controllers/concerns/api_key_authenticatable.rb
module ApiKeyAuthenticatable
  extend ActiveSupport::Concern

  private

  def authenticate_with_api_key!
    render json: { error: 'Invalid API key' }, status: :unauthorized unless current_api_key
  end

  def current_api_key
    return @current_api_key if defined?(@current_api_key)

    @current_api_key = find_api_key
  end

  def current_user_from_api_key
    current_api_key&.user
  end

  def find_api_key
    key = extract_api_key
    return nil unless key

    key_digest = Digest::SHA256.hexdigest(key)
    api_key = ApiKey.active.find_by(key_digest: key_digest)

    api_key&.touch(:last_used_at)
    api_key
  end

  def extract_api_key
    # From header: X-API-Key: your_key
    request.headers['X-API-Key'] ||
      # From query param: ?api_key=your_key
      params[:api_key]
  end
end
```

## OAuth 2.0 with Doorkeeper

### Setup

```ruby
# Gemfile
gem 'doorkeeper'

# config/initializers/doorkeeper.rb
Doorkeeper.configure do
  orm :active_record

  resource_owner_authenticator do
    User.find_by(id: session[:user_id]) || redirect_to(login_url)
  end

  # For API-only apps
  resource_owner_from_credentials do |routes|
    user = User.find_by(email: params[:email])
    user if user&.authenticate(params[:password])
  end

  grant_flows %w[password client_credentials]

  access_token_expires_in 2.hours
  use_refresh_token
end
```

### OAuth Controller

```ruby
# app/controllers/api/v1/oauth_controller.rb
module Api
  module V1
    class OauthController < ApplicationController
      skip_before_action :authenticate_user!

      def token
        strategy = Doorkeeper::Request::Password.new(Doorkeeper.configuration, params)
        response = strategy.authorize

        if response.status == :ok
          render json: {
            access_token: response.token.token,
            refresh_token: response.token.refresh_token,
            token_type: 'Bearer',
            expires_in: response.token.expires_in,
            created_at: response.token.created_at.to_i
          }
        else
          render json: { error: response.body[:error_description] }, status: :unauthorized
        end
      end
    end
  end
end
```

## Multi-Factor Authentication

```ruby
# app/models/user.rb
class User < ApplicationRecord
  has_one :totp_credential, dependent: :destroy

  def mfa_enabled?
    totp_credential&.enabled?
  end

  def verify_totp(code)
    return false unless mfa_enabled?
    totp_credential.verify(code)
  end
end

# app/models/totp_credential.rb
class TotpCredential < ApplicationRecord
  belongs_to :user

  encrypts :secret

  def totp
    ROTP::TOTP.new(secret, issuer: 'MyApp')
  end

  def provisioning_uri
    totp.provisioning_uri(user.email)
  end

  def verify(code)
    totp.verify(code, drift_behind: 15, drift_ahead: 15).present?
  end

  def generate_backup_codes
    codes = 10.times.map { SecureRandom.hex(4) }
    update!(backup_codes: codes.map { |c| BCrypt::Password.create(c) })
    codes
  end
end

# app/controllers/api/v1/auth_controller.rb
def login
  user = User.find_by(email: login_params[:email])

  unless user&.authenticate(login_params[:password])
    return render json: { error: 'Invalid credentials' }, status: :unauthorized
  end

  if user.mfa_enabled?
    if params[:totp_code].present?
      unless user.verify_totp(params[:totp_code])
        return render json: { error: 'Invalid MFA code' }, status: :unauthorized
      end
    else
      return render json: { mfa_required: true }, status: :accepted
    end
  end

  tokens = JwtService.generate_tokens(user)
  render json: { user: UserSerializer.new(user), tokens: tokens }
end
```

## Rate Limiting with Rack::Attack

```ruby
# config/initializers/rack_attack.rb
class Rack::Attack
  # Throttle login attempts
  throttle('auth/login', limit: 5, period: 60.seconds) do |req|
    if req.path == '/api/v1/auth/login' && req.post?
      req.ip
    end
  end

  # Throttle API requests by IP
  throttle('api/ip', limit: 100, period: 1.minute) do |req|
    req.ip if req.path.start_with?('/api/')
  end

  # Throttle API requests by user token
  throttle('api/token', limit: 1000, period: 1.hour) do |req|
    if req.path.start_with?('/api/') && req.env['HTTP_AUTHORIZATION']
      req.env['HTTP_AUTHORIZATION']
    end
  end

  # Custom response
  self.throttled_responder = lambda do |req|
    [
      429,
      { 'Content-Type' => 'application/json' },
      [{ error: 'Rate limit exceeded. Try again later.' }.to_json]
    ]
  end
end
```

## Best Practices

1. **Use HTTPS** - Always in production
2. **Short-lived access tokens** - 15-30 minutes
3. **Secure refresh tokens** - Store securely, allow revocation
4. **Rate limit auth endpoints** - Prevent brute force
5. **Log authentication events** - For security auditing
6. **Implement MFA** - For sensitive applications
7. **Use secure password hashing** - bcrypt with proper cost
8. **Validate all inputs** - Prevent injection attacks
