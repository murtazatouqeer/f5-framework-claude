# Terraform Naming Conventions

## Overview

Consistent naming conventions improve readability, maintainability, and collaboration. This guide covers naming patterns for Terraform resources, variables, and files.

## Resource Naming

### General Principles

1. **Use lowercase with underscores** for Terraform identifiers
2. **Use lowercase with hyphens** for cloud resource names
3. **Be descriptive but concise**
4. **Include environment and purpose**
5. **Follow cloud provider conventions**

### Resource Identifier Pattern

```hcl
# Pattern: resource_type_purpose
resource "aws_s3_bucket" "application_data" {
  # ...
}

resource "aws_iam_role" "lambda_execution" {
  # ...
}

resource "aws_security_group" "database_access" {
  # ...
}
```

### Cloud Resource Name Pattern

```hcl
# Pattern: {project}-{environment}-{purpose}-{type}
locals {
  name_prefix = "${var.project}-${var.environment}"
}

resource "aws_s3_bucket" "main" {
  bucket = "${local.name_prefix}-application-data"
}

resource "aws_rds_cluster" "main" {
  cluster_identifier = "${local.name_prefix}-aurora-cluster"
}

resource "aws_eks_cluster" "main" {
  name = "${local.name_prefix}-cluster"
}
```

## Variable Naming

### Input Variables

```hcl
# Boolean: Use is_, has_, or enable_ prefix
variable "is_production" {
  type = bool
}

variable "has_public_ip" {
  type = bool
}

variable "enable_encryption" {
  type = bool
}

# Numeric: Use _count, _size, _limit suffix
variable "instance_count" {
  type = number
}

variable "disk_size_gb" {
  type = number
}

variable "max_connections" {
  type = number
}

# String: Descriptive name
variable "environment" {
  type = string
}

variable "vpc_cidr_block" {
  type = string
}

# List: Use plural form
variable "availability_zones" {
  type = list(string)
}

variable "subnet_ids" {
  type = list(string)
}

# Map: Use _map suffix or descriptive name
variable "tags" {
  type = map(string)
}

variable "environment_variables" {
  type = map(string)
}
```

### Local Values

```hcl
locals {
  # Computed values
  name_prefix     = "${var.project}-${var.environment}"
  account_id      = data.aws_caller_identity.current.account_id
  region          = data.aws_region.current.name

  # Configuration maps
  instance_types = {
    dev     = "t3.small"
    staging = "t3.medium"
    prod    = "t3.large"
  }

  # Common tags
  common_tags = {
    Project     = var.project
    Environment = var.environment
    ManagedBy   = "terraform"
  }

  # Derived values
  is_production      = var.environment == "prod"
  enable_multi_az    = local.is_production
  backup_retention   = local.is_production ? 30 : 7
}
```

### Output Values

```hcl
# Pattern: resource_attribute
output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = aws_eks_cluster.main.endpoint
}

output "database_connection_string" {
  description = "Database connection string"
  value       = "postgresql://${aws_db_instance.main.endpoint}/${var.database_name}"
  sensitive   = true
}

# For lists
output "private_subnet_ids" {
  description = "List of private subnet IDs"
  value       = aws_subnet.private[*].id
}

# For maps
output "security_group_ids" {
  description = "Map of security group IDs"
  value = {
    web      = aws_security_group.web.id
    app      = aws_security_group.app.id
    database = aws_security_group.database.id
  }
}
```

## File Naming

### Standard Files

| File | Purpose |
|------|---------|
| `main.tf` | Primary resources |
| `variables.tf` | Input variables |
| `outputs.tf` | Output values |
| `providers.tf` | Provider configuration |
| `versions.tf` | Version constraints |
| `locals.tf` | Local values |
| `data.tf` | Data sources |
| `backend.tf` | Backend configuration |

### Resource-Specific Files

```
# Pattern: {resource_type}.tf
networking.tf      # VPC, subnets, routes
compute.tf         # EC2, ASG, launch templates
database.tf        # RDS, Aurora, DynamoDB
storage.tf         # S3, EFS, EBS
security.tf        # Security groups, NACLs
iam.tf             # IAM roles, policies
monitoring.tf      # CloudWatch, alarms
dns.tf             # Route53
```

### Module Files

```
modules/
├── vpc/
│   ├── main.tf
│   ├── subnets.tf
│   ├── nat-gateway.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── versions.tf
```

## Cloud-Specific Conventions

### AWS Resource Names

```hcl
# S3 bucket (globally unique, lowercase)
resource "aws_s3_bucket" "main" {
  bucket = "${var.project}-${var.environment}-${var.purpose}-${random_id.bucket.hex}"
}

# IAM role (alphanumeric with special chars)
resource "aws_iam_role" "main" {
  name = "${var.project}-${var.environment}-${var.purpose}-role"
}

# EC2 instance (tags for display name)
resource "aws_instance" "main" {
  tags = {
    Name = "${var.project}-${var.environment}-${var.purpose}"
  }
}

# RDS instance (alphanumeric and hyphens)
resource "aws_db_instance" "main" {
  identifier = "${var.project}-${var.environment}-postgres"
}

# EKS cluster (alphanumeric, hyphens, underscores)
resource "aws_eks_cluster" "main" {
  name = "${var.project}-${var.environment}"
}

# Lambda function (alphanumeric, hyphens, underscores)
resource "aws_lambda_function" "main" {
  function_name = "${var.project}-${var.environment}-${var.purpose}"
}
```

### GCP Resource Names

```hcl
# GCE instance (lowercase, hyphens)
resource "google_compute_instance" "main" {
  name = "${var.project}-${var.environment}-${var.purpose}"
}

# GCS bucket (globally unique)
resource "google_storage_bucket" "main" {
  name = "${var.project}-${var.environment}-${var.purpose}-${random_id.bucket.hex}"
}

# GKE cluster (lowercase, hyphens)
resource "google_container_cluster" "main" {
  name = "${var.project}-${var.environment}"
}
```

### Azure Resource Names

```hcl
# Resource group
resource "azurerm_resource_group" "main" {
  name = "rg-${var.project}-${var.environment}"
}

# Virtual network
resource "azurerm_virtual_network" "main" {
  name = "vnet-${var.project}-${var.environment}"
}

# Storage account (lowercase, no hyphens, 3-24 chars)
resource "azurerm_storage_account" "main" {
  name = substr("st${var.project}${var.environment}", 0, 24)
}

# AKS cluster
resource "azurerm_kubernetes_cluster" "main" {
  name = "aks-${var.project}-${var.environment}"
}
```

## Tagging Strategy

### Standard Tags

```hcl
locals {
  required_tags = {
    Project      = var.project
    Environment  = var.environment
    ManagedBy    = "terraform"
    Owner        = var.owner
    CostCenter   = var.cost_center
    Application  = var.application
  }

  optional_tags = {
    CreatedAt    = timestamp()
    Repository   = var.repository_url
    TerraformDir = path.module
  }

  all_tags = merge(local.required_tags, local.optional_tags, var.additional_tags)
}

# Usage with AWS default tags
provider "aws" {
  default_tags {
    tags = local.required_tags
  }
}

# Resource-specific tags
resource "aws_instance" "main" {
  tags = merge(local.all_tags, {
    Name = "${local.name_prefix}-web-server"
    Role = "web"
  })
}
```

### Tag Variables

```hcl
variable "project" {
  description = "Project name for resource naming and tagging"
  type        = string

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,20}$", var.project))
    error_message = "Project name must be lowercase, start with letter, 3-21 chars."
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

variable "owner" {
  description = "Team or individual responsible for resources"
  type        = string
}

variable "cost_center" {
  description = "Cost center for billing allocation"
  type        = string
}
```

## Data Source Naming

```hcl
# Pattern: data_source_purpose
data "aws_ami" "amazon_linux_2" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
}

data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

# Remote state
data "terraform_remote_state" "vpc" {
  backend = "s3"
  config = {
    bucket = "terraform-state"
    key    = "vpc/terraform.tfstate"
    region = "us-east-1"
  }
}
```

## Module Naming

### Module Source Names

```hcl
# Local modules
module "vpc" {
  source = "./modules/vpc"
}

# Registry modules
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.0.0"
}

# Git modules
module "vpc" {
  source = "git::https://github.com/company/terraform-modules.git//vpc?ref=v1.0.0"
}
```

### Module Instance Names

```hcl
# Descriptive names for multiple instances
module "vpc_primary" {
  source = "./modules/vpc"
  # ...
}

module "vpc_secondary" {
  source = "./modules/vpc"
  # ...
}

# For_each with meaningful keys
module "database" {
  for_each = {
    users    = { instance_class = "db.t3.small" }
    orders   = { instance_class = "db.t3.medium" }
    analytics = { instance_class = "db.t3.large" }
  }

  source         = "./modules/rds"
  identifier     = "${local.name_prefix}-${each.key}"
  instance_class = each.value.instance_class
}
```

## Best Practices Summary

1. **Consistency**: Apply conventions uniformly across all code
2. **Clarity**: Names should describe purpose without ambiguity
3. **Brevity**: Keep names concise but meaningful
4. **Searchability**: Use patterns that enable easy grep/search
5. **Cloud compliance**: Follow cloud provider naming rules
6. **Documentation**: Document naming conventions in README
