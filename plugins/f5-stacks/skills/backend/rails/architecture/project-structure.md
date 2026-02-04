# Rails Project Structure

Best practices for organizing Rails API applications.

## Standard Rails API Structure

```
app/
├── controllers/
│   ├── application_controller.rb
│   ├── concerns/
│   │   ├── exception_handler.rb
│   │   ├── response_handler.rb
│   │   └── pagination.rb
│   └── api/
│       └── v1/
│           ├── base_controller.rb
│           ├── users_controller.rb
│           ├── products_controller.rb
│           └── orders_controller.rb
├── models/
│   ├── application_record.rb
│   ├── concerns/
│   │   ├── soft_deletable.rb
│   │   ├── searchable.rb
│   │   └── has_uuid.rb
│   ├── user.rb
│   ├── product.rb
│   └── order.rb
├── serializers/
│   ├── user_serializer.rb
│   ├── product_serializer.rb
│   └── order_serializer.rb
├── services/
│   ├── result.rb
│   ├── users/
│   │   ├── create_user.rb
│   │   └── update_user.rb
│   ├── products/
│   │   └── create_product.rb
│   └── orders/
│       ├── create_order.rb
│       └── process_order.rb
├── policies/
│   ├── application_policy.rb
│   ├── user_policy.rb
│   ├── product_policy.rb
│   └── order_policy.rb
├── queries/
│   ├── products_query.rb
│   └── orders_query.rb
├── jobs/
│   ├── application_job.rb
│   └── send_notification_job.rb
├── mailers/
│   ├── application_mailer.rb
│   └── user_mailer.rb
└── validators/
    └── email_validator.rb

config/
├── application.rb
├── routes.rb
├── database.yml
├── environments/
│   ├── development.rb
│   ├── production.rb
│   └── test.rb
└── initializers/
    ├── cors.rb
    ├── devise.rb
    ├── sidekiq.rb
    └── inflections.rb

db/
├── migrate/
├── schema.rb
├── seeds.rb
└── seeds/
    ├── users.rb
    └── products.rb

lib/
└── tasks/
    └── maintenance.rake

spec/
├── rails_helper.rb
├── spec_helper.rb
├── support/
│   ├── auth_helpers.rb
│   ├── request_helpers.rb
│   └── factory_bot.rb
├── factories/
│   ├── users.rb
│   ├── products.rb
│   └── orders.rb
├── models/
├── requests/
│   └── api/
│       └── v1/
├── services/
└── policies/
```

## Application Controller

```ruby
# app/controllers/application_controller.rb
class ApplicationController < ActionController::API
  include Pundit::Authorization
  include ExceptionHandler
  include ResponseHandler
  include Pagination

  before_action :authenticate_user!

  private

  def current_user
    @current_user ||= warden.authenticate(scope: :user)
  end

  def authenticate_user!
    head :unauthorized unless current_user
  end
end
```

## Base API Controller

```ruby
# app/controllers/api/v1/base_controller.rb
module Api
  module V1
    class BaseController < ApplicationController
      # Version-specific configurations
      rescue_from ActiveRecord::RecordNotFound, with: :not_found
      rescue_from Pundit::NotAuthorizedError, with: :forbidden

      private

      def not_found
        render json: { error: 'Resource not found' }, status: :not_found
      end

      def forbidden
        render json: { error: 'Not authorized' }, status: :forbidden
      end
    end
  end
end
```

## Exception Handler Concern

```ruby
# app/controllers/concerns/exception_handler.rb
module ExceptionHandler
  extend ActiveSupport::Concern

  included do
    rescue_from StandardError do |e|
      handle_error(e)
    end

    rescue_from ActiveRecord::RecordNotFound do |e|
      render json: { error: 'Resource not found' }, status: :not_found
    end

    rescue_from ActiveRecord::RecordInvalid do |e|
      render json: { errors: e.record.errors.full_messages }, status: :unprocessable_entity
    end

    rescue_from Pundit::NotAuthorizedError do |e|
      render json: { error: 'Not authorized to perform this action' }, status: :forbidden
    end

    rescue_from ActionController::ParameterMissing do |e|
      render json: { error: "Missing parameter: #{e.param}" }, status: :bad_request
    end
  end

  private

  def handle_error(error)
    Rails.logger.error("#{error.class}: #{error.message}")
    Rails.logger.error(error.backtrace.first(10).join("\n"))

    if Rails.env.development?
      render json: {
        error: error.message,
        backtrace: error.backtrace.first(10)
      }, status: :internal_server_error
    else
      render json: { error: 'Internal server error' }, status: :internal_server_error
    end
  end
end
```

## Pagination Concern

```ruby
# app/controllers/concerns/pagination.rb
module Pagination
  extend ActiveSupport::Concern

  def paginate(collection)
    collection
      .page(params[:page] || 1)
      .per(per_page)
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
        total_count: collection.total_count,
        per_page: collection.limit_value
      }
    }
  end

  def pagination_links(collection, base_url)
    {
      links: {
        self: "#{base_url}?page=#{collection.current_page}",
        first: "#{base_url}?page=1",
        last: "#{base_url}?page=#{collection.total_pages}",
        next: collection.next_page ? "#{base_url}?page=#{collection.next_page}" : nil,
        prev: collection.prev_page ? "#{base_url}?page=#{collection.prev_page}" : nil
      }
    }
  end
end
```

## Application Record

```ruby
# app/models/application_record.rb
class ApplicationRecord < ActiveRecord::Base
  primary_abstract_class

  # Use UUID as primary key
  # Note: Requires enabling uuid-ossp extension in PostgreSQL
  # self.implicit_order_column = 'created_at'
end
```

## Routes Structure

```ruby
# config/routes.rb
Rails.application.routes.draw do
  # Health check
  get '/health', to: proc { [200, {}, ['OK']] }

  # API routes
  namespace :api do
    namespace :v1 do
      # Authentication
      devise_for :users,
        path: '',
        path_names: {
          sign_in: 'login',
          sign_out: 'logout',
          registration: 'signup'
        },
        controllers: {
          sessions: 'api/v1/sessions',
          registrations: 'api/v1/registrations'
        }

      # Resources
      resources :users, only: [:index, :show, :update]
      resources :products
      resources :categories, only: [:index, :show]
      resources :orders do
        member do
          post :confirm
          post :cancel
        end
      end

      # Nested resources
      resources :products do
        resources :reviews, only: [:index, :create]
      end
    end

    # Future API versions
    # namespace :v2 do
    # end
  end

  # Sidekiq Web UI (admin only)
  require 'sidekiq/web'
  authenticate :user, ->(user) { user.admin? } do
    mount Sidekiq::Web => '/sidekiq'
  end
end
```

## Directory Purposes

| Directory | Purpose |
|-----------|---------|
| `controllers/` | Request handling, routing to services |
| `models/` | Data structures, validations, associations |
| `serializers/` | JSON response formatting |
| `services/` | Business logic, complex operations |
| `policies/` | Authorization rules (Pundit) |
| `queries/` | Complex query objects |
| `jobs/` | Background processing (Sidekiq) |
| `mailers/` | Email templates and sending |
| `validators/` | Custom validation classes |

## Best Practices

1. **Keep controllers thin** - Delegate to services
2. **Use concerns** for shared model behavior
3. **Organize by domain** in services directory
4. **Version APIs** from the start
5. **Separate concerns** - Each class has one responsibility
