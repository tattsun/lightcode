"""ファイル編集ツール（検索＆置換方式）"""

from lightcode.tools.base import Tool


class EditFileTool(Tool):
    """ファイル内の文字列を検索して置換するツール"""

    @property
    def name(self) -> str:
        return "edit_file"

    @property
    def description(self) -> str:
        return "ファイル内の指定した文字列を検索し、新しい文字列で置換する。old_stringは一意である必要がある。"

    @property
    def parameters(self) -> dict:
        return {
            "path": {
                "type": "string",
                "description": "編集するファイルのパス",
            },
            "old_string": {
                "type": "string",
                "description": "置換対象の文字列（一意にマッチする必要がある）",
            },
            "new_string": {
                "type": "string",
                "description": "置換後の文字列",
            },
        }

    def execute(self, **kwargs) -> str:
        path = kwargs.get("path")
        old_string = kwargs.get("old_string")
        new_string = kwargs.get("new_string")

        if not path:
            return "Error: path is required"
        if old_string is None:
            return "Error: old_string is required"
        if new_string is None:
            return "Error: new_string is required"

        try:
            with open(path, encoding="utf-8") as f:
                content = f.read()

            # マッチ数をカウント
            count = content.count(old_string)

            if count == 0:
                return f"Error: old_string not found in {path}"
            if count > 1:
                return f"Error: old_string matches {count} times. Please provide more context to make it unique."

            # 置換を実行
            new_content = content.replace(old_string, new_string, 1)

            with open(path, "w", encoding="utf-8") as f:
                f.write(new_content)

            # 変更の統計
            old_lines = old_string.count("\n") + 1
            new_lines = new_string.count("\n") + 1
            return f"Successfully edited {path}: replaced {old_lines} lines with {new_lines} lines"

        except FileNotFoundError:
            return f"Error: File not found: {path}"
        except PermissionError:
            return f"Error: Permission denied: {path}"
        except IsADirectoryError:
            return f"Error: Is a directory: {path}"
        except UnicodeDecodeError:
            return f"Error: Cannot decode file (binary?): {path}"
