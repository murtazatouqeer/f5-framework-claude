# AWS RDS Databases

## Overview

Amazon RDS provides managed relational database services. Terraform enables comprehensive database configuration including parameter groups, option groups, and read replicas.

## RDS Instance

### Basic Instance

```hcl
resource "aws_db_instance" "main" {
  identifier = "${var.project}-db"

  engine         = "postgres"
  engine_version = "15.4"
  instance_class = "db.t3.micro"

  allocated_storage     = 20
  max_allocated_storage = 100
  storage_type          = "gp3"
  storage_encrypted     = true

  db_name  = var.database_name
  username = var.database_username
  password = var.database_password

  vpc_security_group_ids = [aws_security_group.database.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name

  skip_final_snapshot = true

  tags = {
    Name = "${var.project}-db"
  }
}
```

### Production Instance

```hcl
resource "aws_db_instance" "main" {
  identifier = "${var.project}-db"

  engine         = "postgres"
  engine_version = "15.4"
  instance_class = var.instance_class

  allocated_storage     = var.allocated_storage
  max_allocated_storage = var.max_allocated_storage
  storage_type          = "gp3"
  storage_encrypted     = true
  kms_key_id            = aws_kms_key.database.arn

  db_name  = var.database_name
  username = var.database_username
  password = random_password.database.result

  vpc_security_group_ids = [aws_security_group.database.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
  parameter_group_name   = aws_db_parameter_group.main.name

  # High availability
  multi_az = true

  # Backup configuration
  backup_retention_period   = 30
  backup_window             = "03:00-04:00"
  maintenance_window        = "Mon:04:00-Mon:05:00"
  copy_tags_to_snapshot     = true
  delete_automated_backups  = false
  skip_final_snapshot       = false
  final_snapshot_identifier = "${var.project}-db-final-snapshot"

  # Performance
  performance_insights_enabled          = true
  performance_insights_retention_period = 7
  performance_insights_kms_key_id       = aws_kms_key.database.arn

  # Monitoring
  monitoring_interval = 60
  monitoring_role_arn = aws_iam_role.rds_monitoring.arn

  # Logging
  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]

  # Protection
  deletion_protection = true

  # Auto minor version upgrade
  auto_minor_version_upgrade = true

  tags = {
    Name        = "${var.project}-db"
    Environment = var.environment
  }

  lifecycle {
    prevent_destroy = true
  }
}
```

## DB Subnet Group

```hcl
resource "aws_db_subnet_group" "main" {
  name       = "${var.project}-db-subnet-group"
  subnet_ids = var.database_subnet_ids

  tags = {
    Name = "${var.project}-db-subnet-group"
  }
}
```

## Parameter Group

```hcl
resource "aws_db_parameter_group" "main" {
  name   = "${var.project}-pg15-params"
  family = "postgres15"

  parameter {
    name  = "log_statement"
    value = "all"
  }

  parameter {
    name  = "log_min_duration_statement"
    value = "1000"
  }

  parameter {
    name  = "shared_preload_libraries"
    value = "pg_stat_statements"
  }

  parameter {
    name  = "pg_stat_statements.track"
    value = "all"
  }

  parameter {
    name         = "max_connections"
    value        = "200"
    apply_method = "pending-reboot"
  }

  tags = {
    Name = "${var.project}-pg15-params"
  }
}
```

## Option Group

```hcl
# MySQL option group example
resource "aws_db_option_group" "main" {
  name                     = "${var.project}-mysql-options"
  option_group_description = "MySQL options for ${var.project}"
  engine_name              = "mysql"
  major_engine_version     = "8.0"

  option {
    option_name = "MARIADB_AUDIT_PLUGIN"

    option_settings {
      name  = "SERVER_AUDIT_EVENTS"
      value = "CONNECT,QUERY"
    }
  }

  tags = {
    Name = "${var.project}-mysql-options"
  }
}
```

## Read Replica

```hcl
resource "aws_db_instance" "replica" {
  identifier = "${var.project}-db-replica"

  replicate_source_db = aws_db_instance.main.identifier
  instance_class      = var.replica_instance_class

  storage_encrypted = true
  kms_key_id        = aws_kms_key.database.arn

  vpc_security_group_ids = [aws_security_group.database.id]
  parameter_group_name   = aws_db_parameter_group.main.name

  # Replica-specific settings
  multi_az               = false
  backup_retention_period = 0
  skip_final_snapshot    = true

  # Performance insights
  performance_insights_enabled = true

  tags = {
    Name = "${var.project}-db-replica"
  }
}

# Cross-region replica
resource "aws_db_instance" "cross_region_replica" {
  provider = aws.secondary_region

  identifier = "${var.project}-db-replica-dr"

  replicate_source_db = aws_db_instance.main.arn
  instance_class      = var.replica_instance_class

  storage_encrypted = true

  vpc_security_group_ids = [aws_security_group.database_dr.id]
  db_subnet_group_name   = aws_db_subnet_group.dr.name

  skip_final_snapshot = true

  tags = {
    Name = "${var.project}-db-replica-dr"
  }
}
```

## Aurora Cluster

### Aurora PostgreSQL

```hcl
resource "aws_rds_cluster" "main" {
  cluster_identifier = "${var.project}-aurora"

  engine         = "aurora-postgresql"
  engine_version = "15.4"
  engine_mode    = "provisioned"

  database_name   = var.database_name
  master_username = var.database_username
  master_password = random_password.database.result

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.database.id]

  storage_encrypted = true
  kms_key_id        = aws_kms_key.database.arn

  backup_retention_period   = 30
  preferred_backup_window   = "03:00-04:00"
  preferred_maintenance_window = "Mon:04:00-Mon:05:00"
  copy_tags_to_snapshot     = true
  skip_final_snapshot       = false
  final_snapshot_identifier = "${var.project}-aurora-final"

  enabled_cloudwatch_logs_exports = ["postgresql"]

  deletion_protection = true

  serverlessv2_scaling_configuration {
    min_capacity = 0.5
    max_capacity = 16
  }

  tags = {
    Name = "${var.project}-aurora"
  }
}

resource "aws_rds_cluster_instance" "main" {
  count = var.aurora_instance_count

  identifier         = "${var.project}-aurora-${count.index + 1}"
  cluster_identifier = aws_rds_cluster.main.id
  instance_class     = "db.serverless"
  engine             = aws_rds_cluster.main.engine
  engine_version     = aws_rds_cluster.main.engine_version

  performance_insights_enabled = true
  monitoring_interval          = 60
  monitoring_role_arn          = aws_iam_role.rds_monitoring.arn

  tags = {
    Name = "${var.project}-aurora-${count.index + 1}"
  }
}
```

### Aurora Global Database

```hcl
resource "aws_rds_global_cluster" "main" {
  global_cluster_identifier = "${var.project}-global"
  engine                    = "aurora-postgresql"
  engine_version            = "15.4"
  database_name             = var.database_name
  storage_encrypted         = true
}

# Primary cluster
resource "aws_rds_cluster" "primary" {
  cluster_identifier        = "${var.project}-primary"
  global_cluster_identifier = aws_rds_global_cluster.main.id

  engine         = aws_rds_global_cluster.main.engine
  engine_version = aws_rds_global_cluster.main.engine_version

  master_username = var.database_username
  master_password = random_password.database.result

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.database.id]
}

# Secondary cluster (different region)
resource "aws_rds_cluster" "secondary" {
  provider = aws.secondary

  cluster_identifier        = "${var.project}-secondary"
  global_cluster_identifier = aws_rds_global_cluster.main.id

  engine         = aws_rds_global_cluster.main.engine
  engine_version = aws_rds_global_cluster.main.engine_version

  db_subnet_group_name   = aws_db_subnet_group.secondary.name
  vpc_security_group_ids = [aws_security_group.database_secondary.id]

  depends_on = [aws_rds_cluster_instance.primary]
}
```

## Secrets Management

```hcl
resource "random_password" "database" {
  length           = 32
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

resource "aws_secretsmanager_secret" "database" {
  name = "${var.project}/database/credentials"

  tags = {
    Name = "${var.project}-db-credentials"
  }
}

resource "aws_secretsmanager_secret_version" "database" {
  secret_id = aws_secretsmanager_secret.database.id

  secret_string = jsonencode({
    username = var.database_username
    password = random_password.database.result
    host     = aws_db_instance.main.address
    port     = aws_db_instance.main.port
    database = var.database_name
  })
}
```

## Monitoring Role

```hcl
resource "aws_iam_role" "rds_monitoring" {
  name = "${var.project}-rds-monitoring"

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
}

resource "aws_iam_role_policy_attachment" "rds_monitoring" {
  role       = aws_iam_role.rds_monitoring.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}
```

## CloudWatch Alarms

```hcl
resource "aws_cloudwatch_metric_alarm" "database_cpu" {
  alarm_name          = "${var.project}-db-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "Database CPU utilization high"

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.identifier
  }

  alarm_actions = [var.sns_topic_arn]
}

resource "aws_cloudwatch_metric_alarm" "database_storage" {
  alarm_name          = "${var.project}-db-storage-low"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 1
  metric_name         = "FreeStorageSpace"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 10737418240  # 10 GB
  alarm_description   = "Database free storage low"

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.identifier
  }

  alarm_actions = [var.sns_topic_arn]
}

resource "aws_cloudwatch_metric_alarm" "database_connections" {
  alarm_name          = "${var.project}-db-connections-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "DatabaseConnections"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 150
  alarm_description   = "Database connections high"

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.main.identifier
  }

  alarm_actions = [var.sns_topic_arn]
}
```

## Outputs

```hcl
output "db_instance_endpoint" {
  description = "RDS instance endpoint"
  value       = aws_db_instance.main.endpoint
}

output "db_instance_address" {
  description = "RDS instance address"
  value       = aws_db_instance.main.address
}

output "db_instance_port" {
  description = "RDS instance port"
  value       = aws_db_instance.main.port
}

output "db_instance_arn" {
  description = "RDS instance ARN"
  value       = aws_db_instance.main.arn
}

output "db_secret_arn" {
  description = "Secrets Manager secret ARN"
  value       = aws_secretsmanager_secret.database.arn
}
```
