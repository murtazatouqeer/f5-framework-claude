# MCP Server Setup

F5 Framework tích hợp với các MCP (Model Context Protocol) servers để mở rộng khả năng của Claude Code.

## Recommended MCP Servers

| Server | Purpose | Used By F5 Commands |
|--------|---------|---------------------|
| **Context7** | Documentation lookup | `/f5-research`, `/f5-implement`, `/f5-design` |
| **Sequential Thinking** | Multi-step reasoning | `/f5-test-it`, `/f5-analyze`, `/f5-gate` |
| **Playwright** | E2E & Visual testing | `/f5-test-e2e`, `/f5-test-visual` |
| **Serena** | Code understanding | `/f5-load`, `/f5-analyze`, `/f5-refactor` |

## Quick Profile Setup

F5 provides MCP profiles to balance capabilities with token usage:

```bash
# Minimal (low token usage)
/f5-mcp profile minimal

# Standard (recommended for most work)
/f5-mcp profile standard

# Testing (full E2E capabilities)
/f5-mcp profile testing

# Research (BA workflow)
/f5-mcp profile research

# Full (all capabilities)
/f5-mcp profile full
```

| Profile | Servers | Token Est. | Best For |
|---------|---------|------------|----------|
| `minimal` | context7 | ~3K | Quick fixes |
| `standard` | context7, sequential | ~8K | Feature dev |
| `testing` | + playwright | ~22K | G3 gate |
| `research` | context7, tavily | ~6K | D1 gate |
| `full` | All 6 servers | ~45K | Complex projects |

---

## API Key Setup

Some MCP servers require API keys:

### Tavily (Research & Web Search)

```bash
# Set API key
export TAVILY_API_KEY="your-api-key"

# Get key from: https://app.tavily.com
```

### GitHub (PR Management)

```bash
# Set GitHub token
export GITHUB_TOKEN="your-github-token"

# Get token from: GitHub Settings → Developer Settings → Personal Access Tokens
```

Add to your shell profile (`~/.zshrc` or `~/.bashrc`) for persistence:

```bash
echo 'export TAVILY_API_KEY="your-key"' >> ~/.zshrc
echo 'export GITHUB_TOKEN="your-token"' >> ~/.zshrc
source ~/.zshrc
```

---

## Manual Configuration

Add the following to your Claude Code settings file (`~/.claude/settings.json`):

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-context7"]
    },
    "sequential-thinking": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-sequential-thinking"]
    },
    "playwright": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-playwright"]
    },
    "serena": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-serena"]
    }
  }
}
```

### Verify Setup

After adding MCP configuration:

1. Restart Claude Code completely
2. Run `/f5-doctor` to verify MCP servers are detected

## Detailed Server Information

### Context7 - Documentation Lookup

Context7 cung cấp tra cứu documentation cho các libraries và frameworks.

**Used By:**
- `/f5-research` - Research technologies and patterns
- `/f5-implement` - Get implementation examples
- `/f5-design` - Reference design patterns

**Example Usage:**
```bash
# In Claude Code
/f5-research "React Server Components best practices"
/f5-implement "user authentication with NextAuth"
```

### Sequential Thinking - Multi-step Reasoning

Sequential Thinking giúp Claude phân tích các vấn đề phức tạp qua nhiều bước.

**Used By:**
- `/f5-test-it` - Integration testing analysis
- `/f5-analyze` - Code analysis and review
- `/f5-gate` - Quality gate verification

**Example Usage:**
```bash
/f5-analyze "security vulnerabilities in auth module"
/f5-gate check G3 --detailed
```

### Playwright - Browser Automation

Playwright cho phép E2E testing và visual regression testing.

**Used By:**
- `/f5-test-e2e` - End-to-end testing
- `/f5-test-visual` - Visual regression testing

**Example Usage:**
```bash
/f5-test-e2e journey login
/f5-test-visual --compare-figma --threshold 5
```

### Serena - Code Understanding

Serena cung cấp semantic code understanding và project memory.

**Used By:**
- `/f5-load` - Load project context
- `/f5-analyze` - Deep code analysis
- `/f5-refactor` - Safe refactoring

**Example Usage:**
```bash
/f5-load
/f5-analyze "find all usages of UserService"
```

## Optional MCP Servers

### Chrome DevTools

For performance profiling and debugging:

```json
{
  "chrome-devtools": {
    "command": "npx",
    "args": ["-y", "@anthropic/mcp-chrome-devtools"]
  }
}
```

**Used By:**
- `/f5-test-visual` - Screenshot capture
- Performance analysis

### Magic (21st.dev)

For UI component generation:

```json
{
  "magic": {
    "command": "npx",
    "args": ["-y", "@anthropic/mcp-magic"]
  }
}
```

**Used By:**
- `/f5-web` - Frontend development
- UI component generation

## Complete Configuration Example

Full `~/.claude/settings.json` với tất cả MCP servers:

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-context7"]
    },
    "sequential-thinking": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-sequential-thinking"]
    },
    "playwright": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-playwright"]
    },
    "serena": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-serena"]
    },
    "chrome-devtools": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-chrome-devtools"]
    },
    "magic": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-magic"]
    }
  }
}
```

## Troubleshooting

### MCP Server Not Starting

```bash
# Check if npx works
npx -y @upstash/context7-mcp --help

# Check Claude settings file
cat ~/.claude/settings.json

# Ensure valid JSON
python3 -c "import json; json.load(open('$HOME/.claude/settings.json'))"

# Restart Claude Code completely
# macOS: Cmd+Q then reopen
# Windows: Close all Claude windows, reopen
```

### "MCP not detected" in /f5-doctor

1. Verify settings.json syntax is correct
2. Restart Claude Code completely (not just reload)
3. Check that npx has network access
4. Run F5 MCP health check:
   ```bash
   /f5-selftest --mcp
   ```

### Playwright Browser Issues

```bash
# Install browsers if needed
npx playwright install chromium

# Or install all browsers
npx playwright install

# Check installation
npx playwright --version
```

### High Token Usage

If you're running out of context:

```bash
# Switch to minimal profile
/f5-mcp profile minimal

# Check current token usage
/f5-selftest --mcp
```

### Permission Errors

```bash
# Fix npm cache permissions
sudo chown -R $(whoami) ~/.npm

# Or use nvm
nvm install 18
nvm use 18
```

### API Key Not Working

```bash
# Verify environment variable is set
echo $TAVILY_API_KEY
echo $GITHUB_TOKEN

# If empty, reload shell
source ~/.zshrc

# Or set for current session
export TAVILY_API_KEY="your-key"
```

## F5 Commands Without MCP

F5 commands vẫn hoạt động mà không có MCP servers, nhưng với khả năng hạn chế:

| Command | Without MCP | With MCP |
|---------|-------------|----------|
| `/f5-test-e2e` | Manual instructions | Automated browser testing |
| `/f5-test-visual` | Manual comparison | Automated screenshot diff |
| `/f5-research` | Web search only | Documentation lookup |
| `/f5-analyze` | Basic analysis | Deep semantic analysis |

## Best Practices

1. **Always restart Claude Code** after changing MCP configuration
2. **Run `/f5-doctor`** to verify MCP setup
3. **Start with core 4 servers** (context7, sequential, playwright, serena)
4. **Add optional servers** as needed

---

## Next Steps

- [Installation Guide](installation.md)
- [Quick Start](quick-start.md)
- [Command Reference](../guides/commands-reference.md)
