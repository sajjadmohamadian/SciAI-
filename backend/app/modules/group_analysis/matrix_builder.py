# backend/app/modules/group_analysis/matrix_builder.py

import pandas as pd


class GroupMatrixBuilder:


    def __init__(self, dataframe):

        self.df = dataframe



    def build_group_matrix(self):

        if "group" not in self.df.columns:

            raise ValueError(
                "group column missing"
            )


        matrix = pd.get_dummies(
            self.df["group"]
        )


        return matrix



    def build_item_matrix(
            self,
            column="keywords",
            separator=";"
    ):

        if column not in self.df.columns:

            raise ValueError(
                f"{column} column missing"
            )


        rows=[]


        for value in self.df[column]:

            if not isinstance(value,str):

                rows.append([])

            else:

                rows.append(
                    [
                        x.strip()
                        for x in value.split(separator)
                        if x.strip()
                    ]
                )


        all_items = sorted(
            set(
                item
                for row in rows
                for item in row
            )
        )


        matrix = pd.DataFrame(
            0,
            index=self.df.index,
            columns=all_items
        )


        for idx,items in zip(
            self.df.index,
            rows
        ):

            for item in items:

                matrix.loc[idx,item]=1


        return matrix



    def build_association_matrix(
            self,
            group_column="group",
            item_column="keywords"
    ):


        G = self.build_group_matrix()

        X = self.build_item_matrix(
            item_column
        )


        association = (
            G.T
            .dot(X)
        )


        return {

            "group_matrix":G,

            "item_matrix":X,

            "association_matrix":association

        }