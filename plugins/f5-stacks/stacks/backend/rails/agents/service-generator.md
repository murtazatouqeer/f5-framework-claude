# Rails Service Generator Agent

Agent for generating service objects that encapsulate business logic.

## Capabilities

- Generate service objects with Result pattern
- Handle complex business operations
- Implement transaction handling
- Create step-by-step workflows
- Generate related specs

## Input Schema

```yaml
service_name: string     # Full service name (e.g., "Users::CreateUser")
domain: string           # Domain namespace (e.g., "Users")
action: string          # Action name (e.g., "CreateUser")
dependencies: array      # Constructor dependencies
steps: array            # Operation steps
transaction: boolean    # Wrap in transaction
async_jobs: array       # Background jobs to trigger
notifications: array    # Notifications to send
```

## Example Usage

```yaml
service_name: Orders::ProcessOrder
domain: Orders
action: ProcessOrder
dependencies:
  - name: order
    type: Order
  - name: payment_params
    type: Hash
steps:
  - validate_order
  - reserve_inventory
  - process_payment
  - confirm_order
  - send_confirmation
transaction: true
async_jobs:
  - GenerateInvoiceJob
  - NotifyWarehouseJob
notifications:
  - email: OrderMailer.confirmation
```

## Generated Code Template

```ruby
# app/services/{{domain_lower}}/{{action_lower}}.rb
module {{Domain}}
  class {{Action}}
    def initialize({{constructor_params}})
      {{instance_assignments}}
    end

    def call
      ActiveRecord::Base.transaction do
        {{#steps}}
        {{step_name}}!
        {{/steps}}

        Result.success({{return_value}})
      end
    rescue ValidationError => e
      Result.failure(e.message)
    rescue PaymentError => e
      rollback_operations!
      Result.failure("Payment failed: #{e.message}")
    rescue StandardError => e
      Rails.logger.error("{{Action}} failed: #{e.message}")
      Rails.logger.error(e.backtrace.join("\n"))
      Result.failure("Unable to process request")
    end

    private

    attr_reader {{attr_readers}}

    {{#steps}}
    def {{step_name}}!
      # Implementation
    end
    {{/steps}}

    def rollback_operations!
      # Rollback logic
    end
  end
end
```

## Complete Example - Order Processing

```ruby
# app/services/orders/process_order.rb
module Orders
  class ProcessOrder
    def initialize(order:, payment_params:, current_user:)
      @order = order
      @payment_params = payment_params
      @current_user = current_user
    end

    def call
      ActiveRecord::Base.transaction do
        validate_order!
        validate_user_permissions!
        reserve_inventory!
        process_payment!
        confirm_order!
        schedule_jobs!

        Result.success(order.reload)
      end
    rescue ValidationError => e
      Result.failure(e.message)
    rescue InsufficientInventoryError => e
      Result.failure("Insufficient inventory: #{e.message}")
    rescue PaymentError => e
      release_reserved_inventory!
      Result.failure("Payment failed: #{e.message}")
    rescue StandardError => e
      Rails.logger.error("ProcessOrder failed: #{e.message}")
      Rails.logger.error(e.backtrace.join("\n"))
      Result.failure("Unable to process order")
    end

    private

    attr_reader :order, :payment_params, :current_user

    def validate_order!
      raise ValidationError, "Order already processed" if order.processed?
      raise ValidationError, "Order is empty" if order.items.empty?
      raise ValidationError, "Order expired" if order.expired?
    end

    def validate_user_permissions!
      raise ValidationError, "Not authorized" unless order.user == current_user
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
          release_reserved_inventory!
          raise InsufficientInventoryError, "#{item.product.name}: #{result.errors.join(', ')}"
        end

        @reserved_items << item
      end
    end

    def process_payment!
      result = Payments::ProcessPayment.new(
        order: order,
        amount: order.total,
        params: payment_params,
        user: current_user
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

      OrderMailer.confirmation(order).deliver_later
    end

    def schedule_jobs!
      GenerateInvoiceJob.perform_later(order.id)
      NotifyWarehouseJob.perform_later(order.id)
      UpdateAnalyticsJob.perform_later(order.id)
    end

    def release_reserved_inventory!
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
end
```

## Result Object

```ruby
# app/services/result.rb
class Result
  attr_reader :data, :errors

  def initialize(success:, data: nil, errors: nil)
    @success = success
    @data = data
    @errors = errors
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

  def on_success
    yield(data) if success?
    self
  end

  def on_failure
    yield(errors) if failure?
    self
  end

  def and_then
    return self if failure?
    yield(data)
  end

  def map
    return self if failure?
    Result.success(yield(data))
  end
end
```

## Service Spec Template

```ruby
# spec/services/{{domain_lower}}/{{action_lower}}_spec.rb
require 'rails_helper'

RSpec.describe {{Domain}}::{{Action}} do
  let(:user) { create(:user) }
  let(:order) { create(:order, :with_items, user: user) }
  let(:payment_params) { { token: 'valid_token' } }

  describe '#call' do
    subject do
      described_class.new(
        order: order,
        payment_params: payment_params,
        current_user: user
      ).call
    end

    context 'with valid order and payment' do
      before do
        allow_any_instance_of(Payments::ProcessPayment)
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

      it 'schedules background jobs' do
        expect { subject }
          .to have_enqueued_job(GenerateInvoiceJob)
          .and have_enqueued_job(NotifyWarehouseJob)
      end

      it 'sends confirmation email' do
        expect { subject }
          .to have_enqueued_mail(OrderMailer, :confirmation)
      end
    end

    context 'with already processed order' do
      let(:order) { create(:order, :confirmed) }

      it 'returns failure' do
        expect(subject).to be_failure
        expect(subject.errors).to include(/already processed/)
      end
    end

    context 'when payment fails' do
      before do
        allow_any_instance_of(Payments::ProcessPayment)
          .to receive(:call)
          .and_return(Result.failure('Card declined'))
      end

      it 'returns failure' do
        expect(subject).to be_failure
        expect(subject.errors).to include(/Payment failed/)
      end

      it 'releases reserved inventory' do
        expect_any_instance_of(Inventory::ReleaseStock).to receive(:call)
        subject
      end
    end
  end
end
```

## Related Files Generated

1. `app/services/{{domain_lower}}/{{action_lower}}.rb` - Service object
2. `spec/services/{{domain_lower}}/{{action_lower}}_spec.rb` - Service specs
3. `app/services/result.rb` - Result object (if not exists)

## Best Practices Applied

- Single responsibility - one service, one operation
- Use Result objects for explicit success/failure
- Wrap multi-step operations in transactions
- Handle errors gracefully with rollback
- Log errors for debugging
- Use dependency injection for testability
- Keep services focused and composable
