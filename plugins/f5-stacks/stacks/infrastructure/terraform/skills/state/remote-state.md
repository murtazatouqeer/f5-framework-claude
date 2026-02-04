# Remote State

## Overview

Remote state stores Terraform state in a shared location, enabling team collaboration, state locking, and secure state management.

## Backend Types

### S3 Backend (AWS)

```hcl
terraform {
  backend "s3" {
    bucket         = "company-terraform-state"
    key            = "project/environment/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"

    # Optional: KMS encryption
    kms_key_id = "arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012"

    # Optional: Assume role
    role_arn = "arn:aws:iam::123456789012:role/TerraformStateRole"
  }
}
```

### GCS Backend (Google Cloud)

```hcl
terraform {
  backend "gcs" {
    bucket = "company-terraform-state"
    prefix = "project/environment"

    # Optional: Credentials
    credentials = "path/to/service-account.json"
  }
}
```

### Azure Blob Backend

```hcl
terraform {
  backend "azurerm" {
    resource_group_name  = "terraform-state-rg"
    storage_account_name = "companyterraformstate"
    container_name       = "tfstate"
    key                  = "project/environment/terraform.tfstate"

    # Optional: Access key
    access_key = var.storage_access_key

    # Optional: SAS token
    sas_token = var.storage_sas_token
  }
}
```

### Terraform Cloud Backend

```hcl
terraform {
  cloud {
    organization = "my-company"

    workspaces {
      name = "my-workspace"
    }
  }
}

# Or with workspace tags
terraform {
  cloud {
    organization = "my-company"

    workspaces {
      tags = ["app:web", "env:prod"]
    }
  }
}
```

### HTTP Backend

```hcl
terraform {
  backend "http" {
    address        = "https://terraform-state.example.com/state"
    lock_address   = "https://terraform-state.example.com/lock"
    unlock_address = "https://terraform-state.example.com/unlock"
    username       = "terraform"
    password       = var.state_password

    # Optional: Custom headers
    skip_cert_verification = false
  }
}
```

### Consul Backend

```hcl
terraform {
  backend "consul" {
    address = "consul.example.com:8500"
    scheme  = "https"
    path    = "terraform/state/project"

    # Optional: Authentication
    access_token = var.consul_token
  }
}
```

## S3 Backend Infrastructure

### Bootstrap Resources

```hcl
# bootstrap/main.tf - Create backend resources
provider "aws" {
  region = var.region
}

# S3 Bucket
resource "aws_s3_bucket" "terraform_state" {
  bucket = "${var.company}-terraform-state"

  tags = {
    Name      = "Terraform State"
    ManagedBy = "terraform-bootstrap"
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

    noncurrent_version_expiration {
      noncurrent_days = 90
    }
  }
}

# KMS Key
resource "aws_kms_key" "terraform_state" {
  description             = "KMS key for Terraform state encryption"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  tags = {
    Name = "terraform-state-key"
  }
}

resource "aws_kms_alias" "terraform_state" {
  name          = "alias/terraform-state"
  target_key_id = aws_kms_key.terraform_state.key_id
}

# DynamoDB Table for Locking
resource "aws_dynamodb_table" "terraform_locks" {
  name         = "${var.company}-terraform-locks"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = {
    Name = "Terraform State Locks"
  }
}

# Outputs
output "state_bucket" {
  value = aws_s3_bucket.terraform_state.id
}

output "lock_table" {
  value = aws_dynamodb_table.terraform_locks.name
}

output "kms_key_arn" {
  value = aws_kms_key.terraform_state.arn
}
```

### IAM Policy for State Access

```hcl
resource "aws_iam_policy" "terraform_state" {
  name        = "TerraformStateAccess"
  description = "Policy for Terraform state management"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "S3BucketAccess"
        Effect = "Allow"
        Action = [
          "s3:ListBucket",
          "s3:GetBucketVersioning",
          "s3:GetBucketLocation"
        ]
        Resource = aws_s3_bucket.terraform_state.arn
      },
      {
        Sid    = "S3ObjectAccess"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = "${aws_s3_bucket.terraform_state.arn}/*"
      },
      {
        Sid    = "DynamoDBAccess"
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:DeleteItem"
        ]
        Resource = aws_dynamodb_table.terraform_locks.arn
      },
      {
        Sid    = "KMSAccess"
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
}
```

## Remote State Data Source

### Reading from Another Configuration

```hcl
# Read VPC state from network team
data "terraform_remote_state" "vpc" {
  backend = "s3"

  config = {
    bucket = "company-terraform-state"
    key    = "network/vpc/terraform.tfstate"
    region = "us-east-1"
  }
}

# Use outputs from remote state
resource "aws_instance" "web" {
  subnet_id              = data.terraform_remote_state.vpc.outputs.public_subnet_ids[0]
  vpc_security_group_ids = [data.terraform_remote_state.vpc.outputs.web_sg_id]
}

module "app" {
  source = "./modules/app"

  vpc_id     = data.terraform_remote_state.vpc.outputs.vpc_id
  subnet_ids = data.terraform_remote_state.vpc.outputs.private_subnet_ids
}
```

### Cross-Account State Access

```hcl
# State in different AWS account
data "terraform_remote_state" "shared_services" {
  backend = "s3"

  config = {
    bucket   = "shared-terraform-state"
    key      = "services/terraform.tfstate"
    region   = "us-east-1"
    role_arn = "arn:aws:iam::SHARED_ACCOUNT:role/TerraformStateReader"
  }
}
```

### Multiple Remote States

```hcl
data "terraform_remote_state" "network" {
  backend = "s3"
  config = {
    bucket = "terraform-state"
    key    = "network/terraform.tfstate"
    region = "us-east-1"
  }
}

data "terraform_remote_state" "security" {
  backend = "s3"
  config = {
    bucket = "terraform-state"
    key    = "security/terraform.tfstate"
    region = "us-east-1"
  }
}

data "terraform_remote_state" "database" {
  backend = "s3"
  config = {
    bucket = "terraform-state"
    key    = "database/terraform.tfstate"
    region = "us-east-1"
  }
}

# Use all remote states
module "application" {
  source = "./modules/application"

  vpc_id            = data.terraform_remote_state.network.outputs.vpc_id
  security_group_id = data.terraform_remote_state.security.outputs.app_sg_id
  database_endpoint = data.terraform_remote_state.database.outputs.endpoint
}
```

## Backend Configuration Variables

### Partial Configuration

```hcl
# backend.tf - Partial configuration
terraform {
  backend "s3" {
    # Values provided at init time
  }
}
```

```bash
# Provide configuration at init
terraform init \
  -backend-config="bucket=company-terraform-state" \
  -backend-config="key=project/terraform.tfstate" \
  -backend-config="region=us-east-1" \
  -backend-config="dynamodb_table=terraform-locks"
```

### Backend Config File

```hcl
# backend.hcl
bucket         = "company-terraform-state"
key            = "project/terraform.tfstate"
region         = "us-east-1"
encrypt        = true
dynamodb_table = "terraform-locks"
```

```bash
terraform init -backend-config=backend.hcl
```

### Environment-Specific Backends

```bash
# Different backends per environment
terraform init -backend-config=backends/dev.hcl
terraform init -backend-config=backends/prod.hcl
```

## State Organization Patterns

### By Environment

```
terraform-state/
├── dev/
│   ├── network/terraform.tfstate
│   ├── database/terraform.tfstate
│   └── application/terraform.tfstate
├── staging/
│   └── ...
└── prod/
    └── ...
```

### By Team/Domain

```
terraform-state/
├── network-team/
│   ├── vpc/terraform.tfstate
│   └── dns/terraform.tfstate
├── platform-team/
│   ├── eks/terraform.tfstate
│   └── monitoring/terraform.tfstate
└── app-team/
    └── services/terraform.tfstate
```

### Hybrid Approach

```
terraform-state/
├── global/
│   ├── iam/terraform.tfstate
│   └── route53/terraform.tfstate
├── us-east-1/
│   ├── dev/
│   ├── staging/
│   └── prod/
└── eu-west-1/
    └── ...
```

## State Security

### Encryption at Rest

```hcl
# S3 with KMS
terraform {
  backend "s3" {
    encrypt    = true
    kms_key_id = "arn:aws:kms:us-east-1:123456789012:key/..."
  }
}
```

### Access Control

```hcl
# S3 bucket policy
resource "aws_s3_bucket_policy" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "DenyUnencryptedTransport"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:*"
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
```

### Audit Logging

```hcl
# Enable S3 access logging
resource "aws_s3_bucket_logging" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  target_bucket = aws_s3_bucket.logs.id
  target_prefix = "terraform-state-logs/"
}
```

## State Commands

```bash
# Show current state
terraform show

# List resources
terraform state list

# Show specific resource
terraform state show aws_instance.web

# Pull state to local
terraform state pull > state.json

# Push state (dangerous!)
terraform state push state.json

# Refresh state
terraform refresh
terraform apply -refresh-only
```

## Best Practices

1. **Always Use Remote State**: For team projects and CI/CD
2. **Enable Encryption**: Encrypt state at rest and in transit
3. **Enable Versioning**: Use S3 versioning for state recovery
4. **Enable Locking**: Prevent concurrent modifications
5. **Restrict Access**: Use IAM policies for state access control
6. **Separate Environments**: Use different state files per environment
7. **Audit Access**: Enable logging for state bucket access
8. **Regular Backups**: Verify versioning and backup procedures
9. **Documentation**: Document state organization and access
10. **State Hygiene**: Regularly clean up unused resources
