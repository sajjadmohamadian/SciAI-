class TrendsMixin:

    def compute_trends(self):

        if "year" not in self.df.columns:
            self.results["trends"] = {}
            return

        self.results["trends"] = (
            self.df
            .groupby("year")
            .size()
            .to_dict()
        )