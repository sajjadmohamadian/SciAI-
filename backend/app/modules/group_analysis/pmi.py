from math import log2
from typing import Any

import pandas as pd

from .matrix_builder import GroupMatrixBuilder


class PMIMixin:
    """
    PMI, NPMI and Lift analysis for overlapping BiblioGroup memberships.
    """

    def _get_pmi_group_document_matrix(self) -> pd.DataFrame:
        """
        Build the document × group membership matrix.
        """
        builder = GroupMatrixBuilder(
            self.df,
            group_column="group",
        )

        matrix = builder.build_group_matrix()

        if self.groups is not None:
            existing_groups = [
                group
                for group in self.groups
                if group in matrix.columns
            ]

            missing_groups = [
                group
                for group in matrix.columns
                if group not in existing_groups
            ]

            matrix = matrix[
                existing_groups + missing_groups
            ]

        return matrix

    @staticmethod
    def _pmi(
        co_occurrence: int,
        group_a_count: int,
        group_b_count: int,
        total_documents: int,
    ) -> float:
        """
        Pointwise Mutual Information.

        PMI(A,B) = log2(P(A,B) / (P(A) * P(B)))
        """

        if total_documents <= 0:
            return 0.0

        if co_occurrence <= 0:
            return float("-inf")

        if group_a_count <= 0 or group_b_count <= 0:
            return float("-inf")

        p_ab = co_occurrence / total_documents
        p_a = group_a_count / total_documents
        p_b = group_b_count / total_documents

        expected_probability = p_a * p_b

        if expected_probability <= 0:
            return float("-inf")

        return log2(
            p_ab / expected_probability
        )

    @staticmethod
    def _npmi(
        co_occurrence: int,
        group_a_count: int,
        group_b_count: int,
        total_documents: int,
    ) -> float:
        """
        Normalized Pointwise Mutual Information.

        NPMI(A,B) = PMI(A,B) / -log2(P(A,B))

        Range:
            -1 <= NPMI <= 1

        Zero co-occurrence is represented as -1.
        """

        if total_documents <= 0:
            return 0.0

        if co_occurrence <= 0:
            return -1.0

        p_ab = co_occurrence / total_documents

        if p_ab <= 0:
            return -1.0

        pmi = PMIMixin._pmi(
            co_occurrence=co_occurrence,
            group_a_count=group_a_count,
            group_b_count=group_b_count,
            total_documents=total_documents,
        )

        if pmi == float("-inf"):
            return -1.0

        denominator = -log2(p_ab)

        if denominator == 0:
            return 1.0

        return pmi / denominator

    @staticmethod
    def _lift(
        co_occurrence: int,
        group_a_count: int,
        group_b_count: int,
        total_documents: int,
    ) -> float:
        """
        Lift.

        Lift(A,B) = P(A,B) / (P(A) * P(B))

        Interpretation:

            Lift > 1  -> positive association
            Lift = 1  -> independence
            Lift < 1  -> negative association
            Lift = 0  -> no co-occurrence
        """

        if total_documents <= 0:
            return 0.0

        if co_occurrence <= 0:
            return 0.0

        if group_a_count <= 0 or group_b_count <= 0:
            return 0.0

        p_ab = co_occurrence / total_documents
        p_a = group_a_count / total_documents
        p_b = group_b_count / total_documents

        expected_probability = p_a * p_b

        if expected_probability <= 0:
            return 0.0

        return p_ab / expected_probability

    def compute_pmi(self) -> dict[str, Any]:
        """
        Calculate pairwise PMI, NPMI and Lift.

        Results:

            pmi_matrix
            npmi_matrix
            lift_matrix

            group_pmi
            group_npmi
            group_lift
        """

        matrix = self._get_pmi_group_document_matrix()

        if matrix.empty:
            empty = pd.DataFrame()

            self.results["pmi_matrix"] = empty
            self.results["npmi_matrix"] = empty
            self.results["lift_matrix"] = empty

            self.results["group_pmi"] = []
            self.results["group_npmi"] = []
            self.results["group_lift"] = []

            return {
                "pmi_matrix": empty,
                "npmi_matrix": empty,
                "lift_matrix": empty,
                "group_pmi": [],
                "group_npmi": [],
                "group_lift": [],
            }

        groups = list(matrix.columns)
        total_documents = len(matrix)

        document_counts = matrix.sum(
            axis=0
        ).astype(int)

        pmi_matrix = pd.DataFrame(
            float("nan"),
            index=groups,
            columns=groups,
        )

        npmi_matrix = pd.DataFrame(
            float("nan"),
            index=groups,
            columns=groups,
        )

        lift_matrix = pd.DataFrame(
            float("nan"),
            index=groups,
            columns=groups,
        )

        pair_pmi = []
        pair_npmi = []
        pair_lift = []

        for i, group_a in enumerate(groups):

            count_a = int(
                document_counts[group_a]
            )

            for j in range(
                i + 1,
                len(groups),
            ):

                group_b = groups[j]

                count_b = int(
                    document_counts[group_b]
                )

                co_occurrence = int(
                    (
                        matrix[group_a]
                        .astype(int)
                        .mul(
                            matrix[group_b]
                            .astype(int)
                        )
                    ).sum()
                )

                pmi = self._pmi(
                    co_occurrence=co_occurrence,
                    group_a_count=count_a,
                    group_b_count=count_b,
                    total_documents=total_documents,
                )

                npmi = self._npmi(
                    co_occurrence=co_occurrence,
                    group_a_count=count_a,
                    group_b_count=count_b,
                    total_documents=total_documents,
                )

                lift = self._lift(
                    co_occurrence=co_occurrence,
                    group_a_count=count_a,
                    group_b_count=count_b,
                    total_documents=total_documents,
                )

                pmi_matrix.loc[
                    group_a,
                    group_b,
                ] = pmi

                pmi_matrix.loc[
                    group_b,
                    group_a,
                ] = pmi

                npmi_matrix.loc[
                    group_a,
                    group_b,
                ] = npmi

                npmi_matrix.loc[
                    group_b,
                    group_a,
                ] = npmi

                lift_matrix.loc[
                    group_a,
                    group_b,
                ] = lift

                lift_matrix.loc[
                    group_b,
                    group_a,
                ] = lift

                pair_pmi.append(
                    {
                        "group_1": group_a,
                        "group_2": group_b,
                        "documents_group_1": count_a,
                        "documents_group_2": count_b,
                        "shared_documents": co_occurrence,
                        "total_documents": total_documents,
                        "pmi": (
                            round(pmi, 6)
                            if pmi != float("-inf")
                            else float("-inf")
                        ),
                    }
                )

                pair_npmi.append(
                    {
                        "group_1": group_a,
                        "group_2": group_b,
                        "documents_group_1": count_a,
                        "documents_group_2": count_b,
                        "shared_documents": co_occurrence,
                        "total_documents": total_documents,
                        "npmi": round(
                            npmi,
                            6,
                        ),
                    }
                )

                pair_lift.append(
                    {
                        "group_1": group_a,
                        "group_2": group_b,
                        "documents_group_1": count_a,
                        "documents_group_2": count_b,
                        "shared_documents": co_occurrence,
                        "total_documents": total_documents,
                        "lift": round(
                            lift,
                            6,
                        ),
                    }
                )

        pair_pmi.sort(
            key=lambda x: (
                float("-inf")
                if x["pmi"] == float("-inf")
                else x["pmi"]
            ),
            reverse=True,
        )

        pair_npmi.sort(
            key=lambda x: x["npmi"],
            reverse=True,
        )

        pair_lift.sort(
            key=lambda x: x["lift"],
            reverse=True,
        )

        self.results["pmi_matrix"] = pmi_matrix
        self.results["npmi_matrix"] = npmi_matrix
        self.results["lift_matrix"] = lift_matrix

        self.results["group_pmi"] = pair_pmi
        self.results["group_npmi"] = pair_npmi
        self.results["group_lift"] = pair_lift

        return {
            "pmi_matrix": pmi_matrix,
            "npmi_matrix": npmi_matrix,
            "lift_matrix": lift_matrix,
            "group_pmi": pair_pmi,
            "group_npmi": pair_npmi,
            "group_lift": pair_lift,
        }