"""Entry point for running Alembic via ``python -m backend.migrations``."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Sequence

from alembic.config import CommandLine, Config


def _build_config(script_location: Path) -> Config:
    """Construct an Alembic ``Config`` anchored to ``script_location``."""

    config = Config()
    location = str(script_location)

    config.set_main_option("script_location", location)
    config.set_section_option(config.config_ini_section, "script_location", location)
    config.set_section_option(
        config.config_ini_section,
        "prepend_sys_path",
        str(script_location.parent),
    )

    return config


def main(argv: Sequence[str] | None = None) -> int:
    """Invoke Alembic with arguments forwarded from the command line."""

    options = argv if argv is not None else sys.argv[1:]
    command = CommandLine(prog="python -m backend.migrations")
    parsed = command.parser.parse_args(list(options))

    if not getattr(parsed, "cmd", None):
        command.parser.print_help()
        return 0

    config = _build_config(Path(__file__).resolve().parent)
    command.run_cmd(config, parsed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
