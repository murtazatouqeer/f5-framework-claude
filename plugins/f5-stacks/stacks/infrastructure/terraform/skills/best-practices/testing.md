# Terraform Testing Best Practices

## Overview

Testing infrastructure code ensures reliability and prevents costly mistakes. This guide covers testing strategies, tools, and patterns for Terraform.

## Testing Pyramid

```
    /\
   /  \     End-to-End Tests (Integration)
  /----\    - Real infrastructure
 /      \   - Slow, expensive
/--------\
/          \ Contract Tests
/------------\ - Module interfaces
/              \ - Output validation
/----------------\
/                  \ Unit Tests (Static Analysis)
/--------------------\ - terraform validate
/                      \ - tflint, checkov, tfsec
```

## Static Analysis

### Terraform Validate

```bash
# Basic validation
terraform init -backend=false
terraform validate

# CI script
#!/bin/bash
set -e

for dir in $(find . -name "*.tf" -exec dirname {} \; | sort -u); do
  echo "Validating $dir"
  cd "$dir"
  terraform init -backend=false -input=false
  terraform validate
  cd -
done
```

### TFLint

```hcl
# .tflint.hcl
config {
  module = true
  force  = false
}

plugin "aws" {
  enabled = true
  version = "0.27.0"
  source  = "github.com/terraform-linters/tflint-ruleset-aws"
}

plugin "terraform" {
  enabled = true
  preset  = "recommended"
}

rule "terraform_naming_convention" {
  enabled = true
  format  = "snake_case"
}

rule "terraform_documented_variables" {
  enabled = true
}

rule "terraform_documented_outputs" {
  enabled = true
}

rule "aws_instance_invalid_type" {
  enabled = true
}

rule "aws_resource_missing_tags" {
  enabled = true
  tags    = ["Project", "Environment", "Owner"]
}
```

```bash
# Run tflint
tflint --init
tflint --recursive
```

### Checkov Security Scanning

```yaml
# .checkov.yml
framework:
  - terraform
  - terraform_plan
compact: true
directory:
  - .
check:
  - CKV_AWS_*
  - CKV2_AWS_*
skip-check:
  - CKV_AWS_144  # Skip with justification
soft-fail-on:
  - CKV_AWS_18
```

```bash
# Run checkov
checkov -d . --config-file .checkov.yml
checkov -f plan.json --framework terraform_plan
```

## Unit Testing with Terratest

### Basic Module Test

```go
// test/vpc_test.go
package test

import (
    "testing"

    "github.com/gruntwork-io/terratest/modules/terraform"
    "github.com/stretchr/testify/assert"
)

func TestVPCModule(t *testing.T) {
    t.Parallel()

    terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
        TerraformDir: "../modules/vpc",
        Vars: map[string]interface{}{
            "name":               "test-vpc",
            "cidr_block":         "10.0.0.0/16",
            "availability_zones": []string{"us-east-1a", "us-east-1b"},
            "private_subnets":    []string{"10.0.1.0/24", "10.0.2.0/24"},
            "public_subnets":     []string{"10.0.101.0/24", "10.0.102.0/24"},
        },
    })

    defer terraform.Destroy(t, terraformOptions)
    terraform.InitAndApply(t, terraformOptions)

    // Validate outputs
    vpcID := terraform.Output(t, terraformOptions, "vpc_id")
    assert.NotEmpty(t, vpcID)

    privateSubnetIDs := terraform.OutputList(t, terraformOptions, "private_subnet_ids")
    assert.Equal(t, 2, len(privateSubnetIDs))

    publicSubnetIDs := terraform.OutputList(t, terraformOptions, "public_subnet_ids")
    assert.Equal(t, 2, len(publicSubnetIDs))
}
```

### Testing with AWS SDK

```go
// test/ec2_test.go
package test

import (
    "testing"

    "github.com/aws/aws-sdk-go/aws"
    "github.com/aws/aws-sdk-go/aws/session"
    "github.com/aws/aws-sdk-go/service/ec2"
    "github.com/gruntwork-io/terratest/modules/terraform"
    "github.com/stretchr/testify/assert"
)

func TestEC2Instance(t *testing.T) {
    t.Parallel()

    terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
        TerraformDir: "../modules/ec2",
        Vars: map[string]interface{}{
            "name":          "test-instance",
            "instance_type": "t3.micro",
            "ami":           "ami-0c55b159cbfafe1f0",
        },
    })

    defer terraform.Destroy(t, terraformOptions)
    terraform.InitAndApply(t, terraformOptions)

    instanceID := terraform.Output(t, terraformOptions, "instance_id")

    // Validate using AWS SDK
    sess := session.Must(session.NewSession(&aws.Config{
        Region: aws.String("us-east-1"),
    }))
    svc := ec2.New(sess)

    result, err := svc.DescribeInstances(&ec2.DescribeInstancesInput{
        InstanceIds: []*string{aws.String(instanceID)},
    })
    assert.NoError(t, err)
    assert.Equal(t, 1, len(result.Reservations))

    instance := result.Reservations[0].Instances[0]
    assert.Equal(t, "t3.micro", aws.StringValue(instance.InstanceType))
    assert.Equal(t, "running", aws.StringValue(instance.State.Name))
}
```

### Testing EKS Cluster

```go
// test/eks_test.go
package test

import (
    "testing"
    "time"

    "github.com/gruntwork-io/terratest/modules/k8s"
    "github.com/gruntwork-io/terratest/modules/terraform"
    "github.com/stretchr/testify/assert"
)

func TestEKSCluster(t *testing.T) {
    t.Parallel()

    terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
        TerraformDir: "../modules/eks",
        Vars: map[string]interface{}{
            "cluster_name":       "test-eks",
            "kubernetes_version": "1.28",
            "node_count":         2,
        },
    })

    defer terraform.Destroy(t, terraformOptions)
    terraform.InitAndApply(t, terraformOptions)

    // Get kubeconfig
    kubeconfigPath := terraform.Output(t, terraformOptions, "kubeconfig_path")

    // Test Kubernetes connectivity
    options := k8s.NewKubectlOptions("", kubeconfigPath, "default")

    // Wait for nodes to be ready
    k8s.WaitUntilNumNodesReady(t, options, 2, 30, 10*time.Second)

    // Verify cluster info
    nodes := k8s.GetNodes(t, options)
    assert.Equal(t, 2, len(nodes))

    // Deploy test workload
    k8s.KubectlApply(t, options, "../test/fixtures/nginx-deployment.yaml")
    k8s.WaitUntilDeploymentAvailable(t, options, "nginx", 60, 5*time.Second)
}
```

## Contract Testing

### Module Output Validation

```go
// test/module_contract_test.go
package test

import (
    "testing"

    "github.com/gruntwork-io/terratest/modules/terraform"
    "github.com/stretchr/testify/assert"
)

func TestVPCModuleContract(t *testing.T) {
    t.Parallel()

    terraformOptions := &terraform.Options{
        TerraformDir: "../modules/vpc",
        Vars: map[string]interface{}{
            "name":               "contract-test",
            "cidr_block":         "10.0.0.0/16",
            "availability_zones": []string{"us-east-1a"},
            "private_subnets":    []string{"10.0.1.0/24"},
            "public_subnets":     []string{"10.0.101.0/24"},
        },
        PlanFilePath: "./vpc.tfplan",
    }

    // Only run plan, don't apply
    terraform.Init(t, terraformOptions)
    planStruct := terraform.InitAndPlanAndShowWithStruct(t, terraformOptions)

    // Verify expected outputs exist
    outputs := planStruct.RawPlan.PlannedValues.Outputs

    requiredOutputs := []string{
        "vpc_id",
        "vpc_cidr_block",
        "private_subnet_ids",
        "public_subnet_ids",
    }

    for _, output := range requiredOutputs {
        _, exists := outputs[output]
        assert.True(t, exists, "Required output %s is missing", output)
    }
}
```

### Plan Testing

```go
// test/plan_test.go
package test

import (
    "testing"

    "github.com/gruntwork-io/terratest/modules/terraform"
    "github.com/stretchr/testify/assert"
)

func TestPlanResources(t *testing.T) {
    t.Parallel()

    terraformOptions := &terraform.Options{
        TerraformDir: "../environments/dev",
        Vars: map[string]interface{}{
            "environment": "test",
        },
    }

    terraform.Init(t, terraformOptions)
    planStruct := terraform.InitAndPlanAndShowWithStruct(t, terraformOptions)

    // Count resources by type
    resourceCounts := make(map[string]int)
    for _, resource := range planStruct.ResourcePlannedValuesMap {
        resourceCounts[resource.Type]++
    }

    // Verify expected resources
    assert.GreaterOrEqual(t, resourceCounts["aws_vpc"], 1)
    assert.GreaterOrEqual(t, resourceCounts["aws_subnet"], 2)

    // Verify no unwanted changes
    changes := planStruct.ResourceChangesMap
    for name, change := range changes {
        // No resources should be destroyed
        assert.NotContains(t, change.Change.Actions, "delete",
            "Resource %s should not be deleted", name)
    }
}
```

## Integration Testing

### Full Stack Test

```go
// test/integration_test.go
package test

import (
    "crypto/tls"
    "fmt"
    "net/http"
    "testing"
    "time"

    http_helper "github.com/gruntwork-io/terratest/modules/http-helper"
    "github.com/gruntwork-io/terratest/modules/terraform"
)

func TestFullStack(t *testing.T) {
    t.Parallel()

    terraformOptions := terraform.WithDefaultRetryableErrors(t, &terraform.Options{
        TerraformDir: "../environments/test",
        Vars: map[string]interface{}{
            "environment": "integration-test",
        },
    })

    defer terraform.Destroy(t, terraformOptions)
    terraform.InitAndApply(t, terraformOptions)

    // Get ALB DNS name
    albDNS := terraform.Output(t, terraformOptions, "alb_dns_name")
    url := fmt.Sprintf("https://%s/health", albDNS)

    // Test HTTPS endpoint
    tlsConfig := &tls.Config{InsecureSkipVerify: true}
    httpClient := &http.Client{
        Timeout: 10 * time.Second,
        Transport: &http.Transport{
            TLSClientConfig: tlsConfig,
        },
    }

    // Retry until healthy
    http_helper.HttpGetWithRetryWithCustomValidation(
        t,
        url,
        tlsConfig,
        30,
        10*time.Second,
        func(status int, body string) bool {
            return status == 200
        },
    )
}
```

## Testing Patterns

### Test Fixtures

```
test/
├── fixtures/
│   ├── minimal/
│   │   ├── main.tf
│   │   └── terraform.tfvars
│   ├── complete/
│   │   ├── main.tf
│   │   └── terraform.tfvars
│   └── kubernetes/
│       ├── nginx-deployment.yaml
│       └── test-service.yaml
├── vpc_test.go
├── eks_test.go
└── integration_test.go
```

### Minimal Test Fixture

```hcl
# test/fixtures/minimal/main.tf
module "vpc" {
  source = "../../../modules/vpc"

  name               = "test-minimal"
  cidr_block         = "10.0.0.0/16"
  availability_zones = ["us-east-1a"]
  private_subnets    = ["10.0.1.0/24"]
  public_subnets     = ["10.0.101.0/24"]
}

output "vpc_id" {
  value = module.vpc.vpc_id
}
```

### Complete Test Fixture

```hcl
# test/fixtures/complete/main.tf
module "vpc" {
  source = "../../../modules/vpc"

  name                 = "test-complete"
  cidr_block           = "10.0.0.0/16"
  availability_zones   = ["us-east-1a", "us-east-1b", "us-east-1c"]
  private_subnets      = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets       = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
  enable_nat_gateway   = true
  single_nat_gateway   = false
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Test = "complete"
  }
}
```

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/terraform-test.yml
name: Terraform Tests

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  static-analysis:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: 1.6.0

      - name: Terraform Format
        run: terraform fmt -check -recursive

      - name: Terraform Validate
        run: |
          for dir in $(find . -name "*.tf" -exec dirname {} \; | sort -u); do
            terraform -chdir="$dir" init -backend=false
            terraform -chdir="$dir" validate
          done

      - name: TFLint
        uses: terraform-linters/setup-tflint@v4
      - run: |
          tflint --init
          tflint --recursive

      - name: Checkov
        uses: bridgecrewio/checkov-action@v12
        with:
          directory: .
          framework: terraform

  unit-tests:
    runs-on: ubuntu-latest
    needs: static-analysis
    steps:
      - uses: actions/checkout@v4

      - name: Setup Go
        uses: actions/setup-go@v4
        with:
          go-version: '1.21'

      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Run Tests
        run: |
          cd test
          go test -v -timeout 60m
```

### Makefile for Testing

```makefile
# Makefile

.PHONY: test test-unit test-integration lint validate

validate:
	@echo "Validating Terraform..."
	@find . -name "*.tf" -exec dirname {} \; | sort -u | \
		xargs -I {} sh -c 'terraform -chdir={} init -backend=false && terraform -chdir={} validate'

lint:
	@echo "Linting Terraform..."
	terraform fmt -check -recursive
	tflint --recursive
	checkov -d .

test-unit:
	@echo "Running unit tests..."
	cd test && go test -v -run TestUnit -timeout 30m

test-integration:
	@echo "Running integration tests..."
	cd test && go test -v -run TestIntegration -timeout 60m

test: lint validate test-unit

test-all: lint validate test-unit test-integration
```

## Best Practices Summary

1. **Static analysis first** - Run fmt, validate, lint before tests
2. **Test in isolation** - Use separate state for tests
3. **Clean up resources** - Always destroy test infrastructure
4. **Use test fixtures** - Standardize test inputs
5. **Parallel execution** - Run tests in parallel when possible
6. **Test both success and failure** - Validate error handling
7. **Integration in CI/CD** - Automate all testing
8. **Cost awareness** - Use small resources, limit test duration
