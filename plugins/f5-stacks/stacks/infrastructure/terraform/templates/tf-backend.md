---
name: tf-backend
description: Template for Terraform remote backend configuration
applies_to: terraform
---

# Terraform Backend Template

## Overview

Configure Terraform remote state storage with S3/DynamoDB for AWS,
GCS for GCP, or Terraform Cloud for multi-cloud environments.

## AWS S3 Backend

### Backend Configuration

```hcl
# backend.tf
terraform {
  backend "s3" {
    bucket         = "{{company}}-terraform-state"
    key            = "{{project}}/{{environment}}/terraform.tfstate"
    region         = "{{region}}"
    encrypt        = true
    dynamodb_table = "{{company}}-terraform-locks"

    # Optional: Assume role for cross-account
    # role_arn     = "arn:aws:iam::{{account_id}}:role/TerraformRole"

    # Optional: Use specific profile
    # profile      = "terraform"
  }
}
```

### Bootstrap Module

```hcl
# modules/terraform-backend/main.tf

variable "company" {
  description = "Company name for resource naming"
  type        = string
}

variable "region" {
  description = "AWS region"
  type        = string
}

variable "tags" {
  description = "Tags for resources"
  type        = map(string)
  default     = {}
}

locals {
  bucket_name = "${var.company}-terraform-state"
  table_name  = "${var.company}-terraform-locks"

  common_tags = merge(var.tags, {
    Purpose   = "terraform-state"
    ManagedBy = "terraform"
  })
}

# =============================================================================
# S3 Bucket
# =============================================================================

resource "aws_s3_bucket" "terraform_state" {
  bucket = local.bucket_name

  tags = merge(local.common_tags, {
    Name = local.bucket_name
  })

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.terraform_state.arn
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    id     = "cleanup-old-versions"
    status = "Enabled"

    noncurrent_version_transition {
      noncurrent_days = 30
      storage_class   = "STANDARD_IA"
    }

    noncurrent_version_transition {
      noncurrent_days = 90
      storage_class   = "GLACIER"
    }

    noncurrent_version_expiration {
      noncurrent_days = 365
    }
  }
}

# =============================================================================
# KMS Key
# =============================================================================

resource "aws_kms_key" "terraform_state" {
  description             = "KMS key for Terraform state encryption"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  tags = local.common_tags
}

resource "aws_kms_alias" "terraform_state" {
  name          = "alias/terraform-state"
  target_key_id = aws_kms_key.terraform_state.key_id
}

# =============================================================================
# DynamoDB Table
# =============================================================================

resource "aws_dynamodb_table" "terraform_locks" {
  name         = local.table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.terraform_state.arn
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = merge(local.common_tags, {
    Name = local.table_name
  })

  lifecycle {
    prevent_destroy = true
  }
}

# =============================================================================
# IAM Policy for Terraform
# =============================================================================

resource "aws_iam_policy" "terraform_state" {
  name        = "${var.company}-terraform-state-policy"
  description = "Policy for Terraform state management"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "S3StateAccess"
        Effect = "Allow"
        Action = [
          "s3:ListBucket",
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = [
          aws_s3_bucket.terraform_state.arn,
          "${aws_s3_bucket.terraform_state.arn}/*"
        ]
      },
      {
        Sid    = "DynamoDBLocking"
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:DeleteItem"
        ]
        Resource = aws_dynamodb_table.terraform_locks.arn
      },
      {
        Sid    = "KMSEncryption"
        Effect = "Allow"
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:GenerateDataKey"
        ]
        Resource = aws_kms_key.terraform_state.arn
      }
    ]
  })

  tags = local.common_tags
}

# =============================================================================
# Outputs
# =============================================================================

output "bucket_name" {
  description = "S3 bucket name for Terraform state"
  value       = aws_s3_bucket.terraform_state.id
}

output "bucket_arn" {
  description = "S3 bucket ARN"
  value       = aws_s3_bucket.terraform_state.arn
}

output "dynamodb_table_name" {
  description = "DynamoDB table name for state locking"
  value       = aws_dynamodb_table.terraform_locks.name
}

output "kms_key_arn" {
  description = "KMS key ARN for encryption"
  value       = aws_kms_key.terraform_state.arn
}

output "policy_arn" {
  description = "IAM policy ARN for Terraform access"
  value       = aws_iam_policy.terraform_state.arn
}

output "backend_config" {
  description = "Backend configuration snippet"
  value       = <<-EOT
    terraform {
      backend "s3" {
        bucket         = "${aws_s3_bucket.terraform_state.id}"
        key            = "<project>/<environment>/terraform.tfstate"
        region         = "${var.region}"
        encrypt        = true
        dynamodb_table = "${aws_dynamodb_table.terraform_locks.name}"
      }
    }
  EOT
}
```

## Bootstrap Script

```bash
#!/bin/bash
# bootstrap-backend.sh

set -e

COMPANY="${1:-mycompany}"
REGION="${2:-us-east-1}"

BUCKET_NAME="${COMPANY}-terraform-state"
TABLE_NAME="${COMPANY}-terraform-locks"

echo "Creating S3 bucket: ${BUCKET_NAME}"
if [ "$REGION" = "us-east-1" ]; then
  aws s3api create-bucket \
    --bucket "$BUCKET_NAME" \
    --region "$REGION"
else
  aws s3api create-bucket \
    --bucket "$BUCKET_NAME" \
    --region "$REGION" \
    --create-bucket-configuration LocationConstraint="$REGION"
fi

echo "Enabling versioning..."
aws s3api put-bucket-versioning \
  --bucket "$BUCKET_NAME" \
  --versioning-configuration Status=Enabled

echo "Enabling encryption..."
aws s3api put-bucket-encryption \
  --bucket "$BUCKET_NAME" \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "aws:kms"
      },
      "BucketKeyEnabled": true
    }]
  }'

echo "Blocking public access..."
aws s3api put-public-access-block \
  --bucket "$BUCKET_NAME" \
  --public-access-block-configuration '{
    "BlockPublicAcls": true,
    "IgnorePublicAcls": true,
    "BlockPublicPolicy": true,
    "RestrictPublicBuckets": true
  }'

echo "Creating DynamoDB table: ${TABLE_NAME}"
aws dynamodb create-table \
  --table-name "$TABLE_NAME" \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region "$REGION"

echo "Enabling point-in-time recovery..."
aws dynamodb update-continuous-backups \
  --table-name "$TABLE_NAME" \
  --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true \
  --region "$REGION"

echo "Bootstrap complete!"
echo ""
echo "Add this to your backend.tf:"
echo ""
cat <<EOF
terraform {
  backend "s3" {
    bucket         = "${BUCKET_NAME}"
    key            = "<project>/<environment>/terraform.tfstate"
    region         = "${REGION}"
    encrypt        = true
    dynamodb_table = "${TABLE_NAME}"
  }
}
EOF
```

## Environment-Specific Configuration

### Directory Structure

```
infrastructure/
├── bootstrap/           # Backend setup (run once)
│   ├── main.tf
│   └── outputs.tf
├── modules/
│   └── ...
└── environments/
    ├── dev/
    │   ├── backend.tf   # Points to dev state
    │   ├── main.tf
    │   └── terraform.tfvars
    ├── staging/
    │   ├── backend.tf   # Points to staging state
    │   ├── main.tf
    │   └── terraform.tfvars
    └── prod/
        ├── backend.tf   # Points to prod state
        ├── main.tf
        └── terraform.tfvars
```

### Environment Backend Files

```hcl
# environments/dev/backend.tf
terraform {
  backend "s3" {
    bucket         = "mycompany-terraform-state"
    key            = "myproject/dev/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "mycompany-terraform-locks"
  }
}

# environments/staging/backend.tf
terraform {
  backend "s3" {
    bucket         = "mycompany-terraform-state"
    key            = "myproject/staging/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "mycompany-terraform-locks"
  }
}

# environments/prod/backend.tf
terraform {
  backend "s3" {
    bucket         = "mycompany-terraform-state"
    key            = "myproject/prod/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "mycompany-terraform-locks"
  }
}
```

## Terraform Cloud Backend

```hcl
terraform {
  cloud {
    organization = "{{organization}}"

    workspaces {
      name = "{{workspace}}"
      # Or use tags for multiple workspaces
      # tags = ["app:myapp"]
    }
  }
}

# Alternative: Remote backend
terraform {
  backend "remote" {
    hostname     = "app.terraform.io"
    organization = "{{organization}}"

    workspaces {
      name = "{{workspace}}"
    }
  }
}
```

## GCS Backend (Google Cloud)

```hcl
terraform {
  backend "gcs" {
    bucket      = "{{company}}-terraform-state"
    prefix      = "{{project}}/{{environment}}"
    credentials = "path/to/credentials.json"
  }
}
```

## Azure Backend

```hcl
terraform {
  backend "azurerm" {
    resource_group_name  = "{{resource_group}}"
    storage_account_name = "{{storage_account}}"
    container_name       = "tfstate"
    key                  = "{{project}}/{{environment}}/terraform.tfstate"
  }
}
```

## State Management Commands

```bash
# List workspaces
terraform workspace list

# Create new workspace
terraform workspace new staging

# Select workspace
terraform workspace select prod

# Show current state
terraform state list

# Move state (refactoring)
terraform state mv aws_instance.old aws_instance.new

# Import existing resource
terraform import aws_instance.example i-1234567890abcdef0

# Remove from state (without destroying)
terraform state rm aws_instance.example

# Pull remote state locally
terraform state pull > terraform.tfstate

# Push local state to remote
terraform state push terraform.tfstate
```

## Best Practices

1. **Single Backend Per Project**: One state file per environment
2. **Encryption**: Always enable encryption at rest
3. **Locking**: Use DynamoDB/similar for concurrent access
4. **Versioning**: Enable bucket versioning for recovery
5. **Access Control**: Restrict who can modify state
6. **Backup**: Regular backups of state files
7. **No Sensitive Data**: Don't store secrets in state
8. **Separate Bootstrap**: Bootstrap backend infra separately
