from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import pandas as pd


class GroupMatrixBuilder:
    """
    Build group/document and group/item matrices for BiblioGroup.

    Supports:
    - one group per document
    - multiple overlapping groups per document
    - semicolon/comma/pipe separated memberships
    - configurable group and item columns
    """

    DEFAULT_SEPARATORS = (";", "|", ",")

    def __init__(
        self,
        df: pd.DataFrame,
        group_column: str = "group",
    ) -> None:
        self.df = df.copy()
        self.group_column = group_column

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build_group_matrix(
        self,
        group_column: str | None = None,
    ) -> pd.DataFrame:
        """
        Build a document × group membership matrix.

        Example:

            document     group
            A            Iran;USA
            B            Iran
            C            USA;Germany

        becomes:

                  Germany  Iran  USA
            A        0       1    1
            B        0       1    0
            C        1       0    1
        """

        column = group_column or self.group_column

        if column not in self.df.columns:
            raise ValueError(
                f"Group column '{column}' was not found in dataframe."
            )

        memberships = self.df[column].apply(self._parse_memberships)

        groups = sorted(
            {
                group
                for row in memberships
                for group in row
                if group
            }
        )

        if not groups:
            return pd.DataFrame(
                index=self.df.index,
                columns=[],
                dtype=int,
            )

        matrix = pd.DataFrame(
            0,
            index=self.df.index,
            columns=groups,
            dtype=int,
        )

        for index, row_groups in memberships.items():
            for group in row_groups:
                matrix.loc[index, group] = 1

        return matrix

    def build_item_matrix(
        self,
        item_column: str,
        separators: Iterable[str] | None = None,
    ) -> pd.DataFrame:
        """
        Build a document × item binary matrix.

        Example:

            document    keywords
            A           AI;Library
            B           AI
            C           Data Mining;AI

        becomes:

                  AI  Data Mining  Library
            A      1       0          1
            B      1       0          0
            C      1       1          0
        """

        if item_column not in self.df.columns:
            raise ValueError(
                f"Item column '{item_column}' was not found in dataframe."
            )

        separators = tuple(
            separators or self.DEFAULT_SEPARATORS
        )

        parsed_items = self.df[item_column].apply(
            lambda value: self._parse_values(
                value,
                separators=separators,
            )
        )

        items = sorted(
            {
                item
                for row in parsed_items
                for item in row
                if item
            }
        )

        if not items:
            return pd.DataFrame(
                index=self.df.index,
                columns=[],
                dtype=int,
            )

        matrix = pd.DataFrame(
            0,
            index=self.df.index,
            columns=items,
            dtype=int,
        )

        for index, row_items in parsed_items.items():
            for item in row_items:
                matrix.loc[index, item] = 1

        return matrix

    def build_group_item_matrix(
        self,
        item_column: str,
        group_column: str | None = None,
        separators: Iterable[str] | None = None,
    ) -> pd.DataFrame:
        """
        Build a group × item association matrix.

        A document belonging to multiple groups contributes to
        every applicable group.

        The matrix contains document counts for each
        group-item combination.
        """

        group_matrix = self.build_group_matrix(
            group_column=group_column,
        )

        item_matrix = self.build_item_matrix(
            item_column=item_column,
            separators=separators,
        )

        if group_matrix.empty or item_matrix.empty:
            return pd.DataFrame(
                index=group_matrix.columns,
                columns=item_matrix.columns,
                dtype=int,
            )

        # Align documents explicitly before multiplication.
        common_index = group_matrix.index.intersection(
            item_matrix.index
        )

        group_matrix = group_matrix.loc[common_index]
        item_matrix = item_matrix.loc[common_index]

        return group_matrix.T.dot(item_matrix).astype(int)

    def build_group_document_counts(
        self,
        group_column: str | None = None,
    ) -> pd.Series:
        """
        Count documents belonging to each group.

        With overlapping memberships, one document may contribute
        to more than one group.
        """

        matrix = self.build_group_matrix(
            group_column=group_column,
        )

        if matrix.empty:
            return pd.Series(dtype=int)

        return matrix.sum(axis=0).astype(int)

    # ------------------------------------------------------------------
    # Parsing helpers
    # ------------------------------------------------------------------

    @classmethod
    def _parse_memberships(
        cls,
        value: Any,
    ) -> list[str]:
        """
        Parse group memberships.

        Handles:
        - None
        - NaN
        - strings
        - lists
        - tuples
        - sets
        """

        return cls._parse_values(
            value,
            separators=cls.DEFAULT_SEPARATORS,
        )

    @staticmethod
    def _parse_values(
        value: Any,
        separators: Iterable[str],
    ) -> list[str]:
        if value is None:
            return []

        if isinstance(value, float) and pd.isna(value):
            return []

        if isinstance(value, (list, tuple, set)):
            values = value
        else:
            values = [value]

        result: list[str] = []

        for raw_value in values:
            if raw_value is None:
                continue

            if isinstance(raw_value, float) and pd.isna(raw_value):
                continue

            text = str(raw_value).strip()

            if not text:
                continue

            # Normalize separators.
            for separator in separators:
                if separator != ";":
                    text = text.replace(separator, ";")

            parts = text.split(";")

            for part in parts:
                cleaned = part.strip()

                if cleaned:
                    result.append(cleaned)

        # Preserve uniqueness within a single document.
        # A document mentioning the same group/item twice
        # should still count as one membership.
        return list(dict.fromkeys(result))