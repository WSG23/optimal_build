"""Load transformed heritage data into the main heritage overlays file.

This script merges transformed heritage data into backend/app/data/heritage_overlays.geojson,
which is used by the application to provide heritage constraint information.

Usage:
    python -m scripts.heritage.load
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List


def load_heritage_overlays() -> None:
    """Load and merge all transformed heritage data into heritage_overlays.geojson."""
    # Define paths
    processed_dir = Path("data/heritage/processed")
    output_file = Path("backend/app/data/heritage_overlays.geojson")

    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Load existing heritage overlays if they exist
    existing_features: List[Dict[str, Any]] = []
    if output_file.exists():
        print(f"Loading existing heritage overlays from {output_file}...")
        with output_file.open("r") as f:
            existing_data = json.load(f)
            existing_features = existing_data.get("features", [])
        print(f"   Found {len(existing_features)} existing features")

    # Track sources we've already loaded
    existing_sources = {
        feat["properties"].get("source") for feat in existing_features if "properties" in feat
    }

    # Load all processed heritage datasets
    new_features: List[Dict[str, Any]] = []
    if processed_dir.exists():
        for geojson_file in processed_dir.glob("*.geojson"):
            print(f"Loading {geojson_file.name}...")
            with geojson_file.open("r") as f:
                data = json.load(f)
                features = data.get("features", [])

                # Check if this source is already in existing features
                if features and features[0].get("properties", {}).get("source") in existing_sources:
                    print(
                        f"   ⚠️  Skipping {geojson_file.name} - already in heritage overlays"
                    )
                    continue

                new_features.extend(features)
                print(f"   Added {len(features)} features from {geojson_file.name}")
    else:
        print(f"⚠️  No processed heritage data found in {processed_dir}")

    # Merge existing and new features
    all_features = existing_features + new_features

    # Create final GeoJSON structure
    heritage_overlays = {
        "type": "FeatureCollection",
        "features": all_features,
        "metadata": {
            "description": "Heritage overlays for Singapore properties",
            "sources": list({feat["properties"].get("source") for feat in all_features if "properties" in feat}),
            "feature_count": len(all_features),
        },
    }

    # Write merged data
    print(f"\nWriting heritage overlays to {output_file}...")
    with output_file.open("w") as f:
        json.dump(heritage_overlays, f, indent=2)

    print(f"✅ Successfully loaded heritage overlays")
    print(f"   Total features: {len(all_features)}")
    print(f"   New features: {len(new_features)}")
    print(f"   Sources: {', '.join(heritage_overlays['metadata']['sources'])}")
    print(f"   Output: {output_file}")


def main() -> None:
    """Main entry point for heritage data loading."""
    try:
        load_heritage_overlays()
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
