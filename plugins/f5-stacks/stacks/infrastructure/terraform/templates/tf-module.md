---
name: tf-module
description: Template for creating reusable Terraform modules
applies_to: terraform
---

# Terraform Module Template

## Directory Structure

```
modules/{{module_name}}/
├── main.tf           # Primary resources
├── variables.tf      # Input variables with validation
├── outputs.tf        # Output values
├── versions.tf       # Provider version constraints
├── locals.tf         # Local values and computed data
├── data.tf           # Data sources (optional)
└── README.md         # Documentation
```

## versions.tf

```hcl
terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}
```

## variables.tf

```hcl
# =============================================================================
# Required Variables
# =============================================================================

variable "name" {
  description = "Name prefix for all resources"
  type        = string

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]*$", var.name))
    error_message = "Name must start with letter, contain only lowercase, numbers, hyphens."
  }
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

# =============================================================================
# Optional Variables
# =============================================================================

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}

# Add module-specific variables here
```

## locals.tf

```hcl
locals {
  # Naming
  name_prefix = "${var.name}-${var.environment}"

  # Common tags
  common_tags = merge(var.tags, {
    Name        = local.name_prefix
    Environment = var.environment
    ManagedBy   = "terraform"
    Module      = "{{module_name}}"
  })

  # Add module-specific locals here
}
```

## main.tf

```hcl
# =============================================================================
# {{MODULE_NAME}} Resources
# =============================================================================

# Primary resource
resource "aws_{{resource_type}}" "main" {
  name = local.name_prefix

  # Resource-specific configuration

  tags = local.common_tags
}

# Supporting resources
```

## outputs.tf

```hcl
# =============================================================================
# Primary Outputs
# =============================================================================

output "id" {
  description = "Resource ID"
  value       = aws_{{resource_type}}.main.id
}

output "arn" {
  description = "Resource ARN"
  value       = aws_{{resource_type}}.main.arn
}

# =============================================================================
# Connection/Integration Outputs
# =============================================================================

# Add outputs that other modules might need
```

## data.tf (Optional)

```hcl
# =============================================================================
# Data Sources
# =============================================================================

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# Conditional data sources
data "aws_vpc" "selected" {
  count = var.vpc_id != null ? 1 : 0
  id    = var.vpc_id
}
```

## README.md Template

```markdown
# {{Module Name}} Module

Terraform module for creating {{description}}.

## Features

- Feature 1
- Feature 2
- Feature 3

## Usage

### Basic

\`\`\`hcl
module "{{module_name}}" {
  source = "../../modules/{{module_name}}"

  name        = "myapp"
  environment = "prod"
}
\`\`\`

### Advanced

\`\`\`hcl
module "{{module_name}}" {
  source = "../../modules/{{module_name}}"

  name        = "myapp"
  environment = "prod"

  # Advanced options
  option1 = "value1"
  option2 = true

  tags = {
    Project = "MyProject"
    Team    = "Platform"
  }
}
\`\`\`

## Requirements

| Name | Version |
|------|---------|
| terraform | >= 1.6.0 |
| aws | >= 5.0 |

## Providers

| Name | Version |
|------|---------|
| aws | >= 5.0 |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| name | Name prefix for resources | `string` | n/a | yes |
| environment | Environment (dev/staging/prod) | `string` | n/a | yes |
| tags | Additional tags | `map(string)` | `{}` | no |

## Outputs

| Name | Description |
|------|-------------|
| id | Resource ID |
| arn | Resource ARN |

## Examples

See the `examples/` directory for complete usage examples.

## License

MIT
\`\`\`

## Best Practices Applied

1. **Naming Consistency**: Use `local.name_prefix` for all resources
2. **Tag Inheritance**: Merge common tags with resource-specific tags
3. **Input Validation**: Validate critical inputs at module boundary
4. **Sensitive Data**: Mark sensitive outputs appropriately
5. **Documentation**: Generate with terraform-docs
6. **Versioning**: Pin provider versions in versions.tf
