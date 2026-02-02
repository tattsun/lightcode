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
        # propertiesから "required" キーを除去したものを作成
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
