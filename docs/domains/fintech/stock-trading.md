# Stock Trading Domain - F5 Framework v1.2.0

## Entities
| Entity | Description | Attributes |
|--------|-------------|------------|
| Order | Trading order | 50+ |
| Position | Position | 20+ |
| Portfolio | Portfolio | 15+ |
| Quote | Quote | 25+ |

## Business Rules
- BR-ORD-001: Price must be within trading band
- BR-ORD-002: Quantity must be multiple of lot size (100)
- BR-ORD-003: Sell order requires sufficient securities
- BR-ORD-004: Buy order requires sufficient cash/margin

## Workflows
- order-lifecycle: Order lifecycle
- portfolio-rebalancing: Portfolio rebalancing
- margin-trading: Margin trading
- corporate-action: Corporate action

## Use Cases (28+)
- Trading: UC-TRADE-001 to 005
- Portfolio: UC-PORTFOLIO-001/002
- Account: UC-ACCOUNT-001 to 010
- Market Data: UC-MARKET-001 to 010
