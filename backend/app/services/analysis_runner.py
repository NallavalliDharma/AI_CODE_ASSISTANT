"""Static analysis tool runners."""

import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from app.models.analysis import FindingSeverity, ToolType


@dataclass
class ToolFinding:
    severity: FindingSeverity
    category: str
    file_path: str | None
    line_number: int | None
    column_number: int | None
    message: str
    rule_id: str | None = None


@dataclass
class ToolRunResult:
    tool_name: str
    tool_type: ToolType
    status: str
    output: str
    findings: list[ToolFinding] = field(default_factory=list)


def _run_command(cmd: list[str], cwd: str | None = None, timeout: int = 120) -> tuple[int, str, str]:
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=cwd, timeout=timeout, check=False
        )
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return -1, "", f"Command not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"


def run_ruff(target_path: str) -> ToolRunResult:
    cmd = ["ruff", "check", "--output-format", "json", target_path]
    code, stdout, stderr = _run_command(cmd)
    findings: list[ToolFinding] = []
    if stdout.strip():
        try:
            for item in json.loads(stdout):
                findings.append(
                    ToolFinding(
                        severity=FindingSeverity.MEDIUM,
                        category="lint",
                        file_path=item.get("filename"),
                        line_number=item.get("location", {}).get("row"),
                        column_number=item.get("location", {}).get("column"),
                        message=item.get("message", ""),
                        rule_id=item.get("code"),
                    )
                )
        except json.JSONDecodeError:
            pass
    return ToolRunResult(
        tool_name="ruff",
        tool_type=ToolType.LINTER,
        status="completed" if code == 0 else "issues_found",
        output=stdout or stderr,
        findings=findings,
    )


def run_bandit(target_path: str) -> ToolRunResult:
    cmd = ["bandit", "-r", target_path, "-f", "json", "-q"]
    code, stdout, stderr = _run_command(cmd)
    findings: list[ToolFinding] = []
    if stdout.strip():
        try:
            data = json.loads(stdout)
            for item in data.get("results", []):
                sev_map = {
                    "HIGH": FindingSeverity.HIGH,
                    "MEDIUM": FindingSeverity.MEDIUM,
                    "LOW": FindingSeverity.LOW,
                }
                findings.append(
                    ToolFinding(
                        severity=sev_map.get(item.get("issue_severity", "LOW"), FindingSeverity.LOW),
                        category="security",
                        file_path=item.get("filename"),
                        line_number=item.get("line_number"),
                        column_number=item.get("col_offset"),
                        message=item.get("issue_text", ""),
                        rule_id=item.get("test_id"),
                    )
                )
        except json.JSONDecodeError:
            pass
    return ToolRunResult(
        tool_name="bandit",
        tool_type=ToolType.SECURITY,
        status="completed" if code == 0 else "issues_found",
        output=stdout or stderr,
        findings=findings,
    )


def run_eslint(target_path: str) -> ToolRunResult:
    if not shutil.which("eslint"):
        return ToolRunResult(
            tool_name="eslint",
            tool_type=ToolType.LINTER,
            status="skipped",
            output="eslint not installed",
            findings=[],
        )
    cmd = ["eslint", "--format", "json", target_path]
    code, stdout, stderr = _run_command(cmd)
    findings: list[ToolFinding] = []
    if stdout.strip():
        try:
            for file_result in json.loads(stdout):
                for msg in file_result.get("messages", []):
                    sev = FindingSeverity.HIGH if msg.get("severity") == 2 else FindingSeverity.MEDIUM
                    findings.append(
                        ToolFinding(
                            severity=sev,
                            category="lint",
                            file_path=file_result.get("filePath"),
                            line_number=msg.get("line"),
                            column_number=msg.get("column"),
                            message=msg.get("message", ""),
                            rule_id=msg.get("ruleId"),
                        )
                    )
        except json.JSONDecodeError:
            pass
    return ToolRunResult(
        tool_name="eslint",
        tool_type=ToolType.LINTER,
        status="completed" if code == 0 else "issues_found",
        output=stdout or stderr,
        findings=findings,
    )


def run_pip_audit(requirements_path: str) -> ToolRunResult:
    cmd = ["pip-audit", "-r", requirements_path, "--format", "json"]
    code, stdout, stderr = _run_command(cmd)
    findings: list[ToolFinding] = []
    if stdout.strip():
        try:
            data = json.loads(stdout)
            for item in data.get("dependencies", []):
                for vuln in item.get("vulns", []):
                    findings.append(
                        ToolFinding(
                            severity=FindingSeverity.HIGH,
                            category="dependency",
                            file_path=requirements_path,
                            line_number=None,
                            column_number=None,
                            message=f"{item.get('name')}: {vuln.get('id', 'unknown vulnerability')}",
                            rule_id=vuln.get("id"),
                        )
                    )
        except json.JSONDecodeError:
            pass
    return ToolRunResult(
        tool_name="pip-audit",
        tool_type=ToolType.DEPENDENCY,
        status="completed" if code == 0 else "issues_found",
        output=stdout or stderr,
        findings=findings,
    )


def run_npm_audit(package_dir: str) -> ToolRunResult:
    if not shutil.which("npm"):
        return ToolRunResult(
            tool_name="npm-audit",
            tool_type=ToolType.DEPENDENCY,
            status="skipped",
            output="npm not installed",
            findings=[],
        )
    if not os.path.exists(os.path.join(package_dir, "package.json")):
        return ToolRunResult(
            tool_name="npm-audit",
            tool_type=ToolType.DEPENDENCY,
            status="skipped",
            output="No package.json found",
            findings=[],
        )
    cmd = ["npm", "audit", "--json"]
    code, stdout, stderr = _run_command(cmd, cwd=package_dir)
    findings: list[ToolFinding] = []
    if stdout.strip():
        try:
            data = json.loads(stdout)
            for name, advisory in data.get("vulnerabilities", {}).items():
                findings.append(
                    ToolFinding(
                        severity=FindingSeverity.HIGH,
                        category="dependency",
                        file_path="package.json",
                        line_number=None,
                        column_number=None,
                        message=f"{name}: {advisory.get('via', ['unknown'])[0] if advisory.get('via') else 'vulnerability'}",
                        rule_id=name,
                    )
                )
        except (json.JSONDecodeError, IndexError, TypeError):
            pass
    return ToolRunResult(
        tool_name="npm-audit",
        tool_type=ToolType.DEPENDENCY,
        status="completed" if code == 0 else "issues_found",
        output=stdout or stderr,
        findings=findings,
    )


def discover_tests(target_path: str) -> ToolRunResult:
    """Discover test files in the target directory."""
    test_files: list[str] = []
    target = Path(target_path)
    patterns = ["test_*.py", "*_test.py", "*.test.js", "*.spec.js", "*.test.ts", "*.spec.ts"]
    for pattern in patterns:
        test_files.extend(str(p) for p in target.rglob(pattern))

    findings = [
        ToolFinding(
            severity=FindingSeverity.INFO,
            category="test_discovery",
            file_path=f,
            line_number=None,
            column_number=None,
            message=f"Discovered test file: {f}",
        )
        for f in test_files[:50]
    ]
    return ToolRunResult(
        tool_name="test-discovery",
        tool_type=ToolType.TEST,
        status="completed",
        output=json.dumps({"test_files": test_files, "count": len(test_files)}),
        findings=findings,
    )


def prepare_analysis_workspace(repo_path: str, diff_content: str | None = None) -> str:
    """Create a temp workspace, optionally applying a patch."""
    workspace = tempfile.mkdtemp(prefix="cra_analysis_")
    if os.path.isdir(repo_path):
        for item in os.listdir(repo_path):
            src = os.path.join(repo_path, item)
            dst = os.path.join(workspace, item)
            if os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)
    if diff_content:
        patch_file = os.path.join(workspace, "uploaded.patch")
        with open(patch_file, "w", encoding="utf-8") as f:
            f.write(diff_content)
    return workspace


def run_all_analyzers(target_path: str) -> list[ToolRunResult]:
    """Run all available static analysis tools on a target path."""
    results = [
        run_ruff(target_path),
        run_bandit(target_path),
        run_eslint(target_path),
        discover_tests(target_path),
    ]
    req_path = os.path.join(target_path, "requirements.txt")
    if os.path.exists(req_path):
        results.append(run_pip_audit(req_path))
    if os.path.exists(os.path.join(target_path, "package.json")):
        results.append(run_npm_audit(target_path))
    return results
