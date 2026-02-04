# Agents Overview - F5 Framework v1.2.0

## What are Agents?

Agents are specialized AI assistants that help with specific tasks in your development workflow. Each agent has:
- Specific triggers that activate it
- Defined capabilities and outputs
- Integration with F5 quality gates

## Available Agents

### Base Agents
| Agent | Description | Triggers |
|-------|-------------|----------|
| base-researcher | Gathers context and evidence | `/f5-research` |
| base-designer | Creates design documents | `/f5-design` |
| base-implementer | Generates code | `/f5-implement` |
| base-validator | Multi-agent validation | `/f5-validate` |

### Domain Agents

#### Fintech
| Agent | Description | Triggers |
|-------|-------------|----------|
| fintech-security-auditor | Security compliance review | `security audit`, `compliance` |
| fintech-compliance-checker | Regulatory compliance | `regulatory`, `audit` |

#### E-Commerce
| Agent | Description | Triggers |
|-------|-------------|----------|
| ecommerce-catalog-designer | Product catalog design | `catalog`, `product` |
| ecommerce-checkout-designer | Checkout flow design | `checkout`, `cart` |
| ecommerce-fulfillment-designer | Order fulfillment | `fulfillment`, `shipping` |

### Stack Agents

#### NestJS
| Agent | Description | Triggers |
|-------|-------------|----------|
| nestjs-service-generator | Service layer generation | `nestjs service`, `nestjs module` |
| nestjs-api-designer | REST/GraphQL API design | `nestjs api`, `endpoint` |

#### Go
| Agent | Description | Triggers |
|-------|-------------|----------|
| go-service-generator | Go service generation | `go service`, `golang` |
| go-api-designer | Go API design | `go api`, `gin`, `fiber` |

#### React
| Agent | Description | Triggers |
|-------|-------------|----------|
| react-component-designer | Component design patterns | `react component`, `ui` |
| react-hook-generator | Custom hook generation | `react hook`, `useQuery` |

## Using Agents

Agents are automatically activated based on context. You can also explicitly invoke them:

```bash
# In Claude Code
/f5-research "stock trading order flow"  # Activates base-researcher + fintech agents
/f5-design --srs                          # Activates base-designer
```

## Agent Quality Gates

Each agent operates within F5's quality gate system:

| Gate | Agent Checkpoint |
|------|------------------|
| D1 | Research Complete - Evidence gathered |
| D2 | SRS Approved - Requirements documented |
| D3 | Design Approved - Architecture defined |
| G2 | Ready to Implement - Plan exists |
| G3 | Tests Pass - Coverage met |
| G4 | Ready to Deploy - All validations pass |
