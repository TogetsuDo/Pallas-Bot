from __future__ import annotations

import argparse  # noqa: TC003
from importlib import import_module
import sys

from pallas.console.cli import CLI_VERSION

_COMMAND_MODULES = (
    "pallas.console.cli.commands.doctor",
    "pallas.console.cli.commands.sync_cmd",
    "pallas.console.cli.commands.ext_cmd",
    "pallas.console.cli.commands.update_cmd",
    "pallas.console.cli.commands.lifecycle",
    "pallas.console.cli.commands.maintenance_cmd",
    "pallas.console.cli.commands.deploy_cmd",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pallas",
        description="Pallas Bot 统一运维：依赖同步、官方扩展、启停与更新",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {CLI_VERSION}",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    for module_name in _COMMAND_MODULES:
        module = import_module(module_name)
        if hasattr(module, "register"):
            module.register(sub)
        if hasattr(module, "register_run"):
            module.register_run(sub)
        if hasattr(module, "register_lifecycle"):
            module.register_lifecycle(sub)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return 2
    return int(handler(args))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
