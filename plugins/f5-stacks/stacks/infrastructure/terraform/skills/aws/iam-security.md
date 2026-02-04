# AWS IAM Security

## Overview

AWS Identity and Access Management (IAM) enables secure access control to AWS services and resources. Terraform provides comprehensive support for IAM configuration.

## IAM Users

### Basic User

```hcl
resource "aws_iam_user" "developer" {
  name = "developer"
  path = "/users/"

  tags = {
    Team = "Engineering"
  }
}

resource "aws_iam_access_key" "developer" {
  user = aws_iam_user.developer.name
}
```

### User with Console Access

```hcl
resource "aws_iam_user" "admin" {
  name          = "admin"
  path          = "/admins/"
  force_destroy = true

  tags = {
    Role = "Administrator"
  }
}

resource "aws_iam_user_login_profile" "admin" {
  user                    = aws_iam_user.admin.name
  password_reset_required = true
}

output "admin_password" {
  value     = aws_iam_user_login_profile.admin.password
  sensitive = true
}
```

## IAM Groups

```hcl
resource "aws_iam_group" "developers" {
  name = "developers"
  path = "/groups/"
}

resource "aws_iam_group_membership" "developers" {
  name  = "developers-membership"
  group = aws_iam_group.developers.name

  users = [
    aws_iam_user.developer.name,
  ]
}

resource "aws_iam_group_policy_attachment" "developers" {
  group      = aws_iam_group.developers.name
  policy_arn = "arn:aws:iam::aws:policy/PowerUserAccess"
}
```

## IAM Roles

### EC2 Instance Role

```hcl
resource "aws_iam_role" "ec2" {
  name = "${var.project}-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })

  tags = {
    Name = "${var.project}-ec2-role"
  }
}

resource "aws_iam_instance_profile" "ec2" {
  name = "${var.project}-ec2-profile"
  role = aws_iam_role.ec2.name
}

resource "aws_iam_role_policy_attachment" "ec2_ssm" {
  role       = aws_iam_role.ec2.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}
```

### Lambda Execution Role

```hcl
resource "aws_iam_role" "lambda" {
  name = "${var.project}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "lambda_vpc" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}
```

### Cross-Account Role

```hcl
resource "aws_iam_role" "cross_account" {
  name = "CrossAccountRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        AWS = "arn:aws:iam::${var.trusted_account_id}:root"
      }
      Condition = {
        StringEquals = {
          "sts:ExternalId" = var.external_id
        }
      }
    }]
  })
}
```

### Service-Linked Role

```hcl
resource "aws_iam_service_linked_role" "elasticache" {
  aws_service_name = "elasticache.amazonaws.com"
}
```

## IAM Policies

### Inline Policy

```hcl
resource "aws_iam_role_policy" "custom" {
  name = "${var.project}-custom-policy"
  role = aws_iam_role.ec2.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject"
        ]
        Resource = "${aws_s3_bucket.data.arn}/*"
      }
    ]
  })
}
```

### Managed Policy

```hcl
resource "aws_iam_policy" "custom" {
  name        = "${var.project}-custom-policy"
  path        = "/"
  description = "Custom policy for ${var.project}"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "S3Access"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = [
          "${aws_s3_bucket.data.arn}/*"
        ]
      },
      {
        Sid    = "S3ListBucket"
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.data.arn
        ]
      }
    ]
  })

  tags = {
    Name = "${var.project}-custom-policy"
  }
}

resource "aws_iam_role_policy_attachment" "custom" {
  role       = aws_iam_role.ec2.name
  policy_arn = aws_iam_policy.custom.arn
}
```

### Policy Document Data Source

```hcl
data "aws_iam_policy_document" "assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

data "aws_iam_policy_document" "lambda" {
  statement {
    sid    = "CloudWatchLogs"
    effect = "Allow"

    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]

    resources = ["arn:aws:logs:*:*:*"]
  }

  statement {
    sid    = "S3Access"
    effect = "Allow"

    actions = [
      "s3:GetObject"
    ]

    resources = [
      "${aws_s3_bucket.data.arn}/*"
    ]

    condition {
      test     = "StringEquals"
      variable = "s3:ExistingObjectTag/public"
      values   = ["true"]
    }
  }
}

resource "aws_iam_role" "lambda" {
  name               = "${var.project}-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
}

resource "aws_iam_policy" "lambda" {
  name   = "${var.project}-lambda-policy"
  policy = data.aws_iam_policy_document.lambda.json
}
```

## OIDC Provider (GitHub Actions)

```hcl
# GitHub Actions OIDC provider
resource "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"

  client_id_list = ["sts.amazonaws.com"]

  thumbprint_list = [
    "6938fd4d98bab03faadb97b34396831e3780aea1"
  ]
}

# Role for GitHub Actions
resource "aws_iam_role" "github_actions" {
  name = "github-actions-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Federated = aws_iam_openid_connect_provider.github.arn
      }
      Action = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
        }
        StringLike = {
          "token.actions.githubusercontent.com:sub" = "repo:${var.github_org}/${var.github_repo}:*"
        }
      }
    }]
  })
}
```

## Password Policy

```hcl
resource "aws_iam_account_password_policy" "strict" {
  minimum_password_length        = 16
  require_lowercase_characters   = true
  require_numbers                = true
  require_uppercase_characters   = true
  require_symbols                = true
  allow_users_to_change_password = true
  max_password_age               = 90
  password_reuse_prevention      = 12
  hard_expiry                    = false
}
```

## Permission Boundaries

```hcl
resource "aws_iam_policy" "boundary" {
  name = "PermissionBoundary"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowedServices"
        Effect = "Allow"
        Action = [
          "ec2:*",
          "s3:*",
          "rds:*",
          "lambda:*"
        ]
        Resource = "*"
      },
      {
        Sid    = "DenyIAMChanges"
        Effect = "Deny"
        Action = [
          "iam:CreateUser",
          "iam:DeleteUser",
          "iam:CreateRole",
          "iam:DeleteRole"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role" "developer" {
  name                 = "DeveloperRole"
  permissions_boundary = aws_iam_policy.boundary.arn

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
      }
    }]
  })
}
```

## Security Best Practices

### Deny Statements

```hcl
data "aws_iam_policy_document" "deny_root_actions" {
  statement {
    sid    = "DenyRootAccountUsage"
    effect = "Deny"

    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"]
    }

    actions   = ["*"]
    resources = ["*"]

    condition {
      test     = "Bool"
      variable = "aws:MultiFactorAuthPresent"
      values   = ["false"]
    }
  }
}
```

### MFA Required

```hcl
data "aws_iam_policy_document" "require_mfa" {
  statement {
    sid    = "DenyAllExceptMFA"
    effect = "Deny"

    actions   = ["*"]
    resources = ["*"]

    condition {
      test     = "BoolIfExists"
      variable = "aws:MultiFactorAuthPresent"
      values   = ["false"]
    }
  }
}
```

### Least Privilege Example

```hcl
# Instead of s3:*
data "aws_iam_policy_document" "least_privilege_s3" {
  statement {
    sid    = "ReadOnlyAccess"
    effect = "Allow"

    actions = [
      "s3:GetObject",
      "s3:GetObjectVersion",
      "s3:GetObjectTagging"
    ]

    resources = [
      "${aws_s3_bucket.data.arn}/read-only/*"
    ]
  }

  statement {
    sid    = "ReadWriteAccess"
    effect = "Allow"

    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject"
    ]

    resources = [
      "${aws_s3_bucket.data.arn}/uploads/*"
    ]
  }
}
```

## Outputs

```hcl
output "role_arn" {
  description = "IAM role ARN"
  value       = aws_iam_role.ec2.arn
}

output "instance_profile_name" {
  description = "Instance profile name"
  value       = aws_iam_instance_profile.ec2.name
}

output "policy_arn" {
  description = "Custom policy ARN"
  value       = aws_iam_policy.custom.arn
}
```
