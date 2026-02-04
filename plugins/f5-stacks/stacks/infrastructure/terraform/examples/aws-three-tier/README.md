# AWS Three-Tier Architecture Example

Complete three-tier architecture with VPC, ALB, ECS Fargate, and RDS.

## Architecture

```
                    ┌─────────────────────────────────────────────────────────────────┐
                    │                            VPC                                  │
                    │                        10.0.0.0/16                              │
                    │                                                                 │
                    │   ┌─────────────────────────────────────────────────────────┐   │
                    │   │                    PUBLIC SUBNETS                       │   │
    Internet ───────┼───┤                                                         │   │
                    │   │   ┌───────────────────────────────────────────────┐     │   │
                    │   │   │         Application Load Balancer             │     │   │
                    │   │   │                                               │     │   │
                    │   │   │    HTTP:80 ──────────► Target Group           │     │   │
                    │   │   │   HTTPS:443                                   │     │   │
                    │   │   └───────────────────────────────────────────────┘     │   │
                    │   └─────────────────────────────────────────────────────────┘   │
                    │                           │                                     │
                    │                           ▼                                     │
                    │   ┌─────────────────────────────────────────────────────────┐   │
                    │   │                   PRIVATE SUBNETS                       │   │
                    │   │                                                         │   │
                    │   │   ┌─────────────────────────────────────────────────┐   │   │
                    │   │   │              ECS Fargate Cluster                │   │   │
                    │   │   │                                                 │   │   │
                    │   │   │   ┌─────────┐   ┌─────────┐   ┌─────────┐       │   │   │
                    │   │   │   │  Task   │   │  Task   │   │  Task   │       │   │   │
                    │   │   │   │  (AZ1)  │   │  (AZ2)  │   │  (AZ3)  │       │   │   │
                    │   │   │   │         │   │         │   │         │       │   │   │
                    │   │   │   │ App:80  │   │ App:80  │   │ App:80  │       │   │   │
                    │   │   │   └────┬────┘   └────┬────┘   └────┬────┘       │   │   │
                    │   │   │        │             │             │            │   │   │
                    │   │   └────────┼─────────────┼─────────────┼────────────┘   │   │
                    │   └────────────┼─────────────┼─────────────┼────────────────┘   │
                    │                │             │             │                    │
                    │                ▼             ▼             ▼                    │
                    │   ┌─────────────────────────────────────────────────────────┐   │
                    │   │                  DATABASE SUBNETS                       │   │
                    │   │                                                         │   │
                    │   │   ┌─────────────────────────────────────────────────┐   │   │
                    │   │   │                 RDS PostgreSQL                  │   │   │
                    │   │   │                                                 │   │   │
                    │   │   │      Primary (AZ1) ◄───► Standby (AZ2)          │   │   │
                    │   │   │                  (Multi-AZ)                     │   │   │
                    │   │   │                                                 │   │   │
                    │   │   └─────────────────────────────────────────────────┘   │   │
                    │   │                  (No Internet Access)                   │   │
                    │   └─────────────────────────────────────────────────────────┘   │
                    └─────────────────────────────────────────────────────────────────┘
```

## Components

### Presentation Tier (ALB)
- Application Load Balancer in public subnets
- SSL/TLS termination (HTTPS listener optional)
- Health checks for target groups

### Application Tier (ECS Fargate)
- ECS Cluster with Fargate launch type
- Auto-scaling based on CPU utilization
- CloudWatch logs integration
- Secrets Manager for database credentials

### Data Tier (RDS)
- PostgreSQL or MySQL database
- Encrypted storage
- Multi-AZ deployment (optional)
- Automated backups
- Enhanced monitoring

## Usage

### 1. Initialize

```bash
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values

terraform init
```

### 2. Plan

```bash
terraform plan
```

### 3. Apply

```bash
terraform apply
```

### 4. Access Application

```bash
# Get the ALB DNS name
terraform output app_url

# Open in browser
open $(terraform output -raw app_url)
```

## Variables

| Name | Description | Type | Default |
|------|-------------|------|---------|
| project_name | Project name | string | "example" |
| environment | Environment | string | "dev" |
| container_image | Docker image | string | "nginx:alpine" |
| task_cpu | Fargate CPU units | number | 256 |
| task_memory | Fargate memory (MB) | number | 512 |
| database_engine | Database engine | string | "postgres" |
| database_instance_class | DB instance type | string | "db.t3.micro" |

## Outputs

| Name | Description |
|------|-------------|
| app_url | Application URL |
| alb_dns_name | ALB DNS name |
| ecs_cluster_name | ECS cluster name |
| database_endpoint | RDS endpoint |
| database_secret_arn | Secrets Manager ARN |

## Security Features

1. **Network Isolation**
   - Public subnets only for ALB
   - Application in private subnets
   - Database in isolated subnets

2. **Security Groups**
   - ALB: HTTP/HTTPS from internet
   - App: Traffic only from ALB
   - Database: Traffic only from app

3. **Encryption**
   - RDS storage encryption
   - Secrets Manager for credentials
   - SSL/TLS for data in transit

4. **Monitoring**
   - CloudWatch Container Insights
   - RDS Performance Insights
   - VPC Flow Logs (optional)

## Cost Optimization

### Development

```hcl
# dev.tfvars
single_nat_gateway     = true
task_cpu               = 256
task_memory            = 512
desired_count          = 1
database_instance_class = "db.t3.micro"
database_multi_az      = false
```

### Production

```hcl
# prod.tfvars
single_nat_gateway     = false
task_cpu               = 512
task_memory            = 1024
desired_count          = 3
database_instance_class = "db.r6g.large"
database_multi_az      = true
```

## Deploying Your Application

1. **Build Docker Image**

```bash
docker build -t myapp:latest .
```

2. **Push to ECR**

```bash
aws ecr get-login-password | docker login --username AWS --password-stdin <account>.dkr.ecr.<region>.amazonaws.com
docker tag myapp:latest <account>.dkr.ecr.<region>.amazonaws.com/myapp:latest
docker push <account>.dkr.ecr.<region>.amazonaws.com/myapp:latest
```

3. **Update Task Definition**

```bash
# Update terraform.tfvars
container_image = "<account>.dkr.ecr.<region>.amazonaws.com/myapp:latest"

# Apply changes
terraform apply
```

## Adding HTTPS

1. Request ACM certificate
2. Add HTTPS listener to ALB
3. Update security group

```hcl
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.main.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = aws_acm_certificate.main.arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }
}
```

## Cleanup

```bash
terraform destroy
```

**Note**: If `deletion_protection` is enabled for RDS or ALB in production,
you'll need to disable it first via AWS Console or by updating the terraform
configuration.
