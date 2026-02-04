# AWS EKS Example

Production-ready EKS cluster with managed node groups, IRSA, and security best practices.

## Architecture

```
                    ┌─────────────────────────────────────────────────────────────┐
                    │                         VPC                                 │
                    │                                                             │
                    │   ┌─────────────────────────────────────────────────────┐   │
                    │   │                  Public Subnets                     │   │
                    │   │   ┌─────────┐  ┌─────────┐  ┌─────────┐             │   │
                    │   │   │  ALB    │  │  ALB    │  │  ALB    │             │   │
                    │   │   │ (ELB)   │  │ (ELB)   │  │ (ELB)   │             │   │
                    │   │   └────┬────┘  └────┬────┘  └────┬────┘             │   │
                    │   └────────┼────────────┼────────────┼──────────────────┘   │
                    │            │            │            │                      │
                    │   ┌────────┴────────────┴────────────┴──────────────────┐   │
                    │   │                  Private Subnets                    │   │
                    │   │   ┌─────────────────────────────────────────────┐   │   │
                    │   │   │              EKS Control Plane              │   │   │
                    │   │   │    ┌──────────────────────────────────┐     │   │   │
                    │   │   │    │         Kubernetes API           │     │   │   │
                    │   │   │    │    (encrypted with KMS)          │     │   │   │
                    │   │   │    └──────────────────────────────────┘     │   │   │
                    │   │   └─────────────────────────────────────────────┘   │   │
                    │   │                                                     │   │
                    │   │   ┌─────────────────────────────────────────────┐   │   │
                    │   │   │            Managed Node Groups              │   │   │
                    │   │   │   ┌───────┐  ┌───────┐  ┌───────┐           │   │   │
                    │   │   │   │ Node  │  │ Node  │  │ Node  │           │   │   │
                    │   │   │   │ (AZ1) │  │ (AZ2) │  │ (AZ3) │           │   │   │
                    │   │   │   │       │  │       │  │       │           │   │   │
                    │   │   │   │ Pods  │  │ Pods  │  │ Pods  │           │   │   │
                    │   │   │   └───────┘  └───────┘  └───────┘           │   │   │
                    │   │   └─────────────────────────────────────────────┘   │   │
                    │   └─────────────────────────────────────────────────────┘   │
                    └─────────────────────────────────────────────────────────────┘
```

## Features

- **Managed node groups** with auto-scaling
- **IRSA (IAM Roles for Service Accounts)** for pod-level IAM
- **KMS encryption** for Kubernetes secrets
- **Control plane logging** to CloudWatch
- **Security groups** for cluster and nodes
- **EKS managed addons** (CoreDNS, kube-proxy, VPC CNI)
- **Spot instance support** for cost optimization

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

### 4. Configure kubectl

```bash
# Use the output command
aws eks update-kubeconfig --name myapp-dev --region us-east-1

# Verify
kubectl get nodes
```

## Variables

| Name | Description | Type | Default |
|------|-------------|------|---------|
| project_name | Project name | string | "example" |
| environment | Environment (dev/staging/prod) | string | "dev" |
| region | AWS region | string | "us-east-1" |
| vpc_cidr | VPC CIDR block | string | "10.0.0.0/16" |
| cluster_version | Kubernetes version | string | "1.29" |
| node_groups | Node group configurations | map(object) | See defaults |

## Outputs

| Name | Description |
|------|-------------|
| cluster_name | EKS cluster name |
| cluster_endpoint | EKS API endpoint |
| oidc_provider_arn | OIDC provider ARN for IRSA |
| kubectl_config_command | Command to configure kubectl |

## Node Groups

### General Purpose (ON_DEMAND)

```hcl
general = {
  instance_types = ["t3.medium"]
  capacity_type  = "ON_DEMAND"
  min_size       = 2
  max_size       = 10
  desired_size   = 2
}
```

### Spot Instances (Cost Optimized)

```hcl
spot = {
  instance_types = ["t3.medium", "t3.large"]
  capacity_type  = "SPOT"
  min_size       = 0
  max_size       = 20
  desired_size   = 0
  taints = [{
    key    = "spot"
    value  = "true"
    effect = "NO_SCHEDULE"
  }]
}
```

## IRSA (IAM Roles for Service Accounts)

Create an IRSA role for your application:

```hcl
module "irsa_role" {
  source = "../../modules/iam/role"

  name = "myapp-pod-role"

  oidc_provider_arn = module.eks.oidc_provider_arn
  oidc_conditions = {
    sub = {
      test     = "StringEquals"
      variable = "${replace(module.eks.oidc_provider_url, "https://", "")}:sub"
      values   = ["system:serviceaccount:myapp:myapp-sa"]
    }
  }

  policy_statements = [
    {
      effect    = "Allow"
      actions   = ["s3:GetObject"]
      resources = ["arn:aws:s3:::my-bucket/*"]
    }
  ]
}
```

Then annotate your ServiceAccount:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: myapp-sa
  namespace: myapp
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::123456789012:role/myapp-pod-role
```

## Cost Optimization

1. **Use Spot Instances** for non-critical workloads
2. **Right-size nodes** based on actual usage
3. **Enable Cluster Autoscaler** for dynamic scaling
4. **Use single NAT gateway** for dev/staging

## Security Best Practices

1. **Secrets encrypted with KMS**
2. **Private cluster endpoints** (optional)
3. **IRSA** instead of node-level IAM
4. **Network policies** for pod isolation
5. **Control plane logging** for audit
