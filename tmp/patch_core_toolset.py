"""One-off: two-stage tool loading (core + find_tool/call_tool) for the Bitrix bot (run on 186)."""
from pathlib import Path

FILES = {
    "cs": Path("/var/www/albery/mcp/context_server.py"),
    "app": Path("/var/www/albery/app.py"),
    "bot": Path("/var/www/albery/b24bot.py"),
}
SRC = {key: path.read_text(encoding="utf-8") for key, path in FILES.items()}


def norm(text: str) -> str:
    return text.replace("\r\n", "\n")


def splice(key: str, old: str, new: str, label: str) -> None:
    old, new = norm(old), norm(new)
    if SRC[key].count(old) != 1:
        raise SystemExit(f"PATCH FAILED at {label}: anchor found {SRC[key].count(old)} times")
    SRC[key] = SRC[key].replace(old, new, 1)


# =============================== context_server.py ===========================================

# --- 1. CORE set + meta-tool specs + search, after OPS_TOOL_NAMES ----------------------------
splice(
    "cs",
    '''# Operational-full connector: every registered tool EXCEPT the admin-only ones above.
OPS_TOOL_NAMES: set[str] = set(TOOLS) - OWNER_ONLY_TOOL_NAMES''',
    '''# Operational-full connector: every registered tool EXCEPT the admin-only ones above.
OPS_TOOL_NAMES: set[str] = set(TOOLS) - OWNER_ONLY_TOOL_NAMES

# --- Core toolset: two-stage tool loading for the chat bot (/mcp-core, /mcp-ops-core) --------
# The chat bot registers only this curated core (picked from real usage stats in the Hermes
# session DB: ~82% of all historical calls, plus every tool the bot prompt names explicitly)
# and two meta-tools. Everything else is discovered via find_tool and invoked via call_tool.
# Cron agents keep the full /mcp and /mcp-ops connectors, so their scripted tool names are
# unaffected by this list.
CORE_TOOL_NAMES: set[str] = {
    # entry / self-knowledge
    "start_here_always_read_ai_instructions",
    "get_ai_instructions",
    "get_ai_capabilities",
    "get_context_guide",
    # company knowledge
    "search_company_knowledge",
    "list_company_files",
    "get_company_file",
    "get_org_structure",
    "get_employee_absences",
    # tasks
    "search_tasks",
    "get_task_comments",
    "create_bitrix_task",
    # zoom
    "list_zoom_calls",
    "get_zoom_call_transcript",
    "search_zoom_transcripts",
    # dialog memory
    "get_bitrix_bot_chat",
    "list_bitrix_bot_sessions",
    # messaging / web
    "send_bitrix_message",
    "fetch_url",
    # google workflow the bot prompt teaches
    "create_google_sheet",
    "get_google_sheet_meta",
    "write_google_sheet_values",
    "share_drive_item_for_everyone",
    "get_webapp_template",
    "make_sheet_applet",
    "manage_apps_script",
}

META_TOOL_SPECS: dict[str, dict[str, Any]] = {
    "find_tool": {
        "description": (
            "Найди инструмент по задаче. Твой список инструментов — ЯДРО самых частых; у "
            "коннектора есть и другие. Если нужного действия нет в списке — НЕ отвечай «не "
            "умею»: вызови этот поиск, получи имя/описание/схему аргументов и выполни действие "
            "через call_tool. Query — короткие английские ключевые слова по смыслу действия "
            "(например 'delete task', 'zoom report', 'drive folder', 'owner recommendations')."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Английские ключевые слова: что нужно сделать.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Сколько кандидатов вернуть (по умолчанию 5).",
                },
            },
            "required": ["query"],
        },
    },
    "call_tool": {
        "description": (
            "Вызови любой инструмент коннектора по точному имени — в том числе не входящий в "
            "ядро. Сначала найди его через find_tool и заполни arguments по его inputSchema."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Точное имя инструмента (из find_tool)."},
                "arguments": {"type": "object", "description": "Аргументы по схеме инструмента."},
            },
            "required": ["name"],
        },
    },
}


def _find_tool_matches(query: Any, tool_names: set[str] | None, limit: int) -> list[dict[str, Any]]:
    tokens = [t for t in re.split(r"[^0-9a-zA-Zа-яА-ЯёЁ_]+", str(query or "").lower()) if len(t) >= 3]
    if not tokens:
        raise McpError(-32602, "Нужен запрос: find_tool(query='что нужно сделать', английскими словами).")
    scored: list[tuple[int, str, dict[str, Any]]] = []
    for name, spec in _allowed_tools(tool_names).items():
        hay_name = name.lower()
        hay_desc = str(spec.get("description") or "").lower()
        score = 0
        for tok in tokens:
            if tok in hay_name:
                score += 30
            score += 3 * hay_desc.count(tok)
        if score:
            scored.append((score, name, spec))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [
        {
            "name": name,
            "description": spec["description"],
            "inputSchema": spec["inputSchema"],
            "how_to_call": "call_tool(name='" + name + "', arguments={...})",
        }
        for _score, name, spec in scored[: max(1, limit)]
    ]''',
    "core set + meta specs",
)

# --- 2. list_tools with core view -------------------------------------------------------------
splice(
    "cs",
    '''def list_tools(tool_names: set[str] | None = None) -> list[dict[str, Any]]:
    return [
        {
            "name": name,
            "description": (
                spec["description"]
                if name == "start_here_always_read_ai_instructions"
                else TOOL_USAGE_CONTRACT + spec["description"]
            ),
            "inputSchema": spec["inputSchema"],
        }
        for name, spec in _allowed_tools(tool_names).items()
    ]''',
    '''def list_tools(tool_names: set[str] | None = None, core: bool = False) -> list[dict[str, Any]]:
    registry = _allowed_tools(tool_names)
    if core:
        registry = {name: registry[name] for name in sorted(CORE_TOOL_NAMES) if name in registry}
    items = [
        {
            "name": name,
            "description": (
                spec["description"]
                if name == "start_here_always_read_ai_instructions"
                else TOOL_USAGE_CONTRACT + spec["description"]
            ),
            "inputSchema": spec["inputSchema"],
        }
        for name, spec in registry.items()
    ]
    if core:
        items.extend(
            {"name": name, "description": spec["description"], "inputSchema": spec["inputSchema"]}
            for name, spec in META_TOOL_SPECS.items()
        )
    return items''',
    "list_tools core view",
)

# --- 3. handle_request: core param, find_tool/call_tool, hidden tools for start_here ----------
splice(
    "cs",
    '''def handle_request(request: dict[str, Any], tool_names: set[str] | None = None) -> dict[str, Any] | None:
    request_id = request.get("id")
    method = request.get("method")
    available_tools = _allowed_tools(tool_names)

    if method == "notifications/initialized":
        return None

    try:
        if method == "initialize":
            result = {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            }
        elif method == "tools/list":
            result = {"tools": list_tools(tool_names)}
        elif method == "tools/call":
            params = request.get("params") or {}
            name = params.get("name")
            args = params.get("arguments") or {}
            if name not in available_tools:
                raise McpError(-32601, f"Unknown or unavailable tool: {name}")
            # Defense-in-depth: admin-only tools are reachable ONLY via the full/admin connector
            # (tool_names is None). Even if a future config mistakenly added them to a scoped
            # connector's tool set, refuse here.
            if name in OWNER_ONLY_TOOL_NAMES and tool_names is not None:
                raise McpError(-32601, f"Unknown or unavailable tool: {name}")
            if name in ("start_here_always_read_ai_instructions", "get_ai_capabilities"):
                connector_id = "faq" if tool_names == FAQ_TOOL_NAMES else "full"
                args = {
                    **args,
                    "_connector_tools": sorted(available_tools.keys()),
                    "_connector_id": connector_id,
                }''',
    '''def handle_request(request: dict[str, Any], tool_names: set[str] | None = None,
                   core: bool = False) -> dict[str, Any] | None:
    request_id = request.get("id")
    method = request.get("method")
    available_tools = _allowed_tools(tool_names)

    if method == "notifications/initialized":
        return None

    try:
        if method == "initialize":
            result = {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            }
        elif method == "tools/list":
            result = {"tools": list_tools(tool_names, core=core)}
        elif method == "tools/call":
            params = request.get("params") or {}
            name = params.get("name")
            args = params.get("arguments") or {}
            if core and name == "find_tool":
                matches = _find_tool_matches(args.get("query"), tool_names, int(args.get("limit") or 5))
                return {"jsonrpc": "2.0", "id": request_id, "result": text_response({
                    "matches": matches,
                    "note": "Вызывай выбранный инструмент через call_tool(name=..., arguments={...}) по его inputSchema.",
                })}
            if core and name == "call_tool":
                inner_args = args.get("arguments")
                name = str(args.get("name") or "").strip()
                args = inner_args if isinstance(inner_args, dict) else {}
                logger.info("mcp_call_tool_proxy name=%s", name)
            if name not in available_tools:
                if core:
                    raise McpError(-32601, f"Unknown or unavailable tool: {name}. Найди точное имя через find_tool.")
                raise McpError(-32601, f"Unknown or unavailable tool: {name}")
            # Defense-in-depth: admin-only tools are reachable ONLY via the full/admin connector
            # (tool_names is None). Even if a future config mistakenly added them to a scoped
            # connector's tool set, refuse here.
            if name in OWNER_ONLY_TOOL_NAMES and tool_names is not None:
                raise McpError(-32601, f"Unknown or unavailable tool: {name}")
            if name in ("start_here_always_read_ai_instructions", "get_ai_capabilities"):
                connector_id = "faq" if tool_names == FAQ_TOOL_NAMES else "full"
                args = {
                    **args,
                    "_connector_tools": sorted(available_tools.keys()),
                    "_connector_id": connector_id,
                }
                if core:
                    args["_connector_tools"] = sorted(
                        (set(available_tools.keys()) & CORE_TOOL_NAMES) | set(META_TOOL_SPECS)
                    )
                    args["_connector_hidden_tools"] = sorted(
                        set(available_tools.keys()) - CORE_TOOL_NAMES
                    )''',
    "handle_request core dispatch",
)

# --- 4. start_here handler: surface hidden tools honestly -------------------------------------
splice(
    "cs",
    '''    instructions = load_ai_instructions()
    available_tools = list(args.get("_connector_tools") or sorted(TOOLS.keys()))
    connector_id = args.get("_connector_id") or "full"''',
    '''    instructions = load_ai_instructions()
    available_tools = list(args.get("_connector_tools") or sorted(TOOLS.keys()))
    hidden_tools = list(args.get("_connector_hidden_tools") or [])
    connector_id = args.get("_connector_id") or "full"''',
    "start_here hidden var",
)
splice(
    "cs",
    '''            "available_tools": sorted(available_tools),
            "rules": [''',
    '''            "available_tools": sorted(available_tools),
            **({
                "more_tools_via_call_tool": hidden_tools,
                "two_stage_note": (
                    "ВАЖНО: инструменты из more_tools_via_call_tool тебе ТОЖЕ доступны — найди "
                    "нужный через find_tool и вызывай через call_tool(name=..., arguments={...}). "
                    "Правило «нет доступа» применяй ТОЛЬКО к тому, чего нет ни в available_tools, "
                    "ни в more_tools_via_call_tool."
                ),
            } if hidden_tools else {}),
            "rules": [''',
    "start_here hidden keys",
)

# ==================================== app.py =================================================
splice(
    "app",
    '''    response = handle_request(payload, tool_names=OPS_TOOL_NAMES)
    if response is None:
        return ("", 202)
    return jsonify(response), mcp_status_code(response)


@app.get("/sse")''',
    '''    response = handle_request(payload, tool_names=OPS_TOOL_NAMES)
    if response is None:
        return ("", 202)
    return jsonify(response), mcp_status_code(response)


# --- Core connectors: curated tool core + find_tool/call_tool (two-stage loading). Used by the
# Bitrix chat bot to keep per-turn context small; cron agents keep the full /mcp and /mcp-ops
# connectors, so their scripted tool names are unaffected.
@app.get("/mcp-core")
@app.get("/mcp-core/<path:path_token>")
def mcp_core_info(path_token: str | None = None):
    if not mcp_auth_ok(path_token):
        return mcp_auth_error()
    return jsonify({
        "name": "employee-analytics-context-core",
        "transport": "http-json-rpc",
        "endpoint": "/mcp-core",
        "auth": "shared-secret",
        "scope": "curated core of the full connector + find_tool/call_tool for the rest",
        "methods": ["initialize", "tools/list", "tools/call"],
    })


@app.post("/mcp-core")
@app.post("/mcp-core/<path:path_token>")
def mcp_core_http(path_token: str | None = None):
    if not mcp_auth_ok(path_token):
        return mcp_auth_error()
    from mcp.context_server import handle_request

    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify({
            "jsonrpc": "2.0",
            "id": None,
            "error": {"code": -32700, "message": "Request body must be JSON."},
        }), 400

    response = handle_request(payload, core=True)
    if response is None:
        return ("", 202)
    return jsonify(response), mcp_status_code(response)


@app.get("/mcp-ops-core")
@app.get("/mcp-ops-core/<path:path_token>")
def mcp_ops_core_info(path_token: str | None = None):
    if not ops_mcp_auth_ok(path_token):
        return mcp_auth_error()
    return jsonify({
        "name": "employee-analytics-context-ops-core",
        "transport": "http-json-rpc",
        "endpoint": "/mcp-ops-core",
        "auth": "shared-secret",
        "scope": "curated core of the ops connector + find_tool/call_tool for the rest",
        "methods": ["initialize", "tools/list", "tools/call"],
    })


@app.post("/mcp-ops-core")
@app.post("/mcp-ops-core/<path:path_token>")
def mcp_ops_core_http(path_token: str | None = None):
    if not ops_mcp_auth_ok(path_token):
        return mcp_auth_error()
    from mcp.context_server import OPS_TOOL_NAMES, handle_request

    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify({
            "jsonrpc": "2.0",
            "id": None,
            "error": {"code": -32700, "message": "Request body must be JSON."},
        }), 400

    response = handle_request(payload, tool_names=OPS_TOOL_NAMES, core=True)
    if response is None:
        return ("", 202)
    return jsonify(response), mcp_status_code(response)


@app.get("/sse")''',
    "core routes",
)

# ==================================== b24bot.py ==============================================
splice(
    "bot",
    '''    session, seed = _b24_session_prepare(dialog_id)
    toolset = {"admin": "albery", "ops": "albery-ops"}.get(tier, "albery-faq")''',
    '''    session, seed = _b24_session_prepare(dialog_id)
    toolset = {"admin": "albery", "ops": "albery-ops"}.get(tier, "albery-faq")
    core_toolset = tier in ("admin", "ops") and os.getenv("B24_CORE_TOOLSET", "").strip() == "1"
    if core_toolset:
        # Two-stage tools: the bot registers a curated core + find_tool/call_tool (fast turns,
        # small context); the full connectors stay untouched for cron agents.
        toolset = {"admin": "albery-core", "ops": "albery-ops-core"}[tier]''',
    "toolset override",
)
splice(
    "bot",
    '''    parts = [head]
    parts.append(
        "Текущие дата и время: " + msk_now().strftime("%d.%m.%Y %H:%M")
        + " МСК (Europe/Moscow) — это «сегодня/сейчас» для любых расчётов сроков и дат."
    )''',
    '''    parts = [head]
    parts.append(
        "Текущие дата и время: " + msk_now().strftime("%d.%m.%Y %H:%M")
        + " МСК (Europe/Moscow) — это «сегодня/сейчас» для любых расчётов сроков и дат."
    )
    if core_toolset:
        parts.append(
            "ИНСТРУМЕНТЫ — ДВУХСТУПЕНЧАТАЯ СХЕМА (важно): в твоём списке — ядро самых нужных "
            "инструментов. Если нужного действия в списке НЕТ — не отвечай «не умею/нет доступа»: "
            "сначала вызови find_tool (query — короткие английские ключевые слова, например "
            "'delete task', 'zoom report', 'drive folder'), возьми из результата точное имя и "
            "схему аргументов и выполни действие через call_tool(name=..., arguments={...})."
        )''',
    "two-stage prompt",
)

for key, path in FILES.items():
    path.write_text(SRC[key], encoding="utf-8")
print("PATCH OK")
