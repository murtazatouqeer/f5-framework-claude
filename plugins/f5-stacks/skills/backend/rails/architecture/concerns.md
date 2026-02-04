# Rails Concerns

Shared behavior modules for DRY code in Rails applications.

## What are Concerns?

Concerns are modules that encapsulate reusable functionality using
`ActiveSupport::Concern`. They provide:

- **Code reuse** across multiple models or controllers
- **Clean organization** of related functionality
- **Dependency management** between modules

## Model Concerns

### Soft Deletable

```ruby
# app/models/concerns/soft_deletable.rb
module SoftDeletable
  extend ActiveSupport::Concern

  included do
    # Default scope excludes soft-deleted records
    default_scope { where(deleted_at: nil) }

    # Scopes for accessing deleted records
    scope :with_deleted, -> { unscope(where: :deleted_at) }
    scope :only_deleted, -> { unscope(where: :deleted_at).where.not(deleted_at: nil) }
  end

  def soft_delete
    update(deleted_at: Time.current)
  end

  def restore
    update(deleted_at: nil)
  end

  def deleted?
    deleted_at.present?
  end

  def destroy
    soft_delete
  end

  def destroy!
    soft_delete
  end

  def really_destroy!
    super(:destroy)
  end
end

# Usage in model
class User < ApplicationRecord
  include SoftDeletable
end
```

### Searchable

```ruby
# app/models/concerns/searchable.rb
module Searchable
  extend ActiveSupport::Concern

  included do
    scope :search, ->(term) {
      return all if term.blank?

      search_columns = self::SEARCH_COLUMNS rescue [:name]
      conditions = search_columns.map { |col| "#{col} ILIKE :term" }.join(' OR ')
      where(conditions, term: "%#{term}%")
    }
  end

  class_methods do
    def searchable_columns(*columns)
      const_set(:SEARCH_COLUMNS, columns)
    end
  end
end

# Usage in model
class Product < ApplicationRecord
  include Searchable
  searchable_columns :name, :description, :sku
end

# Query
Product.search('laptop')
```

### Has UUID

```ruby
# app/models/concerns/has_uuid.rb
module HasUuid
  extend ActiveSupport::Concern

  included do
    before_create :generate_uuid
  end

  private

  def generate_uuid
    self.id ||= SecureRandom.uuid
  end
end
```

### Auditable

```ruby
# app/models/concerns/auditable.rb
module Auditable
  extend ActiveSupport::Concern

  included do
    has_many :audit_logs, as: :auditable, dependent: :destroy

    after_create :log_create
    after_update :log_update
    after_destroy :log_destroy
  end

  private

  def log_create
    log_action('create', nil, attributes)
  end

  def log_update
    return unless saved_changes.any?

    log_action('update', saved_changes.transform_values(&:first),
                         saved_changes.transform_values(&:last))
  end

  def log_destroy
    log_action('destroy', attributes, nil)
  end

  def log_action(action, old_values, new_values)
    audit_logs.create!(
      action: action,
      old_values: old_values,
      new_values: new_values,
      user_id: Current.user&.id,
      ip_address: Current.ip_address
    )
  end
end
```

### Sluggable

```ruby
# app/models/concerns/sluggable.rb
module Sluggable
  extend ActiveSupport::Concern

  included do
    before_validation :generate_slug, on: :create
    validates :slug, presence: true, uniqueness: true
  end

  class_methods do
    def slug_from(attribute)
      @slug_source = attribute
    end

    def slug_source
      @slug_source || :name
    end
  end

  def to_param
    slug
  end

  private

  def generate_slug
    return if slug.present?

    source_value = send(self.class.slug_source)
    return unless source_value.present?

    base_slug = source_value.parameterize
    unique_slug = base_slug
    counter = 1

    while self.class.unscoped.exists?(slug: unique_slug)
      unique_slug = "#{base_slug}-#{counter}"
      counter += 1
    end

    self.slug = unique_slug
  end
end

# Usage
class Article < ApplicationRecord
  include Sluggable
  slug_from :title
end
```

### Publishable

```ruby
# app/models/concerns/publishable.rb
module Publishable
  extend ActiveSupport::Concern

  included do
    scope :published, -> { where.not(published_at: nil).where('published_at <= ?', Time.current) }
    scope :draft, -> { where(published_at: nil) }
    scope :scheduled, -> { where('published_at > ?', Time.current) }
  end

  def published?
    published_at.present? && published_at <= Time.current
  end

  def draft?
    published_at.nil?
  end

  def scheduled?
    published_at.present? && published_at > Time.current
  end

  def publish!
    update!(published_at: Time.current)
  end

  def unpublish!
    update!(published_at: nil)
  end

  def schedule!(datetime)
    update!(published_at: datetime)
  end
end
```

## Controller Concerns

### Exception Handler

```ruby
# app/controllers/concerns/exception_handler.rb
module ExceptionHandler
  extend ActiveSupport::Concern

  included do
    rescue_from StandardError, with: :handle_standard_error
    rescue_from ActiveRecord::RecordNotFound, with: :handle_not_found
    rescue_from ActiveRecord::RecordInvalid, with: :handle_validation_error
    rescue_from Pundit::NotAuthorizedError, with: :handle_unauthorized
    rescue_from ActionController::ParameterMissing, with: :handle_parameter_missing
  end

  private

  def handle_standard_error(error)
    log_error(error)

    render json: {
      error: Rails.env.production? ? 'Internal server error' : error.message
    }, status: :internal_server_error
  end

  def handle_not_found(error)
    render json: { error: 'Resource not found' }, status: :not_found
  end

  def handle_validation_error(error)
    render json: { errors: error.record.errors.full_messages }, status: :unprocessable_entity
  end

  def handle_unauthorized(error)
    render json: { error: 'Not authorized' }, status: :forbidden
  end

  def handle_parameter_missing(error)
    render json: { error: "Missing parameter: #{error.param}" }, status: :bad_request
  end

  def log_error(error)
    Rails.logger.error("#{error.class}: #{error.message}")
    Rails.logger.error(error.backtrace.first(10).join("\n"))

    # Send to error tracking service
    Sentry.capture_exception(error) if defined?(Sentry)
  end
end
```

### Pagination

```ruby
# app/controllers/concerns/pagination.rb
module Pagination
  extend ActiveSupport::Concern

  included do
    helper_method :pagination_meta if respond_to?(:helper_method)
  end

  def paginate(collection)
    collection.page(page).per(per_page)
  end

  def page
    params[:page]&.to_i || 1
  end

  def per_page
    [(params[:per_page]&.to_i || default_per_page), max_per_page].min
  end

  def default_per_page
    20
  end

  def max_per_page
    100
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

  def pagination_links(collection)
    base_url = request.base_url + request.path

    {
      links: {
        self: "#{base_url}?page=#{collection.current_page}&per_page=#{per_page}",
        first: "#{base_url}?page=1&per_page=#{per_page}",
        last: "#{base_url}?page=#{collection.total_pages}&per_page=#{per_page}",
        next: collection.next_page ? "#{base_url}?page=#{collection.next_page}&per_page=#{per_page}" : nil,
        prev: collection.prev_page ? "#{base_url}?page=#{collection.prev_page}&per_page=#{per_page}" : nil
      }
    }
  end
end
```

### Response Handler

```ruby
# app/controllers/concerns/response_handler.rb
module ResponseHandler
  extend ActiveSupport::Concern

  def render_success(data, status: :ok, **options)
    render json: serialize(data, options), status: status
  end

  def render_created(data, **options)
    render_success(data, status: :created, **options)
  end

  def render_error(message, status: :unprocessable_entity)
    render json: { error: message }, status: status
  end

  def render_errors(errors, status: :unprocessable_entity)
    render json: { errors: Array(errors) }, status: status
  end

  def render_no_content
    head :no_content
  end

  private

  def serialize(data, options = {})
    serializer = options.delete(:serializer) || default_serializer(data)
    return data unless serializer

    serializer.new(data, options).serializable_hash
  end

  def default_serializer(data)
    model_class = data.is_a?(ActiveRecord::Relation) ? data.klass : data.class
    "#{model_class.name}Serializer".safe_constantize
  end
end
```

## Combining Concerns

```ruby
# app/models/article.rb
class Article < ApplicationRecord
  include SoftDeletable
  include Searchable
  include Sluggable
  include Publishable
  include Auditable

  slug_from :title
  searchable_columns :title, :content, :excerpt

  belongs_to :author, class_name: 'User'
  has_many :comments, dependent: :destroy

  validates :title, presence: true
  validates :content, presence: true
end
```

## Testing Concerns

```ruby
# spec/support/shared_examples/soft_deletable.rb
RSpec.shared_examples 'soft_deletable' do
  describe 'soft delete behavior' do
    it 'soft deletes the record' do
      subject.soft_delete
      expect(subject.deleted_at).to be_present
    end

    it 'excludes deleted records by default' do
      subject.soft_delete
      expect(described_class.all).not_to include(subject)
    end

    it 'includes deleted records with with_deleted scope' do
      subject.soft_delete
      expect(described_class.with_deleted).to include(subject)
    end

    it 'restores deleted records' do
      subject.soft_delete
      subject.restore
      expect(subject.deleted_at).to be_nil
    end
  end
end

# spec/models/user_spec.rb
RSpec.describe User do
  subject { create(:user) }

  it_behaves_like 'soft_deletable'
end
```

## Best Practices

1. **Keep concerns focused** - One concern, one feature
2. **Use descriptive names** - `Searchable`, not `Search`
3. **Document dependencies** - Note required columns/methods
4. **Test in isolation** - Use shared examples
5. **Avoid deep nesting** - Keep concerns simple
6. **Use `included` block** - For associations and scopes
7. **Use `class_methods`** - For class-level methods
