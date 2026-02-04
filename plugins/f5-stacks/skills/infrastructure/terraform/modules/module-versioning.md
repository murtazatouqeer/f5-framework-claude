# Module Versioning

## Overview

Module versioning ensures consistent, reproducible infrastructure deployments. Proper version management prevents unexpected changes and enables controlled updates.

## Version Constraints

### Constraint Operators

```hcl
# Exact version
version = "1.2.3"

# Greater than or equal
version = ">= 1.2.0"

# Less than
version = "< 2.0.0"

# Range
version = ">= 1.2.0, < 2.0.0"

# Pessimistic constraint (allows patch updates)
version = "~> 1.2.0"    # >= 1.2.0, < 1.3.0

# Pessimistic constraint (allows minor updates)
version = "~> 1.2"      # >= 1.2.0, < 2.0.0

# Not equal
version = "!= 1.2.5"

# Combined constraints
version = ">= 1.2.0, != 1.2.5, < 2.0.0"
```

### Registry Modules

```hcl
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"  # Allows 5.x updates
}

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "19.16.0"  # Exact version for stability
}
```

### GitHub Modules

```hcl
# Tag reference (recommended)
module "vpc" {
  source = "github.com/company/terraform-vpc?ref=v1.2.3"
}

# Branch reference (for development)
module "vpc" {
  source = "github.com/company/terraform-vpc?ref=develop"
}

# Commit SHA (most stable)
module "vpc" {
  source = "github.com/company/terraform-vpc?ref=abc1234567890"
}
```

## Semantic Versioning

### Version Format

```
MAJOR.MINOR.PATCH

1.2.3
│ │ │
│ │ └── PATCH: Bug fixes, no breaking changes
│ └──── MINOR: New features, backward compatible
└────── MAJOR: Breaking changes
```

### Pre-release Versions

```
1.0.0-alpha
1.0.0-alpha.1
1.0.0-beta
1.0.0-beta.2
1.0.0-rc.1
1.0.0
```

### When to Bump Versions

```yaml
PATCH (1.2.3 → 1.2.4):
  - Bug fixes
  - Documentation updates
  - Minor internal refactoring
  - Security patches without API changes

MINOR (1.2.3 → 1.3.0):
  - New optional variables
  - New outputs
  - New optional resources
  - Backward-compatible enhancements

MAJOR (1.2.3 → 2.0.0):
  - Removing variables or outputs
  - Changing variable types
  - Changing resource names (causes recreation)
  - Removing resources
  - Changing default values significantly
```

## Lock Files

### terraform.lock.hcl

```hcl
# This file is maintained automatically by "terraform init".
# Manual edits may be lost in future updates.

provider "registry.terraform.io/hashicorp/aws" {
  version     = "5.31.0"
  constraints = "~> 5.0"
  hashes = [
    "h1:HASH1...",
    "zh:HASH2...",
  ]
}

provider "registry.terraform.io/hashicorp/random" {
  version     = "3.6.0"
  constraints = "~> 3.0"
  hashes = [
    "h1:HASH1...",
    "zh:HASH2...",
  ]
}
```

### Managing Lock Files

```bash
# Generate or update lock file
terraform init

# Update specific provider
terraform init -upgrade

# Generate lock file for multiple platforms
terraform providers lock \
  -platform=linux_amd64 \
  -platform=darwin_amd64 \
  -platform=darwin_arm64

# Include lock file in version control
git add .terraform.lock.hcl
```

## Version Pinning Strategies

### Development Environment

```hcl
# Allow minor updates for latest features
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"  # Gets 5.x updates
}
```

### Staging Environment

```hcl
# Allow only patch updates
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.1.0"  # Gets 5.1.x updates only
}
```

### Production Environment

```hcl
# Pin to exact version
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.1.2"  # Exact version, no automatic updates
}
```

## Upgrading Modules

### Upgrade Process

```bash
# 1. Review changelog for breaking changes
# Check GitHub releases or CHANGELOG.md

# 2. Update version constraint
# Edit main.tf with new version

# 3. Initialize with upgrade
terraform init -upgrade

# 4. Review plan carefully
terraform plan

# 5. Apply in non-production first
terraform apply
```

### Handling Breaking Changes

```hcl
# Before upgrade: Old module version
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "4.0.0"

  # v4 configuration
  name = "my-vpc"
  cidr = "10.0.0.0/16"
}

# After upgrade: New module version with changes
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.1.2"

  # v5 may have different variable names
  name = "my-vpc"
  cidr = "10.0.0.0/16"

  # New required variable in v5
  enable_dns_hostnames = true
}
```

### State Migration

```bash
# If resource names changed in new version
# Use state mv to prevent recreation

terraform state mv \
  module.vpc.aws_vpc.this \
  module.vpc.aws_vpc.main

# Or use moved blocks in configuration
moved {
  from = module.vpc.aws_vpc.this
  to   = module.vpc.aws_vpc.main
}
```

## Multi-Version Support

### Supporting Multiple Terraform Versions

```hcl
# versions.tf
terraform {
  required_version = ">= 1.5.0, < 2.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 4.0, < 6.0"
    }
  }
}
```

### Conditional Features

```hcl
# Use newer features only when available
terraform {
  required_version = ">= 1.5.0"
}

# Terraform 1.5+ features
import {
  to = aws_instance.existing
  id = "i-1234567890abcdef0"
}

check "health" {
  data "http" "health" {
    url = "https://api.example.com/health"
  }

  assert {
    condition     = data.http.health.status_code == 200
    error_message = "API is unhealthy"
  }
}
```

## Version Documentation

### CHANGELOG.md

```markdown
# Changelog

All notable changes to this module will be documented in this file.

## [Unreleased]

## [2.0.0] - 2024-01-15

### Breaking Changes
- Renamed `vpc_cidr` variable to `cidr_block`
- Removed `enable_classiclink` variable (deprecated by AWS)

### Added
- Support for IPv6 CIDR blocks
- New `ipv6_cidr_block` variable

### Changed
- Default value of `enable_dns_hostnames` changed to `true`

## [1.5.0] - 2023-12-01

### Added
- New output `vpc_owner_id`
- Support for additional tags on subnets

### Fixed
- Fixed NAT gateway creation order

## [1.4.1] - 2023-11-15

### Fixed
- Fixed incorrect CIDR calculation for private subnets

## [1.4.0] - 2023-11-01

### Added
- New variable `enable_vpc_endpoints`
```

### Version Matrix

```markdown
## Compatibility Matrix

| Module Version | Terraform Version | AWS Provider |
|----------------|-------------------|--------------|
| 2.x            | >= 1.5.0          | >= 5.0       |
| 1.x            | >= 1.0.0          | >= 4.0, < 5.0|
| 0.x            | >= 0.14.0         | >= 3.0, < 4.0|
```

## Automated Version Management

### Git Tagging

```bash
# Create annotated tag
git tag -a v1.2.3 -m "Release version 1.2.3"

# Push tags
git push origin v1.2.3
git push --tags

# List tags
git tag -l "v*"

# Delete tag
git tag -d v1.2.3
git push origin :refs/tags/v1.2.3
```

### CI/CD Version Checks

```yaml
# .github/workflows/version-check.yml
name: Version Check

on:
  pull_request:
    branches: [main]

jobs:
  version-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Check version bump
        run: |
          # Extract current version from module
          CURRENT=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")
          echo "Current version: $CURRENT"

          # Check if CHANGELOG was updated
          if ! git diff --name-only origin/main | grep -q "CHANGELOG.md"; then
            echo "Warning: CHANGELOG.md not updated"
          fi
```

### Dependabot for Terraform

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "terraform"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
    commit-message:
      prefix: "terraform"
```

## Best Practices

1. **Pin Production Versions**: Use exact versions in production
2. **Use Lock Files**: Commit .terraform.lock.hcl
3. **Follow Semver**: Use semantic versioning for modules
4. **Document Changes**: Maintain comprehensive CHANGELOG
5. **Test Upgrades**: Test version upgrades in non-production
6. **Gradual Updates**: Update one major version at a time
7. **Review Breaking Changes**: Read changelogs before upgrading
8. **Automate Checks**: Use CI to validate version constraints
9. **Tag Releases**: Use Git tags for module versions
10. **Compatibility Matrix**: Document supported versions
