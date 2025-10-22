"""Publish processed heritage overlays into the application package."""

from __future__ import annotations

import argparse
import shutil
from datetime import datetime
from pathlib import Path

from . import DEFAULT_DATA_DIR

APP_DATA_PATH = Path("backend/app/data/heritage_overlays.geojson")
METADATA_PATH = Path(f"{DEFAULT_DATA_DIR}/processed/metadata.json")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Load processed heritage overlays into the application package"
    )
    parser.add_argument(
        "--source",
        default=f"{DEFAULT_DATA_DIR}/processed/heritage_overlays.geojson",
        help="Path to processed GeoJSON file",
    )
    parser.add_argument(
        "--destination",
        default=str(APP_DATA_PATH),
        help="Destination path within the application package",
    )
    return parser.parse_args(argv)


def _write_metadata(processed_path: Path) -> None:
    METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "source": str(processed_path),
        "published_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
    }
    METADATA_PATH.write_text(
        json_dumps(payload),
        encoding="utf-8",
    )


def json_dumps(payload: dict[str, str]) -> str:
    # Lightweight helper to avoid importing json in module scope when unused.
    import json

    return json.dumps(payload, indent=2)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    source = Path(args.source)
    destination = Path(args.destination)
    if not source.exists():
        raise FileNotFoundError(source)

    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    _write_metadata(source.resolve())
    print(f"Copied {source} to {destination}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
