---
name: disaster-recovery
description: Disaster recovery planning and implementation
category: devops/reliability
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Disaster Recovery

## Overview

Disaster Recovery (DR) is the process of preparing for and recovering from
events that significantly impact business operations. A good DR plan ensures
business continuity with minimal data loss and downtime.

## DR Concepts

```
┌─────────────────────────────────────────────────────────────────┐
│                    Key DR Metrics                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  RTO (Recovery Time Objective)                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Maximum acceptable downtime after disaster               │   │
│  │ "How long can we be down?"                              │   │
│  │ Example: 4 hours RTO = must recover within 4 hours      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  RPO (Recovery Point Objective)                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Maximum acceptable data loss measured in time            │   │
│  │ "How much data can we lose?"                            │   │
│  │ Example: 1 hour RPO = can lose up to 1 hour of data     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Timeline:                                                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                                                          │   │
│  │  ◄─────── RPO ───────►│◄────────── RTO ───────────►    │   │
│  │  |                    |                           |     │   │
│  │  Last Backup      Disaster                    Recovery  │   │
│  │  (Data Loss)      Occurs                      Complete  │   │
│  │                                                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Additional Metrics:                                            │
│  • MTTR: Mean Time To Recovery                                  │
│  • MTPD: Maximum Tolerable Period of Disruption                 │
│  • WRT: Work Recovery Time (to restore full productivity)       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## DR Strategies

```
┌─────────────────────────────────────────────────────────────────┐
│               DR Strategy Comparison                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Strategy       │ RTO      │ RPO     │ Cost    │ Complexity    │
│  ───────────────┼──────────┼─────────┼─────────┼──────────────│
│  Backup/Restore │ Hours    │ Hours   │ $       │ Low          │
│  Pilot Light    │ Minutes  │ Minutes │ $$      │ Medium       │
│  Warm Standby   │ Minutes  │ Seconds │ $$$     │ Medium-High  │
│  Active-Active  │ Seconds  │ Zero    │ $$$$    │ High         │
│                                                                  │
│  Backup & Restore                                               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Primary: ████████████████                                │   │
│  │ Backup:  ░░░░░░░░ (stored but not running)              │   │
│  │ • Lowest cost, highest RTO/RPO                           │   │
│  │ • Good for: Non-critical systems, compliance             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Pilot Light                                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Primary: ████████████████                                │   │
│  │ DR:      ██ (minimal core running, data replicated)     │   │
│  │ • Core infra running, scale up when needed               │   │
│  │ • Good for: Business-critical systems                    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Warm Standby                                                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Primary: ████████████████                                │   │
│  │ DR:      ████████ (scaled-down but running)             │   │
│  │ • Reduced capacity ready to scale                        │   │
│  │ • Good for: Critical systems with moderate budget        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Active-Active (Multi-Region)                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Region 1: ████████████████ ◄──► ████████████████ :2     │   │
│  │ • Both regions serve traffic                             │   │
│  │ • Instant failover, zero data loss                       │   │
│  │ • Good for: Mission-critical systems                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Backup Strategies

### Database Backups

```hcl
# AWS RDS Automated Backups
resource "aws_db_instance" "main" {
  identifier             = "production-db"
  engine                 = "postgres"
  engine_version         = "15.4"
  instance_class         = "db.r5.large"
  allocated_storage      = 100

  # Backup configuration
  backup_retention_period = 30
  backup_window          = "03:00-04:00"
  maintenance_window     = "Mon:04:00-Mon:05:00"

  # Multi-AZ for high availability
  multi_az = true

  # Enable deletion protection
  deletion_protection = true

  # Enable encryption
  storage_encrypted = true
  kms_key_id        = aws_kms_key.rds.arn

  # Enable Performance Insights
  performance_insights_enabled = true
}

# Cross-region snapshot copy
resource "aws_db_instance_automated_backups_replication" "main" {
  source_db_instance_arn = aws_db_instance.main.arn
  kms_key_id             = aws_kms_key.rds_dr.arn
  retention_period       = 14

  provider = aws.dr_region
}

# Manual snapshot for major changes
resource "aws_db_snapshot" "pre_migration" {
  db_instance_identifier = aws_db_instance.main.identifier
  db_snapshot_identifier = "pre-migration-${formatdate("YYYY-MM-DD", timestamp())}"
}
```

### S3 Cross-Region Replication

```hcl
# Primary bucket
resource "aws_s3_bucket" "primary" {
  bucket = "my-app-data-primary"
}

resource "aws_s3_bucket_versioning" "primary" {
  bucket = aws_s3_bucket.primary.id
  versioning_configuration {
    status = "Enabled"
  }
}

# DR bucket
resource "aws_s3_bucket" "dr" {
  provider = aws.dr_region
  bucket   = "my-app-data-dr"
}

resource "aws_s3_bucket_versioning" "dr" {
  provider = aws.dr_region
  bucket   = aws_s3_bucket.dr.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Replication configuration
resource "aws_s3_bucket_replication_configuration" "main" {
  bucket = aws_s3_bucket.primary.id
  role   = aws_iam_role.replication.arn

  rule {
    id     = "replicate-all"
    status = "Enabled"

    destination {
      bucket        = aws_s3_bucket.dr.arn
      storage_class = "STANDARD"

      encryption_configuration {
        replica_kms_key_id = aws_kms_key.s3_dr.arn
      }

      replication_time {
        status = "Enabled"
        time {
          minutes = 15
        }
      }

      metrics {
        status = "Enabled"
        event_threshold {
          minutes = 15
        }
      }
    }

    source_selection_criteria {
      sse_kms_encrypted_objects {
        status = "Enabled"
      }
    }

    delete_marker_replication {
      status = "Enabled"
    }
  }
}
```

## Multi-Region Architecture

### Active-Passive Setup

```hcl
# Primary region resources
module "primary" {
  source = "./modules/app-stack"
  providers = {
    aws = aws.primary
  }

  environment = "production"
  region      = "us-east-1"
  is_primary  = true

  vpc_cidr = "10.0.0.0/16"

  database_config = {
    instance_class = "db.r5.xlarge"
    multi_az       = true
  }
}

# DR region resources (pilot light)
module "dr" {
  source = "./modules/app-stack"
  providers = {
    aws = aws.dr
  }

  environment = "production-dr"
  region      = "us-west-2"
  is_primary  = false

  vpc_cidr = "10.1.0.0/16"

  # Smaller resources for pilot light
  database_config = {
    instance_class = "db.r5.large"
    multi_az       = false
  }

  # Reference primary for replication
  source_region     = "us-east-1"
  source_db_arn     = module.primary.db_arn
}

# Route 53 health check
resource "aws_route53_health_check" "primary" {
  fqdn              = module.primary.alb_dns_name
  port              = 443
  type              = "HTTPS"
  resource_path     = "/health"
  failure_threshold = 3
  request_interval  = 30
}

# DNS failover routing
resource "aws_route53_record" "api" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "api.example.com"
  type    = "A"

  set_identifier = "primary"

  failover_routing_policy {
    type = "PRIMARY"
  }

  alias {
    name                   = module.primary.alb_dns_name
    zone_id                = module.primary.alb_zone_id
    evaluate_target_health = true
  }

  health_check_id = aws_route53_health_check.primary.id
}

resource "aws_route53_record" "api_dr" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "api.example.com"
  type    = "A"

  set_identifier = "secondary"

  failover_routing_policy {
    type = "SECONDARY"
  }

  alias {
    name                   = module.dr.alb_dns_name
    zone_id                = module.dr.alb_zone_id
    evaluate_target_health = true
  }
}
```

### Active-Active Setup

```hcl
# Global Accelerator for multi-region
resource "aws_globalaccelerator_accelerator" "main" {
  name            = "api-accelerator"
  ip_address_type = "IPV4"
  enabled         = true
}

resource "aws_globalaccelerator_listener" "main" {
  accelerator_arn = aws_globalaccelerator_accelerator.main.id
  client_affinity = "SOURCE_IP"
  protocol        = "TCP"

  port_range {
    from_port = 443
    to_port   = 443
  }
}

resource "aws_globalaccelerator_endpoint_group" "primary" {
  listener_arn                  = aws_globalaccelerator_listener.main.id
  endpoint_group_region         = "us-east-1"
  traffic_dial_percentage       = 50
  health_check_interval_seconds = 10
  health_check_path             = "/health"
  health_check_protocol         = "HTTPS"
  threshold_count               = 3

  endpoint_configuration {
    endpoint_id                    = module.primary.alb_arn
    weight                         = 100
    client_ip_preservation_enabled = true
  }
}

resource "aws_globalaccelerator_endpoint_group" "secondary" {
  listener_arn                  = aws_globalaccelerator_listener.main.id
  endpoint_group_region         = "eu-west-1"
  traffic_dial_percentage       = 50
  health_check_interval_seconds = 10
  health_check_path             = "/health"
  health_check_protocol         = "HTTPS"
  threshold_count               = 3

  endpoint_configuration {
    endpoint_id                    = module.secondary.alb_arn
    weight                         = 100
    client_ip_preservation_enabled = true
  }
}

# Aurora Global Database
resource "aws_rds_global_cluster" "main" {
  global_cluster_identifier = "global-aurora"
  engine                    = "aurora-postgresql"
  engine_version            = "15.4"
  database_name             = "myapp"
  storage_encrypted         = true
}

resource "aws_rds_cluster" "primary" {
  cluster_identifier        = "aurora-primary"
  engine                    = aws_rds_global_cluster.main.engine
  engine_version            = aws_rds_global_cluster.main.engine_version
  global_cluster_identifier = aws_rds_global_cluster.main.id
  database_name             = "myapp"
  master_username           = var.db_username
  master_password           = var.db_password

  provider = aws.primary
}

resource "aws_rds_cluster" "secondary" {
  cluster_identifier        = "aurora-secondary"
  engine                    = aws_rds_global_cluster.main.engine
  engine_version            = aws_rds_global_cluster.main.engine_version
  global_cluster_identifier = aws_rds_global_cluster.main.id

  provider = aws.secondary

  depends_on = [aws_rds_cluster.primary]
}
```

## DR Runbooks

### Failover Runbook

```yaml
# dr-failover-runbook.yaml
runbook:
  name: "Regional Failover"
  version: "2.0"
  last_tested: "2024-01-15"

prerequisites:
  - "Access to AWS Console and CLI"
  - "PagerDuty incident acknowledged"
  - "Communication channel established"
  - "Customer communication template ready"

decision_criteria:
  initiate_failover:
    - "Primary region unhealthy for > 5 minutes"
    - "Multiple AZ failures in primary region"
    - "AWS reports regional outage"
    - "RTO threshold approaching"

steps:
  - id: 1
    action: "Verify primary region status"
    commands:
      - "aws ec2 describe-availability-zone-status --region us-east-1"
      - "aws route53 get-health-check-status --health-check-id $HEALTH_CHECK_ID"
    verification: "Confirm primary is unhealthy"

  - id: 2
    action: "Notify stakeholders"
    commands:
      - "./scripts/notify-stakeholders.sh failover-initiated"
    verification: "Confirm notifications sent"

  - id: 3
    action: "Scale up DR environment"
    commands:
      - |
        aws autoscaling update-auto-scaling-group \
          --auto-scaling-group-name dr-asg \
          --min-size 4 --max-size 20 --desired-capacity 8 \
          --region us-west-2
    verification: "Wait for instances to be InService"

  - id: 4
    action: "Promote DR database"
    commands:
      - |
        aws rds promote-read-replica-db-cluster \
          --db-cluster-identifier aurora-secondary \
          --region us-west-2
    verification: "Cluster status = available"

  - id: 5
    action: "Update DNS"
    commands:
      - |
        aws route53 change-resource-record-sets \
          --hosted-zone-id $ZONE_ID \
          --change-batch file://dns-failover.json
    verification: "DNS propagation complete (check with dig)"

  - id: 6
    action: "Verify DR is serving traffic"
    commands:
      - "curl -I https://api.example.com/health"
      - "./scripts/smoke-test.sh"
    verification: "All smoke tests pass"

  - id: 7
    action: "Update status page"
    commands:
      - "./scripts/update-status-page.sh partial-outage"
    verification: "Status page reflects current state"

rollback:
  trigger: "DR region also fails or data inconsistency detected"
  steps:
    - "Stop traffic to DR"
    - "Investigate root cause"
    - "Consider tertiary backup options"
    - "Escalate to executive team"

post_failover:
  - "Document timeline and decisions"
  - "Schedule failback planning"
  - "Create incident ticket"
  - "Notify customers of resolution"
```

### Failback Runbook

```yaml
# dr-failback-runbook.yaml
runbook:
  name: "Regional Failback"
  version: "2.0"

prerequisites:
  - "Primary region fully operational"
  - "Database sync completed"
  - "Low traffic period (if possible)"
  - "Stakeholder approval for failback"

pre_failback_checks:
  - step: "Verify primary region health"
    command: "aws ec2 describe-availability-zone-status --region us-east-1"

  - step: "Check database replication lag"
    command: |
      aws rds describe-db-clusters \
        --db-cluster-identifier aurora-primary \
        --query 'DBClusters[0].ReplicationSourceIdentifier'

  - step: "Verify application deployments match"
    command: "./scripts/compare-deployments.sh primary dr"

steps:
  - id: 1
    action: "Enable replication back to primary"
    commands:
      - |
        # Set up replication from DR to primary
        aws rds create-db-cluster \
          --db-cluster-identifier aurora-primary-new \
          --replication-source-identifier $DR_CLUSTER_ARN \
          --region us-east-1
    verification: "Replication lag < 1 second"

  - id: 2
    action: "Gradually shift traffic"
    commands:
      - |
        # 10% to primary
        aws route53 change-resource-record-sets \
          --change-batch file://traffic-10.json
    verification: "Monitor error rates"
    wait: "15 minutes"

  - id: 3
    action: "Increase traffic to primary"
    commands:
      - "# 50% to primary"
      - "aws route53 change-resource-record-sets --change-batch file://traffic-50.json"
    verification: "Error rates normal"
    wait: "15 minutes"

  - id: 4
    action: "Complete traffic shift"
    commands:
      - "# 100% to primary"
      - "aws route53 change-resource-record-sets --change-batch file://traffic-100.json"
    verification: "All traffic on primary"

  - id: 5
    action: "Promote primary database"
    commands:
      - |
        aws rds failover-global-cluster \
          --global-cluster-identifier global-aurora \
          --target-db-cluster-identifier aurora-primary-new
    verification: "Primary is writer"

  - id: 6
    action: "Scale down DR"
    commands:
      - |
        aws autoscaling update-auto-scaling-group \
          --auto-scaling-group-name dr-asg \
          --min-size 1 --max-size 3 --desired-capacity 2 \
          --region us-west-2
    verification: "DR at pilot light capacity"

  - id: 7
    action: "Re-establish replication to DR"
    commands:
      - "./scripts/setup-dr-replication.sh"
    verification: "Replication active"

post_failback:
  - "Verify all services operational"
  - "Update documentation"
  - "Schedule DR test"
  - "Update status page to resolved"
```

## DR Testing

```yaml
# dr-test-plan.yaml
test_plan:
  name: "Quarterly DR Test"
  frequency: "Quarterly"
  last_test: "2024-01-15"
  next_test: "2024-04-15"

test_types:
  tabletop:
    frequency: "Monthly"
    duration: "2 hours"
    participants: ["Engineering", "Operations", "Leadership"]
    objectives:
      - "Review runbooks for accuracy"
      - "Identify gaps in documentation"
      - "Train new team members"

  component_test:
    frequency: "Monthly"
    duration: "1-2 hours"
    objectives:
      - "Test individual DR components"
      - "Verify backup restoration"
      - "Test replication lag"
    tests:
      - "Database failover"
      - "Backup restoration"
      - "DNS failover"

  full_failover:
    frequency: "Quarterly"
    duration: "4-8 hours"
    objectives:
      - "End-to-end DR validation"
      - "Measure actual RTO/RPO"
      - "Identify process gaps"

metrics_to_capture:
  - "Time to detect failure"
  - "Time to initiate failover"
  - "Time to complete failover"
  - "Data loss (RPO actual)"
  - "Service restoration (RTO actual)"
  - "Error rate during failover"

success_criteria:
  - "RTO achieved: < 30 minutes"
  - "RPO achieved: < 5 minutes"
  - "All critical services operational"
  - "No data corruption"
  - "Runbooks accurate"
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│              Disaster Recovery Best Practices                    │
├─────────────────────────────────────────────────────────────────┤
│ ☐ Define RTO and RPO based on business requirements            │
│ ☐ Choose DR strategy matching RTO/RPO needs                    │
│ ☐ Automate backups and verify them regularly                   │
│ ☐ Use cross-region replication for critical data               │
│ ☐ Document detailed runbooks for all DR procedures             │
│ ☐ Test DR procedures regularly (quarterly minimum)             │
│ ☐ Include DR in change management process                       │
│ ☐ Monitor replication lag continuously                          │
│ ☐ Encrypt all backups and replicated data                      │
│ ☐ Store runbooks in multiple locations                          │
│ ☐ Train multiple team members on DR procedures                 │
│ ☐ Review and update DR plan after each test                    │
│ ☐ Consider cost vs. recovery time tradeoffs                    │
│ ☐ Include third-party services in DR planning                  │
└─────────────────────────────────────────────────────────────────┘
```
