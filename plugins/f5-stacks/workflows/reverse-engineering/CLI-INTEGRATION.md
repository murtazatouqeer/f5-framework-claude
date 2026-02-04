# CLI Integration Proposal: `f5 docs` Commands

> **Purpose**: Add reverse engineering documentation commands to f5-cli
> **Status**: Proposal
> **Priority**: High

---

## Overview

This proposal adds a new command group `f5 docs` to handle reverse engineering documentation workflows.

```
f5 docs
├── init              # Initialize .f5/docs/ structure
├── analyze           # Run reverse engineering analysis
└── version           # Generate version changelog
```

---

## Command Specifications

### `f5 docs init`

**Purpose**: Initialize `.f5/docs/` directory structure in the current project.

**Usage**:
```bash
f5 docs init [options]

Options:
  --force         Overwrite existing structure
  --template      Template style (default: standard)
  --lang <code>   Output language (en, vn, ja)
```

**Implementation**:
```typescript
// packages/cli/src/commands/docs.ts

import { Command } from 'commander';
import * as fs from 'fs-extra';
import * as path from 'path';

interface DocsInitOptions {
  force?: boolean;
  template?: string;
  lang?: 'en' | 'vn' | 'ja';
}

export async function docsInit(options: DocsInitOptions) {
  const projectRoot = process.cwd();
  const docsPath = path.join(projectRoot, '.f5', 'docs');

  // Check if already exists
  if (fs.existsSync(docsPath) && !options.force) {
    console.log('⚠️  .f5/docs/ already exists. Use --force to overwrite.');
    return;
  }

  // Create directory structure
  const dirs = [
    'entities',
    'modules',
    'api',
    'screens',
    'versions'
  ];

  for (const dir of dirs) {
    await fs.ensureDir(path.join(docsPath, dir));
  }

  // Copy README template
  const templatePath = path.join(
    __dirname,
    '../../workflows/reverse-engineering/templates/docs-readme.md'
  );
  const readmePath = path.join(docsPath, 'README.md');

  let template = await fs.readFile(templatePath, 'utf-8');
  template = template.replace(/\{\{PROJECT_NAME\}\}/g, path.basename(projectRoot));
  template = template.replace(/\{\{DATE\}\}/g, new Date().toISOString().split('T')[0]);

  await fs.writeFile(readmePath, template);

  console.log('✅ Initialized .f5/docs/ structure');
  console.log('   Created directories: entities/, modules/, api/, screens/, versions/');
  console.log('   Created README.md from template');
}
```

**Output**:
```
✅ Initialized .f5/docs/ structure
   Created directories: entities/, modules/, api/, screens/, versions/
   Created README.md from template
```

---

### `f5 docs analyze`

**Purpose**: Run reverse engineering analysis using Claude Code prompts.

**Usage**:
```bash
f5 docs analyze [options]

Options:
  --module <name>     Analyze specific module only
  --entity <name>     Analyze specific entity only
  --framework <type>  Specify framework (laravel, nestjs, django, spring, go)
  --output <path>     Custom output path (default: .f5/docs/)
  --prompt <name>     Use specific prompt file
  --dry-run           Show what would be analyzed without executing
```

**Implementation**:
```typescript
// packages/cli/src/commands/docs.ts

interface DocsAnalyzeOptions {
  module?: string;
  entity?: string;
  framework?: 'laravel' | 'nestjs' | 'django' | 'spring' | 'go';
  output?: string;
  prompt?: string;
  dryRun?: boolean;
}

export async function docsAnalyze(options: DocsAnalyzeOptions) {
  const projectRoot = process.cwd();
  const outputPath = options.output || path.join(projectRoot, '.f5', 'docs');

  // Detect framework if not specified
  const framework = options.framework || await detectFramework(projectRoot);

  // Select appropriate prompt
  const promptFile = selectPrompt(framework, options);

  // Read prompt template
  const promptPath = path.join(
    __dirname,
    `../../workflows/reverse-engineering/prompts/${promptFile}`
  );
  let prompt = await fs.readFile(promptPath, 'utf-8');

  // Inject project details
  prompt = prompt.replace(/\[PROJECT_PATH\]/g, projectRoot);
  prompt = prompt.replace(/\[OUTPUT_PATH\]/g, outputPath);

  if (options.dryRun) {
    console.log('🔍 Dry run - would analyze:');
    console.log(`   Framework: ${framework}`);
    console.log(`   Prompt: ${promptFile}`);
    console.log(`   Output: ${outputPath}`);
    return;
  }

  // Copy prompt to clipboard or output for Claude Code
  console.log('📋 Analysis prompt generated');
  console.log('─'.repeat(60));
  console.log(prompt);
  console.log('─'.repeat(60));
  console.log('\n💡 Run this prompt in Claude Code to generate documentation');
}

async function detectFramework(projectRoot: string): Promise<string> {
  // Check for framework indicators
  if (await fs.pathExists(path.join(projectRoot, 'artisan'))) return 'laravel';
  if (await fs.pathExists(path.join(projectRoot, 'nest-cli.json'))) return 'nestjs';
  if (await fs.pathExists(path.join(projectRoot, 'manage.py'))) return 'django';
  if (await fs.pathExists(path.join(projectRoot, 'pom.xml'))) return 'spring';
  if (await fs.pathExists(path.join(projectRoot, 'go.mod'))) return 'go';
  return 'generic';
}

function selectPrompt(framework: string, options: DocsAnalyzeOptions): string {
  if (options.prompt) return options.prompt;
  if (options.entity) return 'extract-entities.md';
  if (framework === 'laravel') return 'analyze-laravel.md';
  return 'extract-entities.md';
}
```

**Output**:
```
📋 Analysis prompt generated
────────────────────────────────────────────────────────────
Analyze the codebase at /path/to/project to generate documentation...
────────────────────────────────────────────────────────────

💡 Run this prompt in Claude Code to generate documentation
```

---

### `f5 docs version <phase>`

**Purpose**: Generate version changelog documentation.

**Usage**:
```bash
f5 docs version <phase> [options]

Arguments:
  phase               Version/phase identifier (e.g., v2.0, phase-3)

Options:
  --from <version>    Compare from this version (git tag)
  --git-analysis      Include git diff analysis
  --output <path>     Custom output path
  --template <name>   Use custom template
```

**Implementation**:
```typescript
// packages/cli/src/commands/docs.ts

interface DocsVersionOptions {
  from?: string;
  gitAnalysis?: boolean;
  output?: string;
  template?: string;
}

export async function docsVersion(phase: string, options: DocsVersionOptions) {
  const projectRoot = process.cwd();
  const outputPath = options.output || path.join(projectRoot, '.f5', 'docs', 'versions');

  // Ensure output directory exists
  await fs.ensureDir(outputPath);

  // Load template
  const templatePath = path.join(
    __dirname,
    `../../workflows/reverse-engineering/templates/${options.template || 'version-template.md'}`
  );
  let template = await fs.readFile(templatePath, 'utf-8');

  // Collect git information if requested
  let gitInfo = '';
  if (options.gitAnalysis) {
    gitInfo = await collectGitInfo(projectRoot, phase, options.from);
  }

  // Generate version document
  template = template.replace(/\{\{VERSION\}\}/g, phase);
  template = template.replace(/\{\{DATE\}\}/g, new Date().toISOString().split('T')[0]);
  template = template.replace(/\{\{GIT_TAG\}\}/g, phase);
  template = template.replace(/\{\{PREV_TAG\}\}/g, options.from || 'N/A');

  // Write output
  const outputFile = path.join(outputPath, `${phase}.md`);
  await fs.writeFile(outputFile, template);

  console.log(`✅ Generated version changelog: ${outputFile}`);

  if (options.gitAnalysis && gitInfo) {
    console.log('\n📊 Git Analysis Summary:');
    console.log(gitInfo);
  }
}

async function collectGitInfo(
  projectRoot: string,
  phase: string,
  fromVersion?: string
): Promise<string> {
  const { execSync } = require('child_process');

  try {
    const range = fromVersion ? `${fromVersion}..${phase}` : phase;

    // Get commit count
    const commitCount = execSync(
      `git rev-list --count ${range}`,
      { cwd: projectRoot, encoding: 'utf-8' }
    ).trim();

    // Get changed files summary
    const diffStat = execSync(
      `git diff ${range} --stat | tail -1`,
      { cwd: projectRoot, encoding: 'utf-8' }
    ).trim();

    return `   Commits: ${commitCount}\n   Changes: ${diffStat}`;
  } catch (error) {
    return '   (Git analysis unavailable)';
  }
}
```

**Output**:
```
✅ Generated version changelog: .f5/docs/versions/v2.0.md

📊 Git Analysis Summary:
   Commits: 47
   Changes: 23 files changed, 1205 insertions(+), 342 deletions(-)
```

---

## Command Registration

```typescript
// packages/cli/src/commands/docs.ts

import { Command } from 'commander';
import { docsInit, docsAnalyze, docsVersion } from './docs-handlers';

export function registerDocsCommand(program: Command) {
  const docs = program
    .command('docs')
    .description('Reverse engineering documentation commands');

  docs
    .command('init')
    .description('Initialize .f5/docs/ structure')
    .option('--force', 'Overwrite existing structure')
    .option('--template <name>', 'Template style', 'standard')
    .option('--lang <code>', 'Output language (en, vn, ja)', 'en')
    .action(docsInit);

  docs
    .command('analyze')
    .description('Run reverse engineering analysis')
    .option('--module <name>', 'Analyze specific module')
    .option('--entity <name>', 'Analyze specific entity')
    .option('--framework <type>', 'Specify framework')
    .option('--output <path>', 'Custom output path')
    .option('--prompt <name>', 'Use specific prompt file')
    .option('--dry-run', 'Show what would be analyzed')
    .action(docsAnalyze);

  docs
    .command('version <phase>')
    .description('Generate version changelog')
    .option('--from <version>', 'Compare from version')
    .option('--git-analysis', 'Include git diff analysis')
    .option('--output <path>', 'Custom output path')
    .option('--template <name>', 'Use custom template')
    .action(docsVersion);
}
```

---

## Integration with Main CLI

```typescript
// packages/cli/src/index.ts

import { registerDocsCommand } from './commands/docs';

// ... existing code ...

registerDocsCommand(program);
```

---

## File Structure

```
packages/cli/src/
├── commands/
│   ├── docs.ts              # Command registration
│   └── docs-handlers.ts     # Command implementations
└── index.ts                 # Main CLI entry (add registration)

workflows/reverse-engineering/
├── WORKFLOW.md              # Updated with CLI references
├── CLI-INTEGRATION.md       # This proposal
├── templates/
│   ├── docs-readme.md
│   ├── entity-template.md
│   ├── workflow-template.md
│   └── version-template.md
└── prompts/
    ├── analyze-git-history.md
    ├── analyze-laravel.md
    ├── analyze-models.md
    ├── extract-business-rules.md
    └── extract-entities.md
```

---

## Next Steps

1. [ ] Implement `docsInit` command
2. [ ] Implement `docsAnalyze` command
3. [ ] Implement `docsVersion` command
4. [ ] Add tests for each command
5. [ ] Update CLI help documentation
6. [ ] Add to `f5 doctor` checks

---

## Usage Examples

```bash
# Full workflow
cd /path/to/legacy-project
f5 docs init
f5 docs analyze --framework laravel
f5 docs version v1.0 --git-analysis

# Quick analysis
f5 docs analyze --entity User --dry-run

# Version comparison
f5 docs version v2.0 --from v1.0 --git-analysis
```

---

*Proposal created for F5 Framework v2.0*
