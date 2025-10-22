"""Transform heritage data from various sources into standardized GeoJSON format.

This script processes heritage data (KML, JSON, etc.) and transforms it into
a standardized GeoJSON format for loading into the heritage overlays.

Usage:
    python -m scripts.heritage.transform \\
        --dataset nhb_heritage_trails \\
        --input-path data/heritage/raw/nhb_heritage_trails.geojson
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List


def transform_nhb_heritage_trails(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Transform NHB Heritage Trails GeoJSON to standardized format.

    Args:
        input_data: Raw GeoJSON data from KML conversion

    Returns:
        Standardized GeoJSON FeatureCollection
    """
    features: List[Dict[str, Any]] = []

    # Process each feature in the input
    for feature in input_data.get("features", []):
        properties = feature.get("properties", {})
        geometry = feature.get("geometry", {})

        # Standardize properties
        standardized_feature = {
            "type": "Feature",
            "geometry": geometry,
            "properties": {
                "source": "nhb_heritage_trails",
                "name": properties.get("Name") or properties.get("name", "Unknown"),
                "description": properties.get("Description")
                or properties.get("description", ""),
                "type": "heritage_trail",
                # Preserve original properties for reference
                "original_properties": properties,
            },
        }

        features.append(standardized_feature)

    return {"type": "FeatureCollection", "features": features}


def transform_dataset(dataset: str, input_path: Path) -> Dict[str, Any]:
    """Transform a heritage dataset based on its type.

    Args:
        dataset: Dataset identifier (e.g., 'nhb_heritage_trails')
        input_path: Path to input GeoJSON file

    Returns:
        Standardized GeoJSON FeatureCollection

    Raises:
        ValueError: If dataset type is not supported
        FileNotFoundError: If input file doesn't exist
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    with input_path.open("r") as f:
        input_data = json.load(f)

    if dataset == "nhb_heritage_trails":
        return transform_nhb_heritage_trails(input_data)
    else:
        raise ValueError(f"Unsupported dataset: {dataset}")


def main() -> None:
    """Main entry point for heritage data transformation."""
    parser = argparse.ArgumentParser(
        description="Transform heritage data to standardized GeoJSON format"
    )
    parser.add_argument(
        "--dataset",
        required=True,
        help="Dataset identifier (e.g., 'nhb_heritage_trails')",
    )
    parser.add_argument(
        "--input-path",
        required=True,
        type=Path,
        help="Path to input GeoJSON file",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        help="Path to output file (default: data/heritage/processed/<dataset>.geojson)",
    )

    args = parser.parse_args()

    # Set default output path if not provided
    if args.output_path is None:
        output_dir = Path("data/heritage/processed")
        output_dir.mkdir(parents=True, exist_ok=True)
        args.output_path = output_dir / f"{args.dataset}.geojson"

    try:
        print(f"Transforming {args.dataset} from {args.input_path}...")
        transformed_data = transform_dataset(args.dataset, args.input_path)

        print(f"Writing transformed data to {args.output_path}...")
        with args.output_path.open("w") as f:
            json.dump(transformed_data, f, indent=2)

        feature_count = len(transformed_data.get("features", []))
        print(f"✅ Successfully transformed {feature_count} features")
        print(f"   Output: {args.output_path}")

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
