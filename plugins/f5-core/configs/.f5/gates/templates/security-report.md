# Security Report

**Project:** {{PROJECT_NAME}}
**Date:** {{DATE}}
**Scan Type:** {{SCAN_TYPE}}
**Gate:** {{GATE_ID}}

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Overall Score | {{SCORE}}/100 |
| Risk Level | {{RISK_LEVEL}} |
| Critical | {{CRITICAL}} |
| High | {{HIGH}} |
| Medium | {{MEDIUM}} |
| Low | {{LOW}} |

### Security Grade

```
┌─────────────────────────────────────┐
│  Security Score: {{SCORE}}/100      │
│  Grade: {{GRADE}}                   │
│  Risk Level: {{RISK_LEVEL}}         │
└─────────────────────────────────────┘
```

---

## OWASP Top 10 Compliance

| # | Vulnerability | Status | Details |
|---|---------------|--------|---------|
| A01 | Broken Access Control | {{A01_STATUS}} | {{A01_DETAILS}} |
| A02 | Cryptographic Failures | {{A02_STATUS}} | {{A02_DETAILS}} |
| A03 | Injection | {{A03_STATUS}} | {{A03_DETAILS}} |
| A04 | Insecure Design | {{A04_STATUS}} | {{A04_DETAILS}} |
| A05 | Security Misconfiguration | {{A05_STATUS}} | {{A05_DETAILS}} |
| A06 | Vulnerable Components | {{A06_STATUS}} | {{A06_DETAILS}} |
| A07 | Auth Failures | {{A07_STATUS}} | {{A07_DETAILS}} |
| A08 | Data Integrity | {{A08_STATUS}} | {{A08_DETAILS}} |
| A09 | Logging Failures | {{A09_STATUS}} | {{A09_DETAILS}} |
| A10 | SSRF | {{A10_STATUS}} | {{A10_DETAILS}} |

### OWASP Compliance Score: {{OWASP_SCORE}}/10

---

## Dependency Vulnerabilities

### Summary

| Severity | Count | Fixed |
|----------|-------|-------|
| Critical | {{CRITICAL_COUNT}} | {{CRITICAL_FIXED}} |
| High | {{HIGH_COUNT}} | {{HIGH_FIXED}} |
| Medium | {{MEDIUM_COUNT}} | {{MEDIUM_FIXED}} |
| Low | {{LOW_COUNT}} | {{LOW_FIXED}} |

### Critical Vulnerabilities

{{#if CRITICAL_VULNS}}
{{#each CRITICAL_VULNS}}
#### :rotating_light: {{package}}@{{version}}

- **CVE:** [{{cve}}](https://nvd.nist.gov/vuln/detail/{{cve}})
- **CVSS Score:** {{cvss}}
- **Description:** {{description}}
- **Affected Versions:** {{affected_versions}}
- **Fix:** Update to `{{fix_version}}`
- **Exploit Available:** {{exploit_available}}

```bash
# Fix command
{{fix_command}}
```

{{/each}}
{{else}}
No critical vulnerabilities found! :white_check_mark:
{{/if}}

### High Vulnerabilities

{{#if HIGH_VULNS}}
{{#each HIGH_VULNS}}
#### :warning: {{package}}@{{version}}

- **CVE:** [{{cve}}](https://nvd.nist.gov/vuln/detail/{{cve}})
- **CVSS Score:** {{cvss}}
- **Description:** {{description}}
- **Fix:** Update to `{{fix_version}}`

{{/each}}
{{else}}
No high severity vulnerabilities found! :white_check_mark:
{{/if}}

### Medium/Low Vulnerabilities

{{#if MEDIUM_LOW_VULNS}}
| Package | Version | Severity | CVE | Fix Version |
|---------|---------|----------|-----|-------------|
{{#each MEDIUM_LOW_VULNS}}
| {{package}} | {{version}} | {{severity}} | {{cve}} | {{fix_version}} |
{{/each}}
{{else}}
No medium/low vulnerabilities found! :white_check_mark:
{{/if}}

---

## Code Security Issues

{{#each CODE_ISSUES}}
### {{severity}}: {{title}}

**File:** `{{file}}:{{line}}`
**Rule:** {{rule}}
**CWE:** [{{cwe}}](https://cwe.mitre.org/data/definitions/{{cwe_id}}.html)

**Vulnerable Code:**
```{{language}}
{{code_snippet}}
```

**Issue:** {{description}}

**Recommendation:** {{recommendation}}

**Fixed Code:**
```{{language}}
{{fixed_code}}
```

---

{{/each}}

{{#unless CODE_ISSUES}}
No code security issues found! :white_check_mark:
{{/unless}}

---

## Authentication & Authorization

| Check | Status | Notes |
|-------|--------|-------|
| Password Hashing | {{PASS_HASH}} | {{PASS_HASH_NOTES}} |
| JWT Implementation | {{JWT}} | {{JWT_NOTES}} |
| Session Management | {{SESSION}} | {{SESSION_NOTES}} |
| RBAC | {{RBAC}} | {{RBAC_NOTES}} |
| API Authentication | {{API_AUTH}} | {{API_AUTH_NOTES}} |
| MFA Support | {{MFA}} | {{MFA_NOTES}} |
| Rate Limiting | {{RATE_LIMIT}} | {{RATE_LIMIT_NOTES}} |

---

## Data Protection

| Check | Status | Notes |
|-------|--------|-------|
| Data Encryption (at rest) | {{ENCRYPTION_REST}} | {{ENCRYPTION_REST_NOTES}} |
| Data Encryption (in transit) | {{ENCRYPTION_TRANSIT}} | {{ENCRYPTION_TRANSIT_NOTES}} |
| PII Handling | {{PII}} | {{PII_NOTES}} |
| Data Masking | {{MASKING}} | {{MASKING_NOTES}} |
| Secure Storage | {{STORAGE}} | {{STORAGE_NOTES}} |
| Key Management | {{KEY_MGMT}} | {{KEY_MGMT_NOTES}} |

---

## Input Validation

| Check | Status | Notes |
|-------|--------|-------|
| SQL Injection Prevention | {{SQL_INJECTION}} | {{SQL_INJECTION_NOTES}} |
| XSS Prevention | {{XSS}} | {{XSS_NOTES}} |
| CSRF Protection | {{CSRF}} | {{CSRF_NOTES}} |
| Command Injection | {{CMD_INJECTION}} | {{CMD_INJECTION_NOTES}} |
| Path Traversal | {{PATH_TRAVERSAL}} | {{PATH_TRAVERSAL_NOTES}} |
| Input Sanitization | {{INPUT_SANITIZE}} | {{INPUT_SANITIZE_NOTES}} |

---

## Security Headers

| Header | Status | Value |
|--------|--------|-------|
| Content-Security-Policy | {{CSP_STATUS}} | {{CSP_VALUE}} |
| X-Frame-Options | {{XFO_STATUS}} | {{XFO_VALUE}} |
| X-Content-Type-Options | {{XCTO_STATUS}} | {{XCTO_VALUE}} |
| Strict-Transport-Security | {{HSTS_STATUS}} | {{HSTS_VALUE}} |
| X-XSS-Protection | {{XXSS_STATUS}} | {{XXSS_VALUE}} |
| Referrer-Policy | {{RP_STATUS}} | {{RP_VALUE}} |

---

## Secrets Detection

{{#if SECRETS_FOUND}}
### :rotating_light: Secrets Detected!

| Type | File | Line | Status |
|------|------|------|--------|
{{#each SECRETS_FOUND}}
| {{type}} | {{file}} | {{line}} | {{status}} |
{{/each}}

**Action Required:** Remove these secrets immediately and rotate credentials!
{{else}}
No hardcoded secrets detected. :white_check_mark:
{{/if}}

---

## Recommendations

### Immediate Actions (Critical/High)

{{#each IMMEDIATE_ACTIONS}}
1. :rotating_light: {{.}}
{{/each}}

{{#unless IMMEDIATE_ACTIONS}}
No immediate actions required.
{{/unless}}

### Short-term (Medium)

{{#each SHORT_TERM_ACTIONS}}
1. :warning: {{.}}
{{/each}}

{{#unless SHORT_TERM_ACTIONS}}
No short-term actions required.
{{/unless}}

### Long-term (Low/Best Practices)

{{#each LONG_TERM_ACTIONS}}
1. :information_source: {{.}}
{{/each}}

{{#unless LONG_TERM_ACTIONS}}
No long-term recommendations.
{{/unless}}

---

## Compliance Status

| Standard | Status | Notes |
|----------|--------|-------|
| OWASP Top 10 | {{OWASP_STATUS}} | {{OWASP_NOTES}} |
| GDPR | {{GDPR_STATUS}} | {{GDPR_NOTES}} |
| PCI-DSS | {{PCI_STATUS}} | {{PCI_NOTES}} |
| SOC 2 | {{SOC2_STATUS}} | {{SOC2_NOTES}} |

---

## Scan Tools Used

| Tool | Version | Checks Performed |
|------|---------|------------------|
{{#each TOOLS_USED}}
| {{name}} | {{version}} | {{checks}} |
{{/each}}

---

## Commands

```bash
# Run security scan
{{SCAN_COMMAND}}

# Fix vulnerabilities
{{FIX_COMMAND}}

# Check dependencies
{{AUDIT_COMMAND}}
```

---

## Artifacts

| Artifact | Location |
|----------|----------|
| Full Scan Report | {{FULL_REPORT_PATH}} |
| Dependency Audit | {{AUDIT_PATH}} |
| SAST Results | {{SAST_PATH}} |

---

**Generated:** {{TIMESTAMP}}
**Tool:** {{TOOL_NAME}} v{{TOOL_VERSION}}
**Scan Duration:** {{SCAN_DURATION}}
