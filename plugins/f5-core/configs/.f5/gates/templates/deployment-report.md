# Deployment Report

**Project:** {{PROJECT_NAME}}
**Version:** {{VERSION}}
**Date:** {{DATE}}
**Gate:** G4

---

## Deployment Summary

| Field | Value |
|-------|-------|
| Environment | {{ENVIRONMENT}} |
| Version | {{VERSION}} |
| Previous Version | {{PREVIOUS_VERSION}} |
| Deployment Time | {{DEPLOY_TIME}} |
| Duration | {{DEPLOY_DURATION}} |
| Status | {{STATUS}} |
| Deployer | {{DEPLOYER}} |

---

## Pre-Deployment Checklist

| Item | Status | Notes |
|------|--------|-------|
| G2 Gate Passed | {{G2_STATUS}} | {{G2_NOTES}} |
| G3 Gate Passed | {{G3_STATUS}} | {{G3_NOTES}} |
| Database Backup | {{BACKUP_STATUS}} | {{BACKUP_NOTES}} |
| Rollback Plan | {{ROLLBACK_STATUS}} | {{ROLLBACK_NOTES}} |
| Stakeholder Notification | {{NOTIFY_STATUS}} | {{NOTIFY_NOTES}} |
| Change Request Approved | {{CR_STATUS}} | {{CR_NOTES}} |
| Security Scan Passed | {{SECURITY_STATUS}} | {{SECURITY_NOTES}} |
| Load Test Passed | {{LOAD_STATUS}} | {{LOAD_NOTES}} |

---

## Deployment Steps

| Step | Status | Start Time | End Time | Duration | Notes |
|------|--------|------------|----------|----------|-------|
{{#each STEPS}}
| {{name}} | {{status}} | {{start_time}} | {{end_time}} | {{duration}} | {{notes}} |
{{/each}}

### Step Details

{{#each STEPS}}
#### {{order}}. {{name}} - {{status}}

**Command:** `{{command}}`
**Duration:** {{duration}}

{{#if output}}
**Output:**
```
{{output}}
```
{{/if}}

{{#if error}}
**Error:**
```
{{error}}
```
{{/if}}

{{/each}}

---

## Database Migrations

{{#if MIGRATIONS}}
### Migration Summary

| Total | Applied | Skipped | Failed |
|-------|---------|---------|--------|
| {{MIGRATION_TOTAL}} | {{MIGRATION_APPLIED}} | {{MIGRATION_SKIPPED}} | {{MIGRATION_FAILED}} |

### Migration Details

| Migration | Status | Duration | Notes |
|-----------|--------|----------|-------|
{{#each MIGRATIONS}}
| {{name}} | {{status}} | {{duration}} | {{notes}} |
{{/each}}

{{#if MIGRATION_SQL}}
### SQL Executed

```sql
{{MIGRATION_SQL}}
```
{{/if}}

{{else}}
No database migrations in this deployment.
{{/if}}

---

## Health Checks

### Endpoint Health

| Endpoint | Status | Response Time | Expected |
|----------|--------|---------------|----------|
{{#each HEALTH_CHECKS}}
| {{endpoint}} | {{status}} | {{response_time}} | {{expected_time}} |
{{/each}}

### Overall Health Status

```
┌─────────────────────────────────────┐
│  Application Health: {{HEALTH_STATUS}}
│  Database Health: {{DB_HEALTH}}
│  Cache Health: {{CACHE_HEALTH}}
│  Queue Health: {{QUEUE_HEALTH}}
└─────────────────────────────────────┘
```

---

## Smoke Tests

| Test | Status | Duration | Notes |
|------|--------|----------|-------|
{{#each SMOKE_TESTS}}
| {{name}} | {{status}} | {{duration}} | {{notes}} |
{{/each}}

### Smoke Test Summary

- **Total:** {{SMOKE_TOTAL}}
- **Passed:** {{SMOKE_PASSED}}
- **Failed:** {{SMOKE_FAILED}}
- **Pass Rate:** {{SMOKE_PASS_RATE}}%

{{#if SMOKE_FAILURES}}
### Failed Smoke Tests

{{#each SMOKE_FAILURES}}
#### :x: {{name}}

**Expected:** {{expected}}
**Actual:** {{actual}}
**Error:** {{error}}

{{/each}}
{{/if}}

---

## Metrics (Post-Deployment)

### Performance Comparison

| Metric | Before | After | Change | Status |
|--------|--------|-------|--------|--------|
| Error Rate | {{ERROR_BEFORE}} | {{ERROR_AFTER}} | {{ERROR_CHANGE}} | {{ERROR_STATUS}} |
| Response Time (p50) | {{RT50_BEFORE}} | {{RT50_AFTER}} | {{RT50_CHANGE}} | {{RT50_STATUS}} |
| Response Time (p95) | {{RT95_BEFORE}} | {{RT95_AFTER}} | {{RT95_CHANGE}} | {{RT95_STATUS}} |
| Response Time (p99) | {{RT99_BEFORE}} | {{RT99_AFTER}} | {{RT99_CHANGE}} | {{RT99_STATUS}} |
| Throughput | {{TP_BEFORE}} | {{TP_AFTER}} | {{TP_CHANGE}} | {{TP_STATUS}} |

### Resource Usage

| Metric | Before | After | Change | Status |
|--------|--------|-------|--------|--------|
| CPU Usage | {{CPU_BEFORE}} | {{CPU_AFTER}} | {{CPU_CHANGE}} | {{CPU_STATUS}} |
| Memory Usage | {{MEM_BEFORE}} | {{MEM_AFTER}} | {{MEM_CHANGE}} | {{MEM_STATUS}} |
| Disk I/O | {{DISK_BEFORE}} | {{DISK_AFTER}} | {{DISK_CHANGE}} | {{DISK_STATUS}} |
| Network I/O | {{NET_BEFORE}} | {{NET_AFTER}} | {{NET_CHANGE}} | {{NET_STATUS}} |

---

## Rollback Information

{{#if ROLLBACK_EXECUTED}}
### :warning: ROLLBACK EXECUTED

**Reason:** {{ROLLBACK_REASON}}
**Rolled back to:** {{ROLLBACK_VERSION}}
**Time:** {{ROLLBACK_TIME}}
**Duration:** {{ROLLBACK_DURATION}}

**Rollback Steps:**
{{#each ROLLBACK_STEPS}}
1. {{.}}
{{/each}}

{{else}}
### Rollback Plan (If Needed)

**Rollback Version:** {{ROLLBACK_VERSION}}
**Estimated Duration:** {{ROLLBACK_EST_DURATION}}

```bash
# Rollback command
{{ROLLBACK_COMMAND}}

# Verify rollback
{{VERIFY_COMMAND}}

# Database rollback (if needed)
{{DB_ROLLBACK_COMMAND}}
```

**Rollback Triggers:**
{{#each ROLLBACK_TRIGGERS}}
- {{.}}
{{/each}}

**Rollback Verification:**
{{#each ROLLBACK_VERIFICATION}}
- [ ] {{.}}
{{/each}}
{{/if}}

---

## Approvals

| Role | Approver | Status | Time |
|------|----------|--------|------|
{{#each APPROVERS}}
| {{role}} | {{name}} | {{status}} | {{time}} |
{{/each}}

---

## Release Notes

### Version {{VERSION}}

#### New Features
{{#each NEW_FEATURES}}
- {{.}}
{{/each}}

{{#unless NEW_FEATURES}}
No new features in this release.
{{/unless}}

#### Bug Fixes
{{#each BUG_FIXES}}
- {{.}}
{{/each}}

{{#unless BUG_FIXES}}
No bug fixes in this release.
{{/unless}}

#### Improvements
{{#each IMPROVEMENTS}}
- {{.}}
{{/each}}

{{#unless IMPROVEMENTS}}
No improvements in this release.
{{/unless}}

#### Breaking Changes
{{#if BREAKING_CHANGES}}
{{#each BREAKING_CHANGES}}
- :warning: {{.}}
{{/each}}
{{else}}
No breaking changes.
{{/if}}

#### Dependencies Updated
{{#each DEPENDENCIES_UPDATED}}
- `{{name}}`: {{old_version}} → {{new_version}}
{{/each}}

{{#unless DEPENDENCIES_UPDATED}}
No dependency updates.
{{/unless}}

---

## Configuration Changes

{{#if CONFIG_CHANGES}}
| Setting | Old Value | New Value | Environment |
|---------|-----------|-----------|-------------|
{{#each CONFIG_CHANGES}}
| {{setting}} | {{old_value}} | {{new_value}} | {{environment}} |
{{/each}}
{{else}}
No configuration changes in this deployment.
{{/if}}

---

## Artifacts

| Artifact | Location |
|----------|----------|
| Docker Image | {{DOCKER_IMAGE}} |
| Build Logs | {{BUILD_LOGS}} |
| Deployment Logs | {{DEPLOY_LOGS}} |
| Test Results | {{TEST_RESULTS}} |
| Monitoring Dashboard | {{DASHBOARD_URL}} |
| Incident Runbook | {{RUNBOOK_URL}} |

---

## Post-Deployment Actions

{{#each POST_DEPLOY_ACTIONS}}
- [{{#if completed}}x{{else}} {{/if}}] {{description}} ({{assignee}})
{{/each}}

---

## Lessons Learned

{{#if LESSONS}}
{{#each LESSONS}}
- **{{category}}:** {{description}}
{{/each}}
{{else}}
No lessons learned recorded.
{{/if}}

---

## Related Items

| Type | ID | Description |
|------|-----|-------------|
{{#each RELATED_ITEMS}}
| {{type}} | {{id}} | {{description}} |
{{/each}}

---

**Generated:** {{TIMESTAMP}}
**Deployed By:** {{DEPLOYER}}
**Deployment ID:** {{DEPLOYMENT_ID}}
