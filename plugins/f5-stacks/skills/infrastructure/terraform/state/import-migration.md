# Import and Migration

## Overview

Importing existing resources and migrating state are essential skills for adopting Terraform with existing infrastructure and reorganizing Terraform configurations.

## Resource Import

### Import Command (Legacy)

```bash
# Basic syntax
terraform import <resource_address> <resource_id>

# Examples
terraform import aws_instance.web i-1234567890abcdef0
terraform import aws_vpc.main vpc-abc123
terraform import aws_s3_bucket.data my-bucket-name
```

### Import Workflow

```bash
# 1. Write resource configuration (empty or partial)
cat >> main.tf << 'EOF'
resource "aws_instance" "web" {
  # Configuration will be filled after import
}
EOF

# 2. Import the resource
terraform import aws_instance.web i-1234567890abcdef0

# 3. View imported state
terraform state show aws_instance.web

# 4. Update configuration to match state
# Copy attributes from state show output

# 5. Verify no changes
terraform plan
# Should show: No changes. Infrastructure is up-to-date.
```

### Import Block (Terraform 1.5+)

```hcl
# imports.tf
import {
  to = aws_instance.web
  id = "i-1234567890abcdef0"
}

import {
  to = aws_vpc.main
  id = "vpc-abc123def456"
}

import {
  to = aws_s3_bucket.data
  id = "my-bucket-name"
}

# Run import
terraform plan -generate-config-out=generated.tf
terraform apply
```

### Generate Configuration

```bash
# Terraform 1.5+ can generate configuration
terraform plan -generate-config-out=generated.tf

# Review generated configuration
cat generated.tf

# Move to appropriate file
mv generated.tf main.tf
```

## Common Import Examples

### AWS Resources

```bash
# EC2 Instance
terraform import aws_instance.web i-1234567890abcdef0

# VPC
terraform import aws_vpc.main vpc-abc123

# Subnet
terraform import aws_subnet.public subnet-abc123

# Security Group
terraform import aws_security_group.web sg-abc123

# S3 Bucket
terraform import aws_s3_bucket.data bucket-name

# RDS Instance
terraform import aws_db_instance.main mydb

# IAM Role
terraform import aws_iam_role.app role-name

# IAM Policy
terraform import aws_iam_policy.custom arn:aws:iam::123456789012:policy/policy-name

# Route 53 Record
terraform import aws_route53_record.www Z123456789_example.com_A

# EKS Cluster
terraform import aws_eks_cluster.main cluster-name

# Lambda Function
terraform import aws_lambda_function.main function-name
```

### Module Import

```bash
# Import into module
terraform import module.vpc.aws_vpc.main vpc-abc123
terraform import module.eks.aws_eks_cluster.main cluster-name
terraform import 'module.instances["web"].aws_instance.main' i-abc123
```

### Import with for_each

```bash
# Import into for_each resource
terraform import 'aws_instance.servers["web"]' i-abc123
terraform import 'aws_subnet.private["us-east-1a"]' subnet-abc123
```

## State Migration

### Local to Remote

```bash
# 1. Backup local state
cp terraform.tfstate terraform.tfstate.backup

# 2. Add backend configuration
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

# 3. Initialize with migration
terraform init -migrate-state

# 4. Verify migration
terraform state list
terraform plan
```

### Between S3 Buckets

```bash
# 1. Pull current state
terraform state pull > backup.tfstate

# 2. Update backend configuration
# Edit backend.tf with new bucket

# 3. Reinitialize with force copy
terraform init -migrate-state -force-copy

# 4. Verify
terraform plan
```

### Backend to Backend

```hcl
# Old backend
terraform {
  backend "s3" {
    bucket = "old-bucket"
    key    = "project/terraform.tfstate"
    region = "us-east-1"
  }
}

# New backend (update the configuration)
terraform {
  backend "s3" {
    bucket = "new-bucket"
    key    = "project/v2/terraform.tfstate"
    region = "us-east-1"
  }
}
```

```bash
terraform init -migrate-state
```

## State Manipulation

### Move Resources

```bash
# Rename resource
terraform state mv aws_instance.web aws_instance.web_server

# Move to module
terraform state mv aws_instance.web module.compute.aws_instance.web

# Move from module
terraform state mv module.compute.aws_instance.web aws_instance.web

# Move between modules
terraform state mv module.old.aws_vpc.main module.new.aws_vpc.main
```

### Move Block (Terraform 1.1+)

```hcl
# moved.tf
moved {
  from = aws_instance.web
  to   = aws_instance.web_server
}

moved {
  from = aws_instance.app
  to   = module.compute.aws_instance.app
}

moved {
  from = module.old_vpc.aws_vpc.main
  to   = module.vpc.aws_vpc.main
}
```

```bash
# Apply moves
terraform apply
# Terraform will update state without recreating resources
```

### Remove from State

```bash
# Remove resource (doesn't destroy actual resource)
terraform state rm aws_instance.old

# Remove module
terraform state rm module.deprecated

# Remove specific instance
terraform state rm 'aws_instance.web[0]'
terraform state rm 'aws_instance.servers["old"]'
```

### Removed Block (Terraform 1.7+)

```hcl
# removed.tf
removed {
  from = aws_instance.old

  lifecycle {
    destroy = false  # Keep the actual resource
  }
}
```

## State Surgery

### Pull and Push

```bash
# Pull state to local file
terraform state pull > state.json

# Edit state (be very careful!)
# Use jq or editor to modify state.json

# Push modified state back
terraform state push state.json

# Force push (dangerous!)
terraform state push -force state.json
```

### Manual State Editing

```bash
# Export state
terraform state pull > state.json

# Edit with jq (example: update resource attribute)
jq '.resources[] | select(.type == "aws_instance" and .name == "web") | .instances[0].attributes.tags.Name = "new-name"' state.json > new_state.json

# Verify and push
terraform state push new_state.json
```

## Bulk Import

### Import Script

```bash
#!/bin/bash
# bulk-import.sh

# Read from CSV: resource_type,resource_name,resource_id
while IFS=, read -r type name id; do
  echo "Importing ${type}.${name} = ${id}"
  terraform import "${type}.${name}" "${id}"
done < resources.csv
```

```csv
# resources.csv
aws_instance,web,i-abc123
aws_instance,api,i-def456
aws_vpc,main,vpc-123456
aws_subnet,public_a,subnet-aaa
aws_subnet,public_b,subnet-bbb
```

### Import with Terraformer

```bash
# Install terraformer
brew install terraformer

# Import all resources from AWS
terraformer import aws --resources=vpc,subnet,security_group --regions=us-east-1

# Import specific resources
terraformer import aws \
  --resources=ec2_instance \
  --filter="Name=tags.Environment;Value=production"

# Generated files in ./generated/aws/
```

### Import with Former2

```bash
# Browser-based import tool
# https://former2.com

# Generates CloudFormation or Terraform
# Copy resources from AWS console
```

## Migration Strategies

### Incremental Migration

```bash
# 1. Start with non-critical resources
terraform import aws_s3_bucket.logs logs-bucket

# 2. Verify and refine
terraform plan

# 3. Gradually add more resources
terraform import aws_vpc.main vpc-123

# 4. Build up complete configuration
```

### Big Bang Migration

```bash
# 1. Export all resources
terraformer import aws --resources=* --regions=us-east-1

# 2. Review generated configuration
# 3. Customize and organize
# 4. Import all at once
```

### Parallel Migration

```hcl
# Run old and new infrastructure in parallel
# Gradually shift traffic
# Delete old resources after migration

resource "aws_instance" "web_new" {
  # New configuration
}

# moved block when ready
moved {
  from = aws_instance.web_old
  to   = aws_instance.web
}
```

## Common Migration Scenarios

### Module Refactoring

```hcl
# Before: Flat structure
resource "aws_vpc" "main" {}
resource "aws_subnet" "public" {}

# After: Module structure
module "network" {
  source = "./modules/network"
}

# Migration
moved {
  from = aws_vpc.main
  to   = module.network.aws_vpc.main
}

moved {
  from = aws_subnet.public
  to   = module.network.aws_subnet.public
}
```

### Count to for_each

```hcl
# Before: count
resource "aws_instance" "web" {
  count = 3
}

# After: for_each
resource "aws_instance" "web" {
  for_each = toset(["web-1", "web-2", "web-3"])
}

# Migration (manual state mv)
terraform state mv 'aws_instance.web[0]' 'aws_instance.web["web-1"]'
terraform state mv 'aws_instance.web[1]' 'aws_instance.web["web-2"]'
terraform state mv 'aws_instance.web[2]' 'aws_instance.web["web-3"]'
```

### Splitting State

```bash
# Original state has too many resources
# Split into multiple states

# 1. Pull original state
terraform state pull > full_state.json

# 2. Create new configuration for network
cd network/
terraform init

# 3. Move resources to new state
terraform state mv -state=../full_state.json -state-out=terraform.tfstate \
  aws_vpc.main aws_vpc.main
terraform state mv -state=../full_state.json -state-out=terraform.tfstate \
  aws_subnet.public aws_subnet.public

# 4. Repeat for other components
```

## Best Practices

1. **Backup First**: Always backup state before migration
2. **Plan Before Import**: Write configuration before importing
3. **Use Import Blocks**: Prefer import blocks over command (Terraform 1.5+)
4. **Use Moved Blocks**: Prefer moved blocks over state mv (Terraform 1.1+)
5. **Incremental Changes**: Migrate in small batches
6. **Verify After Each Step**: Run terraform plan after each change
7. **Document Changes**: Record what was imported/migrated
8. **Test in Non-Prod**: Practice migration in non-production first
9. **Use Version Control**: Commit configuration changes incrementally
10. **Clean Up**: Remove moved/import blocks after migration
