# Changelog

All notable changes to F5 Framework will be documented in this file.

## [Unreleased]

### Changed
- **cc-wf-studio removed** — F5 Workflow Studio đã tách thành project riêng và publish lên VS Code Marketplace (`fujigo.f5-wf-studio`). Không còn bundled trong F5 Framework CLI.
  - Install: `ext install fujigo.f5-wf-studio`
  - Source: Separate repository (cc-wf-studio-marketplace)

## [2.0.0] - 2026-02-03

### Major Release — Plugin Marketplace Architecture

- **BREAKING**: Restructured as Claude Code plugin marketplace format
- **NEW**: 2-plugin architecture (f5-core + f5-stacks)
- **REMOVED**: MCP source code moved to separate repositories
- **REMOVED**: Duplicate content (.f5/stacks, .f5/domains, skills/ root)
- **CHANGED**: Version aligned to 2.0.0 across all components
- **CHANGED**: CLI slimmed to thin wrapper (init, update, mcp health)

## [1.2.8] - 2025-12-31

### Highlights
- **Port Migration** - fujigo-redmine migrated from port 6000 to 6003 (WHATWG Fetch security)
- **Security Hardening** - Removed all hardcoded API keys from deployment files
- **Documentation Update** - Updated MCP documentation for v2.1.1

### Changed
- **fujigo-redmine Port**: 6000 → 6003
  - Reason: Port 6000 blocked by WHATWG Fetch spec (X11 security restriction)
  - Updated all configuration files and documentation

### Security
- Removed hardcoded API keys from deployment scripts
  - `mcp/DEPLOY_NOW.md` - Replaced with placeholders
  - `mcp/common/redeploy-portainer.md` - Replaced with placeholders
  - `mcp/deploy-shared-mcps.sh` - Replaced with placeholders
- Created `mcp/common/DEPLOY.md` - Secure deployment guide

### Documentation
- Updated `mcp/README.md` - Port 6003 in all references
- Updated `docs/MCP_ARCHITECTURE.md` - Port 6003 in diagrams
- Updated `docs/MCP_QUICK_REFERENCE.md` - Port 6003 in tables
- Created `docs/MCP-TEAM-GUIDE.md` - Quick-start team guide (English)
- Updated `cc-wf-studio/README.md` - Added MCP Server Integration section

### Fixed
- CC-WF-Studio v3.10.0 MCP server listing timeout issue
  - Changed from CLI-based (`claude mcp list`) to config-based listing
  - Reads `.mcp.json` directly for instant server list

---

## [1.2.7] - 2025-12-27

### Highlights
- **30% Command Reduction** - Consolidated 69 commands down to 48 active commands
- **F5Error Hierarchy** - Structured error handling with codes F5-001 to F5-999
- **G2.5 Verification Gate** - New quality checkpoint between G2 and G3
- **TokenOptimizer** - Context compression utility (30-50% reduction)
- **MCP Authentication** - Token-based auth for Fujigo servers
- **Security Fix** - Migrated from xlsx to exceljs (CVE-2024-22363, CVE-2024-22362)

### Added
- **F5Error Hierarchy** - Structured error codes for better debugging
  - Validation errors: F5-100 to F5-199
  - Gate errors: F5-200 to F5-299
  - MCP errors: F5-300 to F5-399
  - File errors: F5-400 to F5-499
  - Network errors: F5-500 to F5-599

- **G2.5 Verification Gate** - Enhanced quality checkpoint
  - Asset verification (images, fonts, icons)
  - Integration check (API contracts, database schema)
  - Visual QA (responsive, cross-browser)

- **TokenOptimizer Utility** - Context compression for large projects
  - 5 compression modes: none, light, moderate, aggressive, ultra
  - Preserves code blocks and tables
  - 30-50% token reduction while maintaining quality
  - Usage: `import { compress } from './core/token-optimizer.js'`

- **MCP Authentication** - Security enhancement for Fujigo servers
  - Token-based authentication (`MCP_AUTH_TOKEN` env variable)
  - CORS configuration (`CORS_ALLOWED_ORIGINS` env variable)
  - Secure server-to-server communication

- **Skills Reorganization**
  - Split `security` → `security` (core) + `security-auth` + `security-infra`
  - Split `testing` → `testing` (core) + `testing-advanced`
  - Merged duplicate NestJS skills → single `nestjs` skill
  - Reduced skill token usage by ~40%

- **CI/CD Workflows**
  - `build-verify.yml` - Build and type checking
  - `release.yml` - Automated releases
  - `npm-publish.yml` - NPM publishing
  - `dependabot.yml` - Dependency updates

### Changed
- **Command Consolidation** (Phase 1-6):
  - Phase 1: Jira Consolidation (7→1) - `/f5-jira [subcommand]`
  - Phase 2: Import Consolidation (4→1) - `/f5-import [subcommand]`
  - Phase 3: Context Consolidation (3→1) - `/f5-ctx [subcommand]`
  - Phase 4: Collaboration Consolidation (5→1) - `/f5-team [subcommand]`
  - Phase 5: AI Consolidation (3→1) - `/f5-agent [subcommand]`
  - Phase 6: Other consolidations - mcp, status, learn, memory, implement, design

- **CLAUDE.md Split** - Reduced from 956 to 173 lines
  - Agent documentation → `.claude/docs/AGENTS.md`
  - Gates documentation → `.claude/docs/GATES.md`
  - Commands documentation → `.claude/docs/COMMANDS.md`
  - Workflows documentation → `.claude/docs/WORKFLOWS.md`
  - Skills documentation → `.claude/docs/SKILLS.md`

- **Collab MCP SDK** - Upgraded from ^0.5.0 to ^1.0.0

### Deprecated
24 commands deprecated with redirect stubs:
- `f5-checkpoint` → `f5-ctx checkpoint`
- `f5-codebase` → `f5-memory codebase`
- `f5-collab` → `f5-team session`
- `f5-collaborate` → `f5-team agents`
- `f5-context` → `f5-ctx`
- `f5-doctor` → `f5-status doctor`
- `f5-examples` → `f5-learn examples`
- `f5-fix` → `f5-implement fix`
- `f5-handoff` → `f5-team handoff`
- `f5-import-analyze` → `f5-import analyze`
- `f5-import-batch` → `f5-import batch`
- `f5-import-schema` → `f5-import schema`
- `f5-jira-attachments` → `f5-jira attachments`
- `f5-jira-convert` → `f5-jira convert`
- `f5-jira-issue` → `f5-jira issue`
- `f5-jira-setup` → `f5-jira setup`
- `f5-jira-status` → `f5-jira status`
- `f5-jira-sync` → `f5-jira sync`
- `f5-mcp-setup` → `f5-mcp setup`
- `f5-persona` → `f5-agent persona`
- `f5-selftest` → `f5-status selftest`
- `f5-session` → `f5-ctx`
- `f5-spec` → `f5-design spec`
- `f5-suggest` → `f5-agent suggest`

### Fixed
- **Security**: Migrated from xlsx to exceljs (CVE-2024-22363, CVE-2024-22362)
- **Build**: Pre-existing test type errors resolved
- **Skills**: Removed duplicate skill definitions

### Breaking Changes
- **Deprecated Commands** - Old command names show deprecation notice with migration path
- **CORS Configuration** - `CORS_ALLOWED_ORIGINS` environment variable now required for MCP servers
- **MCP Authentication** - `MCP_AUTH_TOKEN` required for Fujigo server connections

### Migration Guide
See [docs/MIGRATION-1.2.7.md](docs/MIGRATION-1.2.7.md) for detailed migration instructions.

---

## [1.2.1] - 2025-12-23

### Added
- **Fujigo MCP Servers** - Custom MCP servers with SSE transport
  - `fujigo-redmine` (port 6000) - Redmine project management integration
    - Tools: `redmine_get_projects`, `redmine_get_issues`, `redmine_create_issue`, `redmine_update_issue`
    - Docker image: `${DOCKER_REGISTRY}/fujigo/redmine-mcp:1.1.0`
  - `fujigo-docparse` (port 6001) - Document parsing with PaddleOCR
    - Tools: `docparse_excel`, `docparse_image`, `docparse_extract_images`, `docparse_health`
    - Japanese/English OCR support
    - Excel parsing with embedded image extraction
    - Docker image: `${DOCKER_REGISTRY}/fujigo/docparse-mcp:1.1.0`

- **F5 Update System** - Manifest-based version tracking and updates
  - `/f5-update` command for Claude Code
  - `f5-update` CLI script for terminal
  - `scripts/generate-manifest.js` - Manifest generator
  - `.f5/manifest.yaml` - Version tracking with component info

- **New Commands**
  - `/f5-update` - Update F5 Framework from source repository
  - `/f5-improve` - Automatic code improvement and optimization
  - `/f5-redmine` - Redmine integration commands (planned)
  - `/f5-docparse` - Document parsing commands (planned)

### Changed
- Total slash commands: 59 (was 50)
- Updated `.mcp.json` with Fujigo MCP servers
- Added manifest system for version tracking
- Updated documentation (README.md, CLAUDE.md)

### Technical
- MCP servers use HTTP/SSE transport for remote deployment
- Docker images pushed to private registry `${DOCKER_REGISTRY}`
- Portainer-compatible docker-compose configurations

---

## [1.2.2] - 2025-12-19

### Added
- **`f5 update` Command** - Comprehensive asset update system
  - Check for updates: `f5 update --check`
  - Preview changes: `f5 update --dry-run`
  - Update specific category: `f5 update --category commands`
  - Auto backup before update
  - Categories: Commands, Workflows, Skills, Stacks, Domains, Testing, Gates, Personas, Agents

### Changed
- Moved Update section after Installation in README for better visibility
- Removed NPM Global installation approach - now clone-only workflow
- Fixed broken documentation links

### Removed
- `docs/getting-started/quick-start-npm.md` - NPM approach removed
- `docs/guides/using-npm-package.md` - NPM approach removed

## [1.2.1] - 2025-12-18

### Added
- **6 New Stack Commands**
  - `/f5-backend` - Backend development (NestJS, FastAPI, Spring, Go, Django, Laravel, Rails, .NET, Rust)
  - `/f5-web` - Frontend development (Next.js, React, Nuxt, Vue, Angular)
  - `/f5-mobile` - Mobile development (Flutter, React Native, Android, iOS)
  - `/f5-db` - Database management (Prisma, TypeORM, SQLAlchemy, GORM, Eloquent, etc.)
  - `/f5-gateway` - API Gateway (Kong, NGINX, custom Go)
  - `/f5-infra` - Infrastructure (Docker, Kubernetes, Terraform)

- **Simplified `/f5-load` Configuration**
  - Only 2 interactive questions: Starting Point + Project Type
  - Stack auto-detection from source code (nest-cli.json, next.config.js, pubspec.yaml, go.mod, etc.)
  - Removed manual stack selection questions (Q1-Q6)

### Fixed
- **Command Naming Convention**: Changed all `/f5:` patterns to `/f5-` format
  - Fixed in: f5-workflow.md, f5-gate.md, f5-load.md
  - Ensures commands are properly recognized by Claude Code

- **Windows Compatibility**: Fixed `DOMMatrix is not defined` error on Windows
  - Issue: `pdf-parse` library loads `pdfjs-dist` which requires browser APIs
  - Solution: Converted to dynamic import (lazy loading) in `pdf-processor.ts`
  - CLI commands now work without PDF processing dependencies at startup

### Changed
- Total slash commands: 50 (was 44)
- `/f5-load` now auto-detects: backend, frontend, mobile, database, gateway, infrastructure

## [1.2.0] - 2025-12-03

### Added
- **Jira Integration** - Complete Excel-to-Jira sync workflow
  - `f5 jira setup` - Interactive setup wizard for Jira Cloud/Server
  - `f5 jira convert` - Convert Excel/CSV to Jira issues with auto column detection
  - `f5 jira sync` - Bidirectional sync with duplicate protection
  - `f5 jira push-attachments` - Smart image upload (skips existing)
  - `f5 jira status` - Show sync status and diagnostics
  - `f5 jira list/show/create/update/delete` - Issue management commands
  - `f5 jira attachments/upload/download` - Attachment management

- **Claude Code Slash Commands for Jira**
  - `/f5-jira` - Main sync workflow (convert → sync → push-attachments)
  - `/f5-jira-setup` - Configure Jira connection
  - `/f5-jira-issue` - Manage individual issues
  - `/f5-jira-attachments` - Manage attachments
  - `/f5-jira-status` - Check status and diagnose issues

- **Excel/CSV Features**
  - Auto-detect columns (Japanese, Vietnamese, English headers)
  - Extract embedded images from Excel detail sheets
  - Support for multi-sheet workbooks (問題管理表 format)
  - Date validation with year range check (1900-2100)

### Fixed
- Invalid date parsing from Excel (e.g., year ~45000 from formula errors)
- Duplicate issue creation on first sync
- Attachment duplicate uploads (now skips existing files)

### Changed
- Sync engine now tracks `newlyCreatedRemoteIds` to prevent duplicates
- `push-attachments` checks existing attachments before upload
- Improved error messages for Jira field validation errors

## [1.1.0] - 2025-11-26

### Added
- 12 Business Domains: fintech, e-commerce, healthcare, education, entertainment, logistics, insurance, hr-management, saas-platform, manufacturing, real-estate, travel-hospitality
- Fintech Domain Knowledge:
  - Core Entities: account, customer, transaction (Vietnamese docs)
  - Stock-Trading Sub-domain complete:
    - 4 Entities: order (200+ lines), position, portfolio, quote
    - 3 Business Rules: order-validation, trading-hours, risk-limits
    - 4 Workflows: order-lifecycle, portfolio-rebalancing, margin-trading, corporate-action
    - 28+ Use Cases: trading, account, market-data
- E-Commerce Domain Knowledge:
  - B2C Retail Sub-domain complete:
    - 12 Entities: product, category, customer, order, cart, payment, inventory, coupon
    - 70+ Business Rules: pricing, inventory, order, cart, discount, payment, shipping, returns, customer, loyalty
    - 2 Workflows: order-lifecycle, checkout-flow
    - 25+ Use Cases: account management, shopping, wishlist, reviews, tracking, returns
- Tech Stack Agents & Templates:
  - NestJS Backend: service-generator, api-designer, module templates
  - Go Backend: service-generator, api-designer, clean architecture templates
  - React Frontend: component-designer, hook-generator, component/hook templates
- Gateway Modules: nginx, kong with configurations
- Infrastructure Modules: kubernetes with workload types, networking, storage
- CLI Package published to npm
- 20 Specialized Agents (base, workflow, domain, sub-agents)
- Quality Gates System (D1-D4, G2-G4)

### Changed
- Renamed from EPS Framework to F5 Framework
- Unified version numbering to semantic versioning (v1.x.x)
- Documentation language: Vietnamese with English technical terms

### Technical
- TypeScript 5.x with ESM modules
- Commander.js CLI
- pnpm workspace structure

## [1.0.9] - 2025-11-25
- Agent loading fixes
- CLI improvements

## [1.0.0] - 2025-11-24
- Initial npm release
