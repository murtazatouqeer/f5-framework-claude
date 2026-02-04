---
name: tf-rds
description: Template for AWS RDS database with security best practices
applies_to: terraform
---

# AWS RDS Module Template

## Overview

Production-ready RDS module with encryption, monitoring, automated backups,
and security best practices.

## Directory Structure

```
modules/rds/
├── main.tf           # RDS instance
├── security.tf       # Security group
├── monitoring.tf     # Enhanced monitoring, CloudWatch
├── parameters.tf     # Parameter groups
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
    random = {
      source  = "hashicorp/random"
      version = ">= 3.0"
    }
  }
}
```

## variables.tf

```hcl
# =============================================================================
# Required Variables
# =============================================================================

variable "name" {
  description = "Name of the RDS instance"
  type        = string

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]*$", var.name))
    error_message = "Name must start with letter, contain only lowercase, numbers, hyphens."
  }
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "subnet_ids" {
  description = "Subnet IDs for DB subnet group"
  type        = list(string)

  validation {
    condition     = length(var.subnet_ids) >= 2
    error_message = "At least 2 subnet IDs required for Multi-AZ."
  }
}

# =============================================================================
# Engine Configuration
# =============================================================================

variable "engine" {
  description = "Database engine"
  type        = string
  default     = "postgres"

  validation {
    condition     = contains(["postgres", "mysql", "mariadb", "aurora-postgresql", "aurora-mysql"], var.engine)
    error_message = "Engine must be one of: postgres, mysql, mariadb, aurora-postgresql, aurora-mysql."
  }
}

variable "engine_version" {
  description = "Database engine version"
  type        = string
  default     = "15.4"
}

variable "family" {
  description = "Database parameter group family"
  type        = string
  default     = "postgres15"
}

# =============================================================================
# Instance Configuration
# =============================================================================

variable "instance_class" {
  description = "Instance class"
  type        = string
  default     = "db.t3.medium"
}

variable "allocated_storage" {
  description = "Allocated storage in GB"
  type        = number
  default     = 20

  validation {
    condition     = var.allocated_storage >= 20 && var.allocated_storage <= 65536
    error_message = "Allocated storage must be between 20 and 65536 GB."
  }
}

variable "max_allocated_storage" {
  description = "Max allocated storage for autoscaling (0 to disable)"
  type        = number
  default     = 100
}

variable "storage_type" {
  description = "Storage type"
  type        = string
  default     = "gp3"

  validation {
    condition     = contains(["gp2", "gp3", "io1", "io2"], var.storage_type)
    error_message = "Storage type must be one of: gp2, gp3, io1, io2."
  }
}

variable "iops" {
  description = "Provisioned IOPS (for io1/io2 storage)"
  type        = number
  default     = null
}

# =============================================================================
# Database Configuration
# =============================================================================

variable "database_name" {
  description = "Name of the database to create"
  type        = string
}

variable "username" {
  description = "Master username"
  type        = string
  sensitive   = true
}

variable "password" {
  description = "Master password (if not using Secrets Manager)"
  type        = string
  sensitive   = true
  default     = null
}

variable "manage_master_user_password" {
  description = "Use AWS Secrets Manager for password management"
  type        = bool
  default     = true
}

variable "port" {
  description = "Database port"
  type        = number
  default     = 5432
}

# =============================================================================
# Network & Security
# =============================================================================

variable "allowed_security_groups" {
  description = "Security groups allowed to access database"
  type        = list(string)
  default     = []
}

variable "allowed_cidr_blocks" {
  description = "CIDR blocks allowed to access database"
  type        = list(string)
  default     = []
}

variable "publicly_accessible" {
  description = "Make database publicly accessible"
  type        = bool
  default     = false
}

# =============================================================================
# High Availability
# =============================================================================

variable "multi_az" {
  description = "Enable Multi-AZ deployment"
  type        = bool
  default     = false
}

# =============================================================================
# Backup & Maintenance
# =============================================================================

variable "backup_retention_period" {
  description = "Backup retention period in days"
  type        = number
  default     = 7

  validation {
    condition     = var.backup_retention_period >= 0 && var.backup_retention_period <= 35
    error_message = "Backup retention must be between 0 and 35 days."
  }
}

variable "backup_window" {
  description = "Preferred backup window (UTC)"
  type        = string
  default     = "03:00-04:00"
}

variable "maintenance_window" {
  description = "Preferred maintenance window"
  type        = string
  default     = "Mon:04:00-Mon:05:00"
}

variable "auto_minor_version_upgrade" {
  description = "Enable auto minor version upgrade"
  type        = bool
  default     = true
}

variable "apply_immediately" {
  description = "Apply changes immediately"
  type        = bool
  default     = false
}

# =============================================================================
# Encryption
# =============================================================================

variable "storage_encrypted" {
  description = "Enable storage encryption"
  type        = bool
  default     = true
}

variable "kms_key_id" {
  description = "KMS key ID for encryption (null for AWS managed)"
  type        = string
  default     = null
}

# =============================================================================
# Monitoring
# =============================================================================

variable "performance_insights_enabled" {
  description = "Enable Performance Insights"
  type        = bool
  default     = true
}

variable "performance_insights_retention_period" {
  description = "Performance Insights retention period"
  type        = number
  default     = 7
}

variable "monitoring_interval" {
  description = "Enhanced monitoring interval (0 to disable)"
  type        = number
  default     = 60

  validation {
    condition     = contains([0, 1, 5, 10, 15, 30, 60], var.monitoring_interval)
    error_message = "Monitoring interval must be 0, 1, 5, 10, 15, 30, or 60."
  }
}

variable "enabled_cloudwatch_logs_exports" {
  description = "CloudWatch log exports"
  type        = list(string)
  default     = ["postgresql", "upgrade"]
}

# =============================================================================
# Protection
# =============================================================================

variable "deletion_protection" {
  description = "Enable deletion protection"
  type        = bool
  default     = true
}

variable "skip_final_snapshot" {
  description = "Skip final snapshot on deletion"
  type        = bool
  default     = false
}

variable "final_snapshot_identifier_prefix" {
  description = "Prefix for final snapshot identifier"
  type        = string
  default     = "final"
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
  port = var.port != null ? var.port : (
    contains(["mysql", "mariadb", "aurora-mysql"], var.engine) ? 3306 : 5432
  )

  common_tags = merge(var.tags, {
    Module    = "rds"
    ManagedBy = "terraform"
  })
}

# =============================================================================
# DB Subnet Group
# =============================================================================

resource "aws_db_subnet_group" "main" {
  name        = "${var.name}-db-subnet-group"
  description = "Database subnet group for ${var.name}"
  subnet_ids  = var.subnet_ids

  tags = merge(local.common_tags, {
    Name = "${var.name}-db-subnet-group"
  })
}

# =============================================================================
# RDS Instance
# =============================================================================

resource "aws_db_instance" "main" {
  identifier = var.name

  # Engine
  engine               = var.engine
  engine_version       = var.engine_version
  instance_class       = var.instance_class

  # Storage
  allocated_storage     = var.allocated_storage
  max_allocated_storage = var.max_allocated_storage
  storage_type          = var.storage_type
  iops                  = var.iops
  storage_encrypted     = var.storage_encrypted
  kms_key_id            = var.kms_key_id

  # Database
  db_name  = var.database_name
  username = var.username
  password = var.manage_master_user_password ? null : var.password
  port     = local.port

  # Secrets Manager
  manage_master_user_password = var.manage_master_user_password

  # Network
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.database.id]
  publicly_accessible    = var.publicly_accessible
  multi_az               = var.multi_az

  # Parameter Group
  parameter_group_name = aws_db_parameter_group.main.name

  # Backup
  backup_retention_period = var.backup_retention_period
  backup_window           = var.backup_window
  maintenance_window      = var.maintenance_window
  copy_tags_to_snapshot   = true

  # Monitoring
  performance_insights_enabled          = var.performance_insights_enabled
  performance_insights_retention_period = var.performance_insights_retention_period
  monitoring_interval                   = var.monitoring_interval
  monitoring_role_arn                   = var.monitoring_interval > 0 ? aws_iam_role.rds_monitoring[0].arn : null
  enabled_cloudwatch_logs_exports       = var.enabled_cloudwatch_logs_exports

  # Protection
  deletion_protection       = var.deletion_protection
  skip_final_snapshot       = var.skip_final_snapshot
  final_snapshot_identifier = var.skip_final_snapshot ? null : "${var.name}-${var.final_snapshot_identifier_prefix}"

  # Updates
  auto_minor_version_upgrade = var.auto_minor_version_upgrade
  apply_immediately          = var.apply_immediately

  tags = merge(local.common_tags, {
    Name = var.name
  })

  lifecycle {
    ignore_changes = [password]
  }
}
```

## security.tf

```hcl
# =============================================================================
# Security Group
# =============================================================================

resource "aws_security_group" "database" {
  name        = "${var.name}-database-sg"
  description = "Security group for ${var.name} database"
  vpc_id      = var.vpc_id

  tags = merge(local.common_tags, {
    Name = "${var.name}-database-sg"
  })

  lifecycle {
    create_before_destroy = true
  }
}

# From Security Groups
resource "aws_security_group_rule" "from_security_groups" {
  count = length(var.allowed_security_groups)

  type                     = "ingress"
  from_port                = local.port
  to_port                  = local.port
  protocol                 = "tcp"
  source_security_group_id = var.allowed_security_groups[count.index]
  security_group_id        = aws_security_group.database.id
  description              = "Access from ${var.allowed_security_groups[count.index]}"
}

# From CIDR Blocks
resource "aws_security_group_rule" "from_cidr_blocks" {
  count = length(var.allowed_cidr_blocks) > 0 ? 1 : 0

  type              = "ingress"
  from_port         = local.port
  to_port           = local.port
  protocol          = "tcp"
  cidr_blocks       = var.allowed_cidr_blocks
  security_group_id = aws_security_group.database.id
  description       = "Access from CIDR blocks"
}
```

## monitoring.tf

```hcl
# =============================================================================
# Enhanced Monitoring Role
# =============================================================================

resource "aws_iam_role" "rds_monitoring" {
  count = var.monitoring_interval > 0 ? 1 : 0

  name = "${var.name}-rds-monitoring-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "monitoring.rds.amazonaws.com"
      }
    }]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "rds_monitoring" {
  count = var.monitoring_interval > 0 ? 1 : 0

  role       = aws_iam_role.rds_monitoring[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

# =============================================================================
# CloudWatch Alarms
# =============================================================================

resource "aws_cloudwatch_metric_alarm" "cpu_utilization" {
  alarm_name          = "${var.name}-cpu-utilization"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "CPU utilization > 80% for ${var.name}"

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.identifier
  }

  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "free_storage_space" {
  alarm_name          = "${var.name}-free-storage-space"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 2
  metric_name         = "FreeStorageSpace"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 5368709120  # 5 GB in bytes
  alarm_description   = "Free storage < 5GB for ${var.name}"

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.identifier
  }

  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "database_connections" {
  alarm_name          = "${var.name}-database-connections"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "DatabaseConnections"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 100
  alarm_description   = "Database connections > 100 for ${var.name}"

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.identifier
  }

  tags = local.common_tags
}
```

## parameters.tf

```hcl
# =============================================================================
# Parameter Group
# =============================================================================

resource "aws_db_parameter_group" "main" {
  name        = "${var.name}-params"
  family      = var.family
  description = "Parameter group for ${var.name}"

  # PostgreSQL specific parameters
  dynamic "parameter" {
    for_each = contains(["postgres", "aurora-postgresql"], var.engine) ? [1] : []
    content {
      name  = "log_statement"
      value = "all"
    }
  }

  dynamic "parameter" {
    for_each = contains(["postgres", "aurora-postgresql"], var.engine) ? [1] : []
    content {
      name  = "log_min_duration_statement"
      value = "1000"  # Log queries > 1 second
    }
  }

  # MySQL specific parameters
  dynamic "parameter" {
    for_each = contains(["mysql", "mariadb", "aurora-mysql"], var.engine) ? [1] : []
    content {
      name  = "slow_query_log"
      value = "1"
    }
  }

  dynamic "parameter" {
    for_each = contains(["mysql", "mariadb", "aurora-mysql"], var.engine) ? [1] : []
    content {
      name  = "long_query_time"
      value = "1"
    }
  }

  tags = merge(local.common_tags, {
    Name = "${var.name}-params"
  })

  lifecycle {
    create_before_destroy = true
  }
}
```

## outputs.tf

```hcl
# =============================================================================
# Instance Outputs
# =============================================================================

output "instance_id" {
  description = "RDS instance ID"
  value       = aws_db_instance.main.id
}

output "instance_arn" {
  description = "RDS instance ARN"
  value       = aws_db_instance.main.arn
}

output "instance_resource_id" {
  description = "RDS instance resource ID"
  value       = aws_db_instance.main.resource_id
}

# =============================================================================
# Connection Outputs
# =============================================================================

output "endpoint" {
  description = "RDS connection endpoint"
  value       = aws_db_instance.main.endpoint
}

output "address" {
  description = "RDS hostname"
  value       = aws_db_instance.main.address
}

output "port" {
  description = "RDS port"
  value       = aws_db_instance.main.port
}

output "database_name" {
  description = "Database name"
  value       = aws_db_instance.main.db_name
}

output "username" {
  description = "Master username"
  value       = aws_db_instance.main.username
  sensitive   = true
}

# =============================================================================
# Security Outputs
# =============================================================================

output "security_group_id" {
  description = "Security group ID"
  value       = aws_security_group.database.id
}

# =============================================================================
# Secrets Manager (if enabled)
# =============================================================================

output "master_user_secret_arn" {
  description = "ARN of the Secrets Manager secret for master user credentials"
  value       = try(aws_db_instance.main.master_user_secret[0].secret_arn, null)
}

# =============================================================================
# Connection String Helpers
# =============================================================================

output "connection_string_template" {
  description = "Connection string template (password not included)"
  value       = "${var.engine}://${aws_db_instance.main.username}:<PASSWORD>@${aws_db_instance.main.endpoint}/${aws_db_instance.main.db_name}"
  sensitive   = true
}
```

## Usage Example

```hcl
module "database" {
  source = "../../modules/rds"

  name            = "myapp-prod"
  engine          = "postgres"
  engine_version  = "15.4"
  family          = "postgres15"
  instance_class  = "db.r6g.large"

  allocated_storage     = 100
  max_allocated_storage = 500
  storage_type          = "gp3"

  database_name               = "myapp"
  username                    = "admin"
  manage_master_user_password = true

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.database_subnet_ids

  allowed_security_groups = [module.eks.node_security_group_id]

  multi_az                = true
  backup_retention_period = 30
  deletion_protection     = true

  # Monitoring
  performance_insights_enabled          = true
  performance_insights_retention_period = 7
  monitoring_interval                   = 60
  enabled_cloudwatch_logs_exports       = ["postgresql", "upgrade"]

  tags = {
    Environment = "production"
    Project     = "myapp"
  }
}

# Retrieve credentials from Secrets Manager
data "aws_secretsmanager_secret_version" "database" {
  secret_id = module.database.master_user_secret_arn
}
```
