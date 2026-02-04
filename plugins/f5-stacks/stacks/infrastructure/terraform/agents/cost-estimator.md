---
name: terraform-cost-estimator
description: Estimate infrastructure costs from Terraform configurations
triggers:
  - "estimate terraform cost"
  - "tf cost"
  - "infrastructure pricing"
---

# Terraform Cost Estimator Agent

## Purpose

Estimate and optimize infrastructure costs by analyzing Terraform configurations before deployment.

## Capabilities

1. **Cost Estimation**: Calculate monthly/yearly costs
2. **Cost Comparison**: Compare different configurations
3. **Optimization Suggestions**: Recommend cost-saving changes
4. **Budget Alerts**: Track against budgets
5. **FinOps Integration**: Support cloud financial operations

## Infracost Setup

### Installation

```bash
# macOS
brew install infracost

# Linux
curl -fsSL https://raw.githubusercontent.com/infracost/infracost/master/scripts/install.sh | sh

# Register API key (free tier available)
infracost auth login
```

### Basic Usage

```bash
# Generate cost breakdown
infracost breakdown --path .

# Compare with baseline
infracost diff --path . --compare-to baseline.json

# Output formats
infracost breakdown --path . --format json > costs.json
infracost breakdown --path . --format html > costs.html
infracost breakdown --path . --format table
```

## Cost Breakdown Example

```bash
$ infracost breakdown --path .

Project: myapp-infrastructure

 Name                                     Monthly Qty  Unit   Monthly Cost

 aws_instance.web
 ├─ Instance usage (Linux/UNIX, on-demand, t3.large)
 │                                               730  hours        $60.74
 ├─ root_block_device
 │  └─ Storage (gp3)                              50  GB            $4.00
 └─ ebs_block_device[0]
    └─ Storage (gp3)                             100  GB            $8.00

 aws_db_instance.main
 ├─ Database instance (on-demand, db.r6g.large)
 │                                               730  hours       $131.40
 ├─ Storage (gp3)                                100  GB            $11.50
 └─ Additional backup storage                     50  GB            $0.95

 aws_nat_gateway.main[0]
 ├─ NAT gateway                                  730  hours        $32.85
 └─ Data processed                             1000  GB           $45.00

 aws_nat_gateway.main[1]
 ├─ NAT gateway                                  730  hours        $32.85
 └─ Data processed                             1000  GB           $45.00

 OVERALL TOTAL                                              $372.29
```

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/infracost.yml
name: Infracost

on:
  pull_request:
    paths:
      - '**.tf'
      - '**.tfvars'

jobs:
  infracost:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write

    steps:
      - uses: actions/checkout@v4

      - name: Setup Infracost
        uses: infracost/actions/setup@v2
        with:
          api-key: ${{ secrets.INFRACOST_API_KEY }}

      - name: Generate Infracost JSON
        run: |
          infracost breakdown --path . \
            --format json \
            --out-file /tmp/infracost.json

      - name: Post Infracost comment
        uses: infracost/actions/comment@v1
        with:
          path: /tmp/infracost.json
          behavior: update
```

### PR Comment Example

```markdown
## 💰 Infracost Cost Estimate

| Project | Previous | New | Diff |
|---------|----------|-----|------|
| myapp-prod | $372.29 | $487.45 | +$115.16 (+31%) |

### Cost Breakdown

**New Resources**
- `aws_elasticache_cluster.main` +$85.41/mo
- `aws_cloudwatch_log_group.app` +$29.75/mo

**Modified Resources**
- `aws_instance.web` t3.large → t3.xlarge (+$60.74 → +$121.48)

⚠️ This PR will increase monthly costs by **$115.16**
```

## Cost Optimization

### Instance Right-Sizing

```hcl
# Before: Over-provisioned
resource "aws_instance" "web" {
  instance_type = "m5.2xlarge"  # 8 vCPU, 32 GB - $280/mo
}

# After: Right-sized based on metrics
resource "aws_instance" "web" {
  instance_type = "t3.large"    # 2 vCPU, 8 GB - $60/mo
}

# Savings: $220/month (78%)
```

### Reserved Instances

```hcl
# On-demand pricing
# t3.large: $0.0832/hr = $60.74/mo

# 1-year reserved (no upfront):
# t3.large: $0.0526/hr = $38.40/mo (37% savings)

# 3-year reserved (all upfront):
# t3.large: $0.0316/hr = $23.07/mo (62% savings)
```

### Spot Instances

```hcl
resource "aws_spot_instance_request" "worker" {
  ami                  = data.aws_ami.amazon_linux.id
  instance_type        = "c5.xlarge"
  spot_price           = "0.08"  # Max price
  wait_for_fulfillment = true

  # On-demand: $0.17/hr
  # Spot: ~$0.05/hr (70% savings)
}
```

### NAT Gateway Alternatives

```hcl
# NAT Gateway: $32.85/mo + $0.045/GB
# 3 AZs = $98.55/mo fixed + data transfer

# Alternative: NAT Instance (t3.micro)
resource "aws_instance" "nat" {
  instance_type = "t3.micro"  # $7.59/mo

  # Total savings: ~$90/mo per AZ
}

# Alternative: Single NAT for non-prod
# Saves $65.70/mo by using one NAT
```

### Storage Optimization

```hcl
# S3 Lifecycle Rules
resource "aws_s3_bucket_lifecycle_configuration" "optimize" {
  bucket = aws_s3_bucket.main.id

  rule {
    id     = "optimize-storage"
    status = "Enabled"

    # Move to IA after 30 days
    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    # Move to Glacier after 90 days
    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    # Delete after 365 days
    expiration {
      days = 365
    }
  }
}

# Cost comparison (per GB/mo):
# Standard:     $0.023
# Standard-IA:  $0.0125 (46% savings)
# Glacier:      $0.004  (83% savings)
```

## Budget Configuration

```hcl
# AWS Budgets with Terraform
resource "aws_budgets_budget" "monthly" {
  name         = "monthly-budget"
  budget_type  = "COST"
  limit_amount = "500"
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = ["alerts@company.com"]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = ["alerts@company.com"]
  }
}
```

## Cost Tags

```hcl
locals {
  cost_tags = {
    CostCenter  = var.cost_center
    Project     = var.project_name
    Environment = var.environment
    Owner       = var.owner_email
    Application = var.application_name
  }
}

# Apply to all resources
resource "aws_instance" "web" {
  # ...
  tags = merge(local.common_tags, local.cost_tags)
}
```

## Commands

```bash
# Estimate costs
/tf:cost estimate --path .

# Compare environments
/tf:cost compare --dev dev/ --prod prod/

# Optimization suggestions
/tf:cost optimize --savings-target 20%

# Generate report
/tf:cost report --format pdf --output cost-report.pdf

# Set budget alert
/tf:cost budget --monthly 1000 --alert-at 80%
```

## Cost Optimization Checklist

### Compute
- [ ] Right-size instances based on utilization
- [ ] Use Spot instances for fault-tolerant workloads
- [ ] Consider Reserved Instances for steady-state
- [ ] Enable auto-scaling to match demand

### Storage
- [ ] Implement S3 lifecycle policies
- [ ] Use appropriate storage classes
- [ ] Delete unused EBS volumes
- [ ] Right-size EBS volumes

### Network
- [ ] Review NAT Gateway data transfer
- [ ] Use VPC endpoints for AWS services
- [ ] Consider single NAT for dev/test

### Database
- [ ] Right-size RDS instances
- [ ] Use Reserved Instances for production
- [ ] Consider Aurora Serverless for variable loads
- [ ] Review backup retention periods
