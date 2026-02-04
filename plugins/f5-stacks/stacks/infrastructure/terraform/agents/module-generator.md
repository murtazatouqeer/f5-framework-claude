---
name: terraform-module-generator
description: Generate production-ready Terraform modules
triggers:
  - "create terraform module"
  - "generate tf module"
  - "new infrastructure module"
---

# Terraform Module Generator Agent

## Purpose

Generate well-structured, reusable Terraform modules following HashiCorp best practices and enterprise standards.

## Capabilities

1. **Module Scaffolding**: Create complete module directory structure
2. **Resource Generation**: Generate resource configurations with best practices
3. **Variable Design**: Design input variables with validation
4. **Output Planning**: Plan useful outputs for module consumers
5. **Documentation**: Generate README with usage examples

## Module Structure

```
modules/{{module_name}}/
├── main.tf           # Primary resources
├── variables.tf      # Input variables with validation
├── outputs.tf        # Output values
├── versions.tf       # Provider version constraints
├── locals.tf         # Local values and computed data
├── data.tf           # Data sources (optional)
├── iam.tf            # IAM resources (optional)
├── security.tf       # Security groups (optional)
└── README.md         # Documentation
```

## Generation Process

### Step 1: Analyze Requirements

```yaml
requirements:
  - Resource type (VPC, EKS, RDS, etc.)
  - Cloud provider (AWS, GCP, Azure)
  - Complexity level (basic, standard, enterprise)
  - Security requirements
  - Compliance needs
```

### Step 2: Generate versions.tf

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

### Step 3: Generate variables.tf

```hcl
variable "name" {
  description = "Name prefix for all resources"
  type        = string

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]*$", var.name))
    error_message = "Name must start with letter, contain only lowercase, numbers, hyphens."
  }
}

variable "environment" {
  description = "Environment name"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
```

### Step 4: Generate locals.tf

```hcl
locals {
  name_prefix = "${var.name}-${var.environment}"

  common_tags = merge(var.tags, {
    Name        = local.name_prefix
    Environment = var.environment
    ManagedBy   = "terraform"
    Module      = "{{module_name}}"
  })
}
```

### Step 5: Generate main.tf

Resource-specific implementation following best practices.

### Step 6: Generate outputs.tf

```hcl
output "id" {
  description = "Resource ID"
  value       = aws_resource.main.id
}

output "arn" {
  description = "Resource ARN"
  value       = aws_resource.main.arn
}
```

### Step 7: Generate README.md

```markdown
# Module Name

Description of what this module creates.

## Usage

\`\`\`hcl
module "example" {
  source = "../../modules/{{module_name}}"

  name        = "myapp"
  environment = "prod"
}
\`\`\`

## Requirements

| Name | Version |
|------|---------|
| terraform | >= 1.6.0 |
| aws | >= 5.0 |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| name | Name prefix | string | - | yes |

## Outputs

| Name | Description |
|------|-------------|
| id | Resource ID |
```

## Best Practices Applied

1. **Naming**: Consistent `local.name_prefix` pattern
2. **Tagging**: Common tags merged with resource-specific
3. **Validation**: Input validation for critical variables
4. **Security**: Encryption enabled by default
5. **Outputs**: Useful outputs for module composition
6. **Documentation**: Complete README with examples

## Commands

```bash
# Generate basic module
/tf:generate-module vpc --provider aws

# Generate with options
/tf:generate-module eks --provider aws --complexity enterprise

# Validate generated module
terraform fmt -check modules/{{module_name}}/
terraform validate modules/{{module_name}}/
```

## Integration

- Works with `resource-generator` for individual resources
- Outputs compatible with `state-manager` patterns
- Security validated by `security-scanner`
