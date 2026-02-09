"""Subagent tool for running tasks in isolated contexts."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from lightcode.config import SubagentConfig
from lightcode.tools.base import Tool

if TYPE_CHECKING:
    from lightcode.interrupt import InterruptHandler


# Default max turns for subagent execution
DEFAULT_MAX_TURNS = 20


class SubAgentTool(Tool):
    """Tool for running subagents with isolated contexts."""

    def __init__(
        self,
        model: str,
        api_base: str | None,
        api_key: str | None,
        max_input_tokens: int | None,
        all_tools: dict[str, Tool],
        subagent_configs: dict[str, SubagentConfig],
        api_mode: str = "responses",
        reasoning_effort: str = "medium",
    ):
        """Initialize the subagent tool.

        Args:
            model: Model to use for subagents.
            api_base: Custom API base URL (optional).
            api_key: API key (optional).
            max_input_tokens: Maximum input tokens (optional).
            all_tools: Dictionary of all available tools by name.
            subagent_configs: Dictionary of subagent configurations by type name.
            api_mode: API mode ('completion' or 'responses').
            reasoning_effort: Reasoning effort level for Responses API.
        """
        self._model = model
        self._api_base = api_base
        self._api_key = api_key
        self._max_input_tokens = max_input_tokens
        self._all_tools = all_tools
        self._subagent_configs = subagent_configs
        self._api_mode = api_mode
        self._reasoning_effort = reasoning_effort

    @property
    def name(self) -> str:
        return "subagent"

    @property
    def description(self) -> str:
        # Build description with available types
        type_info = []
        for name, config in self._subagent_configs.items():
            type_info.append(f"- {name}: {config.description}")

        types_str = "\n".join(type_info) if type_info else "No subagent types configured."

        return f"""\
Run a task in an isolated subagent with its own context.
Useful for complex tasks that would consume too much context.
The subagent runs independently and returns only the final result.

Available subagent types:
{types_str}
"""

    @property
    def parameters(self) -> dict:
        # Get available type names for enum
        type_names = list(self._subagent_configs.keys())

        return {
            "type": {
                "type": "string",
                "description": "The subagent type to use.",
                "enum": type_names if type_names else ["none"],
                "required": True,
            },
            "task": {
                "type": "string",
                "description": "Description of the task for the subagent to complete.",
                "required": True,
            },
            "context": {
                "type": "string",
                "description": "Additional context to provide to the subagent (optional).",
                "required": False,
            },
            "max_turns": {
                "type": "integer",
                "description": f"Maximum number of turns before stopping (default: {DEFAULT_MAX_TURNS}).",
                "required": False,
            },
        }

    def execute(
        self,
        type: str,
        task: str,
        context: str = "",
        max_turns: int | None = None,
        _interrupt_handler: InterruptHandler | None = None,
        **kwargs,
    ) -> str:
        """Execute a task using a subagent.

        Args:
            type: Subagent type name.
            task: Task description.
            context: Additional context (optional).
            max_turns: Maximum turns (optional).
            _interrupt_handler: Interrupt handler (optional).

        Returns:
            Result from the subagent.
        """
        # Import here to avoid circular import
        from lightcode.subagent import run_subagent

        # Validate type
        if type not in self._subagent_configs:
            available = ", ".join(self._subagent_configs.keys())
            return f"Error: Unknown subagent type '{type}'. Available types: {available}"

        config = self._subagent_configs[type]

        # Build tool list for this subagent type
        # Note: We exclude 'subagent' tool to prevent recursive calls
        tools: list[Tool] = []
        for tool_name in config.tools:
            if tool_name == "subagent":
                continue  # Prevent recursion
            if tool_name in self._all_tools:
                tools.append(self._all_tools[tool_name])

        if not tools:
            return f"Error: No valid tools configured for subagent type '{type}'."

        # Run the subagent
        if max_turns is None:
            max_turns = DEFAULT_MAX_TURNS

        try:
            result = run_subagent(
                subagent_type=type,
                task=task,
                context=context,
                description=config.description,
                model=self._model,
                api_base=self._api_base,
                api_key=self._api_key,
                max_input_tokens=self._max_input_tokens,
                tools=tools,
                api_mode=self._api_mode,
                reasoning_effort=self._reasoning_effort,
                max_turns=max_turns,
                interrupt_handler=_interrupt_handler,
            )
            return result
        except Exception as e:
            # Re-raise InterruptRequested to allow proper interrupt handling
            from lightcode.interrupt import InterruptRequested
            if isinstance(e, InterruptRequested):
                raise
            return f"Error running subagent: {type(e).__name__}: {e}"
