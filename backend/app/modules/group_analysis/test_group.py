import pandas as pd

from .group_engine import SciAIGroupEngine



data = {

    "group":[
        "Iran",
        "Iran",
        "USA",
        "USA",
        "Germany"
    ],

    "keywords":[
        "AI;Machine Learning",
        "Library;AI",
        "Deep Learning;AI",
        "Data Mining",
        "Library;Information Science"
    ],

    "year":[
        2020,
        2021,
        2020,
        2022,
        2021
    ]

}



df = pd.DataFrame(data)



engine = SciAIGroupEngine(df)



result = engine.compute_all()



print(result)



print("\nASSOCIATIONS")

print(
    engine.results["associations"]
)
