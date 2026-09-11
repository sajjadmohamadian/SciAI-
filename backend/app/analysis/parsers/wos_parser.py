from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


def _clean(value: str) -> str:
    """Normalize a WoS field value."""
    return " ".join(value.strip().split())


def _join_values(values: list[str], separator: str) -> str:
    """Join repeated WoS fields while removing empty/duplicate values."""
    result: list[str] = []
    seen: set[str] = set()

    for value in values:
        value = _clean(value)
        if not value:
            continue

        if value not in seen:
            seen.add(value)
            result.append(value)

    return separator.join(result)


def _parse_records(text: str) -> list[dict[str, list[str]]]:
    """Parse WoS tagged text into raw records."""

    records: list[dict[str, list[str]]] = []
    current: dict[str, list[str]] = {}
    current_tag: str | None = None

    for raw_line in text.splitlines():
        line = raw_line.rstrip()

        if line == "ER":
            if current:
                records.append(current)

            current = {}
            current_tag = None
            continue

        if line == "EF":
            break

        if not line.strip():
            continue

        # WoS tagged field: AU, TI, SO, etc.
        if len(line) >= 3 and line[:2].isupper() and line[2] == " ":
            tag = line[:2]
            value = line[3:].strip()

            current.setdefault(tag, []).append(value)
            current_tag = tag
            continue

        # Multiline continuation
        if current_tag is not None:
            current[current_tag].append(line.strip())

    if current:
        records.append(current)

    return records


def _normalize_record(record: dict[str, list[str]]) -> dict[str, Any]:
    """Convert one WoS record to the canonical PyBibX schema."""

    de_keywords = _join_values(record.get("DE", []), ";")
    id_keywords = _join_values(record.get("ID", []), ";")

    all_keywords = _join_values(
        [de_keywords, id_keywords],
        ";",
    )

    journal = _clean(
        record.get("SO", [""])[0]
    )

    return {
        "year": _clean(record.get("PY", [""])[0]),
        "document_type": _clean(record.get("DT", [""])[0]),
        "note": _clean(record.get("TC", ["0"])[0]),
        "references": _join_values(record.get("CR", []), ";"),
        "author": _join_values(record.get("AU", []), " and "),
        "keywords": all_keywords,
        "author_keywords": de_keywords,
        "source": "wos",
        "abbrev_source_title": journal,
        "journal": journal,
        "language": _clean(record.get("LA", [""])[0]),
        "title": _join_values(record.get("TI", []), " "),
        "abstract": _join_values(record.get("AB", []), " "),
        "affiliation_": _join_values(
            record.get("C1", []),
            ";",
        ),
        "countries": _join_values(
            record.get("CU", []),
            ";",
        ),
        "full_authors": _join_values(
            record.get("AF", []),
            ";",
        ),
        "doi": _join_values(
            record.get("DI", []),
            ";",
        ),
    }


COLUMNS = [
    "year",
    "document_type",
    "note",
    "references",
    "author",
    "keywords",
    "author_keywords",
    "source",
    "abbrev_source_title",
    "journal",
    "language",
    "title",
    "abstract",
    "affiliation_",
    "countries",
    "full_authors",
    "doi",
]


def parse_wos_tagged_text(file_path: str | Path) -> pd.DataFrame:
    """
    Parse a Web of Science Tagged Text export
    such as savedrecs.txt.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"WoS file not found: {path}"
        )

    text = path.read_text(
        encoding="utf-8-sig",
        errors="replace",
    )

    records = _parse_records(text)

    normalized = [
        _normalize_record(record)
        for record in records
    ]

    df = pd.DataFrame(
        normalized,
        columns=COLUMNS,
    )

    df["affiliation_"] = (
        df["affiliation_"]
        .fillna("")
        .astype(str)
    )

    df["source"] = (
        df["source"]
        .fillna("wos")
        .astype(str)
    )

    df["journal"] = (
        df["journal"]
        .fillna("")
        .astype(str)
    )

    return df


def parse_wos_text(text: str) -> pd.DataFrame:
    """
    Parse WoS Tagged Text directly from a string.
    """

    records = _parse_records(text)

    normalized = [
        _normalize_record(record)
        for record in records
    ]

    df = pd.DataFrame(
        normalized,
        columns=COLUMNS,
    )

    df["affiliation_"] = (
        df["affiliation_"]
        .fillna("")
        .astype(str)
    )

    df["source"] = (
        df["source"]
        .fillna("wos")
        .astype(str)
    )

    df["journal"] = (
        df["journal"]
        .fillna("")
        .astype(str)
    )

    return df