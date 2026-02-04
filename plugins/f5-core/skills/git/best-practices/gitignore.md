---
name: gitignore
description: Configuring files to exclude from version control
category: git/best-practices
applies_to: [all]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Gitignore

## Overview

The `.gitignore` file tells Git which files and directories to ignore. Properly
configured gitignore prevents committing generated files, secrets, and
platform-specific files that shouldn't be in version control.

## Gitignore Basics

### How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                  Gitignore Processing                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Git checks .gitignore when:                                    │
│  • Running git status                                           │
│  • Running git add                                              │
│  • Showing untracked files                                      │
│                                                                  │
│  Important:                                                     │
│  • .gitignore only affects UNTRACKED files                      │
│  • Already tracked files are NOT affected                       │
│  • To ignore a tracked file, you must untrack it first          │
│                                                                  │
│  Gitignore Locations (in priority order):                       │
│  1. .gitignore in same directory                                │
│  2. .gitignore in parent directories                            │
│  3. .git/info/exclude (local, not shared)                       │
│  4. ~/.config/git/ignore (global)                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Pattern Syntax

```bash
# Comment - lines starting with # are ignored
# This is a comment

# Blank lines are ignored for readability

# Simple file name - matches in any directory
debug.log

# Directory - trailing slash means directory only
node_modules/
dist/
build/

# Wildcard - * matches anything except /
*.log          # All .log files
*.tmp          # All .tmp files

# Double asterisk - ** matches directories
**/logs        # logs directory anywhere
**/logs/*.log  # .log files in any logs directory
logs/**        # Everything inside logs/

# Question mark - ? matches single character
file?.txt      # file1.txt, fileA.txt, etc.

# Character class - [abc] matches a, b, or c
file[0-9].txt  # file0.txt through file9.txt
file[abc].txt  # filea.txt, fileb.txt, filec.txt

# Negation - ! un-ignores a previously ignored pattern
*.log
!important.log # Don't ignore this one

# Escape special characters
\#filename     # File starting with #
\!filename     # File starting with !

# Leading slash - matches from repo root only
/config.local  # Only in root, not subfolders
```

## Common Patterns

### Node.js / JavaScript

```gitignore
# Dependencies
node_modules/
bower_components/

# Build output
dist/
build/
out/

# Logs
logs/
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Runtime data
pids/
*.pid
*.seed
*.pid.lock

# Coverage
coverage/
.nyc_output/

# TypeScript
*.tsbuildinfo

# Cache
.npm/
.eslintcache
.cache/

# Environment
.env
.env.local
.env.*.local

# IDE
.idea/
.vscode/
*.swp
*.swo
```

### Python

```gitignore
# Byte-compiled
__pycache__/
*.py[cod]
*$py.class

# Virtual environments
venv/
env/
.venv/
ENV/

# Distribution
dist/
build/
eggs/
*.egg-info/
*.egg

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage
htmlcov/
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
.pytest_cache/

# Jupyter Notebook
.ipynb_checkpoints/

# Environment
.env
.venv
*.env

# IDE
.idea/
.vscode/
*.swp
```

### Java / Kotlin

```gitignore
# Compiled class files
*.class

# Log files
*.log

# Package files
*.jar
*.war
*.nar
*.ear
*.zip
*.tar.gz
*.rar

# Build directories
target/
build/
out/

# IDE
.idea/
*.iml
.project
.classpath
.settings/

# Gradle
.gradle/
gradle-app.setting
!gradle-wrapper.jar

# Maven
pom.xml.tag
pom.xml.releaseBackup
pom.xml.versionsBackup
pom.xml.next
release.properties
```

### Go

```gitignore
# Binaries
*.exe
*.exe~
*.dll
*.so
*.dylib

# Test binary
*.test

# Output of go coverage
*.out

# Dependency directories
vendor/

# Build directory
bin/

# IDE
.idea/
.vscode/
```

### macOS

```gitignore
# General
.DS_Store
.AppleDouble
.LSOverride

# Icon must end with two \r
Icon

# Thumbnails
._*

# Files on external disk
.Spotlight-V100
.Trashes

# Directories
.fseventsd
.TemporaryItems
```

### Windows

```gitignore
# Windows thumbnail cache
Thumbs.db
ehthumbs.db

# Folder config
Desktop.ini

# Recycle Bin
$RECYCLE.BIN/

# Shortcuts
*.lnk
```

### IDE / Editors

```gitignore
# Visual Studio Code
.vscode/*
!.vscode/settings.json
!.vscode/tasks.json
!.vscode/launch.json
!.vscode/extensions.json

# JetBrains IDEs
.idea/
*.iml
*.iws
*.ipr
out/

# Vim
*.swp
*.swo
*~
.netrwhist

# Emacs
*~
\#*\#
/.emacs.desktop
/.emacs.desktop.lock
auto-save-list/
```

## Global Gitignore

### Setup Global Gitignore

```bash
# Create global gitignore file
touch ~/.gitignore_global

# Configure git to use it
git config --global core.excludesfile ~/.gitignore_global

# Add common patterns
cat >> ~/.gitignore_global << 'EOF'
# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Editor files
*.swp
*.swo
*~
.idea/
.vscode/
*.sublime-*

# Compiled
*.com
*.class
*.dll
*.exe
*.o
*.so
EOF
```

### What Goes Global vs Local

```
┌─────────────────────────────────────────────────────────────────┐
│            Global vs Local Gitignore                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Global (~/.gitignore_global):                                  │
│  • OS-specific files (.DS_Store, Thumbs.db)                     │
│  • Editor/IDE config (.idea/, .vscode/)                         │
│  • Personal tools output                                        │
│                                                                  │
│  Local (.gitignore):                                            │
│  • Project dependencies (node_modules/, vendor/)                │
│  • Build output (dist/, build/, target/)                        │
│  • Project-specific secrets (.env.local)                        │
│  • Generated files (*.generated.ts)                             │
│  • Test artifacts (coverage/, .pytest_cache/)                   │
│                                                                  │
│  Reason:                                                        │
│  • Global = your personal setup                                 │
│  • Local = shared with team via repository                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Advanced Patterns

### Negation Patterns

```gitignore
# Ignore all .txt files
*.txt

# But not this one
!important.txt

# Ignore directory
logs/

# But keep its .gitkeep
!logs/.gitkeep

# Complex example: ignore all except specific files
*
!.gitignore
!src/
!src/**
!package.json
```

### Directory vs File

```gitignore
# This ignores DIRECTORY named foo
foo/

# This ignores FILE named foo (in any directory)
foo

# This ignores FILE named foo only in root
/foo

# This ignores both file and directory
foo
foo/
```

### Nested Gitignore

```bash
# Project structure
project/
├── .gitignore         # Root patterns
├── src/
│   └── .gitignore     # Source-specific patterns
├── tests/
│   └── .gitignore     # Test-specific patterns
└── docs/
    └── .gitignore     # Docs-specific patterns

# Each .gitignore only affects its directory and subdirectories
```

## Managing Ignored Files

### Ignoring Already Tracked Files

```bash
# File is already tracked but you want to ignore it
# Step 1: Add to .gitignore
echo "config.local.json" >> .gitignore

# Step 2: Remove from git (but keep locally)
git rm --cached config.local.json

# Step 3: Commit
git commit -m "Stop tracking config.local.json"

# For directories
git rm -r --cached node_modules/
```

### Ignoring Changes to Tracked Files

```bash
# Temporarily ignore changes (useful for local config)
git update-index --assume-unchanged config.json

# Start tracking changes again
git update-index --no-assume-unchanged config.json

# List files with assume-unchanged
git ls-files -v | grep '^h'

# Alternative: skip-worktree (survives checkout)
git update-index --skip-worktree config.json
git update-index --no-skip-worktree config.json
```

### Force Add Ignored File

```bash
# Sometimes you need to add an ignored file
git add -f build/important-file.js

# Or add with explicit path
git add build/important-file.js --force
```

## Checking Gitignore

### Debug Gitignore Rules

```bash
# Check why a file is ignored
git check-ignore -v filename

# Example output
# .gitignore:3:*.log    debug.log

# Check multiple files
git check-ignore -v file1 file2 file3

# List all ignored files
git status --ignored

# List ignored files in short format
git status --ignored -s
```

### Test Patterns

```bash
# Test pattern without adding to .gitignore
git check-ignore "*.log"

# Check if file would be ignored
git check-ignore path/to/file.log

# Verbose output shows which rule matches
git check-ignore -v path/to/file.log
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│                Gitignore Best Practices                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Structure:                                                     │
│  • Group related patterns with comments                         │
│  • Order: dependencies → build → env → IDE → OS                 │
│  • Use consistent formatting                                    │
│                                                                  │
│  Content:                                                       │
│  • Always ignore dependencies (node_modules/, vendor/)          │
│  • Always ignore build output (dist/, build/)                   │
│  • Always ignore secrets (.env, *.key, credentials.*)           │
│  • Never ignore package.json, go.mod, requirements.txt          │
│                                                                  │
│  Maintenance:                                                   │
│  • Review .gitignore when adding new tools                      │
│  • Use gitignore.io for project-specific templates              │
│  • Keep patterns minimal and specific                           │
│                                                                  │
│  Team:                                                          │
│  • Commit .gitignore to repository                              │
│  • Document unusual patterns                                    │
│  • Keep OS/IDE patterns in global gitignore                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Templates and Tools

### Generate Gitignore

```bash
# Using gitignore.io
curl -sL https://www.toptal.com/developers/gitignore/api/node,react,visualstudiocode

# Using git-ignore-generator (npm)
npx gitignore node react

# Using gig (npm)
npx gig node react
```

### Useful Resources

```bash
# GitHub gitignore templates
# https://github.com/github/gitignore

# gitignore.io website
# https://www.toptal.com/developers/gitignore

# Preview what would be ignored
git status --ignored --short
```

## Useful Commands Reference

```bash
# Check why file is ignored
git check-ignore -v <file>

# List all ignored files
git status --ignored

# Remove file from index but keep locally
git rm --cached <file>

# Force add ignored file
git add -f <file>

# Assume unchanged
git update-index --assume-unchanged <file>
git update-index --no-assume-unchanged <file>

# Skip worktree
git update-index --skip-worktree <file>
git update-index --no-skip-worktree <file>

# List files with special flags
git ls-files -v | grep '^h'   # assume-unchanged
git ls-files -v | grep '^S'   # skip-worktree
```
