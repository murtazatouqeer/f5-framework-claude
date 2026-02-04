# F5 Workflow Studio Setup Guide

F5 Workflow Studio (f5-wf-studio) là visual workflow editor để thiết kế và chạy Claude Code workflows.

> **Đã có trên VS Code Marketplace!**
> Không cần build from source nữa. Install trực tiếp từ Marketplace.

## Installation

### Option 1: VS Code Marketplace (Khuyến nghị)

1. Mở VS Code
2. `Cmd+Shift+X` → Search "F5 Workflow Studio"
3. Click Install
4. Hoặc CLI: `code --install-extension fujigo.f5-wf-studio`

### Option 2: Command Line

```bash
ext install fujigo.f5-wf-studio
```

## Sử dụng

1. `Cmd+Shift+P` → "F5 Workflow Studio: Open Editor"
2. Tạo workflow mới hoặc import từ `.vscode/workflows/`
3. Drag-and-drop nodes để thiết kế
4. Export thành Claude Code slash command

## Tích hợp với F5 Framework

F5 Workflow Studio tự động detect và tích hợp với F5 Framework:

- **Commands:** Browse `.claude/commands/` từ Node Palette
- **Skills:** Load skills từ `.claude/skills/`
- **Agents:** Browse agents từ `.claude/agents/`
- **Workflows:** Import/Export `.vscode/workflows/`
- **Quality Gates:** D1-D4, G2-G4 gate nodes

## CLI Workflow Commands

F5 Framework CLI cũng hỗ trợ quản lý workflows qua command line:

```bash
f5 workflow list                    # List all workflows
f5 workflow info <name>             # Show workflow details
f5 workflow validate --all          # Validate all workflows
f5 workflow export <name>           # Export to Claude Code command
f5 workflow import file.json        # Import workflow from JSON
```

## Links

- **Marketplace:** https://marketplace.visualstudio.com/items?itemName=fujigo.f5-wf-studio
- **Publisher:** Fujigo Software Solutions
