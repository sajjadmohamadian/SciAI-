# backend/app/modules/group_analysis/mixins/statistics.py


class StatisticsMixin:


    def compute_statistics(self):

        self.results["statistics"] = {

            "documents":
                len(self.df),

            "groups":
                0 if self.groups is None
                else len(self.groups)

        }