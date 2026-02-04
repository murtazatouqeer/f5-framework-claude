# Variable Validation

## Overview

Variable validation rules allow you to define constraints on variable values, catching configuration errors early before Terraform attempts to create resources.

## Basic Validation Syntax

```hcl
variable "name" {
  type = string

  validation {
    condition     = length(var.name) > 0
    error_message = "Name must not be empty."
  }
}
```

## String Validation

### Length Constraints

```hcl
variable "name" {
  type = string

  validation {
    condition     = length(var.name) >= 3 && length(var.name) <= 63
    error_message = "Name must be between 3 and 63 characters."
  }
}

variable "description" {
  type = string

  validation {
    condition     = length(var.description) <= 256
    error_message = "Description must not exceed 256 characters."
  }
}
```

### Pattern Matching

```hcl
# Simple regex
variable "environment" {
  type = string

  validation {
    condition     = can(regex("^(dev|staging|prod)$", var.environment))
    error_message = "Environment must be dev, staging, or prod."
  }
}

# DNS-compatible name
variable "bucket_name" {
  type = string

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$", var.bucket_name))
    error_message = "Bucket name must be DNS-compatible (lowercase, numbers, hyphens)."
  }
}

# AWS resource name pattern
variable "resource_name" {
  type = string

  validation {
    condition     = can(regex("^[a-zA-Z][a-zA-Z0-9-_]*$", var.resource_name))
    error_message = "Name must start with a letter and contain only alphanumeric characters, hyphens, and underscores."
  }
}
```

### Allowed Values

```hcl
variable "instance_type" {
  type = string

  validation {
    condition     = contains(["t3.micro", "t3.small", "t3.medium", "t3.large"], var.instance_type)
    error_message = "Instance type must be t3.micro, t3.small, t3.medium, or t3.large."
  }
}

variable "region" {
  type = string

  validation {
    condition = contains([
      "us-east-1", "us-east-2", "us-west-1", "us-west-2",
      "eu-west-1", "eu-central-1", "ap-northeast-1"
    ], var.region)
    error_message = "Region must be one of the approved AWS regions."
  }
}
```

## Number Validation

### Range Constraints

```hcl
variable "instance_count" {
  type = number

  validation {
    condition     = var.instance_count >= 1 && var.instance_count <= 10
    error_message = "Instance count must be between 1 and 10."
  }
}

variable "port" {
  type = number

  validation {
    condition     = var.port >= 1 && var.port <= 65535
    error_message = "Port must be a valid port number (1-65535)."
  }
}

variable "retention_days" {
  type = number

  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653], var.retention_days)
    error_message = "Retention days must be a valid CloudWatch log retention period."
  }
}
```

### Percentage Values

```hcl
variable "cpu_threshold" {
  type = number

  validation {
    condition     = var.cpu_threshold >= 0 && var.cpu_threshold <= 100
    error_message = "CPU threshold must be between 0 and 100 percent."
  }
}
```

### Divisibility

```hcl
variable "volume_size" {
  type = number

  validation {
    condition     = var.volume_size % 10 == 0
    error_message = "Volume size must be a multiple of 10 GB."
  }
}
```

## Network Validation

### CIDR Blocks

```hcl
variable "vpc_cidr" {
  type = string

  validation {
    condition     = can(cidrnetmask(var.vpc_cidr))
    error_message = "VPC CIDR must be a valid CIDR block."
  }
}

variable "vpc_cidr_detailed" {
  type = string

  validation {
    condition     = can(cidrnetmask(var.vpc_cidr_detailed))
    error_message = "Must be a valid CIDR block."
  }

  validation {
    condition     = tonumber(split("/", var.vpc_cidr_detailed)[1]) >= 16 && tonumber(split("/", var.vpc_cidr_detailed)[1]) <= 24
    error_message = "CIDR prefix must be between /16 and /24."
  }
}
```

### IP Addresses

```hcl
variable "ip_address" {
  type = string

  validation {
    condition     = can(regex("^\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}$", var.ip_address))
    error_message = "Must be a valid IPv4 address."
  }
}
```

### Domain Names

```hcl
variable "domain_name" {
  type = string

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-\\.]{1,253}[a-z0-9]$", var.domain_name))
    error_message = "Must be a valid domain name."
  }
}

variable "hosted_zone" {
  type = string

  validation {
    condition     = endswith(var.hosted_zone, ".")
    error_message = "Hosted zone name must end with a period."
  }
}
```

## Collection Validation

### List Validation

```hcl
variable "availability_zones" {
  type = list(string)

  validation {
    condition     = length(var.availability_zones) >= 2
    error_message = "At least 2 availability zones must be specified."
  }

  validation {
    condition     = alltrue([for az in var.availability_zones : can(regex("^[a-z]{2}-[a-z]+-[0-9][a-z]$", az))])
    error_message = "All availability zones must be in valid format (e.g., us-east-1a)."
  }
}

variable "subnet_ids" {
  type = list(string)

  validation {
    condition     = alltrue([for id in var.subnet_ids : can(regex("^subnet-[a-f0-9]{8,17}$", id))])
    error_message = "All subnet IDs must be valid AWS subnet IDs."
  }
}
```

### Map Validation

```hcl
variable "tags" {
  type = map(string)

  validation {
    condition     = length(var.tags) <= 50
    error_message = "Maximum of 50 tags allowed."
  }

  validation {
    condition     = alltrue([for k, v in var.tags : length(k) <= 128 && length(v) <= 256])
    error_message = "Tag keys must be <= 128 chars, values <= 256 chars."
  }
}

variable "environment_config" {
  type = map(string)

  validation {
    condition     = contains(keys(var.environment_config), "name")
    error_message = "Environment config must include 'name' key."
  }
}
```

### Set Validation

```hcl
variable "allowed_protocols" {
  type = set(string)

  validation {
    condition     = length(setsubtract(var.allowed_protocols, ["tcp", "udp", "icmp"])) == 0
    error_message = "Protocols must be tcp, udp, or icmp."
  }
}
```

## Object Validation

### Required Fields

```hcl
variable "database_config" {
  type = object({
    engine         = string
    version        = string
    instance_class = string
    storage_gb     = number
  })

  validation {
    condition     = contains(["mysql", "postgres", "mariadb"], var.database_config.engine)
    error_message = "Database engine must be mysql, postgres, or mariadb."
  }

  validation {
    condition     = var.database_config.storage_gb >= 20 && var.database_config.storage_gb <= 65536
    error_message = "Storage must be between 20 GB and 65536 GB."
  }
}
```

### Nested Object Validation

```hcl
variable "instance_config" {
  type = object({
    name          = string
    instance_type = string
    storage = object({
      size      = number
      type      = string
      encrypted = bool
    })
  })

  validation {
    condition     = var.instance_config.storage.size >= 8
    error_message = "Storage size must be at least 8 GB."
  }

  validation {
    condition     = contains(["gp2", "gp3", "io1", "io2"], var.instance_config.storage.type)
    error_message = "Storage type must be gp2, gp3, io1, or io2."
  }
}
```

## Multiple Validation Rules

```hcl
variable "cluster_name" {
  type = string

  # Length validation
  validation {
    condition     = length(var.cluster_name) >= 1 && length(var.cluster_name) <= 100
    error_message = "Cluster name must be between 1 and 100 characters."
  }

  # Character validation
  validation {
    condition     = can(regex("^[a-zA-Z][a-zA-Z0-9-]*$", var.cluster_name))
    error_message = "Cluster name must start with a letter and contain only alphanumeric characters and hyphens."
  }

  # Reserved names
  validation {
    condition     = !contains(["default", "system", "admin"], lower(var.cluster_name))
    error_message = "Cluster name cannot be a reserved name (default, system, admin)."
  }
}
```

## Conditional Validation

### Using try()

```hcl
variable "json_config" {
  type = string

  validation {
    condition     = can(jsondecode(var.json_config))
    error_message = "Config must be valid JSON."
  }
}
```

### Cross-Variable Validation (Module Level)

```hcl
# In locals or resource preconditions
variable "min_instances" {
  type = number
}

variable "max_instances" {
  type = number
}

resource "aws_autoscaling_group" "main" {
  min_size = var.min_instances
  max_size = var.max_instances

  lifecycle {
    precondition {
      condition     = var.min_instances <= var.max_instances
      error_message = "min_instances must be <= max_instances."
    }
  }
}
```

## AWS-Specific Validation

### ARN Validation

```hcl
variable "kms_key_arn" {
  type = string

  validation {
    condition     = can(regex("^arn:aws:kms:[a-z0-9-]+:[0-9]{12}:key/[a-f0-9-]+$", var.kms_key_arn))
    error_message = "Must be a valid KMS key ARN."
  }
}

variable "s3_bucket_arn" {
  type = string

  validation {
    condition     = can(regex("^arn:aws:s3:::[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$", var.s3_bucket_arn))
    error_message = "Must be a valid S3 bucket ARN."
  }
}
```

### Resource ID Validation

```hcl
variable "vpc_id" {
  type = string

  validation {
    condition     = can(regex("^vpc-[a-f0-9]{8,17}$", var.vpc_id))
    error_message = "Must be a valid VPC ID."
  }
}

variable "ami_id" {
  type = string

  validation {
    condition     = can(regex("^ami-[a-f0-9]{8,17}$", var.ami_id))
    error_message = "Must be a valid AMI ID."
  }
}
```

## Validation Functions Reference

| Function | Usage |
|----------|-------|
| `can()` | Test if expression is valid |
| `regex()` | Pattern matching |
| `contains()` | Check list membership |
| `length()` | String/collection length |
| `alltrue()` | All elements true |
| `anytrue()` | Any element true |
| `startswith()` | String prefix check |
| `endswith()` | String suffix check |
| `tonumber()` | Convert to number |
| `cidrnetmask()` | Validate CIDR |

## Best Practices

1. **Meaningful Messages**: Write clear, actionable error messages
2. **Multiple Rules**: Use separate validations for different concerns
3. **Early Validation**: Catch errors before resource creation
4. **Type First**: Use type constraints before validation rules
5. **Common Patterns**: Create reusable validation patterns
6. **Documentation**: Document validation requirements
7. **Testing**: Test validation rules with invalid inputs
8. **AWS Patterns**: Use AWS-specific regex patterns for IDs
9. **Avoid Complexity**: Keep validation rules readable
10. **Preconditions**: Use lifecycle preconditions for cross-variable validation
