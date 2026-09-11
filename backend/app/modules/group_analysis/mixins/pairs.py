import pandas as pd


class PairsMixin:


    def compute_pairs(self):

        if self.groups is None:

            self.build_groups()


        pairs = []


        for i, g1 in enumerate(self.groups):

            for g2 in self.groups[i+1:]:


                pair_result = {

                    "group1": g1,

                    "group2": g2

                }


                if (
                    "keywords"
                    in self.df.columns
                ):


                    k1 = self._group_keywords(g1)

                    k2 = self._group_keywords(g2)


                    intersection = (
                        k1.intersection(k2)
                    )


                    union = (
                        k1.union(k2)
                    )


                    similarity = (

                        len(intersection)
                        /
                        len(union)

                        if len(union)

                        else 0

                    )


                    pair_result.update(

                        {

                            "shared_keywords":
                                list(intersection),

                            "keyword_similarity":
                                similarity,

                            "shared_count":
                                len(intersection)

                        }

                    )


                pairs.append(pair_result)



        self.results["pairs"] = pairs


        return pairs




    def _group_keywords(self, group):

        keywords=set()


        rows = self.df[
            self.df["group"] == group
        ]["keywords"]


        for row in rows:

            if isinstance(row,str):

                for item in row.split(";"):

                    item=item.strip()

                    if item:

                        keywords.add(item)


        return keywords