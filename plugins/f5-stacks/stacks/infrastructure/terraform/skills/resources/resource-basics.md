# Resource Basics

## Overview

Resources are the fundamental building blocks of Terraform configurations. Each resource block describes one or more infrastructure objects.

## Resource Block Syntax

```hcl
resource "<PROVIDER>_<TYPE>" "<NAME>" {
  # Configuration arguments
  argument_name = argument_value

  # Nested configuration block
  nested_block {
    nested_argument = value
  }
}
```

### Components

| Component | Description | Example |
|-----------|-------------|---------|
| Provider | Cloud provider prefix | `aws`, `google`, `azurerm` |
| Type | Resource type | `instance`, `bucket`, `vpc` |
| Name | Local identifier | `web`, `main`, `primary` |
| Arguments | Configuration options | `ami = "ami-123"` |

## Common Resource Patterns

### AWS EC2 Instance

```hcl
resource "aws_instance" "web" {
  ami           = "ami-0123456789abcdef0"
  instance_type = "t3.micro"

  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.web.id]

  root_block_device {
    volume_type           = "gp3"
    volume_size           = 20
    encrypted             = true
    delete_on_termination = true
  }

  tags = {
    Name        = "web-server"
    Environment = "production"
  }
}
```

### AWS S3 Bucket

```hcl
resource "aws_s3_bucket" "data" {
  bucket = "my-unique-bucket-name"

  tags = {
    Name = "Data Bucket"
  }
}

resource "aws_s3_bucket_versioning" "data" {
  bucket = aws_s3_bucket.data.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data" {
  bucket = aws_s3_bucket.data.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
```

### AWS VPC

```hcl
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "main-vpc"
  }
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "us-east-1a"
  map_public_ip_on_launch = true

  tags = {
    Name = "public-subnet"
    Type = "Public"
  }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "main-igw"
  }
}
```

### Google Compute Instance

```hcl
resource "google_compute_instance" "web" {
  name         = "web-server"
  machine_type = "e2-medium"
  zone         = "us-central1-a"

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-11"
      size  = 20
      type  = "pd-ssd"
    }
  }

  network_interface {
    network    = google_compute_network.main.name
    subnetwork = google_compute_subnetwork.public.name

    access_config {
      // Ephemeral public IP
    }
  }

  labels = {
    environment = "production"
  }
}
```

### Azure Virtual Machine

```hcl
resource "azurerm_linux_virtual_machine" "web" {
  name                = "web-server"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  size                = "Standard_B2s"
  admin_username      = "adminuser"

  network_interface_ids = [
    azurerm_network_interface.web.id,
  ]

  admin_ssh_key {
    username   = "adminuser"
    public_key = file("~/.ssh/id_rsa.pub")
  }

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-jammy"
    sku       = "22_04-lts"
    version   = "latest"
  }

  tags = {
    environment = "production"
  }
}
```

## Resource Attributes

### Input Arguments

```hcl
resource "aws_instance" "web" {
  # Required arguments
  ami           = "ami-0123456789"
  instance_type = "t3.micro"

  # Optional arguments with defaults
  monitoring = true

  # Computed-required (from other resources)
  subnet_id = aws_subnet.public.id
}
```

### Output Attributes

```hcl
# Reference computed attributes
output "instance_id" {
  value = aws_instance.web.id
}

output "public_ip" {
  value = aws_instance.web.public_ip
}

output "private_dns" {
  value = aws_instance.web.private_dns
}
```

## Resource Meta-Arguments

### count

```hcl
resource "aws_instance" "web" {
  count = 3

  ami           = "ami-0123456789"
  instance_type = "t3.micro"

  tags = {
    Name = "web-${count.index + 1}"
  }
}

# References
# aws_instance.web[0]
# aws_instance.web[1]
# aws_instance.web[2]

# Conditional creation
resource "aws_eip" "web" {
  count = var.create_eip ? 1 : 0

  instance = aws_instance.web[0].id
}
```

### for_each

```hcl
# With set
resource "aws_iam_user" "users" {
  for_each = toset(["alice", "bob", "charlie"])

  name = each.value
}

# With map
resource "aws_instance" "servers" {
  for_each = {
    web = "t3.micro"
    api = "t3.small"
    db  = "t3.medium"
  }

  ami           = "ami-0123456789"
  instance_type = each.value

  tags = {
    Name = each.key
  }
}

# References
# aws_iam_user.users["alice"]
# aws_instance.servers["web"]
```

### provider

```hcl
provider "aws" {
  region = "us-east-1"
}

provider "aws" {
  alias  = "west"
  region = "us-west-2"
}

# Use specific provider
resource "aws_instance" "west_coast" {
  provider = aws.west

  ami           = "ami-west-specific"
  instance_type = "t3.micro"
}
```

### depends_on

```hcl
resource "aws_instance" "web" {
  ami           = "ami-0123456789"
  instance_type = "t3.micro"

  # Explicit dependency
  depends_on = [
    aws_iam_role_policy.web,
    aws_security_group.web,
  ]
}
```

### lifecycle

```hcl
resource "aws_instance" "web" {
  ami           = "ami-0123456789"
  instance_type = "t3.micro"

  lifecycle {
    create_before_destroy = true
    prevent_destroy       = true
    ignore_changes        = [ami, tags]

    # Preconditions and postconditions (Terraform 1.2+)
    precondition {
      condition     = var.instance_type != "t3.nano"
      error_message = "Instance type must not be t3.nano"
    }

    postcondition {
      condition     = self.public_ip != ""
      error_message = "Instance must have a public IP"
    }
  }
}
```

## Nested Blocks

### Single Nested Block

```hcl
resource "aws_instance" "web" {
  ami           = "ami-0123456789"
  instance_type = "t3.micro"

  root_block_device {
    volume_size = 20
    encrypted   = true
  }
}
```

### Multiple Nested Blocks

```hcl
resource "aws_instance" "web" {
  ami           = "ami-0123456789"
  instance_type = "t3.micro"

  ebs_block_device {
    device_name = "/dev/sdb"
    volume_size = 100
  }

  ebs_block_device {
    device_name = "/dev/sdc"
    volume_size = 200
  }
}
```

### Dynamic Nested Blocks

```hcl
variable "ebs_volumes" {
  default = [
    { device = "/dev/sdb", size = 100 },
    { device = "/dev/sdc", size = 200 },
  ]
}

resource "aws_instance" "web" {
  ami           = "ami-0123456789"
  instance_type = "t3.micro"

  dynamic "ebs_block_device" {
    for_each = var.ebs_volumes

    content {
      device_name = ebs_block_device.value.device
      volume_size = ebs_block_device.value.size
      encrypted   = true
    }
  }
}
```

## Resource Addressing

```hcl
# Simple resource
aws_instance.web

# Indexed resource (count)
aws_instance.web[0]
aws_instance.web[2]

# Keyed resource (for_each)
aws_instance.servers["web"]
aws_instance.servers["api"]

# Module resource
module.vpc.aws_vpc.main
module.vpc.aws_subnet.public[0]

# Child module resource
module.network.module.vpc.aws_vpc.main
```

## Timeouts

```hcl
resource "aws_db_instance" "main" {
  engine         = "postgres"
  instance_class = "db.t3.micro"

  timeouts {
    create = "60m"
    update = "30m"
    delete = "30m"
  }
}
```

## Resource Behavior

### Create

```bash
# Plan shows creation
terraform plan

# + aws_instance.web will be created
#   + resource "aws_instance" "web" {
#       + ami           = "ami-0123456789"
#       + instance_type = "t3.micro"
#       + id            = (known after apply)
#     }
```

### Update

```bash
# ~ indicates update in-place
# -/+ indicates replace (destroy then create)

# ~ aws_instance.web will be updated in-place
#   ~ instance_type = "t3.micro" -> "t3.small"

# -/+ aws_instance.web must be replaced
#   ~ ami = "ami-old" -> "ami-new" # forces replacement
```

### Destroy

```bash
# - indicates destruction
terraform destroy

# - aws_instance.web will be destroyed
```

## Best Practices

1. **Naming**: Use descriptive, consistent names
2. **Tagging**: Always tag resources for organization
3. **Dependencies**: Prefer implicit over explicit dependencies
4. **Nested Blocks**: Use dynamic blocks for repetitive structures
5. **Meta-Arguments**: Use count/for_each for resource multiplication
6. **Lifecycle**: Use lifecycle rules to control resource behavior
7. **Timeouts**: Set appropriate timeouts for long-running operations
