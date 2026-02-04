# Module Composition

## Overview

Module composition is the practice of combining smaller, focused modules to build complex infrastructure. Well-designed modules are like building blocks that can be assembled in various configurations.

## Composition Patterns

### Layered Architecture

```
infrastructure/
├── layers/
│   ├── network/          # Layer 1: Foundation
│   │   └── main.tf
│   ├── compute/          # Layer 2: Compute resources
│   │   └── main.tf
│   └── application/      # Layer 3: Application
│       └── main.tf
└── environments/
    ├── dev/
    ├── staging/
    └── prod/
```

```hcl
# layers/network/main.tf
module "vpc" {
  source = "../../modules/vpc"

  cidr_block = var.vpc_cidr
  azs        = var.availability_zones
}

output "vpc_id" {
  value = module.vpc.vpc_id
}

output "private_subnet_ids" {
  value = module.vpc.private_subnet_ids
}
```

```hcl
# layers/compute/main.tf
data "terraform_remote_state" "network" {
  backend = "s3"
  config = {
    bucket = "terraform-state"
    key    = "network/terraform.tfstate"
    region = "us-east-1"
  }
}

module "eks" {
  source = "../../modules/eks"

  vpc_id     = data.terraform_remote_state.network.outputs.vpc_id
  subnet_ids = data.terraform_remote_state.network.outputs.private_subnet_ids
}
```

### Wrapper Module Pattern

```hcl
# modules/app-stack/main.tf
# Composes multiple modules into a complete application stack

module "vpc" {
  source = "../vpc"

  name       = var.name
  cidr_block = var.vpc_cidr
}

module "security" {
  source = "../security"

  vpc_id = module.vpc.vpc_id
  name   = var.name
}

module "database" {
  source = "../rds"

  vpc_id             = module.vpc.vpc_id
  subnet_ids         = module.vpc.private_subnet_ids
  security_group_ids = [module.security.db_security_group_id]
}

module "compute" {
  source = "../ecs"

  vpc_id             = module.vpc.vpc_id
  subnet_ids         = module.vpc.private_subnet_ids
  security_group_ids = [module.security.app_security_group_id]
  database_endpoint  = module.database.endpoint
}
```

### Factory Pattern

```hcl
# modules/resource-factory/main.tf
# Creates multiple instances based on configuration

variable "resources" {
  description = "Map of resources to create"
  type = map(object({
    instance_type = string
    volume_size   = number
    tags          = map(string)
  }))
}

module "instances" {
  source   = "../ec2"
  for_each = var.resources

  name          = each.key
  instance_type = each.value.instance_type
  volume_size   = each.value.volume_size
  tags          = each.value.tags
}

output "instance_ids" {
  value = { for k, v in module.instances : k => v.instance_id }
}
```

```hcl
# Usage
module "servers" {
  source = "./modules/resource-factory"

  resources = {
    web = {
      instance_type = "t3.small"
      volume_size   = 20
      tags          = { Role = "web" }
    }
    api = {
      instance_type = "t3.medium"
      volume_size   = 50
      tags          = { Role = "api" }
    }
    worker = {
      instance_type = "t3.large"
      volume_size   = 100
      tags          = { Role = "worker" }
    }
  }
}
```

### Adapter Pattern

```hcl
# modules/cloud-adapter/main.tf
# Provides unified interface across cloud providers

variable "cloud_provider" {
  type = string
}

module "aws_compute" {
  source = "../aws-ec2"
  count  = var.cloud_provider == "aws" ? 1 : 0

  instance_type = var.instance_size
}

module "gcp_compute" {
  source = "../gcp-compute"
  count  = var.cloud_provider == "gcp" ? 1 : 0

  machine_type = var.instance_size
}

module "azure_compute" {
  source = "../azure-vm"
  count  = var.cloud_provider == "azure" ? 1 : 0

  vm_size = var.instance_size
}

output "instance_id" {
  value = coalesce(
    try(module.aws_compute[0].instance_id, null),
    try(module.gcp_compute[0].instance_id, null),
    try(module.azure_compute[0].vm_id, null)
  )
}
```

## Passing Data Between Modules

### Direct Output Reference

```hcl
module "vpc" {
  source = "./modules/vpc"
}

module "ec2" {
  source = "./modules/ec2"

  # Direct reference to vpc module output
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnet_ids
}
```

### Using Remote State

```hcl
# When modules are in separate configurations
data "terraform_remote_state" "vpc" {
  backend = "s3"

  config = {
    bucket = "terraform-state"
    key    = "vpc/terraform.tfstate"
    region = "us-east-1"
  }
}

module "ec2" {
  source = "./modules/ec2"

  vpc_id     = data.terraform_remote_state.vpc.outputs.vpc_id
  subnet_ids = data.terraform_remote_state.vpc.outputs.private_subnet_ids
}
```

### Module Outputs as Inputs

```hcl
# Complex output structure
module "network" {
  source = "./modules/network"
}

module "app" {
  source = "./modules/app"

  network_config = {
    vpc_id            = module.network.vpc_id
    private_subnets   = module.network.private_subnet_ids
    public_subnets    = module.network.public_subnet_ids
    security_groups   = module.network.security_group_ids
  }
}
```

## Conditional Module Composition

### Feature Flags

```hcl
variable "features" {
  type = object({
    enable_monitoring = bool
    enable_logging    = bool
    enable_backup     = bool
  })

  default = {
    enable_monitoring = true
    enable_logging    = true
    enable_backup     = false
  }
}

module "monitoring" {
  source = "./modules/monitoring"
  count  = var.features.enable_monitoring ? 1 : 0

  cluster_id = module.eks.cluster_id
}

module "logging" {
  source = "./modules/logging"
  count  = var.features.enable_logging ? 1 : 0

  cluster_id = module.eks.cluster_id
}

module "backup" {
  source = "./modules/backup"
  count  = var.features.enable_backup ? 1 : 0

  resources = module.database.backup_targets
}
```

### Environment-Based Composition

```hcl
variable "environment" {
  type = string
}

locals {
  is_production = var.environment == "prod"
}

module "database" {
  source = "./modules/rds"

  multi_az     = local.is_production
  backup_days  = local.is_production ? 30 : 7
  instance_class = local.is_production ? "db.r6g.large" : "db.t3.micro"
}

module "cache" {
  source = "./modules/elasticache"
  count  = local.is_production ? 1 : 0

  cluster_mode = true
  num_shards   = 3
}
```

## Module Dependencies

### Implicit Dependencies

```hcl
module "vpc" {
  source = "./modules/vpc"
}

# Implicit dependency via vpc_id reference
module "database" {
  source = "./modules/rds"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.database_subnet_ids
}
```

### Explicit Dependencies

```hcl
module "iam" {
  source = "./modules/iam"
}

module "eks" {
  source = "./modules/eks"

  # Explicit dependency for IAM role propagation
  depends_on = [module.iam]
}
```

### Dependency Graph

```hcl
# Clear dependency chain
module "network" {
  source = "./modules/network"
}

module "security" {
  source = "./modules/security"

  vpc_id = module.network.vpc_id
}

module "database" {
  source = "./modules/database"

  vpc_id            = module.network.vpc_id
  security_group_id = module.security.db_sg_id
  subnet_ids        = module.network.database_subnets
}

module "application" {
  source = "./modules/application"

  vpc_id            = module.network.vpc_id
  security_group_id = module.security.app_sg_id
  subnet_ids        = module.network.private_subnets
  database_endpoint = module.database.endpoint
}
```

## Shared Configuration

### Common Variables Module

```hcl
# modules/common/outputs.tf
output "common_tags" {
  value = {
    ManagedBy = "terraform"
    Project   = var.project_name
  }
}

output "naming_prefix" {
  value = "${var.project_name}-${var.environment}"
}
```

```hcl
# Usage in other modules
module "common" {
  source = "./modules/common"

  project_name = "myapp"
  environment  = "prod"
}

module "vpc" {
  source = "./modules/vpc"

  name = module.common.naming_prefix
  tags = module.common.common_tags
}
```

### Configuration Object

```hcl
# Single configuration object passed to all modules
variable "config" {
  type = object({
    project     = string
    environment = string
    region      = string
    tags        = map(string)
  })
}

module "vpc" {
  source = "./modules/vpc"

  name   = "${var.config.project}-${var.config.environment}"
  region = var.config.region
  tags   = var.config.tags
}

module "eks" {
  source = "./modules/eks"

  name   = "${var.config.project}-${var.config.environment}"
  region = var.config.region
  tags   = var.config.tags
}
```

## Testing Composed Modules

### Example Test Structure

```hcl
# test/composed_stack_test.go
module "test_stack" {
  source = "../modules/app-stack"

  name        = "test-stack"
  environment = "test"
  vpc_cidr    = "10.99.0.0/16"
}

# Validate outputs
output "test_vpc_id" {
  value = module.test_stack.vpc_id != "" ? "PASS" : "FAIL"
}

output "test_database_endpoint" {
  value = can(regex("^.+\\.rds\\.amazonaws\\.com$", module.test_stack.database_endpoint)) ? "PASS" : "FAIL"
}
```

## Best Practices

1. **Single Responsibility**: Each module should handle one logical component
2. **Clear Interfaces**: Define clear inputs and outputs between modules
3. **Loose Coupling**: Minimize dependencies between modules
4. **Version Everything**: Use versioned modules in composition
5. **Document Composition**: Document how modules fit together
6. **Test Compositions**: Write integration tests for composed modules
7. **Use Outputs**: Pass data between modules via outputs, not implicit references
8. **Feature Flags**: Use boolean variables for optional components
9. **Environment Awareness**: Design modules to adapt to environments
10. **Remote State**: Use remote state for cross-configuration composition
