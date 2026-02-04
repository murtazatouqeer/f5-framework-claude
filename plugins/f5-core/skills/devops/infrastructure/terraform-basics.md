---
name: terraform-basics
description: Terraform fundamentals and advanced patterns
category: devops/infrastructure
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Terraform Basics

## Overview

Terraform is an infrastructure as code tool that enables you to safely and
predictably provision and manage infrastructure across multiple cloud providers.

## Core Concepts

```
┌─────────────────────────────────────────────────────────────────┐
│                    Terraform Workflow                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│    Write          Plan            Apply          Destroy        │
│  ┌────────┐    ┌────────┐    ┌────────┐     ┌────────┐        │
│  │  .tf   │ → │ Review │ → │ Create │  →  │ Remove │        │
│  │ files  │    │ changes│    │ infra  │     │ infra  │        │
│  └────────┘    └────────┘    └────────┘     └────────┘        │
│                                                                  │
│  terraform      terraform     terraform     terraform           │
│  init           plan          apply         destroy             │
│                                                                  │
│  State File (.tfstate)                                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Tracks real-world resources to configuration            │   │
│  │ Stores metadata, dependencies, and sensitive data       │   │
│  │ MUST be stored securely (encrypted, remote backend)     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Configuration Files

### Provider Configuration

```hcl
# versions.tf
terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }

  backend "s3" {
    bucket         = "my-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

# providers.tf
provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Environment = var.environment
      ManagedBy   = "terraform"
      Project     = var.project_name
    }
  }
}

# Provider alias for multi-region
provider "aws" {
  alias  = "us_west"
  region = "us-west-2"
}
```

### Variables

```hcl
# variables.tf
variable "environment" {
  description = "Environment name"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "Environment must be dev, staging, or production."
  }
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "instance_config" {
  description = "EC2 instance configuration"
  type = object({
    instance_type = string
    ami_id        = string
    volume_size   = number
    encrypted     = optional(bool, true)
  })
}

variable "allowed_cidrs" {
  description = "Allowed CIDR blocks"
  type        = list(string)
  default     = []
}

variable "tags" {
  description = "Additional tags"
  type        = map(string)
  default     = {}
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}
```

### Outputs

```hcl
# outputs.tf
output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "instance_public_ips" {
  description = "Public IPs of instances"
  value       = aws_instance.web[*].public_ip
}

output "load_balancer_dns" {
  description = "Load balancer DNS name"
  value       = aws_lb.main.dns_name
}

output "database_endpoint" {
  description = "Database endpoint"
  value       = aws_db_instance.main.endpoint
  sensitive   = true
}
```

## Resources and Data Sources

### Resource Syntax

```hcl
# Basic resource
resource "aws_instance" "web" {
  ami           = var.ami_id
  instance_type = var.instance_type

  tags = {
    Name = "web-server"
  }
}

# Resource with count
resource "aws_instance" "web" {
  count = 3

  ami           = var.ami_id
  instance_type = var.instance_type

  tags = {
    Name = "web-server-${count.index + 1}"
  }
}

# Resource with for_each (map)
resource "aws_instance" "servers" {
  for_each = {
    web     = "t3.small"
    api     = "t3.medium"
    worker  = "t3.large"
  }

  ami           = var.ami_id
  instance_type = each.value

  tags = {
    Name = each.key
    Role = each.key
  }
}

# Resource with for_each (set)
resource "aws_iam_user" "users" {
  for_each = toset(["alice", "bob", "charlie"])

  name = each.value
}
```

### Data Sources

```hcl
# Get latest AMI
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# Get availability zones
data "aws_availability_zones" "available" {
  state = "available"
}

# Get current AWS account
data "aws_caller_identity" "current" {}

# Get current region
data "aws_region" "current" {}

# Remote state data source
data "terraform_remote_state" "network" {
  backend = "s3"
  config = {
    bucket = "my-terraform-state"
    key    = "network/terraform.tfstate"
    region = "us-east-1"
  }
}

# Using data sources
resource "aws_instance" "web" {
  ami               = data.aws_ami.amazon_linux.id
  instance_type     = "t3.micro"
  availability_zone = data.aws_availability_zones.available.names[0]
  subnet_id         = data.terraform_remote_state.network.outputs.private_subnet_ids[0]
}
```

## Expressions and Functions

### Local Values

```hcl
locals {
  # Common tags
  common_tags = {
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "terraform"
  }

  # Computed values
  is_production = var.environment == "production"
  name_prefix   = "${var.project_name}-${var.environment}"

  # Conditional expressions
  instance_type = local.is_production ? "t3.large" : "t3.small"

  # Complex transformations
  subnet_map = {
    for idx, subnet in var.subnets :
    subnet.name => {
      cidr = subnet.cidr
      az   = data.aws_availability_zones.available.names[idx % length(data.aws_availability_zones.available.names)]
    }
  }
}
```

### Built-in Functions

```hcl
locals {
  # String functions
  upper_name     = upper(var.name)                  # "MYAPP"
  lower_name     = lower(var.name)                  # "myapp"
  trimmed        = trim("  hello  ", " ")           # "hello"
  replaced       = replace("hello-world", "-", "_") # "hello_world"
  formatted      = format("Hello, %s!", var.name)   # "Hello, MyApp!"
  joined         = join("-", ["a", "b", "c"])       # "a-b-c"
  split_string   = split(",", "a,b,c")              # ["a", "b", "c"]

  # Collection functions
  list_length    = length(var.subnets)              # 3
  first_element  = element(var.subnets, 0)          # First subnet
  flattened      = flatten([["a"], ["b", "c"]])     # ["a", "b", "c"]
  merged_maps    = merge(var.tags, local.common_tags)
  distinct_list  = distinct(["a", "a", "b"])        # ["a", "b"]
  sorted_list    = sort(["c", "a", "b"])            # ["a", "b", "c"]
  contains_check = contains(["a", "b"], "a")        # true
  lookup_value   = lookup(var.sizes, "small", "t3.micro")

  # Numeric functions
  max_value      = max(1, 2, 3)                     # 3
  min_value      = min(1, 2, 3)                     # 1
  ceiling        = ceil(1.5)                        # 2
  flooring       = floor(1.9)                       # 1

  # Type conversion
  to_string      = tostring(123)                    # "123"
  to_number      = tonumber("123")                  # 123
  to_list        = tolist(toset(["a", "b"]))       # ["a", "b"]
  to_set         = toset(["a", "a", "b"])          # ["a", "b"]
  to_map         = tomap({ a = 1, b = 2 })

  # File functions
  file_content   = file("${path.module}/script.sh")
  template       = templatefile("${path.module}/config.tpl", {
    port = 8080
    hosts = ["host1", "host2"]
  })

  # Encoding functions
  base64_encoded = base64encode("hello")
  json_encoded   = jsonencode({ key = "value" })
  yaml_decoded   = yamldecode(file("config.yaml"))
}
```

### Dynamic Blocks

```hcl
resource "aws_security_group" "web" {
  name   = "web-sg"
  vpc_id = var.vpc_id

  # Dynamic ingress rules
  dynamic "ingress" {
    for_each = var.ingress_rules
    content {
      description = ingress.value.description
      from_port   = ingress.value.port
      to_port     = ingress.value.port
      protocol    = ingress.value.protocol
      cidr_blocks = ingress.value.cidr_blocks
    }
  }

  # Static egress
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Variable for dynamic block
variable "ingress_rules" {
  type = list(object({
    description = string
    port        = number
    protocol    = string
    cidr_blocks = list(string)
  }))
  default = [
    {
      description = "HTTP"
      port        = 80
      protocol    = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
    },
    {
      description = "HTTPS"
      port        = 443
      protocol    = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
    }
  ]
}
```

## Modules

### Module Structure

```
modules/
└── web_app/
    ├── main.tf
    ├── variables.tf
    ├── outputs.tf
    ├── versions.tf
    ├── locals.tf
    └── README.md
```

### Creating a Module

```hcl
# modules/web_app/main.tf
resource "aws_security_group" "web" {
  name        = "${var.name}-sg"
  description = "Security group for ${var.name}"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name = "${var.name}-sg"
  })
}

resource "aws_launch_template" "web" {
  name_prefix   = "${var.name}-"
  image_id      = var.ami_id
  instance_type = var.instance_type

  vpc_security_group_ids = [aws_security_group.web.id]

  user_data = base64encode(templatefile("${path.module}/templates/user_data.sh", {
    app_name = var.name
    port     = var.port
  }))

  tag_specifications {
    resource_type = "instance"
    tags = merge(var.tags, {
      Name = var.name
    })
  }
}

resource "aws_autoscaling_group" "web" {
  name                = "${var.name}-asg"
  vpc_zone_identifier = var.subnet_ids
  target_group_arns   = [aws_lb_target_group.web.arn]

  min_size         = var.min_size
  max_size         = var.max_size
  desired_capacity = var.desired_capacity

  launch_template {
    id      = aws_launch_template.web.id
    version = "$Latest"
  }

  dynamic "tag" {
    for_each = merge(var.tags, { Name = var.name })
    content {
      key                 = tag.key
      value               = tag.value
      propagate_at_launch = true
    }
  }
}

resource "aws_lb" "web" {
  name               = "${var.name}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.web.id]
  subnets            = var.public_subnet_ids

  tags = var.tags
}

resource "aws_lb_target_group" "web" {
  name     = "${var.name}-tg"
  port     = var.port
  protocol = "HTTP"
  vpc_id   = var.vpc_id

  health_check {
    path                = var.health_check_path
    healthy_threshold   = 2
    unhealthy_threshold = 10
  }
}

resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.web.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = var.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.web.arn
  }
}
```

### Using Modules

```hcl
# Root module
module "web_app" {
  source = "./modules/web_app"

  name                = "my-app"
  vpc_id              = module.vpc.vpc_id
  subnet_ids          = module.vpc.private_subnet_ids
  public_subnet_ids   = module.vpc.public_subnet_ids
  ami_id              = data.aws_ami.amazon_linux.id
  instance_type       = "t3.small"
  certificate_arn     = aws_acm_certificate.main.arn

  min_size         = 2
  max_size         = 10
  desired_capacity = 3

  port              = 8080
  health_check_path = "/health"

  tags = local.common_tags
}

# Using registry modules
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.0.0"

  name = "my-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["us-east-1a", "us-east-1b", "us-east-1c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  enable_nat_gateway = true
  single_nat_gateway = false
}
```

## State Management

### State Commands

```bash
# List resources in state
terraform state list

# Show specific resource
terraform state show aws_instance.web

# Move resource in state
terraform state mv aws_instance.web aws_instance.web_server

# Remove resource from state (doesn't destroy)
terraform state rm aws_instance.web

# Import existing resource
terraform import aws_instance.web i-1234567890abcdef0

# Pull remote state locally
terraform state pull > terraform.tfstate

# Push local state to remote
terraform state push terraform.tfstate

# Replace provider in state
terraform state replace-provider hashicorp/aws registry.example.com/aws
```

### Import Resources

```hcl
# Define resource block first
resource "aws_instance" "imported" {
  # Configuration will be filled after import
}

# Import command
# terraform import aws_instance.imported i-1234567890abcdef0

# Generate configuration (Terraform 1.5+)
# terraform plan -generate-config-out=generated.tf
```

```hcl
# Import blocks (Terraform 1.5+)
import {
  to = aws_instance.imported
  id = "i-1234567890abcdef0"
}

import {
  to = aws_s3_bucket.imported
  id = "my-existing-bucket"
}
```

## Workspaces

```bash
# List workspaces
terraform workspace list

# Create workspace
terraform workspace new dev
terraform workspace new staging
terraform workspace new production

# Select workspace
terraform workspace select production

# Show current workspace
terraform workspace show

# Delete workspace
terraform workspace delete dev
```

```hcl
# Use workspace in configuration
locals {
  environment = terraform.workspace

  instance_type = {
    dev        = "t3.small"
    staging    = "t3.medium"
    production = "t3.large"
  }
}

resource "aws_instance" "web" {
  ami           = var.ami_id
  instance_type = local.instance_type[local.environment]

  tags = {
    Environment = local.environment
  }
}
```

## Terraform Cloud/Enterprise

```hcl
# Backend configuration for Terraform Cloud
terraform {
  cloud {
    organization = "my-org"

    workspaces {
      name = "my-workspace"
    }
  }
}

# Or using tags for workspace selection
terraform {
  cloud {
    organization = "my-org"

    workspaces {
      tags = ["app:web", "env:production"]
    }
  }
}
```

## Advanced Patterns

### Conditional Resources

```hcl
resource "aws_eip" "nat" {
  count  = var.enable_nat_gateway ? var.az_count : 0
  domain = "vpc"
}

resource "aws_nat_gateway" "main" {
  count         = var.enable_nat_gateway ? var.az_count : 0
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id
}
```

### Depends On

```hcl
resource "aws_instance" "web" {
  ami           = var.ami_id
  instance_type = var.instance_type

  # Explicit dependency
  depends_on = [
    aws_internet_gateway.main,
    aws_db_instance.main
  ]
}
```

### Lifecycle Rules

```hcl
resource "aws_instance" "web" {
  ami           = var.ami_id
  instance_type = var.instance_type

  lifecycle {
    # Create new before destroying old
    create_before_destroy = true

    # Prevent destruction
    prevent_destroy = true

    # Ignore changes to specific attributes
    ignore_changes = [
      ami,
      tags["UpdatedAt"]
    ]

    # Custom replacement condition
    replace_triggered_by = [
      aws_security_group.web.id
    ]

    # Preconditions
    precondition {
      condition     = data.aws_ami.amazon_linux.architecture == "x86_64"
      error_message = "AMI must be x86_64 architecture."
    }

    # Postconditions
    postcondition {
      condition     = self.public_ip != ""
      error_message = "Instance must have a public IP."
    }
  }
}
```

### Provisioners (Use Sparingly)

```hcl
resource "aws_instance" "web" {
  ami           = var.ami_id
  instance_type = var.instance_type

  # Remote exec
  provisioner "remote-exec" {
    inline = [
      "sudo yum update -y",
      "sudo yum install -y nginx",
      "sudo systemctl start nginx"
    ]

    connection {
      type        = "ssh"
      user        = "ec2-user"
      private_key = file("~/.ssh/id_rsa")
      host        = self.public_ip
    }
  }

  # Local exec
  provisioner "local-exec" {
    command = "echo ${self.private_ip} >> private_ips.txt"
  }

  # File provisioner
  provisioner "file" {
    source      = "config/app.conf"
    destination = "/etc/app/app.conf"

    connection {
      type        = "ssh"
      user        = "ec2-user"
      private_key = file("~/.ssh/id_rsa")
      host        = self.public_ip
    }
  }
}
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│                 Terraform Best Practices                         │
├─────────────────────────────────────────────────────────────────┤
│ ☐ Use remote state with locking                                 │
│ ☐ Organize code with consistent file structure                  │
│ ☐ Use modules for reusable components                           │
│ ☐ Pin provider and module versions                              │
│ ☐ Use variable validation                                       │
│ ☐ Mark sensitive variables appropriately                        │
│ ☐ Use locals for repeated expressions                           │
│ ☐ Implement proper tagging strategy                             │
│ ☐ Use data sources instead of hardcoding                        │
│ ☐ Run terraform fmt and validate in CI                          │
│ ☐ Review plan output before applying                            │
│ ☐ Avoid provisioners when possible                              │
│ ☐ Use workspaces or directory structure for environments        │
│ ☐ Document modules with README                                  │
└─────────────────────────────────────────────────────────────────┘
```
