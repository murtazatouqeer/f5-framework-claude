# Input Variables

## Overview

Input variables allow you to parameterize Terraform configurations, making them reusable across different environments and use cases.

## Variable Declaration

### Basic Syntax

```hcl
variable "name" {
  description = "Description of the variable"
  type        = string
  default     = "default-value"
}
```

### Complete Variable Block

```hcl
variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
  nullable    = false
  sensitive   = false

  validation {
    condition     = can(regex("^t3\\.", var.instance_type))
    error_message = "Instance type must be t3 family."
  }
}
```

## Variable Types

### Primitive Types

```hcl
# String
variable "name" {
  type    = string
  default = "my-resource"
}

# Number
variable "instance_count" {
  type    = number
  default = 1
}

# Boolean
variable "enabled" {
  type    = bool
  default = true
}
```

### Collection Types

```hcl
# List
variable "availability_zones" {
  type    = list(string)
  default = ["us-east-1a", "us-east-1b"]
}

# Set (unordered, unique values)
variable "allowed_ips" {
  type    = set(string)
  default = []
}

# Map
variable "tags" {
  type = map(string)
  default = {
    Environment = "dev"
  }
}
```

### Structural Types

```hcl
# Object
variable "instance_config" {
  type = object({
    ami           = string
    instance_type = string
    volume_size   = number
    monitoring    = optional(bool, false)
  })

  default = {
    ami           = "ami-0123456789"
    instance_type = "t3.micro"
    volume_size   = 20
  }
}

# Tuple
variable "network_config" {
  type    = tuple([string, number, bool])
  default = ["10.0.0.0/16", 3, true]
}
```

### Complex Nested Types

```hcl
# List of objects
variable "subnets" {
  type = list(object({
    name       = string
    cidr_block = string
    az         = string
    public     = optional(bool, false)
  }))

  default = [
    {
      name       = "public-1"
      cidr_block = "10.0.1.0/24"
      az         = "us-east-1a"
      public     = true
    },
    {
      name       = "private-1"
      cidr_block = "10.0.2.0/24"
      az         = "us-east-1a"
    }
  ]
}

# Map of objects
variable "instances" {
  type = map(object({
    instance_type = string
    ami           = string
    subnet_key    = string
  }))

  default = {
    web = {
      instance_type = "t3.small"
      ami           = "ami-web"
      subnet_key    = "public-1"
    }
    api = {
      instance_type = "t3.medium"
      ami           = "ami-api"
      subnet_key    = "private-1"
    }
  }
}
```

### Any Type

```hcl
# Accepts any type
variable "flexible_config" {
  type    = any
  default = null
}

# Common use case: complex defaults
variable "settings" {
  type = any
  default = {
    feature_a = true
    limits = {
      max_connections = 100
      timeout         = 30
    }
  }
}
```

## Optional Attributes

### Optional with Default (Terraform 1.3+)

```hcl
variable "config" {
  type = object({
    name     = string
    size     = optional(number, 10)
    enabled  = optional(bool, true)
    tags     = optional(map(string), {})
  })
}

# Usage - only name is required
config = {
  name = "my-resource"
}

# Defaults are applied:
# size = 10
# enabled = true
# tags = {}
```

### Nested Optional Attributes

```hcl
variable "database" {
  type = object({
    engine         = string
    version        = optional(string, "14.0")
    instance_class = optional(string, "db.t3.micro")

    storage = optional(object({
      size      = optional(number, 20)
      type      = optional(string, "gp3")
      encrypted = optional(bool, true)
    }), {})

    backup = optional(object({
      retention_days = optional(number, 7)
      window         = optional(string, "03:00-04:00")
    }), null)
  })
}
```

## Nullable Variables

```hcl
# Default: nullable = true (can be set to null)
variable "optional_value" {
  type    = string
  default = null
}

# nullable = false (cannot be set to null)
variable "required_value" {
  type     = string
  nullable = false
  default  = ""  # Must provide non-null default
}

# Usage in resources
resource "aws_instance" "example" {
  # Conditional based on null
  key_name = var.optional_value != null ? var.optional_value : null
}
```

## Sensitive Variables

```hcl
variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

variable "api_key" {
  description = "API key for external service"
  type        = string
  sensitive   = true
}

# Terraform will hide these values in output
# terraform plan shows:
# + password = (sensitive value)
```

## Setting Variable Values

### terraform.tfvars

```hcl
# terraform.tfvars (auto-loaded)
environment    = "production"
instance_count = 3
tags = {
  Project = "MyApp"
  Team    = "Platform"
}
```

### Environment-Specific Files

```hcl
# dev.tfvars
environment    = "dev"
instance_type  = "t3.micro"
instance_count = 1

# prod.tfvars
environment    = "prod"
instance_type  = "t3.large"
instance_count = 3
```

```bash
# Apply with specific file
terraform apply -var-file="prod.tfvars"
```

### Command Line

```bash
# Single variable
terraform apply -var="environment=production"

# Multiple variables
terraform apply \
  -var="environment=production" \
  -var="instance_count=3"

# Complex values
terraform apply -var='tags={"Project":"MyApp","Team":"Platform"}'
```

### Environment Variables

```bash
# TF_VAR_ prefix
export TF_VAR_environment="production"
export TF_VAR_instance_count=3
export TF_VAR_db_password="secret123"

terraform apply
```

### Variable Precedence

```
1. Environment variables (TF_VAR_*)
2. terraform.tfvars
3. *.auto.tfvars (alphabetical order)
4. -var and -var-file (in order specified)
```

## Variable References

### Basic Reference

```hcl
resource "aws_instance" "web" {
  instance_type = var.instance_type
  ami           = var.ami_id
}
```

### In Expressions

```hcl
locals {
  name_prefix = "${var.project}-${var.environment}"
  full_name   = var.custom_name != null ? var.custom_name : local.name_prefix
}

resource "aws_instance" "web" {
  count = var.create_instances ? var.instance_count : 0

  tags = merge(var.tags, {
    Name = "${local.name_prefix}-${count.index}"
  })
}
```

### In Modules

```hcl
# Passing variables to modules
module "vpc" {
  source = "./modules/vpc"

  name        = var.vpc_name
  cidr_block  = var.vpc_cidr
  environment = var.environment
}
```

## Variable Files Organization

### Standard Structure

```
project/
├── main.tf
├── variables.tf         # Variable declarations
├── terraform.tfvars     # Default values
├── environments/
│   ├── dev.tfvars
│   ├── staging.tfvars
│   └── prod.tfvars
└── secrets.auto.tfvars  # Gitignored sensitive values
```

### Grouped Variables

```hcl
# variables.tf

# ==================
# General Variables
# ==================
variable "project" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

# ==================
# Network Variables
# ==================
variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
}

# ==================
# Compute Variables
# ==================
variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}
```

## Variable Documentation

### In-Code Documentation

```hcl
variable "instance_type" {
  description = <<-EOT
    EC2 instance type for the web servers.

    Recommended values:
    - dev: t3.micro
    - staging: t3.small
    - prod: t3.medium or larger

    See: https://aws.amazon.com/ec2/instance-types/
  EOT

  type    = string
  default = "t3.micro"
}
```

### Variables Table (README)

```markdown
## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| project | Project name | `string` | n/a | yes |
| environment | Environment name | `string` | n/a | yes |
| instance_type | EC2 instance type | `string` | `"t3.micro"` | no |
| tags | Tags to apply | `map(string)` | `{}` | no |
```

## Best Practices

1. **Required vs Optional**: Require only essential variables
2. **Sensible Defaults**: Provide defaults for optional variables
3. **Validation**: Add validation rules for complex variables
4. **Documentation**: Document all variables with descriptions
5. **Grouping**: Group related variables together
6. **Naming**: Use clear, consistent naming conventions
7. **Sensitive Data**: Mark passwords and keys as sensitive
8. **Type Constraints**: Always specify types for clarity
9. **Optional Attributes**: Use optional() for flexible objects
10. **Environment Separation**: Use separate tfvars per environment
