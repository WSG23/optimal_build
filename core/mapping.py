"""Mapping utilities for canonical regulations."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

try:  # pragma: no cover - prefer PyYAML when present
    import yaml  # type: ignore
except Exception:  # pragma: no cover - fallback parser
    yaml = None  # type: ignore[assignment]

from .canonical_models import CanonicalReg

GLOBAL_MAPPING_FILE = Path(__file__).resolve().parent / "global_categories.yaml"


def load_yaml(path: Path) -> dict:
    """Load a YAML file from disk."""

    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        if yaml is None:
            return _parse_simple_yaml(handle.read())
        return yaml.safe_load(handle) or {}


def _parse_simple_yaml(contents: str) -> dict:
    """Parse a minimal subset of YAML for offline environments."""

    result: dict[str, dict] = {"categories": {}}
    current_section: dict[str, dict] | None = None
    current_key: str | None = None
    for line in contents.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if not line.startswith(" "):
            if stripped.endswith(":"):
                key = stripped[:-1]
                if key == "categories":
                    current_section = result["categories"]
                else:
                    current_section = result.setdefault(key, {})  # type: ignore[assignment]
                current_key = None
            continue
        if current_section is None:
            continue
        indent = len(line) - len(stripped)
        if indent == 2 and stripped.endswith(":"):
            current_key = stripped[:-1]
            current_section[current_key] = {}
        elif indent == 4 and stripped.startswith("keywords:"):
            current_section.setdefault(current_key or "", {})["keywords"] = []
        elif indent == 6 and stripped.startswith("- "):
            if current_key is None:
                continue
            keywords = current_section.setdefault(current_key, {}).setdefault(
                "keywords", []
            )
            keywords.append(stripped[2:].strip().strip('"'))
        elif indent == 4 and ":" in stripped:
            if current_key is None:
                continue
            field, value = stripped.split(":", 1)
            current_section.setdefault(current_key, {})[
                field.strip()
            ] = value.strip().strip('"')
    return result


def merge_mappings(global_map: dict, override_map: dict) -> dict:
    """Merge override mappings into the global mapping definition."""

    merged = {"categories": {}}
    global_categories = global_map.get("categories", {})
    override_categories = override_map.get("categories", {})
    for key, payload in global_categories.items():
        merged["categories"][key] = payload.copy()
    for key, payload in override_categories.items():
        base = merged["categories"].setdefault(key, {})
        for field, value in payload.items():
            if field == "keywords":
                existing = set(base.get("keywords", []))
                existing.update(value or [])
                base["keywords"] = sorted(existing)
            else:
                base[field] = value
    return merged


def apply_mapping(
    definition: dict, regulations: Iterable[CanonicalReg]
) -> list[CanonicalReg]:
    """Apply keyword-based mapping rules to the provided regulations."""

    categories = definition.get("categories", {})
    keyword_map = {
        key: set(map(str.lower, payload.get("keywords", [])))
        for key, payload in categories.items()
    }
    mapped: list[CanonicalReg] = []
    for reg in regulations:
        text_lower = f"{reg.title}\n{reg.text}".lower()
        tags = set(reg.global_tags)
        for key, keywords in keyword_map.items():
            if any(keyword in text_lower for keyword in keywords):
                tags.add(key)
        reg.global_tags = sorted(tags)
        mapped.append(reg)
    return mapped


def load_and_apply_mappings(
    regulations: Iterable[CanonicalReg], override_path: Path | None
) -> list[CanonicalReg]:
    """Load mappings from disk and apply them to the regulations."""

    global_map = load_yaml(GLOBAL_MAPPING_FILE)
    override_map: dict = {}
    if override_path is not None:
        override_map = load_yaml(override_path)
    merged = merge_mappings(global_map, override_map)
    return apply_mapping(merged, regulations)
