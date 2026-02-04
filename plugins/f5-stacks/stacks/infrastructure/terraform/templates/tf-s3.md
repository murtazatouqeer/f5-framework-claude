---
name: tf-s3
description: Template for AWS S3 bucket with security best practices
applies_to: terraform
---

# AWS S3 Module Template

## Overview

Production-ready S3 bucket module with encryption, versioning, lifecycle rules,
replication, and security best practices.

## Directory Structure

```
modules/s3/
├── main.tf           # Bucket and core settings
├── encryption.tf     # Encryption configuration
├── lifecycle.tf      # Lifecycle rules
├── replication.tf    # Cross-region replication
├── policy.tf         # Bucket policies
├── variables.tf
├── outputs.tf
├── versions.tf
└── README.md
```

## versions.tf

```hcl
terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}
```

## variables.tf

```hcl
# =============================================================================
# Required Variables
# =============================================================================

variable "bucket_name" {
  description = "Name of the S3 bucket"
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$", var.bucket_name))
    error_message = "Bucket name must be 3-63 characters, lowercase, numbers, hyphens, periods."
  }
}

# =============================================================================
# Versioning
# =============================================================================

variable "versioning_enabled" {
  description = "Enable versioning"
  type        = bool
  default     = true
}

# =============================================================================
# Encryption
# =============================================================================

variable "encryption_type" {
  description = "Encryption type: SSE-S3, SSE-KMS, or SSE-C"
  type        = string
  default     = "SSE-S3"

  validation {
    condition     = contains(["SSE-S3", "SSE-KMS"], var.encryption_type)
    error_message = "Encryption type must be SSE-S3 or SSE-KMS."
  }
}

variable "kms_key_arn" {
  description = "KMS key ARN for SSE-KMS encryption"
  type        = string
  default     = null
}

variable "bucket_key_enabled" {
  description = "Enable S3 Bucket Key for KMS encryption"
  type        = bool
  default     = true
}

# =============================================================================
# Public Access
# =============================================================================

variable "block_public_acls" {
  description = "Block public ACLs"
  type        = bool
  default     = true
}

variable "block_public_policy" {
  description = "Block public bucket policies"
  type        = bool
  default     = true
}

variable "ignore_public_acls" {
  description = "Ignore public ACLs"
  type        = bool
  default     = true
}

variable "restrict_public_buckets" {
  description = "Restrict public bucket policies"
  type        = bool
  default     = true
}

# =============================================================================
# Lifecycle Rules
# =============================================================================

variable "lifecycle_rules" {
  description = "Lifecycle rules for the bucket"
  type = list(object({
    id      = string
    enabled = bool
    prefix  = optional(string, "")
    tags    = optional(map(string), {})

    transition = optional(list(object({
      days          = number
      storage_class = string
    })), [])

    expiration = optional(object({
      days                         = optional(number)
      expired_object_delete_marker = optional(bool)
    }))

    noncurrent_version_transition = optional(list(object({
      noncurrent_days = number
      storage_class   = string
    })), [])

    noncurrent_version_expiration = optional(object({
      noncurrent_days = number
    }))

    abort_incomplete_multipart_upload = optional(object({
      days_after_initiation = number
    }))
  }))
  default = []
}

# =============================================================================
# Replication
# =============================================================================

variable "enable_replication" {
  description = "Enable cross-region replication"
  type        = bool
  default     = false
}

variable "replication_destination_bucket_arn" {
  description = "ARN of the destination bucket for replication"
  type        = string
  default     = null
}

variable "replication_destination_storage_class" {
  description = "Storage class for replicated objects"
  type        = string
  default     = "STANDARD"
}

# =============================================================================
# Logging
# =============================================================================

variable "enable_logging" {
  description = "Enable access logging"
  type        = bool
  default     = false
}

variable "logging_target_bucket" {
  description = "Target bucket for access logs"
  type        = string
  default     = null
}

variable "logging_target_prefix" {
  description = "Prefix for access logs"
  type        = string
  default     = "logs/"
}

# =============================================================================
# CORS
# =============================================================================

variable "cors_rules" {
  description = "CORS rules for the bucket"
  type = list(object({
    allowed_headers = optional(list(string), ["*"])
    allowed_methods = list(string)
    allowed_origins = list(string)
    expose_headers  = optional(list(string), [])
    max_age_seconds = optional(number, 3000)
  }))
  default = []
}

# =============================================================================
# Tags
# =============================================================================

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
```

## main.tf

```hcl
locals {
  common_tags = merge(var.tags, {
    Module    = "s3"
    ManagedBy = "terraform"
  })
}

# =============================================================================
# S3 Bucket
# =============================================================================

resource "aws_s3_bucket" "main" {
  bucket = var.bucket_name

  tags = merge(local.common_tags, {
    Name = var.bucket_name
  })
}

# =============================================================================
# Versioning
# =============================================================================

resource "aws_s3_bucket_versioning" "main" {
  bucket = aws_s3_bucket.main.id

  versioning_configuration {
    status = var.versioning_enabled ? "Enabled" : "Suspended"
  }
}

# =============================================================================
# Public Access Block
# =============================================================================

resource "aws_s3_bucket_public_access_block" "main" {
  bucket = aws_s3_bucket.main.id

  block_public_acls       = var.block_public_acls
  block_public_policy     = var.block_public_policy
  ignore_public_acls      = var.ignore_public_acls
  restrict_public_buckets = var.restrict_public_buckets
}

# =============================================================================
# Ownership Controls
# =============================================================================

resource "aws_s3_bucket_ownership_controls" "main" {
  bucket = aws_s3_bucket.main.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }

  depends_on = [aws_s3_bucket_public_access_block.main]
}

# =============================================================================
# Logging
# =============================================================================

resource "aws_s3_bucket_logging" "main" {
  count = var.enable_logging ? 1 : 0

  bucket = aws_s3_bucket.main.id

  target_bucket = var.logging_target_bucket
  target_prefix = var.logging_target_prefix
}

# =============================================================================
# CORS Configuration
# =============================================================================

resource "aws_s3_bucket_cors_configuration" "main" {
  count = length(var.cors_rules) > 0 ? 1 : 0

  bucket = aws_s3_bucket.main.id

  dynamic "cors_rule" {
    for_each = var.cors_rules
    content {
      allowed_headers = cors_rule.value.allowed_headers
      allowed_methods = cors_rule.value.allowed_methods
      allowed_origins = cors_rule.value.allowed_origins
      expose_headers  = cors_rule.value.expose_headers
      max_age_seconds = cors_rule.value.max_age_seconds
    }
  }
}
```

## encryption.tf

```hcl
# =============================================================================
# Server-Side Encryption
# =============================================================================

resource "aws_s3_bucket_server_side_encryption_configuration" "main" {
  bucket = aws_s3_bucket.main.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = var.encryption_type == "SSE-KMS" ? "aws:kms" : "AES256"
      kms_master_key_id = var.encryption_type == "SSE-KMS" ? var.kms_key_arn : null
    }
    bucket_key_enabled = var.encryption_type == "SSE-KMS" ? var.bucket_key_enabled : null
  }
}
```

## lifecycle.tf

```hcl
# =============================================================================
# Lifecycle Rules
# =============================================================================

resource "aws_s3_bucket_lifecycle_configuration" "main" {
  count = length(var.lifecycle_rules) > 0 ? 1 : 0

  bucket = aws_s3_bucket.main.id

  dynamic "rule" {
    for_each = var.lifecycle_rules
    content {
      id     = rule.value.id
      status = rule.value.enabled ? "Enabled" : "Disabled"

      filter {
        and {
          prefix = rule.value.prefix
          tags   = rule.value.tags
        }
      }

      dynamic "transition" {
        for_each = rule.value.transition
        content {
          days          = transition.value.days
          storage_class = transition.value.storage_class
        }
      }

      dynamic "expiration" {
        for_each = rule.value.expiration != null ? [rule.value.expiration] : []
        content {
          days                         = expiration.value.days
          expired_object_delete_marker = expiration.value.expired_object_delete_marker
        }
      }

      dynamic "noncurrent_version_transition" {
        for_each = rule.value.noncurrent_version_transition
        content {
          noncurrent_days = noncurrent_version_transition.value.noncurrent_days
          storage_class   = noncurrent_version_transition.value.storage_class
        }
      }

      dynamic "noncurrent_version_expiration" {
        for_each = rule.value.noncurrent_version_expiration != null ? [rule.value.noncurrent_version_expiration] : []
        content {
          noncurrent_days = noncurrent_version_expiration.value.noncurrent_days
        }
      }

      dynamic "abort_incomplete_multipart_upload" {
        for_each = rule.value.abort_incomplete_multipart_upload != null ? [rule.value.abort_incomplete_multipart_upload] : []
        content {
          days_after_initiation = abort_incomplete_multipart_upload.value.days_after_initiation
        }
      }
    }
  }

  depends_on = [aws_s3_bucket_versioning.main]
}
```

## replication.tf

```hcl
# =============================================================================
# Replication Configuration
# =============================================================================

resource "aws_iam_role" "replication" {
  count = var.enable_replication ? 1 : 0

  name = "${var.bucket_name}-replication-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "s3.amazonaws.com"
      }
    }]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy" "replication" {
  count = var.enable_replication ? 1 : 0

  name = "${var.bucket_name}-replication-policy"
  role = aws_iam_role.replication[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "s3:GetReplicationConfiguration",
          "s3:ListBucket"
        ]
        Effect   = "Allow"
        Resource = aws_s3_bucket.main.arn
      },
      {
        Action = [
          "s3:GetObjectVersionForReplication",
          "s3:GetObjectVersionAcl",
          "s3:GetObjectVersionTagging"
        ]
        Effect   = "Allow"
        Resource = "${aws_s3_bucket.main.arn}/*"
      },
      {
        Action = [
          "s3:ReplicateObject",
          "s3:ReplicateDelete",
          "s3:ReplicateTags"
        ]
        Effect   = "Allow"
        Resource = "${var.replication_destination_bucket_arn}/*"
      }
    ]
  })
}

resource "aws_s3_bucket_replication_configuration" "main" {
  count = var.enable_replication ? 1 : 0

  bucket = aws_s3_bucket.main.id
  role   = aws_iam_role.replication[0].arn

  rule {
    id     = "entire-bucket"
    status = "Enabled"

    destination {
      bucket        = var.replication_destination_bucket_arn
      storage_class = var.replication_destination_storage_class
    }

    delete_marker_replication {
      status = "Enabled"
    }
  }

  depends_on = [aws_s3_bucket_versioning.main]
}
```

## policy.tf

```hcl
# =============================================================================
# Bucket Policy (Example: Enforce HTTPS)
# =============================================================================

resource "aws_s3_bucket_policy" "enforce_https" {
  bucket = aws_s3_bucket.main.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "EnforceHTTPS"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:*"
        Resource = [
          aws_s3_bucket.main.arn,
          "${aws_s3_bucket.main.arn}/*"
        ]
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
      }
    ]
  })

  depends_on = [aws_s3_bucket_public_access_block.main]
}
```

## outputs.tf

```hcl
# =============================================================================
# Bucket Outputs
# =============================================================================

output "bucket_id" {
  description = "Bucket ID"
  value       = aws_s3_bucket.main.id
}

output "bucket_arn" {
  description = "Bucket ARN"
  value       = aws_s3_bucket.main.arn
}

output "bucket_domain_name" {
  description = "Bucket domain name"
  value       = aws_s3_bucket.main.bucket_domain_name
}

output "bucket_regional_domain_name" {
  description = "Bucket regional domain name"
  value       = aws_s3_bucket.main.bucket_regional_domain_name
}

output "bucket_region" {
  description = "Bucket region"
  value       = aws_s3_bucket.main.region
}

# =============================================================================
# Replication Outputs
# =============================================================================

output "replication_role_arn" {
  description = "Replication IAM role ARN"
  value       = try(aws_iam_role.replication[0].arn, null)
}
```

## Usage Examples

### Standard Bucket

```hcl
module "app_bucket" {
  source = "../../modules/s3"

  bucket_name        = "myapp-prod-assets"
  versioning_enabled = true
  encryption_type    = "SSE-S3"

  lifecycle_rules = [
    {
      id      = "archive-old-versions"
      enabled = true
      noncurrent_version_transition = [
        {
          noncurrent_days = 30
          storage_class   = "STANDARD_IA"
        },
        {
          noncurrent_days = 90
          storage_class   = "GLACIER"
        }
      ]
      noncurrent_version_expiration = {
        noncurrent_days = 365
      }
    }
  ]

  tags = {
    Environment = "production"
    Project     = "myapp"
  }
}
```

### Bucket with KMS Encryption

```hcl
module "secure_bucket" {
  source = "../../modules/s3"

  bucket_name        = "myapp-prod-secure"
  versioning_enabled = true
  encryption_type    = "SSE-KMS"
  kms_key_arn        = aws_kms_key.s3.arn
  bucket_key_enabled = true

  tags = {
    Environment = "production"
    Compliance  = "PCI-DSS"
  }
}
```

### Bucket with Cross-Region Replication

```hcl
module "primary_bucket" {
  source = "../../modules/s3"

  bucket_name        = "myapp-prod-primary"
  versioning_enabled = true

  enable_replication                    = true
  replication_destination_bucket_arn    = "arn:aws:s3:::myapp-prod-replica"
  replication_destination_storage_class = "STANDARD"

  tags = {
    Environment = "production"
    DR          = "enabled"
  }
}
```

### Static Website Bucket

```hcl
module "website_bucket" {
  source = "../../modules/s3"

  bucket_name             = "myapp-website"
  versioning_enabled      = false
  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false

  cors_rules = [
    {
      allowed_methods = ["GET", "HEAD"]
      allowed_origins = ["https://myapp.com"]
      allowed_headers = ["*"]
      max_age_seconds = 3600
    }
  ]

  tags = {
    Environment = "production"
    Type        = "website"
  }
}
```
