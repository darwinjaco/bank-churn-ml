"""Helper Git del workflow: credenciales solo para el Space esperado (spec 007 §6)."""

from __future__ import annotations

import os
import re
import sys

SPACE_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]*/[A-Za-z0-9][A-Za-z0-9_-]*")


def credential(context: dict, environment: dict) -> dict:
    space = environment.get("HF_SPACE", "")
    token = environment.get("HF_TOKEN", "")
    if not SPACE_NAME.fullmatch(space) or not token or "\n" in token or "\r" in token:
        return {}
    if (
        context.get("protocol") != "https"
        or context.get("host") != "huggingface.co"
        or context.get("path") not in {f"spaces/{space}", f"spaces/{space}.git"}
    ):
        return {}
    return {"username": "hf", "password": token}


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args != ["get"]:
        return 0  # No almacena credenciales durante store/erase.
    context = {}
    for line in sys.stdin:
        line = line.rstrip("\r\n")
        if not line:
            break
        if "=" in line:
            key, value = line.split("=", 1)
            context[key] = value
    for key, value in credential(context, os.environ).items():
        print(f"{key}={value}")  # stdout pertenece al pipe privado del protocolo de Git.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
