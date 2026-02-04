# Rails Service Template

## Service Object Template

```ruby
# app/services/{{resource}}_service.rb
class {{Resource}}Service
  attr_reader :{{resource}}, :params, :current_user

  def initialize({{resource}} = nil, params: {}, current_user: nil)
    @{{resource}} = {{resource}}
    @params = params
    @current_user = current_user
  end

  def {{action}}
    return Result.failure('{{Resource}} not found') unless {{resource}}

    {{Resource}}.transaction do
      # Business logic here
      {{resource}}.{{method}}!
      notify_users
      log_activity
    end

    Result.success({{resource}})
  rescue ActiveRecord::RecordInvalid => e
    Result.failure(e.record.errors.full_messages)
  rescue StandardError => e
    Rails.logger.error "{{Resource}}Service#{{action}} failed: #{e.message}"
    Result.failure('An unexpected error occurred')
  end

  private

  def notify_users
    {{Resource}}NotificationJob.perform_async({{resource}}.id)
  end

  def log_activity
    Activity.create!(
      trackable: {{resource}},
      owner: current_user,
      action: '{{action}}'
    )
  end
end
```

## Result Class

```ruby
# app/services/result.rb
class Result
  attr_reader :data, :errors

  def initialize(success:, data: nil, errors: [])
    @success = success
    @data = data
    @errors = Array(errors)
  end

  def self.success(data = nil)
    new(success: true, data: data)
  end

  def self.failure(errors)
    new(success: false, errors: errors)
  end

  def success?
    @success
  end

  def failure?
    !@success
  end

  def on_success
    yield(data) if success?
    self
  end

  def on_failure
    yield(errors) if failure?
    self
  end
end
```

## Usage Example

For an Order service:

```ruby
# app/services/orders/create_order_service.rb
module Orders
  class CreateOrderService
    attr_reader :user, :cart, :params

    def initialize(user:, cart:, params: {})
      @user = user
      @cart = cart
      @params = params
    end

    def call
      return Result.failure('Cart is empty') if cart.empty?
      return Result.failure('User not verified') unless user.verified?

      order = nil

      Order.transaction do
        order = create_order
        create_order_items(order)
        apply_discount(order) if params[:discount_code].present?
        calculate_totals(order)
        reserve_inventory(order)
        order.save!
        clear_cart
      end

      notify_order_created(order)
      Result.success(order)
    rescue ActiveRecord::RecordInvalid => e
      Result.failure(e.record.errors.full_messages)
    rescue InsufficientInventoryError => e
      Result.failure(e.message)
    rescue StandardError => e
      Rails.logger.error "CreateOrderService failed: #{e.message}"
      Result.failure('Failed to create order')
    end

    private

    def create_order
      Order.new(
        user: user,
        order_number: generate_order_number,
        status: :pending,
        shipping_address: params[:shipping_address],
        billing_address: params[:billing_address] || params[:shipping_address]
      )
    end

    def create_order_items(order)
      cart.items.each do |cart_item|
        order.items.build(
          product: cart_item.product,
          quantity: cart_item.quantity,
          unit_price: cart_item.product.price
        )
      end
    end

    def apply_discount(order)
      discount = Discount.active.find_by(code: params[:discount_code])
      return unless discount&.applicable?(order)

      order.discount = discount
      order.discount_amount = discount.calculate(order)
    end

    def calculate_totals(order)
      order.subtotal = order.items.sum { |item| item.quantity * item.unit_price }
      order.tax = TaxCalculator.calculate(order)
      order.shipping = ShippingCalculator.calculate(order)
      order.total = order.subtotal + order.tax + order.shipping - order.discount_amount.to_f
    end

    def reserve_inventory(order)
      order.items.each do |item|
        InventoryService.reserve(item.product, item.quantity)
      end
    end

    def clear_cart
      cart.clear!
    end

    def notify_order_created(order)
      OrderNotificationJob.perform_async(order.id)
      AdminNotificationJob.perform_async('new_order', order.id)
    end

    def generate_order_number
      "ORD-#{Time.current.strftime('%Y%m%d')}-#{SecureRandom.hex(4).upcase}"
    end
  end
end

# Controller usage
class OrdersController < ApplicationController
  def create
    result = Orders::CreateOrderService.new(
      user: current_user,
      cart: current_cart,
      params: order_params
    ).call

    if result.success?
      render json: OrderSerializer.new(result.data), status: :created
    else
      render json: { errors: result.errors }, status: :unprocessable_entity
    end
  end
end
```

## Process Service (Multi-step)

```ruby
# app/services/orders/process_order_service.rb
module Orders
  class ProcessOrderService
    attr_reader :order

    def initialize(order)
      @order = order
    end

    def call
      return Result.failure('Order cannot be processed') unless order.pending?

      Order.transaction do
        validate_inventory!
        charge_payment!
        confirm_order!
        send_confirmation!
      end

      Result.success(order.reload)
    rescue PaymentError => e
      order.fail!(e.message)
      Result.failure("Payment failed: #{e.message}")
    rescue InventoryError => e
      order.fail!(e.message)
      Result.failure("Inventory error: #{e.message}")
    rescue StandardError => e
      Rails.logger.error "ProcessOrderService failed: #{e.message}"
      order.fail!('Processing error')
      Result.failure('Failed to process order')
    end

    private

    def validate_inventory!
      order.items.each do |item|
        unless InventoryService.available?(item.product, item.quantity)
          raise InventoryError, "#{item.product.name} is out of stock"
        end
      end
    end

    def charge_payment!
      result = PaymentService.charge(
        amount: order.total,
        source: order.payment_method,
        metadata: { order_id: order.id }
      )

      raise PaymentError, result.error unless result.success?

      order.update!(
        payment_intent_id: result.data[:payment_intent_id],
        paid_at: Time.current
      )
    end

    def confirm_order!
      order.items.each do |item|
        InventoryService.deduct(item.product, item.quantity)
      end

      order.update!(
        status: :confirmed,
        confirmed_at: Time.current
      )
    end

    def send_confirmation!
      OrderMailer.confirmation(order).deliver_later
      OrderNotificationJob.perform_async(order.id, 'confirmed')
    end
  end
end
```

## Query Service

```ruby
# app/services/products/search_service.rb
module Products
  class SearchService
    attr_reader :params

    def initialize(params)
      @params = params
    end

    def call
      products = Product.active

      products = filter_by_category(products)
      products = filter_by_price(products)
      products = filter_by_tags(products)
      products = search_query(products)
      products = apply_sorting(products)

      Result.success(products)
    end

    private

    def filter_by_category(scope)
      return scope unless params[:category_id].present?

      scope.where(category_id: params[:category_id])
    end

    def filter_by_price(scope)
      scope = scope.where('price >= ?', params[:min_price]) if params[:min_price].present?
      scope = scope.where('price <= ?', params[:max_price]) if params[:max_price].present?
      scope
    end

    def filter_by_tags(scope)
      return scope unless params[:tag_ids].present?

      scope.joins(:tags).where(tags: { id: params[:tag_ids] }).distinct
    end

    def search_query(scope)
      return scope unless params[:q].present?

      scope.search(params[:q])
    end

    def apply_sorting(scope)
      case params[:sort]
      when 'price_asc'
        scope.order(price: :asc)
      when 'price_desc'
        scope.order(price: :desc)
      when 'newest'
        scope.order(created_at: :desc)
      when 'popular'
        scope.order(views_count: :desc)
      else
        scope.order(created_at: :desc)
      end
    end
  end
end
```

## External API Service

```ruby
# app/services/stripe_service.rb
class StripeService
  class << self
    def create_customer(user)
      customer = Stripe::Customer.create(
        email: user.email,
        name: user.name,
        metadata: { user_id: user.id }
      )

      Result.success(customer)
    rescue Stripe::StripeError => e
      Rails.logger.error "Stripe create_customer failed: #{e.message}"
      Result.failure(e.message)
    end

    def charge(amount:, source:, metadata: {})
      payment_intent = Stripe::PaymentIntent.create(
        amount: (amount * 100).to_i,
        currency: 'usd',
        payment_method: source,
        confirm: true,
        metadata: metadata
      )

      Result.success(payment_intent_id: payment_intent.id)
    rescue Stripe::CardError => e
      Result.failure(e.message)
    rescue Stripe::StripeError => e
      Rails.logger.error "Stripe charge failed: #{e.message}"
      Result.failure('Payment processing failed')
    end

    def refund(payment_intent_id:, amount: nil)
      params = { payment_intent: payment_intent_id }
      params[:amount] = (amount * 100).to_i if amount

      refund = Stripe::Refund.create(params)

      Result.success(refund_id: refund.id)
    rescue Stripe::StripeError => e
      Rails.logger.error "Stripe refund failed: #{e.message}"
      Result.failure(e.message)
    end
  end
end
```
