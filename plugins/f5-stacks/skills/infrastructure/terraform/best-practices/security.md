# Terraform Security Best Practices

## Overview

Security is paramount in infrastructure as code. This guide covers security practices for Terraform configurations, secrets management, and compliance.

## Secrets Management

### Never Store Secrets in Code

```hcl
# ❌ BAD: Hardcoded secrets
resource "aws_db_instance" "main" {
  password = "super_secret_password"  # NEVER DO THIS
}

# ✅ GOOD: Use variables with sensitive flag
variable "database_password" {
  type      = string
  sensitive = true
}

resource "aws_db_instance" "main" {
  password = var.database_password
}

# ✅ GOOD: Use secrets manager
data "aws_secretsmanager_secret_version" "db_password" {
  secret_id = aws_secretsmanager_secret.database.id
}

resource "aws_db_instance" "main" {
  password = data.aws_secretsmanager_secret_version.db_password.secret_string
}
```

### Generate Random Secrets

```hcl
resource "random_password" "database" {
  length           = 32
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

resource "aws_secretsmanager_secret" "database" {
  name = "${var.project}/database/password"

  tags = {
    Purpose = "Database credentials"
  }
}

resource "aws_secretsmanager_secret_version" "database" {
  secret_id     = aws_secretsmanager_secret.database.id
  secret_string = random_password.database.result
}
```

### Environment-Specific Secrets

```hcl
# Use different secret paths per environment
data "aws_secretsmanager_secret_version" "api_key" {
  secret_id = "${var.project}/${var.environment}/api-key"
}

# Vault integration
data "vault_generic_secret" "database" {
  path = "secret/${var.environment}/database"
}

resource "aws_db_instance" "main" {
  username = data.vault_generic_secret.database.data["username"]
  password = data.vault_generic_secret.database.data["password"]
}
```

## State Security

### Encrypted Remote State

```hcl
# S3 backend with encryption
terraform {
  backend "s3" {
    bucket         = "company-terraform-state"
    key            = "project/environment/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    kms_key_id     = "alias/terraform-state"
    dynamodb_table = "terraform-locks"
  }
}

# KMS key for state encryption
resource "aws_kms_key" "terraform_state" {
  description             = "Terraform state encryption key"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "Allow Terraform Role"
        Effect = "Allow"
        Principal = {
          AWS = aws_iam_role.terraform.arn
        }
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:GenerateDataKey"
        ]
        Resource = "*"
      }
    ]
  })
}
```

### State Access Control

```hcl
# S3 bucket policy for state
resource "aws_s3_bucket_policy" "state" {
  bucket = aws_s3_bucket.terraform_state.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "DenyUnencryptedUploads"
        Effect = "Deny"
        Principal = "*"
        Action = "s3:PutObject"
        Resource = "${aws_s3_bucket.terraform_state.arn}/*"
        Condition = {
          StringNotEquals = {
            "s3:x-amz-server-side-encryption" = "aws:kms"
          }
        }
      },
      {
        Sid    = "DenyInsecureTransport"
        Effect = "Deny"
        Principal = "*"
        Action = "s3:*"
        Resource = [
          aws_s3_bucket.terraform_state.arn,
          "${aws_s3_bucket.terraform_state.arn}/*"
        ]
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
      }
    ]
  })
}

# Block public access
resource "aws_s3_bucket_public_access_block" "state" {
  bucket = aws_s3_bucket.terraform_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
```

## IAM Security

### Least Privilege Principle

```hcl
# ❌ BAD: Overly permissive
resource "aws_iam_role_policy" "bad" {
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "*"
      Resource = "*"
    }]
  })
}

# ✅ GOOD: Least privilege
resource "aws_iam_role_policy" "good" {
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ReadS3Bucket"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.data.arn,
          "${aws_s3_bucket.data.arn}/*"
        ]
      }
    ]
  })
}
```

### IAM Policy Conditions

```hcl
resource "aws_iam_policy" "secure_access" {
  name = "${var.project}-secure-access"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "RequireMFA"
        Effect = "Allow"
        Action = [
          "s3:*"
        ]
        Resource = "*"
        Condition = {
          Bool = {
            "aws:MultiFactorAuthPresent" = "true"
          }
        }
      },
      {
        Sid    = "RestrictToVPC"
        Effect = "Allow"
        Action = [
          "dynamodb:*"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "aws:SourceVpc" = aws_vpc.main.id
          }
        }
      },
      {
        Sid    = "RestrictByIP"
        Effect = "Allow"
        Action = [
          "ec2:Describe*"
        ]
        Resource = "*"
        Condition = {
          IpAddress = {
            "aws:SourceIp" = var.allowed_ip_ranges
          }
        }
      }
    ]
  })
}
```

### Permission Boundaries

```hcl
resource "aws_iam_policy" "permission_boundary" {
  name = "DeveloperPermissionBoundary"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowedServices"
        Effect = "Allow"
        Action = [
          "s3:*",
          "dynamodb:*",
          "lambda:*",
          "logs:*",
          "cloudwatch:*"
        ]
        Resource = "*"
      },
      {
        Sid    = "DenyIAMChanges"
        Effect = "Deny"
        Action = [
          "iam:CreateUser",
          "iam:DeleteUser",
          "iam:CreateRole",
          "iam:DeleteRole",
          "iam:AttachRolePolicy",
          "iam:PutRolePolicy"
        ]
        Resource = "*"
      },
      {
        Sid    = "DenySecurityChanges"
        Effect = "Deny"
        Action = [
          "organizations:*",
          "account:*"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role" "developer" {
  name                 = "DeveloperRole"
  permissions_boundary = aws_iam_policy.permission_boundary.arn

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
      }
      Action = "sts:AssumeRole"
    }]
  })
}
```

## Network Security

### Secure Security Groups

```hcl
# ❌ BAD: Open to world
resource "aws_security_group" "bad" {
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # NEVER DO THIS
  }
}

# ✅ GOOD: Restricted access
resource "aws_security_group" "good" {
  name        = "${var.project}-bastion"
  description = "Bastion host security group"
  vpc_id      = aws_vpc.main.id

  # SSH from specific IPs only
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.allowed_ssh_cidrs
    description = "SSH from allowed networks"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound"
  }

  tags = {
    Name = "${var.project}-bastion-sg"
  }

  lifecycle {
    create_before_destroy = true
  }
}
```

### Private Subnets and NAT

```hcl
# Application in private subnet
resource "aws_instance" "app" {
  ami           = data.aws_ami.amazon_linux.id
  instance_type = var.instance_type
  subnet_id     = aws_subnet.private.id  # Private subnet

  # No public IP
  associate_public_ip_address = false

  vpc_security_group_ids = [aws_security_group.app.id]

  tags = {
    Name = "${var.project}-app"
  }
}

# NAT Gateway for outbound access
resource "aws_nat_gateway" "main" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public.id

  tags = {
    Name = "${var.project}-nat"
  }
}
```

### VPC Endpoints

```hcl
# S3 Gateway Endpoint
resource "aws_vpc_endpoint" "s3" {
  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.${var.region}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = aws_route_table.private[*].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "AllowS3Access"
      Effect    = "Allow"
      Principal = "*"
      Action    = "s3:*"
      Resource  = "*"
    }]
  })

  tags = {
    Name = "${var.project}-s3-endpoint"
  }
}

# Interface Endpoint for Secrets Manager
resource "aws_vpc_endpoint" "secretsmanager" {
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${var.region}.secretsmanager"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true

  tags = {
    Name = "${var.project}-secretsmanager-endpoint"
  }
}
```

## Encryption

### Encryption at Rest

```hcl
# S3 encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "main" {
  bucket = aws_s3_bucket.main.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.main.arn
    }
    bucket_key_enabled = true
  }
}

# RDS encryption
resource "aws_db_instance" "main" {
  storage_encrypted = true
  kms_key_id        = aws_kms_key.database.arn
  # ...
}

# EBS encryption
resource "aws_ebs_volume" "main" {
  encrypted  = true
  kms_key_id = aws_kms_key.ebs.arn
  # ...
}

# EKS secrets encryption
resource "aws_eks_cluster" "main" {
  encryption_config {
    provider {
      key_arn = aws_kms_key.eks.arn
    }
    resources = ["secrets"]
  }
  # ...
}
```

### Encryption in Transit

```hcl
# ALB with HTTPS
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.main.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = aws_acm_certificate.main.arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.main.arn
  }
}

# RDS SSL enforcement
resource "aws_db_parameter_group" "main" {
  family = "postgres15"

  parameter {
    name  = "rds.force_ssl"
    value = "1"
  }
}
```

## Security Scanning

### Checkov Integration

```yaml
# .checkov.yml
framework:
  - terraform
check:
  - CKV_AWS_*
skip-check:
  - CKV_AWS_144  # Skip specific check if justified
soft-fail:
  - CKV_AWS_18   # Soft fail for non-critical
```

### tfsec Integration

```yaml
# .tfsec/config.yml
severity_overrides:
  AWS006: WARNING
exclude:
  - aws-s3-enable-versioning  # If versioning not needed
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/antonbabenko/pre-commit-terraform
    rev: v1.83.5
    hooks:
      - id: terraform_fmt
      - id: terraform_validate
      - id: terraform_tflint
      - id: terraform_docs
      - id: terraform_checkov
        args:
          - --args=--config-file __GIT_WORKING_DIR__/.checkov.yml
      - id: terraform_tfsec
```

## Compliance

### AWS Config Rules

```hcl
resource "aws_config_config_rule" "encrypted_volumes" {
  name = "encrypted-volumes"

  source {
    owner             = "AWS"
    source_identifier = "ENCRYPTED_VOLUMES"
  }
}

resource "aws_config_config_rule" "s3_bucket_ssl" {
  name = "s3-bucket-ssl-requests-only"

  source {
    owner             = "AWS"
    source_identifier = "S3_BUCKET_SSL_REQUESTS_ONLY"
  }
}
```

### Sentinel Policies (Terraform Enterprise)

```hcl
# sentinel.hcl
policy "require-encryption" {
  enforcement_level = "hard-mandatory"
}

policy "restrict-instance-types" {
  enforcement_level = "soft-mandatory"
}
```

## Best Practices Summary

1. **Never commit secrets** - Use secrets managers, not hardcoded values
2. **Encrypt everything** - State, data at rest, data in transit
3. **Least privilege** - Minimal permissions for all roles
4. **Network isolation** - Private subnets, VPC endpoints
5. **Audit logging** - Enable CloudTrail, VPC Flow Logs
6. **Security scanning** - Integrate Checkov, tfsec in CI/CD
7. **Regular rotation** - Rotate secrets, keys periodically
8. **Version control** - Track all changes, require reviews
