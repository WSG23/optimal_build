"""Helpers used when uploading analytics data via tests."""

from __future__ import annotations

import unicodedata
from typing import Iterable, List, Mapping, MutableMapping

try:
    import pandas as pd  # type: ignore
    from pandas import DataFrame  # type: ignore
except Exception:  # pragma: no cover - pandas is optional for the tests
    pd = None
    DataFrame = None  # type: ignore


def _normalise_key(key: str) -> str:
    normalised = unicodedata.normalize("NFKD", key)
    ascii_key = normalised.encode("ascii", "ignore").decode("ascii")
    return ascii_key.strip().lower().replace(" ", "_")


def normalize_column_names(records: Iterable[Mapping[str, object]]) -> List[MutableMapping[str, object]]:
    """Return a list with normalised dictionary keys."""

    normalised: List[MutableMapping[str, object]] = []
    for record in records:
        converted: MutableMapping[str, object] = {}
        for key, value in record.items():
            converted[_normalise_key(str(key))] = value
        normalised.append(converted)
    return normalised


def validate_dataframe_rows(df: "DataFrame | Iterable[Mapping[str, object]]") -> bool:
    """Validate that rows contain no empty mandatory fields."""

    rows: Iterable[Mapping[str, object]]
    if pd is not None and DataFrame is not None and isinstance(df, DataFrame):
        rows = df.to_dict(orient="records")
    else:
        rows = df  # type: ignore[assignment]

    for row in rows:
        if any(value in (None, "") for value in row.values()):
            return False
    return True
