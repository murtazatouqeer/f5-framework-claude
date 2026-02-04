# State Locking

## Overview

State locking prevents concurrent operations that could corrupt Terraform state. When enabled, Terraform acquires a lock before modifying state and releases it when the operation completes.

## How Locking Works

```
User A: terraform apply
  1. Acquire lock
  2. Read state
  3. Plan changes
  4. Apply changes
  5. Write state
  6. Release lock

User B: terraform apply (concurrent)
  1. Attempt to acquire lock
  2. Lock is held by User A
  3. Wait or fail with error
```

## Lock Providers

### DynamoDB (AWS)

```hcl
terraform {
  backend "s3" {
    bucket         = "company-terraform-state"
    key            = "project/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"  # Enables locking
  }
}
```

#### DynamoDB Table Creation

```hcl
resource "aws_dynamodb_table" "terraform_locks" {
  name         = "terraform-locks"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  # Optional: Point-in-time recovery
  point_in_time_recovery {
    enabled = true
  }

  # Optional: Server-side encryption
  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.dynamodb.arn
  }

  tags = {
    Name    = "Terraform State Locks"
    Purpose = "State locking for Terraform"
  }
}
```

#### Lock Table IAM Policy

```hcl
resource "aws_iam_policy" "terraform_lock" {
  name = "TerraformLockAccess"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
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
```

### GCS (Google Cloud)

```hcl
# GCS backend includes built-in locking
terraform {
  backend "gcs" {
    bucket = "company-terraform-state"
    prefix = "project"
    # Locking is automatic
  }
}
```

### Azure Blob

```hcl
# Azure Blob backend includes built-in locking
terraform {
  backend "azurerm" {
    resource_group_name  = "terraform-state-rg"
    storage_account_name = "companyterraformstate"
    container_name       = "tfstate"
    key                  = "terraform.tfstate"
    # Locking is automatic via blob leases
  }
}
```

### Terraform Cloud

```hcl
# Terraform Cloud includes built-in locking
terraform {
  cloud {
    organization = "my-company"
    workspaces {
      name = "my-workspace"
    }
    # Locking is automatic
  }
}
```

### Consul

```hcl
terraform {
  backend "consul" {
    address = "consul.example.com:8500"
    scheme  = "https"
    path    = "terraform/state/project"
    lock    = true  # Explicitly enable locking
  }
}
```

## Lock Commands

### Force Unlock

```bash
# View lock error
# Error: Error locking state: Error acquiring the state lock...
# Lock Info:
#   ID:        12345678-1234-1234-1234-123456789012
#   Path:      terraform-state/project/terraform.tfstate
#   Operation: OperationTypePlan
#   Who:       user@hostname
#   Version:   1.6.0
#   Created:   2024-01-15 10:30:00.000000000 +0000 UTC

# Force unlock (use with caution!)
terraform force-unlock 12345678-1234-1234-1234-123456789012
```

### Disable Locking

```bash
# Temporarily disable locking (not recommended)
terraform plan -lock=false
terraform apply -lock=false

# Set lock timeout
terraform apply -lock-timeout=10m
```

## Lock Behavior

### Normal Lock Acquisition

```bash
$ terraform apply

# Output shows lock acquisition
Acquiring state lock. This may take a few moments...
# ... terraform operations ...
Releasing state lock. This may take a few moments...
```

### Lock Conflict

```bash
$ terraform apply

Error: Error locking state: Error acquiring the state lock

Terraform acquires a state lock to protect the state from being written
by multiple users at the same time. Please resolve the issue above and try
again. For most commands, you can disable locking with the "-lock=false"
flag, but this is not recommended.

Lock Info:
  ID:        abc123...
  Path:      s3://bucket/key
  Operation: OperationTypeApply
  Who:       other-user@hostname
  Version:   1.6.0
  Created:   2024-01-15 10:30:00 +0000 UTC
  Info:
```

## DynamoDB Lock Details

### Lock Item Structure

```json
{
  "LockID": {
    "S": "company-terraform-state/project/terraform.tfstate"
  },
  "Info": {
    "S": "{\"ID\":\"abc123\",\"Operation\":\"OperationTypeApply\",\"Info\":\"\",\"Who\":\"user@hostname\",\"Version\":\"1.6.0\",\"Created\":\"2024-01-15T10:30:00.000000Z\",\"Path\":\"company-terraform-state/project/terraform.tfstate\"}"
  },
  "Digest": {
    "S": "md5hash..."
  }
}
```

### Viewing Active Locks

```bash
# AWS CLI to view lock
aws dynamodb get-item \
  --table-name terraform-locks \
  --key '{"LockID":{"S":"company-terraform-state/project/terraform.tfstate"}}' \
  --output json

# List all locks
aws dynamodb scan \
  --table-name terraform-locks \
  --output table
```

### Manual Lock Cleanup

```bash
# Delete stale lock (use with extreme caution!)
aws dynamodb delete-item \
  --table-name terraform-locks \
  --key '{"LockID":{"S":"company-terraform-state/project/terraform.tfstate"}}'
```

## Lock Timeouts

### Configuring Timeouts

```bash
# Wait up to 10 minutes for lock
terraform apply -lock-timeout=10m

# Wait up to 30 seconds
terraform plan -lock-timeout=30s

# Default: 0s (fail immediately if locked)
```

### Timeout Behavior

```bash
$ terraform apply -lock-timeout=5m

Acquiring state lock. This may take a few moments...
Lock Info:
  ID:        abc123...
  ...
Terraform is waiting for the lock to become available...
# Waits up to 5 minutes, then fails if still locked
```

## Handling Lock Issues

### Stale Locks

```bash
# Symptoms of stale lock:
# - Process crashed during operation
# - Network interruption
# - User cancelled operation improperly

# Verify lock is actually stale
# 1. Check who holds the lock
# 2. Confirm they're not running Terraform
# 3. Force unlock

terraform force-unlock LOCK_ID
```

### Preventing Stale Locks

```hcl
# Use graceful shutdown in CI/CD
# Example: GitHub Actions
jobs:
  terraform:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Terraform Apply
        run: terraform apply -auto-approve
        timeout-minutes: 30

      # Lock is released on timeout or cancellation
```

### Lock Recovery Script

```bash
#!/bin/bash
# lock-recovery.sh

LOCK_TABLE="terraform-locks"
STATE_KEY="company-terraform-state/project/terraform.tfstate"

# Check lock status
lock_info=$(aws dynamodb get-item \
  --table-name "$LOCK_TABLE" \
  --key "{\"LockID\":{\"S\":\"$STATE_KEY\"}}" \
  --output json)

if [ -n "$lock_info" ]; then
  echo "Lock found:"
  echo "$lock_info" | jq '.Item.Info.S' | jq -r '.' | jq .

  read -p "Force unlock? (yes/no): " confirm
  if [ "$confirm" == "yes" ]; then
    lock_id=$(echo "$lock_info" | jq -r '.Item.Info.S' | jq -r '.ID')
    terraform force-unlock "$lock_id"
  fi
else
  echo "No lock found"
fi
```

## Multi-Region Locking

### Global Lock Table

```hcl
# Single global lock table
resource "aws_dynamodb_table" "terraform_locks" {
  name         = "terraform-locks-global"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  # Global table for multi-region
  dynamic "replica" {
    for_each = toset(["us-west-2", "eu-west-1"])
    content {
      region_name = replica.value
    }
  }
}
```

### Region-Specific Lock Tables

```hcl
# Separate lock table per region
terraform {
  backend "s3" {
    bucket         = "terraform-state-us-east-1"
    key            = "project/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-locks-us-east-1"
  }
}
```

## Best Practices

1. **Always Enable Locking**: Use locking for all shared state
2. **Never Disable in Production**: -lock=false is dangerous
3. **Use Appropriate Timeouts**: Set reasonable lock-timeout values
4. **Document Lock Table**: Include lock table in documentation
5. **Monitor Lock Table**: Set up alerts for stale locks
6. **Backup Lock Table**: Enable point-in-time recovery
7. **Secure Lock Table**: Apply appropriate IAM policies
8. **CI/CD Graceful Shutdown**: Handle timeouts properly in pipelines
9. **Force Unlock Carefully**: Verify before force unlocking
10. **Use Terraform Cloud**: Built-in locking with run queuing

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Lock timeout | Increase -lock-timeout or check who holds lock |
| Stale lock | Verify process is dead, then force-unlock |
| DynamoDB throttling | Switch to PAY_PER_REQUEST billing |
| Permission denied | Check IAM policy for DynamoDB access |
| Lock not releasing | Check for crashed process, force-unlock if needed |
