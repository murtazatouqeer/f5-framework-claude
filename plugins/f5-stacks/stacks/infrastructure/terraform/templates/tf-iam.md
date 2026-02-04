---
name: tf-iam
description: Template for AWS IAM roles and policies
applies_to: terraform
---

# AWS IAM Module Template

## Overview

Production-ready IAM module for creating roles, policies, users, and groups
following AWS security best practices and least privilege principle.

## Directory Structure

```
modules/iam/
├── role/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── versions.tf
├── policy/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── versions.tf
├── user/
│   └── ...
└── group/
    └── ...
```

## IAM Role Module

### variables.tf

```hcl
# =============================================================================
# Required Variables
# =============================================================================

variable "name" {
  description = "Name of the IAM role"
  type        = string

  validation {
    condition     = can(regex("^[a-zA-Z][a-zA-Z0-9+=,.@_-]{0,63}$", var.name))
    error_message = "Role name must be 1-64 characters, alphanumeric with +=,.@_-"
  }
}

variable "trusted_service" {
  description = "AWS service that can assume this role"
  type        = string
  default     = null
}

variable "trusted_accounts" {
  description = "AWS account IDs that can assume this role"
  type        = list(string)
  default     = []
}

variable "trusted_roles" {
  description = "IAM role ARNs that can assume this role"
  type        = list(string)
  default     = []
}

# =============================================================================
# OIDC Configuration (for IRSA)
# =============================================================================

variable "oidc_provider_arn" {
  description = "OIDC provider ARN for web identity federation"
  type        = string
  default     = null
}

variable "oidc_conditions" {
  description = "Conditions for OIDC-based role assumption"
  type = map(object({
    test     = string
    variable = string
    values   = list(string)
  }))
  default = {}
}

# =============================================================================
# Policy Configuration
# =============================================================================

variable "managed_policy_arns" {
  description = "List of managed policy ARNs to attach"
  type        = list(string)
  default     = []
}

variable "inline_policies" {
  description = "Map of inline policy names to policy documents"
  type        = map(string)
  default     = {}
}

variable "policy_statements" {
  description = "List of policy statements for auto-generated inline policy"
  type = list(object({
    sid       = optional(string)
    effect    = string
    actions   = list(string)
    resources = list(string)
    conditions = optional(list(object({
      test     = string
      variable = string
      values   = list(string)
    })), [])
  }))
  default = []
}

# =============================================================================
# Optional Configuration
# =============================================================================

variable "description" {
  description = "Description of the IAM role"
  type        = string
  default     = ""
}

variable "path" {
  description = "Path for the IAM role"
  type        = string
  default     = "/"
}

variable "max_session_duration" {
  description = "Maximum session duration in seconds"
  type        = number
  default     = 3600

  validation {
    condition     = var.max_session_duration >= 3600 && var.max_session_duration <= 43200
    error_message = "Max session duration must be between 3600 and 43200 seconds."
  }
}

variable "permissions_boundary" {
  description = "ARN of the permissions boundary policy"
  type        = string
  default     = null
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
```

### main.tf

```hcl
locals {
  common_tags = merge(var.tags, {
    Module    = "iam-role"
    ManagedBy = "terraform"
  })

  # Build trust policy based on inputs
  trust_policy = {
    Version = "2012-10-17"
    Statement = concat(
      # Service trust
      var.trusted_service != null ? [{
        Effect = "Allow"
        Principal = {
          Service = var.trusted_service
        }
        Action = "sts:AssumeRole"
      }] : [],

      # Account trust
      length(var.trusted_accounts) > 0 ? [{
        Effect = "Allow"
        Principal = {
          AWS = [for account in var.trusted_accounts : "arn:aws:iam::${account}:root"]
        }
        Action = "sts:AssumeRole"
      }] : [],

      # Role trust
      length(var.trusted_roles) > 0 ? [{
        Effect = "Allow"
        Principal = {
          AWS = var.trusted_roles
        }
        Action = "sts:AssumeRole"
      }] : [],

      # OIDC trust (IRSA)
      var.oidc_provider_arn != null ? [{
        Effect = "Allow"
        Principal = {
          Federated = var.oidc_provider_arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          for key, condition in var.oidc_conditions : condition.test => {
            (condition.variable) = condition.values
          }
        }
      }] : []
    )
  }
}

# =============================================================================
# IAM Role
# =============================================================================

resource "aws_iam_role" "main" {
  name                 = var.name
  description          = var.description
  path                 = var.path
  max_session_duration = var.max_session_duration
  permissions_boundary = var.permissions_boundary

  assume_role_policy = jsonencode(local.trust_policy)

  tags = local.common_tags
}

# =============================================================================
# Managed Policy Attachments
# =============================================================================

resource "aws_iam_role_policy_attachment" "managed" {
  for_each = toset(var.managed_policy_arns)

  role       = aws_iam_role.main.name
  policy_arn = each.value
}

# =============================================================================
# Inline Policies
# =============================================================================

resource "aws_iam_role_policy" "inline" {
  for_each = var.inline_policies

  name   = each.key
  role   = aws_iam_role.main.id
  policy = each.value
}

# =============================================================================
# Auto-generated Policy from Statements
# =============================================================================

resource "aws_iam_role_policy" "statements" {
  count = length(var.policy_statements) > 0 ? 1 : 0

  name = "${var.name}-policy"
  role = aws_iam_role.main.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      for stmt in var.policy_statements : {
        Sid      = stmt.sid
        Effect   = stmt.effect
        Action   = stmt.actions
        Resource = stmt.resources
        Condition = length(stmt.conditions) > 0 ? {
          for cond in stmt.conditions : cond.test => {
            (cond.variable) = cond.values
          }
        } : null
      }
    ]
  })
}
```

### outputs.tf

```hcl
output "role_arn" {
  description = "IAM role ARN"
  value       = aws_iam_role.main.arn
}

output "role_name" {
  description = "IAM role name"
  value       = aws_iam_role.main.name
}

output "role_id" {
  description = "IAM role ID"
  value       = aws_iam_role.main.id
}

output "role_unique_id" {
  description = "IAM role unique ID"
  value       = aws_iam_role.main.unique_id
}
```

## Common IAM Patterns

### EC2 Instance Role

```hcl
module "ec2_role" {
  source = "../../modules/iam/role"

  name            = "myapp-ec2-role"
  description     = "Role for EC2 instances"
  trusted_service = "ec2.amazonaws.com"

  managed_policy_arns = [
    "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore",
    "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
  ]

  policy_statements = [
    {
      sid       = "S3Access"
      effect    = "Allow"
      actions   = ["s3:GetObject", "s3:ListBucket"]
      resources = [
        "arn:aws:s3:::myapp-config",
        "arn:aws:s3:::myapp-config/*"
      ]
    }
  ]

  tags = {
    Environment = "production"
  }
}

resource "aws_iam_instance_profile" "ec2" {
  name = "myapp-ec2-profile"
  role = module.ec2_role.role_name
}
```

### Lambda Execution Role

```hcl
module "lambda_role" {
  source = "../../modules/iam/role"

  name            = "myapp-lambda-role"
  description     = "Execution role for Lambda functions"
  trusted_service = "lambda.amazonaws.com"

  managed_policy_arns = [
    "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
    "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
  ]

  policy_statements = [
    {
      sid       = "DynamoDBAccess"
      effect    = "Allow"
      actions   = [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:Query"
      ]
      resources = ["arn:aws:dynamodb:*:*:table/myapp-*"]
    },
    {
      sid       = "SecretsManagerAccess"
      effect    = "Allow"
      actions   = ["secretsmanager:GetSecretValue"]
      resources = ["arn:aws:secretsmanager:*:*:secret:myapp/*"]
    }
  ]

  tags = {
    Environment = "production"
  }
}
```

### EKS IRSA Role

```hcl
module "app_irsa_role" {
  source = "../../modules/iam/role"

  name        = "myapp-eks-pod-role"
  description = "IRSA role for myapp pods"

  oidc_provider_arn = module.eks.oidc_provider_arn
  oidc_conditions = {
    sub = {
      test     = "StringEquals"
      variable = "${replace(module.eks.oidc_provider_url, "https://", "")}:sub"
      values   = ["system:serviceaccount:myapp:myapp-sa"]
    }
    aud = {
      test     = "StringEquals"
      variable = "${replace(module.eks.oidc_provider_url, "https://", "")}:aud"
      values   = ["sts.amazonaws.com"]
    }
  }

  policy_statements = [
    {
      sid       = "S3Access"
      effect    = "Allow"
      actions   = ["s3:GetObject", "s3:PutObject"]
      resources = ["arn:aws:s3:::myapp-data/*"]
    },
    {
      sid       = "SQSAccess"
      effect    = "Allow"
      actions   = ["sqs:SendMessage", "sqs:ReceiveMessage", "sqs:DeleteMessage"]
      resources = ["arn:aws:sqs:*:*:myapp-*"]
    }
  ]

  tags = {
    Environment = "production"
  }
}
```

### Cross-Account Role

```hcl
module "cross_account_role" {
  source = "../../modules/iam/role"

  name             = "cross-account-deploy-role"
  description      = "Role for cross-account deployments"
  trusted_accounts = ["123456789012", "234567890123"]

  managed_policy_arns = [
    "arn:aws:iam::aws:policy/AmazonECS_FullAccess"
  ]

  policy_statements = [
    {
      sid       = "ECRPull"
      effect    = "Allow"
      actions   = [
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:BatchCheckLayerAvailability"
      ]
      resources = ["*"]
    }
  ]

  tags = {
    Environment = "production"
    Purpose     = "cross-account"
  }
}
```

### GitHub Actions OIDC Role

```hcl
# OIDC Provider for GitHub
resource "aws_iam_openid_connect_provider" "github" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"]
}

module "github_actions_role" {
  source = "../../modules/iam/role"

  name        = "github-actions-deploy-role"
  description = "Role for GitHub Actions deployments"

  oidc_provider_arn = aws_iam_openid_connect_provider.github.arn
  oidc_conditions = {
    sub = {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:myorg/myrepo:*"]
    }
    aud = {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }
  }

  managed_policy_arns = [
    "arn:aws:iam::aws:policy/AmazonECS_FullAccess"
  ]

  policy_statements = [
    {
      sid       = "ECRPush"
      effect    = "Allow"
      actions   = [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload"
      ]
      resources = ["*"]
    }
  ]

  tags = {
    Environment = "production"
    CI          = "github-actions"
  }
}
```

## IAM Policy Module

### Simple Policy

```hcl
module "s3_read_policy" {
  source = "../../modules/iam/policy"

  name        = "myapp-s3-read-policy"
  description = "Read-only access to myapp S3 bucket"

  policy_statements = [
    {
      effect    = "Allow"
      actions   = ["s3:GetObject", "s3:ListBucket"]
      resources = [
        "arn:aws:s3:::myapp-data",
        "arn:aws:s3:::myapp-data/*"
      ]
    }
  ]
}
```

### Complex Policy with Conditions

```hcl
module "admin_policy" {
  source = "../../modules/iam/policy"

  name        = "myapp-admin-policy"
  description = "Admin policy with MFA and IP restrictions"

  policy_statements = [
    {
      sid       = "AllowAllWithMFA"
      effect    = "Allow"
      actions   = ["*"]
      resources = ["*"]
      conditions = [
        {
          test     = "Bool"
          variable = "aws:MultiFactorAuthPresent"
          values   = ["true"]
        },
        {
          test     = "IpAddress"
          variable = "aws:SourceIp"
          values   = ["10.0.0.0/8", "192.168.0.0/16"]
        }
      ]
    },
    {
      sid       = "DenyDeleteProtectedResources"
      effect    = "Deny"
      actions   = ["*:Delete*", "*:Remove*"]
      resources = ["*"]
      conditions = [
        {
          test     = "StringEquals"
          variable = "aws:ResourceTag/Protected"
          values   = ["true"]
        }
      ]
    }
  ]
}
```

## Security Best Practices

1. **Least Privilege**: Grant minimum required permissions
2. **Use Conditions**: Add MFA, IP restrictions, time-based access
3. **Resource Scoping**: Avoid `*` in resources when possible
4. **Permission Boundaries**: Use for delegated administration
5. **Regular Review**: Audit and rotate unused credentials
6. **Service-Linked Roles**: Use when available for AWS services
7. **Session Tags**: Pass attributes for fine-grained access control
