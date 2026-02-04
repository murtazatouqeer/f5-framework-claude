# F5 Framework

[![Version](https://img.shields.io/badge/version-2.0.0-blue)](https://github.com/Fujigo-Software/f5-framework-claude)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Plugins](https://img.shields.io/badge/plugins-2-orange)](INSTALL.md)

> AI-Powered Development Framework for Claude Code

## Quick Start

```bash
# Add F5 Framework marketplace
/plugin marketplace add Fujigo-Software/f5-framework-claude

# Install plugins
/plugin install f5-core
/plugin install f5-stacks

# Initialize in your project
/f5-init

# Verify installation
/f5-status
```

## Plugins

| Plugin | Size | Description |
|--------|------|-------------|
| **f5-core** | 7.3 MB | 70 commands, 25 agents, 381 skills, quality gates |
| **f5-stacks** | 30 MB | 872 stacks, 14 domains, 44 workflow templates |

## Features

### Commands (70+)
- `/f5-init` - Initialize F5 Framework
- `/f5-analyze` - Analyze codebase architecture
- `/f5-implement` - Implement with quality gates
- `/f5-test` - TDD-driven testing
- `/f5-review` - Code review workflow
- `/f5-design` - Generate design documents (D1-D4)

### Technology Stacks
- **Backend**: NestJS, Spring Boot, Laravel, Django, FastAPI, Express
- **Frontend**: React, Angular, Vue.js, Next.js, Nuxt.js
- **Mobile**: Flutter, React Native, iOS, Android
- **Infrastructure**: Docker, Kubernetes, Terraform

### Industry Domains (14)
Agriculture, E-commerce, Education, Entertainment, Fintech, Healthcare, HR Management, Insurance, Logistics, Manufacturing, Real Estate, SaaS Platform, Travel & Hospitality

### Quality Gates
| Gate | Phase | Description |
|------|-------|-------------|
| D1-D4 | Design | Research, SRS, Basic/Detail Design |
| G2 | Implementation | Code complete |
| G2.5 | Review | Code review passed |
| G3 | Testing | All tests pass |
| G4 | Deployment | Production ready |

## AI Agents (25)

Invoke with `@f5:<alias>`:

| Agent | Aliases | Purpose |
|-------|---------|---------|
| System Architect | `@f5:architect` | System design, patterns |
| Code Generator | `@f5:backend`, `@f5:frontend` | Production code |
| Test Writer | `@f5:qa`, `@f5:test` | Unit/integration tests |
| Security Scanner | `@f5:security` | OWASP, vulnerabilities |
| Debugger | `@f5:debug` | Bug diagnosis |
| Code Reviewer | `@f5:review` | Code quality |
| Performance Analyzer | `@f5:perf` | Optimization |
| Documenter | `@f5:docs` | Documentation |
| Mentor | `@f5:mentor` | Explanations |

## MCP Integration

Recommended MCP servers:

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"]
    },
    "sequential-thinking": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-sequential-thinking"]
    },
    "playwright": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-playwright"]
    }
  }
}
```

## Documentation

| Document | Description |
|----------|-------------|
| [INSTALL.md](INSTALL.md) | Installation guide |
| [docs/COMMANDS.md](docs/COMMANDS.md) | Command reference |
| [docs/PLUGINS.md](docs/PLUGINS.md) | Plugin architecture |
| [docs/MIGRATION.md](docs/MIGRATION.md) | Migration from v1.x |

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open a Pull Request

## License

MIT License - see [LICENSE](LICENSE) for details.

---

**Made with love for Claude Code developers by [Fujigo Software Solutions](https://github.com/Fujigo-Software)**
