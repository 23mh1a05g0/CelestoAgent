"""File tool for reading and writing files inside a sandbox."""
import base64
from typing import Optional, Dict, Any
from app.tools.shell_tool import ShellTool


class FileTool:
    """Manipulates files inside the sandbox via shell commands."""

    def __init__(self, shell_tool: ShellTool):
        self.shell_tool = shell_tool

    def read_file(self, path: str) -> Dict[str, Any]:
        """Read content of a file in the sandbox."""
        cmd = f"cat '{path}'"
        res = self.shell_tool.execute(cmd)
        if res.exit_code == 0 and not res.blocked:
            return {"success": True, "content": res.stdout, "error": None}
        return {"success": False, "content": None, "error": res.stderr}

    def write_file(self, path: str, content: str) -> Dict[str, Any]:
        """Write text content to a file in the sandbox using base64 encoding for safety."""
        b64 = base64.b64encode(content.encode("utf-8")).decode("ascii")
        cmd = f"echo '{b64}' | base64 -d > '{path}'"
        res = self.shell_tool.execute(cmd)
        if res.exit_code == 0 and not res.blocked:
            return {"success": True, "error": None}
        return {"success": False, "error": res.stderr}

    def list_dir(self, path: str = ".") -> Dict[str, Any]:
        """List files in directory."""
        cmd = f"ls -la '{path}'"
        res = self.shell_tool.execute(cmd)
        if res.exit_code == 0 and not res.blocked:
            return {"success": True, "output": res.stdout, "error": None}
        return {"success": False, "output": None, "error": res.stderr}
