---
description: Project learning, patterns, and code examples
argument-hint: <scan|show|apply|examples> [options]
---

# /f5-learn - Unified Learning & Examples Command

**Consolidated command** that replaces:
- `/f5-examples` → `/f5-learn examples`

Learn and apply project-specific coding patterns, naming conventions, and style preferences.

## ARGUMENTS
$ARGUMENTS

## MODE DETECTION

| Pattern | Mode | Description |
|---------|------|-------------|
| `examples <action>` | EXAMPLES | Code example management |
| `<other>` (default) | LEARN | Pattern learning |

---

## MODE: EXAMPLES (from /f5-examples)

### `/f5-learn examples <action>`

Collect, manage, and reference high-quality code examples.

| Action | Description |
|--------|-------------|
| `collect` | Find and score example code |
| `list [category]` | List examples by category |
| `show <id>` | Display specific example |
| `add <file>` | Manually add example |
| `remove <id>` | Remove example |
| `apply <id>` | Apply example to current context |

**Categories:** services, controllers, repositories, entities, utils, tests, components, hooks

**Examples:**
```bash
/f5-learn examples collect --category services
/f5-learn examples list tests
/f5-learn examples show svc_001
/f5-learn examples apply svc_001
```

---

## MODE: LEARN (Default)

Learn project-specific coding patterns.

## Usage

```bash
/f5-learn <action> [options]
```

## Actions

### scan
Analyze codebase to detect patterns.

```bash
/f5-learn scan [--full] [--path <dir>]
```

**Options:**
- `--full` - Deep scan including all file types
- `--path` - Specific directory to scan (default: project root)
- `--force` - Overwrite existing profile

### show
Display current learning profile.

```bash
/f5-learn show [section]
```

**Sections:**
- `naming` - Naming conventions
- `style` - Code style preferences
- `architecture` - Architecture patterns
- `all` - Full profile (default)

### apply
Apply learned patterns to current session.

```bash
/f5-learn apply [--strict]
```

**Options:**
- `--strict` - Enforce all patterns as errors

### correct
Record a correction to learn from.

```bash
/f5-learn correct "<original>" "<corrected>" [--file <path>]
```

### rule
Add or manage custom rules.

```bash
/f5-learn rule add "<name>" "<pattern>" [--severity <level>]
/f5-learn rule list
/f5-learn rule remove <id>
```

### reset
Reset learning profile.

```bash
/f5-learn reset [--keep-custom]
```

## Examples

```bash
# Full codebase scan
/f5-learn scan --full

# Show naming conventions
/f5-learn show naming

# Apply patterns
/f5-learn apply

# Record a correction
/f5-learn correct "getUserData" "findUserById" --file "src/services/user.ts"

# Add custom rule
/f5-learn rule add "no-any" ":\\s*any" --severity error

# Reset but keep custom rules
/f5-learn reset --keep-custom
```

## Execution

When user runs this command:

### ACTION: SCAN

1. **Initialize**:
   - Get project ID from `.f5/config.json`
   - Create/update `.f5/learning/profile.yaml`

2. **Analyze Files**:
   ```typescript
   // Scan patterns
   const patterns = {
     naming: analyzeNamingConventions(files),
     style: analyzeCodeStyle(files),
     architecture: analyzeArchitecture(files),
     errorHandling: analyzeErrorHandling(files),
     testing: analyzeTestingPatterns(files),
     documentation: analyzeDocumentation(files)
   };
   ```

3. **Detect Naming Conventions**:
   ```typescript
   // File naming
   analyzeFileNames(files) => {
     pattern: detectCase(fileNames), // kebab-case, camelCase, etc.
     examples: sampleFileNames,
     confidence: calculateConfidence(matches, total)
   }

   // Variable naming
   analyzeVariables(ast) => {
     pattern: detectCase(variables),
     prefixes: {
       boolean: detectBooleanPrefix(booleanVars), // is, has, should
       private: detectPrivatePrefix(privateVars), // _, __
       constant: detectConstantStyle(constants)   // UPPER_SNAKE
     }
   }

   // Function naming
   analyzeFunctions(ast) => {
     pattern: detectCase(functionNames),
     verb_prefixes: extractVerbPrefixes(functionNames) // get, set, create, etc.
   }

   // Class naming
   analyzeClasses(ast) => {
     pattern: "PascalCase", // Usually PascalCase
     suffixes: {
       service: detectSuffix(services),      // Service, Svc
       controller: detectSuffix(controllers), // Controller, Ctrl
       repository: detectSuffix(repos)        // Repository, Repo
     }
   }
   ```

4. **Detect Code Style**:
   ```typescript
   analyzeCodeStyle(files) => {
     indentation: detectIndentation(content), // spaces/tabs, size
     quotes: detectQuoteStyle(ast),           // single/double
     semicolons: detectSemicolonUsage(ast),   // true/false
     trailingCommas: detectTrailingCommas(ast),
     imports: analyzeImportOrder(ast),
     arrowFunctions: countArrowVsFunction(ast),
     constUsage: countConstVsLet(ast)
   }
   ```

5. **Detect Architecture**:
   ```typescript
   analyzeArchitecture(projectStructure) => {
     primary: detectArchitecturePattern(dirs),
     layers: mapLayersFromStructure(dirs),
     dependencyDirection: analyzeDependencies(imports)
   }
   ```

6. **Calculate Confidence**:
   ```typescript
   calculateConfidence(matches, total) => {
     const ratio = matches / total;
     return Math.round(ratio * 100);
   }
   ```

7. **Save Profile**:
   - Write to `.f5/learning/profile.yaml`
   - Store examples in `.f5/learning/patterns/`

### ACTION: SHOW

1. **Load Profile**:
   ```bash
   if [ -f ".f5/learning/profile.yaml" ]; then
     cat .f5/learning/profile.yaml
   else
     echo "No learning profile. Run /f5-learn scan first."
   fi
   ```

2. **Format Output**:
   ```markdown
   ## Learning Profile: [PROJECT_NAME]

   Scanned: [DATE] | Files: [COUNT] | Confidence: [SCORE]%

   ### Naming Conventions

   | Element | Pattern | Examples | Confidence |
   |---------|---------|----------|------------|
   | Files | kebab-case | user-service.ts | 95% |
   | Variables | camelCase | userName, isActive | 90% |
   | Functions | camelCase | getUserById, createOrder | 92% |
   | Classes | PascalCase + Suffix | UserService, AuthController | 98% |
   | Interfaces | I-prefix | IUserRepository | 85% |

   ### Code Style

   | Property | Value | Confidence |
   |----------|-------|------------|
   | Indentation | 2 spaces | 100% |
   | Quotes | single | 95% |
   | Semicolons | yes | 98% |
   | Arrow Functions | preferred | 88% |

   ### Architecture

   | Property | Value |
   |----------|-------|
   | Pattern | clean-architecture |
   | Layers | domain → application → infrastructure |
   | Dependency | inward |

   ### Custom Rules

   | Rule | Severity |
   |------|----------|
   | no-console | warning |
   | async-service | error |
   ```

### ACTION: APPLY

1. **Load Profile**:
   ```bash
   PROFILE=$(cat .f5/learning/profile.yaml)
   ```

2. **Set Session Rules**:
   ```markdown
   ### Pattern Rules Applied

   When generating code in this session:

   #### Naming
   - Files: Use {{FILE_PATTERN}}
   - Variables: Use {{VAR_PATTERN}}, prefix booleans with "{{BOOL_PREFIX}}"
   - Functions: Use {{FUNC_PATTERN}}, start with verb ({{VERBS}})
   - Classes: Use {{CLASS_PATTERN}}, suffix with role (Service, Controller, etc.)

   #### Style
   - Indentation: {{INDENT_SIZE}} {{INDENT_TYPE}}
   - Quotes: {{QUOTE_TYPE}}
   - Semicolons: {{SEMICOLON}}
   - Arrow functions: {{PREFER_ARROW}}

   #### Architecture
   - Follow {{ARCHITECTURE}} pattern
   - Respect layer dependencies
   - Place files in correct directories

   #### Custom Rules
   {{#each CUSTOM_RULES}}
   - {{this.name}}: {{this.description}}
   {{/each}}
   ```

### ACTION: CORRECT

1. **Parse Correction**:
   ```bash
   ORIGINAL="$1"
   CORRECTED="$2"
   FILE="${3:-unknown}"
   ```

2. **Analyze Difference**:
   ```typescript
   analyzeDiff(original, corrected) => {
     // Detect what changed
     if (isNamingChange(original, corrected)) {
       return { type: 'naming', details: extractNamingRule(original, corrected) };
     }
     if (isStyleChange(original, corrected)) {
       return { type: 'style', details: extractStyleRule(original, corrected) };
     }
     return { type: 'custom', details: { original, corrected } };
   }
   ```

3. **Create or Update Rule**:
   ```yaml
   # Add to learned_from_corrections
   - date: "2024-01-15T10:00:00Z"
     file: "src/services/user.ts"
     original: "getUserData"
     corrected: "findUserById"
     rule_created: "use-find-for-single-item"
   ```

4. **Update Profile**:
   - If naming pattern, update naming_conventions
   - If style pattern, update code_style
   - If new pattern, add to custom_rules

### ACTION: RULE

1. **Add Rule**:
   ```yaml
   # Append to custom_rules
   - id: "{{RULE_ID}}"
     name: "{{RULE_NAME}}"
     description: "Auto-generated from pattern"
     pattern: "{{PATTERN}}"
     severity: "{{SEVERITY}}"
     auto_fix: false
   ```

2. **List Rules**:
   ```markdown
   ### Custom Rules

   | ID | Name | Pattern | Severity |
   |----|------|---------|----------|
   | no-any | No any type | :\s*any | error |
   | use-logger | Use logger | console\. | warning |
   ```

3. **Remove Rule**:
   - Find rule by ID
   - Remove from custom_rules array
   - Save profile

## Output Format

### Scan Results

```
📚 Learning Profile Scan
━━━━━━━━━━━━━━━━━━━━━━━

Project: my-project
Files Analyzed: 150
Overall Confidence: 85%

✅ Naming Conventions
   Files:      kebab-case (95%)
   Variables:  camelCase (90%)
   Functions:  camelCase + verb (92%)
   Classes:    PascalCase + suffix (98%)

✅ Code Style
   Indentation: 2 spaces (100%)
   Quotes:      single (95%)
   Semicolons:  yes (98%)

✅ Architecture
   Pattern: clean-architecture (88%)
   Layers: domain → application → infrastructure

📁 Saved to .f5/learning/profile.yaml

Next: Run /f5-learn apply to use these patterns
```

### Correction Recorded

```
📝 Correction Recorded
━━━━━━━━━━━━━━━━━━━━━

File: src/services/user.service.ts

Original:  getUserData
Corrected: findUserById

Analysis:
- Changed verb: get → find
- Pattern: Use "find" for single item retrieval

Rule Created: use-find-for-single-item
Applied to: function naming conventions

Profile updated. This pattern will be used in future code generation.
```

## Integration

### With /f5-implement
Learning profile is automatically loaded and applied when generating code.

### With /f5-review
Code review checks against learned patterns.

### With /f5-load
Learning profile status shown in project summary.

## Best Practices

1. **Run scan on existing projects** before generating new code
2. **Record corrections** to teach patterns over time
3. **Review and adjust** auto-detected patterns
4. **Add custom rules** for project-specific requirements
5. **Reset periodically** if patterns have changed significantly

## Storage

```
.f5/learning/
├── profile.yaml           # Main learning profile
├── patterns/              # Detected pattern examples
│   ├── naming.yaml
│   ├── style.yaml
│   └── architecture.yaml
├── corrections/           # Recorded corrections
│   └── 2024-01-15.yaml
├── templates/             # Learned code templates
│   ├── service.ts
│   └── controller.ts
├── style-guide/           # Generated style guide
│   └── README.md
└── examples/              # Collected examples
    ├── services/
    └── controllers/
```

## Confidence Thresholds

| Confidence | Meaning | Action |
|------------|---------|--------|
| 90-100% | Very confident | Auto-apply |
| 70-89% | Confident | Apply with note |
| 50-69% | Uncertain | Suggest, don't enforce |
| < 50% | Low confidence | Skip or ask |
