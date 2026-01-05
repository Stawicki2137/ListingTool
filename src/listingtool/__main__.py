from __future__ import annotations

import argparse
import json
import sys

from .listing import list_native_functions

def cli() -> None:
    raise SystemExit(main(sys.argv))



def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="listingtool",
        description="List exported native function symbols from a Linux .so file",
    )
    parser.add_argument("so_path", help="Path to shared object (.so)")
    parser.add_argument("--json", action="store_true", help="Output JSON array")

    args = parser.parse_args(argv[1:])

    funcs = list_native_functions(args.so_path)

    if args.json:
        print(json.dumps(funcs))
    else:
        for f in funcs:
            print(f)

    return 0


if __name__ == "__main__":
    cli()
