# Terraform Basics

## Overview

Terraform is an Infrastructure as Code (IaC) tool that enables declarative infrastructure provisioning across multiple cloud providers and services.

## Core Concepts

### Declarative Configuration

```hcl
# Describe WHAT you want, not HOW to create it
resource "aws_instance" "web" {
  ami           = "ami-0123456789abcdef0"
  instance_type = "t3.micro"

  tags = {
    Name = "web-server"
  }
}
```

### Resource Block Structure

```hcl
resource "<PROVIDER>_<TYPE>" "<NAME>" {
  # Configuration arguments
  argument1 = value1
  argument2 = value2

  # Nested block
  nested_block {
    nested_argument = value
  }
}
```

### Data Source Block

```hcl
# Read existing infrastructure
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }
}

# Reference in resources
resource "aws_instance" "web" {
  ami = data.aws_ami.amazon_linux.id
}
```

## Terraform Workflow

### 1. Write Configuration

```hcl
# main.tf
terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

resource "aws_s3_bucket" "example" {
  bucket = "my-unique-bucket-name"
}
```

### 2. Initialize

```bash
# Download providers and initialize backend
terraform init

# Upgrade providers
terraform init -upgrade

# Reconfigure backend
terraform init -reconfigure
```

### 3. Plan

```bash
# Preview changes
terraform plan

# Save plan to file
terraform plan -out=tfplan

# Target specific resources
terraform plan -target=aws_instance.web
```

### 4. Apply

```bash
# Apply changes with confirmation
terraform apply

# Apply saved plan
terraform apply tfplan

# Auto-approve (use carefully)
terraform apply -auto-approve
```

### 5. Destroy

```bash
# Destroy all infrastructure
terraform destroy

# Target specific resources
terraform destroy -target=aws_instance.web
```

## File Organization

### Standard Structure

```
project/
├── main.tf           # Primary resources
├── variables.tf      # Input variables
├── outputs.tf        # Output values
├── providers.tf      # Provider configuration
├── versions.tf       # Version constraints
├── locals.tf         # Local values
├── data.tf           # Data sources
└── terraform.tfvars  # Variable values
```

### Environment-Based Structure

```
project/
├── modules/
│   └── vpc/
├── environments/
│   ├── dev/
│   │   ├── main.tf
│   │   └── terraform.tfvars
│   ├── staging/
│   └── prod/
└── global/
    └── iam/
```

## Resource References

### Direct Reference

```hcl
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
}

resource "aws_subnet" "public" {
  vpc_id     = aws_vpc.main.id  # Reference VPC ID
  cidr_block = "10.0.1.0/24"
}
```

### Implicit Dependencies

```hcl
# Terraform automatically determines order
resource "aws_security_group" "web" {
  vpc_id = aws_vpc.main.id  # Depends on VPC
}

resource "aws_instance" "web" {
  vpc_security_group_ids = [aws_security_group.web.id]  # Depends on SG
}
```

### Explicit Dependencies

```hcl
resource "aws_instance" "web" {
  ami           = "ami-0123456789"
  instance_type = "t3.micro"

  # Explicit dependency
  depends_on = [aws_iam_role_policy.web]
}
```

## Count and For Each

### Count

```hcl
resource "aws_instance" "web" {
  count = 3

  ami           = "ami-0123456789"
  instance_type = "t3.micro"

  tags = {
    Name = "web-${count.index + 1}"
  }
}

# Reference: aws_instance.web[0], aws_instance.web[1], ...
```

### For Each with Set

```hcl
resource "aws_iam_user" "users" {
  for_each = toset(["alice", "bob", "charlie"])

  name = each.value
}

# Reference: aws_iam_user.users["alice"]
```

### For Each with Map

```hcl
variable "instances" {
  default = {
    web  = "t3.micro"
    api  = "t3.small"
    db   = "t3.medium"
  }
}

resource "aws_instance" "servers" {
  for_each = var.instances

  ami           = "ami-0123456789"
  instance_type = each.value

  tags = {
    Name = each.key
  }
}
```

## Conditional Expressions

```hcl
# Conditional resource creation
resource "aws_eip" "web" {
  count = var.create_eip ? 1 : 0

  instance = aws_instance.web.id
}

# Conditional values
locals {
  instance_type = var.environment == "prod" ? "t3.large" : "t3.micro"
}

# Null for optional values
resource "aws_instance" "web" {
  ami           = "ami-0123456789"
  instance_type = "t3.micro"
  key_name      = var.enable_ssh ? var.key_name : null
}
```

## Dynamic Blocks

```hcl
variable "ingress_rules" {
  default = [
    { port = 80, cidr = "0.0.0.0/0" },
    { port = 443, cidr = "0.0.0.0/0" },
  ]
}

resource "aws_security_group" "web" {
  name = "web-sg"

  dynamic "ingress" {
    for_each = var.ingress_rules

    content {
      from_port   = ingress.value.port
      to_port     = ingress.value.port
      protocol    = "tcp"
      cidr_blocks = [ingress.value.cidr]
    }
  }
}
```

## Common Commands

```bash
# Format code
terraform fmt
terraform fmt -recursive

# Validate configuration
terraform validate

# Show current state
terraform show

# List resources in state
terraform state list

# Import existing resource
terraform import aws_instance.web i-1234567890abcdef0

# Refresh state
terraform refresh

# Output values
terraform output
terraform output -json

# Console for testing
terraform console
```

## Best Practices

1. **Version Control**: Always use version control for Terraform code
2. **Remote State**: Use remote state for team collaboration
3. **State Locking**: Enable state locking to prevent conflicts
4. **Variables**: Parameterize configurations for reusability
5. **Modules**: Use modules for reusable infrastructure components
6. **Naming**: Follow consistent naming conventions
7. **Documentation**: Document complex configurations
8. **Testing**: Validate configurations before applying
