"""Bounded stackctl invocations for known Assist projects."""

import json
import os
from pathlib import Path
import re
import shutil
import subprocess

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib


WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
SERVICE_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*\Z")


class StackctlError(Exception):
    def __init__(self, message, status_code=502):
        super().__init__(message)
        self.status_code = status_code


def workspace_root(config):
    return Path(config.get("storage", {}).get("workspace_root") or WORKSPACE_ROOT).resolve()


def read_discovery_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default
    except (OSError, ValueError) as exc:
        raise StackctlError(f"Cannot read project discovery {path}: {exc}", 503) from exc


def has_stackctl(root):
    path = root / "pyproject.toml"
    try:
        project = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return False
    except (OSError, ValueError) as exc:
        raise StackctlError(f"Cannot read project configuration {path}: {exc}", 503) from exc
    tools = project.get("tool", {})
    if not isinstance(tools, dict):
        raise StackctlError(f"Invalid tool configuration in {path}", 503)
    tool = tools.get("stackctl")
    if tool is not None and not isinstance(tool, dict):
        raise StackctlError(f"Invalid [tool.stackctl] configuration in {path}", 503)
    return tool is not None


def known_projects(config):
    """Reuse project metadata/recent cache; never treat an HTTP path as registration."""
    workspace = workspace_root(config)
    roots = {}
    state_home = Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local" / "state")
    discovery_path = state_home / "stackctl" / "projects.json"
    entries = read_discovery_json(discovery_path, [])
    if not isinstance(entries, list) or any(
        not isinstance(entry, dict)
        or set(entry) != {"name", "root"}
        or any(not isinstance(value, str) or not value for value in entry.values())
        or not Path(entry["root"]).is_absolute()
        for entry in entries
    ):
        raise StackctlError(f"Invalid project discovery registry: {discovery_path}", 503)
    for entry in entries:
        root = Path(entry["root"]).expanduser().resolve()
        if root.is_dir():
            roots[str(root)] = {"name": entry["name"], "path": str(root)}
    configured = config.get("storage", {}).get("project_root")
    if configured:
        root = Path(configured).expanduser().resolve()
        if root.is_dir():
            roots[str(root)] = {"name": root.name, "path": str(root)}
    recent_path = workspace / ".kicli_recent_projects"
    candidates = read_discovery_json(recent_path, [])
    if not isinstance(candidates, list) or any(not isinstance(item, dict) for item in candidates):
        raise StackctlError(f"Invalid recent project discovery: {recent_path}", 503)
    for marker in workspace.glob("*/.kicli_project"):
        metadata = read_discovery_json(marker, {})
        if not isinstance(metadata, dict):
            raise StackctlError(f"Invalid project metadata: {marker}", 503)
        candidates.append({**metadata, "path": str(marker.parent)})
    for item in candidates:
        path = item.get("path")
        if not isinstance(path, str) or not path:
            continue
        root = Path(path).expanduser().resolve()
        if root.is_dir() and root.is_relative_to(workspace):
            roots[str(root)] = {
                "name": item.get("name") or root.name,
                "path": str(root),
            }
    return [project for project in roots.values() if has_stackctl(Path(project["path"]))]


class StackctlBridge:
    def __init__(self, config):
        self.config = config

    def project(self, selector):
        if not isinstance(selector, str) or not selector:
            raise StackctlError("A known project path is required", 400)
        # Compare with server-discovered roots, not arbitrary client paths.
        for project in known_projects(self.config):
            if selector == project["path"]:
                return Path(project["path"])
        raise StackctlError("Unknown project; open a registered workspace project first", 403)

    def command(self, root):
        central = Path.home() / ".local" / "bin" / "stackctl"
        if central.is_file() and os.access(central, os.X_OK):
            return [str(central)]
        executable = shutil.which("stackctl")
        if executable:
            return [executable]
        raise StackctlError("Central stackctl executable missing: install it in ~/.local/bin or PATH", 503)

    def invoke(self, root, action, services=(), json_output=False):
        if action not in {"status", "logs", "start", "stop", "restart"}:
            raise StackctlError("Unsupported stackctl action", 400)
        args = self.command(root)
        if json_output:
            args.append("--json")
        args.extend([action, *services])
        try:
            result = subprocess.run(
                args, cwd=str(root), capture_output=True, text=True,
                timeout=15 if action in {"status", "logs"} else 90,
                stdin=subprocess.DEVNULL,
            )
        except subprocess.TimeoutExpired as exc:
            raise StackctlError(
                "stackctl timed out; refresh status before retrying (the operation may still finish)", 504
            ) from exc
        except OSError as exc:
            raise StackctlError(f"Unable to execute project stackctl: {exc}", 503) from exc
        if result.returncode:
            detail = (result.stderr or result.stdout).strip()[-4000:]
            raise StackctlError(f"stackctl {action} failed ({result.returncode}): {detail}")
        if not json_output:
            return {"output": result.stdout[-16000:]}
        try:
            payload = json.loads(result.stdout)
        except ValueError as exc:
            raise StackctlError(f"stackctl {action} returned invalid JSON") from exc
        if not isinstance(payload, dict):
            raise StackctlError(f"stackctl {action} returned an invalid object")
        return payload

    def status(self, root):
        payload = self.invoke(root, "status", json_output=True)
        services = payload.get("services")
        if (
            payload.get("root") != str(root)
            or not isinstance(payload.get("project"), str)
            or not isinstance(payload.get("target"), str)
            or not isinstance(services, list)
            or any(
                not isinstance(service, dict)
                or not isinstance(service.get("name"), str)
                or not SERVICE_NAME.fullmatch(service["name"])
                or service.get("status") not in {"running", "unhealthy", "stopped", "foreign"}
                for service in services
            )
        ):
            raise StackctlError("stackctl status returned an invalid project/services object")
        if payload["target"] != "local":
            raise StackctlError(
                f"Assist server management supports local targets only; project target is {payload['target']}", 400
            )
        return payload

    def services(self, root, requested):
        if not isinstance(requested, list) or any(
            not isinstance(name, str) or not SERVICE_NAME.fullmatch(name)
            for name in requested
        ):
            raise StackctlError("services must be a list of service names (not options or commands)", 400)
        available = {service["name"] for service in self.status(root)["services"]}
        unknown = set(requested) - available
        if unknown:
            raise StackctlError(f"Unknown services: {', '.join(sorted(unknown))}", 400)
        return requested


def register_stackctl_routes(app):
    from flask import jsonify, request

    def bridge():
        return StackctlBridge(app.config.get("KICLI_CONFIG", {}))

    @app.errorhandler(StackctlError)
    def stackctl_error(error):
        return jsonify(success=False, error=str(error)), error.status_code

    @app.get("/api/server/projects")
    def server_projects():
        return jsonify(success=True, projects=known_projects(app.config.get("KICLI_CONFIG", {})))

    @app.get("/api/server/status")
    def server_status():
        manager = bridge()
        selector = request.args.get("project")
        if selector:
            payload = manager.status(manager.project(selector))
            return jsonify(success=True, manager="stackctl", **payload)
        projects, services, errors = [], [], []
        for project in known_projects(manager.config):
            try:
                payload = manager.status(Path(project["path"]))
                projects.append(payload)
                services.extend({**service, "project": payload["project"], "root": payload["root"]}
                                for service in payload["services"])
            except StackctlError as exc:
                errors.append({"root": project["path"], "error": str(exc)})
        counts = {state: sum(item["status"] == state for item in services)
                  for state in ("running", "unhealthy", "stopped", "foreign")}
        return jsonify(success=not errors, manager="stackctl", projects=projects,
                       services=services, errors=errors, counts={**counts, "total": len(services)}), (
                           502 if errors else 200)

    @app.get("/api/server/logs")
    def server_logs():
        manager = bridge()
        root = manager.project(request.args.get("project"))
        services = manager.services(root, request.args.getlist("service"))
        return jsonify(success=True, manager="stackctl",
                       **manager.invoke(root, "logs", services, json_output=True))

    def lifecycle(action):
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            raise StackctlError("A JSON object is required", 400)
        if set(data) - {"project", "services"}:
            raise StackctlError("Only project and services are accepted", 400)
        manager = bridge()
        root = manager.project(data.get("project"))
        services = manager.services(root, data.get("services", []))
        return jsonify(success=True, manager="stackctl",
                       **manager.invoke(root, action, services))

    for action in ("start", "stop", "restart"):
        app.add_url_rule(f"/api/server/{action}", f"stackctl_{action}",
                         lambda action=action: lifecycle(action), methods=["POST"])
