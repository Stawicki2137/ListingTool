from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
from typing import Iterable


class SymbolToolError(RuntimeError):
    pass


def list_native_functions(so_path: str | Path) -> list[str]:
    """
    List exported (dynamic) function symbols available in a Linux shared object (.so).

    Tries to use `nm` first, falls back to `readelf` if needed.
    Returns a sorted list of unique function names (as seen in the binary; may be mangled for C++).
    """
    p = Path(so_path)

    if not p.exists():
        raise FileNotFoundError(str(p))
    if not p.is_file():
        raise ValueError(f"Not a file: {p}")

    # allow libfoo.so.1 etc.
    if ".so" not in p.name:
        raise ValueError(f"Not a shared object (.so): {p}")

    if shutil.which("nm"):
        try:
            return _list_with_nm(p)
        except subprocess.CalledProcessError as e:
            # fall back to readelf
            pass

    if shutil.which("readelf"):
        return _list_with_readelf(p)

    raise SymbolToolError("Neither 'nm' nor 'readelf' found in PATH")


def _run(cmd: list[str]) -> str:
    proc = subprocess.run(cmd, check=True, text=True, capture_output=True)
    return proc.stdout


def _strip_version_suffix(name: str) -> str:
    return name.split("@", 1)[0]


def _list_with_nm(p: Path) -> list[str]:
    out = _run(["nm", "-D", "--defined-only", str(p)])

    exported: set[str] = set()
    exported_types = {"T", "W"}

    for line in out.splitlines():
        parts = line.split()
        if not parts:
            continue

        sym_type = None
        name = None

        for i, tok in enumerate(parts):
            if len(tok) == 1 and tok in exported_types | {"t", "w", "U"}:
                sym_type = tok
                if i + 1 < len(parts):
                    name = parts[i + 1]
                break

        if sym_type is None or name is None:
            continue

        if sym_type not in exported_types:
            continue

        exported.add(_strip_version_suffix(name))

    return sorted(exported)


_RE_READELF = re.compile(
    r"^\s*\d+:\s+[0-9a-fA-F]+\s+\d+\s+FUNC\s+(GLOBAL|WEAK)\s+\S+\s+\S+\s+(\S+)\s*$"
)


def _list_with_readelf(p: Path) -> list[str]:
    out = _run(["readelf", "--dyn-syms", "-W", str(p)])

    exported: set[str] = set()

    for line in out.splitlines():
        m = _RE_READELF.match(line)
        if not m:
            continue
        name = m.group(2)
        exported.add(_strip_version_suffix(name))

    return sorted(exported)
