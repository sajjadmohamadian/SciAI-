# backend/app/modules/group_analysis/association_stats.py

import pandas as pd
from scipy.stats import chi2_contingency
from sklearn.metrics import jaccard_score


class AssociationStatistics:


    def __init__(self, association_matrix):

        self.matrix = association_matrix



    def chi_square(self):

        results = []


        for item in self.matrix.columns:

            values = self.matrix[item]


            table = pd.DataFrame(
                {
                    "present": values,
                    "absent": self.matrix.sum(axis=1)-values
                }
            )


            try:

                chi2, p, _, _ = chi2_contingency(
                    table
                )


                results.append(
                    {
                        "item": item,
                        "chi2": chi2,
                        "p_value": p
                    }
                )


            except Exception:

                results.append(
                    {
                        "item": item,
                        "chi2": None,
                        "p_value": None
                    }
                )


        return pd.DataFrame(results)



    def association_strength(self):

        result=[]


        total = self.matrix.sum().sum()


        for group in self.matrix.index:

            for item in self.matrix.columns:

                value = self.matrix.loc[group,item]


                strength = (
                    value / total
                    if total
                    else 0
                )


                result.append(
                    {
                        "group":group,
                        "item":item,
                        "count":value,
                        "strength":strength
                    }
                )


        return pd.DataFrame(result)



    def similarity(self):

        output=[]


        groups=list(
            self.matrix.index
        )


        for i,g1 in enumerate(groups):

            for g2 in groups[i+1:]:


                a=self.matrix.loc[g1].values
                b=self.matrix.loc[g2].values


                score=jaccard_score(
                    a>0,
                    b>0
                )


                output.append(
                    {
                        "group1":g1,
                        "group2":g2,
                        "jaccard":score
                    }
                )


        return pd.DataFrame(output)