from ..association_engine import AssociationEngine


class AssociationsMixin:


    def compute_associations(self):

        engine = AssociationEngine(
            self.df
        )


        associations = {}


        fields = [
            "keywords",
            "authors",
            "country",
            "topics"
        ]


        for field in fields:

            if field in self.df.columns:

                try:

                    associations[field] = (
                        engine
                        .compute_group_item_association(
                            field
                        )
                    )

                except Exception as e:

                    associations[field] = {
                        "error": str(e)
                    }



        self.results["associations"] = associations


        return associations