# F5 Framework Workflow Templates

Pre-built CC-WF-Studio workflow templates for common development patterns across F5 Framework domains.

## Overview

These templates provide quick-start workflows for enterprise development scenarios. Each template follows the CC-WF-Studio workflow schema (v1.0.0) and includes F5-specific metadata for seamless integration.

## Template Categories

| Domain | Template | Description |
|--------|----------|-------------|
| **auth** | user-registration.json | Complete user registration with validation |
| **auth** | login-flow.json | Multi-factor authentication workflow |
| **user** | user-crud.json | User CRUD operations with permissions |
| **product** | product-catalog.json | Product catalog management |
| **order** | order-processing.json | Order lifecycle management |
| **payment** | payment-integration.json | Payment gateway integration |
| **inventory** | stock-management.json | Inventory tracking and alerts |
| **notification** | multi-channel.json | Email, SMS, push notifications |
| **reporting** | report-generator.json | Dynamic report generation |
| **file-management** | file-upload.json | Secure file upload pipeline |
| **search** | search-index.json | Search indexing and optimization |
| **audit** | audit-log.json | Compliance audit logging |
| **localization** | translation-flow.json | Multi-language content management |
| **integration** | external-api.json | External API orchestration |

## Usage

### Via F5 CLI

```bash
# List available templates
f5 workflow list

# Load a template
f5 workflow load auth/user-registration

# Create new workflow from template
f5 workflow new --from auth/login-flow my-auth-flow
```

### Via CC-WF-Studio

1. Open CC-WF-Studio in VSCode
2. Use "Import Template" or load from `.f5/templates/workflows/`
3. Customize the workflow for your project requirements

## Template Structure

Each template follows this structure:

```json
{
  "id": "unique-template-id",
  "name": "Template Name",
  "description": "What this workflow does",
  "version": "1.0.0",
  "f5Metadata": {
    "domain": "domain-name",
    "category": "template-category",
    "complexity": "simple|medium|complex",
    "estimatedDuration": "5-10 minutes",
    "requiredSkills": ["skill-1", "skill-2"],
    "mcpServers": ["server-1", "server-2"],
    "qualityGates": ["G2", "G3"]
  },
  "nodes": [...],
  "connections": [...]
}
```

## F5 Metadata Fields

| Field | Description |
|-------|-------------|
| `domain` | F5 domain this template belongs to |
| `category` | Template category (auth, crud, workflow, etc.) |
| `complexity` | simple, medium, or complex |
| `estimatedDuration` | Expected time to customize and implement |
| `requiredSkills` | F5 skills needed for this workflow |
| `mcpServers` | Recommended MCP servers for execution |
| `qualityGates` | Applicable F5 quality gates |

## MCP Server Recommendations

| Domain | Recommended MCP Servers |
|--------|------------------------|
| auth, user | github, sequential-thinking |
| product, order | serena, context7 |
| payment | sequential-thinking, github |
| inventory | serena, context7 |
| notification | github, playwright |
| reporting | context7, serena |
| file-management | github, serena |
| search | serena, context7 |
| audit | sequential-thinking, github |
| localization | context7, serena |
| integration | tavily, sequential-thinking |

## Quality Gates

Templates include references to F5 quality gates:

- **D3**: Basic Design - Workflow design reviewed
- **D4**: Detail Design - Implementation details complete
- **G2**: Implementation - Code complete
- **G2.5**: Code Review - Review passed
- **G3**: Testing - All tests pass

## Customization Tips

1. **Variables**: Replace placeholder values with your project specifics
2. **Connections**: Add/remove branches based on your requirements
3. **MCP Servers**: Enable recommended servers for optimal execution
4. **Quality Gates**: Integrate gates appropriate to your project phase

## Contributing

To add new templates:

1. Create workflow in CC-WF-Studio
2. Export to appropriate domain folder
3. Add F5 metadata fields
4. Update this README with template description
5. Submit PR with template and documentation

## Related Documentation

- [F5 Framework Documentation](../../docs/)
- [F5 Workflow Studio](https://marketplace.visualstudio.com/items?itemName=fujigo.f5-wf-studio)
- [Quality Gates Reference](../../.claude/docs/GATES.md)
- [MCP Server Configuration](../../docker/mcp-archive/)
