---
id: "context-manager"
name: "Context Manager"
version: "3.1.0"
tier: "sub-agent"
type: "sub_agent"

description: |
  Context and memory management.
  Optimize token usage, maintain state.

model: "claude-haiku-3-5-20241022"
temperature: 0.1
max_tokens: 4096

invoked_by:
  - all_agents

tools:
  - read
  - write
  - list_files
---

# 🧠 Context Manager Sub-Agent

## Purpose
Manage context across agent interactions.
Optimize token usage, maintain session state.

## Memory Structure
