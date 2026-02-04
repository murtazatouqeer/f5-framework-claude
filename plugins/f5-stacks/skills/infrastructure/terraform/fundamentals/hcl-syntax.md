# HCL Syntax

## Overview

HashiCorp Configuration Language (HCL) is the declarative language used by Terraform for infrastructure configuration.

## Basic Syntax Elements

### Comments

```hcl
# Single line comment

// Alternative single line comment (less common)

/*
Multi-line
comment block
*/
```

### Identifiers

```hcl
# Valid identifiers
resource "aws_instance" "web_server" {}
variable "instance_count" {}
local.my_value

# Identifiers must:
# - Start with letter or underscore
# - Contain letters, digits, underscores, hyphens
```

### Arguments and Attributes

```hcl
# Argument (configuration input)
resource "aws_instance" "web" {
  ami           = "ami-0123456789"  # Argument
  instance_type = "t3.micro"        # Argument
}

# Attribute (computed output)
output "instance_id" {
  value = aws_instance.web.id  # Attribute reference
}
```

## Data Types

### Primitive Types

```hcl
# String
name = "web-server"
multiline = <<-EOT
  This is a
  multiline string
EOT

# Number
count = 3
ratio = 0.75

# Boolean
enabled = true
disabled = false
```

### Complex Types

```hcl
# List (ordered sequence)
availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]

# Set (unordered unique values)
users = toset(["alice", "bob", "charlie"])

# Map (key-value pairs)
tags = {
  Name        = "web-server"
  Environment = "production"
}

# Object (structured type)
variable "instance" {
  type = object({
    ami           = string
    instance_type = string
    tags          = map(string)
  })
}

# Tuple (fixed-length sequence with element types)
variable "config" {
  type = tuple([string, number, bool])
  default = ["web", 3, true]
}
```

### Type Constraints

```hcl
variable "string_var" {
  type = string
}

variable "number_var" {
  type = number
}

variable "bool_var" {
  type = bool
}

variable "list_of_strings" {
  type = list(string)
}

variable "map_of_numbers" {
  type = map(number)
}

variable "any_type" {
  type = any
}

variable "optional_fields" {
  type = object({
    required = string
    optional = optional(string, "default")
  })
}
```

## String Operations

### String Interpolation

```hcl
locals {
  name = "web"
  env  = "prod"

  # Simple interpolation
  full_name = "${local.name}-${local.env}"

  # Expression interpolation
  instance_type = "${var.environment == "prod" ? "t3.large" : "t3.micro"}"
}
```

### Heredoc Strings

```hcl
# Standard heredoc (preserves indentation)
user_data = <<EOF
#!/bin/bash
echo "Hello World"
apt-get update
EOF

# Indented heredoc (strips leading whitespace)
user_data = <<-EOF
  #!/bin/bash
  echo "Hello World"
  apt-get update
EOF
```

### String Functions

```hcl
locals {
  # Case functions
  upper = upper("hello")           # "HELLO"
  lower = lower("HELLO")           # "hello"
  title = title("hello world")     # "Hello World"

  # Manipulation
  trimmed    = trim("  hello  ", " ")    # "hello"
  replaced   = replace("hello", "l", "L") # "heLLo"
  substring  = substr("hello", 0, 3)      # "hel"

  # Joining and splitting
  joined = join("-", ["a", "b", "c"])  # "a-b-c"
  split  = split("-", "a-b-c")         # ["a", "b", "c"]

  # Formatting
  formatted = format("Hello, %s!", "World")      # "Hello, World!"
  list_fmt  = formatlist("item-%s", ["a", "b"])  # ["item-a", "item-b"]
}
```

## Collection Operations

### List Functions

```hcl
locals {
  list = ["a", "b", "c", "d"]

  length    = length(local.list)           # 4
  element   = element(local.list, 1)       # "b"
  index     = index(local.list, "c")       # 2
  contains  = contains(local.list, "b")    # true

  concat    = concat(["a"], ["b", "c"])    # ["a", "b", "c"]
  flatten   = flatten([["a"], ["b", "c"]]) # ["a", "b", "c"]
  distinct  = distinct(["a", "a", "b"])    # ["a", "b"]
  reverse   = reverse(["a", "b", "c"])     # ["c", "b", "a"]
  sort      = sort(["c", "a", "b"])        # ["a", "b", "c"]

  slice     = slice(local.list, 1, 3)      # ["b", "c"]
  compact   = compact(["a", "", "b", null]) # ["a", "b"]
}
```

### Map Functions

```hcl
locals {
  map = {
    a = 1
    b = 2
    c = 3
  }

  keys   = keys(local.map)            # ["a", "b", "c"]
  values = values(local.map)          # [1, 2, 3]
  lookup = lookup(local.map, "a", 0)  # 1

  merged = merge(
    { a = 1 },
    { b = 2 }
  )  # { a = 1, b = 2 }

  zipmap = zipmap(
    ["a", "b"],
    [1, 2]
  )  # { a = 1, b = 2 }
}
```

## Expressions

### For Expressions

```hcl
locals {
  list = ["a", "b", "c"]
  map  = { a = 1, b = 2, c = 3 }

  # List to list
  upper_list = [for s in local.list : upper(s)]
  # ["A", "B", "C"]

  # List to map
  list_to_map = { for s in local.list : s => upper(s) }
  # { a = "A", b = "B", c = "C" }

  # Map to list
  map_to_list = [for k, v in local.map : "${k}=${v}"]
  # ["a=1", "b=2", "c=3"]

  # Map to map
  doubled = { for k, v in local.map : k => v * 2 }
  # { a = 2, b = 4, c = 6 }

  # With filtering
  filtered = [for s in local.list : s if s != "b"]
  # ["a", "c"]

  # Nested
  flattened = flatten([
    for env in ["dev", "prod"] : [
      for app in ["web", "api"] : "${env}-${app}"
    ]
  ])
  # ["dev-web", "dev-api", "prod-web", "prod-api"]
}
```

### Conditional Expressions

```hcl
locals {
  # Ternary operator
  instance_type = var.environment == "prod" ? "t3.large" : "t3.micro"

  # Nested conditions
  size = (
    var.environment == "prod" ? "large" :
    var.environment == "staging" ? "medium" :
    "small"
  )

  # With null
  value = var.input != null ? var.input : "default"

  # Coalesce (first non-null)
  result = coalesce(var.a, var.b, "default")
}
```

### Splat Expressions

```hcl
# Full splat (equivalent to for expression)
instance_ids = aws_instance.web[*].id

# Legacy splat (list resources only)
instance_ids = aws_instance.web.*.id

# Splat with nested attributes
public_ips = aws_instance.web[*].public_ip

# Equivalent for expression
instance_ids = [for i in aws_instance.web : i.id]
```

## Operators

### Arithmetic

```hcl
locals {
  add      = 5 + 3   # 8
  subtract = 5 - 3   # 2
  multiply = 5 * 3   # 15
  divide   = 6 / 3   # 2
  modulo   = 5 % 3   # 2
  negate   = -5      # -5
}
```

### Comparison

```hcl
locals {
  equal        = 5 == 5   # true
  not_equal    = 5 != 3   # true
  less         = 3 < 5    # true
  less_equal   = 5 <= 5   # true
  greater      = 5 > 3    # true
  greater_eq   = 5 >= 5   # true
}
```

### Logical

```hcl
locals {
  and = true && false  # false
  or  = true || false  # true
  not = !true          # false
}
```

## Blocks

### Resource Block

```hcl
resource "aws_instance" "web" {
  ami           = "ami-0123456789"
  instance_type = "t3.micro"

  # Nested block
  root_block_device {
    volume_size = 20
    encrypted   = true
  }

  # Multiple nested blocks
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

### Dynamic Block

```hcl
variable "ports" {
  default = [80, 443, 8080]
}

resource "aws_security_group" "web" {
  name = "web-sg"

  dynamic "ingress" {
    for_each = var.ports

    content {
      from_port   = ingress.value
      to_port     = ingress.value
      protocol    = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
    }
  }
}
```

## Special Values

```hcl
locals {
  # Null - absence of value
  optional_value = null

  # Path references
  module_path = path.module
  root_path   = path.root
  cwd_path    = path.cwd

  # Terraform metadata
  workspace = terraform.workspace
}
```

## Type Conversion Functions

```hcl
locals {
  # String conversions
  to_string = tostring(123)        # "123"

  # Number conversions
  to_number = tonumber("123")      # 123

  # Boolean conversions
  to_bool = tobool("true")         # true

  # Collection conversions
  to_list = tolist(toset(["a"]))   # ["a"]
  to_set  = toset(["a", "a"])      # toset(["a"])
  to_map  = tomap({ a = 1 })       # { a = 1 }

  # JSON encoding
  json_encode = jsonencode({ a = 1 })
  json_decode = jsondecode("{\"a\":1}")

  # YAML encoding
  yaml_encode = yamlencode({ a = 1 })
  yaml_decode = yamldecode("a: 1")
}
```
