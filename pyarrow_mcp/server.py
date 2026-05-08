"""MCP server: SDK reference resources + introspection tools (no live trading calls)."""

from __future__ import annotations

import importlib
import inspect
import json
from enum import Enum
from typing import Any

from mcp.server.fastmcp import FastMCP

import pyarrow_client
from pyarrow_client import constants as const
from pyarrow_client import exceptions as exc_mod
from pyarrow_client.connect import ArrowClient
from pyarrow_client.sockets import ArrowStreams, DataMode, DataStream, HFTDataStream, OrderStream

from pyarrow_mcp import reference_docs as docs

_INSTRUCTIONS = """This MCP server documents the Python SDK **pyarrow-client** (import: `pyarrow_client`) for Arrow Trading.
Use it before writing or reviewing code so method names, enums, and flows match the real library.

- Read resources with URI prefix `pyarrow-sdk://reference/` for curated docs.
- Call tools `sdk_version`, `list_sdk_resources`, `list_package_exports`, `inspect_class`, `enum_members`, `lookup_constant` for ground truth from the installed package.
- This server does **not** execute trades or call Arrow APIs; it only exposes documentation and introspection.
"""

mcp = FastMCP(
    "pyarrow-client-sdk",
    instructions=_INSTRUCTIONS,
)

_CLASS_REGISTRY: dict[str, type] = {
    "arrowclient": ArrowClient,
    "arrow_client": ArrowClient,
    "arrow": ArrowClient,  # alias in connect.py
    "arrowstreams": ArrowStreams,
    "orderstream": OrderStream,
    "datastream": DataStream,
    "hftdatastream": HFTDataStream,
    "hft_data_stream": HFTDataStream,
    "routes": const.Routes,
    "exchange": const.Exchange,
    "ordertype": const.OrderType,
    "producttype": const.ProductType,
    "retention": const.Retention,
    "transactiontype": const.TransactionType,
    "variety": const.Variety,
    "quotemode": const.QuoteMode,
    "datamode": DataMode,
}

_ENUM_REGISTRY: dict[str, type[Enum]] = {
    "exchange": const.Exchange,
    "ordertype": const.OrderType,
    "producttype": const.ProductType,
    "retention": const.Retention,
    "transactiontype": const.TransactionType,
    "variety": const.Variety,
    "quotemode": const.QuoteMode,
    "datamode": DataMode,
}


def _resolve_class(name: str) -> type | None:
    key = name.strip().lower().replace("_", "")
    if key in _CLASS_REGISTRY:
        return _CLASS_REGISTRY[key]
    # allow exact module path e.g. pyarrow_client.connect.ArrowClient
    if "." in name:
        try:
            module_path, _, cls_name = name.rpartition(".")
            mod = importlib.import_module(module_path)
            obj = getattr(mod, cls_name, None)
            if isinstance(obj, type):
                return obj
        except (ImportError, AttributeError, ValueError):
            return None
    return None


def _serialize_signature(callable_obj: Any) -> str:
    try:
        return str(inspect.signature(callable_obj))
    except (TypeError, ValueError):
        return "(signature unavailable)"


def _enum_resolve(enum_cls: type[Enum], value: str) -> tuple[str | None, str | None]:
    """Return (canonical_string_value, error_message)."""
    v = value.strip()
    try:
        member = enum_cls[v.upper()] if v.isidentifier() else None
    except KeyError:
        member = None
    if member is None:
        for m in enum_cls:
            if m.name.upper() == v.upper() or str(m.value) == v:
                member = m
                break
    if member is None:
        return None, f"Not found: {value!r} in {enum_cls.__name__}"
    return str(member.value), None


# --- Resources -----------------------------------------------------------------


@mcp.resource("pyarrow-sdk://reference/overview", mime_type="text/markdown")
def resource_overview() -> str:
    return docs.REF_OVERVIEW


@mcp.resource("pyarrow-sdk://reference/authentication", mime_type="text/markdown")
def resource_authentication() -> str:
    return docs.REF_AUTHENTICATION


@mcp.resource("pyarrow-sdk://reference/http-client", mime_type="text/markdown")
def resource_http_client() -> str:
    return docs.REF_HTTP_CLIENT


@mcp.resource("pyarrow-sdk://reference/enums", mime_type="text/markdown")
def resource_enums() -> str:
    return docs.REF_ENUMS


@mcp.resource("pyarrow-sdk://reference/exceptions", mime_type="text/markdown")
def resource_exceptions() -> str:
    return docs.REF_EXCEPTIONS


@mcp.resource("pyarrow-sdk://reference/websockets", mime_type="text/markdown")
def resource_websockets() -> str:
    return docs.REF_WEBSOCKETS


@mcp.resource("pyarrow-sdk://reference/routes-and-urls", mime_type="text/markdown")
def resource_routes() -> str:
    return docs.REF_ROUTES


@mcp.resource("pyarrow-sdk://introspection/class/{class_name}", mime_type="text/markdown")
def resource_introspect_class(class_name: str) -> str:
    """Dynamic class/method listing (ground truth from installed `pyarrow_client`)."""
    cls = _resolve_class(class_name)
    if cls is None:
        return f"# Unknown class: {class_name!r}\n\nTry: ArrowClient, ArrowStreams, OrderStream, DataStream, HFTDataStream, Routes, or a full dotted path."
    lines = [
        f"# {cls.__module__}.{cls.__name__}",
        "",
        f"Defined in `{inspect.getsourcefile(cls)}`.",
        "",
        "## Callable members",
        "",
    ]
    for nm, member in inspect.getmembers(cls):
        if nm.startswith("_"):
            continue
        if inspect.isfunction(member) or inspect.ismethoddescriptor(member):
            # methods on class
            func = getattr(cls, nm, None)
            if callable(func) and not isinstance(func, type):
                doc = (inspect.getdoc(func) or "").strip()
                doc_line = f" — {doc.splitlines()[0]}" if doc else ""
                lines.append(f"- `{nm}{_serialize_signature(func)}`{doc_line}")
        elif isinstance(member, property):
            doc = (inspect.getdoc(member) or "").strip()
            doc_line = f" — {doc.splitlines()[0]}" if doc else ""
            lines.append(f"- `@property {nm}`{doc_line}")

    if inspect.isclass(cls) and issubclass(cls, Enum):
        lines.extend(["", "## Enum members", ""])
        for m in cls:
            lines.append(f"- `{m.name}` = `{m.value!r}`")

    return "\n".join(lines)


# --- Tools ----------------------------------------------------------------------


@mcp.tool()
def list_sdk_resources() -> str:
    """URIs of bundled markdown reference resources (read via MCP resources)."""
    uris = [
        "pyarrow-sdk://reference/overview",
        "pyarrow-sdk://reference/authentication",
        "pyarrow-sdk://reference/http-client",
        "pyarrow-sdk://reference/enums",
        "pyarrow-sdk://reference/exceptions",
        "pyarrow-sdk://reference/websockets",
        "pyarrow-sdk://reference/routes-and-urls",
        "pyarrow-sdk://introspection/class/{class_name}",
    ]
    return json.dumps({"resources": uris, "note": "Replace {class_name} e.g. ArrowClient, HFTDataStream."}, indent=2)


@mcp.tool()
def sdk_version() -> str:
    """Installed pyarrow-client version string (from pyarrow_client.__version__)."""
    return pyarrow_client.__version__


@mcp.tool()
def list_package_exports() -> str:
    """Symbols exported in `pyarrow_client.__all__` plus the submodule path for ArrowClient."""
    data = {
        "__all__": list(pyarrow_client.__all__),
        "ArrowClient_module": f"{ArrowClient.__module__}.{ArrowClient.__name__}",
        "HFTDataStream_note": "HFTDataStream lives in pyarrow_client.sockets (not in __all__).",
    }
    return json.dumps(data, indent=2)


@mcp.tool()
def inspect_class(
    class_name: str,
    include_private: bool = False,
) -> str:
    """
    Inspect a class: methods, properties, signatures, first line of docstrings.
    Names accepted: ArrowClient, Arrow, ArrowStreams, OrderStream, DataStream,
    HFTDataStream, Routes, enum types, or dotted path like pyarrow_client.connect.ArrowClient.
    """
    cls = _resolve_class(class_name)
    if cls is None:
        return json.dumps({"error": f"unknown class: {class_name}", "known_keys": sorted(_CLASS_REGISTRY.keys())})

    items: list[dict[str, Any]] = []
    for nm, member in inspect.getmembers(cls):
        if nm.startswith("_") and not include_private:
            continue
        if inspect.isfunction(member):
            doc = inspect.getdoc(member) or ""
            items.append(
                {
                    "kind": "function",
                    "name": nm,
                    "signature": _serialize_signature(member),
                    "doc_first_line": doc.splitlines()[0] if doc else None,
                }
            )
        elif isinstance(member, staticmethod):
            fn = member.__func__
            doc = inspect.getdoc(fn) or ""
            items.append(
                {
                    "kind": "staticmethod",
                    "name": nm,
                    "signature": _serialize_signature(fn),
                    "doc_first_line": doc.splitlines()[0] if doc else None,
                }
            )
        elif isinstance(member, classmethod):
            fn = member.__func__
            doc = inspect.getdoc(fn) or ""
            items.append(
                {
                    "kind": "classmethod",
                    "name": nm,
                    "signature": _serialize_signature(fn),
                    "doc_first_line": doc.splitlines()[0] if doc else None,
                }
            )
        elif isinstance(member, property):
            doc = inspect.getdoc(member) or ""
            items.append(
                {
                    "kind": "property",
                    "name": nm,
                    "doc_first_line": doc.splitlines()[0] if doc else None,
                }
            )

    if inspect.isclass(cls) and issubclass(cls, Enum):
        items.extend(
            {"kind": "enum_member", "name": m.name, "value": m.value} for m in cls  # type: ignore[arg-type]
        )

    out = {
        "module": cls.__module__,
        "name": cls.__name__,
        "file": inspect.getsourcefile(cls),
        "members": sorted(items, key=lambda x: (x["kind"], x["name"])),
    }
    return json.dumps(out, indent=2, default=str)


@mcp.tool()
def enum_members(enum_name: str) -> str:
    """List members of a trading/stream enum: Exchange, OrderType, ProductType, Retention, TransactionType, Variety, QuoteMode, DataMode."""
    key = enum_name.strip().lower().replace("_", "")
    enum_cls = _ENUM_REGISTRY.get(key)
    if enum_cls is None:
        return json.dumps({"error": f"unknown enum: {enum_name}", "known": sorted(_ENUM_REGISTRY.keys())})
    members = [{"name": m.name, "value": m.value, "str_for_api": str(m)} for m in enum_cls]
    return json.dumps({"enum": enum_cls.__name__, "members": members}, indent=2)


@mcp.tool()
def resolve_enum_value(enum_name: str, value: str) -> str:
    """Map a user-supplied value or member name to the exact API string used by the SDK (str(enum))."""
    key = enum_name.strip().lower().replace("_", "")
    enum_cls = _ENUM_REGISTRY.get(key)
    if enum_cls is None:
        return json.dumps({"ok": False, "error": f"unknown enum: {enum_name}"})
    canonical, err = _enum_resolve(enum_cls, value)
    if err:
        return json.dumps({"ok": False, "error": err})
    return json.dumps({"ok": True, "enum": enum_cls.__name__, "api_value": canonical})


@mcp.tool()
def lookup_constant(name: str) -> str:
    """Look up module-level constants in pyarrow_client.constants (e.g. STATUS, ERROR_CODE, path names)."""
    n = name.strip()
    if not hasattr(const, n):
        keys = sorted(k for k in dir(const) if not k.startswith("_"))
        return json.dumps({"found": False, "candidates": keys[:80], "hint": "too many to list fully; narrow name"})
    val = getattr(const, n)
    if inspect.isclass(val):
        return json.dumps({"found": True, "kind": "class", "name": val.__name__, "module": val.__module__})
    return json.dumps({"found": True, "kind": "value", "repr": repr(val)}, default=str)


@mcp.tool()
def list_exception_classes() -> str:
    """Exception types defined in pyarrow_client.exceptions (for error handling code)."""
    classes = []
    for nm in dir(exc_mod):
        if nm.startswith("_"):
            continue
        obj = getattr(exc_mod, nm)
        if inspect.isclass(obj) and issubclass(obj, Exception):
            classes.append({"name": nm, "module": obj.__module__})
    return json.dumps(sorted(classes, key=lambda x: x["name"]), indent=2)


def main() -> None:
    """Run the MCP server over stdio (default for Cursor / Claude Desktop)."""
    import os
    import sys

    # Interactive terminal: stdio MCP blocks reading stdin — that is normal. Cursor
    # spawns this process with piped stdio and drives the protocol.
    if sys.stdin.isatty():
        print(
            "pyarrow_mcp: MCP stdio server — waiting for JSON-RPC on stdin. "
            "If you opened this in a shell, it will idle here until Cursor (or another "
            "MCP host) attaches. Press Ctrl+C once to exit.",
            file=sys.stderr,
        )

    try:
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        # Immediate process exit avoids a rare interpreter crash on second ^C during
        # stdio transport teardown (stdin lock / daemon threads).
        os._exit(130)