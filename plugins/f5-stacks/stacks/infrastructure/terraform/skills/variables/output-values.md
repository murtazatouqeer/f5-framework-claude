# Output Values

## Overview

Output values expose information about your infrastructure. They're essential for module composition, cross-configuration references, and providing useful information to users.

## Output Declaration

### Basic Syntax

```hcl
output "name" {
  value = resource.attribute
}
```

### Complete Output Block

```hcl
output "vpc_id" {
  description = "The ID of the VPC"
  value       = aws_vpc.main.id
  sensitive   = false

  # Terraform 1.2+
  precondition {
    condition     = aws_vpc.main.id != ""
    error_message = "VPC ID must not be empty."
  }
}
```

## Output Types

### Simple Values

```hcl
# String
output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

# Number
output "instance_count" {
  description = "Number of instances created"
  value       = length(aws_instance.web)
}

# Boolean
output "nat_gateway_enabled" {
  description = "Whether NAT gateway was created"
  value       = var.enable_nat_gateway
}
```

### Collections

```hcl
# List
output "subnet_ids" {
  description = "List of subnet IDs"
  value       = aws_subnet.private[*].id
}

# Set
output "security_group_ids" {
  description = "Set of security group IDs"
  value       = toset([
    aws_security_group.web.id,
    aws_security_group.db.id
  ])
}

# Map
output "instance_ips" {
  description = "Map of instance names to IPs"
  value       = { for k, v in aws_instance.servers : k => v.private_ip }
}
```

### Complex Structures

```hcl
# Object
output "vpc_info" {
  description = "Complete VPC information"
  value = {
    id         = aws_vpc.main.id
    arn        = aws_vpc.main.arn
    cidr_block = aws_vpc.main.cidr_block
  }
}

# Nested structure
output "database_config" {
  description = "Database configuration"
  value = {
    endpoint = aws_db_instance.main.endpoint
    port     = aws_db_instance.main.port
    database = aws_db_instance.main.db_name
    connection = {
      host     = aws_db_instance.main.address
      port     = aws_db_instance.main.port
      username = aws_db_instance.main.username
    }
  }
}
```

## Sensitive Outputs

```hcl
# Hide sensitive values from CLI output
output "db_password" {
  description = "Database password"
  value       = random_password.db.result
  sensitive   = true
}

output "api_key" {
  description = "API key"
  value       = aws_api_gateway_api_key.main.value
  sensitive   = true
}

# Access sensitive outputs
# terraform output db_password
# terraform output -json db_password
```

## Conditional Outputs

### Using Conditionals

```hcl
output "nat_gateway_ip" {
  description = "NAT gateway public IP"
  value       = var.enable_nat_gateway ? aws_eip.nat[0].public_ip : null
}

output "load_balancer_dns" {
  description = "Load balancer DNS name"
  value       = var.create_alb ? aws_lb.main[0].dns_name : "N/A"
}
```

### Using try()

```hcl
output "optional_resource" {
  description = "Optional resource ID"
  value       = try(aws_instance.optional[0].id, null)
}

output "nested_value" {
  description = "Nested attribute with fallback"
  value       = try(aws_instance.main.root_block_device[0].volume_id, "unknown")
}
```

## Output from count/for_each

### From count

```hcl
resource "aws_instance" "web" {
  count         = 3
  ami           = var.ami_id
  instance_type = "t3.micro"
}

# All IDs as list
output "instance_ids" {
  value = aws_instance.web[*].id
}

# All IPs as list
output "instance_ips" {
  value = aws_instance.web[*].private_ip
}

# Specific instance
output "first_instance_id" {
  value = aws_instance.web[0].id
}
```

### From for_each

```hcl
resource "aws_instance" "servers" {
  for_each      = var.servers
  ami           = var.ami_id
  instance_type = each.value.instance_type
}

# All instances as map
output "server_ids" {
  value = { for k, v in aws_instance.servers : k => v.id }
}

# IPs as map
output "server_ips" {
  value = { for k, v in aws_instance.servers : k => v.private_ip }
}

# Specific instance
output "web_server_id" {
  value = aws_instance.servers["web"].id
}
```

## Module Outputs

### Defining in Module

```hcl
# modules/vpc/outputs.tf

output "vpc_id" {
  description = "The VPC ID"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "List of public subnet IDs"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "List of private subnet IDs"
  value       = aws_subnet.private[*].id
}

output "nat_gateway_ips" {
  description = "NAT gateway public IPs"
  value       = aws_eip.nat[*].public_ip
}
```

### Using Module Outputs

```hcl
module "vpc" {
  source = "./modules/vpc"
}

# Reference module outputs
resource "aws_instance" "web" {
  subnet_id = module.vpc.public_subnet_ids[0]
}

# Pass to another module
module "eks" {
  source = "./modules/eks"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnet_ids
}

# Expose module outputs
output "vpc_id" {
  value = module.vpc.vpc_id
}
```

## Output Preconditions

### Validation (Terraform 1.2+)

```hcl
output "instance_ip" {
  description = "Instance public IP"
  value       = aws_instance.web.public_ip

  precondition {
    condition     = aws_instance.web.public_ip != ""
    error_message = "Instance must have a public IP."
  }
}

output "load_balancer_dns" {
  description = "ALB DNS name"
  value       = aws_lb.main.dns_name

  precondition {
    condition     = can(regex("^.+\\.elb\\.amazonaws\\.com$", aws_lb.main.dns_name))
    error_message = "Invalid ALB DNS name format."
  }
}
```

## Accessing Outputs

### CLI Commands

```bash
# Show all outputs
terraform output

# Show specific output
terraform output vpc_id

# Show in JSON format
terraform output -json

# Show specific output in JSON
terraform output -json vpc_id

# Raw value (no quotes for strings)
terraform output -raw vpc_id
```

### In Other Configurations

```hcl
# Using remote state
data "terraform_remote_state" "network" {
  backend = "s3"

  config = {
    bucket = "terraform-state"
    key    = "network/terraform.tfstate"
    region = "us-east-1"
  }
}

resource "aws_instance" "web" {
  subnet_id = data.terraform_remote_state.network.outputs.public_subnet_ids[0]
}
```

## Output Organization

### Standard Outputs File

```hcl
# outputs.tf

# ====================
# VPC Outputs
# ====================
output "vpc_id" {
  description = "The VPC ID"
  value       = aws_vpc.main.id
}

output "vpc_cidr_block" {
  description = "The VPC CIDR block"
  value       = aws_vpc.main.cidr_block
}

# ====================
# Subnet Outputs
# ====================
output "public_subnet_ids" {
  description = "List of public subnet IDs"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "List of private subnet IDs"
  value       = aws_subnet.private[*].id
}

# ====================
# Security Outputs
# ====================
output "web_security_group_id" {
  description = "Web server security group ID"
  value       = aws_security_group.web.id
}
```

### Grouped Output Object

```hcl
# Single comprehensive output
output "infrastructure" {
  description = "Complete infrastructure details"
  value = {
    vpc = {
      id         = aws_vpc.main.id
      cidr_block = aws_vpc.main.cidr_block
    }
    subnets = {
      public  = aws_subnet.public[*].id
      private = aws_subnet.private[*].id
    }
    security_groups = {
      web = aws_security_group.web.id
      db  = aws_security_group.db.id
    }
  }
}
```

## Documentation

### README Format

```markdown
## Outputs

| Name | Description |
|------|-------------|
| vpc_id | The ID of the VPC |
| public_subnet_ids | List of public subnet IDs |
| private_subnet_ids | List of private subnet IDs |
| nat_gateway_ips | Elastic IPs of NAT gateways |
```

### In-Code Documentation

```hcl
output "eks_cluster_endpoint" {
  description = <<-EOT
    The endpoint for the EKS cluster API server.

    Use this value to configure kubectl:
    aws eks update-kubeconfig --name <cluster-name>

    Format: https://<unique-id>.<region>.eks.amazonaws.com
  EOT

  value = aws_eks_cluster.main.endpoint
}
```

## Best Practices

1. **Document Everything**: Add descriptions to all outputs
2. **Useful Names**: Use clear, descriptive output names
3. **Sensitive Data**: Mark passwords and keys as sensitive
4. **Complete Information**: Output all useful resource attributes
5. **Consistent Structure**: Use consistent naming patterns
6. **Module Interface**: Design outputs as part of module API
7. **Validation**: Add preconditions for critical outputs
8. **Grouped Outputs**: Consider grouping related outputs
9. **Format Output**: Use proper types (lists, maps) for collections
10. **Dependencies**: Be mindful of output dependencies
