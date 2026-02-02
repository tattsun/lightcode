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
