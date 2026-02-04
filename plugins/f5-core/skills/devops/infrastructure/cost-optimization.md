---
name: cost-optimization
description: Cloud cost optimization strategies and FinOps practices
category: devops/infrastructure
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Cloud Cost Optimization

## Overview

Cloud cost optimization is the practice of reducing cloud spending while
maintaining performance and availability. It involves right-sizing, reserved
capacity, spot instances, and architectural decisions.

## Cost Optimization Framework

```
┌─────────────────────────────────────────────────────────────────┐
│              Cost Optimization Pillars                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Right-Sizing          2. Reserved Capacity                  │
│  ┌─────────────────┐     ┌─────────────────┐                   │
│  │ Match resources │     │ Commit for      │                   │
│  │ to actual needs │     │ discounts       │                   │
│  └─────────────────┘     └─────────────────┘                   │
│                                                                  │
│  3. Spot/Preemptible      4. Architecture                       │
│  ┌─────────────────┐     ┌─────────────────┐                   │
│  │ Use spare       │     │ Design for cost │                   │
│  │ capacity        │     │ efficiency      │                   │
│  └─────────────────┘     └─────────────────┘                   │
│                                                                  │
│  5. Tagging & Visibility  6. Automation                         │
│  ┌─────────────────┐     ┌─────────────────┐                   │
│  │ Track costs by  │     │ Auto-shutdown,  │                   │
│  │ project/team    │     │ scheduling      │                   │
│  └─────────────────┘     └─────────────────┘                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Right-Sizing

### Analyze Resource Utilization

```hcl
# CloudWatch metrics for right-sizing
resource "aws_cloudwatch_metric_alarm" "low_cpu" {
  alarm_name          = "low-cpu-utilization"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 4
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = 3600
  statistic           = "Average"
  threshold           = 10
  alarm_description   = "EC2 instance has low CPU - consider downsizing"

  dimensions = {
    InstanceId = aws_instance.web.id
  }

  alarm_actions = [aws_sns_topic.cost_alerts.arn]
}

# Enable Compute Optimizer
resource "aws_compute_optimizer_enrollment_status" "main" {
  status = "Active"
}
```

### Auto-Scaling for Efficiency

```hcl
# Target Tracking Scaling Policy
resource "aws_autoscaling_policy" "cpu_target" {
  name                   = "cpu-target-tracking"
  autoscaling_group_name = aws_autoscaling_group.web.name
  policy_type            = "TargetTrackingScaling"

  target_tracking_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ASGAverageCPUUtilization"
    }
    target_value = 70.0
  }
}

# Scheduled Scaling for Predictable Patterns
resource "aws_autoscaling_schedule" "scale_down_night" {
  scheduled_action_name  = "scale-down-night"
  autoscaling_group_name = aws_autoscaling_group.web.name

  min_size         = 1
  max_size         = 3
  desired_capacity = 1

  recurrence = "0 22 * * *"  # 10 PM daily
}

resource "aws_autoscaling_schedule" "scale_up_morning" {
  scheduled_action_name  = "scale-up-morning"
  autoscaling_group_name = aws_autoscaling_group.web.name

  min_size         = 2
  max_size         = 10
  desired_capacity = 4

  recurrence = "0 7 * * MON-FRI"  # 7 AM weekdays
}
```

## Reserved Capacity

### Savings Plans & Reserved Instances

```hcl
# Reserved Instance (via AWS Console/API)
# Terraform doesn't create RIs but can reference them

# Variable for commitment planning
variable "reservation_strategy" {
  type = object({
    ec2_ri = object({
      instance_type = string
      count         = number
      term          = string  # "1_year" or "3_year"
      payment       = string  # "all_upfront", "partial_upfront", "no_upfront"
    })
    rds_ri = object({
      instance_class = string
      count          = number
      multi_az       = bool
    })
  })

  default = {
    ec2_ri = {
      instance_type = "t3.large"
      count         = 10
      term          = "1_year"
      payment       = "partial_upfront"
    }
    rds_ri = {
      instance_class = "db.r5.large"
      count          = 2
      multi_az       = true
    }
  }
}

# Cost Explorer Anomaly Detection
resource "aws_ce_anomaly_monitor" "service" {
  name              = "service-anomaly-monitor"
  monitor_type      = "DIMENSIONAL"
  monitor_dimension = "SERVICE"
}

resource "aws_ce_anomaly_subscription" "main" {
  name      = "cost-anomaly-subscription"
  frequency = "DAILY"

  monitor_arn_list = [aws_ce_anomaly_monitor.service.arn]

  subscriber {
    type    = "EMAIL"
    address = var.cost_alert_email
  }

  threshold_expression {
    dimension {
      key           = "ANOMALY_TOTAL_IMPACT_ABSOLUTE"
      values        = ["100"]
      match_options = ["GREATER_THAN_OR_EQUAL"]
    }
  }
}
```

## Spot Instances

### Mixed Instance ASG

```hcl
# Auto Scaling Group with Mixed Instances
resource "aws_autoscaling_group" "web" {
  name                = "web-asg"
  vpc_zone_identifier = var.private_subnets
  target_group_arns   = [aws_lb_target_group.web.arn]

  min_size         = 2
  max_size         = 20
  desired_capacity = 4

  mixed_instances_policy {
    instances_distribution {
      on_demand_base_capacity                  = 2
      on_demand_percentage_above_base_capacity = 25
      spot_allocation_strategy                 = "capacity-optimized"
      spot_instance_pools                      = 0
    }

    launch_template {
      launch_template_specification {
        launch_template_id = aws_launch_template.web.id
        version            = "$Latest"
      }

      override {
        instance_type     = "t3.large"
        weighted_capacity = 1
      }

      override {
        instance_type     = "t3a.large"
        weighted_capacity = 1
      }

      override {
        instance_type     = "t3.xlarge"
        weighted_capacity = 2
      }
    }
  }

  instance_refresh {
    strategy = "Rolling"
    preferences {
      min_healthy_percentage = 75
    }
  }
}
```

### EKS with Spot Nodes

```hcl
# EKS Node Group with Spot Instances
resource "aws_eks_node_group" "spot" {
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "spot-workers"
  node_role_arn   = aws_iam_role.node.arn
  subnet_ids      = var.private_subnets

  capacity_type = "SPOT"

  scaling_config {
    desired_size = 3
    max_size     = 10
    min_size     = 0
  }

  instance_types = [
    "t3.large",
    "t3a.large",
    "t3.xlarge",
    "t3a.xlarge",
    "m5.large",
    "m5a.large"
  ]

  labels = {
    "node-type" = "spot"
  }

  taint {
    key    = "spot"
    value  = "true"
    effect = "NO_SCHEDULE"
  }
}

# Karpenter for dynamic provisioning
resource "helm_release" "karpenter" {
  name       = "karpenter"
  repository = "oci://public.ecr.aws/karpenter"
  chart      = "karpenter"
  namespace  = "karpenter"
  version    = "0.32.0"

  set {
    name  = "settings.clusterName"
    value = aws_eks_cluster.main.name
  }

  set {
    name  = "settings.interruptionQueue"
    value = aws_sqs_queue.karpenter.name
  }
}
```

```yaml
# Karpenter NodePool with Spot
apiVersion: karpenter.sh/v1beta1
kind: NodePool
metadata:
  name: spot-pool
spec:
  template:
    spec:
      requirements:
        - key: kubernetes.io/arch
          operator: In
          values: ["amd64"]
        - key: karpenter.sh/capacity-type
          operator: In
          values: ["spot"]
        - key: node.kubernetes.io/instance-type
          operator: In
          values: ["t3.large", "t3a.large", "m5.large", "m5a.large"]
      nodeClassRef:
        name: default
  limits:
    cpu: 1000
  disruption:
    consolidationPolicy: WhenUnderutilized
    consolidateAfter: 30s
```

## Storage Optimization

### S3 Lifecycle Policies

```hcl
resource "aws_s3_bucket_lifecycle_configuration" "main" {
  bucket = aws_s3_bucket.data.id

  rule {
    id     = "archive-logs"
    status = "Enabled"

    filter {
      prefix = "logs/"
    }

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    transition {
      days          = 365
      storage_class = "DEEP_ARCHIVE"
    }

    expiration {
      days = 2555  # 7 years
    }
  }

  rule {
    id     = "multipart-cleanup"
    status = "Enabled"

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }

  rule {
    id     = "intelligent-tiering"
    status = "Enabled"

    filter {
      prefix = "data/"
    }

    transition {
      days          = 0
      storage_class = "INTELLIGENT_TIERING"
    }
  }
}

# S3 Intelligent Tiering Configuration
resource "aws_s3_bucket_intelligent_tiering_configuration" "main" {
  bucket = aws_s3_bucket.data.id
  name   = "full-archive"

  tiering {
    access_tier = "DEEP_ARCHIVE_ACCESS"
    days        = 180
  }

  tiering {
    access_tier = "ARCHIVE_ACCESS"
    days        = 90
  }
}
```

### EBS Optimization

```hcl
# Use GP3 instead of GP2
resource "aws_ebs_volume" "data" {
  availability_zone = var.az
  size              = 100
  type              = "gp3"
  iops              = 3000
  throughput        = 125
  encrypted         = true

  tags = {
    Name = "data-volume"
  }
}

# Snapshot Lifecycle
resource "aws_dlm_lifecycle_policy" "ebs_backup" {
  description        = "EBS snapshot policy"
  execution_role_arn = aws_iam_role.dlm.arn
  state              = "ENABLED"

  policy_details {
    resource_types = ["VOLUME"]

    schedule {
      name = "daily-snapshots"

      create_rule {
        interval      = 24
        interval_unit = "HOURS"
        times         = ["03:00"]
      }

      retain_rule {
        count = 14
      }

      tags_to_add = {
        SnapshotCreator = "DLM"
      }

      copy_tags = true
    }

    target_tags = {
      Backup = "true"
    }
  }
}
```

## Tagging Strategy

### Cost Allocation Tags

```hcl
# Default tags for all resources
provider "aws" {
  default_tags {
    tags = {
      Environment  = var.environment
      Project      = var.project
      Team         = var.team
      CostCenter   = var.cost_center
      ManagedBy    = "terraform"
      CreatedAt    = timestamp()
    }
  }
}

# Enforce tagging policy
resource "aws_organizations_policy" "require_tags" {
  name        = "require-cost-tags"
  description = "Require cost allocation tags"
  type        = "TAG_POLICY"

  content = jsonencode({
    tags = {
      CostCenter = {
        tag_key = {
          "@@assign" = "CostCenter"
        }
        tag_value = {
          "@@assign" = [
            "engineering",
            "marketing",
            "sales",
            "operations"
          ]
        }
        enforced_for = {
          "@@assign" = [
            "ec2:instance",
            "rds:db",
            "s3:bucket"
          ]
        }
      }
      Environment = {
        tag_key = {
          "@@assign" = "Environment"
        }
        tag_value = {
          "@@assign" = [
            "production",
            "staging",
            "development"
          ]
        }
      }
    }
  })
}
```

## Budget Alerts

```hcl
# AWS Budget with alerts
resource "aws_budgets_budget" "monthly" {
  name         = "monthly-budget"
  budget_type  = "COST"
  limit_amount = "10000"
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  cost_filter {
    name   = "TagKeyValue"
    values = ["user:Environment$production"]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = [var.finance_email]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.finance_email, var.ops_email]
    subscriber_sns_topic_arns  = [aws_sns_topic.cost_alerts.arn]
  }
}

# Budget per service
resource "aws_budgets_budget" "ec2" {
  name         = "ec2-budget"
  budget_type  = "COST"
  limit_amount = "5000"
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  cost_filter {
    name   = "Service"
    values = ["Amazon Elastic Compute Cloud - Compute"]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 90
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = [var.ops_email]
  }
}
```

## Automated Cost Control

### Lambda for Resource Cleanup

```python
# lambda/cleanup_unused_resources.py
import boto3
from datetime import datetime, timedelta

def lambda_handler(event, context):
    ec2 = boto3.client('ec2')

    # Find unattached EBS volumes
    volumes = ec2.describe_volumes(
        Filters=[
            {'Name': 'status', 'Values': ['available']}
        ]
    )

    for volume in volumes['Volumes']:
        # Check if volume is old enough
        created = volume['CreateTime'].replace(tzinfo=None)
        if datetime.utcnow() - created > timedelta(days=7):
            # Check for exception tag
            tags = {t['Key']: t['Value'] for t in volume.get('Tags', [])}
            if tags.get('DoNotDelete') != 'true':
                print(f"Deleting unused volume: {volume['VolumeId']}")
                ec2.delete_volume(VolumeId=volume['VolumeId'])

    # Find unused Elastic IPs
    addresses = ec2.describe_addresses()
    for address in addresses['Addresses']:
        if 'InstanceId' not in address and 'NetworkInterfaceId' not in address:
            print(f"Releasing unused EIP: {address['AllocationId']}")
            ec2.release_address(AllocationId=address['AllocationId'])

    return {'statusCode': 200, 'body': 'Cleanup completed'}
```

```hcl
# Scheduled Lambda for cleanup
resource "aws_cloudwatch_event_rule" "cleanup" {
  name                = "resource-cleanup"
  description         = "Trigger cleanup of unused resources"
  schedule_expression = "cron(0 2 * * ? *)"  # 2 AM daily
}

resource "aws_cloudwatch_event_target" "cleanup" {
  rule      = aws_cloudwatch_event_rule.cleanup.name
  target_id = "CleanupLambda"
  arn       = aws_lambda_function.cleanup.arn
}
```

### Instance Scheduler

```hcl
# Stop dev instances on nights/weekends
resource "aws_scheduler_schedule" "stop_dev" {
  name       = "stop-dev-instances"
  group_name = "cost-optimization"

  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression = "cron(0 20 ? * MON-FRI *)"  # 8 PM weekdays

  target {
    arn      = "arn:aws:scheduler:::aws-sdk:ec2:stopInstances"
    role_arn = aws_iam_role.scheduler.arn

    input = jsonencode({
      InstanceIds = var.dev_instance_ids
    })
  }
}

resource "aws_scheduler_schedule" "start_dev" {
  name       = "start-dev-instances"
  group_name = "cost-optimization"

  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression = "cron(0 8 ? * MON-FRI *)"  # 8 AM weekdays

  target {
    arn      = "arn:aws:scheduler:::aws-sdk:ec2:startInstances"
    role_arn = aws_iam_role.scheduler.arn

    input = jsonencode({
      InstanceIds = var.dev_instance_ids
    })
  }
}
```

## Cost Dashboard

```hcl
# CloudWatch Dashboard for costs
resource "aws_cloudwatch_dashboard" "costs" {
  dashboard_name = "cost-overview"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          title  = "Daily Costs by Service"
          view   = "timeSeries"
          region = var.region
          metrics = [
            ["AWS/Billing", "EstimatedCharges", "ServiceName", "AmazonEC2", "Currency", "USD"],
            [".", ".", "ServiceName", "AmazonRDS", ".", "."],
            [".", ".", "ServiceName", "AmazonS3", ".", "."],
            [".", ".", "ServiceName", "AWSLambda", ".", "."]
          ]
          period = 86400
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          title  = "Total Estimated Charges"
          view   = "singleValue"
          region = "us-east-1"
          metrics = [
            ["AWS/Billing", "EstimatedCharges", "Currency", "USD"]
          ]
          period = 86400
        }
      }
    ]
  })
}
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│              Cost Optimization Best Practices                    │
├─────────────────────────────────────────────────────────────────┤
│ ☐ Implement comprehensive tagging for cost allocation           │
│ ☐ Set up budget alerts at 50%, 80%, 100% thresholds            │
│ ☐ Right-size instances based on actual utilization             │
│ ☐ Use Reserved Instances/Savings Plans for steady workloads    │
│ ☐ Leverage Spot instances for fault-tolerant workloads         │
│ ☐ Implement auto-scaling to match demand                        │
│ ☐ Use S3 lifecycle policies for data tiering                   │
│ ☐ Schedule non-production resources to stop off-hours          │
│ ☐ Clean up unused resources regularly                           │
│ ☐ Choose appropriate storage types (GP3 over GP2)              │
│ ☐ Use managed services when cost-effective                      │
│ ☐ Monitor and optimize data transfer costs                      │
│ ☐ Review Cost Explorer recommendations regularly                │
│ ☐ Implement FinOps practices and governance                    │
└─────────────────────────────────────────────────────────────────┘
```

## Cost Comparison Matrix

```
┌─────────────────────────────────────────────────────────────────┐
│              Pricing Model Comparison                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Model            Discount    Best For           Flexibility    │
│  ──────────────────────────────────────────────────────────    │
│  On-Demand         0%        Variable loads     Highest        │
│  Spot            60-90%      Fault-tolerant    Lowest         │
│  Savings Plans   30-72%      Steady baseline   Medium         │
│  Reserved (1yr)  30-40%      Predictable       Low            │
│  Reserved (3yr)  50-60%      Long-term         Lowest         │
│                                                                  │
│  Recommended Mix (Production):                                  │
│  • Reserved/Savings Plans: 60-70% (baseline capacity)          │
│  • On-Demand: 10-20% (burst capacity)                          │
│  • Spot: 10-20% (fault-tolerant batch jobs)                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```
