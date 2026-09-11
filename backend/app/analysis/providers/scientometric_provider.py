from collections import Counter
from itertools import combinations
from pathlib import Path
from typing import Any

import pandas as pd

from backend.app.analysis.parsers.wos_parser import parse_wos_tagged_text


class SciAINativeProvider:
    """
    Native scientometric analysis provider for SciAI.

    Supports common Scopus CSV and Web of Science tagged-text fields.
    """

    version = "1.1.0"
    package = "SciAI Native"

    def __init__(self, capability: str) -> None:
        self.capability = capability

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def _load(self, file_path: str | Path) -> pd.DataFrame:
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Dataset file not found: {path}"
            )

        suffix = path.suffix.lower()

        if suffix in {".txt", ".ciw"}:
            return parse_wos_tagged_text(path)

        if suffix == ".csv":
            return pd.read_csv(
                path,
                encoding="utf-8-sig",
                low_memory=False,
            )

        raise ValueError(
            f"Unsupported dataset file format: {suffix}"
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _find_column(
        df: pd.DataFrame,
        candidates: list[str],
    ) -> str | None:
        """
        Return the first matching column from the candidate list.

        Matching is first attempted exactly, then case-insensitively
        after trimming whitespace.
        """

        for candidate in candidates:
            if candidate in df.columns:
                return candidate

        normalized = {
            str(column).strip().lower(): column
            for column in df.columns
        }

        for candidate in candidates:
            key = candidate.strip().lower()
            if key in normalized:
                return normalized[key]

        return None

    @staticmethod
    def _numeric_series(
        df: pd.DataFrame,
        candidates: list[str],
    ) -> pd.Series | None:
        column = SciAINativeProvider._find_column(
            df,
            candidates,
        )

        if column is None:
            return None

        return pd.to_numeric(
            df[column],
            errors="coerce",
        ).fillna(0)

    @staticmethod
    def _split_authors(value: Any) -> list[str]:
        """
        Split author strings from common Scopus/WoS formats.

        Examples:
        - "Smith, J.; Jones, A."
        - "Smith, J. and Jones, A."
        - "Smith J; Jones A"
        """

        if value is None:
            return []

        if pd.isna(value):
            return []

        text = str(value).strip()

        if not text:
            return []

        # Scopus normally uses semicolon between authors.
        if ";" in text:
            parts = text.split(";")
        elif " and " in text:
            parts = text.split(" and ")
        else:
            parts = [text]

        authors: list[str] = []

        for part in parts:
            author = part.strip()

            if author:
                authors.append(author)

        return authors

    @staticmethod
    def _split_keywords(value: Any) -> list[str]:
        """
        Split keyword values from Scopus/WoS formats.
        """

        if value is None:
            return []

        if pd.isna(value):
            return []

        text = str(value).strip()

        if not text:
            return []

        # Scopus keyword fields normally use semicolons.
        # Some imported datasets may use commas or newlines.
        raw_keywords = text.replace("\n", ";").split(";")

        keywords: list[str] = []

        for keyword in raw_keywords:
            keyword = keyword.strip()

            if keyword:
                keywords.append(keyword)

        return keywords

    # ------------------------------------------------------------------
    # 1. Document count
    # ------------------------------------------------------------------

    def document_count(
        self,
        df: pd.DataFrame,
        parameters: dict[str, Any],
    ) -> list[dict[str, Any]]:

        return [
            {
                "metric": "document_count",
                "value": int(len(df)),
            }
        ]

    # ------------------------------------------------------------------
    # 2. Publication year distribution
    # ------------------------------------------------------------------

    def year_distribution(
        self,
        df: pd.DataFrame,
        parameters: dict[str, Any],
    ) -> list[dict[str, Any]]:

        column = self._find_column(
            df,
            [
                "year",
                "Year",
                "PY",
                "publication_year",
                "Publication Year",
            ],
        )

        if column is None:
            return []

        years = pd.to_numeric(
            df[column],
            errors="coerce",
        ).dropna()

        counter = Counter(
            int(year)
            for year in years
        )

        return [
            {
                "year": year,
                "count": count,
            }
            for year, count in sorted(counter.items())
        ]

    # ------------------------------------------------------------------
    # 3. Author productivity
    # ------------------------------------------------------------------

    def author_productivity(
        self,
        df: pd.DataFrame,
        parameters: dict[str, Any],
    ) -> list[dict[str, Any]]:

        column = self._find_column(
            df,
            [
                "author",
                "authors",
                "Authors",
                "AU",
                "Author",
            ],
        )

        if column is None:
            return []

        counter: Counter[str] = Counter()

        for value in df[column].fillna("").astype(str):
            authors = self._split_authors(value)

            for author in authors:
                counter[author] += 1

        limit = parameters.get("limit")

        items = counter.most_common(
            int(limit) if limit else None
        )

        return [
            {
                "author": author,
                "documents": int(count),
            }
            for author, count in items
        ]

    # ------------------------------------------------------------------
    # 4. Total citations
    # ------------------------------------------------------------------

    def citation_total(
        self,
        df: pd.DataFrame,
        parameters: dict[str, Any],
    ) -> list[dict[str, Any]]:

        citations = self._numeric_series(
            df,
            [
                "citation",
                "citations",
                "times_cited",
                "Times Cited",
                "Cited by",
                "TC",
            ],
        )

        if citations is None:
            return []

        total = int(citations.sum())

        return [
            {
                "metric": "citation_total",
                "value": total,
            }
        ]

    # ------------------------------------------------------------------
    # 5. Average citations
    # ------------------------------------------------------------------

    def citation_average(
        self,
        df: pd.DataFrame,
        parameters: dict[str, Any],
    ) -> list[dict[str, Any]]:

        citations = self._numeric_series(
            df,
            [
                "citation",
                "citations",
                "times_cited",
                "Times Cited",
                "Cited by",
                "TC",
            ],
        )

        if citations is None:
            return []

        average = (
            float(citations.mean())
            if len(citations) > 0
            else 0.0
        )

        return [
            {
                "metric": "citation_average",
                "value": round(average, 4),
            }
        ]

    # ------------------------------------------------------------------
    # 6. Citation distribution
    # ------------------------------------------------------------------

    def citation_distribution(
        self,
        df: pd.DataFrame,
        parameters: dict[str, Any],
    ) -> list[dict[str, Any]]:

        citations = self._numeric_series(
            df,
            [
                "citation",
                "citations",
                "times_cited",
                "Times Cited",
                "Cited by",
                "TC",
            ],
        )

        if citations is None:
            return []

        counter = Counter(
            int(value)
            for value in citations
        )

        return [
            {
                "citations": citation_count,
                "documents": document_count,
            }
            for citation_count, document_count
            in sorted(counter.items())
        ]

    # ------------------------------------------------------------------
    # 7. Source productivity
    # ------------------------------------------------------------------

    def source_productivity(
        self,
        df: pd.DataFrame,
        parameters: dict[str, Any],
    ) -> list[dict[str, Any]]:

        column = self._find_column(
            df,
            [
                "journal",
                "source",
                "Source",
                "Source title",
                "source_title",
                "abbrev_source_title",
                "Abbreviated Source Title",
                "SO",
            ],
        )

        if column is None:
            return []

        counter: Counter[str] = Counter()

        for value in df[column].fillna("").astype(str):
            source = value.strip()

            if source:
                counter[source] += 1

        limit = parameters.get("limit")

        items = counter.most_common(
            int(limit) if limit else None
        )

        return [
            {
                "source": source,
                "documents": int(count),
            }
            for source, count in items
        ]

    # ------------------------------------------------------------------
    # 8. Keyword frequency
    # ------------------------------------------------------------------

    def keyword_frequency(
        self,
        df: pd.DataFrame,
        parameters: dict[str, Any],
    ) -> list[dict[str, Any]]:

        keyword_columns = [
            "keywords",
            "author_keywords",
            "keyword",
            "Author Keywords",
            "Index Keywords",
            "DE",
            "ID",
        ]

        selected_columns = [
            column
            for column in keyword_columns
            if column in df.columns
        ]

        # Case-insensitive fallback.
        if not selected_columns:
            normalized = {
                str(column).strip().lower(): column
                for column in df.columns
            }

            for candidate in keyword_columns:
                key = candidate.strip().lower()

                if key in normalized:
                    selected_columns.append(
                        normalized[key]
                    )

        if not selected_columns:
            return []

        counter: Counter[str] = Counter()

        for column in selected_columns:

            for value in df[column].fillna("").astype(str):

                keywords = self._split_keywords(value)

                for keyword in keywords:
                    keyword = keyword.strip().lower()

                    if keyword:
                        counter[keyword] += 1

        limit = parameters.get("limit")

        items = counter.most_common(
            int(limit) if limit else None
        )

        return [
            {
                "keyword": keyword,
                "frequency": int(count),
            }
            for keyword, count in items
        ]

    # ------------------------------------------------------------------
    # 9. Author co-authorship
    # ------------------------------------------------------------------

    def author_co_authorship(
        self,
        df: pd.DataFrame,
        parameters: dict[str, Any],
    ) -> list[dict[str, Any]]:

        column = self._find_column(
            df,
            [
                "author",
                "authors",
                "Authors",
                "AU",
                "Author",
            ],
        )

        if column is None:
            return []

        counter: Counter[tuple[str, str]] = Counter()

        for value in df[column].fillna("").astype(str):

            authors = self._split_authors(value)

            # Remove duplicate authors within a document.
            authors = list(dict.fromkeys(authors))

            if len(authors) < 2:
                continue

            for author_a, author_b in combinations(
                sorted(authors),
                2,
            ):
                counter[(author_a, author_b)] += 1

        limit = parameters.get("limit")

        items = counter.most_common(
            int(limit) if limit else None
        )

        return [
            {
                "author_1": author_a,
                "author_2": author_b,
                "co_authored_documents": int(count),
            }
            for (author_a, author_b), count in items
        ]

    # ------------------------------------------------------------------
    # Capability dispatcher
    # ------------------------------------------------------------------

    def execute(
        self,
        file_path: str | Path,
        parameters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:

        parameters = parameters or {}

        df = self._load(file_path)

        methods = {
            "document.count": self.document_count,
            "publication.year_distribution": self.year_distribution,
            "author.productivity": self.author_productivity,
            "citation.total": self.citation_total,
            "citation.average": self.citation_average,
            "citation.distribution": self.citation_distribution,
            "source.productivity": self.source_productivity,
            "keyword.frequency": self.keyword_frequency,
            "author.co_authorship": self.author_co_authorship,
        }

        method = methods.get(self.capability)

        if method is None:
            raise ValueError(
                f"Unsupported SciAI Native capability: "
                f"'{self.capability}'"
            )

        records = method(
            df,
            parameters,
        )

        return {
            "status": "completed",
            "capability": self.capability,
            "provider": self.package,
            "package": self.package,
            "package_version": self.version,
            "parameters": parameters,
            "records": records,
            "count": len(records),
        }