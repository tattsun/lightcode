# lightcode

A simple coding agent with tool calling support.

## ⚠️ Warning

When using `--no-permissions` option (including `make docker-run` and `sandbox.sh`), this agent may automatically:
- Execute shell commands on your system
- Read, write, and delete files
- Make network requests (API calls, web searches)

Use in a sandboxed environment (e.g., Docker) is strongly recommended.

## Setup

```bash
rye sync
```

## Environment Variables

```bash
export OPENAI_API_KEY=sk-xxxxx
export TAVILY_API_KEY=tvly-xxxxx  # Required for web search
```

## Usage

```bash
# Local
make run

# Docker
make docker-build
make docker-run

# Docker with custom directory
./sandbox.sh /path/to/your/project
```

## Options

| Option | Description |
|--------|-------------|
| `--no-permissions` | Skip permission prompts for tool execution |
| `--web-search` | Enable web search tools |
| `--log-file <path>` | Save session log to JSONL file |

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Ctrl-C` or `Esc` | Interrupt current operation (API call, tool execution) |

## Available Tools

### File Operations
- `read_file`, `write_file`, `edit_file`, `delete_file`, `move_file`, `copy_file`
- `list_files`, `find_files`, `grep`, `file_info`

### Media
- `read_image` - Read images for LLM visual recognition (PNG, JPEG, GIF, WebP)

### PowerPoint (shape-based layout control)
- `pptx_create` - Create presentations with full shape control
- `pptx_read` - Read slide content with position/size info
- `pptx_add_slide` - Add slides with shape-based layout
- `pptx_modify_slide` - Edit slides, add/remove shapes
- `pptx_export_image` - Export slides as PNG images
- `pptx_duplicate_slide` - Duplicate an existing slide
- `pptx_find_text` - Find text across slides
- `pptx_layout` - Align/distribute/snap shapes on a slide

### System
- `run_command` - Execute shell commands
- `subagent` - Run tasks in isolated subagent contexts (requires configuration)

## Configuration

Configure tools in `~/.lightcode/config.yaml` (global) or `./lightcode.yaml` (local). Local config overrides global.

```yaml
# Main agent tools (optional - defaults to all tools if not specified)
main_agent:
  tools:
    - run_command
    - read_file
    - write_file
    - subagent  # Include to enable subagent calls

# Subagent types for isolated task execution
subagents:
  general:
    description: "General-purpose agent for file operations"
    tools:
      - run_command
      - grep
      - find_files
      - read_file
      - write_file

  pptx:
    description: "PowerPoint specialist agent"
    tools:
      - read_file
      - write_file
      - pptx_create
      - pptx_read
      - pptx_add_slide
      - pptx_modify_slide
```

Subagents run tasks in isolated contexts, preventing context saturation. Include `subagent` in `main_agent.tools` to enable calling subagents.

## System Requirements

For `pptx_export_image`:
```bash
# macOS
brew install --cask libreoffice
brew install poppler
```
