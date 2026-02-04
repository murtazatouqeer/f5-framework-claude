# Checkout Flow Template

## Overview

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    Cart     │────▶│   Address   │────▶│  Shipping   │────▶│   Payment   │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                                                                   │
                                                                   ▼
                                                            ┌─────────────┐
                                                            │   Review    │
                                                            └─────────────┘
                                                                   │
                                                                   ▼
                                                            ┌─────────────┐
                                                            │ Confirmation│
                                                            └─────────────┘
```

## Step 1: Cart Review

### Requirements
- Display cart items with images, names, quantities, prices
- Allow quantity updates
- Show subtotal, shipping estimate, taxes
- Validate stock availability
- Apply coupon codes

### API Endpoints
```
GET  /api/cart
PUT  /api/cart/items/{id}
DELETE /api/cart/items/{id}
POST /api/cart/coupon
```

## Step 2: Shipping Address

### Requirements
- Collect shipping address
- Address validation
- Save address for logged-in users
- Support multiple addresses

### Fields
- Full name
- Address line 1
- Address line 2 (optional)
- City
- State/Province
- Postal code
- Country
- Phone number

## Step 3: Shipping Method

### Requirements
- Calculate shipping rates
- Display delivery estimates
- Support multiple carriers
- Free shipping threshold

### Options Example
```json
{
  "shippingMethods": [
    {
      "id": "standard",
      "name": "Standard Shipping",
      "price": 5.99,
      "estimatedDays": "5-7 business days"
    },
    {
      "id": "express",
      "name": "Express Shipping",
      "price": 15.99,
      "estimatedDays": "2-3 business days"
    }
  ]
}
```

## Step 4: Payment

### Requirements
- PCI-DSS compliant payment form
- Support multiple payment methods
- Save payment method option
- 3D Secure support

### Payment Methods
- Credit/Debit cards (Stripe)
- Digital wallets (PayPal, Apple Pay, Google Pay)
- Local methods (VNPay, MoMo)
- Buy Now Pay Later (Klarna, Afterpay)

## Step 5: Order Review

### Requirements
- Display complete order summary
- Show all costs breakdown
- Terms acceptance checkbox
- Edit links for each section

### Summary Structure
```json
{
  "items": [...],
  "shippingAddress": {...},
  "shippingMethod": {...},
  "paymentMethod": {...},
  "pricing": {
    "subtotal": 99.99,
    "shipping": 5.99,
    "tax": 8.50,
    "discount": -10.00,
    "total": 104.48
  }
}
```

## Step 6: Order Confirmation

### Requirements
- Display order number
- Send confirmation email
- Show estimated delivery
- Provide tracking information when available

## Order States

```
┌──────────┐
│ Pending  │──────▶ Payment processing
└──────────┘
      │
      ▼
┌──────────┐
│  Paid    │──────▶ Payment confirmed
└──────────┘
      │
      ▼
┌──────────┐
│Processing│──────▶ Preparing for shipment
└──────────┘
      │
      ▼
┌──────────┐
│ Shipped  │──────▶ In transit
└──────────┘
      │
      ▼
┌──────────┐
│Delivered │──────▶ Complete
└──────────┘
```
