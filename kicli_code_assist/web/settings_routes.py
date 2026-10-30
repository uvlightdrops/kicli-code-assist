"""Runtime settings API: ``GET/POST /api/settings`` and ``/api/settings/secrets``.

The Flask server has no user accounts, so configuration writes are bound to
the local machine and the served UI:

* client address must be loopback (``KICLI_SETTINGS_ALLOW_REMOTE`` opts out),
* ``Host`` must be a loopback name, the configured ``web.host`` or a host of
  ``web.cors_origins`` (DNS-rebinding protection),
* a present ``Origin``/``Referer`` must be one of ``web.cors_origins`` or the
  server's own origin,
* ``POST`` additionally needs ``X-Kicli-Settings-Token`` (per-process random
  token handed out by ``GET`` to same-origin/allowed-origin callers only) and
  a JSON body with exactly ``revision``/``changes``/``remove``.

``/api/settings/secrets`` is write-only: ``GET`` lists credential paths with a
``configured`` flag and the creds.yaml revision, ``POST`` takes
``{revision, path, value}`` or ``{revision, path, remove: true}`` and returns
the same value-free inventory.

Error messages come from ki-core's safe exception texts; values are never
echoed back except through the masked snapshot.
"""

from __future__ import annotations

import hmac
import ipaddress
import logging
import secrets
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlsplit

from flask import Flask, jsonify, request

from kicli_code_assist import runtime_config
from kicli_code_assist.runtime_config import ConflictError, EditorError, ValidationError

logger = logging.getLogger("kicli-web-settings")

TOKEN_HEADER = "X-Kicli-Settings-Token"
MAX_BODY = 64 * 1024
MAX_ITEMS = 200
MAX_REVISION = 128
MAX_PATH = 200
MAX_SECRET_BODY = 16 * 1024
MAX_SECRET_VALUE = 8192
_LOOPBACK_NAMES = {"localhost", "127.0.0.1", "::1"}


def _host_of(value: str) -> Optional[str]:
    try:
        parts = urlsplit(value if "://" in value else f"//{value}")
        return (parts.hostname or "").lower() or None
    except ValueError:
        return None


def _origin_of(value: str) -> Optional[str]:
    try:
        parts = urlsplit(value)
    except ValueError:
        return None
    if parts.scheme not in ("http", "https") or not parts.netloc:
        return None
    return f"{parts.scheme}://{parts.netloc}".lower()


def _is_loopback(addr: Optional[str]) -> bool:
    if not addr:
        return False
    try:
        return ipaddress.ip_address(addr.split("%", 1)[0]).is_loopback
    except ValueError:
        return False


def _error(status: int, message: str, **extra: Any):
    response = jsonify({"error": message, **extra})
    response.status_code = status
    response.headers["Cache-Control"] = "no-store"
    return response


def after_save(app: Flask, result: dict, paths) -> None:
    """Refresh the app's live config and tell connected clients."""
    refresh = app.config.get("KICLI_REFRESH_CONFIG")
    if callable(refresh):
        refresh(force=True)
    socketio = app.config.get("SOCKETIO")
    if socketio is not None:
        try:
            socketio.emit("settings.updated", {
                "revision": result["revision"],
                "paths": sorted(paths),
                "restart_required_paths": result.get("restart_required_paths", []),
            })
        except Exception:
            logger.debug("settings.updated broadcast failed", exc_info=True)
    logger.info("Runtime settings saved: %s", ", ".join(sorted(paths)))


def register_settings_routes(app: Flask, project_root: Optional[Path] = None) -> None:
    app.config.setdefault("KICLI_SETTINGS_TOKEN", secrets.token_urlsafe(32))
    app.config.setdefault("KICLI_SETTINGS_ALLOW_REMOTE", False)
    root = Path(project_root).resolve() if project_root else None

    def _web_config() -> dict:
        config = app.config.get("KICLI_CONFIG") or {}
        web = config.get("web") if hasattr(config, "get") else None
        return web if isinstance(web, dict) else {}

    def _configured_origins() -> set[str]:
        origins = _web_config().get("cors_origins") or ["http://localhost:3000"]
        return {o for o in (_origin_of(str(x)) for x in origins) if o}

    def _allowed_origins() -> set[str]:
        # Same-origin is only trusted after the Host header passed the check below.
        return _configured_origins() | {f"{request.scheme}://{request.host}".lower()}

    def _guard() -> Optional[Any]:
        if not app.config["KICLI_SETTINGS_ALLOW_REMOTE"] and not _is_loopback(request.remote_addr):
            return _error(403, "Settings are only available from the local machine.")
        host = _host_of(request.host or "")
        allowed_hosts = set(_LOOPBACK_NAMES)
        configured = str(_web_config().get("host") or "").lower()
        if configured and configured not in ("0.0.0.0", "::"):
            allowed_hosts.add(configured)
        allowed_hosts.update(h for h in (_host_of(o) for o in _configured_origins()) if h)
        if host not in allowed_hosts:
            return _error(403, "Host not allowed for settings.")
        origin = request.headers.get("Origin")
        if origin is None and request.headers.get("Referer"):
            origin = _origin_of(request.headers["Referer"]) or "invalid"
        if origin is not None and (_origin_of(origin) or "invalid") not in _allowed_origins():
            return _error(403, "Origin not allowed for settings.")
        return None

    def _check_token() -> Optional[Any]:
        token = request.headers.get(TOKEN_HEADER, "")
        if not token or not hmac.compare_digest(token.encode(), app.config["KICLI_SETTINGS_TOKEN"].encode()):
            return _error(403, "Missing or invalid settings token.")
        return None

    def check_access(write: bool = False) -> Optional[Any]:
        """Shared guard for every config endpoint (None = allowed)."""
        return _guard() or (_check_token() if write else None)

    app.config["KICLI_SETTINGS_ACCESS"] = check_access

    def _respond(payload: dict, status: int = 200):
        payload = dict(payload)
        payload["token"] = app.config["KICLI_SETTINGS_TOKEN"]
        payload["token_header"] = TOKEN_HEADER
        response = jsonify(payload)
        response.status_code = status
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.route("/api/settings", methods=["GET"])
    def get_runtime_settings():
        denied = _guard()
        if denied is not None:
            return denied
        try:
            return _respond(runtime_config.snapshot(root))
        except EditorError as exc:
            return _error(503, str(exc))
        except Exception:
            logger.exception("settings snapshot failed")
            return _error(500, "Settings could not be read.")

    @app.route("/api/settings", methods=["POST"])
    def save_runtime_settings():
        denied = check_access(write=True)
        if denied is not None:
            return denied
        if request.content_length is None or request.content_length > MAX_BODY:
            return _error(413, "Request body missing or too large.")
        if not request.is_json:
            return _error(415, "Content-Type must be application/json.")
        data = request.get_json(silent=True)
        if not isinstance(data, dict) or set(data) - {"revision", "changes", "remove"}:
            return _error(400, "Body must be an object with revision, changes, remove.")
        revision = data.get("revision")
        changes = data.get("changes", {})
        remove = data.get("remove", [])
        if not isinstance(revision, str) or not revision or len(revision) > MAX_REVISION:
            return _error(400, "revision must be the snapshot revision string.")
        if not isinstance(changes, dict) or len(changes) > MAX_ITEMS:
            return _error(400, f"changes must be an object with at most {MAX_ITEMS} entries.")
        if (not isinstance(remove, list) or len(remove) > MAX_ITEMS
                or not all(isinstance(p, str) for p in remove)):
            return _error(400, f"remove must be a list of at most {MAX_ITEMS} paths.")
        if not changes and not remove:
            return _error(400, "Nothing to save.")
        if set(changes) & set(remove):
            return _error(400, "A path cannot be changed and removed at once.")
        try:
            result = runtime_config.save(revision, changes, remove, root)
        except ConflictError as exc:
            return _error(409, str(exc) or "Configuration changed meanwhile; reload.")
        except ValidationError as exc:
            return _error(422, str(exc) or "Invalid settings.")
        except EditorError as exc:
            return _error(503, str(exc))
        except Exception:
            logger.exception("settings save failed")
            return _error(500, "Settings could not be saved.")

        after_save(app, result, set(changes) | set(remove))
        return _respond(result)

    @app.route("/api/settings/secrets", methods=["GET"])
    def get_secret_settings():
        denied = _guard()
        if denied is not None:
            return denied
        try:
            return _respond(runtime_config.secret_snapshot(root))
        except EditorError as exc:
            return _error(503, str(exc))
        except Exception:
            logger.error("secret snapshot failed")
            return _error(500, "Credentials could not be read.")

    @app.route("/api/settings/secrets", methods=["POST"])
    def save_secret_setting():
        """Write-only: {revision, path, value} or {revision, path, remove: true}."""
        denied = check_access(write=True)
        if denied is not None:
            return denied
        if request.content_length is None or request.content_length > MAX_SECRET_BODY:
            return _error(413, "Request body missing or too large.")
        if not request.is_json:
            return _error(415, "Content-Type must be application/json.")
        data = request.get_json(silent=True)
        if not isinstance(data, dict) or set(data) - {"revision", "path", "value", "remove"}:
            return _error(400, "Body must be an object with revision, path and value or remove.")
        revision, path = data.get("revision"), data.get("path")
        remove = data.get("remove", False)
        if not isinstance(revision, str) or not revision or len(revision) > MAX_REVISION:
            return _error(400, "revision must be the secret snapshot revision string.")
        if not isinstance(path, str) or not path or len(path) > MAX_PATH:
            return _error(400, "path must be a credential path.")
        if not isinstance(remove, bool):
            return _error(400, "remove must be a boolean.")
        if remove == ("value" in data):
            return _error(400, "Send either value or remove: true.")
        value = data.get("value")
        if not remove and (not isinstance(value, str) or len(value) > MAX_SECRET_VALUE):
            return _error(400, f"value must be a string of at most {MAX_SECRET_VALUE} characters.")
        try:
            result = runtime_config.save_secret(revision, path, value, remove=remove, project_root=root)
        except ConflictError as exc:
            return _error(409, str(exc) or "Credentials changed meanwhile; reload.")
        except ValidationError as exc:
            return _error(422, str(exc) or "Invalid credential.")
        except EditorError as exc:
            return _error(503, str(exc))
        except Exception:
            # Never log exception details here: they could contain the submitted value.
            logger.error("secret save failed")
            return _error(500, "Credentials could not be saved.")
        refresh = app.config.get("KICLI_REFRESH_CONFIG")
        if callable(refresh):
            refresh(force=True)
        socketio = app.config.get("SOCKETIO")
        if socketio is not None:
            try:
                socketio.emit("settings.updated", {"secrets_revision": result["revision"], "paths": [path]})
            except Exception:
                logger.debug("settings.updated broadcast failed")
        logger.info("Credential %s %s", path, "removed" if remove else "updated")
        return _respond(result)
