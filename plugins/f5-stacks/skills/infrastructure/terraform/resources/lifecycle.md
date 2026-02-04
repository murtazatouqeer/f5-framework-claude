# Resource Lifecycle

## Overview

Terraform lifecycle meta-arguments control how resources are created, updated, and destroyed. Understanding lifecycle management is essential for safe infrastructure changes.

## Lifecycle Block

```hcl
resource "aws_instance" "web" {
  ami           = "ami-0123456789"
  instance_type = "t3.micro"

  lifecycle {
    create_before_destroy = true
    prevent_destroy       = false
    ignore_changes        = [tags]
    replace_triggered_by  = [null_resource.trigger.id]

    # Terraform 1.2+ features
    precondition {
      condition     = var.environment != ""
      error_message = "Environment must be specified."
    }

    postcondition {
      condition     = self.public_ip != ""
      error_message = "Instance must have a public IP."
    }
  }
}
```

## create_before_destroy

### Purpose

Creates new resource before destroying the old one. Essential for zero-downtime updates.

### Usage

```hcl
resource "aws_instance" "web" {
  ami           = var.ami_id
  instance_type = "t3.micro"

  lifecycle {
    create_before_destroy = true
  }
}
```

### Common Use Cases

```hcl
# Security groups (to maintain connectivity)
resource "aws_security_group" "web" {
  name_prefix = "web-sg-"
  vpc_id      = aws_vpc.main.id

  lifecycle {
    create_before_destroy = true
  }
}

# Launch configurations
resource "aws_launch_configuration" "web" {
  name_prefix   = "web-lc-"
  image_id      = var.ami_id
  instance_type = "t3.micro"

  lifecycle {
    create_before_destroy = true
  }
}

# Auto Scaling Group reference
resource "aws_autoscaling_group" "web" {
  launch_configuration = aws_launch_configuration.web.name
  min_size             = 2
  max_size             = 10

  lifecycle {
    create_before_destroy = true
  }
}
```

### Dependency Propagation

```hcl
# If resource A has create_before_destroy, dependent resources
# should also have it to avoid issues
resource "aws_security_group" "web" {
  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_instance" "web" {
  vpc_security_group_ids = [aws_security_group.web.id]

  lifecycle {
    create_before_destroy = true
  }
}
```

## prevent_destroy

### Purpose

Prevents accidental destruction of critical resources.

### Usage

```hcl
# Protect production database
resource "aws_db_instance" "production" {
  identifier = "production-db"
  engine     = "postgres"

  lifecycle {
    prevent_destroy = true
  }
}

# Protect S3 bucket with important data
resource "aws_s3_bucket" "data" {
  bucket = "critical-data-bucket"

  lifecycle {
    prevent_destroy = true
  }
}
```

### Behavior

```bash
# Attempting to destroy will fail
terraform destroy

# Error: Instance cannot be destroyed
# Resource aws_db_instance.production has lifecycle.prevent_destroy set

# To override, you must first remove prevent_destroy
```

### Environment-Based Protection

```hcl
variable "environment" {
  type = string
}

resource "aws_db_instance" "main" {
  identifier = "${var.environment}-db"

  lifecycle {
    # Only prevent destroy in production
    prevent_destroy = var.environment == "production"
  }
}
```

## ignore_changes

### Purpose

Ignores specific attribute changes during updates.

### Common Patterns

```hcl
# Ignore tags managed externally
resource "aws_instance" "web" {
  ami           = "ami-0123456789"
  instance_type = "t3.micro"

  lifecycle {
    ignore_changes = [tags]
  }
}

# Ignore AMI updates (managed separately)
resource "aws_instance" "web" {
  ami           = "ami-0123456789"
  instance_type = "t3.micro"

  lifecycle {
    ignore_changes = [ami]
  }
}

# Ignore multiple attributes
resource "aws_instance" "web" {
  lifecycle {
    ignore_changes = [
      ami,
      user_data,
      tags,
    ]
  }
}

# Ignore all attributes (only track existence)
resource "aws_instance" "web" {
  lifecycle {
    ignore_changes = all
  }
}
```

### Use Cases

```hcl
# Auto Scaling Group capacity (managed by scaling policies)
resource "aws_autoscaling_group" "web" {
  desired_capacity = 2
  min_size         = 1
  max_size         = 10

  lifecycle {
    ignore_changes = [desired_capacity]
  }
}

# ECS service task count (managed by auto-scaling)
resource "aws_ecs_service" "main" {
  name            = "main-service"
  desired_count   = 2

  lifecycle {
    ignore_changes = [desired_count]
  }
}

# Lambda function code (deployed separately)
resource "aws_lambda_function" "main" {
  filename         = "lambda.zip"
  source_code_hash = filebase64sha256("lambda.zip")

  lifecycle {
    ignore_changes = [
      filename,
      source_code_hash,
    ]
  }
}

# RDS password (rotated externally)
resource "aws_db_instance" "main" {
  password = var.initial_password

  lifecycle {
    ignore_changes = [password]
  }
}
```

### Nested Attributes

```hcl
# Ignore specific nested block
resource "aws_instance" "web" {
  lifecycle {
    ignore_changes = [
      root_block_device[0].volume_size,
      ebs_block_device,
    ]
  }
}

# Ignore map key
resource "aws_instance" "web" {
  tags = {
    Name       = "web"
    LastUpdate = timestamp()
  }

  lifecycle {
    ignore_changes = [
      tags["LastUpdate"],
    ]
  }
}
```

## replace_triggered_by

### Purpose

Force replacement when related resources change (Terraform 1.2+).

### Usage

```hcl
resource "null_resource" "trigger" {
  triggers = {
    config_hash = sha256(file("config.json"))
  }
}

resource "aws_instance" "web" {
  ami           = "ami-0123456789"
  instance_type = "t3.micro"

  lifecycle {
    replace_triggered_by = [null_resource.trigger.id]
  }
}
```

### Multiple Triggers

```hcl
resource "aws_instance" "web" {
  lifecycle {
    replace_triggered_by = [
      null_resource.config_change.id,
      aws_security_group.web.id,
    ]
  }
}
```

### With Resource References

```hcl
resource "aws_security_group" "web" {
  name = "web-sg"
}

resource "aws_instance" "web" {
  vpc_security_group_ids = [aws_security_group.web.id]

  lifecycle {
    # Replace instance when security group is replaced
    replace_triggered_by = [aws_security_group.web]
  }
}
```

## Preconditions and Postconditions

### Preconditions (Terraform 1.2+)

```hcl
variable "instance_type" {
  type = string
}

resource "aws_instance" "web" {
  ami           = var.ami_id
  instance_type = var.instance_type

  lifecycle {
    precondition {
      condition     = contains(["t3.micro", "t3.small", "t3.medium"], var.instance_type)
      error_message = "Instance type must be t3.micro, t3.small, or t3.medium."
    }
  }
}
```

### Postconditions

```hcl
resource "aws_instance" "web" {
  ami           = "ami-0123456789"
  instance_type = "t3.micro"

  lifecycle {
    postcondition {
      condition     = self.public_ip != ""
      error_message = "Instance must have a public IP address."
    }

    postcondition {
      condition     = self.root_block_device[0].volume_size >= 20
      error_message = "Root volume must be at least 20 GB."
    }
  }
}
```

### Data Source Preconditions

```hcl
data "aws_ami" "app" {
  most_recent = true
  owners      = ["self"]

  filter {
    name   = "name"
    values = ["app-*"]
  }

  lifecycle {
    postcondition {
      condition     = self.image_id != null
      error_message = "No AMI found matching the criteria."
    }
  }
}
```

## Taint and Replace

### Marking for Replacement

```bash
# Modern approach (Terraform 0.15.2+)
terraform apply -replace="aws_instance.web"

# Legacy approach (deprecated)
terraform taint aws_instance.web
terraform untaint aws_instance.web
```

### Targeted Replacement

```bash
# Plan with replacement
terraform plan -replace="aws_instance.web"

# Apply with replacement
terraform apply -replace="aws_instance.web"

# Multiple resources
terraform apply \
  -replace="aws_instance.web" \
  -replace="aws_instance.api"
```

## Resource Drift

### Detecting Drift

```bash
# Refresh state and show drift
terraform plan -refresh-only

# Apply refresh only
terraform apply -refresh-only
```

### Handling Drift

```hcl
# Option 1: Ignore drifted attributes
resource "aws_instance" "web" {
  lifecycle {
    ignore_changes = [tags]
  }
}

# Option 2: Force replacement
# terraform apply -replace="aws_instance.web"

# Option 3: Import current state
# Update configuration then refresh
```

## Import and Lifecycle

### Importing with Lifecycle

```hcl
# Define resource with lifecycle before import
resource "aws_instance" "existing" {
  lifecycle {
    ignore_changes = [ami]
  }
}

# Import
# terraform import aws_instance.existing i-1234567890abcdef0
```

### Import Block (Terraform 1.5+)

```hcl
import {
  to = aws_instance.web
  id = "i-1234567890abcdef0"
}

resource "aws_instance" "web" {
  # Configuration generated or written manually

  lifecycle {
    ignore_changes = [ami, user_data]
  }
}
```

## Moved Block

### Renaming Resources (Terraform 1.1+)

```hcl
# Old resource name
# resource "aws_instance" "web" { ... }

# New resource name
resource "aws_instance" "web_server" {
  # Same configuration
}

moved {
  from = aws_instance.web
  to   = aws_instance.web_server
}
```

### Moving to Module

```hcl
# Move resource into module
moved {
  from = aws_instance.web
  to   = module.compute.aws_instance.main
}
```

### Moving Between Modules

```hcl
moved {
  from = module.old_vpc.aws_vpc.main
  to   = module.new_vpc.aws_vpc.main
}
```

## Removed Block (Terraform 1.7+)

```hcl
# Remove resource from Terraform without destroying
removed {
  from = aws_instance.old

  lifecycle {
    destroy = false
  }
}
```

## Best Practices

1. **Use create_before_destroy**: For resources requiring zero-downtime updates
2. **Protect Critical Resources**: Use prevent_destroy for production databases and storage
3. **Ignore External Changes**: Use ignore_changes for attributes managed outside Terraform
4. **Validate Inputs**: Use preconditions to catch configuration errors early
5. **Verify Outputs**: Use postconditions to ensure resources are created correctly
6. **Plan Replacements**: Use -replace flag instead of taint
7. **Track Moves**: Use moved blocks to refactor without recreation
8. **Document Lifecycle Choices**: Comment why specific lifecycle rules are used
