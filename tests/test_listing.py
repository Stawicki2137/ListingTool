from __future__ import annotations

import platform
import shutil
import subprocess
from pathlib import Path

import pytest

from listingtool.listing import SymbolToolError, list_native_functions


@pytest.mark.skipif(platform.system() != "Linux", reason="Task targets Linux .so files only")
def test_lists_exported_functions_only(tmp_path: Path) -> None:
    if shutil.which("gcc") is None:
        pytest.skip("gcc not available")
    if shutil.which("nm") is None and shutil.which("readelf") is None:
        pytest.skip("Neither nm nor readelf available")

    c_file = tmp_path / "libtest.c"
    so_file = tmp_path / "libtest.so"
    map_file = tmp_path / "exports.map"

    c_file.write_text(
        r"""
        __attribute__((visibility("default")))
        int add(int a, int b) { return a + b; }

        __attribute__((visibility("default")))
        int mul(int a, int b) { return a * b; }

        static int hidden(int x) { return x + 1; }

        int global_var = 42;
        """,
        encoding="utf-8",
    )

    # Export ONLY add and mul, hide everything else (including compiler/runtime extras)
    map_file.write_text(
        r"""
        {
          global:
            add;
            mul;
          local:
            *;
        };
        """,
        encoding="utf-8",
    )

    subprocess.run(
        [
            "gcc",
            "-shared",
            "-fPIC",
            "-o",
            str(so_file),
            str(c_file),
            f"-Wl,--version-script={map_file}",
        ],
        check=True,
        text=True,
        capture_output=True,
    )

    funcs = list_native_functions(so_file)
    assert funcs == ["add", "mul"]


def test_raises_for_missing_file(tmp_path: Path) -> None:
    missing = tmp_path / "nope.so"
    with pytest.raises(FileNotFoundError):
        list_native_functions(missing)


def test_raises_for_non_so_file(tmp_path: Path) -> None:
    p = tmp_path / "not_a_so.txt"
    p.write_text("hello", encoding="utf-8")
    with pytest.raises(ValueError):
        list_native_functions(p)


def test_raises_if_no_symbol_tools_available(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = tmp_path / "libfake.so"
    fake.write_bytes(b"\x7fELF")

    monkeypatch.setattr(shutil, "which", lambda _: None)

    with pytest.raises(SymbolToolError):
        list_native_functions(fake)


@pytest.mark.skipif(platform.system() != "Linux", reason="Task targets Linux .so files only")
def test_falls_back_to_readelf_when_nm_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    if shutil.which("gcc") is None:
        pytest.skip("gcc not available")
    if shutil.which("readelf") is None:
        pytest.skip("readelf not available")

    c_file = tmp_path / "libtest.c"
    so_file = tmp_path / "libtest.so"
    map_file = tmp_path / "exports.map"

    c_file.write_text(
        r"""
        __attribute__((visibility("default")))
        int add(int a, int b) { return a + b; }

        __attribute__((visibility("default")))
        int mul(int a, int b) { return a * b; }
        """,
        encoding="utf-8",
    )

    map_file.write_text(
        r"""
        {
          global:
            add;
            mul;
          local:
            *;
        };
        """,
        encoding="utf-8",
    )

    subprocess.run(
        [
            "gcc",
            "-shared",
            "-fPIC",
            "-o",
            str(so_file),
            str(c_file),
            f"-Wl,--version-script={map_file}",
        ],
        check=True,
        text=True,
        capture_output=True,
    )

    # Pretend nm exists...
    real_which = shutil.which

    def fake_which(cmd: str):
        if cmd == "nm":
            return "/usr/bin/nm"
        return real_which(cmd)

    monkeypatch.setattr(shutil, "which", fake_which)

    # ...but make nm fail, so we hit the readelf fallback.
    real_run = subprocess.run

    def fake_run(cmd, *args, **kwargs):
        if isinstance(cmd, list) and cmd and cmd[0] == "nm":
            raise subprocess.CalledProcessError(returncode=1, cmd=cmd, output="", stderr="nm failed")
        return real_run(cmd, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", fake_run)

    funcs = list_native_functions(so_file)
    assert funcs == ["add", "mul"]
