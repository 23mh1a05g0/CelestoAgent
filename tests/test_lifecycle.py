"""Unit tests for sandbox lifecycle operations."""
import pytest
from app.services.celesto_service import celesto_service, SimulatedComputer
from app.tools.shell_tool import ShellTool
from app.tools.file_tool import FileTool


def test_simulated_computer_lifecycle():
    computer = celesto_service.create_sandbox(template_id="coding-agent", force_simulator=True)
    assert computer is not None
    assert computer.status == "ready"
    assert computer.name.startswith("sim-sbx-")
    assert hasattr(computer, "boot_to_ready_s")

    # Command execution
    shell = ShellTool(computer)
    res = shell.execute("uname -a")
    assert res.exit_code == 0
    assert "Linux" in res.stdout
    assert res.blocked is False

    # Blocked command inside shell tool
    res_blocked = shell.execute("rm -rf /")
    assert res_blocked.blocked is True
    assert res_blocked.exit_code == 126

    # Deletion
    deleted = celesto_service.delete_sandbox(computer.name)
    assert deleted is True
    assert computer.status == "deleted"


def test_file_tool_operations():
    computer = celesto_service.create_sandbox(force_simulator=True)
    shell = ShellTool(computer)
    file_tool = FileTool(shell)

    # List dir
    list_res = file_tool.list_dir(".")
    assert list_res["success"] is True

    celesto_service.delete_sandbox(computer.name)
