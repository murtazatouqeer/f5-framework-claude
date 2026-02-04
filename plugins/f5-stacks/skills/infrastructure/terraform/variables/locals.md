# Local Values

## Overview

Local values (locals) are named expressions that can be referenced throughout a module. They help reduce repetition, improve readability, and centralize complex expressions.

## Basic Syntax

```hcl
locals {
  name_prefix = "${var.project}-${var.environment}"
}

resource "aws_instance" "web" {
  tags = {
    Name = "${local.name_prefix}-web"
  }
}
```

## Common Use Cases

### Naming Conventions

```hcl
locals {
  # Standard name prefix
  name_prefix = "${var.project}-${var.environment}"

  # Resource-specific names
  vpc_name = "${local.name_prefix}-vpc"
  eks_name = "${local.name_prefix}-eks"
  rds_name = "${local.name_prefix}-db"
}

resource "aws_vpc" "main" {
  tags = { Name = local.vpc_name }
}

resource "aws_eks_cluster" "main" {
  name = local.eks_name
}
```

### Common Tags

```hcl
locals {
  common_tags = {
    Project     = var.project
    Environment = var.environment
    ManagedBy   = "terraform"
    Owner       = var.owner
    CostCenter  = var.cost_center
  }
}

resource "aws_vpc" "main" {
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-vpc"
  })
}

resource "aws_instance" "web" {
  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-web"
    Role = "webserver"
  })
}
```

### Computed Values

```hcl
locals {
  # Subnet calculations
  subnet_count     = length(var.availability_zones)
  private_subnets  = [for i in range(local.subnet_count) : cidrsubnet(var.vpc_cidr, 4, i)]
  public_subnets   = [for i in range(local.subnet_count) : cidrsubnet(var.vpc_cidr, 4, i + local.subnet_count)]
  database_subnets = [for i in range(local.subnet_count) : cidrsubnet(var.vpc_cidr, 4, i + local.subnet_count * 2)]
}

resource "aws_subnet" "private" {
  count      = local.subnet_count
  cidr_block = local.private_subnets[count.index]
}
```

### Conditional Logic

```hcl
locals {
  # Environment-based settings
  is_production = var.environment == "prod"

  instance_type = local.is_production ? "t3.large" : "t3.micro"
  instance_count = local.is_production ? 3 : 1

  # Multi-AZ only in production
  multi_az = local.is_production

  # Logging configuration
  log_retention_days = {
    dev     = 7
    staging = 14
    prod    = 90
  }[var.environment]
}
```

### Data Transformation

```hcl
variable "users" {
  type = list(object({
    name  = string
    email = string
    role  = string
  }))
}

locals {
  # Transform list to map keyed by name
  users_by_name = { for user in var.users : user.name => user }

  # Filter users by role
  admin_users = [for user in var.users : user if user.role == "admin"]

  # Extract specific field
  user_emails = [for user in var.users : user.email]

  # Create formatted strings
  user_arns = [for user in var.users : "arn:aws:iam::${data.aws_caller_identity.current.account_id}:user/${user.name}"]
}
```

### Merging Configuration

```hcl
variable "custom_settings" {
  type    = map(any)
  default = {}
}

locals {
  default_settings = {
    instance_type     = "t3.micro"
    volume_size       = 20
    monitoring        = true
    detailed_metrics  = false
  }

  # Merge custom settings with defaults
  settings = merge(local.default_settings, var.custom_settings)
}

resource "aws_instance" "web" {
  instance_type = local.settings.instance_type
  monitoring    = local.settings.monitoring

  root_block_device {
    volume_size = local.settings.volume_size
  }
}
```

### AWS Account Information

```hcl
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}
data "aws_partition" "current" {}

locals {
  account_id = data.aws_caller_identity.current.account_id
  region     = data.aws_region.current.name
  partition  = data.aws_partition.current.partition

  # Construct ARNs
  s3_bucket_arn = "arn:${local.partition}:s3:::${var.bucket_name}"
  lambda_arn    = "arn:${local.partition}:lambda:${local.region}:${local.account_id}:function:${var.function_name}"
}
```

## Complex Examples

### Network Configuration

```hcl
locals {
  # VPC configuration
  vpc_cidr = "10.0.0.0/16"
  azs      = ["us-east-1a", "us-east-1b", "us-east-1c"]
  az_count = length(local.azs)

  # Subnet CIDR calculations
  subnet_bits = 8  # /24 subnets

  public_subnets = [
    for idx in range(local.az_count) : {
      az         = local.azs[idx]
      cidr_block = cidrsubnet(local.vpc_cidr, local.subnet_bits, idx)
      name       = "${local.name_prefix}-public-${local.azs[idx]}"
    }
  ]

  private_subnets = [
    for idx in range(local.az_count) : {
      az         = local.azs[idx]
      cidr_block = cidrsubnet(local.vpc_cidr, local.subnet_bits, idx + 10)
      name       = "${local.name_prefix}-private-${local.azs[idx]}"
    }
  ]

  database_subnets = [
    for idx in range(local.az_count) : {
      az         = local.azs[idx]
      cidr_block = cidrsubnet(local.vpc_cidr, local.subnet_bits, idx + 20)
      name       = "${local.name_prefix}-database-${local.azs[idx]}"
    }
  ]
}

resource "aws_subnet" "public" {
  for_each = { for subnet in local.public_subnets : subnet.az => subnet }

  vpc_id            = aws_vpc.main.id
  cidr_block        = each.value.cidr_block
  availability_zone = each.value.az

  tags = {
    Name = each.value.name
  }
}
```

### Security Group Rules

```hcl
locals {
  # Define ingress rules
  web_ingress_rules = [
    {
      port        = 80
      protocol    = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
      description = "HTTP from anywhere"
    },
    {
      port        = 443
      protocol    = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
      description = "HTTPS from anywhere"
    }
  ]

  ssh_ingress_rules = var.allow_ssh ? [
    {
      port        = 22
      protocol    = "tcp"
      cidr_blocks = var.ssh_allowed_cidrs
      description = "SSH from allowed CIDRs"
    }
  ] : []

  # Combine rules
  all_ingress_rules = concat(local.web_ingress_rules, local.ssh_ingress_rules)
}

resource "aws_security_group" "web" {
  name   = "${local.name_prefix}-web-sg"
  vpc_id = aws_vpc.main.id

  dynamic "ingress" {
    for_each = local.all_ingress_rules

    content {
      from_port   = ingress.value.port
      to_port     = ingress.value.port
      protocol    = ingress.value.protocol
      cidr_blocks = ingress.value.cidr_blocks
      description = ingress.value.description
    }
  }
}
```

### IAM Policy Document

```hcl
locals {
  # Define S3 permissions
  s3_permissions = {
    read = [
      "s3:GetObject",
      "s3:GetObjectVersion",
      "s3:ListBucket"
    ]
    write = [
      "s3:PutObject",
      "s3:DeleteObject"
    ]
    admin = [
      "s3:*"
    ]
  }

  # Determine permissions based on role
  s3_actions = local.s3_permissions[var.s3_access_level]

  # Build policy document
  policy_statements = [
    {
      effect    = "Allow"
      actions   = local.s3_actions
      resources = [
        aws_s3_bucket.main.arn,
        "${aws_s3_bucket.main.arn}/*"
      ]
    }
  ]
}
```

### Multi-Environment Configuration

```hcl
locals {
  # Environment-specific configurations
  env_config = {
    dev = {
      instance_type    = "t3.micro"
      instance_count   = 1
      db_instance_class = "db.t3.micro"
      multi_az         = false
      backup_retention = 1
    }
    staging = {
      instance_type    = "t3.small"
      instance_count   = 2
      db_instance_class = "db.t3.small"
      multi_az         = false
      backup_retention = 7
    }
    prod = {
      instance_type    = "t3.large"
      instance_count   = 3
      db_instance_class = "db.r6g.large"
      multi_az         = true
      backup_retention = 30
    }
  }

  # Current environment config
  config = local.env_config[var.environment]
}

resource "aws_instance" "web" {
  count         = local.config.instance_count
  instance_type = local.config.instance_type
}

resource "aws_db_instance" "main" {
  instance_class      = local.config.db_instance_class
  multi_az            = local.config.multi_az
  backup_retention_period = local.config.backup_retention
}
```

## Multiple Locals Blocks

```hcl
# Organize related locals into separate blocks

# Naming locals
locals {
  name_prefix = "${var.project}-${var.environment}"
}

# Network locals
locals {
  vpc_cidr = "10.0.0.0/16"
  azs      = data.aws_availability_zones.available.names
}

# Tags locals
locals {
  common_tags = {
    Project     = var.project
    Environment = var.environment
  }
}

# Computed locals
locals {
  subnet_count = length(local.azs)
}
```

## Local Expressions

### String Functions

```hcl
locals {
  # String manipulation
  lower_name = lower(var.name)
  upper_name = upper(var.name)
  title_name = title(var.name)

  # Replace
  cleaned_name = replace(var.name, " ", "-")

  # Format
  formatted = format("%s-%s-%03d", var.project, var.environment, var.instance_number)

  # Join
  subnet_list = join(",", var.subnet_ids)
}
```

### Collection Functions

```hcl
locals {
  # Length
  az_count = length(var.availability_zones)

  # Merge maps
  all_tags = merge(var.default_tags, var.custom_tags)

  # Flatten
  all_subnets = flatten([var.public_subnets, var.private_subnets])

  # Distinct
  unique_azs = distinct(var.availability_zones)

  # Sort
  sorted_subnets = sort(var.subnet_ids)

  # Lookup
  instance_type = lookup(var.instance_types, var.environment, "t3.micro")
}
```

### Type Conversion

```hcl
locals {
  # Convert types
  count_string = tostring(var.count)
  count_number = tonumber(var.count_string)

  # Convert to set (unique values)
  unique_values = toset(var.values)

  # Convert to map
  list_to_map = { for item in var.items : item.name => item }
}
```

## Best Practices

1. **DRY Principle**: Use locals to avoid repetition
2. **Meaningful Names**: Use descriptive local names
3. **Organization**: Group related locals together
4. **Complexity**: Move complex expressions to locals
5. **Documentation**: Comment complex local expressions
6. **Avoid Over-Use**: Don't create locals for simple values
7. **Immutability**: Locals are computed once per run
8. **Dependencies**: Be aware of local dependencies
9. **Readability**: Balance abstraction with readability
10. **Testing**: Test complex local expressions
