---
name: gitlab-ci
description: GitLab CI/CD implementation
category: devops/ci-cd
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# GitLab CI

## Overview

GitLab CI/CD is a built-in continuous integration and delivery platform
that enables automated testing, building, and deployment.

## Complete CI/CD Pipeline

```yaml
# .gitlab-ci.yml
stages:
  - validate
  - build
  - test
  - security
  - package
  - deploy

variables:
  DOCKER_HOST: tcp://docker:2376
  DOCKER_TLS_CERTDIR: "/certs"
  DOCKER_TLS_VERIFY: 1
  DOCKER_CERT_PATH: "$DOCKER_TLS_CERTDIR/client"
  IMAGE_TAG: $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA

# =============================================================================
# Templates
# =============================================================================
.node-setup: &node-setup
  image: node:20-alpine
  cache:
    key: ${CI_COMMIT_REF_SLUG}
    paths:
      - node_modules/
      - .npm/
  before_script:
    - npm ci --cache .npm --prefer-offline

.docker-setup: &docker-setup
  image: docker:24
  services:
    - docker:24-dind
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY

# =============================================================================
# Validate Stage
# =============================================================================
lint:
  <<: *node-setup
  stage: validate
  script:
    - npm run lint
    - npm run type-check
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH

format-check:
  <<: *node-setup
  stage: validate
  script:
    - npm run format:check
  allow_failure: true

# =============================================================================
# Build Stage
# =============================================================================
build:
  <<: *node-setup
  stage: build
  script:
    - npm run build
  artifacts:
    paths:
      - dist/
    expire_in: 1 day

# =============================================================================
# Test Stage
# =============================================================================
unit-tests:
  <<: *node-setup
  stage: test
  script:
    - npm run test:unit -- --coverage
  coverage: '/All files[^|]*\|[^|]*\s+([\d\.]+)/'
  artifacts:
    when: always
    reports:
      junit: junit.xml
      coverage_report:
        coverage_format: cobertura
        path: coverage/cobertura-coverage.xml

integration-tests:
  <<: *node-setup
  stage: test
  services:
    - postgres:16-alpine
    - redis:7-alpine
  variables:
    POSTGRES_DB: testdb
    POSTGRES_USER: test
    POSTGRES_PASSWORD: test
    DATABASE_URL: postgresql://test:test@postgres:5432/testdb
    REDIS_URL: redis://redis:6379
  script:
    - npm run db:migrate
    - npm run test:integration
  artifacts:
    when: always
    reports:
      junit: junit-integration.xml

e2e-tests:
  <<: *node-setup
  stage: test
  image: mcr.microsoft.com/playwright:v1.40.0-focal
  script:
    - npm run test:e2e
  artifacts:
    when: always
    paths:
      - playwright-report/
    reports:
      junit: e2e-results.xml
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"

# =============================================================================
# Security Stage
# =============================================================================
dependency-scan:
  <<: *node-setup
  stage: security
  script:
    - npm audit --audit-level=high
  allow_failure: true

sast:
  stage: security
  include:
    - template: Security/SAST.gitlab-ci.yml

container-scan:
  stage: security
  needs: [docker-build]
  image:
    name: aquasec/trivy:latest
    entrypoint: [""]
  script:
    - trivy image --exit-code 1 --severity CRITICAL,HIGH $IMAGE_TAG
  allow_failure: true

# =============================================================================
# Package Stage
# =============================================================================
docker-build:
  <<: *docker-setup
  stage: package
  needs: [build, unit-tests]
  script:
    - docker build -t $IMAGE_TAG .
    - docker push $IMAGE_TAG
    - |
      if [ "$CI_COMMIT_BRANCH" == "$CI_DEFAULT_BRANCH" ]; then
        docker tag $IMAGE_TAG $CI_REGISTRY_IMAGE:latest
        docker push $CI_REGISTRY_IMAGE:latest
      fi
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
    - if: $CI_COMMIT_BRANCH == "develop"

# =============================================================================
# Deploy Stage
# =============================================================================
.deploy-template: &deploy-template
  image: bitnami/kubectl:latest
  before_script:
    - kubectl config set-cluster k8s --server="$KUBE_URL" --insecure-skip-tls-verify=true
    - kubectl config set-credentials admin --token="$KUBE_TOKEN"
    - kubectl config set-context default --cluster=k8s --user=admin --namespace=$KUBE_NAMESPACE
    - kubectl config use-context default

deploy-staging:
  <<: *deploy-template
  stage: deploy
  environment:
    name: staging
    url: https://staging.example.com
    on_stop: stop-staging
  variables:
    KUBE_NAMESPACE: staging
  script:
    - kubectl set image deployment/api api=$IMAGE_TAG -n $KUBE_NAMESPACE
    - kubectl rollout status deployment/api -n $KUBE_NAMESPACE --timeout=300s
  rules:
    - if: $CI_COMMIT_BRANCH == "develop"

stop-staging:
  <<: *deploy-template
  stage: deploy
  environment:
    name: staging
    action: stop
  variables:
    KUBE_NAMESPACE: staging
  script:
    - kubectl scale deployment/api --replicas=0 -n $KUBE_NAMESPACE
  when: manual
  rules:
    - if: $CI_COMMIT_BRANCH == "develop"

deploy-production:
  <<: *deploy-template
  stage: deploy
  environment:
    name: production
    url: https://example.com
  variables:
    KUBE_NAMESPACE: production
  script:
    - kubectl set image deployment/api api=$IMAGE_TAG -n $KUBE_NAMESPACE
    - kubectl rollout status deployment/api -n $KUBE_NAMESPACE --timeout=300s
  when: manual
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

## Multi-Project Pipelines

### Parent Pipeline

```yaml
# .gitlab-ci.yml (parent project)
stages:
  - trigger

trigger-frontend:
  stage: trigger
  trigger:
    project: mygroup/frontend
    branch: main
    strategy: depend

trigger-backend:
  stage: trigger
  trigger:
    project: mygroup/backend
    branch: main
    strategy: depend
```

### Child Pipeline

```yaml
# Child pipeline in same repo
stages:
  - build
  - deploy

include:
  - local: '/ci/build.yml'
  - local: '/ci/deploy.yml'

# Trigger child pipeline
trigger-deploy:
  stage: deploy
  trigger:
    include: ci/deploy-pipeline.yml
    strategy: depend
```

## Dynamic Child Pipelines

```yaml
generate-pipeline:
  stage: build
  script:
    - |
      cat > child-pipeline.yml << EOF
      stages:
        - test

      test-${SERVICE}:
        stage: test
        script:
          - echo "Testing ${SERVICE}"
      EOF
  artifacts:
    paths:
      - child-pipeline.yml

run-child-pipeline:
  stage: test
  needs: [generate-pipeline]
  trigger:
    include:
      - artifact: child-pipeline.yml
        job: generate-pipeline
    strategy: depend
```

## Rules and Conditions

```yaml
# Complex rules
deploy:
  stage: deploy
  script:
    - ./deploy.sh
  rules:
    # Deploy on main branch
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
      when: manual
    # Deploy on tags
    - if: $CI_COMMIT_TAG
      when: on_success
    # Deploy on schedule
    - if: $CI_PIPELINE_SOURCE == "schedule"
      when: on_success
    # Never deploy on MRs
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
      when: never
    # Default: don't run
    - when: never

# Using changes
test:
  stage: test
  script:
    - npm test
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
      changes:
        - src/**/*
        - tests/**/*
        - package.json
```

## Caching Strategies

```yaml
# Global cache configuration
cache:
  key:
    files:
      - package-lock.json
  paths:
    - node_modules/
  policy: pull-push

# Job-specific cache
build:
  cache:
    - key: ${CI_COMMIT_REF_SLUG}
      paths:
        - node_modules/
      policy: pull  # Only pull, don't update
    - key: build-cache
      paths:
        - dist/
      policy: push  # Only push, don't pull

# Distributed cache with S3
variables:
  CACHE_S3_SERVER_ADDRESS: s3.amazonaws.com
  CACHE_S3_BUCKET: gitlab-runner-cache
  CACHE_S3_ACCESS_KEY: $AWS_ACCESS_KEY_ID
  CACHE_S3_SECRET_KEY: $AWS_SECRET_ACCESS_KEY
```

## Artifacts Configuration

```yaml
build:
  stage: build
  script:
    - npm run build
  artifacts:
    name: "$CI_JOB_NAME-$CI_COMMIT_REF_NAME"
    paths:
      - dist/
    exclude:
      - dist/**/*.map
    expire_in: 1 week
    when: on_success
    reports:
      junit: junit.xml
      coverage_report:
        coverage_format: cobertura
        path: coverage/cobertura-coverage.xml
      dotenv: build.env
```

## Environments

```yaml
# Review apps (dynamic environments)
deploy-review:
  stage: deploy
  environment:
    name: review/$CI_COMMIT_REF_SLUG
    url: https://$CI_COMMIT_REF_SLUG.review.example.com
    on_stop: stop-review
    auto_stop_in: 1 week
  script:
    - helm install review-$CI_COMMIT_REF_SLUG ./chart --set image.tag=$CI_COMMIT_SHA
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"

stop-review:
  stage: deploy
  environment:
    name: review/$CI_COMMIT_REF_SLUG
    action: stop
  script:
    - helm uninstall review-$CI_COMMIT_REF_SLUG
  when: manual
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```

## Protected Variables and Secrets

```yaml
deploy-production:
  stage: deploy
  variables:
    # Protected variables only available in protected branches/tags
    DATABASE_URL: $PROD_DATABASE_URL
    API_KEY: $PROD_API_KEY
  script:
    - ./deploy.sh
  environment:
    name: production
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

## Services and Dependencies

```yaml
# Using services
test:
  stage: test
  services:
    - name: postgres:16-alpine
      alias: db
      variables:
        POSTGRES_DB: test
        POSTGRES_USER: test
        POSTGRES_PASSWORD: test
    - name: redis:7-alpine
      alias: cache
    - name: elasticsearch:8.10.0
      alias: search
      command: ["elasticsearch", "-Ediscovery.type=single-node"]
  variables:
    DATABASE_URL: postgresql://test:test@db:5432/test
    REDIS_URL: redis://cache:6379
    ELASTICSEARCH_URL: http://search:9200
  script:
    - npm run test:integration
```

## Parallel Jobs

```yaml
# Parallel matrix
test:
  stage: test
  parallel:
    matrix:
      - NODE_VERSION: ['18', '20', '22']
        DATABASE: ['postgres', 'mysql']
  image: node:${NODE_VERSION}
  services:
    - name: ${DATABASE}:latest
  script:
    - npm test

# Split large test suites
test:
  stage: test
  parallel: 4
  script:
    - npm run test:unit -- --shard=$CI_NODE_INDEX/$CI_NODE_TOTAL
```

## DAG (Directed Acyclic Graph)

```yaml
stages:
  - build
  - test
  - deploy

build-frontend:
  stage: build
  script: npm run build:frontend

build-backend:
  stage: build
  script: npm run build:backend

test-frontend:
  stage: test
  needs: [build-frontend]  # Only waits for build-frontend
  script: npm run test:frontend

test-backend:
  stage: test
  needs: [build-backend]  # Only waits for build-backend
  script: npm run test:backend

deploy:
  stage: deploy
  needs: [test-frontend, test-backend]
  script: ./deploy.sh
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│                GitLab CI Best Practices                          │
├─────────────────────────────────────────────────────────────────┤
│ ☐ Use stages to organize pipeline flow                          │
│ ☐ Leverage caching for faster builds                            │
│ ☐ Use artifacts to pass data between jobs                       │
│ ☐ Implement parallel jobs for faster execution                  │
│ ☐ Use DAG (needs) for optimized job ordering                    │
│ ☐ Define reusable templates with YAML anchors                   │
│ ☐ Use rules instead of only/except                              │
│ ☐ Protect sensitive variables                                   │
│ ☐ Set up environments for deployments                           │
│ ☐ Use services for integration testing                          │
│ ☐ Implement review apps for MRs                                 │
│ ☐ Add timeout limits to jobs                                    │
└─────────────────────────────────────────────────────────────────┘
```
