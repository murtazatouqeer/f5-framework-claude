# Factory Bot Patterns

Test data generation with Factory Bot for Rails applications.

## Setup

```ruby
# Gemfile
group :development, :test do
  gem 'factory_bot_rails'
  gem 'faker'
end

# spec/support/factory_bot.rb
RSpec.configure do |config|
  config.include FactoryBot::Syntax::Methods
end
```

## Basic Factory

```ruby
# spec/factories/users.rb
FactoryBot.define do
  factory :user do
    email { Faker::Internet.unique.email }
    password { 'password123' }
    password_confirmation { password }
    name { Faker::Name.name }
    role { :user }
    status { :active }

    # Timestamps are auto-set, but can be overridden
    created_at { Time.current }
    updated_at { Time.current }
  end
end
```

## Traits

```ruby
# spec/factories/users.rb
FactoryBot.define do
  factory :user do
    email { Faker::Internet.unique.email }
    password { 'password123' }
    name { Faker::Name.name }
    role { :user }
    status { :active }

    # Role traits
    trait :admin do
      role { :admin }
    end

    trait :moderator do
      role { :moderator }
    end

    # Status traits
    trait :inactive do
      status { :inactive }
    end

    trait :pending do
      status { :pending }
      confirmed_at { nil }
    end

    # Profile traits
    trait :with_avatar do
      after(:create) do |user|
        user.avatar.attach(
          io: File.open(Rails.root.join('spec/fixtures/avatar.png')),
          filename: 'avatar.png',
          content_type: 'image/png'
        )
      end
    end

    trait :with_profile do
      after(:create) do |user|
        create(:profile, user: user)
      end
    end

    # Soft deleted
    trait :deleted do
      deleted_at { Time.current }
    end

    # Time-based traits
    trait :recently_created do
      created_at { 1.hour.ago }
    end

    trait :old do
      created_at { 1.year.ago }
    end
  end
end

# Usage
create(:user)                      # Regular user
create(:user, :admin)              # Admin user
create(:user, :admin, :with_profile)  # Admin with profile
create(:user, :inactive, :deleted) # Inactive and deleted
```

## Associations

```ruby
# spec/factories/orders.rb
FactoryBot.define do
  factory :order do
    user
    order_number { "ORD-#{SecureRandom.hex(4).upcase}" }
    status { :pending }
    total { 0 }

    # Explicit association
    association :shipping_address, factory: :address

    # Association with traits
    trait :with_admin_user do
      association :user, factory: [:user, :admin]
    end

    # Nested creation
    trait :with_items do
      transient do
        items_count { 3 }
      end

      after(:create) do |order, evaluator|
        create_list(:order_item, evaluator.items_count, order: order)
        order.reload
        order.update!(total: order.items.sum(&:subtotal))
      end
    end

    # Polymorphic association
    trait :with_payment do
      after(:create) do |order|
        create(:payment, payable: order)
      end
    end
  end
end

# spec/factories/order_items.rb
FactoryBot.define do
  factory :order_item do
    order
    product
    quantity { rand(1..5) }
    unit_price { product.price }
    subtotal { quantity * unit_price }
  end
end

# Usage
create(:order, :with_items)
create(:order, :with_items, items_count: 5)
create(:order, :with_admin_user, :with_payment)
```

## Transient Attributes

```ruby
# spec/factories/products.rb
FactoryBot.define do
  factory :product do
    name { Faker::Commerce.product_name }
    description { Faker::Lorem.paragraph }
    price { Faker::Commerce.price(range: 10.0..100.0) }
    status { :active }

    transient do
      tags_count { 0 }
      reviews_count { 0 }
      with_discount { false }
      discount_percent { 20 }
    end

    after(:create) do |product, evaluator|
      # Create tags
      if evaluator.tags_count > 0
        create_list(:tag, evaluator.tags_count).each do |tag|
          product.tags << tag
        end
      end

      # Create reviews
      create_list(:review, evaluator.reviews_count, product: product) if evaluator.reviews_count > 0

      # Apply discount
      if evaluator.with_discount
        product.update!(
          compare_price: product.price,
          price: product.price * (1 - evaluator.discount_percent / 100.0)
        )
      end
    end

    # Convenience traits
    trait :with_tags do
      transient do
        tags_count { 3 }
      end
    end

    trait :with_reviews do
      transient do
        reviews_count { 5 }
      end
    end

    trait :on_sale do
      transient do
        with_discount { true }
        discount_percent { 25 }
      end
    end
  end
end

# Usage
create(:product, tags_count: 5)
create(:product, :with_tags, :with_reviews)
create(:product, :on_sale, discount_percent: 30)
```

## Sequences

```ruby
# spec/factories/sequences.rb
FactoryBot.define do
  sequence :email do |n|
    "user#{n}@example.com"
  end

  sequence :sku do |n|
    "SKU-#{n.to_s.rjust(6, '0')}"
  end

  sequence :order_number do |n|
    "ORD-#{Time.current.strftime('%Y%m%d')}-#{n.to_s.rjust(4, '0')}"
  end

  sequence :uuid do
    SecureRandom.uuid
  end
end

# spec/factories/products.rb
FactoryBot.define do
  factory :product do
    sku { generate(:sku) }
    name { Faker::Commerce.product_name }
  end
end

# Alternative: inline sequence
factory :category do
  sequence(:name) { |n| "Category #{n}" }
  sequence(:slug) { |n| "category-#{n}" }
end
```

## Inheritance

```ruby
# spec/factories/users.rb
FactoryBot.define do
  factory :user do
    email { Faker::Internet.unique.email }
    password { 'password123' }
    name { Faker::Name.name }
    role { :user }

    # Child factories
    factory :admin_user do
      role { :admin }
      name { "Admin #{Faker::Name.last_name}" }
    end

    factory :super_admin do
      role { :admin }
      super_admin { true }

      after(:create) do |user|
        user.permissions << Permission.all
      end
    end
  end
end

# Usage
create(:user)        # Regular user
create(:admin_user)  # Inherits from user
create(:super_admin) # Inherits from user
```

## Callbacks

```ruby
# spec/factories/articles.rb
FactoryBot.define do
  factory :article do
    title { Faker::Lorem.sentence }
    body { Faker::Lorem.paragraphs(number: 5).join("\n\n") }
    author factory: :user
    status { :draft }

    # Before callbacks
    before(:create) do |article|
      article.slug ||= article.title.parameterize
    end

    # After callbacks
    after(:create) do |article|
      article.update_column(:word_count, article.body.split.size)
    end

    # Build callback (doesn't hit DB)
    after(:build) do |article|
      article.reading_time = (article.body.split.size / 200.0).ceil
    end

    # Stub callback (for stubbed factories)
    after(:stub) do |article|
      article.id ||= SecureRandom.uuid
    end

    trait :published do
      status { :published }
      published_at { Time.current }

      after(:create) do |article|
        create(:activity, trackable: article, action: 'published')
      end
    end
  end
end
```

## Aliases

```ruby
# spec/factories/users.rb
FactoryBot.define do
  factory :user, aliases: [:author, :owner, :creator, :assignee] do
    email { Faker::Internet.unique.email }
    name { Faker::Name.name }
  end
end

# Usage in associations
factory :article do
  author  # Uses :user factory
end

factory :task do
  creator   # Uses :user factory
  assignee  # Uses :user factory
end
```

## Building vs Creating

```ruby
# build - Creates instance without saving to DB
user = build(:user)
user.persisted? # => false

# create - Creates and saves to DB
user = create(:user)
user.persisted? # => true

# build_stubbed - Creates stub with fake ID (fastest)
user = build_stubbed(:user)
user.id # => 1001 (fake)
user.persisted? # => true (stubbed)

# attributes_for - Returns hash of attributes
attrs = attributes_for(:user)
# => { email: "...", name: "...", password: "..." }

# build_list / create_list - Multiple records
users = build_list(:user, 5)
users = create_list(:user, 5)

# build_pair / create_pair - Two records
user1, user2 = create_pair(:user)
```

## Linting Factories

```ruby
# spec/factories_spec.rb
RSpec.describe 'Factory lint' do
  it 'has valid factories' do
    FactoryBot.lint(traits: true)
  end
end

# Or in spec_helper.rb
RSpec.configure do |config|
  config.before(:suite) do
    FactoryBot.lint if ENV['LINT_FACTORIES']
  end
end

# Run with: LINT_FACTORIES=true rspec
```

## Complex Factory Examples

### E-commerce Order

```ruby
# spec/factories/orders.rb
FactoryBot.define do
  factory :order do
    user
    order_number { generate(:order_number) }
    status { :pending }
    subtotal { 0 }
    tax { 0 }
    shipping { 0 }
    total { 0 }

    transient do
      products { [] }
      products_count { 0 }
    end

    after(:create) do |order, evaluator|
      # Use specific products or generate random ones
      items_products = evaluator.products.presence ||
                       create_list(:product, evaluator.products_count)

      items_products.each do |product|
        create(:order_item, order: order, product: product)
      end

      order.reload
      order.recalculate_totals!
    end

    trait :pending do
      status { :pending }
    end

    trait :confirmed do
      status { :confirmed }
      confirmed_at { Time.current }
    end

    trait :shipped do
      status { :shipped }
      confirmed_at { 2.days.ago }
      shipped_at { Time.current }

      after(:create) do |order|
        create(:shipment, order: order, tracking_number: "TRK#{SecureRandom.hex(8).upcase}")
      end
    end

    trait :delivered do
      status { :delivered }
      confirmed_at { 5.days.ago }
      shipped_at { 3.days.ago }
      delivered_at { Time.current }
    end

    trait :with_payment do
      after(:create) do |order|
        create(:payment, :completed, payable: order, amount: order.total)
      end
    end

    factory :complete_order do
      transient do
        products_count { 3 }
      end

      with_payment
      confirmed
    end
  end
end

# Usage
create(:order, products_count: 2)
create(:order, products: [product1, product2])
create(:complete_order)
create(:order, :shipped, :with_payment, products_count: 5)
```

### Multi-tenant Application

```ruby
# spec/factories/tenants.rb
FactoryBot.define do
  factory :tenant do
    name { Faker::Company.name }
    subdomain { Faker::Internet.unique.domain_word }
    plan { :free }

    trait :premium do
      plan { :premium }
    end

    trait :with_users do
      transient do
        users_count { 3 }
      end

      after(:create) do |tenant, evaluator|
        create_list(:user, evaluator.users_count, tenant: tenant)
      end
    end

    trait :with_admin do
      after(:create) do |tenant|
        create(:user, :admin, tenant: tenant)
      end
    end

    factory :complete_tenant do
      with_admin
      with_users
      premium
    end
  end
end
```

### Nested Resources

```ruby
# spec/factories/comments.rb
FactoryBot.define do
  factory :comment do
    user
    body { Faker::Lorem.paragraph }

    # Polymorphic
    for_article

    trait :for_article do
      association :commentable, factory: :article
    end

    trait :for_product do
      association :commentable, factory: :product
    end

    # Nested comments
    trait :with_replies do
      transient do
        replies_count { 2 }
      end

      after(:create) do |comment, evaluator|
        create_list(:comment, evaluator.replies_count,
          commentable: comment.commentable,
          parent: comment
        )
      end
    end
  end
end
```

## Best Practices

1. **Keep factories minimal** - Only required attributes
2. **Use traits for variations** - Not separate factories
3. **Use transient for computed values** - Clean separation
4. **Use sequences for unique values** - Avoid collisions
5. **Use build_stubbed when possible** - Faster tests
6. **Lint factories regularly** - Catch issues early
7. **Use Faker for realistic data** - Better test coverage
8. **Document complex factories** - Help teammates understand
