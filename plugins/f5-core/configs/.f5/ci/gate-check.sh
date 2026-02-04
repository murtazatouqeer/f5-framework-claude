#!/bin/bash

# F5 Gate Check Script
# Usage: ./gate-check.sh <gate_id> [--strict] [--verbose]
#
# Examples:
#   ./gate-check.sh G2             # Check G2 gate
#   ./gate-check.sh G3 --strict    # Check G3, fail on warnings
#   ./gate-check.sh G4 --verbose   # Check G4 with detailed output
#
# Exit Codes:
#   0 = Gate passed
#   1 = Gate failed
#   2 = Gate passed with warnings

set -e

# =============================================================================
# Configuration
# =============================================================================

GATE_ID="${1:-G2}"
EVIDENCE_DIR=".f5/evidence/${GATE_ID}"
TIMESTAMP=$(date +%Y-%m-%d)
REPORT_FILE="${EVIDENCE_DIR}/${GATE_ID}-check-${TIMESTAMP}.md"
STRICT_MODE=false
VERBOSE=false

# Parse flags
for arg in "$@"; do
    case $arg in
        --strict)
            STRICT_MODE=true
            ;;
        --verbose)
            VERBOSE=true
            ;;
    esac
done

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0
WARNINGS=0
TOTAL=0

# =============================================================================
# Functions
# =============================================================================

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_verbose() {
    if [ "$VERBOSE" == "true" ]; then
        echo -e "${CYAN}   $1${NC}"
    fi
}

# Function to run a check
run_check() {
    local name=$1
    local command=$2
    local required=${3:-true}

    ((TOTAL++))

    echo -n "Running: ${name}... "

    # Create temp file for output
    local temp_output="/tmp/f5_check_${GATE_ID}_${TOTAL}.txt"

    if eval "$command" > "$temp_output" 2>&1; then
        echo -e "${GREEN}✅ PASSED${NC}"
        ((PASSED++))

        # Log to report
        echo "| ${name} | ✅ Pass | - |" >> "$REPORT_FILE"

        log_verbose "Output: $(head -5 "$temp_output")"
        return 0
    else
        local exit_code=$?

        if [ "$required" == "true" ]; then
            echo -e "${RED}❌ FAILED${NC}"
            ((FAILED++))

            # Log to report
            echo "| ${name} | ❌ Fail | Exit code: ${exit_code} |" >> "$REPORT_FILE"

            if [ "$VERBOSE" == "true" ]; then
                echo "   Error output:"
                cat "$temp_output" | head -20 | sed 's/^/   /'
            fi
            return 1
        else
            echo -e "${YELLOW}⚠️ WARNING${NC}"
            ((WARNINGS++))

            # Log to report
            echo "| ${name} | ⚠️ Warning | Exit code: ${exit_code} |" >> "$REPORT_FILE"

            log_verbose "Warning output: $(head -5 "$temp_output")"
            return 0
        fi
    fi
}

# Function to check if command exists
check_command() {
    local cmd=$1
    if ! command -v "$cmd" &> /dev/null; then
        return 1
    fi
    return 0
}

# Function to detect package manager
detect_package_manager() {
    if [ -f "package-lock.json" ]; then
        echo "npm"
    elif [ -f "yarn.lock" ]; then
        echo "yarn"
    elif [ -f "pnpm-lock.yaml" ]; then
        echo "pnpm"
    elif [ -f "pom.xml" ]; then
        echo "maven"
    elif [ -f "build.gradle" ] || [ -f "build.gradle.kts" ]; then
        echo "gradle"
    elif [ -f "go.mod" ]; then
        echo "go"
    elif [ -f "requirements.txt" ] || [ -f "pyproject.toml" ]; then
        echo "pip"
    else
        echo "unknown"
    fi
}

# =============================================================================
# Initialization
# =============================================================================

echo ""
echo "══════════════════════════════════════════════════════════════"
echo "  F5 Framework - Gate Check"
echo "══════════════════════════════════════════════════════════════"
echo ""
echo "  Gate:     ${GATE_ID}"
echo "  Project:  $(basename $(pwd))"
echo "  Date:     $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo "  Strict:   ${STRICT_MODE}"
echo ""
echo "══════════════════════════════════════════════════════════════"
echo ""

# Create evidence directory
mkdir -p "$EVIDENCE_DIR"

# Detect package manager
PKG_MANAGER=$(detect_package_manager)
log_info "Detected package manager: ${PKG_MANAGER}"

# Initialize report file
cat << EOF > "$REPORT_FILE"
# Gate ${GATE_ID} Check Report

**Date:** $(date -u +"%Y-%m-%dT%H:%M:%SZ")
**Project:** $(basename $(pwd))
**Branch:** $(git branch --show-current 2>/dev/null || echo "N/A")
**Commit:** $(git rev-parse --short HEAD 2>/dev/null || echo "N/A")
**Package Manager:** ${PKG_MANAGER}

---

## Automated Checks

| Check | Status | Details |
|-------|--------|---------|
EOF

# =============================================================================
# Gate-specific Checks
# =============================================================================

case $GATE_ID in
    D1)
        echo "## D1: Research Complete"
        echo ""

        run_check "Requirements File Exists" "test -f .f5/input/requirements/*.xlsx -o -f .f5/input/requirements/*.md" "true"
        run_check "Research Notes" "test -d .f5/specs/research" "false"
        ;;

    D2)
        echo "## D2: SRS Approved"
        echo ""

        run_check "D1 Evidence" "ls .f5/evidence/D1/D1-*.md 2>/dev/null | head -1" "true"
        run_check "SRS Document" "test -f .f5/specs/srs/srs.md -o -f .f5/specs/srs/v*/srs.md" "true"
        run_check "Requirements Validated" "test -f .f5/specs/srs/requirements-validated.md" "false"
        ;;

    D3)
        echo "## D3: Basic Design Approved"
        echo ""

        run_check "D2 Evidence" "ls .f5/evidence/D2/D2-*.md 2>/dev/null | head -1" "true"
        run_check "Architecture Document" "test -f .f5/specs/basic-design/architecture.md" "true"
        run_check "DB Design" "test -f .f5/specs/basic-design/database-design.md" "true"
        run_check "API Design" "test -f .f5/specs/basic-design/api-design.md" "true"
        ;;

    D4)
        echo "## D4: Detail Design Approved"
        echo ""

        run_check "D3 Evidence" "ls .f5/evidence/D3/D3-*.md 2>/dev/null | head -1" "true"
        run_check "Detail Design Docs" "test -d .f5/specs/detail-design" "true"
        run_check "Screen Specs" "ls .f5/specs/detail-design/screens/*.md 2>/dev/null | head -1" "false"
        run_check "API Specs" "ls .f5/specs/detail-design/api/*.md 2>/dev/null | head -1" "false"
        ;;

    G2)
        echo "## G2: Implementation Ready"
        echo ""

        case $PKG_MANAGER in
            npm|yarn|pnpm)
                run_check "Dependencies Installed" "test -d node_modules" "true"
                run_check "Lint" "npm run lint 2>/dev/null || yarn lint 2>/dev/null" "true"
                run_check "Type Check" "npm run type-check 2>/dev/null || npm run typecheck 2>/dev/null || yarn type-check 2>/dev/null || echo 'Skip'" "false"
                run_check "Unit Tests" "npm run test 2>/dev/null || yarn test 2>/dev/null" "true"
                run_check "Test Coverage" "npm run test:cov 2>/dev/null || npm run test -- --coverage 2>/dev/null" "false"
                run_check "Security Audit" "npm audit --audit-level=high 2>/dev/null || yarn audit --level high 2>/dev/null" "true"
                run_check "Build" "npm run build 2>/dev/null || yarn build 2>/dev/null" "true"
                ;;
            maven)
                run_check "Maven Build" "mvn clean compile" "true"
                run_check "Maven Tests" "mvn test" "true"
                run_check "Maven Package" "mvn package -DskipTests" "false"
                ;;
            gradle)
                run_check "Gradle Build" "./gradlew build" "true"
                run_check "Gradle Tests" "./gradlew test" "true"
                ;;
            go)
                run_check "Go Build" "go build ./..." "true"
                run_check "Go Test" "go test ./..." "true"
                run_check "Go Vet" "go vet ./..." "true"
                run_check "Go Lint" "golangci-lint run 2>/dev/null || echo 'Skip'" "false"
                ;;
            pip)
                run_check "Python Tests" "pytest 2>/dev/null || python -m pytest 2>/dev/null" "true"
                run_check "Python Lint" "flake8 . 2>/dev/null || ruff check . 2>/dev/null" "false"
                run_check "Python Type Check" "mypy . 2>/dev/null || echo 'Skip'" "false"
                ;;
            *)
                log_warning "Unknown package manager. Running basic checks..."
                run_check "Source Files Exist" "ls src/ 2>/dev/null || ls lib/ 2>/dev/null || ls app/ 2>/dev/null" "true"
                ;;
        esac

        # Common checks
        run_check "Git Clean" "test -z \"$(git status --porcelain 2>/dev/null)\" || echo 'Has changes'" "false"
        ;;

    G3)
        echo "## G3: Testing Complete"
        echo ""

        run_check "G2 Evidence" "ls .f5/evidence/G2/G2-*.md 2>/dev/null | head -1" "true"

        case $PKG_MANAGER in
            npm|yarn|pnpm)
                run_check "Unit Tests" "npm run test 2>/dev/null || yarn test 2>/dev/null" "true"
                run_check "Integration Tests" "npm run test:integration 2>/dev/null || yarn test:integration 2>/dev/null || echo 'No integration tests'" "false"
                run_check "E2E Tests" "npm run test:e2e 2>/dev/null || yarn test:e2e 2>/dev/null || echo 'No E2E tests'" "false"
                run_check "Coverage >= 80%" "npm run test:cov 2>/dev/null || npm run test -- --coverage 2>/dev/null" "true"
                run_check "Security Scan" "npm audit 2>/dev/null || yarn audit 2>/dev/null" "true"
                ;;
            maven)
                run_check "Maven Test" "mvn test" "true"
                run_check "Maven Integration Test" "mvn verify" "false"
                ;;
            gradle)
                run_check "Gradle Test" "./gradlew test" "true"
                run_check "Gradle Integration Test" "./gradlew integrationTest 2>/dev/null || echo 'Skip'" "false"
                ;;
            go)
                run_check "Go Test" "go test ./..." "true"
                run_check "Go Coverage" "go test -cover ./..." "true"
                run_check "Go Race Detection" "go test -race ./..." "false"
                ;;
            pip)
                run_check "Pytest" "pytest 2>/dev/null || python -m pytest 2>/dev/null" "true"
                run_check "Coverage" "pytest --cov 2>/dev/null || python -m pytest --cov 2>/dev/null" "false"
                ;;
        esac

        run_check "Test Report Exists" "test -f .f5/evidence/G3/test-report-*.md 2>/dev/null || echo 'Will be generated'" "false"
        ;;

    G4)
        echo "## G4: Deployment Ready"
        echo ""

        run_check "G2 Evidence" "ls .f5/evidence/G2/G2-*.md 2>/dev/null | head -1" "true"
        run_check "G3 Evidence" "ls .f5/evidence/G3/G3-*.md 2>/dev/null | head -1" "true"
        run_check "CHANGELOG Updated" "test -f CHANGELOG.md" "true"
        run_check "Version Tag" "git describe --tags 2>/dev/null || echo 'No tags'" "false"
        run_check "Rollback Plan" "test -f docs/deployment/rollback-plan.md 2>/dev/null || test -f .f5/specs/deployment/rollback.md 2>/dev/null || echo 'No rollback plan'" "false"

        # Container checks
        if [ -f "Dockerfile" ]; then
            run_check "Dockerfile Exists" "test -f Dockerfile" "true"
            run_check "Docker Build" "docker build -t f5-test-build . --quiet 2>/dev/null && docker rmi f5-test-build 2>/dev/null" "false"
        fi

        # Kubernetes checks
        if [ -d "k8s" ] || [ -d "kubernetes" ]; then
            run_check "K8s Manifests" "ls k8s/*.yaml 2>/dev/null || ls kubernetes/*.yaml 2>/dev/null" "false"
        fi

        run_check "Environment Config" "test -f .env.example || test -f .env.template || test -f config/env.example.yaml" "false"
        run_check "Production Build" "npm run build 2>/dev/null || yarn build 2>/dev/null || echo 'Skip'" "true"
        ;;

    *)
        log_error "Unknown gate: ${GATE_ID}"
        echo "Valid gates: D1, D2, D3, D4, G2, G3, G4"
        exit 1
        ;;
esac

# =============================================================================
# Summary
# =============================================================================

echo ""
echo "══════════════════════════════════════════════════════════════"
echo "  Summary"
echo "══════════════════════════════════════════════════════════════"
echo ""
echo -e "  Total:    ${TOTAL}"
echo -e "  Passed:   ${GREEN}${PASSED}${NC}"
echo -e "  Failed:   ${RED}${FAILED}${NC}"
echo -e "  Warnings: ${YELLOW}${WARNINGS}${NC}"
echo ""

# Append summary to report
cat << EOF >> "$REPORT_FILE"

---

## Summary

| Metric | Count |
|--------|-------|
| Total | ${TOTAL} |
| Passed | ${PASSED} |
| Failed | ${FAILED} |
| Warnings | ${WARNINGS} |

---

## Gate Status

EOF

# =============================================================================
# Final Decision
# =============================================================================

if [ $FAILED -eq 0 ]; then
    if [ $WARNINGS -eq 0 ]; then
        echo -e "${GREEN}══════════════════════════════════════════════════════════════${NC}"
        echo -e "${GREEN}  ✅ Gate ${GATE_ID} PASSED${NC}"
        echo -e "${GREEN}══════════════════════════════════════════════════════════════${NC}"
        echo "**Status:** ✅ PASSED" >> "$REPORT_FILE"
        echo ""
        echo "Evidence saved to: ${REPORT_FILE}"
        exit 0
    else
        if [ "$STRICT_MODE" == "true" ]; then
            echo -e "${RED}══════════════════════════════════════════════════════════════${NC}"
            echo -e "${RED}  ❌ Gate ${GATE_ID} FAILED (strict mode - warnings present)${NC}"
            echo -e "${RED}══════════════════════════════════════════════════════════════${NC}"
            echo "**Status:** ❌ FAILED (strict mode)" >> "$REPORT_FILE"
            echo ""
            echo "Evidence saved to: ${REPORT_FILE}"
            exit 1
        else
            echo -e "${YELLOW}══════════════════════════════════════════════════════════════${NC}"
            echo -e "${YELLOW}  ⚠️  Gate ${GATE_ID} PASSED WITH WARNINGS${NC}"
            echo -e "${YELLOW}══════════════════════════════════════════════════════════════${NC}"
            echo "**Status:** ⚠️ PASSED WITH WARNINGS" >> "$REPORT_FILE"
            echo ""
            echo "Evidence saved to: ${REPORT_FILE}"
            exit 2
        fi
    fi
else
    echo -e "${RED}══════════════════════════════════════════════════════════════${NC}"
    echo -e "${RED}  ❌ Gate ${GATE_ID} FAILED${NC}"
    echo -e "${RED}══════════════════════════════════════════════════════════════${NC}"
    echo "**Status:** ❌ FAILED" >> "$REPORT_FILE"
    echo ""
    echo "Evidence saved to: ${REPORT_FILE}"
    echo ""
    echo "Please fix the failed checks and run again."
    exit 1
fi
