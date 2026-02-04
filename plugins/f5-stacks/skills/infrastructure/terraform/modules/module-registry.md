# Module Registry

## Overview

Module registries provide centralized storage and versioning for Terraform modules. The Terraform Registry is the public registry, while organizations can use private registries for internal modules.

## Terraform Public Registry

### Using Registry Modules

```hcl
# Official AWS VPC module
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.1.2"

  name = "my-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["us-east-1a", "us-east-1b", "us-east-1c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  enable_nat_gateway = true
  single_nat_gateway = true
}

# Official AWS EKS module
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"

  cluster_name    = "my-cluster"
  cluster_version = "1.28"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets
}

# Official AWS RDS module
module "rds" {
  source  = "terraform-aws-modules/rds/aws"
  version = "~> 6.0"

  identifier = "mydb"
  engine     = "postgres"

  instance_class = "db.t3.micro"
  allocated_storage = 20

  vpc_security_group_ids = [module.security_group.security_group_id]
  subnet_ids             = module.vpc.database_subnets
}
```

### Module Source Format

```hcl
# Public registry format
source = "<NAMESPACE>/<NAME>/<PROVIDER>"
source = "terraform-aws-modules/vpc/aws"

# With version constraint
source  = "terraform-aws-modules/vpc/aws"
version = "5.1.2"

# Submodule
source  = "terraform-aws-modules/vpc/aws//modules/vpc-endpoints"
version = "5.1.2"
```

### Finding Modules

```bash
# Browse registry
# https://registry.terraform.io/

# Search for modules
# https://registry.terraform.io/search/modules

# Popular module namespaces
# - terraform-aws-modules (AWS)
# - terraform-google-modules (GCP)
# - Azure (Azure)
```

## Terraform Cloud Private Registry

### Publishing to Private Registry

```hcl
# Module structure required for private registry
modules/
└── vpc/
    ├── main.tf
    ├── variables.tf
    ├── outputs.tf
    ├── versions.tf
    └── README.md
```

### Using Private Registry Modules

```hcl
# Terraform Cloud private registry
module "vpc" {
  source  = "app.terraform.io/<ORG>/vpc/aws"
  version = "1.0.0"

  name = "my-vpc"
}
```

### Configuration

```hcl
# Configure Terraform Cloud credentials
# In ~/.terraformrc or as environment variable

credentials "app.terraform.io" {
  token = "your-api-token"
}

# Or via environment variable
# TF_TOKEN_app_terraform_io=your-api-token
```

## GitHub as Module Source

### Public GitHub Repository

```hcl
# HTTPS
module "vpc" {
  source = "github.com/company/terraform-aws-vpc"
}

# With specific ref (tag, branch, commit)
module "vpc" {
  source = "github.com/company/terraform-aws-vpc?ref=v1.0.0"
}

module "vpc" {
  source = "github.com/company/terraform-aws-vpc?ref=main"
}

module "vpc" {
  source = "github.com/company/terraform-aws-vpc?ref=abc123"
}

# SSH (for private repos)
module "vpc" {
  source = "git@github.com:company/terraform-aws-vpc.git"
}

# With path to submodule
module "endpoints" {
  source = "github.com/company/terraform-aws-vpc//modules/endpoints?ref=v1.0.0"
}
```

### Private GitHub Repository

```bash
# Configure SSH key
ssh-keygen -t ed25519 -C "terraform@company.com"

# Add to GitHub as deploy key or SSH key

# Use SSH source
module "vpc" {
  source = "git@github.com:company/private-modules.git//vpc?ref=v1.0.0"
}
```

### GitHub Enterprise

```hcl
module "vpc" {
  source = "git::https://github.company.com/terraform/modules.git//vpc?ref=v1.0.0"
}
```

## GitLab as Module Source

```hcl
# Public GitLab
module "vpc" {
  source = "gitlab.com/company/terraform-modules/vpc"
}

# Private GitLab
module "vpc" {
  source = "git::https://gitlab.com/company/terraform-modules.git//vpc?ref=v1.0.0"
}

# GitLab Self-Hosted
module "vpc" {
  source = "git::https://gitlab.company.com/terraform/modules.git//vpc?ref=v1.0.0"
}
```

## S3 as Module Source

```hcl
# S3 bucket
module "vpc" {
  source = "s3::https://s3-us-east-1.amazonaws.com/company-terraform-modules/vpc.zip"
}

# With specific version in path
module "vpc" {
  source = "s3::https://s3-us-east-1.amazonaws.com/company-terraform-modules/vpc/1.0.0/vpc.zip"
}
```

## GCS as Module Source

```hcl
# Google Cloud Storage
module "vpc" {
  source = "gcs::https://www.googleapis.com/storage/v1/company-terraform-modules/vpc.zip"
}
```

## HTTP(S) as Module Source

```hcl
# Generic HTTP source (must return zip file)
module "vpc" {
  source = "https://modules.company.com/vpc/v1.0.0.zip"
}
```

## Local Path as Module Source

```hcl
# Relative path
module "vpc" {
  source = "./modules/vpc"
}

module "vpc" {
  source = "../shared-modules/vpc"
}

# Absolute path (not recommended)
module "vpc" {
  source = "/opt/terraform/modules/vpc"
}
```

## Publishing Modules to Public Registry

### Requirements

1. **GitHub Public Repository**: Module must be in a public GitHub repo
2. **Naming Convention**: `terraform-<PROVIDER>-<NAME>`
3. **Repository Structure**: Standard module structure
4. **Semantic Versioning**: Use Git tags for versions

### Repository Structure

```
terraform-aws-vpc/
├── main.tf
├── variables.tf
├── outputs.tf
├── versions.tf
├── README.md
├── LICENSE
├── examples/
│   ├── simple/
│   │   └── main.tf
│   └── complete/
│       └── main.tf
└── modules/
    └── vpc-endpoints/
        ├── main.tf
        ├── variables.tf
        └── outputs.tf
```

### Publishing Steps

```bash
# 1. Create repository with correct name
# terraform-<provider>-<name>

# 2. Add required files
# main.tf, variables.tf, outputs.tf, README.md

# 3. Tag releases
git tag v1.0.0
git push origin v1.0.0

# 4. Sign in to registry.terraform.io
# 5. Connect GitHub account
# 6. Publish module from GitHub repo
```

### README Template for Registry

```markdown
# AWS VPC Terraform Module

Terraform module which creates VPC resources on AWS.

## Usage

\`\`\`hcl
module "vpc" {
  source  = "company/vpc/aws"
  version = "1.0.0"

  name = "my-vpc"
  cidr = "10.0.0.0/16"
}
\`\`\`

## Examples

- [Simple VPC](examples/simple)
- [Complete VPC](examples/complete)

## Requirements

| Name | Version |
|------|---------|
| terraform | >= 1.6.0 |
| aws | >= 5.0 |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| name | VPC name | `string` | n/a | yes |
| cidr | VPC CIDR block | `string` | n/a | yes |

## Outputs

| Name | Description |
|------|-------------|
| vpc_id | VPC ID |
| vpc_arn | VPC ARN |

## License

Apache 2.0
```

## Module Caching

### Cache Location

```bash
# Default cache directory
~/.terraform.d/plugin-cache

# Configure in CLI config
# ~/.terraformrc
plugin_cache_dir = "$HOME/.terraform.d/plugin-cache"
```

### Cache Behavior

```bash
# terraform init downloads modules to
.terraform/modules/

# Lock file records versions
.terraform.lock.hcl
```

## Best Practices

1. **Version Constraints**: Always specify version constraints for registry modules
2. **Lock File**: Commit .terraform.lock.hcl to version control
3. **Trusted Sources**: Only use modules from trusted sources
4. **Review Before Use**: Review module code before using
5. **Pin Versions**: Use exact versions in production
6. **Private for Sensitive**: Use private registry for proprietary modules
7. **Semantic Versioning**: Follow semver for published modules
8. **Documentation**: Include comprehensive README and examples
9. **Examples**: Provide working examples for modules
10. **Testing**: Test modules before publishing new versions
