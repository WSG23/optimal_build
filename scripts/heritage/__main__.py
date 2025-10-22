"""Run heritage ingestion commands."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import (
    DEFAULT_DATA_DIR,
    fetch as fetch_module,
    load as load_module,
    transform as transform_module,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Heritage ingestion toolkit")
    subparsers = parser.add_subparsers(dest="command", required=True)

    fetch_parser = subparsers.add_parser("fetch", help="Download raw heritage datasets")
    fetch_parser.add_argument(
        "--dataset",
        choices=fetch_module.DATASETS.keys(),
        default="ura_conservation",
        help="Dataset key to download",
    )
    fetch_parser.add_argument(
        "--output-dir",
        default=f"{DEFAULT_DATA_DIR}/raw",
        help="Directory to store downloaded files",
    )
    fetch_parser.add_argument(
        "--print-metadata",
        action="store_true",
        help="Print metadata after download",
    )

    transform_parser = subparsers.add_parser(
        "transform", help="Transform raw data into canonical overlays"
    )
    transform_parser.add_argument(
        "--dataset",
        choices=transform_module.TRANSFORMERS.keys(),
        default="ura_conservation",
        help="Dataset key to transform",
    )
    transform_parser.add_argument(
        "--input-path",
        default=f"{DEFAULT_DATA_DIR}/raw/ura_conservation",
        help="Path to raw dataset (directory or zip file)",
    )
    transform_parser.add_argument(
        "--output",
        default=f"{DEFAULT_DATA_DIR}/processed/heritage_overlays.geojson",
        help="Destination GeoJSON path",
    )

    load_parser = subparsers.add_parser(
        "load", help="Publish processed overlays to the application package"
    )
    load_parser.add_argument(
        "--source",
        default=f"{DEFAULT_DATA_DIR}/processed/heritage_overlays.geojson",
        help="Source GeoJSON path",
    )
    load_parser.add_argument(
        "--destination",
        default="backend/app/data/heritage_overlays.geojson",
        help="Destination path within the app",
    )

    pipeline_parser = subparsers.add_parser(
        "pipeline", help="Run fetch → transform → load for a dataset"
    )
    pipeline_parser.add_argument(
        "--dataset",
        choices=fetch_module.DATASETS.keys(),
        default="ura_conservation",
        help="Dataset key to process end-to-end",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    command = args.command
    if command == "fetch":
        return fetch_module.main(
            ["--dataset", args.dataset, "--output-dir", args.output_dir]
            + (["--print-metadata"] if args.print_metadata else [])
        )
    if command == "transform":
        return transform_module.main(
            [
                "--dataset",
                args.dataset,
                "--input-path",
                args.input_path,
                "--output",
                args.output,
            ]
        )
    if command == "load":
        return load_module.main(
            ["--source", args.source, "--destination", args.destination]
        )
    if command == "pipeline":
        dataset = args.dataset
        output_dir = f"{DEFAULT_DATA_DIR}/raw"
        processed_path = f"{DEFAULT_DATA_DIR}/processed/heritage_overlays.geojson"
        fetch_rc = fetch_module.main(["--dataset", dataset, "--output-dir", output_dir])
        if fetch_rc != 0:
            return fetch_rc
        if dataset not in transform_module.TRANSFORMERS:
            print(f"No transformer registered for dataset '{dataset}'", file=sys.stderr)
            return 1
        input_path = Path(output_dir) / fetch_module.DATASETS[dataset]["filename"]
        transform_rc = transform_module.main(
            [
                "--dataset",
                dataset,
                "--input-path",
                str(input_path),
                "--output",
                processed_path,
            ]
        )
        if transform_rc != 0:
            return transform_rc
        return load_module.main(["--source", processed_path])

    parser.print_help()
    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
