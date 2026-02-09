# lightcode

A simple coding agent with tool calling support.

## Warning

With `--no-permissions`, this agent may automatically execute commands, modify files, and make network requests. Use in a sandboxed environment is recommended.

## Quick Start

```bash
rye sync
export OPENAI_API_KEY=sk-xxxxx
make run
```

## Command Line Options

| Option | Description |
|--------|-------------|
| `--no-permissions` | Skip tool permission prompts |
| `--web-search` | Enable web search (requires `TAVILY_API_KEY`) |
| `--log-file <path>` | Save session log to JSONL file |
| `--api <mode>` | `completion` or `responses` (default: `responses`) |
| `--reasoning-effort <level>` | `low`, `medium` (default), or `high` (Responses API only) |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | OpenAI API key |
| `TAVILY_API_KEY` | Tavily API key (for `--web-search`) |
| `LIGHTCODE_MODEL` | Model name (overrides config file) |
| `LIGHTCODE_API_BASE` | Custom API base URL |
| `LIGHTCODE_API_KEY` | API key (`none` to disable) |

## Configuration File

Config files: `~/.lightcode/config.yaml` (global) or `./lightcode.yaml` (local, takes priority).

```yaml
# Model settings
model:
  name: "openai/gpt-4o"          # LiteLLM format
  api_base: null                  # Custom endpoint (optional)
  api_key: null                   # API key (optional)
  max_input_tokens: 128000        # Token limit (optional)

# Separate model for subagents (optional)
subagent_model:
  name: "openai/gpt-4o-mini"

# Restrict main agent tools (optional, defaults to all)
main_agent:
  tools: [read_file, write_file, run_command, subagent]

# Define subagent types (optional)
subagents:
  researcher:
    description: "Research and analyze code"
    tools: [read_file, grep, find_files]
```

### Local LLM Examples

**Ollama:**
```yaml
model:
  name: "ollama_chat/llama3.1"    # Use ollama_chat/ for tool support
  api_base: "http://localhost:11434"
  max_input_tokens: 131072        # Sets num_ctx (Ollama default is only 8192)
```

**vLLM:**
```yaml
model:
  name: "hosted_vllm/meta-llama/Llama-3.1-70B-Instruct"
  api_base: "http://localhost:8000/v1"
  api_key: "EMPTY"
```

Note: Local models (Ollama/vLLM) automatically use Completion API.

## Available Tools

| Category | Tools |
|----------|-------|
| File | `read_file`, `write_file`, `edit_file`, `delete_file`, `move_file`, `copy_file` |
| Search | `grep`, `find_files`, `list_files`, `file_info` |
| Media | `read_image` |
| System | `run_command` |
| PowerPoint | `pptx_create`, `pptx_read`, `pptx_add_slide`, `pptx_modify_slide`, `pptx_export_image`, `pptx_duplicate_slide`, `pptx_find_text`, `pptx_layout` |
| Optional | `web_search`, `web_fetch` (with `--web-search`), `subagent` (with config) |

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Ctrl-C` / `Esc` | Interrupt current operation |
| `Ctrl-V` | Paste image from clipboard |

## System Requirements

For `pptx_export_image` (macOS):
```bash
brew install --cask libreoffice
brew install poppler
```
