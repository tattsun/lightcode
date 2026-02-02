"""Base class for tools."""

from abc import ABC, abstractmethod


class Tool(ABC):
    """Base class for tools."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description."""
        ...

    @property
    @abstractmethod
    def parameters(self) -> dict:
        """JSON Schema for parameters."""
        ...

    @abstractmethod
    def execute(self, **kwargs) -> str:
        """Execute the tool."""
        ...

    def to_schema(self) -> dict:
        """Generate tool schema for LLM."""
        # Create properties without the "required" key
        properties = {
            k: {pk: pv for pk, pv in v.items() if pk != "required"}
            for k, v in self.parameters.items()
        }
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": [
                        k for k, v in self.parameters.items() if v.get("required")
                    ],
                },
            },
        }
