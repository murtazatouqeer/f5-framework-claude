# Terraform State Management

## Overview

Terraform state tracks the mapping between your configuration and the real-world resources it manages. Proper state management is critical for team collaboration and infrastructure safety.

## State File Basics

### What State Contains

```json
{
  "version": 4,
  "terraform_version": "1.6.0",
  "serial": 42,
  "lineage": "unique-uuid",
  "outputs": {},
  "resources": [
    {
      "mode": "managed",
      "type": "aws_instance",
      "name": "web",
      "provider": "provider[\"registry.terraform.io/hashicorp/aws\"]",
      "instances": [
        {
          "schema_version": 1,
          "attributes": {
            "id": "i-1234567890abcdef0",
            "ami": "ami-0123456789",
            "instance_type": "t3.micro"
          }
        }
      ]
    }
  ]
}
```

### State File Location

```bash
# Default: local state file
terraform.tfstate

# State backup
terraform.tfstate.backup

# State in specific directory
TF_DATA_DIR=./state terraform init
```

## Remote State Backends

### S3 Backend (AWS)

```hcl
terraform {
  backend "s3" {
    bucket         = "company-terraform-state"
    key            = "project/environment/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"

    # Optional: assume role for cross-account
    role_arn = "arn:aws:iam::123456789012:role/TerraformRole"
  }
}
```

### GCS Backend (GCP)

```hcl
terraform {
  backend "gcs" {
    bucket = "company-terraform-state"
    prefix = "project/environment"
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

# Or with tags for multiple workspaces
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
  }
}
```

## State Locking

### DynamoDB Lock Table (AWS)

```hcl
# Create lock table
resource "aws_dynamodb_table" "terraform_locks" {
  name         = "terraform-locks"
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
```

### Lock Behavior

```bash
# Force unlock (use with caution!)
terraform force-unlock LOCK_ID

# Disable locking for specific command
terraform apply -lock=false

# Set lock timeout
terraform apply -lock-timeout=10m
```

## State Commands

### Listing Resources

```bash
# List all resources
terraform state list

# Filter resources
terraform state list aws_instance.*
terraform state list module.vpc.*
```

### Showing Resource Details

```bash
# Show specific resource
terraform state show aws_instance.web

# Show all state
terraform show

# Show state in JSON
terraform show -json
```

### Moving Resources

```bash
# Rename resource
terraform state mv aws_instance.web aws_instance.web_server

# Move to module
terraform state mv aws_instance.web module.compute.aws_instance.web

# Move between state files
terraform state mv -state=source.tfstate -state-out=dest.tfstate \
  aws_instance.web aws_instance.web
```

### Removing Resources

```bash
# Remove from state (doesn't destroy)
terraform state rm aws_instance.web

# Remove module
terraform state rm module.old_module
```

### Importing Resources

```bash
# Import existing resource
terraform import aws_instance.web i-1234567890abcdef0

# Import with specific provider
terraform import -provider=aws.west aws_instance.web i-0987654321

# Import to module
terraform import module.vpc.aws_vpc.main vpc-1234567890
```

## State Migration

### Local to Remote

```bash
# 1. Add backend configuration
cat >> backend.tf << 'EOF'
terraform {
  backend "s3" {
    bucket         = "company-terraform-state"
    key            = "project/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
EOF

# 2. Initialize with migration
terraform init -migrate-state
```

### Between Remote Backends

```bash
# 1. Pull current state
terraform state pull > terraform.tfstate.backup

# 2. Update backend configuration
# Edit backend.tf with new configuration

# 3. Reinitialize with migration
terraform init -migrate-state -force-copy
```

### Using State Push/Pull

```bash
# Pull state to local file
terraform state pull > state.json

# Push state from local file (dangerous!)
terraform state push state.json

# Push with force (very dangerous!)
terraform state push -force state.json
```

## Remote State Data Source

### Reading State from Another Configuration

```hcl
# Read VPC state from another Terraform configuration
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
  subnet_id = data.terraform_remote_state.vpc.outputs.public_subnet_ids[0]

  vpc_security_group_ids = [
    data.terraform_remote_state.vpc.outputs.web_security_group_id
  ]
}
```

### Cross-Region State Access

```hcl
data "terraform_remote_state" "east" {
  backend = "s3"

  config = {
    bucket = "terraform-state-us-east-1"
    key    = "terraform.tfstate"
    region = "us-east-1"
  }
}

data "terraform_remote_state" "west" {
  backend = "s3"

  config = {
    bucket = "terraform-state-us-west-2"
    key    = "terraform.tfstate"
    region = "us-west-2"
  }
}
```

## Workspaces

### Basic Workspace Commands

```bash
# List workspaces
terraform workspace list

# Create new workspace
terraform workspace new staging

# Select workspace
terraform workspace select production

# Show current workspace
terraform workspace show

# Delete workspace
terraform workspace delete staging
```

### Workspace-Aware Configuration

```hcl
locals {
  environment = terraform.workspace

  # Environment-specific settings
  config = {
    default = {
      instance_type = "t3.micro"
      instance_count = 1
    }
    staging = {
      instance_type = "t3.small"
      instance_count = 2
    }
    production = {
      instance_type = "t3.large"
      instance_count = 3
    }
  }

  current = local.config[local.environment]
}

resource "aws_instance" "web" {
  count         = local.current.instance_count
  instance_type = local.current.instance_type

  tags = {
    Environment = local.environment
  }
}
```

### Workspace with Remote Backend

```hcl
terraform {
  backend "s3" {
    bucket         = "company-terraform-state"
    key            = "project/terraform.tfstate"
    region         = "us-east-1"

    # Workspace prefix in S3
    workspace_key_prefix = "workspaces"
  }
}

# Results in:
# workspaces/default/project/terraform.tfstate
# workspaces/staging/project/terraform.tfstate
# workspaces/production/project/terraform.tfstate
```

## State Security

### Encryption at Rest

```hcl
# S3 with KMS encryption
terraform {
  backend "s3" {
    bucket         = "company-terraform-state"
    key            = "terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    kms_key_id     = "arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012"
    dynamodb_table = "terraform-locks"
  }
}
```

### Access Control

```hcl
# IAM policy for state access
resource "aws_iam_policy" "terraform_state" {
  name = "TerraformStateAccess"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = "arn:aws:s3:::company-terraform-state"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = "arn:aws:s3:::company-terraform-state/*"
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:DeleteItem"
        ]
        Resource = "arn:aws:dynamodb:us-east-1:*:table/terraform-locks"
      }
    ]
  })
}
```

### Sensitive Values in State

```hcl
# Mark outputs as sensitive
output "db_password" {
  value     = random_password.db.result
  sensitive = true
}

# Sensitive variables
variable "api_key" {
  type      = string
  sensitive = true
}
```

## State Recovery

### From Backup

```bash
# Check for backup
ls -la terraform.tfstate.backup

# Restore from backup
cp terraform.tfstate.backup terraform.tfstate
terraform refresh
```

### From S3 Versioning

```bash
# List versions
aws s3api list-object-versions \
  --bucket company-terraform-state \
  --prefix project/terraform.tfstate

# Restore specific version
aws s3api get-object \
  --bucket company-terraform-state \
  --key project/terraform.tfstate \
  --version-id VERSION_ID \
  terraform.tfstate.recovered
```

## Best Practices

1. **Remote State**: Always use remote state for team projects
2. **State Locking**: Enable state locking to prevent concurrent modifications
3. **Encryption**: Enable encryption for state at rest
4. **Versioning**: Enable bucket versioning for state file recovery
5. **Access Control**: Restrict access to state files
6. **Sensitive Data**: Be aware that state contains sensitive data
7. **Regular Backups**: Maintain state file backups
8. **Workspace Strategy**: Use workspaces or separate state files per environment
9. **State Hygiene**: Regularly clean up unused resources from state
10. **CI/CD Integration**: Automate state management in pipelines
