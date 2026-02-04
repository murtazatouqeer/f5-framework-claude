-- V1__create_products_table.sql
-- Description: Create products table with full auditing and soft delete support

-- Create categories table first (products depend on it)
CREATE TABLE IF NOT EXISTS categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description VARCHAR(500),
    parent_id UUID REFERENCES categories(id),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create products table
CREATE TABLE products (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Business Fields
    name VARCHAR(100) NOT NULL,
    description VARCHAR(2000),
    sku VARCHAR(50) UNIQUE,
    price NUMERIC(19, 4) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'DRAFT',
    stock_quantity INTEGER NOT NULL DEFAULT 0,
    is_featured BOOLEAN NOT NULL DEFAULT FALSE,

    -- Foreign Keys
    category_id UUID REFERENCES categories(id) ON DELETE SET NULL,

    -- Auditing Fields
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by VARCHAR(255),
    updated_by VARCHAR(255),

    -- Soft Delete
    deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,

    -- Optimistic Locking
    version BIGINT NOT NULL DEFAULT 0,

    -- Constraints
    CONSTRAINT chk_products_status
        CHECK (status IN ('DRAFT', 'ACTIVE', 'INACTIVE', 'ARCHIVED')),
    CONSTRAINT chk_products_price_positive
        CHECK (price >= 0),
    CONSTRAINT chk_products_stock_non_negative
        CHECK (stock_quantity >= 0)
);

-- Product tags (element collection)
CREATE TABLE product_tags (
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    tag VARCHAR(50) NOT NULL,
    PRIMARY KEY (product_id, tag)
);

-- Indexes for products table
CREATE INDEX idx_products_name ON products(name);
CREATE INDEX idx_products_sku ON products(sku) WHERE sku IS NOT NULL;
CREATE INDEX idx_products_status ON products(status) WHERE deleted = FALSE;
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_products_price ON products(price) WHERE deleted = FALSE;
CREATE INDEX idx_products_featured ON products(is_featured) WHERE deleted = FALSE AND is_featured = TRUE;
CREATE INDEX idx_products_created_at ON products(created_at);
CREATE INDEX idx_products_deleted ON products(deleted) WHERE deleted = FALSE;

-- Index for product tags
CREATE INDEX idx_product_tags_tag ON product_tags(tag);

-- Trigger for auto-updating updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS trigger AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER products_updated_at
    BEFORE UPDATE ON products
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comments
COMMENT ON TABLE products IS 'Products table - stores product information';
COMMENT ON COLUMN products.id IS 'Unique identifier (UUID)';
COMMENT ON COLUMN products.name IS 'Product name';
COMMENT ON COLUMN products.description IS 'Product description';
COMMENT ON COLUMN products.sku IS 'Stock Keeping Unit - unique product identifier';
COMMENT ON COLUMN products.price IS 'Product price with 4 decimal precision';
COMMENT ON COLUMN products.status IS 'Product status: DRAFT, ACTIVE, INACTIVE, ARCHIVED';
COMMENT ON COLUMN products.stock_quantity IS 'Available stock quantity';
COMMENT ON COLUMN products.is_featured IS 'Whether product is featured on homepage';
COMMENT ON COLUMN products.deleted IS 'Soft delete flag';
COMMENT ON COLUMN products.version IS 'Optimistic locking version';

-- Insert sample categories
INSERT INTO categories (id, name, description) VALUES
    ('11111111-1111-1111-1111-111111111111', 'Electronics', 'Electronic devices and accessories'),
    ('22222222-2222-2222-2222-222222222222', 'Clothing', 'Apparel and fashion items'),
    ('33333333-3333-3333-3333-333333333333', 'Books', 'Books and publications');

-- Insert sample products
INSERT INTO products (name, description, sku, price, status, stock_quantity, is_featured, category_id, created_by) VALUES
    ('Laptop Pro 15', 'High-performance laptop for professionals', 'LAP-PRO-15', 1299.99, 'ACTIVE', 50, TRUE, '11111111-1111-1111-1111-111111111111', 'system'),
    ('Wireless Mouse', 'Ergonomic wireless mouse', 'MOU-WIR-01', 49.99, 'ACTIVE', 200, FALSE, '11111111-1111-1111-1111-111111111111', 'system'),
    ('Classic T-Shirt', 'Cotton t-shirt in multiple colors', 'TSH-CLS-01', 24.99, 'ACTIVE', 500, FALSE, '22222222-2222-2222-2222-222222222222', 'system');
