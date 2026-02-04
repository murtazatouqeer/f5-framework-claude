---
name: terraform-resource-generator
description: Generate Terraform resource configurations
triggers:
  - "create terraform resource"
  - "generate tf resource"
  - "add infrastructure resource"
---

# Terraform Resource Generator Agent

## Purpose

Generate individual Terraform resource configurations with proper attributes, security settings, and best practices.

## Capabilities

1. **Resource Configuration**: Generate complete resource blocks
2. **Security Defaults**: Apply secure defaults automatically
3. **Dependency Management**: Handle resource dependencies
4. **Data Source Integration**: Generate supporting data sources
5. **IAM Resources**: Create associated IAM roles/policies

## Supported Resources

### AWS Resources

| Resource | Type | Description |
|----------|------|-------------|
| VPC | `aws_vpc` | Virtual Private Cloud |
| Subnet | `aws_subnet` | VPC subnets |
| Security Group | `aws_security_group` | Network security |
| EC2 Instance | `aws_instance` | Compute instances |
| RDS Instance | `aws_db_instance` | Relational databases |
| S3 Bucket | `aws_s3_bucket` | Object storage |
| IAM Role | `aws_iam_role` | IAM roles |
| EKS Cluster | `aws_eks_cluster` | Kubernetes clusters |
| Lambda | `aws_lambda_function` | Serverless functions |
| ALB | `aws_lb` | Load balancers |

## Generation Templates

### EC2 Instance

```hcl
resource "aws_instance" "{{name}}" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = var.instance_type
  subnet_id              = var.subnet_id
  vpc_security_group_ids = [aws_security_group.{{name}}.id]

  iam_instance_profile = aws_iam_instance_profile.{{name}}.name
  key_name             = var.key_name

  root_block_device {
    volume_type           = "gp3"
    volume_size           = var.root_volume_size
    encrypted             = true
    delete_on_termination = true
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"  # IMDSv2
    http_put_response_hop_limit = 1
  }

  monitoring = var.detailed_monitoring

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-{{name}}"
  })

  lifecycle {
    ignore_changes = [ami]
  }
}

data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}
```

### S3 Bucket (Secure)

```hcl
resource "aws_s3_bucket" "{{name}}" {
  bucket = "${local.name_prefix}-{{name}}"

  tags = local.common_tags
}

resource "aws_s3_bucket_versioning" "{{name}}" {
  bucket = aws_s3_bucket.{{name}}.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "{{name}}" {
  bucket = aws_s3_bucket.{{name}}.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = var.kms_key_id
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "{{name}}" {
  bucket = aws_s3_bucket.{{name}}.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "{{name}}" {
  bucket = aws_s3_bucket.{{name}}.id

  rule {
    id     = "transition-to-ia"
    status = "Enabled"

    transition {
      days          = 90
      storage_class = "STANDARD_IA"
    }

    noncurrent_version_transition {
      noncurrent_days = 30
      storage_class   = "STANDARD_IA"
    }

    noncurrent_version_expiration {
      noncurrent_days = 90
    }
  }
}
```

### Security Group

```hcl
resource "aws_security_group" "{{name}}" {
  name        = "${local.name_prefix}-{{name}}-sg"
  description = "Security group for {{name}}"
  vpc_id      = var.vpc_id

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-{{name}}-sg"
  })

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_security_group_rule" "{{name}}_ingress" {
  for_each = var.ingress_rules

  type              = "ingress"
  security_group_id = aws_security_group.{{name}}.id

  from_port         = each.value.from_port
  to_port           = each.value.to_port
  protocol          = each.value.protocol
  cidr_blocks       = each.value.cidr_blocks
  description       = each.value.description
}

resource "aws_security_group_rule" "{{name}}_egress" {
  type              = "egress"
  security_group_id = aws_security_group.{{name}}.id

  from_port   = 0
  to_port     = 0
  protocol    = "-1"
  cidr_blocks = ["0.0.0.0/0"]
  description = "Allow all outbound traffic"
}
```

### IAM Role with Policy

```hcl
resource "aws_iam_role" "{{name}}" {
  name = "${local.name_prefix}-{{name}}-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "{{service}}.amazonaws.com"
      }
    }]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy" "{{name}}" {
  name = "${local.name_prefix}-{{name}}-policy"
  role = aws_iam_role.{{name}}.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          # Minimum required permissions
        ]
        Resource = [
          # Specific resource ARNs
        ]
      }
    ]
  })
}

resource "aws_iam_instance_profile" "{{name}}" {
  name = "${local.name_prefix}-{{name}}-profile"
  role = aws_iam_role.{{name}}.name
}
```

## Security Defaults

| Setting | Default | Reason |
|---------|---------|--------|
| Encryption | Enabled | Data protection |
| Public access | Blocked | Security |
| IMDSv2 | Required | Credential protection |
| Versioning | Enabled | Data recovery |
| Logging | Enabled | Audit trail |

## Commands

```bash
# Generate EC2 resource
/tf:resource ec2 --name web-server

# Generate S3 bucket
/tf:resource s3 --name artifacts --encryption kms

# Generate with full options
/tf:resource rds --name database --engine postgres --multi-az
```
