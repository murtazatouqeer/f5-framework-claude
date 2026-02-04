# f5 init - Project Initialization

## Overview

The `f5 init` command initializes F5 Framework in your project. It has two modes:

1. **Existing Project** - Add F5 config to current directory (simplified)
2. **New Project** - Create new folder with full structure (wizard)

## Quick Start

```bash
# Existing project
cd my-project
f5 init

# New project
f5 init my-new-project
```

## Existing Project Mode

When you run `f5 init` or `f5 init .` in a directory that contains project files, F5 will:

1. **Auto-detect** the project type
2. **Ask only 2 questions** (domain and scale)
3. **Create minimal config** files
4. **Detect your tech stack** automatically

### Detection

F5 looks for these indicators:
- `package.json` (Node.js)
- `go.mod` (Go)
- `pom.xml`, `build.gradle` (Java)
- `requirements.txt` (Python)
- `Cargo.toml` (Rust)
- `.git`, `src/`, `lib/`, `app/`

### Stack Detection

From `package.json` dependencies:
- **Backend**: NestJS, Express, Fastify, Koa
- **Frontend**: Next.js, React, Vue, Angular
- **Database**: PostgreSQL (pg, prisma), MongoDB (mongoose), MySQL

From project files:
- **Go**: go.mod
- **Python**: FastAPI, Django, Flask (from requirements.txt)
- **Java/Kotlin**: Spring (pom.xml, build.gradle)
- **Rust**: Cargo.toml

### Example Output

```
🚀 F5 Framework v1.2.0

📂 Detected existing project

📋 Quick Setup

? Project domain: SaaS Platform
? Project scale: Growth (10K-100K users)

📦 Creating F5 configuration...

  ✓ Created .f5/config.json
  ✓ Created CLAUDE.md
  ✓ Updated .gitignore

✅ F5 initialized for "my-project"!

🔍 Detected Stack:
   Backend:  nestjs
   Frontend: react
   Database: postgresql

📋 What you can do now:

  claude                        # Start Claude Code
  /f5-research "feature"        # Research a feature
  /f5-design --srs              # Create SRS document
  f5 jira setup                 # Setup Jira integration
  f5 status                     # Check project status
```

### Files Created

```
my-project/
├── .f5/
│   ├── config.json          # F5 configuration
│   ├── input/               # For Excel/CSV files
│   ├── issues/              # Converted issues
│   └── sync/                # Sync state
├── CLAUDE.md                # AI context file
└── .gitignore               # Updated with F5 entries
```

## New Project Mode

When you run `f5 init my-project`, F5 will:

1. Create a new folder `my-project`
2. Run the **full wizard** (12+ questions)
3. Generate project structure based on architecture
4. Create all config files

### Wizard Questions

1. Project name
2. Architecture (monolith, modular-monolith, microservices, serverless)
3. Scale (starter, growth, enterprise)
4. Backend stack (NestJS, Go, Spring, etc.)
5. Frontend stack (React, Next.js, Vue, etc.)
6. Mobile stack (Flutter, React Native, etc.)
7. Database (PostgreSQL, MongoDB, MySQL)
8. Cache (Redis)
9. Message queue (RabbitMQ, Kafka)
10. Business domain
11. Sub-domain
12. Variant

### Generated Structure

**Monolith:**
```
my-project/
├── src/
│   ├── modules/
│   ├── common/
│   └── config/
├── tests/
├── docs/
├── .f5/config.json
├── CLAUDE.md
├── docker-compose.yml
├── .gitignore
└── README.md
```

**Microservices:**
```
my-project/
├── services/
├── shared/
├── infrastructure/
├── gateway/
├── docs/
├── .f5/config.json
├── CLAUDE.md
├── docker-compose.yml
├── .gitignore
└── README.md
```

## Options

| Option | Description |
|--------|-------------|
| `--here` | Force init in current directory |
| `-a, --architecture <type>` | Set architecture pattern |
| `-s, --scale <level>` | Set scale template |
| `-d, --domain <name>` | Set business domain |
| `--subdomain <name>` | Set sub-domain |
| `--variant <name>` | Set variant |
| `-i, --interactive` | Force interactive mode |
| `--no-git` | Skip git initialization |

## Examples

```bash
# Existing project - simplified
cd my-existing-app
f5 init

# New project - full wizard
f5 init my-new-app

# New project - non-interactive with options
f5 init my-fintech-app \
  --architecture microservices \
  --scale growth \
  --domain fintech \
  --subdomain stock-trading
```

## Configuration File

The generated `.f5/config.json`:

```json
{
  "version": "1.2.0",
  "name": "my-project",
  "architecture": "modular-monolith",
  "scale": "growth",
  "stack": {
    "backend": ["nestjs"],
    "frontend": "react",
    "database": ["postgresql"]
  },
  "domain": {
    "name": "saas-platform",
    "subDomain": "general",
    "variant": "standard"
  },
  "generatedAt": "2024-12-02T...",
  "isExistingProject": true
}
```

## CLAUDE.md

The generated CLAUDE.md provides context for AI assistants:

```markdown
# my-project

## F5 Framework v1.2.0

### Project Configuration

| Dimension | Value |
|-----------|-------|
| Architecture | modular-monolith |
| Scale | growth |
| Domain | saas-platform > general > standard |

### Tech Stack

- **Backend**: nestjs
- **Frontend**: react
- **Database**: postgresql

### Commands

| Command | Description |
|---------|-------------|
| `/f5-research` | Gather context and evidence |
| `/f5-design` | Create design documents |
| `/f5-implement` | Generate code |
```
