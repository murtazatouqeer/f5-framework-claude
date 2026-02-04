---
name: devops
description: DevOps practices, CI/CD, and infrastructure management
category: skill
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: true
context: inject
---

# DevOps Skills

## Overview

DevOps practices for continuous integration, delivery, and operations
to enable fast, reliable software delivery.

## DevOps Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│                       CONTINUOUS                                 │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌───────┐             │
│  │ Plan │→ │ Code │→ │Build │→ │ Test │→ │Release│             │
│  └──────┘  └──────┘  └──────┘  └──────┘  └───────┘             │
│      ↑                                        │                  │
│      │       INTEGRATION / DELIVERY           ↓                  │
│  ┌──────┐  ┌───────┐  ┌──────┐                                  │
│  │Learn │← │Monitor│← │Deploy│                                   │
│  └──────┘  └───────┘  └──────┘                                  │
│                     OPERATIONS                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Categories

### CI/CD
- Pipeline fundamentals
- GitHub Actions / GitLab CI
- Pipeline patterns
- Deployment strategies (Blue-Green, Canary)

### Containerization
- Docker fundamentals
- Docker Compose
- Container best practices
- Multi-stage builds

### Orchestration
- Kubernetes basics
- Helm charts
- Service mesh
- GitOps (ArgoCD, Flux)

### Monitoring
- Metrics and SLIs/SLOs
- Prometheus & Grafana
- Alerting strategies
- Dashboard design

### Logging
- Structured logging
- Log aggregation
- ELK/EFK stack
- Distributed tracing

### Infrastructure
- Infrastructure as Code
- Terraform
- Cloud patterns
- Cost optimization

### Reliability
- SRE fundamentals
- Incident management
- Chaos engineering
- Disaster recovery

## DORA Metrics

| Metric | Elite | High | Medium | Low |
|--------|-------|------|--------|-----|
| Deployment Frequency | On-demand | Weekly | Monthly | Yearly |
| Lead Time | < 1 day | 1 week | 1 month | > 6 months |
| Change Failure Rate | < 15% | 16-30% | 31-45% | > 45% |
| MTTR | < 1 hour | < 1 day | < 1 week | > 1 week |

## Skills Index

### CI/CD
- [CI/CD Fundamentals](ci-cd/ci-cd-fundamentals.md)
- [GitHub Actions](ci-cd/github-actions.md)
- [GitLab CI](ci-cd/gitlab-ci.md)
- [Pipeline Patterns](ci-cd/pipeline-patterns.md)
- [Deployment Strategies](ci-cd/deployment-strategies.md)

### Containerization
- [Docker Basics](containerization/docker-basics.md)
- [Docker Compose](containerization/docker-compose.md)
- [Container Best Practices](containerization/container-best-practices.md)
- [Multi-Stage Builds](containerization/multi-stage-builds.md)

### Orchestration
- [Kubernetes Basics](orchestration/kubernetes-basics.md)
- [Helm Charts](orchestration/helm-charts.md)
- [Service Mesh](orchestration/service-mesh.md)
- [GitOps](orchestration/gitops.md)

### Monitoring
- [Metrics Fundamentals](monitoring/metrics-fundamentals.md)
- [Prometheus & Grafana](monitoring/prometheus-grafana.md)
- [Alerting](monitoring/alerting.md)
- [Dashboards](monitoring/dashboards.md)

### Logging
- [Logging Best Practices](logging/logging-best-practices.md)
- [Structured Logging](logging/structured-logging.md)
- [ELK Stack](logging/elk-stack.md)
- [Log Aggregation](logging/log-aggregation.md)

### Infrastructure
- [IaC Fundamentals](infrastructure/iac-fundamentals.md)
- [Terraform Basics](infrastructure/terraform-basics.md)
- [Cloud Patterns](infrastructure/cloud-patterns.md)
- [Cost Optimization](infrastructure/cost-optimization.md)

### Reliability
- [SRE Fundamentals](reliability/sre-fundamentals.md)
- [Incident Management](reliability/incident-management.md)
- [Chaos Engineering](reliability/chaos-engineering.md)
- [Disaster Recovery](reliability/disaster-recovery.md)

## DevOps Maturity Model

```
┌─────────────────────────────────────────────────────────────────┐
│                    DevOps Maturity Levels                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Level 5: Optimizing                                            │
│  ├── Continuous improvement culture                              │
│  ├── Predictive analytics                                        │
│  └── Self-healing systems                                        │
│                                                                  │
│  Level 4: Measured                                               │
│  ├── Comprehensive metrics                                       │
│  ├── Data-driven decisions                                       │
│  └── Automated compliance                                        │
│                                                                  │
│  Level 3: Defined                                                │
│  ├── Standardized pipelines                                      │
│  ├── Infrastructure as Code                                      │
│  └── Centralized logging/monitoring                              │
│                                                                  │
│  Level 2: Managed                                                │
│  ├── Basic CI/CD                                                 │
│  ├── Some automation                                             │
│  └── Manual deployments                                          │
│                                                                  │
│  Level 1: Initial                                                │
│  ├── Ad-hoc processes                                            │
│  ├── Manual everything                                           │
│  └── Siloed teams                                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Best Practices

1. **Automate Everything** - Reduce manual toil
2. **Version Control All** - Code, configs, infrastructure
3. **Shift Left** - Test and secure early
4. **Measure What Matters** - Focus on DORA metrics
5. **Embrace Failure** - Learn from incidents
6. **Continuous Improvement** - Iterate and optimize
7. **Collaboration** - Break down silos
8. **Documentation** - Runbooks and playbooks
