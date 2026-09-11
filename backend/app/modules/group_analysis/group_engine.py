from .mixins.counting import CountingMixin
from .mixins.statistics import StatisticsMixin
from .mixins.associations import AssociationsMixin
from .mixins.pairs import PairsMixin
from .mixins.trends import TrendsMixin


class SciAIGroupEngine(
    CountingMixin,
    StatisticsMixin,
    AssociationsMixin,
    PairsMixin,
    TrendsMixin
):

    def __init__(self, dataframe):

        self.df = dataframe

        self.groups = None

        self.group_matrix = None

        self.results = {}


    def compute_all(self):

        completed=[]
        errors=[]


        steps=[
            ("build_groups",self.build_groups),
            ("count_items",self.count_items),
            ("compute_statistics",self.compute_statistics),
            ("compute_associations",self.compute_associations),
            ("compute_pairs",self.compute_pairs),
            ("compute_trends",self.compute_trends),
        ]


        for name,func in steps:

            try:
                func()
                completed.append(name)

            except Exception as e:

                errors.append({
                    "step":name,
                    "error":str(e)
                })


        return {
            "completed":completed,
            "errors":errors,
            "results":self.results
        }


    def build_groups(self):

        self.groups = (
            self.df["group"]
            .dropna()
            .unique()
            .tolist()
        )

        self.results["groups"]=self.groups