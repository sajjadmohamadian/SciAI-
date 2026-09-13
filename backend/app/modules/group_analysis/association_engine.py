from __future__ import annotations

from typing import Any

import pandas as pd

from .association_stats import AssociationStatistics
from .matrix_builder import GroupMatrixBuilder


class AssociationEngine:
    """
    High-level BiblioGroup association engine.

    Responsible for:
    1. Building group × item matrices.
    2. Delegating statistical calculations.
    3. Returning a stable JSON-friendly result.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        group_column: str = "group",
    ) -> None:
        self.df = df.copy()
        self.group_column = group_column

        self.matrix_builder = GroupMatrixBuilder(
            self.df,
            group_column=group_column,
        )

    def compute_group_item_association(
        self,
        item_column: str,
        min_frequency: int = 0,
    ) -> dict[str, Any]:
        matrix = self.matrix_builder.build_group_item_matrix(
            item_column=item_column,
            group_column=self.group_column,
        )

        if matrix.empty:
            return self._empty_result()

        matrix = matrix.loc[
            :,
            matrix.sum(axis=0) > 0,
        ]

        if min_frequency > 0:
            frequencies = matrix.sum(axis=0)

            matrix = matrix.loc[
                :,
                frequencies >= min_frequency,
            ]

        if matrix.empty:
            return self._empty_result()

        stats = AssociationStatistics(
            matrix
        )

        summary = stats.summary()

        return {
            "association_matrix": matrix.astype(int).to_dict(
                orient="index"
            ),
            "expected_counts": summary[
                "expected_counts"
            ],
            "pearson_residuals": summary[
                "pearson_residuals"
            ],
            "standardized_residuals": summary[
                "standardized_residuals"
            ],
            "association_strength": summary[
                "association_strength"
            ],
            "log_ratio": summary[
                "log_ratio"
            ],
            "similarity": summary[
                "similarity"
            ],
            "chi_square": summary[
                "chi_square"
            ],
            "p_value": summary[
                "p_value"
            ],
            "degrees_of_freedom": summary[
                "degrees_of_freedom"
            ],
            "cramers_v": summary[
                "cramers_v"
            ],
            "total": float(
                matrix.to_numpy().sum()
            ),
            "shape": matrix.shape,
            "groups": list(matrix.index),
            "items": list(matrix.columns),
        }

    def compute_top_associations(
        self,
        item_column: str,
        top_n: int = 10,
        metric: str = "standardized_residual",
    ) -> dict[str, list[dict[str, Any]]]:
        result = self.compute_group_item_association(
            item_column=item_column,
        )

        if not result["groups"]:
            return {}

        if metric == "standardized_residual":
            source = result[
                "standardized_residuals"
            ]

        elif metric == "association_strength":
            source = result[
                "association_strength"
            ]

        elif metric == "log_ratio":
            source = result[
                "log_ratio"
            ]

        elif metric == "observed":
            source = result[
                "association_matrix"
            ]

        else:
            raise ValueError(
                f"Unsupported association metric: {metric}"
            )

        output: dict[
            str,
            list[dict[str, Any]],
        ] = {}

        for group in result["groups"]:
            values = source.get(
                group,
                {},
            )

            ranked = sorted(
                values.items(),
                key=lambda pair: abs(
                    float(pair[1])
                ),
                reverse=True,
            )

            output[group] = [
                {
                    "item": item,
                    "value": float(value),
                }
                for item, value in ranked[:top_n]
            ]

        return output

    @staticmethod
    def _empty_result() -> dict[str, Any]:
        return {
            "association_matrix": {},
            "expected_counts": {},
            "pearson_residuals": {},
            "standardized_residuals": {},
            "association_strength": {},
            "log_ratio": {},
            "similarity": {
                "jaccard": {},
                "dice": {},
                "overlap_coefficient": {},
            },
            "chi_square": 0.0,
            "p_value": 1.0,
            "degrees_of_freedom": 0,
            "cramers_v": 0.0,
            "total": 0.0,
            "shape": (0, 0),
            "groups": [],
            "items": [],
        }