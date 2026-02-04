# Module Basics

## Overview

Terraform modules are containers for multiple resources that are used together. Modules enable code reuse, organization, and encapsulation of infrastructure components.

## Module Structure

### Standard Layout

```
modules/vpc/
├── main.tf           # Primary resources
├── variables.tf      # Input variables
├── outputs.tf        # Output values
├── versions.tf       # Provider requirements
├── locals.tf         # Local values
├── data.tf           # Data sources
└── README.md         # Documentation
```

### Minimal Module

```hcl
# modules/s3-bucket/main.tf
resource "aws_s3_bucket" "this" {
  bucket = var.bucket_name

  tags = var.tags
}

resource "aws_s3_bucket_versioning" "this" {
  bucket = aws_s3_bucket.this.id

  versioning_configuration {
    status = var.versioning_enabled ? "Enabled" : "Suspended"
  }
}

# modules/s3-bucket/variables.tf
variable "bucket_name" {
  description = "Name of the S3 bucket"
  type        = string
}

variable "versioning_enabled" {
  description = "Enable versioning"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Tags to apply"
  type        = map(string)
  default     = {}
}

# modules/s3-bucket/outputs.tf
output "bucket_id" {
  description = "The bucket ID"
  value       = aws_s3_bucket.this.id
}

output "bucket_arn" {
  description = "The bucket ARN"
  value       = aws_s3_bucket.this.arn
}
```

## Calling Modules

### Local Module

```hcl
module "bucket" {
  source = "./modules/s3-bucket"

  bucket_name        = "my-app-data"
  versioning_enabled = true

  tags = {
    Environment = "production"
  }
}

# Access outputs
output "bucket_arn" {
  value = module.bucket.bucket_arn
}
```

### Remote Module (GitHub)

```hcl
module "vpc" {
  source = "github.com/company/terraform-modules//vpc?ref=v1.0.0"

  cidr_block = "10.0.0.0/16"
}
```

### Terraform Registry Module

```hcl
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "my-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["us-east-1a", "us-east-1b", "us-east-1c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  enable_nat_gateway = true
  single_nat_gateway = true
}
```

## Module Arguments

### Required Arguments

```hcl
module "ec2" {
  source = "./modules/ec2"

  # Required - must be provided
  instance_name = "web-server"
  ami_id        = "ami-0123456789"
  subnet_id     = aws_subnet.public.id
}
```

### Optional Arguments

```hcl
module "ec2" {
  source = "./modules/ec2"

  instance_name = "web-server"
  ami_id        = "ami-0123456789"
  subnet_id     = aws_subnet.public.id

  # Optional - have defaults in module
  instance_type = "t3.small"  # default: t3.micro
  monitoring    = true        # default: false
}
```

### Meta-Arguments

```hcl
# count
module "bucket" {
  source = "./modules/s3-bucket"
  count  = 3

  bucket_name = "bucket-${count.index}"
}

# for_each
module "bucket" {
  source   = "./modules/s3-bucket"
  for_each = toset(["data", "logs", "backup"])

  bucket_name = "app-${each.key}"
}

# providers
module "vpc" {
  source = "./modules/vpc"

  providers = {
    aws = aws.west
  }
}

# depends_on
module "app" {
  source = "./modules/app"

  depends_on = [module.vpc]
}
```

## Input Variables

### Type Constraints

```hcl
# variables.tf
variable "name" {
  description = "Resource name"
  type        = string
}

variable "count" {
  description = "Number of instances"
  type        = number
  default     = 1
}

variable "enabled" {
  description = "Enable feature"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default     = {}
}

variable "subnets" {
  description = "Subnet IDs"
  type        = list(string)
}

variable "config" {
  description = "Configuration object"
  type = object({
    instance_type = string
    volume_size   = number
    encrypted     = optional(bool, true)
  })
}
```

### Validation

```hcl
variable "environment" {
  type = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "cidr_block" {
  type = string

  validation {
    condition     = can(cidrnetmask(var.cidr_block))
    error_message = "Must be a valid CIDR block."
  }
}

variable "instance_type" {
  type = string

  validation {
    condition     = can(regex("^t3\\.", var.instance_type))
    error_message = "Instance type must be t3 family."
  }
}
```

### Sensitive Variables

```hcl
variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}
```

## Output Values

### Basic Outputs

```hcl
# outputs.tf
output "vpc_id" {
  description = "The VPC ID"
  value       = aws_vpc.main.id
}

output "subnet_ids" {
  description = "List of subnet IDs"
  value       = aws_subnet.main[*].id
}
```

### Sensitive Outputs

```hcl
output "db_password" {
  description = "Database password"
  value       = random_password.db.result
  sensitive   = true
}
```

### Conditional Outputs

```hcl
output "public_ip" {
  description = "Public IP if assigned"
  value       = var.assign_public_ip ? aws_instance.main.public_ip : null
}
```

### Complex Outputs

```hcl
output "instance_info" {
  description = "Instance information"
  value = {
    id         = aws_instance.main.id
    public_ip  = aws_instance.main.public_ip
    private_ip = aws_instance.main.private_ip
    arn        = aws_instance.main.arn
  }
}
```

## Local Values

```hcl
# locals.tf
locals {
  name_prefix = "${var.project}-${var.environment}"

  common_tags = {
    Project     = var.project
    Environment = var.environment
    ManagedBy   = "terraform"
  }

  # Computed values
  subnet_count = length(var.availability_zones)

  # Conditional logic
  instance_type = var.environment == "prod" ? "t3.large" : "t3.micro"
}

# Usage in resources
resource "aws_instance" "main" {
  instance_type = local.instance_type

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-instance"
  })
}
```

## Provider Configuration

### versions.tf

```hcl
terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }

    random = {
      source  = "hashicorp/random"
      version = ">= 3.0"
    }
  }
}
```

### Provider Aliasing

```hcl
# Module that accepts provider configuration
terraform {
  required_providers {
    aws = {
      source                = "hashicorp/aws"
      version               = ">= 5.0"
      configuration_aliases = [aws.alternate]
    }
  }
}

# Use default provider
resource "aws_instance" "main" {
  # Uses default aws provider
}

# Use aliased provider
resource "aws_instance" "alternate" {
  provider = aws.alternate
}
```

## Module Documentation

### README.md Template

```markdown
# Module Name

Brief description of what this module creates.

## Usage

\`\`\`hcl
module "example" {
  source = "./modules/example"

  name        = "my-resource"
  environment = "production"
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
| name | Resource name | `string` | n/a | yes |
| environment | Environment name | `string` | `"dev"` | no |

## Outputs

| Name | Description |
|------|-------------|
| id | The resource ID |
| arn | The resource ARN |

## Resources

| Name | Type |
|------|------|
| aws_instance.main | resource |
| aws_security_group.main | resource |

## License

MIT
```

## Best Practices

1. **Single Responsibility**: Each module should do one thing well
2. **Clear Interface**: Define clear inputs and outputs
3. **Documentation**: Include README with usage examples
4. **Versioning**: Use semantic versioning for modules
5. **Validation**: Add input validation rules
6. **Defaults**: Provide sensible defaults for optional variables
7. **Naming**: Use consistent naming conventions
8. **Testing**: Write tests for modules
9. **Composition**: Design modules to be composed together
10. **Encapsulation**: Hide implementation details
