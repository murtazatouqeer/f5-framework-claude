---
name: tf-vpc
description: Template for AWS VPC module with production-ready networking
applies_to: terraform
---

# AWS VPC Module Template

## Overview

Production-ready VPC module with public/private/database subnets, NAT gateways,
VPC endpoints, and flow logs.

## Directory Structure

```
modules/vpc/
├── main.tf
├── subnets.tf
├── nat.tf
├── routes.tf
├── endpoints.tf
├── flow-logs.tf
├── variables.tf
├── outputs.tf
├── versions.tf
└── README.md
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

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"

  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0))
    error_message = "Must be a valid CIDR block."
  }
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)

  validation {
    condition     = length(var.availability_zones) >= 2
    error_message = "At least 2 availability zones required for HA."
  }
}

variable "region" {
  description = "AWS region"
  type        = string
}

# =============================================================================
# Subnet Configuration
# =============================================================================

variable "create_public_subnets" {
  description = "Create public subnets"
  type        = bool
  default     = true
}

variable "create_private_subnets" {
  description = "Create private subnets"
  type        = bool
  default     = true
}

variable "create_database_subnets" {
  description = "Create isolated database subnets"
  type        = bool
  default     = true
}

variable "public_subnet_suffix" {
  description = "Suffix for public subnet names"
  type        = string
  default     = "public"
}

variable "private_subnet_suffix" {
  description = "Suffix for private subnet names"
  type        = string
  default     = "private"
}

variable "database_subnet_suffix" {
  description = "Suffix for database subnet names"
  type        = string
  default     = "database"
}

# =============================================================================
# NAT Gateway Configuration
# =============================================================================

variable "enable_nat_gateway" {
  description = "Enable NAT gateway for private subnets"
  type        = bool
  default     = true
}

variable "single_nat_gateway" {
  description = "Use single NAT gateway (cost saving for non-prod)"
  type        = bool
  default     = false
}

# =============================================================================
# VPC Endpoints
# =============================================================================

variable "enable_s3_endpoint" {
  description = "Enable S3 VPC endpoint (Gateway)"
  type        = bool
  default     = true
}

variable "enable_dynamodb_endpoint" {
  description = "Enable DynamoDB VPC endpoint (Gateway)"
  type        = bool
  default     = false
}

variable "enable_ecr_endpoints" {
  description = "Enable ECR VPC endpoints (Interface)"
  type        = bool
  default     = false
}

variable "enable_ssm_endpoints" {
  description = "Enable SSM VPC endpoints (Interface)"
  type        = bool
  default     = false
}

# =============================================================================
# Flow Logs
# =============================================================================

variable "enable_flow_logs" {
  description = "Enable VPC flow logs"
  type        = bool
  default     = true
}

variable "flow_logs_retention_days" {
  description = "Flow logs retention in days"
  type        = number
  default     = 30
}

# =============================================================================
# Tags
# =============================================================================

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}

variable "public_subnet_tags" {
  description = "Additional tags for public subnets"
  type        = map(string)
  default     = {}
}

variable "private_subnet_tags" {
  description = "Additional tags for private subnets"
  type        = map(string)
  default     = {}
}

variable "database_subnet_tags" {
  description = "Additional tags for database subnets"
  type        = map(string)
  default     = {}
}
```

## main.tf

```hcl
locals {
  name_prefix = var.name

  common_tags = merge(var.tags, {
    Module    = "vpc"
    ManagedBy = "terraform"
  })

  # Calculate subnet CIDRs
  public_subnet_cidrs   = [for i in range(length(var.availability_zones)) : cidrsubnet(var.vpc_cidr, 4, i)]
  private_subnet_cidrs  = [for i in range(length(var.availability_zones)) : cidrsubnet(var.vpc_cidr, 4, i + length(var.availability_zones))]
  database_subnet_cidrs = [for i in range(length(var.availability_zones)) : cidrsubnet(var.vpc_cidr, 4, i + 2 * length(var.availability_zones))]
}

# =============================================================================
# VPC
# =============================================================================

resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-vpc"
  })
}

# =============================================================================
# Internet Gateway
# =============================================================================

resource "aws_internet_gateway" "main" {
  count = var.create_public_subnets ? 1 : 0

  vpc_id = aws_vpc.main.id

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-igw"
  })
}
```

## subnets.tf

```hcl
# =============================================================================
# Public Subnets
# =============================================================================

resource "aws_subnet" "public" {
  count = var.create_public_subnets ? length(var.availability_zones) : 0

  vpc_id                  = aws_vpc.main.id
  cidr_block              = local.public_subnet_cidrs[count.index]
  availability_zone       = var.availability_zones[count.index]
  map_public_ip_on_launch = true

  tags = merge(local.common_tags, var.public_subnet_tags, {
    Name                        = "${local.name_prefix}-${var.public_subnet_suffix}-${var.availability_zones[count.index]}"
    Type                        = "public"
    "kubernetes.io/role/elb"    = "1"
  })
}

# =============================================================================
# Private Subnets
# =============================================================================

resource "aws_subnet" "private" {
  count = var.create_private_subnets ? length(var.availability_zones) : 0

  vpc_id            = aws_vpc.main.id
  cidr_block        = local.private_subnet_cidrs[count.index]
  availability_zone = var.availability_zones[count.index]

  tags = merge(local.common_tags, var.private_subnet_tags, {
    Name                              = "${local.name_prefix}-${var.private_subnet_suffix}-${var.availability_zones[count.index]}"
    Type                              = "private"
    "kubernetes.io/role/internal-elb" = "1"
  })
}

# =============================================================================
# Database Subnets
# =============================================================================

resource "aws_subnet" "database" {
  count = var.create_database_subnets ? length(var.availability_zones) : 0

  vpc_id            = aws_vpc.main.id
  cidr_block        = local.database_subnet_cidrs[count.index]
  availability_zone = var.availability_zones[count.index]

  tags = merge(local.common_tags, var.database_subnet_tags, {
    Name = "${local.name_prefix}-${var.database_subnet_suffix}-${var.availability_zones[count.index]}"
    Type = "database"
  })
}

# Database Subnet Group
resource "aws_db_subnet_group" "main" {
  count = var.create_database_subnets ? 1 : 0

  name        = "${local.name_prefix}-db-subnet-group"
  description = "Database subnet group for ${local.name_prefix}"
  subnet_ids  = aws_subnet.database[*].id

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-db-subnet-group"
  })
}

# ElastiCache Subnet Group
resource "aws_elasticache_subnet_group" "main" {
  count = var.create_database_subnets ? 1 : 0

  name        = "${local.name_prefix}-cache-subnet-group"
  description = "ElastiCache subnet group for ${local.name_prefix}"
  subnet_ids  = aws_subnet.database[*].id

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-cache-subnet-group"
  })
}
```

## nat.tf

```hcl
# =============================================================================
# NAT Gateways
# =============================================================================

locals {
  nat_gateway_count = var.enable_nat_gateway && var.create_private_subnets ? (
    var.single_nat_gateway ? 1 : length(var.availability_zones)
  ) : 0
}

# Elastic IPs for NAT
resource "aws_eip" "nat" {
  count  = local.nat_gateway_count
  domain = "vpc"

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-nat-eip-${count.index + 1}"
  })

  depends_on = [aws_internet_gateway.main]
}

# NAT Gateways
resource "aws_nat_gateway" "main" {
  count = local.nat_gateway_count

  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-nat-${count.index + 1}"
  })

  depends_on = [aws_internet_gateway.main]
}
```

## routes.tf

```hcl
# =============================================================================
# Public Route Table
# =============================================================================

resource "aws_route_table" "public" {
  count = var.create_public_subnets ? 1 : 0

  vpc_id = aws_vpc.main.id

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-public-rt"
  })
}

resource "aws_route" "public_internet" {
  count = var.create_public_subnets ? 1 : 0

  route_table_id         = aws_route_table.public[0].id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.main[0].id
}

resource "aws_route_table_association" "public" {
  count = var.create_public_subnets ? length(var.availability_zones) : 0

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public[0].id
}

# =============================================================================
# Private Route Tables
# =============================================================================

resource "aws_route_table" "private" {
  count = var.create_private_subnets ? (
    var.single_nat_gateway ? 1 : length(var.availability_zones)
  ) : 0

  vpc_id = aws_vpc.main.id

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-private-rt-${count.index + 1}"
  })
}

resource "aws_route" "private_nat" {
  count = var.enable_nat_gateway && var.create_private_subnets ? (
    var.single_nat_gateway ? 1 : length(var.availability_zones)
  ) : 0

  route_table_id         = aws_route_table.private[count.index].id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = aws_nat_gateway.main[count.index].id
}

resource "aws_route_table_association" "private" {
  count = var.create_private_subnets ? length(var.availability_zones) : 0

  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[var.single_nat_gateway ? 0 : count.index].id
}

# =============================================================================
# Database Route Tables (no internet access)
# =============================================================================

resource "aws_route_table" "database" {
  count = var.create_database_subnets ? 1 : 0

  vpc_id = aws_vpc.main.id

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-database-rt"
  })
}

resource "aws_route_table_association" "database" {
  count = var.create_database_subnets ? length(var.availability_zones) : 0

  subnet_id      = aws_subnet.database[count.index].id
  route_table_id = aws_route_table.database[0].id
}
```

## outputs.tf

```hcl
# =============================================================================
# VPC Outputs
# =============================================================================

output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "vpc_cidr" {
  description = "VPC CIDR block"
  value       = aws_vpc.main.cidr_block
}

output "vpc_arn" {
  description = "VPC ARN"
  value       = aws_vpc.main.arn
}

# =============================================================================
# Subnet Outputs
# =============================================================================

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = aws_subnet.public[*].id
}

output "public_subnet_cidrs" {
  description = "Public subnet CIDR blocks"
  value       = aws_subnet.public[*].cidr_block
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = aws_subnet.private[*].id
}

output "private_subnet_cidrs" {
  description = "Private subnet CIDR blocks"
  value       = aws_subnet.private[*].cidr_block
}

output "database_subnet_ids" {
  description = "Database subnet IDs"
  value       = aws_subnet.database[*].id
}

output "database_subnet_cidrs" {
  description = "Database subnet CIDR blocks"
  value       = aws_subnet.database[*].cidr_block
}

# =============================================================================
# Subnet Groups
# =============================================================================

output "database_subnet_group_name" {
  description = "Database subnet group name"
  value       = try(aws_db_subnet_group.main[0].name, null)
}

output "elasticache_subnet_group_name" {
  description = "ElastiCache subnet group name"
  value       = try(aws_elasticache_subnet_group.main[0].name, null)
}

# =============================================================================
# Gateway Outputs
# =============================================================================

output "internet_gateway_id" {
  description = "Internet Gateway ID"
  value       = try(aws_internet_gateway.main[0].id, null)
}

output "nat_gateway_ids" {
  description = "NAT Gateway IDs"
  value       = aws_nat_gateway.main[*].id
}

output "nat_gateway_ips" {
  description = "NAT Gateway public IPs"
  value       = aws_eip.nat[*].public_ip
}

# =============================================================================
# Route Table Outputs
# =============================================================================

output "public_route_table_id" {
  description = "Public route table ID"
  value       = try(aws_route_table.public[0].id, null)
}

output "private_route_table_ids" {
  description = "Private route table IDs"
  value       = aws_route_table.private[*].id
}

output "database_route_table_id" {
  description = "Database route table ID"
  value       = try(aws_route_table.database[0].id, null)
}
```

## Usage Example

```hcl
module "vpc" {
  source = "../../modules/vpc"

  name               = "myapp-prod"
  vpc_cidr           = "10.0.0.0/16"
  region             = "us-east-1"
  availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]

  # Subnet configuration
  create_public_subnets   = true
  create_private_subnets  = true
  create_database_subnets = true

  # NAT configuration (HA for production)
  enable_nat_gateway = true
  single_nat_gateway = false

  # VPC endpoints
  enable_s3_endpoint   = true
  enable_ecr_endpoints = true

  # Flow logs
  enable_flow_logs         = true
  flow_logs_retention_days = 30

  tags = {
    Environment = "production"
    Project     = "myapp"
  }

  # Kubernetes tags for EKS
  public_subnet_tags = {
    "kubernetes.io/cluster/myapp-prod" = "shared"
  }
  private_subnet_tags = {
    "kubernetes.io/cluster/myapp-prod" = "shared"
  }
}
```
