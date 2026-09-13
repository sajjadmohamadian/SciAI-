import pandas as pd


class TrendsMixin:
    """
    Time-trend analysis for BiblioGroup.

    Supports overlapping group memberships.
    """

    def _get_group_document_matrix(self) -> pd.DataFrame:
        """
        Build document × group membership matrix.
        """

        from ..matrix_builder import GroupMatrixBuilder

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

    def compute_trends(self):

        if "year" not in self.df.columns:
            self.results["trends"] = {}
            self.results["group_year_trends"] = {}
            self.results["group_year_shares"] = {}
            return

        years = pd.to_numeric(
            self.df["year"],
            errors="coerce",
        )

        valid_years = years.notna()

        # Overall document trend
        overall_trend = (
            years[valid_years]
            .astype(int)
            .value_counts()
            .sort_index()
            .to_dict()
        )

        self.results["trends"] = overall_trend

        # No group column
        if "group" not in self.df.columns:
            self.results["group_year_trends"] = {}
            self.results["group_year_shares"] = {}
            return

        # Document × group matrix
        matrix = self._get_group_document_matrix()

        if matrix.empty:
            self.results["group_year_trends"] = {}
            self.results["group_year_shares"] = {}
            return

        trend_df = matrix.copy()

        trend_df["year"] = years

        trend_df = trend_df[
            trend_df["year"].notna()
        ]

        trend_df["year"] = (
            trend_df["year"]
            .astype(int)
        )

        # Group × year document counts
        group_year = (
            trend_df
            .groupby("year")[list(matrix.columns)]
            .sum()
            .astype(int)
        )

        self.results["group_year_trends"] = (
            group_year
            .to_dict(orient="index")
        )

        # Group shares within each year
        group_year_shares = group_year.astype(float).copy()

        for year in group_year_shares.index:

            total = group_year_shares.loc[year].sum()

            if total > 0:
                group_year_shares.loc[year] = (
                    group_year_shares.loc[year] / total
                ).round(4)

        self.results["group_year_shares"] = (
            group_year_shares
            .to_dict(orient="index")
        )

        return self.results["group_year_trends"]