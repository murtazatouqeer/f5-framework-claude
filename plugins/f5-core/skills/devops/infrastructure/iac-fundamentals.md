---
name: iac-fundamentals
description: Infrastructure as Code principles and practices
category: devops/infrastructure
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Infrastructure as Code (IaC) Fundamentals

## Overview

Infrastructure as Code (IaC) is the practice of managing and provisioning
infrastructure through machine-readable configuration files rather than
manual processes.

## IaC Benefits

```
┌─────────────────────────────────────────────────────────────────┐
│                    Benefits of IaC                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Traditional Infrastructure          Infrastructure as Code     │
│  ┌─────────────────────┐            ┌─────────────────────┐    │
│  │ Manual provisioning │            │ Automated, repeatable│    │
│  │ Documentation drift │            │ Self-documenting     │    │
│  │ Inconsistent envs   │            │ Identical environments│   │
│  │ Slow recovery       │            │ Fast disaster recovery│   │
│  │ Audit challenges    │            │ Full version control │    │
│  │ Human errors        │            │ Reduced errors       │    │
│  └─────────────────────┘            └─────────────────────┘    │
│                                                                  │
│  Key Principles:                                                 │
│  • Declarative > Imperative                                     │
│  • Idempotency                                                  │
│  • Version Control                                              │
│  • Immutable Infrastructure                                     │
│  • Testing & Validation                                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## IaC Tools Landscape

```
┌─────────────────────────────────────────────────────────────────┐
│                    IaC Tools Categories                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Provisioning          Configuration      Container Orchestration│
│  (Infrastructure)      (Software)         (Application)          │
│  ┌──────────────┐     ┌──────────────┐   ┌──────────────┐       │
│  │ • Terraform  │     │ • Ansible    │   │ • Kubernetes │       │
│  │ • Pulumi     │     │ • Chef       │   │ • Docker     │       │
│  │ • CloudForm. │     │ • Puppet     │   │   Compose    │       │
│  │ • CDK        │     │ • SaltStack  │   │ • Helm       │       │
│  │ • Crossplane │     │              │   │              │       │
│  └──────────────┘     └──────────────┘   └──────────────┘       │
│                                                                  │
│  Cloud-Specific        Multi-Cloud        GitOps                 │
│  ┌──────────────┐     ┌──────────────┐   ┌──────────────┐       │
│  │ • AWS CDK    │     │ • Terraform  │   │ • ArgoCD     │       │
│  │ • ARM Templ. │     │ • Pulumi     │   │ • Flux       │       │
│  │ • GCP DM     │     │ • Crossplane │   │ • Jenkins X  │       │
│  └──────────────┘     └──────────────┘   └──────────────┘       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Declarative vs Imperative

### Declarative Approach (Recommended)

```hcl
# Terraform (Declarative)
# "What" you want, not "how" to get there

resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.micro"

  tags = {
    Name        = "web-server"
    Environment = "production"
  }
}

resource "aws_security_group" "web" {
  name = "web-sg"

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
```

### Imperative Approach

```bash
#!/bin/bash
# Imperative script
# "How" to achieve the result step by step

# Check if instance exists
INSTANCE_ID=$(aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=web-server" \
  --query "Reservations[0].Instances[0].InstanceId" \
  --output text)

if [ "$INSTANCE_ID" == "None" ]; then
  # Create security group
  SG_ID=$(aws ec2 create-security-group \
    --group-name web-sg \
    --description "Web security group" \
    --output text)

  # Add ingress rule
  aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID \
    --protocol tcp \
    --port 443 \
    --cidr 0.0.0.0/0

  # Launch instance
  aws ec2 run-instances \
    --image-id ami-0c55b159cbfafe1f0 \
    --instance-type t3.micro \
    --security-group-ids $SG_ID \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=web-server}]'
fi
```

## State Management

```
┌─────────────────────────────────────────────────────────────────┐
│                    State Management                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Local State              Remote State                          │
│  ┌─────────────┐         ┌─────────────────────────────────┐   │
│  │ terraform.  │         │     Remote Backend               │   │
│  │ tfstate     │         │  ┌───────────────────────────┐  │   │
│  │             │  ──→    │  │ S3 / GCS / Azure Blob    │  │   │
│  │ Single user │         │  │ • Shared access           │  │   │
│  │ No locking  │         │  │ • State locking           │  │   │
│  │ Not secure  │         │  │ • Encryption              │  │   │
│  └─────────────┘         │  │ • Versioning              │  │   │
│                          │  └───────────────────────────┘  │   │
│                          └─────────────────────────────────┘   │
│                                                                  │
│  State Contains:                                                 │
│  • Resource metadata                                            │
│  • Resource dependencies                                        │
│  • Sensitive values (encrypted)                                 │
│  • Output values                                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Remote State Configuration

```hcl
# Terraform backend configuration
terraform {
  backend "s3" {
    bucket         = "my-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

# State locking with DynamoDB
resource "aws_dynamodb_table" "terraform_locks" {
  name         = "terraform-locks"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }
}
```

## Modular Infrastructure

### Module Structure

```
modules/
├── vpc/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── README.md
├── compute/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── README.md
└── database/
    ├── main.tf
    ├── variables.tf
    ├── outputs.tf
    └── README.md
```

### Module Example

```hcl
# modules/vpc/variables.tf
variable "name" {
  description = "Name of the VPC"
  type        = string
}

variable "cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "azs" {
  description = "Availability zones"
  type        = list(string)
}

variable "private_subnets" {
  description = "Private subnet CIDRs"
  type        = list(string)
}

variable "public_subnets" {
  description = "Public subnet CIDRs"
  type        = list(string)
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
```

```hcl
# modules/vpc/main.tf
resource "aws_vpc" "this" {
  cidr_block           = var.cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(var.tags, {
    Name = var.name
  })
}

resource "aws_subnet" "private" {
  count             = length(var.private_subnets)
  vpc_id            = aws_vpc.this.id
  cidr_block        = var.private_subnets[count.index]
  availability_zone = var.azs[count.index]

  tags = merge(var.tags, {
    Name = "${var.name}-private-${count.index + 1}"
    Type = "private"
  })
}

resource "aws_subnet" "public" {
  count                   = length(var.public_subnets)
  vpc_id                  = aws_vpc.this.id
  cidr_block              = var.public_subnets[count.index]
  availability_zone       = var.azs[count.index]
  map_public_ip_on_launch = true

  tags = merge(var.tags, {
    Name = "${var.name}-public-${count.index + 1}"
    Type = "public"
  })
}

resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id

  tags = merge(var.tags, {
    Name = "${var.name}-igw"
  })
}

resource "aws_nat_gateway" "this" {
  count         = length(var.public_subnets)
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id

  tags = merge(var.tags, {
    Name = "${var.name}-nat-${count.index + 1}"
  })
}

resource "aws_eip" "nat" {
  count  = length(var.public_subnets)
  domain = "vpc"
}
```

```hcl
# modules/vpc/outputs.tf
output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.this.id
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = aws_subnet.private[*].id
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = aws_subnet.public[*].id
}
```

### Using Modules

```hcl
# environments/production/main.tf
module "vpc" {
  source = "../../modules/vpc"

  name = "prod-vpc"
  cidr = "10.0.0.0/16"
  azs  = ["us-east-1a", "us-east-1b", "us-east-1c"]

  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  tags = {
    Environment = "production"
    ManagedBy   = "terraform"
  }
}

module "database" {
  source = "../../modules/database"

  name       = "prod-db"
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnet_ids
}
```

## Environment Management

```
┌─────────────────────────────────────────────────────────────────┐
│                 Environment Strategies                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Strategy 1: Directory-Based                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  environments/                                           │   │
│  │  ├── dev/                                               │   │
│  │  │   ├── main.tf                                        │   │
│  │  │   ├── variables.tf                                   │   │
│  │  │   └── terraform.tfvars                               │   │
│  │  ├── staging/                                           │   │
│  │  │   └── ...                                            │   │
│  │  └── production/                                        │   │
│  │      └── ...                                            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Strategy 2: Workspace-Based                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  terraform workspace new dev                             │   │
│  │  terraform workspace new staging                         │   │
│  │  terraform workspace new production                      │   │
│  │                                                          │   │
│  │  # Use workspace in configuration                        │   │
│  │  locals {                                                │   │
│  │    env = terraform.workspace                             │   │
│  │  }                                                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Strategy 3: Variable Files                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  terraform apply -var-file="dev.tfvars"                  │   │
│  │  terraform apply -var-file="staging.tfvars"              │   │
│  │  terraform apply -var-file="production.tfvars"           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Environment Variables

```hcl
# environments/production/terraform.tfvars
environment = "production"
region      = "us-east-1"

# Compute
instance_type = "t3.large"
min_size      = 3
max_size      = 10
desired_size  = 5

# Database
db_instance_class = "db.r5.large"
db_multi_az       = true

# Monitoring
enable_detailed_monitoring = true
log_retention_days         = 90
```

```hcl
# environments/dev/terraform.tfvars
environment = "development"
region      = "us-east-1"

# Compute
instance_type = "t3.small"
min_size      = 1
max_size      = 2
desired_size  = 1

# Database
db_instance_class = "db.t3.small"
db_multi_az       = false

# Monitoring
enable_detailed_monitoring = false
log_retention_days         = 7
```

## Testing Infrastructure

### Terraform Validate

```bash
# Syntax validation
terraform validate

# Format check
terraform fmt -check -recursive

# Static analysis with tfsec
tfsec .

# Policy as code with OPA
conftest test . -p policies/
```

### Terratest

```go
// test/vpc_test.go
package test

import (
    "testing"

    "github.com/gruntwork-io/terratest/modules/aws"
    "github.com/gruntwork-io/terratest/modules/terraform"
    "github.com/stretchr/testify/assert"
)

func TestVPCModule(t *testing.T) {
    t.Parallel()

    terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
        TerraformDir: "../modules/vpc",
        Vars: map[string]interface{}{
            "name":            "test-vpc",
            "cidr":            "10.0.0.0/16",
            "azs":             []string{"us-east-1a", "us-east-1b"},
            "private_subnets": []string{"10.0.1.0/24", "10.0.2.0/24"},
            "public_subnets":  []string{"10.0.101.0/24", "10.0.102.0/24"},
        },
    })

    defer terraform.Destroy(t, terraformOptions)
    terraform.InitAndApply(t, terraformOptions)

    // Get outputs
    vpcId := terraform.Output(t, terraformOptions, "vpc_id")
    privateSubnetIds := terraform.OutputList(t, terraformOptions, "private_subnet_ids")

    // Assertions
    assert.NotEmpty(t, vpcId)
    assert.Equal(t, 2, len(privateSubnetIds))

    // Verify VPC exists
    vpc := aws.GetVpcById(t, vpcId, "us-east-1")
    assert.Equal(t, "10.0.0.0/16", *vpc.CidrBlock)
}
```

### Policy as Code

```rego
# policies/security.rego
package main

# Deny public S3 buckets
deny[msg] {
    resource := input.resource.aws_s3_bucket[name]
    resource.acl == "public-read"
    msg := sprintf("S3 bucket '%s' should not be publicly readable", [name])
}

# Require encryption for RDS
deny[msg] {
    resource := input.resource.aws_db_instance[name]
    not resource.storage_encrypted
    msg := sprintf("RDS instance '%s' must have encryption enabled", [name])
}

# Require tags
deny[msg] {
    resource := input.resource.aws_instance[name]
    not resource.tags.Environment
    msg := sprintf("EC2 instance '%s' must have Environment tag", [name])
}
```

## CI/CD for Infrastructure

```yaml
# .github/workflows/terraform.yml
name: Terraform

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  TF_VERSION: "1.6.0"

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ env.TF_VERSION }}

      - name: Terraform Format
        run: terraform fmt -check -recursive

      - name: Terraform Init
        run: terraform init -backend=false

      - name: Terraform Validate
        run: terraform validate

      - name: TFSec Security Scan
        uses: aquasecurity/tfsec-action@v1.0.0
        with:
          soft_fail: true

  plan:
    needs: validate
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'
    steps:
      - uses: actions/checkout@v4

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ env.TF_VERSION }}
          cli_config_credentials_token: ${{ secrets.TF_API_TOKEN }}

      - name: Terraform Init
        run: terraform init
        working-directory: environments/production

      - name: Terraform Plan
        id: plan
        run: terraform plan -no-color -out=tfplan
        working-directory: environments/production
        continue-on-error: true

      - name: Comment PR
        uses: actions/github-script@v7
        with:
          script: |
            const output = `#### Terraform Plan 📖
            \`\`\`
            ${{ steps.plan.outputs.stdout }}
            \`\`\`
            `;
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: output
            })

  apply:
    needs: validate
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    environment: production
    steps:
      - uses: actions/checkout@v4

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ${{ env.TF_VERSION }}
          cli_config_credentials_token: ${{ secrets.TF_API_TOKEN }}

      - name: Terraform Init
        run: terraform init
        working-directory: environments/production

      - name: Terraform Apply
        run: terraform apply -auto-approve
        working-directory: environments/production
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│                    IaC Best Practices                            │
├─────────────────────────────────────────────────────────────────┤
│ ☐ Use version control for all infrastructure code               │
│ ☐ Implement remote state with locking                           │
│ ☐ Create reusable modules                                       │
│ ☐ Use consistent naming conventions                             │
│ ☐ Separate environments (dev, staging, prod)                    │
│ ☐ Implement policy as code                                      │
│ ☐ Test infrastructure changes before applying                   │
│ ☐ Use CI/CD for infrastructure deployments                      │
│ ☐ Document modules with README and examples                     │
│ ☐ Tag all resources appropriately                               │
│ ☐ Use secrets management (not hardcoded)                        │
│ ☐ Implement drift detection                                     │
└─────────────────────────────────────────────────────────────────┘
```
