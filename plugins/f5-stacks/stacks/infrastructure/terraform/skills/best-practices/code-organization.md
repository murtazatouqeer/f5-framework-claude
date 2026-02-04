# Terraform Code Organization

## Overview

Proper code organization is essential for maintainable Terraform projects. This guide covers file structure, module organization, and project layout patterns.

## File Structure

### Standard File Layout

```
project/
├── main.tf              # Primary resources
├── variables.tf         # Input variable declarations
├── outputs.tf           # Output declarations
├── providers.tf         # Provider configuration
├── versions.tf          # Version constraints
├── locals.tf            # Local values
├── data.tf              # Data sources
├── terraform.tfvars     # Default variable values
└── README.md            # Documentation
```

### Resource-Specific Files

For larger projects, split by resource type:

```
project/
├── main.tf              # Core resources, locals
├── networking.tf        # VPC, subnets, security groups
├── compute.tf           # EC2, ASG, launch templates
├── database.tf          # RDS, ElastiCache
├── storage.tf           # S3, EFS
├── iam.tf               # IAM roles, policies
├── monitoring.tf        # CloudWatch, alarms
├── variables.tf
├── outputs.tf
├── providers.tf
├── versions.tf
└── terraform.tfvars
```

### Environment-Based Structure

```
infrastructure/
├── modules/                    # Reusable modules
│   ├── vpc/
│   ├── eks/
│   └── rds/
├── environments/
│   ├── dev/
│   │   ├── main.tf
│   │   ├── terraform.tfvars
│   │   └── backend.tf
│   ├── staging/
│   │   ├── main.tf
│   │   ├── terraform.tfvars
│   │   └── backend.tf
│   └── prod/
│       ├── main.tf
│       ├── terraform.tfvars
│       └── backend.tf
└── shared/                     # Shared resources
    └── global/
```

## Module Organization

### Module Structure

```
modules/
├── vpc/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── versions.tf
│   ├── README.md
│   └── examples/
│       └── complete/
│           ├── main.tf
│           └── outputs.tf
├── eks/
│   ├── main.tf
│   ├── node-pools.tf
│   ├── iam.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── versions.tf
└── rds/
    ├── main.tf
    ├── security-group.tf
    ├── parameter-group.tf
    ├── variables.tf
    └── outputs.tf
```

### Module Composition Pattern

```
infrastructure/
├── modules/
│   ├── base/                   # Layer 1: Foundation
│   │   ├── vpc/
│   │   └── iam-baseline/
│   ├── data/                   # Layer 2: Data
│   │   ├── rds/
│   │   ├── elasticache/
│   │   └── s3/
│   ├── compute/                # Layer 3: Compute
│   │   ├── eks/
│   │   ├── ecs/
│   │   └── ec2/
│   └── edge/                   # Layer 4: Edge
│       ├── cloudfront/
│       ├── alb/
│       └── api-gateway/
└── stacks/
    ├── network/                # Deploys base modules
    ├── data/                   # Deploys data modules
    ├── compute/                # Deploys compute modules
    └── edge/                   # Deploys edge modules
```

## Project Patterns

### Monorepo Pattern

```
terraform-infrastructure/
├── .github/
│   └── workflows/
│       └── terraform.yml
├── modules/
│   ├── aws/
│   │   ├── vpc/
│   │   └── eks/
│   └── common/
│       └── tags/
├── live/
│   ├── production/
│   │   ├── us-east-1/
│   │   │   ├── vpc/
│   │   │   ├── eks/
│   │   │   └── rds/
│   │   └── eu-west-1/
│   │       ├── vpc/
│   │       └── eks/
│   └── staging/
│       └── us-east-1/
│           ├── vpc/
│           └── eks/
├── scripts/
│   ├── plan.sh
│   └── apply.sh
├── Makefile
└── README.md
```

### Terragrunt Structure

```
infrastructure/
├── terragrunt.hcl              # Root configuration
├── modules/
│   ├── vpc/
│   └── eks/
├── _env/
│   ├── dev.hcl
│   ├── staging.hcl
│   └── prod.hcl
└── live/
    ├── dev/
    │   ├── vpc/
    │   │   └── terragrunt.hcl
    │   └── eks/
    │       └── terragrunt.hcl
    ├── staging/
    │   ├── vpc/
    │   │   └── terragrunt.hcl
    │   └── eks/
    │       └── terragrunt.hcl
    └── prod/
        ├── vpc/
        │   └── terragrunt.hcl
        └── eks/
            └── terragrunt.hcl
```

## Configuration Patterns

### versions.tf

```hcl
terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.11"
    }
  }
}
```

### providers.tf

```hcl
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
}

provider "kubernetes" {
  host                   = module.eks.cluster_endpoint
  cluster_ca_certificate = base64decode(module.eks.cluster_ca_certificate)
  token                  = data.aws_eks_cluster_auth.main.token
}
```

### backend.tf

```hcl
terraform {
  backend "s3" {
    bucket         = "company-terraform-state"
    key            = "project/environment/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
```

### locals.tf

```hcl
locals {
  # Environment configuration
  environment_config = {
    dev = {
      instance_count = 1
      instance_type  = "t3.small"
    }
    staging = {
      instance_count = 2
      instance_type  = "t3.medium"
    }
    prod = {
      instance_count = 3
      instance_type  = "t3.large"
    }
  }

  # Current environment settings
  env_settings = local.environment_config[var.environment]

  # Common tags
  common_tags = {
    Project     = var.project
    Environment = var.environment
    ManagedBy   = "terraform"
    Owner       = var.owner
  }

  # Resource naming
  name_prefix = "${var.project}-${var.environment}"
}
```

## Module Interface Design

### Well-Designed Module Variables

```hcl
# modules/vpc/variables.tf

variable "name" {
  description = "Name prefix for VPC resources"
  type        = string
}

variable "cidr_block" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"

  validation {
    condition     = can(cidrnetmask(var.cidr_block))
    error_message = "Must be a valid CIDR block."
  }
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
}

variable "private_subnets" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = []
}

variable "public_subnets" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = []
}

variable "enable_nat_gateway" {
  description = "Enable NAT gateway for private subnets"
  type        = bool
  default     = true
}

variable "single_nat_gateway" {
  description = "Use single NAT gateway for all AZs"
  type        = bool
  default     = false
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
```

### Well-Designed Module Outputs

```hcl
# modules/vpc/outputs.tf

output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = aws_vpc.main.cidr_block
}

output "private_subnet_ids" {
  description = "List of private subnet IDs"
  value       = aws_subnet.private[*].id
}

output "public_subnet_ids" {
  description = "List of public subnet IDs"
  value       = aws_subnet.public[*].id
}

output "nat_gateway_ids" {
  description = "List of NAT gateway IDs"
  value       = aws_nat_gateway.main[*].id
}

output "private_route_table_ids" {
  description = "List of private route table IDs"
  value       = aws_route_table.private[*].id
}

# Convenience outputs for common use cases
output "database_subnet_group_name" {
  description = "Name of database subnet group"
  value       = try(aws_db_subnet_group.main[0].name, null)
}
```

## Documentation

### Module README Template

```markdown
# Module Name

Brief description of what this module does.

## Usage

\`\`\`hcl
module "example" {
  source = "./modules/example"

  name        = "my-resource"
  environment = "prod"
}
\`\`\`

## Requirements

| Name | Version |
|------|---------|
| terraform | >= 1.6.0 |
| aws | ~> 5.0 |

## Providers

| Name | Version |
|------|---------|
| aws | ~> 5.0 |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| name | Resource name | `string` | n/a | yes |
| environment | Environment name | `string` | n/a | yes |

## Outputs

| Name | Description |
|------|-------------|
| id | Resource ID |
| arn | Resource ARN |

## Examples

- [Complete](./examples/complete)
- [Minimal](./examples/minimal)
\`\`\`
```

## Best Practices Summary

### File Organization
1. **Consistent naming**: Use lowercase with hyphens
2. **Logical grouping**: Group related resources
3. **Separation of concerns**: Keep variables, outputs, providers separate
4. **Environment isolation**: Separate state per environment

### Module Design
1. **Single responsibility**: Each module does one thing well
2. **Minimal interface**: Expose only necessary variables
3. **Sensible defaults**: Provide defaults where appropriate
4. **Comprehensive outputs**: Export useful information

### Code Quality
1. **Format code**: Use `terraform fmt`
2. **Validate configuration**: Use `terraform validate`
3. **Document modules**: Include README with examples
4. **Version control**: Use semantic versioning for modules
