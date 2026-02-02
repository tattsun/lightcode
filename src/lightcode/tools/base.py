"""ツールの基底クラス"""

from abc import ABC, abstractmethod


class Tool(ABC):
    """ツールの基底クラス"""

    @property
    @abstractmethod
    def name(self) -> str:
        """ツール名"""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """ツールの説明"""
        ...

    @property
    @abstractmethod
    def parameters(self) -> dict:
        """パラメータのJSON Schema"""
        ...

    @abstractmethod
    def execute(self, **kwargs) -> str:
        """ツールを実行"""
        ...

    def to_schema(self) -> dict:
        """LLM用のツールスキーマを生成"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": self.parameters,
                    "required": [
                        k for k, v in self.parameters.items() if v.get("required")
                    ],
                },
            },
        }
