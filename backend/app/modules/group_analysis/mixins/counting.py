from collections import Counter


class CountingMixin:


    def count_items(self):

        if "keywords" not in self.df.columns:

            raise ValueError(
                "keywords column missing"
            )


        counter = Counter()


        for value in self.df["keywords"]:

            if not isinstance(value,str):
                continue


            items = value.split(";")

            for item in items:

                item=item.strip()

                if item:

                    counter[item]+=1


        self.results["keyword_counts"] = dict(counter)


        return self.results["keyword_counts"]



    def count_groups(self):

        if self.groups is None:

            self.build_groups()


        counts={}


        for g in self.groups:

            counts[g]=(
                self.df["group"]
                .eq(g)
                .sum()
            )


        self.results["group_counts"]=counts


        return counts



    def count_authors(self):

        if "authors" not in self.df.columns:

            return {}


        counter=Counter()


        for value in self.df["authors"]:

            if not isinstance(value,str):
                continue


            for author in value.split(";"):

                author=author.strip()

                if author:

                    counter[author]+=1


        self.results["author_counts"]=dict(counter)


        return self.results["author_counts"]