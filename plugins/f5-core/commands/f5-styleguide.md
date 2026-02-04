# /f5-styleguide - Style Guide Management

Generate and manage project style guides from learned patterns.

## Usage

```bash
/f5-styleguide <action> [options]
```

## Actions

### generate
Generate style guide from learning profile.

```bash
/f5-styleguide generate [--format <format>] [--output <path>]
```

**Options:**
- `--format` - Output format: markdown (default), html, json
- `--output` - Output path (default: `.f5/learning/style-guide/README.md`)

### show
Display current style guide.

```bash
/f5-styleguide show [section]
```

**Sections:**
- `naming` - Naming conventions
- `style` - Code style rules
- `architecture` - Architecture guidelines
- `examples` - Code examples
- `all` - Full guide (default)

### update
Update style guide with new patterns.

```bash
/f5-styleguide update [--from-profile] [--from-scan]
```

### export
Export style guide for team sharing.

```bash
/f5-styleguide export [--format <format>] [--output <path>]
```

**Formats:**
- `markdown` - Standard markdown
- `html` - Styled HTML page
- `pdf` - PDF document (requires pandoc)
- `confluence` - Confluence wiki format
- `notion` - Notion markdown

### lint-rules
Generate linting configuration from style guide.

```bash
/f5-styleguide lint-rules [--target <linter>]
```

**Targets:**
- `eslint` - ESLint configuration
- `prettier` - Prettier configuration
- `stylelint` - Stylelint configuration

## Examples

```bash
# Generate markdown style guide
/f5-styleguide generate

# Generate HTML format
/f5-styleguide generate --format html --output docs/style-guide.html

# Show naming conventions
/f5-styleguide show naming

# Update from latest scan
/f5-styleguide update --from-scan

# Export for Confluence
/f5-styleguide export --format confluence --output style-guide.wiki

# Generate ESLint config
/f5-styleguide lint-rules --target eslint
```

## Execution

When user runs this command:

### ACTION: GENERATE

1. **Load Learning Profile**:
   ```bash
   if [ ! -f ".f5/learning/profile.yaml" ]; then
     echo "No learning profile. Run /f5-learn scan first."
     exit 1
   fi
   PROFILE=$(cat .f5/learning/profile.yaml)
   ```

2. **Generate Style Guide Content**:
   ```markdown
   # [PROJECT_NAME] Style Guide

   Generated: [DATE]
   Based on: Learning Profile v[VERSION]
   Confidence: [SCORE]%

   ---

   ## Table of Contents

   1. [Naming Conventions](#naming-conventions)
   2. [Code Style](#code-style)
   3. [Architecture](#architecture)
   4. [Error Handling](#error-handling)
   5. [Testing](#testing)
   6. [Documentation](#documentation)
   7. [Examples](#examples)

   ---

   ## Naming Conventions

   ### Files

   **Pattern:** {{FILE_PATTERN}}

   | Type | Convention | Example |
   |------|------------|---------|
   | Components | {{FILE_PATTERN}} | `user-profile.tsx` |
   | Services | {{FILE_PATTERN}} | `user-service.ts` |
   | Utils | {{FILE_PATTERN}} | `date-utils.ts` |

   ### Variables

   **Pattern:** {{VAR_PATTERN}}

   | Type | Convention | Example |
   |------|------------|---------|
   | Regular | camelCase | `userName`, `orderItems` |
   | Boolean | {{BOOL_PREFIX}}CamelCase | `isActive`, `hasPermission` |
   | Private | {{PRIVATE_PREFIX}}camelCase | `_internalState` |
   | Constants | SCREAMING_SNAKE | `MAX_RETRY_COUNT` |

   ### Functions

   **Pattern:** {{FUNC_PATTERN}}

   **Verb Prefixes:**
   {{#each VERB_PREFIXES}}
   - `{{this}}` - {{VERB_DESCRIPTION}}
   {{/each}}

   | Action | Prefix | Example |
   |--------|--------|---------|
   | Get single | `find`, `get` | `findUserById()` |
   | Get multiple | `list`, `getAll` | `listOrders()` |
   | Create | `create`, `add` | `createUser()` |
   | Update | `update`, `set` | `updateProfile()` |
   | Delete | `delete`, `remove` | `deleteOrder()` |
   | Boolean check | `is`, `has`, `can` | `isValid()` |
   | Event handler | `handle`, `on` | `handleSubmit()` |

   ### Classes

   **Pattern:** PascalCase + Role Suffix

   | Role | Suffix | Example |
   |------|--------|---------|
   | Service | `Service` | `UserService` |
   | Controller | `Controller` | `AuthController` |
   | Repository | `Repository` | `OrderRepository` |
   | Entity | (none) | `User`, `Order` |
   | DTO | `Dto` | `CreateUserDto` |
   | Module | `Module` | `AuthModule` |

   ### Interfaces & Types

   | Element | Convention | Example |
   |---------|------------|---------|
   | Interface | {{INTERFACE_PATTERN}} | `IUserRepository` or `UserRepository` |
   | Type | {{TYPE_PATTERN}} | `UserType`, `OrderStatus` |
   | Enum | PascalCase | `UserRole`, `OrderStatus` |

   ---

   ## Code Style

   ### Formatting

   | Property | Value |
   |----------|-------|
   | Indentation | {{INDENT_SIZE}} {{INDENT_TYPE}} |
   | Line Length | {{MAX_LINE}} characters |
   | Quotes | {{QUOTE_TYPE}} |
   | Semicolons | {{SEMICOLON}} |
   | Trailing Commas | {{TRAILING_COMMA}} |

   ### Imports

   **Order:**
   1. React/Framework imports
   2. External libraries
   3. Internal modules
   4. Relative imports
   5. Types/Interfaces

   **Example:**
   ```typescript
   // Framework
   import { Injectable } from '@nestjs/common';

   // External
   import { v4 as uuid } from 'uuid';

   // Internal
   import { UserRepository } from '@/repositories';

   // Relative
   import { CreateUserDto } from './dto';

   // Types
   import type { User } from '@/types';
   ```

   ### Functions

   | Preference | Usage |
   |------------|-------|
   | Arrow Functions | {{ARROW_PREFERENCE}} |
   | Const | {{CONST_PREFERENCE}} |
   | Explicit Types | {{EXPLICIT_TYPES}} |

   ---

   ## Architecture

   **Pattern:** {{ARCHITECTURE_PATTERN}}

   ### Layer Structure

   ```
   {{#each LAYERS}}
   {{this.path}}/  ({{this.name}})
   {{/each}}
   ```

   ### Dependency Rules

   {{DEPENDENCY_DESCRIPTION}}

   ```
   {{DEPENDENCY_DIAGRAM}}
   ```

   ---

   ## Error Handling

   **Pattern:** {{ERROR_PATTERN}}

   ```typescript
   {{ERROR_EXAMPLE}}
   ```

   ---

   ## Testing

   | Property | Value |
   |----------|-------|
   | Framework | {{TEST_FRAMEWORK}} |
   | File Pattern | {{TEST_FILE_PATTERN}} |
   | Location | {{TEST_LOCATION}} |

   **Naming:**
   ```typescript
   describe('UserService', () => {
     describe('createUser', () => {
       it('should create a new user', async () => {
         // Arrange
         // Act
         // Assert
       });
     });
   });
   ```

   ---

   ## Documentation

   **Style:** {{DOC_STYLE}}

   ```typescript
   /**
    * Description of the function
    * @param userId - The user's unique identifier
    * @returns The user object or null
    * @throws {NotFoundException} When user is not found
    */
   async findUserById(userId: string): Promise<User | null> {
     // ...
   }
   ```

   ---

   ## Examples

   See `.f5/learning/examples/` for complete code examples.

   ---

   ## Custom Rules

   {{#each CUSTOM_RULES}}
   ### {{this.name}}

   **Severity:** {{this.severity}}

   {{this.description}}

   {{#if this.example}}
   **Example:**
   ```typescript
   // Bad
   {{this.bad_example}}

   // Good
   {{this.good_example}}
   ```
   {{/if}}
   {{/each}}
   ```

3. **Save Style Guide**:
   ```bash
   mkdir -p .f5/learning/style-guide
   echo "$STYLE_GUIDE" > .f5/learning/style-guide/README.md
   ```

### ACTION: LINT-RULES

1. **Generate ESLint Config**:
   ```javascript
   // .eslintrc.js generated from style guide
   module.exports = {
     rules: {
       // From naming conventions
       'camelcase': ['error', { properties: 'always' }],
       '@typescript-eslint/naming-convention': [
         'error',
         { selector: 'variable', format: ['camelCase', 'UPPER_CASE'] },
         { selector: 'function', format: ['camelCase'] },
         { selector: 'class', format: ['PascalCase'] },
         { selector: 'interface', format: ['PascalCase'], prefix: ['I'] }
       ],

       // From code style
       'indent': ['error', {{INDENT_SIZE}}],
       'quotes': ['error', '{{QUOTE_TYPE}}'],
       'semi': ['error', '{{SEMICOLON ? 'always' : 'never'}}'],
       'comma-dangle': ['error', '{{TRAILING_COMMA}}'],
       'max-len': ['warn', { code: {{MAX_LINE}} }],

       // From custom rules
       {{#each CUSTOM_RULES}}
       '{{this.eslint_rule}}': '{{this.severity}}',
       {{/each}}
     }
   };
   ```

2. **Generate Prettier Config**:
   ```json
   {
     "tabWidth": {{INDENT_SIZE}},
     "useTabs": {{INDENT_TYPE === 'tabs'}},
     "singleQuote": {{QUOTE_TYPE === 'single'}},
     "semi": {{SEMICOLON}},
     "trailingComma": "{{TRAILING_COMMA}}",
     "printWidth": {{MAX_LINE}}
   }
   ```

## Output Format

### Generated Style Guide

```
📖 Style Guide Generated
━━━━━━━━━━━━━━━━━━━━━━━

Project: my-project
Based on: Learning Profile v1.0.0
Confidence: 85%

Sections:
  ✅ Naming Conventions (15 rules)
  ✅ Code Style (8 rules)
  ✅ Architecture (3 guidelines)
  ✅ Error Handling (2 patterns)
  ✅ Testing (4 conventions)
  ✅ Documentation (3 requirements)
  ✅ Custom Rules (5 rules)

📁 Saved to: .f5/learning/style-guide/README.md

Share with team: /f5-styleguide export --format html
```

### Lint Rules Generated

```
📋 Lint Configuration Generated
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Target: ESLint

Rules Generated:
  ✅ naming-convention (from naming profile)
  ✅ indent (from code style)
  ✅ quotes (from code style)
  ✅ semi (from code style)
  ✅ max-len (from code style)
  ✅ no-console (from custom rules)

📁 Saved to: .eslintrc.generated.js

To apply: cp .eslintrc.generated.js .eslintrc.js
```

## Storage

```
.f5/learning/style-guide/
├── README.md              # Main style guide
├── naming.md              # Naming conventions detail
├── style.md               # Code style detail
├── architecture.md        # Architecture guidelines
├── examples.md            # Code examples
└── exports/
    ├── style-guide.html   # HTML export
    └── style-guide.wiki   # Confluence export
```

## Integration

### With /f5-learn
Style guide is auto-updated when learning profile changes.

### With /f5-review
Reviews check code against style guide rules.

### With CI/CD
Export lint rules for automated checking.

## Best Practices

1. **Generate after scan** - Run after `/f5-learn scan`
2. **Review and adjust** - Check generated rules match intent
3. **Export for team** - Share HTML or Confluence format
4. **Integrate with linting** - Apply generated lint rules
5. **Keep updated** - Regenerate when patterns change
