# ListingTool

A simple Python tool for listing exported native function symbols from Linux shared objects (`.so`).

## Requirements (Linux)

- Python 3.10+ (tested with Python 3.12)
- `gcc` (needed for building the demo `.so` and for unit tests)
- `nm` or `readelf` (symbol extraction; usually provided by `binutils`)

Verify tools are available:

```bash
python3 --version
gcc --version
nm --version || true
readelf --version || true 
```

## Setup (venv)

From the project root:
```bash 
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -U pytest
```

## Install for easy usage

To avoid PYTHONPATH=src and make the package importable from anywhere, install it in editable mode:

```bash
pip install -e .
```

After that, you can run the tool as a module:

```bash
python -m listingtool ...
```


If you also configured a console script entrypoint, you can additionally use:
```bash
listingtool ...
```

## Demo: build a sample .so

The demo/ folder contains:

libdemo.c — small C library (exports add and mul)

exports.map — linker version script to export only add and mul

Build the demo library:
```bash
cd demo
gcc -shared -fPIC -o libdemo.so libdemo.c -Wl,--version-script=exports.map
nm -D --defined-only libdemo.so
```

Expected nm output should include add and mul.

## Usage
Run as a module (recommended)

From the project root:
```bash
python -m listingtool ./demo/libdemo.so
```


From any directory (works after pip install -e .), pass an absolute/relative path to the .so:
```bash
python -m listingtool /full/path/to/libdemo.so
```

## If you did NOT run pip install -e .

From the project root:
```bash
PYTHONPATH=src python -m listingtool ./demo/libdemo.so
```

From demo/:
```bash
PYTHONPATH=../src python -m listingtool ./libdemo.so
```
## Tests

Run tests from the project root:
```bash
pytest -q
```

## Notes:

Tests compile a small .so during execution, so gcc is required.

The tool uses nm if available and falls back to readelf.