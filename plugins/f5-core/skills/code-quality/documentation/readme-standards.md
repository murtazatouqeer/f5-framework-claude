---
name: readme-standards
description: Standards for README and project documentation
category: code-quality/documentation
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# README Standards

## Overview

A good README is the first impression of your project. It should help users quickly understand what the project does, how to use it, and how to contribute.

## Essential Sections

### 1. Project Title and Description

```markdown
# Project Name

![Build Status](https://img.shields.io/github/actions/workflow/status/owner/repo/ci.yml)
![npm version](https://img.shields.io/npm/v/package-name)
![License](https://img.shields.io/badge/license-MIT-blue)

A brief, compelling description of what this project does and why it exists.
Key benefits and use cases in 2-3 sentences.

## Highlights

- ⚡ **Fast** - Optimized for performance
- 🔒 **Secure** - Built with security in mind
- 🛠 **Flexible** - Highly configurable
- 📦 **Lightweight** - Minimal dependencies
```

### 2. Table of Contents (for long READMEs)

```markdown
## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [API Reference](#api-reference)
- [Configuration](#configuration)
- [Contributing](#contributing)
- [License](#license)
```

### 3. Installation

```markdown
## Installation

### Prerequisites

- Node.js >= 18.0.0
- npm >= 9.0.0

### Package Manager

```bash
# npm
npm install package-name

# yarn
yarn add package-name

# pnpm
pnpm add package-name
```

### From Source

```bash
git clone https://github.com/owner/repo.git
cd repo
npm install
npm run build
```
```

### 4. Quick Start

```markdown
## Quick Start

Get up and running in 30 seconds:

```typescript
import { Client } from 'package-name';

const client = new Client({ apiKey: 'your-key' });

// Fetch data
const result = await client.getData();
console.log(result);
```

For more examples, see the [examples directory](./examples).
```

### 5. Usage Examples

```markdown
## Usage

### Basic Example

```typescript
import { createApp } from 'package-name';

const app = createApp({
  port: 3000,
  debug: true,
});

app.start();
```

### Advanced Configuration

```typescript
import { createApp, middleware } from 'package-name';

const app = createApp({
  port: 3000,
  middleware: [
    middleware.logging(),
    middleware.rateLimit({ max: 100 }),
  ],
  database: {
    url: process.env.DATABASE_URL,
    pool: { min: 2, max: 10 },
  },
});
```

### Common Use Cases

<details>
<summary>Authentication Example</summary>

```typescript
// Authentication setup
const auth = app.useAuth({
  provider: 'jwt',
  secret: process.env.JWT_SECRET,
});
```

</details>

<details>
<summary>Error Handling</summary>

```typescript
// Global error handler
app.onError((error, context) => {
  console.error('Error:', error.message);
  return { status: 500, message: 'Internal error' };
});
```

</details>
```

### 6. API Reference

```markdown
## API Reference

### `createClient(options)`

Creates a new client instance.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `options.apiKey` | `string` | Yes | Your API key |
| `options.baseUrl` | `string` | No | Custom API URL |
| `options.timeout` | `number` | No | Request timeout (ms) |

**Returns:** `Client` instance

**Example:**

```typescript
const client = createClient({
  apiKey: 'sk-xxx',
  timeout: 5000,
});
```

### `client.getData(query)`

Fetches data based on query parameters.

| Parameter | Type | Description |
|-----------|------|-------------|
| `query.filter` | `object` | Filter criteria |
| `query.limit` | `number` | Max results (default: 10) |

**Returns:** `Promise<Data[]>`

**Throws:**
- `AuthenticationError` - Invalid API key
- `RateLimitError` - Rate limit exceeded
```

### 7. Configuration

```markdown
## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `API_KEY` | API authentication key | Required |
| `PORT` | Server port | `3000` |
| `LOG_LEVEL` | Logging verbosity | `info` |
| `DATABASE_URL` | Database connection string | Required |

### Configuration File

Create a `config.json` in your project root:

```json
{
  "server": {
    "port": 3000,
    "host": "0.0.0.0"
  },
  "database": {
    "url": "${DATABASE_URL}",
    "pool": {
      "min": 2,
      "max": 10
    }
  },
  "logging": {
    "level": "info",
    "format": "json"
  }
}
```
```

### 8. Contributing

```markdown
## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Quick Start for Contributors

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`npm test`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Development Setup

```bash
# Install dependencies
npm install

# Run tests
npm test

# Run linter
npm run lint

# Build
npm run build
```
```

### 9. License

```markdown
## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
```

## Additional Sections

### Troubleshooting

```markdown
## Troubleshooting

### Common Issues

<details>
<summary>"Module not found" error</summary>

**Problem:** Import statements fail to resolve.

**Solution:**
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

</details>

<details>
<summary>Connection timeout</summary>

**Problem:** API requests timeout.

**Solution:** Increase the timeout in configuration:
```typescript
const client = createClient({
  timeout: 30000, // 30 seconds
});
```

</details>
```

### FAQ

```markdown
## FAQ

**Q: Can I use this in production?**
A: Yes! This library is production-ready and used by [Company A], [Company B].

**Q: Is TypeScript supported?**
A: Yes, full TypeScript support with type definitions included.

**Q: How do I report bugs?**
A: Please open an issue on [GitHub Issues](https://github.com/owner/repo/issues).
```

### Changelog

```markdown
## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a list of changes.

### Recent Changes

- **v2.0.0** - Breaking changes, new API
- **v1.5.0** - Added authentication support
- **v1.4.0** - Performance improvements
```

## README Templates

### Library/Package Template

```markdown
# Library Name

Brief description.

## Installation

\`\`\`bash
npm install library-name
\`\`\`

## Quick Start

\`\`\`typescript
import { feature } from 'library-name';
// usage
\`\`\`

## API Reference

[API documentation]

## License

MIT
```

### Application Template

```markdown
# Application Name

Brief description.

## Features

- Feature 1
- Feature 2

## Getting Started

### Prerequisites

- Node.js 18+
- PostgreSQL 14+

### Installation

1. Clone the repo
2. Install dependencies
3. Configure environment
4. Start the application

## Usage

[Usage instructions]

## Deployment

[Deployment guide]

## License

MIT
```

## Best Practices

| Practice | Description |
|----------|-------------|
| Keep it updated | Update README when API changes |
| Use badges | Show build status, version, coverage |
| Include examples | Working code examples for common use cases |
| Be concise | Get to the point quickly |
| Use visuals | Screenshots, diagrams when helpful |
| Test examples | Ensure code examples actually work |
| Link to docs | Reference detailed documentation |
| Add search keywords | Help users find your project |
