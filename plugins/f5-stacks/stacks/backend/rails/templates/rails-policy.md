# Rails Policy Template

## Pundit Policy Template

```ruby
# app/policies/{{resource}}_policy.rb
class {{Resource}}Policy < ApplicationPolicy
  # === Query Methods ===
  def index?
    true
  end

  def show?
    {{SHOW_CONDITION}}
  end

  def create?
    user.present?
  end

  def update?
    owner_or_admin?
  end

  def destroy?
    owner_or_admin?
  end

  # === Custom Actions ===
  def {{custom_action}}?
    {{CUSTOM_CONDITION}}
  end

  # === Permitted Attributes ===
  def permitted_attributes
    if admin?
      [{{ADMIN_ATTRIBUTES}}]
    else
      [{{USER_ATTRIBUTES}}]
    end
  end

  def permitted_attributes_for_create
    [{{CREATE_ATTRIBUTES}}]
  end

  def permitted_attributes_for_update
    permitted_attributes
  end

  # === Scope ===
  class Scope < ApplicationPolicy::Scope
    def resolve
      if admin?
        scope.all
      elsif user.present?
        scope.where({{USER_SCOPE_CONDITION}})
      else
        scope.where({{GUEST_SCOPE_CONDITION}})
      end
    end
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
    return false unless user && record.respond_to?(:user_id)

    record.user_id == user.id
  end

  def created_by_user?
    return false unless user && record.respond_to?(:created_by_id)

    record.created_by_id == user.id
  end

  def owner_or_admin?
    admin? || owner? || created_by_user?
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

## Usage Example

For a `Product` policy:

```ruby
# app/policies/product_policy.rb
class ProductPolicy < ApplicationPolicy
  # === Query Methods ===
  def index?
    true
  end

  def show?
    # Everyone can see active products
    # Only admin/owner can see draft products
    record.status_active? || owner_or_admin?
  end

  def create?
    user.present?
  end

  def update?
    owner_or_admin?
  end

  def destroy?
    # Only admin can delete, or owner if product has no orders
    admin? || (owner_or_admin? && record.order_items.empty?)
  end

  # === Custom Actions ===
  def publish?
    owner_or_admin? && record.status_draft?
  end

  def archive?
    admin?
  end

  def duplicate?
    user.present?
  end

  def manage_inventory?
    admin? || owner_or_admin?
  end

  def view_analytics?
    admin? || owner_or_admin?
  end

  # === Permitted Attributes ===
  def permitted_attributes
    if admin?
      [:name, :description, :price, :compare_price, :status, :category_id,
       :sku, :stock_quantity, :featured, :internal_notes, :cost_price, tag_ids: []]
    else
      [:name, :description, :price, :compare_price, :category_id, tag_ids: []]
    end
  end

  def permitted_attributes_for_create
    [:name, :description, :price, :compare_price, :category_id, tag_ids: []]
  end

  # === Scope ===
  class Scope < ApplicationPolicy::Scope
    def resolve
      if admin?
        scope.all
      elsif user.present?
        # User sees all active products + their own drafts
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

  # === Order State Transitions ===
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
    admin? && record.delivered? && within_refund_period?
  end

  # === Order Item Management ===
  def add_item?
    owner_or_admin? && record.pending?
  end

  def remove_item?
    owner_or_admin? && record.pending?
  end

  def update_item_quantity?
    owner_or_admin? && record.pending?
  end

  private

  def owner?
    record.user_id == user&.id
  end

  def within_refund_period?
    record.delivered_at && record.delivered_at > 30.days.ago
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

## Role-Based Policy

```ruby
# app/policies/concerns/role_permissions.rb
module RolePermissions
  extend ActiveSupport::Concern

  ROLE_PERMISSIONS = {
    viewer: {
      can: [:index, :show],
      cannot: [:create, :update, :destroy, :admin]
    },
    editor: {
      can: [:index, :show, :create, :update],
      cannot: [:destroy, :admin]
    },
    manager: {
      can: [:index, :show, :create, :update, :destroy, :publish, :archive],
      cannot: [:admin]
    },
    admin: {
      can: [:all],
      cannot: []
    }
  }.freeze

  def can?(action)
    permissions = role_permissions
    return true if permissions[:can].include?(:all)

    permissions[:can].include?(action)
  end

  def cannot?(action)
    role_permissions[:cannot].include?(action)
  end

  private

  def role_permissions
    ROLE_PERMISSIONS[user&.role&.to_sym] || ROLE_PERMISSIONS[:viewer]
  end
end

# Usage
class ArticlePolicy < ApplicationPolicy
  include RolePermissions

  def publish?
    can?(:publish) && record.draft?
  end

  def archive?
    can?(:archive) && record.published?
  end

  def admin_edit?
    can?(:admin)
  end
end
```

## Headless Policy

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

  def user_analytics?
    admin? || user.role?(:manager)
  end
end

# Controller usage
class DashboardController < ApplicationController
  def show
    authorize :dashboard, :show?
  end

  def admin_stats
    authorize :dashboard, :admin_stats?
  end
end
```
