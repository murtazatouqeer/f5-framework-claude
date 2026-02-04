# Data Sources

## Overview

Data sources allow Terraform to fetch and compute data from external sources. They provide read-only views of existing infrastructure or compute dynamic values.

## Data Source Syntax

```hcl
data "<PROVIDER>_<TYPE>" "<NAME>" {
  # Query arguments
  filter_argument = value
}

# Reference
data.<PROVIDER>_<TYPE>.<NAME>.attribute
```

## Common Data Sources

### AWS AMI

```hcl
# Find latest Amazon Linux 2023 AMI
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  filter {
    name   = "root-device-type"
    values = ["ebs"]
  }
}

# Find Ubuntu AMI
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]  # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
}

# Usage
resource "aws_instance" "web" {
  ami           = data.aws_ami.amazon_linux.id
  instance_type = "t3.micro"
}
```

### AWS Availability Zones

```hcl
data "aws_availability_zones" "available" {
  state = "available"

  filter {
    name   = "opt-in-status"
    values = ["opt-in-not-required"]
  }
}

# Usage
resource "aws_subnet" "public" {
  count             = length(data.aws_availability_zones.available.names)
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index)
  availability_zone = data.aws_availability_zones.available.names[count.index]
}

# Output
output "azs" {
  value = data.aws_availability_zones.available.names
}
```

### AWS VPC

```hcl
# Fetch existing VPC by ID
data "aws_vpc" "selected" {
  id = var.vpc_id
}

# Fetch VPC by tag
data "aws_vpc" "main" {
  filter {
    name   = "tag:Name"
    values = ["main-vpc"]
  }
}

# Fetch default VPC
data "aws_vpc" "default" {
  default = true
}

# Usage
resource "aws_security_group" "web" {
  vpc_id = data.aws_vpc.selected.id
}
```

### AWS Subnets

```hcl
# Fetch subnets by VPC
data "aws_subnets" "private" {
  filter {
    name   = "vpc-id"
    values = [var.vpc_id]
  }

  filter {
    name   = "tag:Type"
    values = ["Private"]
  }
}

# Fetch subnet details
data "aws_subnet" "selected" {
  for_each = toset(data.aws_subnets.private.ids)
  id       = each.value
}

# Usage
resource "aws_instance" "web" {
  count     = length(data.aws_subnets.private.ids)
  subnet_id = data.aws_subnets.private.ids[count.index]
}
```

### AWS Security Group

```hcl
# Fetch by name
data "aws_security_group" "selected" {
  name   = "allow-ssh"
  vpc_id = var.vpc_id
}

# Fetch by ID
data "aws_security_group" "by_id" {
  id = var.security_group_id
}

# Fetch by tag
data "aws_security_group" "web" {
  filter {
    name   = "tag:Name"
    values = ["web-sg"]
  }

  filter {
    name   = "vpc-id"
    values = [var.vpc_id]
  }
}
```

### AWS IAM Policy Document

```hcl
data "aws_iam_policy_document" "assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

data "aws_iam_policy_document" "s3_access" {
  statement {
    effect = "Allow"

    actions = [
      "s3:GetObject",
      "s3:PutObject",
    ]

    resources = [
      "${aws_s3_bucket.main.arn}/*"
    ]
  }

  statement {
    effect = "Allow"

    actions = [
      "s3:ListBucket"
    ]

    resources = [
      aws_s3_bucket.main.arn
    ]
  }
}

# Usage
resource "aws_iam_role" "ec2" {
  name               = "ec2-role"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
}

resource "aws_iam_policy" "s3" {
  name   = "s3-access"
  policy = data.aws_iam_policy_document.s3_access.json
}
```

### AWS Caller Identity

```hcl
data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

data "aws_partition" "current" {}

locals {
  account_id = data.aws_caller_identity.current.account_id
  region     = data.aws_region.current.name
  partition  = data.aws_partition.current.partition

  # Construct ARN
  bucket_arn = "arn:${local.partition}:s3:::${var.bucket_name}"
}

output "account_info" {
  value = {
    account_id = data.aws_caller_identity.current.account_id
    arn        = data.aws_caller_identity.current.arn
    user_id    = data.aws_caller_identity.current.user_id
  }
}
```

### AWS EKS Cluster

```hcl
data "aws_eks_cluster" "main" {
  name = var.cluster_name
}

data "aws_eks_cluster_auth" "main" {
  name = var.cluster_name
}

# Use with Kubernetes provider
provider "kubernetes" {
  host                   = data.aws_eks_cluster.main.endpoint
  cluster_ca_certificate = base64decode(data.aws_eks_cluster.main.certificate_authority[0].data)
  token                  = data.aws_eks_cluster_auth.main.token
}
```

### AWS Secrets Manager

```hcl
data "aws_secretsmanager_secret" "db" {
  name = "production/database"
}

data "aws_secretsmanager_secret_version" "db" {
  secret_id = data.aws_secretsmanager_secret.db.id
}

locals {
  db_credentials = jsondecode(data.aws_secretsmanager_secret_version.db.secret_string)
}

# Usage
resource "aws_db_instance" "main" {
  username = local.db_credentials["username"]
  password = local.db_credentials["password"]
}
```

### AWS SSM Parameter

```hcl
data "aws_ssm_parameter" "db_host" {
  name = "/production/database/host"
}

data "aws_ssm_parameter" "db_password" {
  name            = "/production/database/password"
  with_decryption = true
}

# Fetch multiple parameters by path
data "aws_ssm_parameters_by_path" "config" {
  path            = "/production/config"
  with_decryption = true
}

# Usage
output "db_host" {
  value = data.aws_ssm_parameter.db_host.value
}
```

### Google Compute Image

```hcl
data "google_compute_image" "debian" {
  family  = "debian-11"
  project = "debian-cloud"
}

# Usage
resource "google_compute_instance" "web" {
  boot_disk {
    initialize_params {
      image = data.google_compute_image.debian.self_link
    }
  }
}
```

### Azure Resource Group

```hcl
data "azurerm_resource_group" "main" {
  name = var.resource_group_name
}

# Usage
resource "azurerm_virtual_network" "main" {
  resource_group_name = data.azurerm_resource_group.main.name
  location            = data.azurerm_resource_group.main.location
}
```

## Data Source with Remote State

```hcl
# Read outputs from another Terraform state
data "terraform_remote_state" "vpc" {
  backend = "s3"

  config = {
    bucket = "company-terraform-state"
    key    = "network/vpc/terraform.tfstate"
    region = "us-east-1"
  }
}

# Usage
resource "aws_instance" "web" {
  subnet_id              = data.terraform_remote_state.vpc.outputs.public_subnet_ids[0]
  vpc_security_group_ids = [data.terraform_remote_state.vpc.outputs.web_sg_id]
}
```

## External Data Source

```hcl
# Execute external program
data "external" "example" {
  program = ["python3", "${path.module}/scripts/get_data.py"]

  query = {
    environment = var.environment
    service     = "web"
  }
}

# Script must output JSON to stdout
# {"key1": "value1", "key2": "value2"}

output "external_data" {
  value = data.external.example.result
}
```

## HTTP Data Source

```hcl
data "http" "example" {
  url = "https://api.example.com/config"

  request_headers = {
    Accept = "application/json"
  }
}

locals {
  config = jsondecode(data.http.example.response_body)
}
```

## Local File Data Source

```hcl
# Read local file
data "local_file" "config" {
  filename = "${path.module}/config.json"
}

# Read sensitive file
data "local_sensitive_file" "private_key" {
  filename = "${path.module}/key.pem"
}

# Usage
locals {
  config = jsondecode(data.local_file.config.content)
}
```

## Template Data Sources

### Template File

```hcl
# templates/user_data.sh.tpl
#!/bin/bash
echo "Hello, ${name}!"
apt-get update
apt-get install -y ${packages}

# main.tf
data "template_file" "user_data" {
  template = file("${path.module}/templates/user_data.sh.tpl")

  vars = {
    name     = var.instance_name
    packages = join(" ", var.packages)
  }
}

# Usage
resource "aws_instance" "web" {
  user_data = data.template_file.user_data.rendered
}
```

### Templatefile Function (Preferred)

```hcl
# Modern approach using templatefile function
resource "aws_instance" "web" {
  user_data = templatefile("${path.module}/templates/user_data.sh.tpl", {
    name     = var.instance_name
    packages = var.packages
  })
}
```

## Data Source Dependencies

```hcl
# Explicit dependency on resource
data "aws_instance" "web" {
  filter {
    name   = "tag:Name"
    values = ["web-server"]
  }

  depends_on = [aws_instance.web]
}
```

## Conditional Data Sources

```hcl
# Only fetch if condition is true
data "aws_ami" "custom" {
  count = var.use_custom_ami ? 1 : 0

  owners = ["self"]

  filter {
    name   = "name"
    values = ["custom-ami-*"]
  }
}

# Usage with conditional
locals {
  ami_id = var.use_custom_ami ? data.aws_ami.custom[0].id : data.aws_ami.amazon_linux.id
}
```

## Best Practices

1. **Use Data Sources for Discovery**: Fetch existing resources instead of hardcoding IDs
2. **Filter Precisely**: Use specific filters to avoid ambiguous results
3. **Handle Multiple Results**: Use `most_recent = true` for AMIs
4. **Prefer Functions**: Use `templatefile()` instead of `template_file` data source
5. **Document Dependencies**: Make implicit dependencies explicit when needed
6. **Cache Awareness**: Data sources are read every apply; consider performance
7. **Error Handling**: Use `try()` function for optional data
