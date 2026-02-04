# Product Schema Template

## Product Entity

```typescript
interface Product {
  id: string;
  sku: string;
  name: string;
  slug: string;
  description: string;
  shortDescription: string;

  // Pricing
  basePrice: Money;
  salePrice?: Money;
  costPrice?: Money;

  // Categorization
  categories: Category[];
  tags: string[];
  brand?: Brand;

  // Media
  images: ProductImage[];
  videos?: ProductVideo[];

  // Variants
  hasVariants: boolean;
  variants?: ProductVariant[];
  options?: ProductOption[];

  // Inventory
  trackInventory: boolean;
  stockQuantity?: number;
  lowStockThreshold?: number;

  // Shipping
  weight?: number;
  dimensions?: Dimensions;
  shippingClass?: string;

  // SEO
  metaTitle?: string;
  metaDescription?: string;

  // Status
  status: 'draft' | 'active' | 'archived';
  visibility: 'visible' | 'hidden' | 'search_only';

  // Timestamps
  createdAt: Date;
  updatedAt: Date;
  publishedAt?: Date;
}
```

## Variant Structure

```typescript
interface ProductVariant {
  id: string;
  sku: string;
  name: string;

  // Option values
  optionValues: OptionValue[];

  // Pricing (override)
  price?: Money;
  compareAtPrice?: Money;

  // Inventory
  stockQuantity: number;

  // Media
  image?: ProductImage;

  // Physical
  weight?: number;
  barcode?: string;
}

interface ProductOption {
  id: string;
  name: string; // e.g., "Size", "Color"
  position: number;
  values: OptionValue[];
}

interface OptionValue {
  id: string;
  name: string; // e.g., "Small", "Red"
  position: number;
}
```

## Category Structure

```typescript
interface Category {
  id: string;
  name: string;
  slug: string;
  description?: string;

  // Hierarchy
  parentId?: string;
  path: string; // e.g., "/electronics/phones/smartphones"
  level: number;

  // Media
  image?: string;

  // SEO
  metaTitle?: string;
  metaDescription?: string;

  // Status
  status: 'active' | 'inactive';

  // Sorting
  position: number;
}
```

## Money Type

```typescript
interface Money {
  amount: number;
  currency: string; // ISO 4217
}
```
