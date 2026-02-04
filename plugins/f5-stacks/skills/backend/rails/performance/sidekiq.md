# Sidekiq Background Jobs

Background job processing with Sidekiq for Rails applications.

## Setup

### Gemfile

```ruby
gem 'sidekiq'
gem 'sidekiq-scheduler'  # For scheduled jobs
gem 'sidekiq-unique-jobs'  # Prevent duplicate jobs
```

### Configuration

```ruby
# config/initializers/sidekiq.rb
Sidekiq.configure_server do |config|
  config.redis = { url: ENV.fetch('REDIS_URL', 'redis://localhost:6379/1') }

  # Connection pool size
  config.redis = {
    url: ENV['REDIS_URL'],
    size: 25,
    network_timeout: 5
  }

  # Error handling
  config.error_handlers << proc { |ex, ctx_hash|
    Sentry.capture_exception(ex, extra: ctx_hash)
  }
end

Sidekiq.configure_client do |config|
  config.redis = { url: ENV.fetch('REDIS_URL', 'redis://localhost:6379/1'), size: 5 }
end

# Strict argument mode (recommended)
Sidekiq.strict_args!

# Default options
Sidekiq.default_job_options = {
  'backtrace' => true,
  'retry' => 5
}
```

### Routes

```ruby
# config/routes.rb
require 'sidekiq/web'

Rails.application.routes.draw do
  # Protect Sidekiq web UI
  authenticate :user, ->(user) { user.admin? } do
    mount Sidekiq::Web => '/sidekiq'
  end
end
```

## Basic Job

```ruby
# app/jobs/application_job.rb
class ApplicationJob
  include Sidekiq::Job

  sidekiq_options retry: 5, backtrace: true

  # Shared error handling
  sidekiq_retries_exhausted do |job, exception|
    Rails.logger.error "Job #{job['class']} with args #{job['args']} failed: #{exception.message}"
    Sentry.capture_exception(exception, extra: { job: job })
  end
end

# app/jobs/send_welcome_email_job.rb
class SendWelcomeEmailJob < ApplicationJob
  sidekiq_options queue: :mailers

  def perform(user_id)
    user = User.find(user_id)
    UserMailer.welcome_email(user).deliver_now
  end
end

# Usage
SendWelcomeEmailJob.perform_async(user.id)
SendWelcomeEmailJob.perform_in(1.hour, user.id)
SendWelcomeEmailJob.perform_at(Date.tomorrow.noon, user.id)
```

## Queue Configuration

```yaml
# config/sidekiq.yml
:concurrency: <%= ENV.fetch('SIDEKIQ_CONCURRENCY', 10) %>
:timeout: 25
:max_retries: 5

:queues:
  - [critical, 6]
  - [default, 4]
  - [mailers, 3]
  - [low, 2]

# Production with multiple processes
production:
  :concurrency: 25
  :queues:
    - [critical, 10]
    - [default, 5]
    - [mailers, 3]
    - [low, 1]
    - [scheduled, 1]
```

### Queue-Specific Jobs

```ruby
class ProcessPaymentJob < ApplicationJob
  sidekiq_options queue: :critical, retry: 3

  def perform(order_id)
    order = Order.find(order_id)
    PaymentService.new(order).process!
  end
end

class GenerateReportJob < ApplicationJob
  sidekiq_options queue: :low, retry: 1

  def perform(report_type, params)
    ReportGenerator.new(report_type, params).generate
  end
end
```

## Job Patterns

### Idempotent Jobs

```ruby
class ProcessOrderJob < ApplicationJob
  def perform(order_id)
    order = Order.find(order_id)

    # Idempotency check
    return if order.processed?

    Order.transaction do
      order.process!
      order.update!(processed_at: Time.current)
    end
  end
end
```

### Batch Processing

```ruby
class BulkImportJob < ApplicationJob
  sidekiq_options queue: :low

  BATCH_SIZE = 100

  def perform(import_id)
    import = Import.find(import_id)
    records = import.pending_records

    records.find_each(batch_size: BATCH_SIZE) do |record|
      ImportRecordJob.perform_async(record.id)
    end
  end
end

class ImportRecordJob < ApplicationJob
  def perform(record_id)
    record = ImportRecord.find(record_id)
    RecordImporter.new(record).import!
  end
end
```

### Job with Progress Tracking

```ruby
class ExportJob < ApplicationJob
  def perform(export_id)
    export = Export.find(export_id)
    export.update!(status: :processing, started_at: Time.current)

    total = export.items.count
    processed = 0

    export.items.find_each do |item|
      process_item(item, export)
      processed += 1
      update_progress(export, processed, total)
    end

    export.update!(status: :completed, completed_at: Time.current)
  rescue StandardError => e
    export.update!(status: :failed, error_message: e.message)
    raise
  end

  private

  def update_progress(export, processed, total)
    progress = (processed.to_f / total * 100).round
    export.update!(progress: progress) if processed % 10 == 0
  end
end
```

### Chained Jobs

```ruby
class OrderProcessingJob < ApplicationJob
  def perform(order_id)
    order = Order.find(order_id)

    # Process in sequence
    ValidateInventoryJob.perform_async(order_id)
  end
end

class ValidateInventoryJob < ApplicationJob
  def perform(order_id)
    order = Order.find(order_id)

    if InventoryService.validate(order)
      ChargePaymentJob.perform_async(order_id)
    else
      order.fail!('Insufficient inventory')
    end
  end
end

class ChargePaymentJob < ApplicationJob
  def perform(order_id)
    order = Order.find(order_id)

    if PaymentService.charge(order)
      FulfillOrderJob.perform_async(order_id)
    else
      order.fail!('Payment failed')
    end
  end
end
```

## Sidekiq Batches (Pro)

```ruby
# With Sidekiq Pro
class BatchImportJob < ApplicationJob
  def perform(import_id)
    import = Import.find(import_id)

    batch = Sidekiq::Batch.new
    batch.description = "Import #{import_id}"
    batch.on(:success, ImportCallbacks, import_id: import_id)
    batch.on(:complete, ImportCallbacks, import_id: import_id)

    batch.jobs do
      import.records.find_each do |record|
        ImportRecordJob.perform_async(record.id)
      end
    end
  end
end

class ImportCallbacks
  def on_success(status, options)
    import = Import.find(options['import_id'])
    import.update!(status: :completed)
  end

  def on_complete(status, options)
    import = Import.find(options['import_id'])
    if status.failures > 0
      import.update!(status: :partially_completed, failures: status.failures)
    end
  end
end
```

## Scheduled Jobs

```yaml
# config/sidekiq_scheduler.yml
:schedule:
  cleanup_expired_sessions:
    cron: '0 2 * * *'  # Daily at 2 AM
    class: CleanupExpiredSessionsJob
    queue: low

  send_daily_digest:
    cron: '0 8 * * *'  # Daily at 8 AM
    class: SendDailyDigestJob
    queue: mailers

  generate_daily_report:
    cron: '0 6 * * *'  # Daily at 6 AM
    class: GenerateDailyReportJob
    queue: scheduled

  sync_inventory:
    every: '30m'
    class: SyncInventoryJob
    queue: default
```

```ruby
# config/initializers/sidekiq.rb
require 'sidekiq-scheduler'

Sidekiq.configure_server do |config|
  config.on(:startup) do
    Sidekiq.schedule = YAML.load_file(Rails.root.join('config/sidekiq_scheduler.yml'))[:schedule]
    SidekiqScheduler::Scheduler.instance.reload_schedule!
  end
end
```

## Unique Jobs

```ruby
# Prevent duplicate jobs
class SyncUserJob < ApplicationJob
  sidekiq_options lock: :until_executed,
                  on_conflict: :log

  def perform(user_id)
    user = User.find(user_id)
    UserSyncService.new(user).sync!
  end
end

# Lock until timeout
class ProcessWebhookJob < ApplicationJob
  sidekiq_options lock: :until_timeout,
                  lock_timeout: 1.hour,
                  on_conflict: :reject

  def perform(webhook_id)
    webhook = Webhook.find(webhook_id)
    WebhookProcessor.new(webhook).process!
  end
end
```

## Error Handling

```ruby
class ReliableJob < ApplicationJob
  sidekiq_options retry: 5

  # Custom retry delays
  sidekiq_retry_in do |count, exception|
    case exception
    when RateLimitError
      60 * 5  # 5 minutes
    when ServiceUnavailable
      60 * count  # Linear backoff
    else
      :default  # Exponential backoff
    end
  end

  sidekiq_retries_exhausted do |job, exception|
    # Called when all retries are exhausted
    FailedJobHandler.handle(job, exception)
  end

  def perform(resource_id)
    resource = Resource.find(resource_id)
    ExternalService.process(resource)
  rescue ExternalService::RateLimitError => e
    # Will use custom retry delay
    raise
  rescue ExternalService::PermanentError => e
    # Don't retry
    Rails.logger.error "Permanent error for resource #{resource_id}: #{e.message}"
  end
end
```

## Job Testing

```ruby
# spec/jobs/send_welcome_email_job_spec.rb
RSpec.describe SendWelcomeEmailJob, type: :job do
  include ActiveJob::TestHelper

  let(:user) { create(:user) }

  describe '#perform' do
    it 'sends welcome email' do
      expect {
        described_class.perform_now(user.id)
      }.to change { ActionMailer::Base.deliveries.count }.by(1)
    end

    it 'handles missing user gracefully' do
      expect {
        described_class.perform_now(-1)
      }.to raise_error(ActiveRecord::RecordNotFound)
    end
  end

  describe 'enqueueing' do
    it 'enqueues the job' do
      expect {
        described_class.perform_async(user.id)
      }.to change(described_class.jobs, :size).by(1)
    end

    it 'enqueues on correct queue' do
      described_class.perform_async(user.id)
      expect(described_class.jobs.last['queue']).to eq('mailers')
    end
  end
end
```

### Testing with Sidekiq::Testing

```ruby
# spec/rails_helper.rb
require 'sidekiq/testing'

RSpec.configure do |config|
  config.before do
    Sidekiq::Testing.fake!
  end
end

# In specs
RSpec.describe OrderService do
  describe '#process' do
    it 'enqueues notification job' do
      Sidekiq::Testing.fake! do
        order = create(:order)
        OrderService.new(order).process

        expect(SendOrderNotificationJob.jobs.size).to eq(1)
        expect(SendOrderNotificationJob.jobs.first['args']).to eq([order.id])
      end
    end
  end
end

# Inline mode - execute immediately
Sidekiq::Testing.inline! do
  # Jobs execute synchronously
  SendWelcomeEmailJob.perform_async(user.id)
  # Email already sent
end
```

## Monitoring

```ruby
# Custom metrics
class InstrumentedJob < ApplicationJob
  def perform(*args)
    start_time = Time.current

    super
  ensure
    duration = Time.current - start_time
    StatsD.timing("jobs.#{self.class.name.underscore}.duration", duration * 1000)
    StatsD.increment("jobs.#{self.class.name.underscore}.count")
  end
end

# Death handler
Sidekiq.configure_server do |config|
  config.death_handlers << ->(job, exception) do
    StatsD.increment("jobs.dead")
    SlackNotifier.notify_job_death(job, exception)
  end
end
```

## Best Practices

1. **Keep jobs small and focused** - One responsibility per job
2. **Make jobs idempotent** - Safe to run multiple times
3. **Use appropriate queues** - Critical vs low priority
4. **Handle errors gracefully** - Custom retry strategies
5. **Pass IDs not objects** - Avoid serialization issues
6. **Set reasonable timeouts** - Prevent stuck workers
7. **Monitor job metrics** - Track failures and latency
8. **Test jobs thoroughly** - Unit and integration tests
