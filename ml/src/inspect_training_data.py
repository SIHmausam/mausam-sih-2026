import pandas as pd


FILE_PATH = "data/processed/training_data.csv"

df = pd.read_csv(FILE_PATH)


print("\n================================")
print("TRAINING DATA OVERVIEW")
print("================================")

print("Rows:", len(df))
print("Columns:", len(df.columns))


print("\n================================")
print("FIRST 10 ROWS")
print("================================")

print(df.head(10).to_string())


print("\n================================")
print("DATA TYPES")
print("================================")

print(df.dtypes)


print("\n================================")
print("MISSING VALUES")
print("================================")

missing = df.isnull().sum()

print(
    missing[missing > 0]
)


print("\n================================")
print("UNIQUE VALUES")
print("================================")

for column in [
    "city",
    "persona",
    "card",
    "weather_code",
    "is_daylight"
]:
    print(f"\n{column}:")
    print(df[column].unique())


print("\n================================")
print("RELEVANCE BY PERSONA")
print("================================")

print(
    df.groupby("persona")["relevance_score"]
    .agg(["mean", "min", "max"])
)


print("\n================================")
print("RELEVANCE BY CARD")
print("================================")

print(
    df.groupby("card")["relevance_score"]
    .agg(["mean", "min", "max"])
)


print("\n================================")
print("PERSONA + CARD RELEVANCE")
print("================================")

print(
    df.groupby(
        ["persona", "card"]
    )["relevance_score"]
    .mean()
    .round(3)
    .unstack()
)