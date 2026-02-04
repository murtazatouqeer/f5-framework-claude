# Resource Dependencies

## Overview

Terraform automatically determines the order of resource operations based on dependencies. Understanding dependency management is crucial for reliable infrastructure provisioning.

## Implicit Dependencies

### Reference-Based Dependencies

```hcl
# VPC must be created first (referenced by subnet)
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
}

# Subnet depends on VPC (implicit via vpc_id reference)
resource "aws_subnet" "public" {
  vpc_id     = aws_vpc.main.id  # Creates dependency
  cidr_block = "10.0.1.0/24"
}

# Security group depends on VPC
resource "aws_security_group" "web" {
  vpc_id = aws_vpc.main.id  # Creates dependency
  name   = "web-sg"
}

# Instance depends on subnet and security group
resource "aws_instance" "web" {
  subnet_id              = aws_subnet.public.id           # Creates dependency
  vpc_security_group_ids = [aws_security_group.web.id]    # Creates dependency
}
```

### Dependency Graph

```
aws_vpc.main
    │
    ├── aws_subnet.public
    │       │
    │       └── aws_instance.web
    │               │
    └── aws_security_group.web ─┘
```

### Viewing Dependencies

```bash
# Generate dependency graph
terraform graph | dot -Tpng > graph.png

# View graph in text format
terraform graph
```

## Explicit Dependencies

### depends_on

```hcl
# Use when dependency isn't apparent from references
resource "aws_instance" "web" {
  ami           = "ami-0123456789"
  instance_type = "t3.micro"

  # IAM role policy must exist before instance
  depends_on = [aws_iam_role_policy.web]
}

resource "aws_iam_role_policy" "web" {
  role   = aws_iam_role.web.id
  policy = data.aws_iam_policy_document.web.json
}
```

### When to Use depends_on

```hcl
# 1. Side effects that aren't captured by references
resource "null_resource" "setup" {
  provisioner "local-exec" {
    command = "setup-script.sh"
  }
}

resource "aws_instance" "web" {
  depends_on = [null_resource.setup]
}

# 2. API rate limiting or ordering requirements
resource "aws_route53_record" "main" {
  depends_on = [aws_route53_record.ns]  # NS records first
}

# 3. Resources with eventual consistency
resource "aws_iam_role_policy_attachment" "web" {
  role       = aws_iam_role.web.name
  policy_arn = aws_iam_policy.web.arn
}

resource "aws_instance" "web" {
  iam_instance_profile = aws_iam_instance_profile.web.name

  depends_on = [aws_iam_role_policy_attachment.web]
}
```

## Module Dependencies

### Module to Module

```hcl
module "vpc" {
  source = "./modules/vpc"
}

module "eks" {
  source = "./modules/eks"

  vpc_id     = module.vpc.vpc_id        # Implicit dependency
  subnet_ids = module.vpc.private_subnets

  depends_on = [module.vpc]  # Explicit if needed
}
```

### Passing Dependencies

```hcl
# Parent module
module "database" {
  source = "./modules/database"
}

module "application" {
  source = "./modules/application"

  database_endpoint = module.database.endpoint

  # Pass dependency information
  depends_on = [module.database]
}
```

## Circular Dependencies

### Problem

```hcl
# This creates a circular dependency (WILL FAIL)
resource "aws_security_group" "web" {
  ingress {
    security_groups = [aws_security_group.api.id]  # Depends on api
  }
}

resource "aws_security_group" "api" {
  ingress {
    security_groups = [aws_security_group.web.id]  # Depends on web
  }
}
```

### Solution: Separate Rules

```hcl
# Create security groups without rules
resource "aws_security_group" "web" {
  name   = "web-sg"
  vpc_id = aws_vpc.main.id
}

resource "aws_security_group" "api" {
  name   = "api-sg"
  vpc_id = aws_vpc.main.id
}

# Add rules separately
resource "aws_security_group_rule" "web_to_api" {
  type                     = "ingress"
  security_group_id        = aws_security_group.api.id
  source_security_group_id = aws_security_group.web.id
  from_port                = 8080
  to_port                  = 8080
  protocol                 = "tcp"
}

resource "aws_security_group_rule" "api_to_web" {
  type                     = "ingress"
  security_group_id        = aws_security_group.web.id
  source_security_group_id = aws_security_group.api.id
  from_port                = 443
  to_port                  = 443
  protocol                 = "tcp"
}
```

## Data Source Dependencies

### Depends on Resource

```hcl
resource "aws_instance" "web" {
  ami           = "ami-0123456789"
  instance_type = "t3.micro"

  tags = {
    Name = "web-server"
  }
}

# Data source depends on resource
data "aws_instance" "web" {
  filter {
    name   = "tag:Name"
    values = ["web-server"]
  }

  depends_on = [aws_instance.web]
}
```

### Resource Depends on Data

```hcl
# Data source fetches existing VPC
data "aws_vpc" "main" {
  filter {
    name   = "tag:Name"
    values = ["main-vpc"]
  }
}

# Resource implicitly depends on data source
resource "aws_subnet" "new" {
  vpc_id     = data.aws_vpc.main.id  # Implicit dependency
  cidr_block = "10.0.100.0/24"
}
```

## Provisioner Dependencies

### Local-Exec

```hcl
resource "aws_instance" "web" {
  ami           = "ami-0123456789"
  instance_type = "t3.micro"

  provisioner "local-exec" {
    command = "echo ${self.private_ip} >> inventory.txt"
  }
}

# Ensure provisioner completes before dependent resource
resource "null_resource" "configure" {
  depends_on = [aws_instance.web]

  provisioner "local-exec" {
    command = "ansible-playbook -i inventory.txt playbook.yml"
  }
}
```

### Remote-Exec

```hcl
resource "aws_instance" "web" {
  ami           = "ami-0123456789"
  instance_type = "t3.micro"

  provisioner "remote-exec" {
    inline = [
      "sudo apt-get update",
      "sudo apt-get install -y nginx",
    ]

    connection {
      type        = "ssh"
      user        = "ubuntu"
      private_key = file("~/.ssh/id_rsa")
      host        = self.public_ip
    }
  }

  # Provisioner depends on security group allowing SSH
  depends_on = [aws_security_group_rule.ssh_ingress]
}
```

## Count and For_Each Dependencies

### With Count

```hcl
resource "aws_instance" "web" {
  count = 3

  ami           = "ami-0123456789"
  instance_type = "t3.micro"
}

# Depends on all instances
resource "aws_elb" "web" {
  instances = aws_instance.web[*].id  # Depends on all
}

# Depends on specific instance
resource "aws_eip" "web" {
  count    = 3
  instance = aws_instance.web[count.index].id  # Depends on corresponding instance
}
```

### With For_Each

```hcl
resource "aws_instance" "servers" {
  for_each = {
    web = "t3.micro"
    api = "t3.small"
  }

  ami           = "ami-0123456789"
  instance_type = each.value
}

# Depends on specific instance
resource "aws_eip" "web" {
  instance = aws_instance.servers["web"].id
}

# Depends on all instances
resource "aws_lb_target_group_attachment" "servers" {
  for_each = aws_instance.servers

  target_group_arn = aws_lb_target_group.main.arn
  target_id        = each.value.id
}
```

## Dependency Patterns

### Gateway Pattern

```hcl
# Internet Gateway must be created before NAT Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
}

# EIP for NAT depends on IGW attachment
resource "aws_eip" "nat" {
  domain = "vpc"

  depends_on = [aws_internet_gateway.main]
}

# NAT Gateway depends on IGW for internet access
resource "aws_nat_gateway" "main" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public.id

  depends_on = [aws_internet_gateway.main]
}
```

### IAM Pattern

```hcl
# Role -> Policy -> Attachment -> Resource using role
resource "aws_iam_role" "lambda" {
  name               = "lambda-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}

resource "aws_iam_policy" "lambda" {
  name   = "lambda-policy"
  policy = data.aws_iam_policy_document.lambda.json
}

resource "aws_iam_role_policy_attachment" "lambda" {
  role       = aws_iam_role.lambda.name
  policy_arn = aws_iam_policy.lambda.arn
}

resource "aws_lambda_function" "main" {
  role = aws_iam_role.lambda.arn

  # Wait for policy attachment
  depends_on = [aws_iam_role_policy_attachment.lambda]
}
```

### DNS Pattern

```hcl
# Certificate must be created first
resource "aws_acm_certificate" "main" {
  domain_name       = "example.com"
  validation_method = "DNS"
}

# DNS records for validation
resource "aws_route53_record" "validation" {
  for_each = {
    for dvo in aws_acm_certificate.main.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  zone_id = aws_route53_zone.main.zone_id
  name    = each.value.name
  type    = each.value.type
  records = [each.value.record]
  ttl     = 60
}

# Wait for certificate validation
resource "aws_acm_certificate_validation" "main" {
  certificate_arn         = aws_acm_certificate.main.arn
  validation_record_fqdns = [for record in aws_route53_record.validation : record.fqdn]
}

# Use validated certificate
resource "aws_lb_listener" "https" {
  certificate_arn = aws_acm_certificate_validation.main.certificate_arn

  depends_on = [aws_acm_certificate_validation.main]
}
```

## Best Practices

1. **Prefer Implicit**: Use resource references for dependencies when possible
2. **Explicit When Needed**: Use depends_on for side effects and timing issues
3. **Avoid Circular**: Restructure resources to eliminate circular dependencies
4. **Module Boundaries**: Pass outputs between modules rather than direct references
5. **Document Complex Dependencies**: Add comments explaining non-obvious dependencies
6. **Test Order**: Verify dependency ordering with `terraform graph`
7. **IAM Delays**: Account for IAM eventual consistency with depends_on
