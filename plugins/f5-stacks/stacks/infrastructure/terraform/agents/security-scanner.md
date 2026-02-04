---
name: terraform-security-scanner
description: Scan Terraform configurations for security issues
triggers:
  - "scan terraform security"
  - "check tf security"
  - "terraform compliance"
---

# Terraform Security Scanner Agent

## Purpose

Identify security misconfigurations, compliance violations, and best practice deviations in Terraform configurations.

## Capabilities

1. **Security Scanning**: Detect misconfigurations and vulnerabilities
2. **Compliance Checking**: Validate against standards (CIS, SOC2, HIPAA)
3. **Best Practices**: Enforce HashiCorp and cloud provider best practices
4. **Policy as Code**: Implement custom security policies
5. **CI/CD Integration**: Automated scanning in pipelines

## Security Tools

### Checkov

```bash
# Install
pip install checkov

# Scan directory
checkov -d .

# Scan with specific framework
checkov -d . --framework terraform

# Output formats
checkov -d . -o json > checkov-results.json
checkov -d . -o sarif > checkov-results.sarif

# Skip specific checks
checkov -d . --skip-check CKV_AWS_18,CKV_AWS_19

# Custom policies
checkov -d . --external-checks-dir ./custom-policies
```

### tfsec

```bash
# Install
brew install tfsec

# Basic scan
tfsec .

# With severity filter
tfsec . --minimum-severity HIGH

# Specific format output
tfsec . --format json > tfsec-results.json

# Exclude paths
tfsec . --exclude-path modules/legacy
```

### Terrascan

```bash
# Install
brew install terrascan

# Scan
terrascan scan -t aws

# With policy set
terrascan scan -t aws -p aws_cis

# Output
terrascan scan -t aws -o json > terrascan-results.json
```

## Common Security Issues

### S3 Bucket Misconfigurations

```hcl
# ❌ INSECURE - Public bucket
resource "aws_s3_bucket" "bad" {
  bucket = "my-bucket"
  acl    = "public-read"  # DANGER!
}

# ✅ SECURE - Private with encryption
resource "aws_s3_bucket" "good" {
  bucket = "my-bucket"
}

resource "aws_s3_bucket_public_access_block" "good" {
  bucket = aws_s3_bucket.good.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "good" {
  bucket = aws_s3_bucket.good.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.main.arn
    }
  }
}
```

### Security Group Issues

```hcl
# ❌ INSECURE - Open to world
resource "aws_security_group_rule" "bad" {
  type        = "ingress"
  from_port   = 22
  to_port     = 22
  protocol    = "tcp"
  cidr_blocks = ["0.0.0.0/0"]  # DANGER!
}

# ✅ SECURE - Restricted CIDR
resource "aws_security_group_rule" "good" {
  type        = "ingress"
  from_port   = 22
  to_port     = 22
  protocol    = "tcp"
  cidr_blocks = ["10.0.0.0/8"]  # Internal only
  description = "SSH from internal network"
}
```

### RDS Security

```hcl
# ❌ INSECURE
resource "aws_db_instance" "bad" {
  publicly_accessible    = true   # DANGER!
  storage_encrypted      = false  # DANGER!
  deletion_protection    = false  # Risk
  skip_final_snapshot    = true   # Risk
}

# ✅ SECURE
resource "aws_db_instance" "good" {
  publicly_accessible     = false
  storage_encrypted       = true
  kms_key_id              = aws_kms_key.rds.arn
  deletion_protection     = true
  skip_final_snapshot     = false
  backup_retention_period = 30

  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]

  performance_insights_enabled    = true
  monitoring_interval             = 60
}
```

### IAM Policy Issues

```hcl
# ❌ INSECURE - Overly permissive
resource "aws_iam_policy" "bad" {
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "*"           # DANGER!
      Resource = "*"           # DANGER!
    }]
  })
}

# ✅ SECURE - Least privilege
resource "aws_iam_policy" "good" {
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "s3:GetObject",
        "s3:PutObject"
      ]
      Resource = [
        "arn:aws:s3:::my-bucket/*"
      ]
      Condition = {
        StringEquals = {
          "aws:RequestedRegion" = "us-east-1"
        }
      }
    }]
  })
}
```

## Custom Policy Example (Checkov)

```python
# custom-policies/require_encryption.py
from checkov.terraform.checks.resource.base_resource_check import BaseResourceCheck
from checkov.common.models.enums import CheckResult, CheckCategories

class S3BucketEncryption(BaseResourceCheck):
    def __init__(self):
        name = "Ensure S3 bucket has encryption enabled"
        id = "CUSTOM_S3_001"
        supported_resources = ['aws_s3_bucket']
        categories = [CheckCategories.ENCRYPTION]
        super().__init__(name=name, id=id, categories=categories,
                        supported_resources=supported_resources)

    def scan_resource_conf(self, conf):
        # Check for encryption configuration
        if 'server_side_encryption_configuration' in conf:
            return CheckResult.PASSED
        return CheckResult.FAILED

check = S3BucketEncryption()
```

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/terraform-security.yml
name: Terraform Security Scan

on:
  pull_request:
    paths:
      - '**.tf'
      - '**.tfvars'

jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run Checkov
        uses: bridgecrewio/checkov-action@v12
        with:
          directory: .
          framework: terraform
          output_format: sarif
          output_file_path: checkov-results.sarif

      - name: Upload SARIF
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: checkov-results.sarif

      - name: Run tfsec
        uses: aquasecurity/tfsec-action@v1.0.0
        with:
          soft_fail: false
```

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/antonbabenko/pre-commit-terraform
    rev: v1.83.5
    hooks:
      - id: terraform_fmt
      - id: terraform_validate
      - id: terraform_tflint
      - id: terraform_checkov
        args:
          - --args=--quiet
          - --args=--compact
      - id: terraform_tfsec
```

## Security Checklist

### Network Security
- [ ] No 0.0.0.0/0 in security groups (except ALB/NLB)
- [ ] VPC flow logs enabled
- [ ] Private subnets for databases
- [ ] NACLs configured appropriately

### Data Protection
- [ ] Encryption at rest enabled
- [ ] Encryption in transit enabled
- [ ] KMS keys with rotation
- [ ] No hardcoded secrets

### Access Control
- [ ] Least privilege IAM policies
- [ ] No wildcard permissions
- [ ] MFA for sensitive operations
- [ ] Role-based access

### Logging & Monitoring
- [ ] CloudTrail enabled
- [ ] VPC flow logs
- [ ] CloudWatch alarms
- [ ] Config rules

## Commands

```bash
# Run full security scan
/tf:security scan --all

# Check specific compliance
/tf:security compliance --standard cis-aws

# Generate security report
/tf:security report --format html --output security-report.html

# Fix common issues
/tf:security fix --auto
```
