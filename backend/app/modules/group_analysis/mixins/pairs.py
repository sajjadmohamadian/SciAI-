# biblium/bibgroup_modules/pairs.py

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


class GroupPairsMixin:
    """Mixin providing concept × concept pair analysis methods."""

    def compute_group_pmi(
        self,
        smoothing: float = 1e-9,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:

        if not hasattr(self, "group_matrix") or self.group_matrix is None:
            raise RuntimeError(
                "group_matrix not built. Pass `group_desc` to "
                "BiblioGroupAnalysis(...) constructor."
            )

        M = self.group_matrix.astype(int)
        N = len(M)

        raw = M.T.dot(M).astype(int)

        sizes = pd.Series(
            np.diag(raw.values),
            index=raw.index
        ).astype(float)

        p = sizes.values / max(N, 1)

        with np.errstate(divide="ignore", invalid="ignore"):
            lift = (raw.values / max(N, 1)) / (
                (p[:, None] * p[None, :]) + smoothing
            )

            lift = np.where(
                np.isfinite(lift),
                lift,
                0.0
            )

            pmi = np.log(
                np.where(lift > 0, lift, 1.0)
            )

        lift_df = pd.DataFrame(
            lift,
            index=raw.index,
            columns=raw.columns
        )

        pmi_df = pd.DataFrame(
            pmi,
            index=raw.index,
            columns=raw.columns
        )

        self.group_pair_raw = raw
        self.group_pair_lift = lift_df
        self.group_pair_pmi = pmi_df

        return raw, lift_df, pmi_df


    def compute_group_conditional(self) -> pd.DataFrame:

        if not hasattr(self, "group_matrix") or self.group_matrix is None:
            raise RuntimeError(
                "group_matrix not built. Pass `group_desc` to "
                "BiblioGroupAnalysis(...) constructor."
            )

        M = self.group_matrix.astype(int)

        raw = M.T.dot(M).astype(int)

        sizes = pd.Series(
            np.diag(raw.values),
            index=raw.index
        ).astype(float)

        with np.errstate(divide="ignore", invalid="ignore"):
            cond = raw.values / sizes.values[:, None].clip(min=1)

        cond_df = pd.DataFrame(
            cond,
            index=raw.index,
            columns=raw.columns
        )

        self.group_pair_conditional = cond_df

        return cond_df


    def get_group_citation_impact(
        self,
        citations_col: str = "Cited by",
        min_papers: int = 5,
    ) -> pd.DataFrame:

        if not hasattr(self, "group_matrix") or self.group_matrix is None:
            raise RuntimeError(
                "group_matrix not built. Pass `group_desc` to "
                "BiblioGroupAnalysis(...) constructor."
            )

        if citations_col not in self.df.columns:
            raise KeyError(
                f"Citation column '{citations_col}' not in df."
            )

        cits = (
            pd.to_numeric(
                self.df[citations_col],
                errors="coerce"
            )
            .fillna(0)
            .values
        )

        M = self.group_matrix.astype(bool).values

        names = list(self.group_matrix.columns)
        n = len(names)

        impact = np.full(
            (n, n),
            np.nan,
            dtype=float
        )

        for i in range(n):
            m1 = M[:, i]

            for j in range(n):
                m2 = M[:, j]

                both = m1 & m2
                k = int(both.sum())

                if k >= min_papers:
                    impact[i, j] = float(
                        round(cits[both].mean(), 2)
                    )

        df_out = pd.DataFrame(
            impact,
            index=names,
            columns=names
        )

        self.group_pair_citation_impact = df_out

        return df_out


    def analyze_pair_year_trends(
        self,
        top_n_pairs: int = 10,
        year_col: str = "Year",
        n_windows: int = 4,
        rank_by: str = "pmi",
        current_year_exclude: Optional[int] = None,
    ) -> pd.DataFrame:


        if (
            not hasattr(self, "group_pair_pmi")
            or self.group_pair_pmi is None
        ):
            self.compute_group_pmi()


        if rank_by == "pmi":

            rank_M = self.group_pair_pmi

        elif rank_by == "lift":

            rank_M = self.group_pair_lift

        elif rank_by == "raw":

            rank_M = self.group_pair_raw

        else:

            raise ValueError(
                "rank_by must be 'pmi', 'lift', or 'raw'"
            )


        rows = []

        names = list(rank_M.index)


        for i, c1 in enumerate(names):

            for j, c2 in enumerate(names):

                if i >= j:
                    continue


                rows.append(
                    {
                        "c1": c1,
                        "c2": c2,
                        "score": float(
                            rank_M.iloc[i, j]
                        ),
                    }
                )


        if not rows:

            self.group_pair_year_trends = pd.DataFrame()

            return self.group_pair_year_trends



        pairs_df = (

            pd.DataFrame(rows)

            .sort_values(
                "score",
                ascending=False
            )

            .head(top_n_pairs)

        )


        # -------------------------------
        # Flexible year column detection
        # -------------------------------

        if year_col not in self.df.columns:


            alternatives = [

                "year",

                "Year",

                "PY",

                "Publication Year",

                "Publication_Year",

            ]


            found = None


            for col in alternatives:

                if col in self.df.columns:

                    found = col

                    break


            if found is None:

                raise KeyError(
                    f"No year column found. Tried: {alternatives}"
                )


            year_col = found



        years = pd.to_numeric(

            self.df[year_col],

            errors="coerce"

        )


        mask = years.notna()



        if current_year_exclude is not None:

            mask &= (

                years < current_year_exclude

            )



        sub_df = self.df[mask].copy()



        if sub_df.empty:

            self.group_pair_year_trends = pd.DataFrame()

            return self.group_pair_year_trends



        sub_gm = self.group_matrix.loc[

            sub_df.index

        ]



        sub_y = (

            pd.to_numeric(

                sub_df[year_col],

                errors="coerce"

            )

            .astype(int)

        )


        ymin = int(sub_y.min())

        ymax = int(sub_y.max())



        if ymin == ymax:

            cuts = np.array(

                [

                    ymin,

                    ymax + 1

                ]

            )

            n_windows = 1


        else:

            cuts = np.linspace(

                ymin,

                ymax + 1,

                n_windows + 1

            ).astype(int)



        bin_labels = [

            f"{cuts[i]}-{cuts[i + 1] - 1}"

            for i in range(len(cuts)-1)

        ]



        bin_idx = pd.cut(

            sub_y,

            bins=list(cuts),

            labels=bin_labels,

            include_lowest=True,

            right=False,

        )



        out_rows = []



        for _, pair in pairs_df.iterrows():


            c1 = pair["c1"]

            c2 = pair["c2"]



            for b in bin_labels:


                bmask = (

                    bin_idx == b

                ).values



                if bmask.sum() == 0:

                    continue



                gm_b = sub_gm.loc[bmask]



                m1 = gm_b[c1].astype(bool)

                m2 = gm_b[c2].astype(bool)



                n12 = int(

                    (m1 & m2).sum()

                )


                n1 = int(

                    m1.sum()

                )


                n_tot = int(

                    bmask.sum()

                )



                out_rows.append(

                    {

                        "pair":
                            f"{c1} × {c2}",

                        "c1": c1,

                        "c2": c2,

                        "bin": str(b),

                        "n_total_in_bin": n_tot,

                        "n_c1": n1,

                        "n_c1_and_c2": n12,

                        "share_c1_in_bin_pct":
                            round(
                                100 * n1 /
                                max(n_tot, 1),
                                2
                            ),

                        "share_c1c2_of_bin_pct":
                            round(
                                100 * n12 /
                                max(n_tot, 1),
                                2
                            ),

                        "share_c1c2_of_c1_pct":
                            round(
                                100 * n12 /
                                max(n1, 1),
                                2
                            ),

                    }

                )



        out = pd.DataFrame(out_rows)


        self.group_pair_year_trends = out


        return out


    def get_group_bibliographic_coupling(
        self,
        references_col: str = "References",
    ) -> pd.DataFrame:

        if not hasattr(self, "group_matrix") \
                or self.group_matrix is None:
            raise RuntimeError(
                "group_matrix not built."
            )

        if references_col not in self.df.columns:
            raise KeyError(
                f"Reference column '{references_col}' not in df."
            )

        names = list(
            self.group_matrix.columns
        )

        reference_sets = {}

        for group in names:

            docs = self.group_matrix[group].astype(bool)

            refs = set()

            for value in self.df.loc[
                docs,
                references_col
            ].dropna():

                if isinstance(value, str):
                    refs.update(
                        x.strip()
                        for x in value.split(";")
                        if x.strip()
                    )

            reference_sets[group] = refs

        n = len(names)

        result = np.zeros(
            (n, n),
            dtype=float
        )

        for i, g1 in enumerate(names):

            for j, g2 in enumerate(names):

                a = reference_sets[g1]
                b = reference_sets[g2]

                union = a | b

                if union:
                    result[i, j] = (
                        len(a & b) /
                        len(union)
                    )

        out = pd.DataFrame(
            result,
            index=names,
            columns=names
        )

        self.group_bibliographic_coupling = out

        return out
# Backward-compatible alias used by SciAI group_engine
PairsMixin = GroupPairsMixin
