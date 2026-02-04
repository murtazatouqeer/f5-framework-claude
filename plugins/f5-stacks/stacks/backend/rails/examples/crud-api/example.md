# CRUD API Example - Products Module

Complete example of a RESTful API for Products in Rails.

## Overview

This example demonstrates:
- Full CRUD operations
- JSON:API serialization
- Pundit authorization
- Filtering, sorting, and pagination
- Service objects
- Comprehensive testing

## Directory Structure

```
app/
├── controllers/
│   └── api/
│       └── v1/
│           ├── base_controller.rb
│           └── products_controller.rb
├── models/
│   └── product.rb
├── serializers/
│   └── product_serializer.rb
├── policies/
│   └── product_policy.rb
├── services/
│   └── products/
│       ├── create_service.rb
│       ├── update_service.rb
│       └── search_service.rb
└── jobs/
    └── product_notification_job.rb
```

## Model

```ruby
# app/models/product.rb
class Product < ApplicationRecord
  include Sluggable
  include SoftDeletable

  belongs_to :category
  belongs_to :created_by, class_name: 'User', optional: true

  has_many :product_tags, dependent: :destroy
  has_many :tags, through: :product_tags
  has_many :reviews, dependent: :destroy
  has_many :order_items, dependent: :restrict_with_error

  has_one_attached :featured_image
  has_many_attached :gallery_images

  enum :status, {
    draft: 'draft',
    active: 'active',
    archived: 'archived'
  }, prefix: true, default: :draft

  validates :name, presence: true, length: { maximum: 255 }
  validates :slug, presence: true, uniqueness: true
  validates :sku, presence: true, uniqueness: { scope: :category_id }
  validates :price, presence: true, numericality: { greater_than_or_equal_to: 0 }
  validates :compare_price, numericality: { greater_than: :price }, allow_nil: true

  scope :active, -> { where(status: :active) }
  scope :featured, -> { where(featured: true) }
  scope :by_category, ->(category_id) { where(category_id: category_id) }
  scope :price_range, ->(min, max) { where(price: min..max) }
  scope :search, ->(query) {
    where('name ILIKE :q OR description ILIKE :q OR sku ILIKE :q', q: "%#{query}%")
  }

  before_validation :generate_slug, on: :create
  before_validation :generate_sku, on: :create
  after_commit :invalidate_cache

  def on_sale?
    compare_price.present? && compare_price > price
  end

  def discount_percentage
    return 0 unless on_sale?

    ((compare_price - price) / compare_price * 100).round
  end

  def in_stock?
    stock_quantity.to_i > 0
  end

  def publish!
    return false unless status_draft?

    update!(status: :active, published_at: Time.current)
  end

  def archive!
    update!(status: :archived, archived_at: Time.current)
  end

  private

  def generate_slug
    self.slug ||= name&.parameterize
  end

  def generate_sku
    self.sku ||= "#{category&.code || 'GEN'}-#{SecureRandom.hex(4).upcase}"
  end

  def invalidate_cache
    Rails.cache.delete("products/#{id}")
    Rails.cache.delete('products/featured')
  end
end
```

## Migration

```ruby
# db/migrate/20240115120000_create_products.rb
class CreateProducts < ActiveRecord::Migration[7.1]
  def change
    create_table :products, id: :uuid do |t|
      t.references :category, null: false, foreign_key: true, type: :uuid
      t.references :created_by, foreign_key: { to_table: :users }, type: :uuid

      t.string :name, null: false
      t.string :slug, null: false
      t.string :sku, null: false
      t.text :description
      t.decimal :price, precision: 10, scale: 2, null: false
      t.decimal :compare_price, precision: 10, scale: 2
      t.integer :stock_quantity, default: 0, null: false
      t.boolean :featured, default: false, null: false
      t.string :status, default: 'draft', null: false
      t.jsonb :metadata, default: {}

      t.integer :reviews_count, default: 0, null: false
      t.decimal :average_rating, precision: 3, scale: 2

      t.datetime :published_at
      t.datetime :archived_at
      t.datetime :deleted_at

      t.timestamps
    end

    add_index :products, :slug, unique: true
    add_index :products, :sku, unique: true
    add_index :products, :status
    add_index :products, :featured
    add_index :products, :deleted_at
    add_index :products, [:category_id, :status]
  end
end
```

## Controller

```ruby
# app/controllers/api/v1/products_controller.rb
module Api
  module V1
    class ProductsController < BaseController
      before_action :set_product, only: [:show, :update, :destroy, :publish, :archive]

      def index
        result = Products::SearchService.new(search_params).call

        @products = policy_scope(result.data)
          .includes(:category, :tags, featured_image_attachment: :blob)
          .page(params[:page])
          .per(params[:per_page] || 20)

        render json: ProductSerializer.new(
          @products,
          include: [:category],
          meta: pagination_meta(@products)
        )
      end

      def show
        authorize @product

        render json: ProductSerializer.new(
          @product,
          include: [:category, :tags],
          params: { current_user: current_user }
        )
      end

      def create
        authorize Product

        result = Products::CreateService.new(
          params: product_params,
          current_user: current_user
        ).call

        if result.success?
          render json: ProductSerializer.new(result.data), status: :created
        else
          render json: { errors: result.errors }, status: :unprocessable_entity
        end
      end

      def update
        authorize @product

        result = Products::UpdateService.new(
          product: @product,
          params: product_params,
          current_user: current_user
        ).call

        if result.success?
          render json: ProductSerializer.new(result.data)
        else
          render json: { errors: result.errors }, status: :unprocessable_entity
        end
      end

      def destroy
        authorize @product

        @product.destroy!
        head :no_content
      end

      def publish
        authorize @product

        if @product.publish!
          render json: ProductSerializer.new(@product)
        else
          render json: { error: 'Cannot publish this product' }, status: :unprocessable_entity
        end
      end

      def archive
        authorize @product

        @product.archive!
        render json: ProductSerializer.new(@product)
      end

      private

      def set_product
        @product = Product.find(params[:id])
      end

      def product_params
        params.require(:product).permit(
          :name, :description, :price, :compare_price,
          :category_id, :stock_quantity, :featured,
          :featured_image, tag_ids: [], gallery_images: []
        )
      end

      def search_params
        params.permit(:q, :category_id, :min_price, :max_price, :status, :sort, tag_ids: [])
      end

      def pagination_meta(collection)
        {
          current_page: collection.current_page,
          total_pages: collection.total_pages,
          total_count: collection.total_count,
          per_page: collection.limit_value
        }
      end
    end
  end
end
```

## Serializer

```ruby
# app/serializers/product_serializer.rb
class ProductSerializer
  include JSONAPI::Serializer

  set_type :product
  set_id :id

  attributes :name, :slug, :description, :price, :compare_price,
             :status, :sku, :stock_quantity, :featured

  attribute :created_at do |product|
    product.created_at.iso8601
  end

  attribute :on_sale do |product|
    product.on_sale?
  end

  attribute :discount_percentage do |product|
    product.discount_percentage
  end

  attribute :in_stock do |product|
    product.in_stock?
  end

  attribute :image_url do |product|
    if product.featured_image.attached?
      Rails.application.routes.url_helpers.rails_blob_url(
        product.featured_image,
        only_path: true
      )
    end
  end

  attribute :internal_notes, if: proc { |_record, params|
    params[:current_user]&.admin?
  }

  belongs_to :category, serializer: CategorySerializer
  has_many :tags, serializer: TagSerializer

  meta do |product|
    {
      reviews_count: product.reviews_count,
      average_rating: product.average_rating
    }
  end
end
```

## Policy

```ruby
# app/policies/product_policy.rb
class ProductPolicy < ApplicationPolicy
  def index?
    true
  end

  def show?
    record.status_active? || owner_or_admin?
  end

  def create?
    user.present?
  end

  def update?
    owner_or_admin?
  end

  def destroy?
    admin? || (owner_or_admin? && record.order_items.empty?)
  end

  def publish?
    owner_or_admin? && record.status_draft?
  end

  def archive?
    admin?
  end

  def permitted_attributes
    if admin?
      [:name, :description, :price, :compare_price, :status, :category_id,
       :sku, :stock_quantity, :featured, :internal_notes, tag_ids: []]
    else
      [:name, :description, :price, :compare_price, :category_id, tag_ids: []]
    end
  end

  class Scope < ApplicationPolicy::Scope
    def resolve
      if admin?
        scope.all
      elsif user.present?
        scope.where(status: :active).or(scope.where(created_by_id: user.id))
      else
        scope.where(status: :active)
      end
    end
  end
end
```

## Services

```ruby
# app/services/products/create_service.rb
module Products
  class CreateService
    attr_reader :params, :current_user

    def initialize(params:, current_user:)
      @params = params
      @current_user = current_user
    end

    def call
      product = Product.new(params)
      product.created_by = current_user

      Product.transaction do
        product.save!
        attach_images(product)
        notify_admin(product)
      end

      Result.success(product)
    rescue ActiveRecord::RecordInvalid => e
      Result.failure(e.record.errors.full_messages)
    rescue StandardError => e
      Rails.logger.error "Products::CreateService failed: #{e.message}"
      Result.failure('Failed to create product')
    end

    private

    def attach_images(product)
      return unless params[:featured_image]

      product.featured_image.attach(params[:featured_image])
    end

    def notify_admin(product)
      ProductNotificationJob.perform_async(product.id, 'created')
    end
  end
end

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
      when 'price_asc' then scope.order(price: :asc)
      when 'price_desc' then scope.order(price: :desc)
      when 'newest' then scope.order(created_at: :desc)
      when 'popular' then scope.order(views_count: :desc)
      else scope.order(created_at: :desc)
      end
    end
  end
end
```

## Routes

```ruby
# config/routes.rb
Rails.application.routes.draw do
  namespace :api do
    namespace :v1 do
      resources :products do
        member do
          post :publish
          post :archive
        end
      end
    end
  end
end
```

## Tests

```ruby
# spec/requests/api/v1/products_spec.rb
RSpec.describe 'Api::V1::Products', type: :request do
  let(:current_user) { create(:user) }
  let(:headers) { auth_headers_for(current_user) }
  let(:category) { create(:category) }

  describe 'GET /api/v1/products' do
    let!(:products) { create_list(:product, 5, :active) }

    it 'returns all active products' do
      get '/api/v1/products', headers: headers

      expect(response).to have_http_status(:ok)
      expect(json_data.length).to eq(5)
    end

    it 'filters by category' do
      product = create(:product, :active, category: category)

      get '/api/v1/products', params: { category_id: category.id }, headers: headers

      expect(json_data.length).to eq(1)
      expect(json_data.first[:id]).to eq(product.id.to_s)
    end

    it 'filters by price range' do
      cheap = create(:product, :active, price: 10)
      expensive = create(:product, :active, price: 100)

      get '/api/v1/products', params: { min_price: 50 }, headers: headers

      expect(json_data.map { |p| p[:id] }).to include(expensive.id.to_s)
      expect(json_data.map { |p| p[:id] }).not_to include(cheap.id.to_s)
    end

    it 'searches by name' do
      product = create(:product, :active, name: 'Unique Product')

      get '/api/v1/products', params: { q: 'unique' }, headers: headers

      expect(json_data.length).to eq(1)
    end

    it 'paginates results' do
      create_list(:product, 25, :active)

      get '/api/v1/products', params: { page: 1, per_page: 10 }, headers: headers

      expect(json_data.length).to eq(10)
      expect(json_response[:meta][:total_count]).to eq(25)
    end
  end

  describe 'POST /api/v1/products' do
    let(:valid_params) do
      {
        product: {
          name: 'New Product',
          description: 'Product description',
          price: 29.99,
          category_id: category.id
        }
      }
    end

    it 'creates a product' do
      expect {
        post '/api/v1/products', params: valid_params, headers: headers
      }.to change(Product, :count).by(1)

      expect(response).to have_http_status(:created)
      expect(json_data[:attributes][:name]).to eq('New Product')
    end

    it 'sets created_by to current user' do
      post '/api/v1/products', params: valid_params, headers: headers

      expect(Product.last.created_by).to eq(current_user)
    end
  end

  describe 'POST /api/v1/products/:id/publish' do
    let!(:product) { create(:product, :draft, created_by: current_user) }

    it 'publishes the product' do
      post "/api/v1/products/#{product.id}/publish", headers: headers

      expect(response).to have_http_status(:ok)
      expect(product.reload).to be_status_active
    end
  end
end
```

## Factory

```ruby
# spec/factories/products.rb
FactoryBot.define do
  factory :product do
    category
    name { Faker::Commerce.product_name }
    description { Faker::Lorem.paragraph }
    price { Faker::Commerce.price(range: 10.0..100.0) }
    stock_quantity { rand(0..100) }
    status { :draft }

    trait :active do
      status { :active }
      published_at { Time.current }
    end

    trait :with_tags do
      transient { tags_count { 3 } }

      after(:create) do |product, evaluator|
        create_list(:tag, evaluator.tags_count).each do |tag|
          product.tags << tag
        end
      end
    end

    trait :on_sale do
      after(:build) do |product|
        product.compare_price = product.price * 1.25
      end
    end
  end
end
```
