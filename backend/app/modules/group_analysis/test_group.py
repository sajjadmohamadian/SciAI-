import pandas as pd

from .group_engine import SciAIGroupEngine


data = {
    "group": [
        "Iran",
        "Iran;USA",
        "USA",
        "USA;Germany",
        "Germany",
    ],

    "keywords": [
        "AI;Machine Learning",
        "Library;AI",
        "Deep Learning;AI",
        "Data Mining",
        "Library;Information Science",
    ],

    "year": [
        2020,
        2021,
        2020,
        2022,
        2021,
    ],

    "citation": [
        10,
        20,
        5,
        30,
        15,
    ],
}


df = pd.DataFrame(data)


engine = SciAIGroupEngine(df)


result = engine.compute_all()


print("COMPLETED")
print(result["completed"])


print("\nERRORS")
print(result["errors"])


print("\nGROUPS")
print(engine.results.get("groups"))


print("\nASSOCIATIONS")
print(engine.results.get("associations"))


print("\nTRENDS")
print(engine.results.get("trends"))


print("\nGROUP YEAR TRENDS")
print(engine.results.get("group_year_trends"))


print("\nGROUP YEAR SHARES")
print(engine.results.get("group_year_shares"))


print("\nGROUP PAIRS")
print(engine.results.get("group_pairs"))


print("\nOVERLAP MATRIX")
print(engine.results.get("overlap_matrix"))


print("\nSIMILARITY MATRIX")
print(engine.results.get("similarity_matrix"))

print("\nGROUP PMI")
print(engine.results.get("group_pmi"))

print("\nGROUP NPMI")
print(engine.results.get("group_npmi"))

print("\nGROUP LIFT")
print(engine.results.get("group_lift"))

print("\nNPMI MATRIX")
print(engine.results.get("npmi_matrix"))

print("\nLIFT MATRIX")
print(engine.results.get("lift_matrix"))

print("\nCONDITIONAL ASSOCIATIONS")
print(
    engine.results.get(
        "group_conditional_associations"
    )
)

print("\nCONDITIONAL MATRIX")
print(
    engine.results.get(
        "conditional_matrix"
    )
)

print("\nJOINT PROBABILITY MATRIX")
print(
    engine.results.get(
        "joint_probability_matrix"
    )
)

print("\nCONDITIONAL RISK RATIO MATRIX")
print(
    engine.results.get(
        "conditional_risk_ratio_matrix"
    )
)

print("\nCONDITIONAL ASSOCIATIONS")
print(engine.results.get("group_conditional_associations"))

print("\nCONDITIONAL MATRIX")
print(engine.results.get("conditional_matrix"))

print("\nJOINT PROBABILITY MATRIX")
print(engine.results.get("joint_probability_matrix"))

print("\nCONDITIONAL RISK RATIO MATRIX")
print(engine.results.get("conditional_risk_ratio_matrix"))