# Rails Service Objects

Encapsulate business logic in service objects for cleaner architecture.

## Why Service Objects?

- **Thin Controllers**: Move business logic out of controllers
- **Thin Models**: Keep models focused on persistence
- **Testability**: Easy to test in isolation
- **Reusability**: Share logic across controllers, jobs, etc.
- **Single Responsibility**: Each service does one thing

## Basic Service Object

```ruby
# app/services/users/create_user.rb
module Users
  class CreateUser
    def initialize(params:, current_user: nil)
      @params = params
      @current_user = current_user
    end

    def call
      user = User.new(user_params)

      ActiveRecord::Base.transaction do
        user.save!
        send_welcome_email(user)
        track_signup(user)
      end

      Result.success(user)
    rescue ActiveRecord::RecordInvalid => e
      Result.failure(e.record.errors.full_messages)
    rescue StandardError => e
      Rails.logger.error("CreateUser failed: #{e.message}")
      Result.failure(['Unable to create user'])
    end

    private

    attr_reader :params, :current_user

    def user_params
      params.slice(:email, :name, :password, :password_confirmation)
    end

    def send_welcome_email(user)
      UserMailer.welcome(user).deliver_later
    end

    def track_signup(user)
      Analytics.track(
        user_id: user.id,
        event: 'User Signed Up',
        properties: { source: params[:source] }
      )
    end
  end
end
```

## Result Object Pattern

```ruby
# app/services/result.rb
class Result
  attr_reader :data, :errors

  def initialize(success:, data: nil, errors: nil)
    @success = success
    @data = data
    @errors = errors || []
  end

  def success?
    @success
  end

  def failure?
    !@success
  end

  def self.success(data = nil)
    new(success: true, data: data)
  end

  def self.failure(errors)
    new(success: false, errors: Array(errors))
  end

  # Chainable callbacks
  def on_success
    yield(data) if success?
    self
  end

  def on_failure
    yield(errors) if failure?
    self
  end

  # Monadic operations
  def and_then
    return self if failure?
    yield(data)
  end

  def map
    return self if failure?
    Result.success(yield(data))
  end

  def or_else
    return self if success?
    yield(errors)
  end

  # Convert to hash for JSON
  def to_h
    if success?
      { success: true, data: data }
    else
      { success: false, errors: errors }
    end
  end
end
```

## Controller Usage

```ruby
# app/controllers/api/v1/users_controller.rb
module Api
  module V1
    class UsersController < BaseController
      def create
        result = Users::CreateUser.new(
          params: user_params,
          current_user: current_user
        ).call

        result
          .on_success { |user| render json: UserSerializer.new(user), status: :created }
          .on_failure { |errors| render json: { errors: errors }, status: :unprocessable_entity }
      end

      private

      def user_params
        params.require(:user).permit(:email, :name, :password, :password_confirmation)
      end
    end
  end
end
```

## Complex Service with Steps

```ruby
# app/services/orders/process_order.rb
module Orders
  class ProcessOrder
    def initialize(order:, payment_params:, current_user:)
      @order = order
      @payment_params = payment_params
      @current_user = current_user
      @errors = []
    end

    def call
      ActiveRecord::Base.transaction do
        validate_order!
        reserve_inventory!
        process_payment!
        confirm_order!
        schedule_fulfillment!

        Result.success(order.reload)
      end
    rescue ValidationError => e
      Result.failure([e.message])
    rescue InsufficientInventoryError => e
      Result.failure(["Insufficient inventory: #{e.message}"])
    rescue PaymentError => e
      release_inventory!
      Result.failure(["Payment failed: #{e.message}"])
    rescue StandardError => e
      Rails.logger.error("ProcessOrder failed: #{e.message}")
      Rails.logger.error(e.backtrace.join("\n"))
      Result.failure(['Unable to process order'])
    end

    private

    attr_reader :order, :payment_params, :current_user

    def validate_order!
      raise ValidationError, 'Order already processed' if order.processed?
      raise ValidationError, 'Order is empty' if order.items.empty?
      raise ValidationError, 'Order has expired' if order.expired?
      raise ValidationError, 'Not authorized' unless order.user == current_user
    end

    def reserve_inventory!
      @reserved_items = []

      order.items.each do |item|
        result = Inventory::ReserveStock.new(
          product: item.product,
          quantity: item.quantity,
          order: order
        ).call

        if result.failure?
          release_inventory!
          raise InsufficientInventoryError, item.product.name
        end

        @reserved_items << item
      end
    end

    def process_payment!
      result = Payments::ChargeCard.new(
        amount: order.total,
        token: payment_params[:token],
        order: order
      ).call

      raise PaymentError, result.errors.join(', ') if result.failure?

      @payment = result.data
    end

    def confirm_order!
      order.update!(
        status: :confirmed,
        confirmed_at: Time.current,
        payment_id: @payment.id
      )
    end

    def schedule_fulfillment!
      FulfillOrderJob.perform_later(order.id)
      OrderMailer.confirmation(order).deliver_later
    end

    def release_inventory!
      return unless @reserved_items

      @reserved_items.each do |item|
        Inventory::ReleaseStock.new(
          product: item.product,
          quantity: item.quantity,
          order: order
        ).call
      end
    end
  end

  class ValidationError < StandardError; end
  class InsufficientInventoryError < StandardError; end
  class PaymentError < StandardError; end
end
```

## Service with Dependencies

```ruby
# app/services/notifications/send_notification.rb
module Notifications
  class SendNotification
    def initialize(user:, message:, channel: :email, notifier: nil)
      @user = user
      @message = message
      @channel = channel
      @notifier = notifier || default_notifier
    end

    def call
      validate_user!

      @notifier.deliver(
        to: user,
        message: message
      )

      Result.success(message: 'Notification sent')
    rescue NotifierError => e
      Result.failure([e.message])
    end

    private

    attr_reader :user, :message, :channel, :notifier

    def validate_user!
      raise ValidationError, 'User has no contact method' unless user.contactable?
    end

    def default_notifier
      case channel
      when :email
        EmailNotifier.new
      when :sms
        SmsNotifier.new
      when :push
        PushNotifier.new
      else
        raise ArgumentError, "Unknown channel: #{channel}"
      end
    end
  end
end
```

## Composing Services

```ruby
# app/services/users/onboard_user.rb
module Users
  class OnboardUser
    def initialize(params:)
      @params = params
    end

    def call
      # Chain services together
      Users::CreateUser.new(params: params).call
        .and_then { |user| Users::SetupProfile.new(user: user, params: params).call }
        .and_then { |user| Users::SendWelcomeEmail.new(user: user).call }
        .and_then { |user| Users::TrackSignup.new(user: user, source: params[:source]).call }
    end

    private

    attr_reader :params
  end
end
```

## Service Testing

```ruby
# spec/services/orders/process_order_spec.rb
require 'rails_helper'

RSpec.describe Orders::ProcessOrder do
  let(:user) { create(:user) }
  let(:order) { create(:order, :with_items, user: user) }
  let(:payment_params) { { token: 'valid_token' } }

  subject do
    described_class.new(
      order: order,
      payment_params: payment_params,
      current_user: user
    ).call
  end

  describe '#call' do
    context 'when successful' do
      before do
        allow_any_instance_of(Payments::ChargeCard)
          .to receive(:call)
          .and_return(Result.success(build(:payment)))
      end

      it 'returns success' do
        expect(subject).to be_success
      end

      it 'confirms the order' do
        subject
        expect(order.reload).to be_confirmed
      end

      it 'schedules fulfillment job' do
        expect { subject }.to have_enqueued_job(FulfillOrderJob)
      end

      it 'sends confirmation email' do
        expect { subject }.to have_enqueued_mail(OrderMailer, :confirmation)
      end
    end

    context 'when order already processed' do
      let(:order) { create(:order, :confirmed) }

      it 'returns failure' do
        expect(subject).to be_failure
        expect(subject.errors).to include(/already processed/)
      end
    end

    context 'when payment fails' do
      before do
        allow_any_instance_of(Payments::ChargeCard)
          .to receive(:call)
          .and_return(Result.failure(['Card declined']))
      end

      it 'returns failure' do
        expect(subject).to be_failure
        expect(subject.errors).to include(/Payment failed/)
      end

      it 'releases reserved inventory' do
        expect_any_instance_of(Inventory::ReleaseStock).to receive(:call)
        subject
      end

      it 'does not confirm the order' do
        subject
        expect(order.reload).not_to be_confirmed
      end
    end
  end
end
```

## Best Practices

1. **Single Responsibility** - One service, one operation
2. **Use Result Objects** - Explicit success/failure
3. **Inject Dependencies** - For testability
4. **Handle Errors Gracefully** - Don't let exceptions bubble up
5. **Log Important Events** - For debugging
6. **Use Transactions** - For multi-step operations
7. **Keep Services Composable** - Chain small services together
