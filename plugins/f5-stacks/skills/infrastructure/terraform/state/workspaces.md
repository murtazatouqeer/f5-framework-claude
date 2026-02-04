# Terraform Workspaces

## Overview

Workspaces allow you to manage multiple distinct sets of infrastructure resources from a single configuration. Each workspace has its own state file.

## Basic Commands

```bash
# List workspaces
terraform workspace list

# Current workspace indicator
terraform workspace show

# Create new workspace
terraform workspace new staging

# Select workspace
terraform workspace select production

# Delete workspace
terraform workspace delete staging
```

## Workspace Concepts

### Default Workspace

```bash
# Every Terraform configuration starts with "default" workspace
$ terraform workspace list
* default

# State file location (local)
terraform.tfstate

# State file location (S3)
s3://bucket/key/terraform.tfstate
```

### Multiple Workspaces

```bash
$ terraform workspace new dev
Created and switched to workspace "dev"!

$ terraform workspace new staging
Created and switched to workspace "staging"!

$ terraform workspace new prod
Created and switched to workspace "prod"!

$ terraform workspace list
  default
  dev
* prod
  staging
```

## Workspace-Aware Configuration

### Using terraform.workspace

```hcl
# Access current workspace name
locals {
  environment = terraform.workspace
}

resource "aws_instance" "web" {
  tags = {
    Environment = local.environment
    Name        = "${var.project}-${local.environment}-web"
  }
}
```

### Environment-Specific Settings

```hcl
locals {
  # Map workspace to configuration
  config = {
    default = {
      instance_type  = "t3.micro"
      instance_count = 1
      multi_az       = false
    }
    dev = {
      instance_type  = "t3.micro"
      instance_count = 1
      multi_az       = false
    }
    staging = {
      instance_type  = "t3.small"
      instance_count = 2
      multi_az       = false
    }
    prod = {
      instance_type  = "t3.large"
      instance_count = 3
      multi_az       = true
    }
  }

  # Current workspace config
  current = local.config[terraform.workspace]
}

resource "aws_instance" "web" {
  count         = local.current.instance_count
  instance_type = local.current.instance_type
}

resource "aws_db_instance" "main" {
  multi_az = local.current.multi_az
}
```

### Conditional Resources

```hcl
# Only create in production
resource "aws_waf_web_acl" "main" {
  count = terraform.workspace == "prod" ? 1 : 0

  name = "${var.project}-waf"
}

# Different resources per workspace
resource "aws_instance" "bastion" {
  count = terraform.workspace != "prod" ? 1 : 0

  # Bastion only in non-prod environments
}
```

### Naming Conventions

```hcl
locals {
  name_prefix = "${var.project}-${terraform.workspace}"
}

resource "aws_vpc" "main" {
  tags = {
    Name = "${local.name_prefix}-vpc"
  }
}

resource "aws_s3_bucket" "data" {
  bucket = "${local.name_prefix}-data-${data.aws_caller_identity.current.account_id}"
}
```

## Workspace State Storage

### Local Backend

```
.terraform/
terraform.tfstate.d/
├── dev/
│   └── terraform.tfstate
├── staging/
│   └── terraform.tfstate
└── prod/
    └── terraform.tfstate
```

### S3 Backend

```hcl
terraform {
  backend "s3" {
    bucket               = "company-terraform-state"
    key                  = "project/terraform.tfstate"
    region               = "us-east-1"
    workspace_key_prefix = "workspaces"
    dynamodb_table       = "terraform-locks"
  }
}
```

```
# Resulting S3 paths:
s3://company-terraform-state/workspaces/default/project/terraform.tfstate
s3://company-terraform-state/workspaces/dev/project/terraform.tfstate
s3://company-terraform-state/workspaces/staging/project/terraform.tfstate
s3://company-terraform-state/workspaces/prod/project/terraform.tfstate
```

### Terraform Cloud

```hcl
terraform {
  cloud {
    organization = "my-company"

    workspaces {
      tags = ["project:myapp"]
    }
  }
}
```

## Workspace Variables

### Workspace-Specific tfvars

```
project/
├── main.tf
├── variables.tf
├── terraform.tfvars       # Common values
└── workspaces/
    ├── dev.tfvars
    ├── staging.tfvars
    └── prod.tfvars
```

```bash
# Apply with workspace-specific variables
terraform workspace select dev
terraform apply -var-file="workspaces/dev.tfvars"
```

### Environment Variables

```bash
# Set variables per workspace
export TF_VAR_environment=$(terraform workspace show)

# Or in CI/CD
TF_VAR_environment=${WORKSPACE} terraform apply
```

## Workspace Workflows

### Creating New Environment

```bash
# 1. Create workspace
terraform workspace new staging

# 2. Workspace is automatically selected
$ terraform workspace show
staging

# 3. Initialize (if needed)
terraform init

# 4. Plan and apply
terraform plan -var-file="workspaces/staging.tfvars"
terraform apply -var-file="workspaces/staging.tfvars"
```

### Switching Environments

```bash
# Save current work
terraform apply

# Switch to production
terraform workspace select prod

# Work in production
terraform plan
terraform apply
```

### Destroying Environment

```bash
# Select workspace
terraform workspace select staging

# Destroy all resources
terraform destroy

# Delete workspace
terraform workspace select default
terraform workspace delete staging
```

## Workspace Patterns

### Pattern 1: Simple Environment Separation

```hcl
# Single configuration, multiple workspaces
# dev, staging, prod workspaces

locals {
  environment = terraform.workspace
}

resource "aws_instance" "web" {
  tags = {
    Environment = local.environment
  }
}
```

### Pattern 2: Feature Branches

```bash
# Create workspace for feature development
terraform workspace new feature-auth

# Develop and test
terraform apply

# Clean up when done
terraform destroy
terraform workspace select default
terraform workspace delete feature-auth
```

### Pattern 3: Regional Deployments

```hcl
# Workspace per region
locals {
  region_config = {
    us-east = { region = "us-east-1", azs = ["us-east-1a", "us-east-1b"] }
    us-west = { region = "us-west-2", azs = ["us-west-2a", "us-west-2b"] }
    eu      = { region = "eu-west-1", azs = ["eu-west-1a", "eu-west-1b"] }
  }

  config = local.region_config[terraform.workspace]
}

provider "aws" {
  region = local.config.region
}
```

## Workspace vs Directory Structure

### When to Use Workspaces

```yaml
Use Workspaces When:
  - Same configuration, different environments
  - Resources differ only in scale/size
  - Simple environment separation
  - Temporary environments (feature branches)

Don't Use Workspaces When:
  - Configurations differ significantly
  - Different cloud accounts per environment
  - Different teams own different environments
  - Complex multi-region deployments
```

### Alternative: Directory Structure

```
infrastructure/
├── modules/
│   ├── vpc/
│   └── eks/
├── environments/
│   ├── dev/
│   │   ├── main.tf
│   │   └── terraform.tfvars
│   ├── staging/
│   │   ├── main.tf
│   │   └── terraform.tfvars
│   └── prod/
│       ├── main.tf
│       └── terraform.tfvars
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Terraform

on:
  push:
    branches: [main, develop]

jobs:
  terraform:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3

      - name: Select Workspace
        run: |
          if [[ "${{ github.ref }}" == "refs/heads/main" ]]; then
            terraform workspace select prod
          else
            terraform workspace select dev
          fi

      - name: Terraform Apply
        run: terraform apply -auto-approve
```

### GitLab CI

```yaml
.terraform_template:
  before_script:
    - terraform init
    - terraform workspace select $TF_WORKSPACE || terraform workspace new $TF_WORKSPACE

deploy_dev:
  extends: .terraform_template
  variables:
    TF_WORKSPACE: dev
  script:
    - terraform apply -auto-approve

deploy_prod:
  extends: .terraform_template
  variables:
    TF_WORKSPACE: prod
  script:
    - terraform apply -auto-approve
  when: manual
```

## Workspace Gotchas

### Common Issues

```hcl
# Issue 1: Forgetting to switch workspaces
# Always check current workspace before apply
# terraform workspace show

# Issue 2: Hardcoded values
# Bad:
resource "aws_instance" "web" {
  instance_type = "t3.micro"  # Same for all environments!
}

# Good:
resource "aws_instance" "web" {
  instance_type = local.config[terraform.workspace].instance_type
}

# Issue 3: Not handling unknown workspaces
locals {
  config = lookup(local.workspace_configs, terraform.workspace, local.workspace_configs["default"])
}
```

### Workspace Name Validation

```hcl
locals {
  valid_workspaces = ["default", "dev", "staging", "prod"]

  # Validate workspace name
  workspace_valid = contains(local.valid_workspaces, terraform.workspace)
}

resource "null_resource" "workspace_check" {
  count = local.workspace_valid ? 0 : 1

  provisioner "local-exec" {
    command = "echo 'Invalid workspace: ${terraform.workspace}' && exit 1"
  }
}
```

## Best Practices

1. **Document Workspaces**: Document available workspaces and their purposes
2. **Naming Convention**: Use consistent workspace naming
3. **Default Configuration**: Provide sensible defaults for unknown workspaces
4. **CI/CD Integration**: Automate workspace selection in pipelines
5. **State Isolation**: Ensure each workspace has isolated state
6. **Variable Files**: Use workspace-specific variable files
7. **Resource Naming**: Include workspace in resource names
8. **Clean Up**: Delete unused workspaces and their resources
9. **Protection**: Protect production workspace from accidental changes
10. **Consider Alternatives**: Evaluate if directory structure is better fit
