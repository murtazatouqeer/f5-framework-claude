# F5 Framework Installation Guide

## Quick Install (Recommended)

### Via Claude Code Plugin Marketplace

```bash
# Install the full framework (f5-core + f5-stacks)
/plugin marketplace add fujigo/f5-framework

# Or install only the core plugin
/plugin marketplace add fujigo/f5-framework/f5-core
```

### Post-Installation

```bash
# Initialize F5 in your workspace
/f5-init

# Verify installation
/f5-status
```

## Plugin Structure

F5 Framework is distributed as two plugins:

| Plugin | Size | Description | Required |
|--------|------|-------------|----------|
| **f5-core** | 7.3 MB | Commands, agents, core skills, quality gates | Yes |
| **f5-stacks** | 30 MB | Technology stacks, domains, stack-specific skills | Optional |

### f5-core (Required)

Core development tools:
- **70 Commands** - Slash commands for all development phases
- **25 Agents** - AI agents for specialized tasks
- **381 Skills** - Core development skills
- **7 Hooks** - Claude Code integration hooks
- **78 Configs** - Framework configuration files

### f5-stacks (Optional)

Extended stack support:
- **872 Stack Definitions** - Backend, frontend, mobile, infrastructure
- **492 Stack Skills** - Technology-specific skills
- **1,159 Domain Files** - 14 industry domains
- **44 Workflows** - Project workflow templates

## Alternative Installation Methods

### Git Clone

```bash
# Clone to Claude plugins directory
git clone https://github.com/fujigo/f5-framework.git ~/.claude/plugins/f5-framework

# Or to custom location
git clone https://github.com/fujigo/f5-framework.git /path/to/f5-framework
/plugin add /path/to/f5-framework
```

### Local Install (Development)

```bash
# Clone repository
git clone https://github.com/fujigo/f5-framework.git
cd f5-framework

# Install dependencies
pnpm install

# Build
pnpm build

# Add as local plugin
/plugin add ./
```

## MCP Server Setup (Recommended)

F5 Framework works best with these MCP servers:

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"]
    },
    "sequential-thinking": {
      "command": "npx",
      "args": ["-y", "@anthropic/sequential-thinking-mcp"]
    },
    "playwright": {
      "command": "npx",
      "args": ["-y", "@anthropic/playwright-mcp"]
    },
    "tavily": {
      "command": "npx",
      "args": ["tavily-mcp"],
      "env": {
        "TAVILY_API_KEY": "${TAVILY_API_KEY}"
      }
    }
  }
}
```

### Quick MCP Setup

```bash
# After F5 installation, run:
/f5-mcp setup

# Or use a predefined profile:
/f5-mcp profile standard
```

## Verification

After installation, verify everything is working:

```bash
# Check installation status
/f5-status

# Run diagnostics
/f5-status doctor

# List available commands
/f5-help
```

## Getting Started

1. **Load project context**
   ```bash
   /f5-load
   ```

2. **Check project status**
   ```bash
   /f5-status
   ```

3. **Start development workflow**
   ```bash
   # Design phase
   /f5-design D1  # Research document
   /f5-design D2  # SRS document

   # Implementation phase
   /f5-implement feature "user authentication"

   # Testing phase
   /f5-test
   ```

## Updating

```bash
# Update via marketplace
/plugin marketplace update fujigo/f5-framework

# Or via git
cd ~/.claude/plugins/f5-framework
git pull
```

## Uninstalling

```bash
# Remove via marketplace
/plugin marketplace remove fujigo/f5-framework

# Or manually
rm -rf ~/.claude/plugins/f5-framework
```

## Requirements

- Claude Code >= 2.0.0
- Node.js >= 18.0.0
- macOS, Linux, or Windows

## Support

- **Documentation**: https://f5-framework.dev/docs
- **Issues**: https://github.com/fujigo/f5-framework/issues
- **Discussions**: https://github.com/fujigo/f5-framework/discussions

## License

MIT License - see [LICENSE](LICENSE) for details.
