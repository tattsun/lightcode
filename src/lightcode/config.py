"""Configuration file loading and management."""

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class ModelConfig:
    """Configuration for LLM model."""

    name: str = "openai/gpt-5.2"
    api_base: str | None = None
    api_key: str | None = None
    max_input_tokens: int | None = None


@dataclass
class SubagentConfig:
    """Configuration for a subagent type."""

    name: str
    description: str
    tools: list[str]


@dataclass
class LightcodeConfig:
    """Full configuration for lightcode."""

    model: ModelConfig = field(default_factory=ModelConfig)
    subagent_model: ModelConfig | None = None
    main_tools: list[str] | None = None  # None means use ALL_TOOLS (default)
    subagents: dict[str, SubagentConfig] = field(default_factory=dict)


def load_config() -> LightcodeConfig:
    """Load and merge global + local config files.

    Global config: ~/.lightcode/config.yaml
    Local config: ./lightcode.yaml

    Local config overrides global config.

    Returns:
        LightcodeConfig with merged settings.
    """
    config = LightcodeConfig()

    # 1. Load global config
    global_config_path = Path.home() / ".lightcode" / "config.yaml"
    if global_config_path.exists():
        global_cfg = _load_config_from_file(global_config_path)
        config = _merge_configs(config, global_cfg)

    # 2. Load local config (overrides global)
    local_config_path = Path.cwd() / "lightcode.yaml"
    if local_config_path.exists():
        local_cfg = _load_config_from_file(local_config_path)
        config = _merge_configs(config, local_cfg)

    return config


def _merge_configs(base: LightcodeConfig, override: LightcodeConfig) -> LightcodeConfig:
    """Merge two configs, with override taking precedence.

    Args:
        base: Base configuration.
        override: Configuration to override with.

    Returns:
        Merged configuration.
    """
    # model: override if specified (check if it's non-default)
    model = override.model if override.model.name != ModelConfig().name else base.model

    # subagent_model: override if specified
    subagent_model = override.subagent_model if override.subagent_model is not None else base.subagent_model

    # main_tools: override if specified
    main_tools = override.main_tools if override.main_tools is not None else base.main_tools

    # subagents: merge dictionaries, override takes precedence
    subagents = dict(base.subagents)
    subagents.update(override.subagents)

    return LightcodeConfig(
        model=model,
        subagent_model=subagent_model,
        main_tools=main_tools,
        subagents=subagents,
    )


def _parse_model_config(data: dict | None) -> ModelConfig:
    """Parse model configuration from YAML data.

    Args:
        data: Dictionary with model configuration.

    Returns:
        ModelConfig parsed from the data.
    """
    if not data or not isinstance(data, dict):
        return ModelConfig()

    name = data.get("name", ModelConfig().name)
    api_base = data.get("api_base")
    api_key = data.get("api_key")
    max_input_tokens = data.get("max_input_tokens")

    return ModelConfig(
        name=name,
        api_base=api_base,
        api_key=api_key,
        max_input_tokens=max_input_tokens,
    )


def _load_config_from_file(path: Path) -> LightcodeConfig:
    """Load configuration from a YAML file.

    Args:
        path: Path to the YAML config file.

    Returns:
        LightcodeConfig parsed from the file.
    """
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except Exception:
        return LightcodeConfig()

    if not data or not isinstance(data, dict):
        return LightcodeConfig()

    # Parse model section
    model = _parse_model_config(data.get("model"))

    # Parse subagent_model section (optional)
    subagent_model_data = data.get("subagent_model")
    subagent_model = _parse_model_config(subagent_model_data) if subagent_model_data else None

    # Parse main_agent section
    main_tools: list[str] | None = None
    main_agent_data = data.get("main_agent", {})
    if isinstance(main_agent_data, dict):
        tools = main_agent_data.get("tools", None)
        if isinstance(tools, list):
            main_tools = [t for t in tools if isinstance(t, str)]

    # Parse subagents section
    subagents: dict[str, SubagentConfig] = {}
    subagents_data = data.get("subagents", {})
    if isinstance(subagents_data, dict):
        for name, config in subagents_data.items():
            if not isinstance(config, dict):
                continue

            description = config.get("description", "")
            tools = config.get("tools", [])

            if not isinstance(tools, list):
                tools = []

            # Filter to only string tool names
            tools = [t for t in tools if isinstance(t, str)]

            subagents[name] = SubagentConfig(
                name=name,
                description=description,
                tools=tools,
            )

    return LightcodeConfig(
        model=model,
        subagent_model=subagent_model,
        main_tools=main_tools,
        subagents=subagents,
    )


def get_effective_model_config(config: LightcodeConfig) -> ModelConfig:
    """Get effective model config with environment variable overrides.

    Environment variables (override YAML):
    - LIGHTCODE_MODEL: Model name
    - LIGHTCODE_API_BASE: Custom API base URL
    - LIGHTCODE_API_KEY: API key ('none' to disable)

    Args:
        config: Loaded configuration.

    Returns:
        ModelConfig with environment variable overrides applied.
    """
    # Start with config values
    name = config.model.name
    api_base = config.model.api_base
    api_key = config.model.api_key
    max_input_tokens = config.model.max_input_tokens

    # Override with environment variables
    if env_model := os.environ.get("LIGHTCODE_MODEL"):
        name = env_model

    if env_api_base := os.environ.get("LIGHTCODE_API_BASE"):
        api_base = env_api_base

    env_api_key = os.environ.get("LIGHTCODE_API_KEY")
    if env_api_key is not None:
        # 'none' means no API key
        api_key = None if env_api_key.lower() == "none" else env_api_key

    return ModelConfig(
        name=name,
        api_base=api_base,
        api_key=api_key,
        max_input_tokens=max_input_tokens,
    )


def should_use_completion_api(model: str) -> bool:
    """Check if a model requires Completion API (Responses API unsupported).

    Local models like Ollama and vLLM don't support Responses API.

    Args:
        model: Model name in LiteLLM format.

    Returns:
        True if Completion API should be used.
    """
    local_prefixes = ("ollama/", "ollama_chat/", "hosted_vllm/")
    return model.lower().startswith(local_prefixes)
