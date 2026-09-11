# backend/app/modules/group_analysis/association_engine.py

import pandas as pd

from .matrix_builder import GroupMatrixBuilder



class AssociationEngine:


    def __init__(self, dataframe):

        self.df = dataframe

        self.builder = GroupMatrixBuilder(
            dataframe
        )



    def compute_group_item_association(
            self,
            item_column="keywords"
    ):


        matrices = (
            self.builder
            .build_association_matrix(
                item_column=item_column
            )
        )


        association = (
            matrices["association_matrix"]
        )


        return {

            "association_matrix":
                association,

            "shape":
                association.shape,

            "groups":
                list(
                    association.index
                ),

            "items":
                list(
                    association.columns
                )

        }



    def compute_top_associations(
            self,
            item_column="keywords",
            top_n=10
    ):


        result = (
            self.compute_group_item_association(
                item_column
            )
        )


        matrix = result[
            "association_matrix"
        ]


        output={}


        for group in matrix.index:

            output[group] = (
                matrix
                .loc[group]
                .sort_values(
                    ascending=False
                )
                .head(top_n)
                .to_dict()
            )


        return output