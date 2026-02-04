# Cloud Migration Workflow

Workflow cho di chuyển hệ thống từ on-premise lên cloud - áp dụng 6 Rs of Cloud Migration.

## Overview

| Attribute | Value |
|-----------|-------|
| **Type** | Migration Type |
| **Duration** | 2-6 tháng |
| **Team Size** | 3-10 người |
| **Quality Gates** | Full + Cloud Gates (C1→C4) |
| **Risk Level** | Medium-High |
| **Starting Point** | requirements |

## When to Use

### Ideal For

- On-premise to cloud migration
- Data center consolidation
- Cloud-to-cloud migration
- Hybrid cloud setup

### Prerequisites

- Cloud account setup
- Network connectivity planned
- Security/compliance reviewed
- Cost estimates approved

## 6 Rs of Cloud Migration

```
┌─────────────────────────────────────────────────────────────────┐
│                    6 Rs OF CLOUD MIGRATION                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │   REHOST    │  │ REPLATFORM  │  │ REPURCHASE  │            │
│  │ (Lift&Shift)│  │(Lift&Tinker)│  │  (Replace)  │            │
│  │             │  │             │  │             │            │
│  │ Fastest     │  │ Some optim. │  │ Buy SaaS    │            │
│  │ No changes  │  │ Minor mods  │  │ Replace app │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │  REFACTOR   │  │   RETIRE    │  │   RETAIN    │            │
│  │(Re-architect)│  │ (Eliminate) │  │   (Keep)    │            │
│  │             │  │             │  │             │            │
│  │ Cloud-native│  │ Decomm apps │  │ Stay on-prem│            │
│  │ Major work  │  │ No longer   │  │ Can't move  │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Strategy Selection Matrix

| Factor | Rehost | Replatform | Refactor |
|--------|--------|------------|----------|
| Timeline | Weeks | Months | Months |
| Cost | Low | Medium | High |
| Optimization | None | Some | Full |
| Complexity | Low | Medium | High |
| Cloud Benefits | Limited | Moderate | Maximum |

## Cloud Gates

Ngoài Quality Gates tiêu chuẩn, Cloud Migration có thêm:

| Gate | Name | Description |
|------|------|-------------|
| **C1** | Cloud Readiness | Infrastructure và security ready |
| **C2** | Migration Validated | Application works in cloud |
| **C3** | Performance Validated | Meets performance requirements |
| **C4** | Cutover Complete | Full production in cloud |

## Phases

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CLOUD MIGRATION WORKFLOW                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐          │
│  │ Phase 1 │─▶│ Phase 2 │─▶│ Phase 3 │─▶│ Phase 4 │─▶│ Phase 5 │          │
│  │ Assess  │  │  Plan   │  │ Prepare │  │ Migrate │  │Optimize │          │
│  │  D1     │  │ D2→C1   │  │ D3→D4   │  │ C2→C3   │  │ C4→G4   │          │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘          │
│                                                                             │
│  Duration:     Duration:    Duration:    Duration:    Duration:             │
│  2-3 weeks     2-4 weeks    2-4 weeks    4-12 weeks   2-4 weeks            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Phase 1: Assess (D1)

**Duration**: 2-3 weeks
**Gate**: D1 (Research Complete)

**Objectives**:
- Inventory tất cả workloads
- Assess cloud readiness
- Categorize theo 6 Rs
- Cost analysis

**Activities**:
```bash
# 1. Initialize cloud migration
/f5:init cloud-migration --workflow cloud-migration

# 2. Application inventory
/f5:cloud inventory --scan

# 3. Cloud readiness assessment
/f5:cloud assess-readiness

# 4. 6R categorization
/f5:cloud categorize-6r

# 5. Cost projection
/f5:cloud cost-estimate

# 6. Complete D1
/f5:gate complete D1
```

**Application Assessment Matrix**:
```markdown
| App | Strategy | Complexity | Dependencies | Priority |
|-----|----------|------------|--------------|----------|
| App1 | Rehost | Low | None | High |
| App2 | Replatform | Medium | DB | Medium |
| App3 | Refactor | High | Multiple | Low |
| App4 | Retire | - | - | - |
| App5 | Retain | - | Compliance | - |
```

**Deliverables**:
- [ ] Application Inventory
- [ ] Cloud Readiness Report
- [ ] 6R Categorization
- [ ] Cost Analysis
- [ ] Migration Prioritization

### Phase 2: Plan (D2→C1)

**Duration**: 2-4 weeks
**Gates**: D2 (SRS), C1 (Cloud Readiness)

**Objectives**:
- Design cloud architecture
- Plan network connectivity
- Security architecture
- Migration wave planning

**Activities**:
```bash
# 1. Cloud architecture design
/f5:design generate cloud-architecture

# 2. Network design
/f5:design generate network --hybrid

# 3. Security design
/f5:design generate cloud-security

# 4. Migration waves
/f5:cloud plan-waves

# 5. Complete D2
/f5:gate complete D2

# 6. Complete C1
/f5:gate complete C1
```

**Cloud Architecture Considerations**:
```
┌─────────────────────────────────────────────────────────────┐
│                  CLOUD ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Network:                                                   │
│  ├── VPC/VNet design                                       │
│  ├── Subnets (public/private)                              │
│  ├── VPN/Direct Connect                                    │
│  └── Load balancers                                        │
│                                                             │
│  Security:                                                  │
│  ├── IAM roles/policies                                    │
│  ├── Security groups/firewalls                             │
│  ├── Encryption (at rest, in transit)                      │
│  └── Compliance requirements                               │
│                                                             │
│  Compute:                                                   │
│  ├── Instance sizing                                       │
│  ├── Auto-scaling policies                                 │
│  ├── Container strategy (if applicable)                    │
│  └── Serverless options                                    │
│                                                             │
│  Data:                                                      │
│  ├── Database migration approach                           │
│  ├── Storage strategy                                      │
│  ├── Backup/DR                                             │
│  └── Data residency                                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Migration Wave Plan**:
```markdown
## Wave 1: Low-risk, Low-dependency
- App1 (Rehost)
- App5 (Rehost)
Duration: 2 weeks

## Wave 2: Medium complexity
- App2 (Replatform)
- App6 (Rehost)
Duration: 3 weeks

## Wave 3: High complexity
- App3 (Refactor)
Duration: 6 weeks

## Wave 4: Dependencies resolved
- App4 (Replatform)
Duration: 2 weeks
```

**Deliverables**:
- [ ] Cloud Architecture Document
- [ ] Network Design
- [ ] Security Architecture
- [ ] Migration Wave Plan
- [ ] Rollback Strategy

### Phase 3: Prepare (D3→D4)

**Duration**: 2-4 weeks
**Gates**: D3 (Basic Design), D4 (Detail Design)

**Objectives**:
- Setup cloud infrastructure
- Configure networking
- Setup security controls
- Prepare migration tools

**Activities**:
```bash
# 1. Provision cloud infrastructure
/f5:cloud provision infrastructure

# 2. Configure networking
/f5:cloud configure network

# 3. Setup security
/f5:cloud configure security

# 4. Setup migration tools
/f5:cloud setup-tools

# 5. Test connectivity
/f5:cloud test connectivity

# 6. Complete D3, D4
/f5:gate complete D3
/f5:gate complete D4
```

**Infrastructure as Code**:
```hcl
# Example Terraform for AWS
module "vpc" {
  source = "./modules/vpc"

  cidr_block = "10.0.0.0/16"

  public_subnets  = ["10.0.1.0/24", "10.0.2.0/24"]
  private_subnets = ["10.0.10.0/24", "10.0.20.0/24"]

  enable_nat_gateway = true
  enable_vpn_gateway = true
}

module "security" {
  source = "./modules/security"

  vpc_id = module.vpc.vpc_id

  ingress_rules = var.ingress_rules
  egress_rules  = var.egress_rules
}
```

**Deliverables**:
- [ ] Cloud Infrastructure Deployed
- [ ] Network Configured
- [ ] Security Controls Active
- [ ] Migration Tools Ready
- [ ] Connectivity Verified

### Phase 4: Migrate (C2→C3)

**Duration**: 4-12 weeks
**Gates**: C2 (Migration Validated), C3 (Performance Validated)

**Objectives**:
- Execute migration waves
- Validate each application
- Performance testing
- Fix issues

**Activities (Per Wave)**:
```bash
# For each application in wave:

# 1. Pre-migration check
/f5:cloud pre-migrate-check app1

# 2. Execute migration
/f5:cloud migrate app1 --strategy rehost

# 3. Validate functionality
/f5:cloud validate app1 --functional

# 4. Complete C2 for app
/f5:gate complete C2 --app app1

# 5. Performance test
/f5:cloud test-performance app1

# 6. Complete C3 for app
/f5:gate complete C3 --app app1

# 7. Cutover traffic
/f5:cloud cutover app1

# 8. Monitor
/f5:monitor app1 --duration 24h
```

**Migration Strategies Execution**:

#### Rehost (Lift & Shift)
```bash
# Using AWS Server Migration Service
/f5:cloud migrate --strategy rehost --tool aws-sms

# Steps:
# 1. Install SMS agent
# 2. Configure replication
# 3. Test migration
# 4. Final cutover
```

#### Replatform
```bash
# Example: Migrate to managed database
/f5:cloud migrate --strategy replatform --component database

# Steps:
# 1. Setup target (RDS, Cloud SQL)
# 2. Configure DMS replication
# 3. Sync data
# 4. Cutover
```

#### Refactor
```bash
# Containerize and deploy to Kubernetes
/f5:cloud migrate --strategy refactor --target kubernetes

# Steps:
# 1. Containerize application
# 2. Deploy to staging cluster
# 3. Test thoroughly
# 4. Production deployment
```

**Deliverables**:
- [ ] Applications Migrated
- [ ] Functional Validation Reports
- [ ] Performance Test Results
- [ ] Cutover Completed per Wave

### Phase 5: Optimize (C4→G4)

**Duration**: 2-4 weeks
**Gates**: C4 (Cutover Complete), G4 (Deployment Ready)

**Objectives**:
- Optimize cloud resources
- Decommission on-premise
- Setup monitoring/alerting
- Cost optimization

**Activities**:
```bash
# 1. Complete all cutover
/f5:cloud cutover --verify-all

# 2. Complete C4
/f5:gate complete C4

# 3. Setup cloud monitoring
/f5:cloud setup-monitoring

# 4. Cost optimization
/f5:cloud optimize-cost

# 5. Decommission on-premise
/f5:cloud decommission-onprem

# 6. Documentation
/f5:doc cloud-operations

# 7. Complete G4
/f5:gate complete G4
```

**Cloud Optimization Areas**:
```
┌─────────────────────────────────────────────────────────────┐
│                  OPTIMIZATION CHECKLIST                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Cost Optimization:                                         │
│  ├── [ ] Right-size instances                              │
│  ├── [ ] Reserved instances/savings plans                  │
│  ├── [ ] Spot instances where applicable                   │
│  ├── [ ] Storage tiering                                   │
│  └── [ ] Delete unused resources                           │
│                                                             │
│  Performance Optimization:                                  │
│  ├── [ ] Enable auto-scaling                               │
│  ├── [ ] CDN configuration                                 │
│  ├── [ ] Database optimization                             │
│  └── [ ] Caching strategy                                  │
│                                                             │
│  Security Optimization:                                     │
│  ├── [ ] Enable cloud-native security                      │
│  ├── [ ] Configure backup policies                         │
│  ├── [ ] Setup compliance monitoring                       │
│  └── [ ] Enable encryption everywhere                      │
│                                                             │
│  Operations Optimization:                                   │
│  ├── [ ] CloudWatch/Stackdriver setup                      │
│  ├── [ ] Alerting configured                               │
│  ├── [ ] Runbooks created                                  │
│  └── [ ] On-call procedures                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Deliverables**:
- [ ] Cloud Operations Manual
- [ ] Cost Optimization Report
- [ ] Monitoring Dashboards
- [ ] On-premise Decommission Plan
- [ ] Handover Documentation

## Cost Management

### Cost Components

| Component | On-Premise | Cloud | Optimization |
|-----------|------------|-------|--------------|
| Compute | Fixed | Variable | Right-sizing |
| Storage | Fixed | Variable | Tiering |
| Network | Fixed | Variable | CDN, caching |
| Licensing | Fixed | Variable | BYOL/SaaS |
| Operations | High | Low | Automation |

### Cost Monitoring

```bash
# Setup cost alerts
/f5:cloud cost-alert --budget 10000 --threshold 80%

# Monthly cost review
/f5:cloud cost-report --monthly
```

## Security Considerations

### Shared Responsibility Model

```
┌─────────────────────────────────────────────────────────────┐
│               SHARED RESPONSIBILITY MODEL                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  CUSTOMER RESPONSIBILITY (Security IN the cloud):          │
│  ├── Customer data                                         │
│  ├── Platform, applications, IAM                           │
│  ├── Operating system, network, firewall config            │
│  ├── Client-side encryption                                │
│  └── Server-side encryption                                │
│                                                             │
│  ─────────────────────────────────────────────────────     │
│                                                             │
│  CLOUD PROVIDER RESPONSIBILITY (Security OF the cloud):    │
│  ├── Hardware/Infrastructure                               │
│  ├── Software (compute, storage, database, networking)     │
│  ├── Regions, availability zones, edge locations          │
│  └── Physical security                                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Security Checklist

- [ ] IAM roles configured (least privilege)
- [ ] MFA enabled for all users
- [ ] Encryption at rest enabled
- [ ] Encryption in transit (TLS)
- [ ] Security groups properly configured
- [ ] VPC flow logs enabled
- [ ] CloudTrail/audit logging
- [ ] Compliance standards met

## Best Practices

### 1. Start with Assessment

- Know what you're moving
- Understand dependencies
- Calculate true costs

### 2. Wave-Based Migration

- Don't migrate everything at once
- Start with low-risk apps
- Build confidence and expertise

### 3. Validate Thoroughly

- Functional testing
- Performance testing
- Security testing
- Disaster recovery testing

### 4. Plan for Rollback

- Keep on-premise running during validation
- Clear rollback triggers
- Tested rollback procedures

### 5. Optimize Continuously

- Right-size after migration
- Use cloud-native features
- Monitor costs

## Templates

- [Cloud Assessment Template](./templates/cloud-assessment.md)
- [Migration Wave Plan](./templates/wave-plan.md)
- [Cloud Architecture Template](./templates/cloud-architecture.md)
- [Cutover Runbook](./templates/cutover-runbook.md)
- [Cost Analysis Template](./templates/cost-analysis.md)

## Examples

- [AWS Migration](./examples/aws-migration/)
- [Azure Migration](./examples/azure-migration/)
- [GCP Migration](./examples/gcp-migration/)
- [Multi-Cloud Setup](./examples/multi-cloud/)

---

# ═══════════════════════════════════════════════════════════════
# F5 FEATURE INTEGRATION
# ═══════════════════════════════════════════════════════════════

## Auto-Activated Features Per Phase

| Phase | Mode | Persona | Verbosity | Recommended Agents |
|-------|------|---------|-----------|-------------------|
| Assess | 🔍 analytical | 📊 analyst | 4 | documenter |
| Plan | 🏗️ planning | 🏛️ architect | 4 | api_designer |
| Prepare | 🏗️ planning | 🔧 devops | 3 | - |
| Migrate | 💻 coding | 🔧 devops | 2 | code_generator |
| Optimize | 🔍 analytical | 🔧 devops | 3 | security_scanner |

## Phase-Specific Commands

### Phase 1: Assess (D1)

**Essential:**
```bash
/f5-load                         # Load project context
/f5-cloud inventory --scan       # Application inventory
/f5-cloud assess-readiness       # Cloud readiness
/f5-cloud categorize-6r          # 6R categorization
/f5-gate complete D1             # Complete D1
```

**Recommended:**
```bash
/f5-mode set analytical          # Deep analysis
/f5-cloud cost-estimate          # Cost projection
/f5-session checkpoint 'assessment-done'
```

### Phase 2: Plan (D2→C1)

**Essential:**
```bash
/f5-design generate cloud-architecture
/f5-design generate cloud-security
/f5-cloud plan-waves             # Migration wave plan
/f5-gate complete D2             # Complete D2
/f5-gate complete C1             # Complete C1
```

**Recommended:**
```bash
/f5-persona architect            # Architecture focus
/f5-agent invoke api_designer    # API design
/f5-session checkpoint 'plan-approved'
```

### Phase 3: Prepare (D3→D4)

**Essential:**
```bash
/f5-cloud provision infrastructure
/f5-cloud configure network
/f5-cloud configure security
/f5-cloud test connectivity
/f5-gate complete D3             # Complete D3
/f5-gate complete D4             # Complete D4
```

**Recommended:**
```bash
/f5-mode set planning            # Infrastructure planning
/f5-persona devops               # DevOps focus
```

### Phase 4: Migrate (C2→C3)

**Essential:**
```bash
/f5-cloud pre-migrate-check app1
/f5-cloud migrate app1 --strategy rehost
/f5-cloud validate app1 --functional
/f5-gate complete C2             # Complete C2
/f5-cloud test-performance app1
/f5-gate complete C3             # Complete C3
```

**Recommended:**
```bash
/f5-mode set coding              # Fast implementation
/f5-cloud cutover app1           # Cutover traffic
/f5-monitor app1 --duration 24h
```

### Phase 5: Optimize (C4→G4)

**Essential:**
```bash
/f5-cloud cutover --verify-all
/f5-gate complete C4             # Complete C4
/f5-cloud setup-monitoring
/f5-cloud optimize-cost
/f5-gate complete G4             # Complete G4
```

**Recommended:**
```bash
/f5-agent pipeline security_audit  # Final security
/f5-cloud decommission-onprem
/f5-doc cloud-operations
```

## Agent Pipelines

| Phase | Recommended Pipeline |
|-------|---------------------|
| Assess | - |
| Plan | - |
| Prepare | - |
| Migrate | - |
| Optimize | `security_audit` |

## Checkpoints

Create checkpoints at:
- [ ] After 6R categorization (Assess)
- [ ] After cloud architecture approved (Plan)
- [ ] After infrastructure provisioned (Prepare)
- [ ] After each wave migrated (Migrate)
- [ ] After optimization complete (Optimize)

## Integration with Other F5 Features

### TDD Mode
- Not typically used in cloud migration
- Use for application refactoring: `/f5-tdd start refactor`

### Code Review
- Required for: Infrastructure as Code (IaC)
- Run: `/f5-review code --type terraform`

### Analytics
- Track progress: `/f5-analytics summary`
- Cost tracking: `/f5-cloud cost-report --monthly`

### Health Check
- Before gates: `/f5-selftest`
- Cloud health: `/f5-cloud health-check`

## Cloud Migration-Specific Tips

### 6 Rs Strategy
| Strategy | When to Use | Mode |
|----------|-------------|------|
| Rehost | Quick migration, no changes | coding |
| Replatform | Minor optimizations | coding |
| Refactor | Cloud-native transformation | coding + TDD |
| Retire | Decommission unused | - |
| Retain | Keep on-premise | - |
| Repurchase | Replace with SaaS | - |

### Cloud Gates (C1-C4)
- C1: Cloud infrastructure ready
- C2: Migration validated
- C3: Performance validated
- C4: Cutover complete

### When to Use Agents

| Task | Agent/Pipeline |
|------|---------------|
| Cloud architecture design | `api_designer` |
| Documentation | `documenter` |
| Security review | `security_audit` pipeline |
| IaC code generation | `code_generator` |

### Wave-Based Migration
- Wave 1: Low-risk, low-dependency apps
- Wave 2: Medium complexity
- Wave 3: High complexity
- Each wave: Validate → Cutover → Monitor
