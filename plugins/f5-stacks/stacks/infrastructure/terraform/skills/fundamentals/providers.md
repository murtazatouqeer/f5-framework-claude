# Terraform Providers

## Overview

Providers are plugins that enable Terraform to interact with cloud platforms, SaaS providers, and other APIs.

## Provider Configuration

### Basic Configuration

```hcl
# versions.tf
terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }

    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }

    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

# providers.tf
provider "aws" {
  region = "us-east-1"
}
```

### Version Constraints

```hcl
required_providers {
  aws = {
    source  = "hashicorp/aws"

    # Exact version
    version = "5.31.0"

    # Pessimistic constraint (allows patch updates)
    version = "~> 5.31.0"    # >= 5.31.0, < 5.32.0

    # Pessimistic constraint (allows minor updates)
    version = "~> 5.31"      # >= 5.31.0, < 6.0.0

    # Range constraints
    version = ">= 5.0, < 6.0"

    # Multiple constraints
    version = ">= 5.0, != 5.10.0"
  }
}
```

## AWS Provider

### Basic Configuration

```hcl
provider "aws" {
  region = "us-east-1"

  # Optional: Profile from ~/.aws/credentials
  profile = "production"

  # Optional: Explicit credentials (not recommended)
  # access_key = var.aws_access_key
  # secret_key = var.aws_secret_key
}
```

### Assume Role

```hcl
provider "aws" {
  region = "us-east-1"

  assume_role {
    role_arn     = "arn:aws:iam::123456789012:role/TerraformRole"
    session_name = "terraform-session"
    external_id  = "terraform"
  }
}
```

### Multiple AWS Accounts

```hcl
# Default provider
provider "aws" {
  region = "us-east-1"
}

# Aliased provider for different account
provider "aws" {
  alias  = "production"
  region = "us-east-1"

  assume_role {
    role_arn = "arn:aws:iam::PROD_ACCOUNT:role/TerraformRole"
  }
}

# Aliased provider for different region
provider "aws" {
  alias  = "eu"
  region = "eu-west-1"
}

# Using aliased providers
resource "aws_s3_bucket" "prod" {
  provider = aws.production
  bucket   = "prod-bucket"
}

resource "aws_s3_bucket" "eu" {
  provider = aws.eu
  bucket   = "eu-bucket"
}
```

### Default Tags

```hcl
provider "aws" {
  region = "us-east-1"

  default_tags {
    tags = {
      Environment = var.environment
      Project     = var.project_name
      ManagedBy   = "terraform"
      Owner       = var.owner
    }
  }
}
```

## Google Cloud Provider

### Basic Configuration

```hcl
provider "google" {
  project = "my-project-id"
  region  = "us-central1"
  zone    = "us-central1-a"
}

# With explicit credentials
provider "google" {
  project     = "my-project-id"
  region      = "us-central1"
  credentials = file("service-account.json")
}
```

### Multiple Projects

```hcl
provider "google" {
  project = "dev-project"
  region  = "us-central1"
}

provider "google" {
  alias   = "production"
  project = "prod-project"
  region  = "us-central1"
}
```

### Impersonation

```hcl
provider "google" {
  project = "my-project"
  region  = "us-central1"

  impersonate_service_account = "terraform@my-project.iam.gserviceaccount.com"
}
```

## Azure Provider

### Basic Configuration

```hcl
provider "azurerm" {
  features {}

  subscription_id = var.subscription_id
  tenant_id       = var.tenant_id
}
```

### Service Principal Authentication

```hcl
provider "azurerm" {
  features {}

  subscription_id = var.subscription_id
  tenant_id       = var.tenant_id
  client_id       = var.client_id
  client_secret   = var.client_secret
}
```

### Multiple Subscriptions

```hcl
provider "azurerm" {
  features {}
  subscription_id = "dev-subscription-id"
}

provider "azurerm" {
  alias           = "production"
  features {}
  subscription_id = "prod-subscription-id"
}
```

### Features Block

```hcl
provider "azurerm" {
  features {
    resource_group {
      prevent_deletion_if_contains_resources = true
    }

    key_vault {
      purge_soft_delete_on_destroy    = false
      recover_soft_deleted_key_vaults = true
    }

    virtual_machine {
      delete_os_disk_on_deletion     = true
      graceful_shutdown              = false
      skip_shutdown_and_force_delete = false
    }
  }
}
```

## Kubernetes Provider

```hcl
# Using kubeconfig
provider "kubernetes" {
  config_path    = "~/.kube/config"
  config_context = "my-context"
}

# Using explicit configuration
provider "kubernetes" {
  host                   = var.cluster_endpoint
  cluster_ca_certificate = base64decode(var.cluster_ca_cert)
  token                  = var.cluster_token
}

# Using EKS cluster
provider "kubernetes" {
  host                   = data.aws_eks_cluster.cluster.endpoint
  cluster_ca_certificate = base64decode(data.aws_eks_cluster.cluster.certificate_authority[0].data)

  exec {
    api_version = "client.authentication.k8s.io/v1beta1"
    command     = "aws"
    args        = ["eks", "get-token", "--cluster-name", var.cluster_name]
  }
}
```

## Helm Provider

```hcl
provider "helm" {
  kubernetes {
    config_path = "~/.kube/config"
  }
}

# With EKS authentication
provider "helm" {
  kubernetes {
    host                   = data.aws_eks_cluster.cluster.endpoint
    cluster_ca_certificate = base64decode(data.aws_eks_cluster.cluster.certificate_authority[0].data)

    exec {
      api_version = "client.authentication.k8s.io/v1beta1"
      command     = "aws"
      args        = ["eks", "get-token", "--cluster-name", var.cluster_name]
    }
  }
}
```

## Random Provider

```hcl
terraform {
  required_providers {
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

# Random string
resource "random_string" "suffix" {
  length  = 8
  special = false
  upper   = false
}

# Random password
resource "random_password" "db" {
  length           = 16
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

# Random UUID
resource "random_uuid" "id" {}

# Random integer
resource "random_integer" "port" {
  min = 8000
  max = 9000
}

# Random pet name
resource "random_pet" "name" {
  length    = 2
  separator = "-"
}
```

## Null Provider

```hcl
terraform {
  required_providers {
    null = {
      source  = "hashicorp/null"
      version = "~> 3.0"
    }
  }
}

# Null resource for local-exec
resource "null_resource" "provisioner" {
  triggers = {
    cluster_id = aws_eks_cluster.main.id
  }

  provisioner "local-exec" {
    command = "aws eks update-kubeconfig --name ${var.cluster_name}"
  }
}
```

## Local Provider

```hcl
terraform {
  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.0"
    }
  }
}

# Create local file
resource "local_file" "kubeconfig" {
  filename = "${path.module}/kubeconfig"
  content  = data.aws_eks_cluster.cluster.kubeconfig
}

# Sensitive file
resource "local_sensitive_file" "private_key" {
  filename        = "${path.module}/key.pem"
  content         = tls_private_key.main.private_key_pem
  file_permission = "0600"
}
```

## TLS Provider

```hcl
terraform {
  required_providers {
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
  }
}

# Private key
resource "tls_private_key" "main" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

# Self-signed certificate
resource "tls_self_signed_cert" "main" {
  private_key_pem = tls_private_key.main.private_key_pem

  subject {
    common_name  = "example.com"
    organization = "Example Inc"
  }

  validity_period_hours = 8760  # 1 year

  allowed_uses = [
    "key_encipherment",
    "digital_signature",
    "server_auth",
  ]
}
```

## Provider Authentication Methods

### Environment Variables

```bash
# AWS
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_REGION="us-east-1"

# GCP
export GOOGLE_CREDENTIALS="$(cat service-account.json)"
export GOOGLE_PROJECT="my-project"

# Azure
export ARM_CLIENT_ID="your-client-id"
export ARM_CLIENT_SECRET="your-client-secret"
export ARM_SUBSCRIPTION_ID="your-subscription-id"
export ARM_TENANT_ID="your-tenant-id"
```

### Provider-Specific Auth Files

```hcl
# AWS: Uses ~/.aws/credentials
provider "aws" {
  profile = "my-profile"
  region  = "us-east-1"
}

# GCP: Uses GOOGLE_APPLICATION_CREDENTIALS env var
provider "google" {
  project = "my-project"
  region  = "us-central1"
}

# Azure: Uses az login
provider "azurerm" {
  features {}
}
```

## Best Practices

1. **Version Constraints**: Always specify provider version constraints
2. **Aliases**: Use aliases for multi-region or multi-account deployments
3. **Environment Variables**: Use environment variables for credentials
4. **Avoid Hardcoding**: Never hardcode credentials in configuration
5. **Default Tags**: Use default_tags for consistent resource tagging
6. **Lock File**: Commit .terraform.lock.hcl for reproducible builds
7. **Minimal Permissions**: Use least-privilege IAM policies
