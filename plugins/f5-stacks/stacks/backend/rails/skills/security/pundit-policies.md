# Pundit Authorization Policies

Role-based access control with Pundit in Rails applications.

## Setup

```ruby
# Gemfile
gem 'pundit'

# app/controllers/application_controller.rb
class ApplicationController < ActionController::API
  include Pundit::Authorization

  rescue_from Pundit::NotAuthorizedError, with: :handle_unauthorized

  private

  def handle_unauthorized
    render json: { error: 'Not authorized to perform this action' }, status: :forbidden
  end
end
```

## Application Policy

```ruby
# app/policies/application_policy.rb
class ApplicationPolicy
  attr_reader :user, :record

  def initialize(user, record)
    @user = user
    @record = record
  end

  def index?
    true
  end

  def show?
    true
  end

  def create?
    user.present?
  end

  def new?
    create?
  end

  def update?
    owner_or_admin?
  end

  def edit?
    update?
  end

  def destroy?
    owner_or_admin?
  end

  private

  def admin?
    user&.admin?
  end

  def owner?
    record.respond_to?(:user_id) && record.user_id == user&.id
  end

  def owner_or_admin?
    admin? || owner?
  end

  class Scope
    def initialize(user, scope)
      @user = user
      @scope = scope
    end

    def resolve
      raise NotImplementedError, "You must define #resolve in #{self.class}"
    end

    private

    attr_reader :user, :scope

    def admin?
      user&.admin?
    end
  end
end
```

## Resource Policy

```ruby
# app/policies/product_policy.rb
class ProductPolicy < ApplicationPolicy
  def index?
    true
  end

  def show?
    # Everyone can see active products
    # Only admin/owner can see draft products
    record.active? || owner_or_admin?
  end

  def create?
    user.present?
  end

  def update?
    owner_or_admin?
  end

  def destroy?
    # Only admin can delete, or owner if product has no orders
    admin? || (owner? && record.orders.empty?)
  end

  def publish?
    owner_or_admin? && record.draft?
  end

  def archive?
    admin?
  end

  # Permitted attributes for different actions
  def permitted_attributes
    if admin?
      [:name, :description, :price, :compare_price, :category_id, :status, :is_featured, tag_ids: []]
    else
      [:name, :description, :price, :compare_price, :category_id, tag_ids: []]
    end
  end

  def permitted_attributes_for_create
    [:name, :description, :price, :compare_price, :category_id, tag_ids: []]
  end

  def permitted_attributes_for_update
    permitted_attributes
  end

  class Scope < ApplicationPolicy::Scope
    def resolve
      if admin?
        scope.all
      elsif user.present?
        # User sees all active + their own drafts
        scope.where(status: :active)
             .or(scope.where(created_by_id: user.id))
      else
        # Anonymous sees only active
        scope.where(status: :active)
      end
    end
  end
end
```

## Order Policy (Complex Example)

```ruby
# app/policies/order_policy.rb
class OrderPolicy < ApplicationPolicy
  def index?
    user.present?
  end

  def show?
    owner? || admin?
  end

  def create?
    user.present?
  end

  def update?
    return false unless owner_or_admin?
    return false if record.completed? || record.cancelled?
    true
  end

  def destroy?
    admin? && record.pending?
  end

  def confirm?
    owner_or_admin? && record.pending?
  end

  def cancel?
    return true if admin?
    owner? && %w[pending processing].include?(record.status)
  end

  def ship?
    admin? && record.confirmed?
  end

  def deliver?
    admin? && record.shipped?
  end

  def refund?
    admin? && record.delivered?
  end

  class Scope < ApplicationPolicy::Scope
    def resolve
      if admin?
        scope.all
      else
        scope.where(user_id: user.id)
      end
    end
  end
end
```

## Using Policies in Controllers

```ruby
# app/controllers/api/v1/products_controller.rb
module Api
  module V1
    class ProductsController < BaseController
      def index
        # Use policy scope to filter records
        @products = policy_scope(Product)
                    .includes(:category)
                    .page(params[:page])

        render json: ProductSerializer.new(@products)
      end

      def show
        @product = Product.find(params[:id])
        authorize @product

        render json: ProductSerializer.new(@product)
      end

      def create
        @product = Product.new(permitted_attributes(Product))
        @product.created_by = current_user

        authorize @product

        if @product.save
          render json: ProductSerializer.new(@product), status: :created
        else
          render json: { errors: @product.errors }, status: :unprocessable_entity
        end
      end

      def update
        @product = Product.find(params[:id])
        authorize @product

        if @product.update(permitted_attributes(@product))
          render json: ProductSerializer.new(@product)
        else
          render json: { errors: @product.errors }, status: :unprocessable_entity
        end
      end

      def destroy
        @product = Product.find(params[:id])
        authorize @product

        @product.destroy!
        head :no_content
      end

      def publish
        @product = Product.find(params[:id])
        authorize @product

        @product.publish!
        render json: ProductSerializer.new(@product)
      end
    end
  end
end
```

## Headless Policy (Non-Record Actions)

```ruby
# app/policies/dashboard_policy.rb
class DashboardPolicy < ApplicationPolicy
  def initialize(user, _record = nil)
    @user = user
  end

  def show?
    user.present?
  end

  def admin_stats?
    admin?
  end

  def export?
    admin?
  end
end

# Controller usage
class DashboardController < ApplicationController
  def show
    authorize :dashboard, :show?
    # ...
  end

  def admin_stats
    authorize :dashboard, :admin_stats?
    # ...
  end
end
```

## Role-Based Permissions

```ruby
# app/policies/concerns/role_permissions.rb
module RolePermissions
  extend ActiveSupport::Concern

  ROLES = {
    user: {
      can: [:read, :create_own],
      cannot: [:admin_actions, :delete_others]
    },
    moderator: {
      can: [:read, :create, :update, :moderate],
      cannot: [:delete, :admin_actions]
    },
    admin: {
      can: [:all],
      cannot: []
    }
  }.freeze

  def can?(action)
    role_permissions[:can].include?(:all) ||
      role_permissions[:can].include?(action)
  end

  def cannot?(action)
    role_permissions[:cannot].include?(action)
  end

  private

  def role_permissions
    ROLES[user&.role&.to_sym] || ROLES[:user]
  end
end

# Usage in policy
class CommentPolicy < ApplicationPolicy
  include RolePermissions

  def moderate?
    can?(:moderate)
  end
end
```

## Testing Policies

```ruby
# spec/policies/product_policy_spec.rb
require 'rails_helper'

RSpec.describe ProductPolicy, type: :policy do
  let(:user) { create(:user) }
  let(:admin) { create(:user, :admin) }
  let(:product) { create(:product, created_by: user) }
  let(:other_product) { create(:product) }

  subject { described_class }

  permissions :show? do
    context 'active product' do
      let(:product) { create(:product, status: :active) }

      it 'permits everyone' do
        expect(subject).to permit(nil, product)
        expect(subject).to permit(user, product)
        expect(subject).to permit(admin, product)
      end
    end

    context 'draft product' do
      let(:product) { create(:product, status: :draft, created_by: user) }

      it 'denies anonymous users' do
        expect(subject).not_to permit(nil, product)
      end

      it 'permits owner' do
        expect(subject).to permit(user, product)
      end

      it 'permits admin' do
        expect(subject).to permit(admin, product)
      end

      it 'denies other users' do
        expect(subject).not_to permit(create(:user), product)
      end
    end
  end

  permissions :update? do
    it 'permits owner' do
      expect(subject).to permit(user, product)
    end

    it 'permits admin' do
      expect(subject).to permit(admin, other_product)
    end

    it 'denies non-owner' do
      expect(subject).not_to permit(create(:user), product)
    end
  end

  permissions :destroy? do
    context 'product without orders' do
      it 'permits owner' do
        expect(subject).to permit(user, product)
      end

      it 'permits admin' do
        expect(subject).to permit(admin, product)
      end
    end

    context 'product with orders' do
      before { create(:order_item, product: product) }

      it 'denies owner' do
        expect(subject).not_to permit(user, product)
      end

      it 'permits admin' do
        expect(subject).to permit(admin, product)
      end
    end
  end

  describe ProductPolicy::Scope do
    subject { described_class.new(user, Product).resolve }

    let!(:active_product) { create(:product, status: :active) }
    let!(:draft_product) { create(:product, status: :draft, created_by: user) }
    let!(:other_draft) { create(:product, status: :draft) }

    context 'as regular user' do
      it 'includes active products' do
        expect(subject).to include(active_product)
      end

      it 'includes own draft products' do
        expect(subject).to include(draft_product)
      end

      it 'excludes other drafts' do
        expect(subject).not_to include(other_draft)
      end
    end

    context 'as admin' do
      subject { described_class.new(admin, Product).resolve }

      it 'includes all products' do
        expect(subject).to include(active_product, draft_product, other_draft)
      end
    end
  end
end
```

## Best Practices

1. **Keep policies focused** - One policy per resource
2. **Use scopes** - Filter records based on user permissions
3. **Use permitted_attributes** - Whitelist attributes per role
4. **Test thoroughly** - Every permission path should be tested
5. **Fail secure** - Default to denying access
6. **Use meaningful method names** - `publish?`, `archive?` not just CRUD
7. **Document complex rules** - Add comments for business logic
