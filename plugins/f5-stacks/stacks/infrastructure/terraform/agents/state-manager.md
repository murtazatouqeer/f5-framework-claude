---
name: terraform-state-manager
description: Manage Terraform state operations safely
triggers:
  - "terraform state"
  - "manage tf state"
  - "import resource"
  - "migrate state"
---

# Terraform State Manager Agent

## Purpose

Safely manage Terraform state operations including remote backend setup, state migration, resource imports, and state manipulation.

## Capabilities

1. **Backend Configuration**: Set up remote state backends
2. **State Migration**: Migrate between backends safely
3. **Resource Import**: Import existing resources into state
4. **State Operations**: Move, remove, and taint resources
5. **Workspace Management**: Create and manage workspaces

## Backend Setup

### S3 Backend (AWS)

```hcl
# backend.tf
terraform {
  backend "s3" {
    bucket         = "{{company}}-terraform-state"
    key            = "{{project}}/{{environment}}/terraform.tfstate"
    region         = "{{region}}"
    encrypt        = true
    dynamodb_table = "{{company}}-terraform-locks"

    # Role assumption for cross-account
    # role_arn = "arn:aws:iam::{{account_id}}:role/TerraformStateRole"
  }
}
```

### Bootstrap Backend Infrastructure

```hcl
# bootstrap/main.tf - Run once to create backend resources

provider "aws" {
  region = var.region
}

# S3 Bucket for State
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
      sse_algorithm = "aws:kms"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# DynamoDB Table for State Locking
resource "aws_dynamodb_table" "terraform_locks" {
  name         = "${var.company}-terraform-locks"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = {
    Name      = "Terraform State Locks"
    ManagedBy = "terraform-bootstrap"
  }
}

# IAM Policy for Terraform State Access
resource "aws_iam_policy" "terraform_state" {
  name        = "TerraformStateAccess"
  description = "Policy for Terraform state management"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket",
          "s3:GetBucketVersioning"
        ]
        Resource = aws_s3_bucket.terraform_state.arn
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = "${aws_s3_bucket.terraform_state.arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:DeleteItem"
        ]
        Resource = aws_dynamodb_table.terraform_locks.arn
      }
    ]
  })
}

output "backend_config" {
  value = <<-EOT
    terraform {
      backend "s3" {
        bucket         = "${aws_s3_bucket.terraform_state.id}"
        key            = "PROJECT/ENVIRONMENT/terraform.tfstate"
        region         = "${var.region}"
        encrypt        = true
        dynamodb_table = "${aws_dynamodb_table.terraform_locks.name}"
      }
    }
  EOT
}
```

## State Migration

### Local to Remote

```bash
#!/bin/bash
# migrate-to-s3.sh

# 1. Ensure local state exists
if [ ! -f "terraform.tfstate" ]; then
  echo "No local state found"
  exit 1
fi

# 2. Backup local state
cp terraform.tfstate terraform.tfstate.backup.$(date +%Y%m%d)

# 3. Add backend configuration to backend.tf
cat > backend.tf << 'EOF'
terraform {
  backend "s3" {
    bucket         = "company-terraform-state"
    key            = "project/env/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "company-terraform-locks"
  }
}
EOF

# 4. Initialize with migration
terraform init -migrate-state

# 5. Verify state
terraform state list
```

### Between S3 Buckets

```bash
#!/bin/bash
# migrate-between-buckets.sh

# 1. Pull current state
terraform state pull > terraform.tfstate.backup

# 2. Update backend.tf with new bucket
sed -i 's/old-bucket/new-bucket/g' backend.tf

# 3. Reinitialize with migration
terraform init -migrate-state -force-copy

# 4. Verify
terraform plan
```

## Resource Import

### Import Workflow

```bash
# 1. Write resource configuration first
cat >> main.tf << 'EOF'
resource "aws_vpc" "imported" {
  # Configuration will be filled after import
}
EOF

# 2. Import the resource
terraform import aws_vpc.imported vpc-1234567890abcdef0

# 3. Run plan to see current configuration
terraform plan

# 4. Update configuration to match imported resource
# 5. Run plan again - should show no changes
terraform plan
```

### Bulk Import Script

```bash
#!/bin/bash
# bulk-import.sh

# Import multiple resources from a list
while IFS=, read -r resource_type resource_name resource_id; do
  echo "Importing ${resource_type}.${resource_name} = ${resource_id}"
  terraform import "${resource_type}.${resource_name}" "${resource_id}"
done < resources-to-import.csv
```

### Generate Import Blocks (Terraform 1.5+)

```hcl
# imports.tf
import {
  to = aws_vpc.main
  id = "vpc-1234567890abcdef0"
}

import {
  to = aws_subnet.public[0]
  id = "subnet-0123456789abcdef0"
}

import {
  to = aws_subnet.public[1]
  id = "subnet-0123456789abcdef1"
}
```

```bash
# Generate configuration from imports
terraform plan -generate-config-out=generated.tf
```

## State Operations

### Safe State Commands

```bash
# List all resources
terraform state list

# Show resource details
terraform state show aws_instance.web

# Move resource (rename)
terraform state mv aws_instance.web aws_instance.web_server

# Move to module
terraform state mv aws_instance.web module.compute.aws_instance.web

# Remove from state (does not destroy)
terraform state rm aws_instance.legacy

# Pull state to local file
terraform state pull > state-backup.json

# Push state from local file (dangerous!)
terraform state push state-backup.json
```

### Taint and Replace

```bash
# Mark for recreation (deprecated)
terraform taint aws_instance.web

# Modern approach - use replace
terraform apply -replace="aws_instance.web"

# Plan with replacement
terraform plan -replace="aws_instance.web"
```

## Workspace Management

```bash
# List workspaces
terraform workspace list

# Create workspace
terraform workspace new staging

# Select workspace
terraform workspace select production

# Delete workspace
terraform workspace delete staging

# Show current workspace
terraform workspace show
```

### Workspace-Aware Configuration

```hcl
locals {
  environment = terraform.workspace

  instance_count = {
    default    = 1
    dev        = 1
    staging    = 2
    production = 3
  }
}

resource "aws_instance" "web" {
  count = local.instance_count[local.environment]
  # ...
}
```

## Safety Checklist

1. ✅ **Backup state** before any operation
2. ✅ **Lock state** during operations
3. ✅ **Test in dev** before production
4. ✅ **Review plan** after state changes
5. ✅ **Document changes** for audit trail

## Commands

```bash
# Set up S3 backend
/tf:state setup-backend --provider aws --bucket my-state

# Import existing resource
/tf:state import --type aws_vpc --id vpc-123

# Migrate state
/tf:state migrate --from local --to s3

# Backup state
/tf:state backup --output backup.tfstate
```
