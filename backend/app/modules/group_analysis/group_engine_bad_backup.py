from .mixins.counting import CountingMixin
from .mixins.statistics import StatisticsMixin
from .mixins.associations import AssociationsMixin
from .mixins.pairs import PairsMixin
from .mixins.trends import TrendsMixin
from .pmi import PMIMixin
from .conditional import ConditionalMixin


class SciAIGroupEngine(
    CountingMixin,
    StatisticsMixin,
    AssociationsMixin,
    PairsMixin,
    TrendsMixin,
    PMIMixin,
    ConditionalMixin,
):

    def __init__(self, dataframe):
        self.df = dataframe
        self.groups = None
        self.group_matrix = None
        self.results = {}

    def compute_all(self):
        completed = []
        errors = []

        steps = [
            ("build_groups", self.build_groups),
            ("count_items", self.count_items),
            ("compute_statistics", self.compute_statistics),
            ("compute_associations", self.compute_associations),
            ("count_groups", self.count_groups),
            ("count_authors", self.count_authors),
            ("compute_pmi", self.compute_pmi),
            ('compute_group_pmi', self.compute_group_pmi),
            ('compute_group_conditional', self.compute_group_conditional),`r`n            ("compute_group_pmi", self.compute_group_pmi),
            (
                "compute_conditional_associations",
                self.compute_conditional_associations,
            ),
            ("compute_trends", self.compute_trends),`r`n            ("analyze_pair_year_trends", self.analyze_pair_year_trends),
        ]

        for name, func in steps:
            try:
                func()
                completed.append(name)

            except Exception as e:
                errors.append({
                    "step": name,
                    "error": str(e),
                })

        return {
            "completed": completed,
            "errors": errors,
            "results": self.results,
        }

    def build_groups(self):
        """
        Build a unique list of atomic groups
        from overlapping memberships.
        """
        groups = []

        for value in self.df["group"].dropna():
            parts = (
                str(value)
                .replace("|", ";")
                .replace(",", ";")
                .split(";")
            )

            for part in parts:
                group = part.strip()

                if group and group not in groups:
                    groups.append(group)

        self.groups = groups
        self.results["groups"] = self.groups
