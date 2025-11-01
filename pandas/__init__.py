"""Lightweight pandas compatibility layer for tests."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any, Dict, List

__all__ = ["DataFrame", "Series", "__version__", "to_datetime"]

__version__ = "0.0-test-stub"


class Series(list):
    """Minimal series implementation backed by ``list``."""

    name: str | None = None

    def to_list(self) -> list[Any]:
        return list(self)


class DataFrame:
    """Very small subset of pandas.DataFrame used in the tests."""

    def __init__(
        self,
        data: Iterable[Mapping[str, Any]] | Mapping[str, Sequence[Any]] | Sequence[Sequence[Any]],
        columns: Sequence[str] | None = None,
    ) -> None:
        self._records: list[dict[str, Any]] = []
        if isinstance(data, Mapping):
            keys = list(data.keys())
            length = max((len(values) for values in data.values()), default=0)
            for index in range(length):
                row: dict[str, Any] = {}
                for key in keys:
                    values = list(data[key])
                    row[key] = values[index] if index < len(values) else None
                self._records.append(row)
            self.columns = columns or keys
        elif isinstance(data, Iterable) and not isinstance(data, (str, bytes)):
            rows = list(data)
            if rows and isinstance(rows[0], Mapping):
                self._records = [dict(row) for row in rows]  # type: ignore[arg-type]
                self.columns = columns or list(self._records[0].keys())
            else:
                cols = list(columns or [])
                for row in rows:
                    values = list(row)  # type: ignore[arg-type]
                    record: dict[str, Any] = {}
                    for idx, value in enumerate(values):
                        key = cols[idx] if idx < len(cols) else str(idx)
                        record[key] = value
                    self._records.append(record)
                self.columns = cols or [str(i) for i in range(len(self._records[0]))] if self._records else []
        else:
            self.columns = list(columns or [])

    def to_dict(self, orient: str = "records") -> List[Dict[str, Any]]:
        if orient != "records":
            raise ValueError("stub DataFrame only supports orient='records'")
        return [dict(row) for row in self._records]

    def __iter__(self):
        return iter(self._records)

    def __len__(self) -> int:
        return len(self._records)


def to_datetime(values: Sequence[Any]) -> Series:
    series = Series(values)
    return series
