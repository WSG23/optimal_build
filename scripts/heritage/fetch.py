"""Download heritage datasets from data.gov.sg or OneMap themes."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any
from urllib import request

from . import DEFAULT_DATA_DIR

DATASETS: Mapping[str, Mapping[str, str]] = {
    "ura_conservation": {
        "dataset_id": "d_f105660dd749c0aafa1a858f435603f2",
        "description": "URA Conservation Areas (polygons)",
        "filename": "ura_conservation.zip",
    },
    "nhb_historic_sites": {
        "dataset_id": "d_eb325aa046af62849daca32acdfef17b",
        "description": "NHB Historic Sites",
        "filename": "nhb_historic_sites.geojson",
    },
    "nhb_heritage_trails": {
        "dataset_id": "d_e12a738c0dab18d7ab9b60c255ba697d",
        "theme_query": "Heritage_Trails",
        "description": "NHB Heritage Trails",
        "filename": "nhb_heritage_trails.geojson",
    },
    "nhb_monuments": {
        "theme_query": "National_Monuments",
        "description": "NHB National Monuments (OneMap theme)",
        "filename": "nhb_monuments.geojson",
    },
}

POLL_ENDPOINT = (
    "https://api-open.data.gov.sg/v1/public/api/datasets/{dataset_id}/poll-download"
)
ONEMAP_DOWNLOAD_ENDPOINT = "https://developers.onemap.sg/privateapi/dataapi/download"


def _download_file(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with request.urlopen(url, timeout=60) as response, destination.open("wb") as handle:
        while True:
            chunk = response.read(8192)
            if not chunk:
                break
            handle.write(chunk)


def _poll_dataset(dataset_id: str) -> str:
    with request.urlopen(
        POLL_ENDPOINT.format(dataset_id=dataset_id), timeout=30
    ) as response:
        payload: Mapping[str, Any] = json.loads(response.read().decode("utf-8"))
    if payload.get("code") != 0:
        raise RuntimeError(payload.get("errMsg") or "Failed to poll dataset")
    data = payload.get("data") or {}
    url = data.get("url")
    if not url:
        raise RuntimeError("Poll response missing download URL")
    return str(url)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download heritage datasets from data.gov.sg or OneMap themes"
    )
    parser.add_argument(
        "--dataset",
        choices=sorted(DATASETS.keys()),
        default="ura_conservation",
        help="Dataset key to download",
    )
    parser.add_argument(
        "--output-dir",
        default=f"{DEFAULT_DATA_DIR}/raw",
        help="Directory to store downloaded files (default: %(default)s)",
    )
    parser.add_argument(
        "--print-metadata",
        action="store_true",
        help="Print dataset description after download",
    )
    parser.add_argument(
        "--theme-query",
        help=(
            "Download a OneMap theme (overrides --dataset). "
            "Requires --onemap-token or ONEMAP_TOKEN env var."
        ),
    )
    parser.add_argument(
        "--output",
        help="Override output filename when using --theme-query.",
    )
    parser.add_argument(
        "--onemap-token",
        help="OneMap access token (optional if ONEMAP_TOKEN env var is set).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if args.theme_query:
        token = args.onemap_token or os.environ.get("ONEMAP_TOKEN")
        if not token:
            print(
                "OneMap token required. Provide via --onemap-token or ONEMAP_TOKEN env var.",
                file=sys.stderr,
            )
            return 1
        output_dir = Path(args.output_dir)
        filename = args.output or f"{args.theme_query.lower()}.geojson"
        destination = output_dir / filename
        query = args.theme_query
        download_url = (
            f"{ONEMAP_DOWNLOAD_ENDPOINT}"
            f"?datasetName={query}"
            f"&token={token}"
            "&outputFormat=GeoJSON"
        )
        try:
            _download_file(download_url, destination)
        except Exception as exc:  # pragma: no cover - CLI convenience
            print(f"Failed to download OneMap theme '{query}': {exc}", file=sys.stderr)
            return 1
        if args.print_metadata:
            metadata = {
                "dataset": query,
                "description": f"OneMap theme download ({query})",
                "destination": str(destination),
            }
            print(json.dumps(metadata, indent=2))
        return 0

    dataset = DATASETS[args.dataset]
    output_dir = Path(args.output_dir)
    destination = output_dir / dataset["filename"]

    try:
        if "dataset_id" in dataset:
            download_url = _poll_dataset(dataset["dataset_id"])
            _download_file(download_url, destination)
        elif "theme_query" in dataset:
            token = args.onemap_token or os.environ.get("ONEMAP_TOKEN")
            if not token:
                raise RuntimeError(
                    "OneMap token required for theme downloads. "
                    "Provide via --onemap-token or ONEMAP_TOKEN env var."
                )
            query = dataset["theme_query"]
            download_url = (
                f"{ONEMAP_DOWNLOAD_ENDPOINT}"
                f"?datasetName={query}"
                f"&token={token}"
                "&outputFormat=GeoJSON"
            )
            _download_file(download_url, destination)
        else:
            raise RuntimeError(
                f"No download method configured for dataset '{args.dataset}'"
            )
    except Exception as exc:  # pragma: no cover - CLI convenience
        print(f"Failed to download '{args.dataset}': {exc}", file=sys.stderr)
        return 1

    if args.print_metadata:
        metadata = {
            "dataset": args.dataset,
            "description": dataset["description"],
            "destination": str(destination),
        }
        print(json.dumps(metadata, indent=2))

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
