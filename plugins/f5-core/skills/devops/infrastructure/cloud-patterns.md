---
name: cloud-patterns
description: Cloud architecture patterns and best practices
category: devops/infrastructure
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Cloud Architecture Patterns

## Overview

Cloud architecture patterns are reusable solutions to common problems
in cloud computing. Understanding these patterns helps build scalable,
reliable, and cost-effective systems.

## High Availability Patterns

```
┌─────────────────────────────────────────────────────────────────┐
│                 Multi-AZ Architecture                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Region: us-east-1                                               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                                                          │   │
│  │  AZ-1a              AZ-1b              AZ-1c            │   │
│  │  ┌──────────┐      ┌──────────┐      ┌──────────┐      │   │
│  │  │ Public   │      │ Public   │      │ Public   │      │   │
│  │  │ Subnet   │      │ Subnet   │      │ Subnet   │      │   │
│  │  │ ┌──────┐ │      │ ┌──────┐ │      │ ┌──────┐ │      │   │
│  │  │ │ NAT  │ │      │ │ NAT  │ │      │ │ NAT  │ │      │   │
│  │  │ └──────┘ │      │ └──────┘ │      │ └──────┘ │      │   │
│  │  └──────────┘      └──────────┘      └──────────┘      │   │
│  │                                                          │   │
│  │  ┌──────────┐      ┌──────────┐      ┌──────────┐      │   │
│  │  │ Private  │      │ Private  │      │ Private  │      │   │
│  │  │ Subnet   │      │ Subnet   │      │ Subnet   │      │   │
│  │  │ ┌──────┐ │      │ ┌──────┐ │      │ ┌──────┐ │      │   │
│  │  │ │ App  │ │      │ │ App  │ │      │ │ App  │ │      │   │
│  │  │ └──────┘ │      │ └──────┘ │      │ └──────┘ │      │   │
│  │  └──────────┘      └──────────┘      └──────────┘      │   │
│  │                                                          │   │
│  │  ┌──────────┐      ┌──────────┐      ┌──────────┐      │   │
│  │  │ Database │      │ Database │      │ Database │      │   │
│  │  │ Subnet   │      │ Subnet   │      │ Subnet   │      │   │
│  │  │ ┌──────┐ │      │ ┌──────┐ │      │ ┌──────┐ │      │   │
│  │  │ │Primary│ │      │ │Standby│ │      │ │ Read │ │      │   │
│  │  │ └──────┘ │      │ └──────┘ │      │ │Replica│ │      │   │
│  │  └──────────┘      └──────────┘      │ └──────┘ │      │   │
│  │                                       └──────────┘      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Multi-AZ Terraform

```hcl
# Multi-AZ VPC
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.0.0"

  name = "production-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["us-east-1a", "us-east-1b", "us-east-1c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  enable_nat_gateway     = true
  single_nat_gateway     = false
  one_nat_gateway_per_az = true

  enable_dns_hostnames = true
  enable_dns_support   = true
}

# Multi-AZ RDS
resource "aws_db_instance" "main" {
  identifier             = "production-db"
  engine                 = "postgres"
  engine_version         = "15.4"
  instance_class         = "db.r5.large"
  allocated_storage      = 100

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.db.id]

  multi_az               = true
  storage_encrypted      = true

  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "Mon:04:00-Mon:05:00"
}

# Multi-AZ Auto Scaling Group
resource "aws_autoscaling_group" "web" {
  name                = "web-asg"
  vpc_zone_identifier = module.vpc.private_subnets
  target_group_arns   = [aws_lb_target_group.web.arn]

  min_size         = 3
  max_size         = 12
  desired_capacity = 6

  launch_template {
    id      = aws_launch_template.web.id
    version = "$Latest"
  }

  health_check_type         = "ELB"
  health_check_grace_period = 300
}
```

## Multi-Region Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                Multi-Region Active-Active                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│                      Global Load Balancer                        │
│                       (Route 53 / CloudFront)                    │
│                             │                                    │
│              ┌──────────────┼──────────────┐                    │
│              │              │              │                    │
│              ▼              ▼              ▼                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  US-EAST-1   │  │  EU-WEST-1   │  │  AP-SOUTH-1  │         │
│  │  ┌────────┐  │  │  ┌────────┐  │  │  ┌────────┐  │         │
│  │  │  ALB   │  │  │  │  ALB   │  │  │  │  ALB   │  │         │
│  │  └────────┘  │  │  └────────┘  │  │  └────────┘  │         │
│  │      │       │  │      │       │  │      │       │         │
│  │  ┌────────┐  │  │  ┌────────┐  │  │  ┌────────┐  │         │
│  │  │  ECS/  │  │  │  │  ECS/  │  │  │  │  ECS/  │  │         │
│  │  │  EKS   │  │  │  │  EKS   │  │  │  │  EKS   │  │         │
│  │  └────────┘  │  │  └────────┘  │  │  └────────┘  │         │
│  │      │       │  │      │       │  │      │       │         │
│  │  ┌────────┐  │  │  ┌────────┐  │  │  ┌────────┐  │         │
│  │  │ Aurora │  │  │  │ Aurora │  │  │  │ Aurora │  │         │
│  │  │ Global │◄─┼──┼──│ Replica│◄─┼──┼──│ Replica│  │         │
│  │  └────────┘  │  │  └────────┘  │  │  └────────┘  │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Multi-Region Terraform

```hcl
# Provider for multiple regions
provider "aws" {
  alias  = "primary"
  region = "us-east-1"
}

provider "aws" {
  alias  = "secondary"
  region = "eu-west-1"
}

# Aurora Global Database
resource "aws_rds_global_cluster" "main" {
  global_cluster_identifier = "global-db"
  engine                    = "aurora-postgresql"
  engine_version            = "15.4"
  database_name             = "myapp"
  storage_encrypted         = true
}

resource "aws_rds_cluster" "primary" {
  provider = aws.primary

  cluster_identifier        = "primary-cluster"
  engine                    = aws_rds_global_cluster.main.engine
  engine_version            = aws_rds_global_cluster.main.engine_version
  global_cluster_identifier = aws_rds_global_cluster.main.id
  database_name             = "myapp"
  master_username           = var.db_username
  master_password           = var.db_password
  db_subnet_group_name      = aws_db_subnet_group.primary.name
  vpc_security_group_ids    = [aws_security_group.db_primary.id]
}

resource "aws_rds_cluster" "secondary" {
  provider = aws.secondary

  cluster_identifier        = "secondary-cluster"
  engine                    = aws_rds_global_cluster.main.engine
  engine_version            = aws_rds_global_cluster.main.engine_version
  global_cluster_identifier = aws_rds_global_cluster.main.id
  db_subnet_group_name      = aws_db_subnet_group.secondary.name
  vpc_security_group_ids    = [aws_security_group.db_secondary.id]

  depends_on = [aws_rds_cluster.primary]
}

# Route 53 Latency-Based Routing
resource "aws_route53_record" "api" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "api.example.com"
  type    = "A"

  set_identifier = "primary"
  latency_routing_policy {
    region = "us-east-1"
  }

  alias {
    name                   = aws_lb.primary.dns_name
    zone_id                = aws_lb.primary.zone_id
    evaluate_target_health = true
  }
}

resource "aws_route53_record" "api_secondary" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "api.example.com"
  type    = "A"

  set_identifier = "secondary"
  latency_routing_policy {
    region = "eu-west-1"
  }

  alias {
    name                   = aws_lb.secondary.dns_name
    zone_id                = aws_lb.secondary.zone_id
    evaluate_target_health = true
  }
}
```

## Serverless Patterns

```
┌─────────────────────────────────────────────────────────────────┐
│                 Serverless Event-Driven Architecture             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  API Gateway ────► Lambda ────► DynamoDB                        │
│       │               │              │                          │
│       │               ▼              │                          │
│       │          EventBridge         │                          │
│       │               │              │                          │
│       │        ┌──────┴──────┐       │                          │
│       │        ▼             ▼       │                          │
│       │    Lambda        Lambda      │                          │
│       │    (async)       (async)     │                          │
│       │        │             │       │                          │
│       │        ▼             ▼       │                          │
│       │      SQS           SNS       │                          │
│       │        │             │       │                          │
│       │        ▼             ▼       │                          │
│       │    Lambda     Email/SMS      │                          │
│       │        │                     │                          │
│       │        ▼                     │                          │
│       │       S3 ◄───────────────────┘                          │
│       │                                                          │
│       └─────────────► CloudWatch Logs                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Serverless Terraform

```hcl
# API Gateway
resource "aws_apigatewayv2_api" "main" {
  name          = "serverless-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = ["https://example.com"]
    allow_methods = ["GET", "POST", "PUT", "DELETE"]
    allow_headers = ["Content-Type", "Authorization"]
  }
}

resource "aws_apigatewayv2_stage" "prod" {
  api_id      = aws_apigatewayv2_api.main.id
  name        = "prod"
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      routeKey       = "$context.routeKey"
      status         = "$context.status"
      responseLength = "$context.responseLength"
    })
  }
}

# Lambda Function
resource "aws_lambda_function" "api" {
  function_name = "api-handler"
  role          = aws_iam_role.lambda.arn
  handler       = "index.handler"
  runtime       = "nodejs20.x"
  timeout       = 30
  memory_size   = 256

  filename         = data.archive_file.lambda.output_path
  source_code_hash = data.archive_file.lambda.output_base64sha256

  environment {
    variables = {
      TABLE_NAME  = aws_dynamodb_table.main.name
      ENVIRONMENT = var.environment
    }
  }

  tracing_config {
    mode = "Active"
  }

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [aws_security_group.lambda.id]
  }
}

# DynamoDB Table
resource "aws_dynamodb_table" "main" {
  name           = "app-data"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "PK"
  range_key      = "SK"

  attribute {
    name = "PK"
    type = "S"
  }

  attribute {
    name = "SK"
    type = "S"
  }

  attribute {
    name = "GSI1PK"
    type = "S"
  }

  global_secondary_index {
    name            = "GSI1"
    hash_key        = "GSI1PK"
    range_key       = "SK"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }
}

# EventBridge Rule
resource "aws_cloudwatch_event_rule" "orders" {
  name        = "order-events"
  description = "Capture order events"

  event_pattern = jsonencode({
    source      = ["app.orders"]
    detail-type = ["Order Created", "Order Updated"]
  })
}

resource "aws_cloudwatch_event_target" "process_order" {
  rule      = aws_cloudwatch_event_rule.orders.name
  target_id = "ProcessOrder"
  arn       = aws_lambda_function.process_order.arn
}
```

## Microservices Patterns

```
┌─────────────────────────────────────────────────────────────────┐
│              Microservices Architecture                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│           ┌───────────────────────────────────────┐             │
│           │           API Gateway                  │             │
│           │      (Rate Limiting, Auth)            │             │
│           └─────────────────┬─────────────────────┘             │
│                             │                                    │
│           ┌─────────────────┼─────────────────┐                 │
│           ▼                 ▼                 ▼                 │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐          │
│  │   User      │   │   Order     │   │   Product   │          │
│  │   Service   │   │   Service   │   │   Service   │          │
│  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘          │
│         │                 │                 │                   │
│         ▼                 ▼                 ▼                   │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐          │
│  │  Users DB   │   │  Orders DB  │   │ Products DB │          │
│  │ (Postgres)  │   │  (Postgres) │   │  (MongoDB)  │          │
│  └─────────────┘   └─────────────┘   └─────────────┘          │
│                                                                  │
│         Message Bus (Kafka / SQS / EventBridge)                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Events: UserCreated, OrderPlaced, InventoryUpdated     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│         Service Mesh (Istio / App Mesh)                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  mTLS, Traffic Management, Observability                │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### ECS Microservices

```hcl
# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "microservices"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

resource "aws_ecs_cluster_capacity_providers" "main" {
  cluster_name = aws_ecs_cluster.main.name

  capacity_providers = ["FARGATE", "FARGATE_SPOT"]

  default_capacity_provider_strategy {
    base              = 1
    weight            = 100
    capacity_provider = "FARGATE"
  }
}

# Service Module
module "user_service" {
  source = "./modules/ecs-service"

  name           = "user-service"
  cluster_id     = aws_ecs_cluster.main.id
  vpc_id         = module.vpc.vpc_id
  subnets        = module.vpc.private_subnets
  container_port = 8080

  image          = "${aws_ecr_repository.user_service.repository_url}:latest"
  cpu            = 256
  memory         = 512
  desired_count  = 2

  environment = {
    DATABASE_URL = "postgresql://${var.db_host}:5432/users"
    REDIS_URL    = aws_elasticache_cluster.main.cache_nodes[0].address
  }

  secrets = {
    DB_PASSWORD = aws_secretsmanager_secret.db_password.arn
  }

  health_check_path = "/health"

  service_discovery_namespace_id = aws_service_discovery_private_dns_namespace.main.id
}

# Service Discovery
resource "aws_service_discovery_private_dns_namespace" "main" {
  name = "services.internal"
  vpc  = module.vpc.vpc_id
}

# App Mesh
resource "aws_appmesh_mesh" "main" {
  name = "microservices"

  spec {
    egress_filter {
      type = "ALLOW_ALL"
    }
  }
}

resource "aws_appmesh_virtual_node" "user_service" {
  name      = "user-service"
  mesh_name = aws_appmesh_mesh.main.name

  spec {
    backend {
      virtual_service {
        virtual_service_name = "order-service.services.internal"
      }
    }

    listener {
      port_mapping {
        port     = 8080
        protocol = "http"
      }

      health_check {
        protocol            = "http"
        path                = "/health"
        healthy_threshold   = 2
        unhealthy_threshold = 2
        timeout_millis      = 2000
        interval_millis     = 5000
      }
    }

    service_discovery {
      aws_cloud_map {
        namespace_name = aws_service_discovery_private_dns_namespace.main.name
        service_name   = "user-service"
      }
    }
  }
}
```

## Data Architecture Patterns

```
┌─────────────────────────────────────────────────────────────────┐
│                Data Lake Architecture                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Data Sources                                                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │   App    │ │   IoT    │ │  Logs    │ │  Third   │          │
│  │   DBs    │ │ Devices  │ │          │ │  Party   │          │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘          │
│       │            │            │            │                  │
│       └────────────┴────────────┴────────────┘                  │
│                         │                                        │
│                         ▼                                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    Ingestion Layer                       │   │
│  │     Kinesis Data Streams / Kafka / EventBridge          │   │
│  └──────────────────────────┬──────────────────────────────┘   │
│                             │                                    │
│                             ▼                                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    S3 Data Lake                          │   │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐           │   │
│  │  │   Raw     │  │  Curated  │  │  Analytics │           │   │
│  │  │  (Bronze) │→│  (Silver)  │→│  (Gold)    │           │   │
│  │  └───────────┘  └───────────┘  └───────────┘           │   │
│  └──────────────────────────┬──────────────────────────────┘   │
│                             │                                    │
│           ┌─────────────────┼─────────────────┐                 │
│           ▼                 ▼                 ▼                 │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐          │
│  │   Athena    │   │   Redshift  │   │   EMR       │          │
│  │  (Ad-hoc)   │   │    (DW)     │   │  (Spark)   │          │
│  └─────────────┘   └─────────────┘   └─────────────┘          │
│                             │                                    │
│                             ▼                                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    QuickSight / BI Tools                 │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Data Lake Terraform

```hcl
# S3 Data Lake Buckets
resource "aws_s3_bucket" "raw" {
  bucket = "${var.project}-data-lake-raw"
}

resource "aws_s3_bucket" "curated" {
  bucket = "${var.project}-data-lake-curated"
}

resource "aws_s3_bucket" "analytics" {
  bucket = "${var.project}-data-lake-analytics"
}

# Lifecycle policies for each tier
resource "aws_s3_bucket_lifecycle_configuration" "raw" {
  bucket = aws_s3_bucket.raw.id

  rule {
    id     = "move-to-ia"
    status = "Enabled"

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    expiration {
      days = 365
    }
  }
}

# Glue Catalog Database
resource "aws_glue_catalog_database" "main" {
  name = "${var.project}_data_lake"
}

# Glue Crawler for raw data
resource "aws_glue_crawler" "raw" {
  database_name = aws_glue_catalog_database.main.name
  name          = "raw-data-crawler"
  role          = aws_iam_role.glue.arn

  s3_target {
    path = "s3://${aws_s3_bucket.raw.bucket}/"
  }

  schedule = "cron(0 */6 * * ? *)"

  configuration = jsonencode({
    Version = 1.0
    Grouping = {
      TableGroupingPolicy = "CombineCompatibleSchemas"
    }
  })
}

# Kinesis Data Stream
resource "aws_kinesis_stream" "events" {
  name             = "event-stream"
  shard_count      = 4
  retention_period = 24

  stream_mode_details {
    stream_mode = "PROVISIONED"
  }

  encryption_type = "KMS"
  kms_key_id      = aws_kms_key.kinesis.id
}

# Kinesis Firehose to S3
resource "aws_kinesis_firehose_delivery_stream" "to_s3" {
  name        = "events-to-s3"
  destination = "extended_s3"

  kinesis_source_configuration {
    kinesis_stream_arn = aws_kinesis_stream.events.arn
    role_arn           = aws_iam_role.firehose.arn
  }

  extended_s3_configuration {
    role_arn   = aws_iam_role.firehose.arn
    bucket_arn = aws_s3_bucket.raw.arn
    prefix     = "events/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/"

    buffering_size     = 128
    buffering_interval = 300

    data_format_conversion_configuration {
      input_format_configuration {
        deserializer {
          open_x_json_ser_de {}
        }
      }

      output_format_configuration {
        serializer {
          parquet_ser_de {
            compression = "SNAPPY"
          }
        }
      }

      schema_configuration {
        database_name = aws_glue_catalog_database.main.name
        table_name    = "events"
        role_arn      = aws_iam_role.firehose.arn
      }
    }
  }
}

# Athena Workgroup
resource "aws_athena_workgroup" "main" {
  name = "analytics"

  configuration {
    enforce_workgroup_configuration    = true
    publish_cloudwatch_metrics_enabled = true

    result_configuration {
      output_location = "s3://${aws_s3_bucket.analytics.bucket}/athena-results/"

      encryption_configuration {
        encryption_option = "SSE_KMS"
        kms_key_arn       = aws_kms_key.athena.arn
      }
    }
  }
}
```

## Network Patterns

### Hub-and-Spoke Network

```hcl
# Transit Gateway
resource "aws_ec2_transit_gateway" "main" {
  description = "Main transit gateway"

  default_route_table_association = "disable"
  default_route_table_propagation = "disable"

  tags = {
    Name = "main-tgw"
  }
}

# Hub VPC (Shared Services)
resource "aws_ec2_transit_gateway_vpc_attachment" "hub" {
  subnet_ids         = module.hub_vpc.private_subnets
  transit_gateway_id = aws_ec2_transit_gateway.main.id
  vpc_id             = module.hub_vpc.vpc_id

  tags = {
    Name = "hub-attachment"
  }
}

# Spoke VPCs
resource "aws_ec2_transit_gateway_vpc_attachment" "spoke" {
  for_each = var.spoke_vpcs

  subnet_ids         = each.value.private_subnets
  transit_gateway_id = aws_ec2_transit_gateway.main.id
  vpc_id             = each.value.vpc_id

  tags = {
    Name = "${each.key}-attachment"
  }
}

# Route Tables
resource "aws_ec2_transit_gateway_route_table" "hub" {
  transit_gateway_id = aws_ec2_transit_gateway.main.id
  tags = { Name = "hub-rt" }
}

resource "aws_ec2_transit_gateway_route_table" "spoke" {
  transit_gateway_id = aws_ec2_transit_gateway.main.id
  tags = { Name = "spoke-rt" }
}

# Route Propagation
resource "aws_ec2_transit_gateway_route_table_propagation" "hub_to_spoke" {
  transit_gateway_attachment_id  = aws_ec2_transit_gateway_vpc_attachment.hub.id
  transit_gateway_route_table_id = aws_ec2_transit_gateway_route_table.spoke.id
}
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│              Cloud Architecture Best Practices                   │
├─────────────────────────────────────────────────────────────────┤
│ ☐ Design for failure - assume everything will fail              │
│ ☐ Implement multi-AZ for high availability                      │
│ ☐ Use auto-scaling to handle variable load                      │
│ ☐ Implement proper network segmentation                         │
│ ☐ Encrypt data at rest and in transit                           │
│ ☐ Use managed services when possible                            │
│ ☐ Implement proper logging and monitoring                       │
│ ☐ Design for cost optimization                                  │
│ ☐ Use infrastructure as code                                    │
│ ☐ Implement disaster recovery plans                             │
│ ☐ Follow the principle of least privilege                       │
│ ☐ Design loosely coupled systems                                │
└─────────────────────────────────────────────────────────────────┘
```
