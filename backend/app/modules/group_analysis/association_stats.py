from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency, fisher_exact


class AssociationStatistics:
    """
    Statistical engine for BiblioGroup group-item analysis.

    Provides:
    - Pearson chi-square
    - expected frequencies
    - Pearson residuals
    - standardized residuals
    - Cramer's V
    - observed/expected association strength
    - log2 ratio
    - Jaccard
    - Dice
    - overlap coefficient
    - odds ratio for 2x2 tables
    - Fisher exact test for 2x2 tables
    - Benjamini-Hochberg FDR correction
    - Bonferroni correction
    """

    def __init__(self, association_matrix: pd.DataFrame) -> None:
        self.matrix = association_matrix.copy().astype(float)

    # ------------------------------------------------------------------
    # Basic frequencies
    # ------------------------------------------------------------------

    def expected_counts(self) -> pd.DataFrame:
        observed = self.matrix.to_numpy(dtype=float)

        if observed.size == 0:
            return pd.DataFrame(
                index=self.matrix.index,
                columns=self.matrix.columns,
                dtype=float,
            )

        row_totals = observed.sum(axis=1, keepdims=True)
        column_totals = observed.sum(axis=0, keepdims=True)
        total = observed.sum()

        if total <= 0:
            return pd.DataFrame(
                0.0,
                index=self.matrix.index,
                columns=self.matrix.columns,
            )

        expected = (row_totals @ column_totals) / total

        return pd.DataFrame(
            expected,
            index=self.matrix.index,
            columns=self.matrix.columns,
        )

    # ------------------------------------------------------------------
    # Pearson residuals
    # ------------------------------------------------------------------

    def pearson_residuals(self) -> pd.DataFrame:
        expected = self.expected_counts()

        observed = self.matrix.to_numpy(dtype=float)
        expected_values = expected.to_numpy(dtype=float)

        with np.errstate(divide="ignore", invalid="ignore"):
            residuals = (
                observed - expected_values
            ) / np.sqrt(expected_values)

        residuals = np.nan_to_num(
            residuals,
            nan=0.0,
            posinf=0.0,
            neginf=0.0,
        )

        return pd.DataFrame(
            residuals,
            index=self.matrix.index,
            columns=self.matrix.columns,
        )

    # ------------------------------------------------------------------
    # Chi-square
    # ------------------------------------------------------------------

    def chi_square(self) -> dict[str, Any]:
        values = self.matrix.to_numpy(dtype=float)

        if values.size == 0:
            return self._empty_chi_square()

        if values.shape[0] < 2 or values.shape[1] < 2:
            return self._empty_chi_square()

        if values.sum() <= 0:
            return self._empty_chi_square()

        try:
            statistic, p_value, dof, expected = chi2_contingency(
                values,
                correction=False,
            )

            return {
                "chi_square": float(statistic),
                "p_value": float(p_value),
                "degrees_of_freedom": int(dof),
                "expected": pd.DataFrame(
                    expected,
                    index=self.matrix.index,
                    columns=self.matrix.columns,
                ),
            }

        except (ValueError, RuntimeError):
            return self._empty_chi_square()

    # ------------------------------------------------------------------
    # Cramer's V
    # ------------------------------------------------------------------

    def cramers_v(self) -> float:
        result = self.chi_square()

        statistic = float(
            result["chi_square"]
        )

        n = float(self.matrix.to_numpy().sum())

        if n <= 0:
            return 0.0

        rows, columns = self.matrix.shape

        denominator = min(
            rows - 1,
            columns - 1,
        )

        if denominator <= 0:
            return 0.0

        return float(
            np.sqrt(
                statistic / (n * denominator)
            )
        )

    # ------------------------------------------------------------------
    # Association strength
    # ------------------------------------------------------------------

    def association_strength(self) -> pd.DataFrame:
        """
        Observed / Expected.

        > 1 = over-representation
        = 1 = expected
        < 1 = under-representation
        """

        expected = self.expected_counts()

        observed = self.matrix.to_numpy(dtype=float)
        expected_values = expected.to_numpy(dtype=float)

        with np.errstate(divide="ignore", invalid="ignore"):
            strength = observed / expected_values

        strength = np.nan_to_num(
            strength,
            nan=0.0,
            posinf=0.0,
            neginf=0.0,
        )

        return pd.DataFrame(
            strength,
            index=self.matrix.index,
            columns=self.matrix.columns,
        )

    # ------------------------------------------------------------------
    # Log ratio
    # ------------------------------------------------------------------

    def log_ratio(self) -> pd.DataFrame:
        """
        log2(observed / expected).

        Positive = over-represented
        Negative = under-represented
        Zero = approximately expected
        """

        expected = self.expected_counts()

        observed = self.matrix.to_numpy(dtype=float)
        expected_values = expected.to_numpy(dtype=float)

        with np.errstate(divide="ignore", invalid="ignore"):
            ratio = np.log2(
                observed / expected_values
            )

        ratio = np.nan_to_num(
            ratio,
            nan=0.0,
            posinf=0.0,
            neginf=0.0,
        )

        return pd.DataFrame(
            ratio,
            index=self.matrix.index,
            columns=self.matrix.columns,
        )

    # ------------------------------------------------------------------
    # Similarity between groups
    # ------------------------------------------------------------------

    def similarity(self) -> dict[str, dict[str, dict[str, float]]]:
        groups = list(self.matrix.index)

        group_sets = {
            group: {
                item
                for item, value in self.matrix.loc[group].items()
                if value > 0
            }
            for group in groups
        }

        jaccard: dict[str, dict[str, float]] = {}
        dice: dict[str, dict[str, float]] = {}
        overlap: dict[str, dict[str, float]] = {}

        for group_a in groups:
            jaccard[group_a] = {}
            dice[group_a] = {}
            overlap[group_a] = {}

            set_a = group_sets[group_a]

            for group_b in groups:
                set_b = group_sets[group_b]

                intersection = len(
                    set_a & set_b
                )

                union = len(
                    set_a | set_b
                )

                size_sum = (
                    len(set_a) + len(set_b)
                )

                min_size = min(
                    len(set_a),
                    len(set_b),
                )

                jaccard_value = (
                    intersection / union
                    if union
                    else 0.0
                )

                dice_value = (
                    2.0 * intersection / size_sum
                    if size_sum
                    else 0.0
                )

                overlap_value = (
                    intersection / min_size
                    if min_size
                    else 0.0
                )

                jaccard[group_a][group_b] = float(
                    jaccard_value
                )

                dice[group_a][group_b] = float(
                    dice_value
                )

                overlap[group_a][group_b] = float(
                    overlap_value
                )

        return {
            "jaccard": jaccard,
            "dice": dice,
            "overlap_coefficient": overlap,
        }

    # ------------------------------------------------------------------
    # 2x2 odds ratio / Fisher exact
    # ------------------------------------------------------------------

    @staticmethod
    def binary_association(
        a: int | float,
        b: int | float,
        c: int | float,
        d: int | float,
    ) -> dict[str, float]:
        """
        Analyze a 2x2 table:

                 Item    No Item
        Group A    a        b
        Group B    c        d
        """

        table = np.array(
            [
                [a, b],
                [c, d],
            ],
            dtype=float,
        )

        if np.any(table < 0):
            raise ValueError(
                "2x2 table values cannot be negative."
            )

        # Odds ratio.
        if b == 0 or c == 0:
            if a > 0 and d > 0:
                odds_ratio = float("inf")
            else:
                odds_ratio = 0.0
        else:
            odds_ratio = float(
                (a * d) / (b * c)
            )

        try:
            _, fisher_p = fisher_exact(
                table,
                alternative="two-sided",
            )
        except ValueError:
            fisher_p = 1.0

        return {
            "odds_ratio": odds_ratio,
            "fisher_p_value": float(fisher_p),
        }

    # ------------------------------------------------------------------
    # Multiple testing correction
    # ------------------------------------------------------------------

    @staticmethod
    def benjamini_hochberg(
        p_values: list[float],
    ) -> list[float]:
        """
        Benjamini-Hochberg FDR correction.
        """

        if not p_values:
            return []

        values = np.asarray(
            p_values,
            dtype=float,
        )

        values = np.nan_to_num(
            values,
            nan=1.0,
            posinf=1.0,
            neginf=0.0,
        )

        n = len(values)

        order = np.argsort(values)

        sorted_p = values[order]

        adjusted = np.empty(n)

        previous = 1.0

        for i in range(
            n - 1,
            -1,
            -1,
        ):
            rank = i + 1

            value = (
                sorted_p[i] * n / rank
            )

            previous = min(
                previous,
                value,
            )

            adjusted[i] = previous

        result = np.empty(n)

        result[order] = np.minimum(
            adjusted,
            1.0,
        )

        return result.tolist()

    @staticmethod
    def bonferroni(
        p_values: list[float],
    ) -> list[float]:
        """
        Bonferroni correction.
        """

        if not p_values:
            return []

        n = len(p_values)

        return [
            min(
                float(p) * n,
                1.0,
            )
            for p in p_values
        ]

    # ------------------------------------------------------------------
    # Per-cell statistical results
    # ------------------------------------------------------------------

    def cell_statistics(
        self,
        correction: str = "fdr_bh",
    ) -> list[dict[str, Any]]:
        """
        Produce one statistical record for every group-item cell.

        Each record contains:
        - observed
        - expected
        - residual
        - standardized residual
        - association strength
        - log ratio
        - p-value
        - adjusted p-value
        """

        expected = self.expected_counts()
        residuals = self.pearson_residuals()
        strength = self.association_strength()
        log_ratio = self.log_ratio()

        chi = self.chi_square()

        # Global chi-square is not a cell-level p-value.
        #
        # For cell ranking, the standardized residual is the primary
        # local association measure. We therefore expose the global
        # p-value separately and do not pretend it is a cell p-value.
        global_p = float(
            chi["p_value"]
        )

        records: list[dict[str, Any]] = []

        for group in self.matrix.index:
            for item in self.matrix.columns:
                records.append(
                    {
                        "group": group,
                        "item": item,
                        "observed": float(
                            self.matrix.loc[group, item]
                        ),
                        "expected": float(
                            expected.loc[group, item]
                        ),
                        "pearson_residual": float(
                            residuals.loc[group, item]
                        ),
                        "standardized_residual": float(
                            residuals.loc[group, item]
                        ),
                        "association_strength": float(
                            strength.loc[group, item]
                        ),
                        "log_ratio": float(
                            log_ratio.loc[group, item]
                        ),
                        "global_chi_square_p_value": global_p,
                    }
                )

        return records

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def summary(
        self,
        correction: str = "fdr_bh",
    ) -> dict[str, Any]:
        chi = self.chi_square()

        expected = self.expected_counts()
        residuals = self.pearson_residuals()
        strength = self.association_strength()
        log_ratio = self.log_ratio()
        similarity = self.similarity()

        return {
            "chi_square": float(
                chi["chi_square"]
            ),
            "p_value": float(
                chi["p_value"]
            ),
            "degrees_of_freedom": int(
                chi["degrees_of_freedom"]
            ),
            "cramers_v": self.cramers_v(),
            "expected_counts": expected.round(6).to_dict(
                orient="index"
            ),
            "pearson_residuals": residuals.round(6).to_dict(
                orient="index"
            ),
            "standardized_residuals": residuals.round(6).to_dict(
                orient="index"
            ),
            "association_strength": strength.round(6).to_dict(
                orient="index"
            ),
            "log_ratio": log_ratio.round(6).to_dict(
                orient="index"
            ),
            "similarity": similarity,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _empty_chi_square() -> dict[str, Any]:
        return {
            "chi_square": 0.0,
            "p_value": 1.0,
            "degrees_of_freedom": 0,
            "expected": pd.DataFrame(),
        }