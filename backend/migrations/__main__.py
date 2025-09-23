from __future__ import annotations

import os
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile, gettempdir
from textwrap import dedent

from alembic.config import main as alembic_main

_CONFIG_TEMPLATE = """\
[alembic]
script_location = {script_location}
prepend_sys_path = {prepend_sys_path}
sqlalchemy.url = sqlite:///placeholder

timezone = UTC

autogenerate = true

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
"""


def _normalize_args(args: list[str]) -> list[str]:
    # Allow commands to include an "alembic" prefix to mirror the upstream CLI.
    if args and args[0] == "alembic":
        return args[1:]
    return args


def _write_config(tmp_dir: Path) -> Path:
    migrations_dir = Path(__file__).resolve().parent
    config_body = _CONFIG_TEMPLATE.format(
        script_location=migrations_dir.as_posix(),
        prepend_sys_path=migrations_dir.parent.as_posix(),
    )

    with NamedTemporaryFile("w", suffix=".ini", dir=tmp_dir, delete=False) as handle:
        handle.write(dedent(config_body))
        return Path(handle.name)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    normalized = _normalize_args(args)

    tmp_dir = Path(os.getenv("TMPDIR", gettempdir()))
    config_path = _write_config(tmp_dir)
    try:
        alembic_main(["-c", str(config_path), *normalized])
    finally:
        try:
            config_path.unlink()
        except FileNotFoundError:
            pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
