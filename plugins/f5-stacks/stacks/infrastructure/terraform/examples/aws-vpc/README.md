# AWS VPC Example

Production-ready VPC infrastructure with public, private, and database subnets.

## Architecture

```
                    ┌─────────────────────────────────────────────────────┐
                    │                       VPC                          │
                    │                   10.0.0.0/16                       │
                    │                                                     │
    ┌───────────────┼─────────────────────────────────────────────────────┤
    │               │                                                     │
    │    ┌──────────┴──────────┐                                          │
    │    │  Internet Gateway   │                                          │
    │    └──────────┬──────────┘                                          │
    │               │                                                     │
    │    ┌──────────┴──────────────────────────────────────────┐          │
    │    │               Public Subnets                        │          │
    │    │  ┌─────────┐  ┌─────────┐  ┌─────────┐              │          │
    │    │  │ AZ-1    │  │ AZ-2    │  │ AZ-3    │              │          │
    │    │  │10.0.0.0 │  │10.0.1.0 │  │10.0.2.0 │              │          │
    │    │  │   /20   │  │   /20   │  │   /20   │              │          │
    │    │  │         │  │         │  │         │              │          │
    │    │  │  [NAT]  │  │  [NAT]  │  │  [NAT]  │              │          │
    │    │  └────┬────┘  └────┬────┘  └────┬────┘              │          │
    │    └───────┼────────────┼────────────┼───────────────────┘          │
    │            │            │            │                              │
    │    ┌───────┴────────────┴────────────┴───────────────────┐          │
    │    │               Private Subnets                       │          │
    │    │  ┌─────────┐  ┌─────────┐  ┌─────────┐              │          │
    │    │  │ AZ-1    │  │ AZ-2    │  │ AZ-3    │              │          │
    │    │  │10.0.3.0 │  │10.0.4.0 │  │10.0.5.0 │              │          │
    │    │  │   /20   │  │   /20   │  │   /20   │              │          │
    │    │  │         │  │         │  │         │              │          │
    │    │  │ [Apps]  │  │ [Apps]  │  │ [Apps]  │              │          │
    │    │  └─────────┘  └─────────┘  └─────────┘              │          │
    │    └─────────────────────────────────────────────────────┘          │
    │                                                                     │
    │    ┌─────────────────────────────────────────────────────┐          │
    │    │               Database Subnets                      │          │
    │    │  ┌─────────┐  ┌─────────┐  ┌─────────┐              │          │
    │    │  │ AZ-1    │  │ AZ-2    │  │ AZ-3    │              │          │
    │    │  │10.0.6.0 │  │10.0.7.0 │  │10.0.8.0 │              │          │
    │    │  │   /20   │  │   /20   │  │   /20   │              │          │
    │    │  │         │  │         │  │         │              │          │
    │    │  │  [RDS]  │  │  [RDS]  │  │  [RDS]  │              │          │
    │    │  └─────────┘  └─────────┘  └─────────┘              │          │
    │    │            (No Internet Access)                     │          │
    │    └─────────────────────────────────────────────────────┘          │
    │                                                                     │
    └─────────────────────────────────────────────────────────────────────┘
```

## Features

- **Multi-AZ deployment** for high availability
- **Public subnets** with direct internet access
- **Private subnets** with NAT gateway access
- **Database subnets** with no internet access (isolated)
- **VPC Flow Logs** for network monitoring
- **S3 VPC Endpoint** for private S3 access
- **Kubernetes-ready** tags for EKS integration

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

## Variables

| Name | Description | Type | Default |
|------|-------------|------|---------|
| project_name | Project name for resource naming | string | "example" |
| environment | Environment (dev/staging/prod) | string | "dev" |
| region | AWS region | string | "us-east-1" |
| vpc_cidr | VPC CIDR block | string | "10.0.0.0/16" |
| az_count | Number of availability zones | number | 3 |
| single_nat_gateway | Use single NAT for cost savings | bool | true |
| enable_s3_endpoint | Enable S3 VPC endpoint | bool | true |
| enable_flow_logs | Enable VPC flow logs | bool | true |

## Outputs

| Name | Description |
|------|-------------|
| vpc_id | VPC ID |
| public_subnet_ids | List of public subnet IDs |
| private_subnet_ids | List of private subnet IDs |
| database_subnet_ids | List of database subnet IDs |
| database_subnet_group_name | RDS subnet group name |
| nat_gateway_public_ips | NAT Gateway public IPs |

## Cost Considerations

- **NAT Gateways**: ~$32/month per gateway + data processing
  - Use `single_nat_gateway = true` for dev/staging
  - Use `single_nat_gateway = false` for production (HA)
- **Flow Logs**: CloudWatch Logs storage costs
- **VPC Endpoints**: Interface endpoints cost ~$7/month each
  - Gateway endpoints (S3, DynamoDB) are free

## Integration with Other Modules

```hcl
# Use VPC outputs in EKS module
module "eks" {
  source = "../aws-eks"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnet_ids
}

# Use VPC outputs in RDS module
module "rds" {
  source = "../aws-rds"

  vpc_id                   = module.vpc.vpc_id
  database_subnet_group_name = module.vpc.database_subnet_group_name
}
```

## Security Best Practices

1. Database subnets have no internet access
2. Private subnets only have outbound NAT access
3. VPC Flow Logs enabled for audit trail
4. S3 endpoint avoids internet traffic for S3 access
