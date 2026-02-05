"""Configuration file loading and management."""

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class SubagentConfig:
    """Configuration for a subagent type."""

    name: str
    description: str
    tools: list[str]


@dataclass
class LightcodeConfig:
    """Full configuration for lightcode."""

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
    # main_tools: override if specified
    main_tools = override.main_tools if override.main_tools is not None else base.main_tools

    # subagents: merge dictionaries, override takes precedence
    subagents = dict(base.subagents)
    subagents.update(override.subagents)

    return LightcodeConfig(main_tools=main_tools, subagents=subagents)


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

    return LightcodeConfig(main_tools=main_tools, subagents=subagents)
