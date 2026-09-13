from typing import Any

import pandas as pd

from .matrix_builder import GroupMatrixBuilder


class ConditionalMixin:
    """
    Conditional association analysis for overlapping BiblioGroup memberships.

    Calculates:

        P(B | A)
        P(A | B)
        P(A and B)
        P(A)
        P(B)
        Lift
        Conditional Risk Ratio

    based on the document × group binary membership matrix.
    """

    def _get_conditional_group_document_matrix(self) -> pd.DataFrame:
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
    def _conditional_probability(
        shared_documents: int,
        condition_group_count: int,
    ) -> float:
        """
        Calculate:

            P(B | A) = shared_documents / documents_in_A
        """

        if condition_group_count <= 0:
            return 0.0

        return shared_documents / condition_group_count

    @staticmethod
    def _joint_probability(
        shared_documents: int,
        total_documents: int,
    ) -> float:
        """
        Calculate:

            P(A and B)
        """

        if total_documents <= 0:
            return 0.0

        return shared_documents / total_documents

    @staticmethod
    def _marginal_probability(
        group_count: int,
        total_documents: int,
    ) -> float:
        """
        Calculate:

            P(A)
        """

        if total_documents <= 0:
            return 0.0

        return group_count / total_documents

    @staticmethod
    def _conditional_lift(
        shared_documents: int,
        group_a_count: int,
        group_b_count: int,
        total_documents: int,
    ) -> float:
        """
        Calculate Lift.

            Lift(A,B) =
                P(A and B) / (P(A) * P(B))
        """

        if total_documents <= 0:
            return 0.0

        if (
            shared_documents <= 0
            or group_a_count <= 0
            or group_b_count <= 0
        ):
            return 0.0

        p_ab = shared_documents / total_documents
        p_a = group_a_count / total_documents
        p_b = group_b_count / total_documents

        denominator = p_a * p_b

        if denominator <= 0:
            return 0.0

        return p_ab / denominator

    @staticmethod
    def _conditional_risk_ratio(
        conditional_probability: float,
        baseline_probability: float,
    ) -> float:
        """
        Calculate:

            P(B | A) / P(B)

        This is mathematically equivalent to Lift(A,B).
        """

        if baseline_probability <= 0:
            return 0.0

        return conditional_probability / baseline_probability

    def compute_conditional_associations(self) -> dict[str, Any]:
        """
        Calculate pairwise conditional associations.

        Results are stored in:

            conditional_matrix
            conditional_reverse_matrix
            joint_probability_matrix
            conditional_risk_ratio_matrix

        and:

            group_conditional_associations
        """

        matrix = (
            self._get_conditional_group_document_matrix()
        )

        if matrix.empty:
            empty = pd.DataFrame()

            self.results[
                "conditional_matrix"
            ] = empty

            self.results[
                "conditional_reverse_matrix"
            ] = empty

            self.results[
                "joint_probability_matrix"
            ] = empty

            self.results[
                "conditional_risk_ratio_matrix"
            ] = empty

            self.results[
                "group_conditional_associations"
            ] = []

            return {
                "conditional_matrix": empty,
                "conditional_reverse_matrix": empty,
                "joint_probability_matrix": empty,
                "conditional_risk_ratio_matrix": empty,
                "group_conditional_associations": [],
            }

        groups = list(matrix.columns)

        total_documents = len(matrix)

        document_counts = (
            matrix.sum(axis=0).astype(int)
        )

        conditional_matrix = pd.DataFrame(
            float("nan"),
            index=groups,
            columns=groups,
        )

        conditional_reverse_matrix = pd.DataFrame(
            float("nan"),
            index=groups,
            columns=groups,
        )

        joint_probability_matrix = pd.DataFrame(
            float("nan"),
            index=groups,
            columns=groups,
        )

        conditional_risk_ratio_matrix = pd.DataFrame(
            float("nan"),
            index=groups,
            columns=groups,
        )

        pair_results = []

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

                shared_documents = int(
                    (
                        matrix[group_a]
                        .astype(int)
                        .mul(
                            matrix[group_b]
                            .astype(int)
                        )
                    ).sum()
                )

                p_a = self._marginal_probability(
                    group_count=count_a,
                    total_documents=total_documents,
                )

                p_b = self._marginal_probability(
                    group_count=count_b,
                    total_documents=total_documents,
                )

                p_ab = self._joint_probability(
                    shared_documents=shared_documents,
                    total_documents=total_documents,
                )

                p_b_given_a = (
                    self._conditional_probability(
                        shared_documents=shared_documents,
                        condition_group_count=count_a,
                    )
                )

                p_a_given_b = (
                    self._conditional_probability(
                        shared_documents=shared_documents,
                        condition_group_count=count_b,
                    )
                )

                lift = self._conditional_lift(
                    shared_documents=shared_documents,
                    group_a_count=count_a,
                    group_b_count=count_b,
                    total_documents=total_documents,
                )

                risk_ratio_b_given_a = (
                    self._conditional_risk_ratio(
                        conditional_probability=p_b_given_a,
                        baseline_probability=p_b,
                    )
                )

                risk_ratio_a_given_b = (
                    self._conditional_risk_ratio(
                        conditional_probability=p_a_given_b,
                        baseline_probability=p_a,
                    )
                )

                conditional_matrix.loc[
                    group_a,
                    group_b,
                ] = p_b_given_a

                conditional_matrix.loc[
                    group_b,
                    group_a,
                ] = p_a_given_b

                conditional_reverse_matrix.loc[
                    group_a,
                    group_b,
                ] = p_a_given_b

                conditional_reverse_matrix.loc[
                    group_b,
                    group_a,
                ] = p_b_given_a

                joint_probability_matrix.loc[
                    group_a,
                    group_b,
                ] = p_ab

                joint_probability_matrix.loc[
                    group_b,
                    group_a,
                ] = p_ab

                conditional_risk_ratio_matrix.loc[
                    group_a,
                    group_b,
                ] = risk_ratio_b_given_a

                conditional_risk_ratio_matrix.loc[
                    group_b,
                    group_a,
                ] = risk_ratio_a_given_b

                pair_results.append(
                    {
                        "group_1": group_a,
                        "group_2": group_b,
                        "documents_group_1": count_a,
                        "documents_group_2": count_b,
                        "shared_documents": shared_documents,
                        "total_documents": total_documents,
                        "p_group_1": round(
                            p_a,
                            6,
                        ),
                        "p_group_2": round(
                            p_b,
                            6,
                        ),
                        "p_group_1_given_group_2": round(
                            p_a_given_b,
                            6,
                        ),
                        "p_group_2_given_group_1": round(
                            p_b_given_a,
                            6,
                        ),
                        "joint_probability": round(
                            p_ab,
                            6,
                        ),
                        "lift": round(
                            lift,
                            6,
                        ),
                        "conditional_risk_ratio_group_2_given_group_1": round(
                            risk_ratio_b_given_a,
                            6,
                        ),
                        "conditional_risk_ratio_group_1_given_group_2": round(
                            risk_ratio_a_given_b,
                            6,
                        ),
                    }
                )

        pair_results.sort(
            key=lambda x: x["lift"],
            reverse=True,
        )

        self.results[
            "conditional_matrix"
        ] = conditional_matrix

        self.results[
            "conditional_reverse_matrix"
        ] = conditional_reverse_matrix

        self.results[
            "joint_probability_matrix"
        ] = joint_probability_matrix

        self.results[
            "conditional_risk_ratio_matrix"
        ] = conditional_risk_ratio_matrix

        self.results[
            "group_conditional_associations"
        ] = pair_results

        return {
            "conditional_matrix": conditional_matrix,
            "conditional_reverse_matrix": conditional_reverse_matrix,
            "joint_probability_matrix": joint_probability_matrix,
            "conditional_risk_ratio_matrix": conditional_risk_ratio_matrix,
            "group_conditional_associations": pair_results,
        }