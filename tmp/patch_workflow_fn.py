"""One-off: make app_workflow_function resolve across extracted modules (run on 186)."""
from pathlib import Path

path = Path("/var/www/albery/mcp/context_server.py")
src = path.read_text(encoding="utf-8")

old = '''def app_workflow_function(name: str) -> Any:
    try:
        app_module = importlib.import_module("app")
    except Exception as exc:  # noqa: BLE001
        raise McpError(-32000, f"Cannot load local app workflow module: {exc}") from exc
    workflow = getattr(app_module, name, None)
    if not callable(workflow):
        raise McpError(-32000, f"Local app workflow is not available: {name}")
    return workflow
'''

new = '''# app.py is being split module-by-module (move-only refactor), so a workflow may now
# live in an extracted module; resolve across all of them, app first.
WORKFLOW_MODULES = ("app", "bitrix", "gdrive", "zoom", "b24bot", "llm", "utils")


def app_workflow_function(name: str) -> Any:
    import_errors: list[str] = []
    for module_name in WORKFLOW_MODULES:
        try:
            module = importlib.import_module(module_name)
        except Exception as exc:  # noqa: BLE001
            import_errors.append(f"{module_name}: {exc}")
            continue
        workflow = getattr(module, name, None)
        if callable(workflow):
            return workflow
    detail = (" (import errors: " + "; ".join(import_errors) + ")") if import_errors else ""
    raise McpError(-32000, f"Local app workflow is not available: {name}{detail}")
'''

if old not in src:
    raise SystemExit("PATCH FAILED: old block not found")
path.write_text(src.replace(old, new, 1), encoding="utf-8")
print("PATCH OK")
