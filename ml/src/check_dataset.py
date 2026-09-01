import pandas as pd


FILE_PATH = "data/raw/historical_data.csv"


# Load dataset
df = pd.read_csv(FILE_PATH)


print("\n================================")
print("DATASET OVERVIEW")
print("================================")

print("Rows:", len(df))
print("Columns:", len(df.columns))

print("\nColumn names:")
print(df.columns.tolist())


# --------------------------------
# Missing values
# --------------------------------

print("\n================================")
print("MISSING VALUES")
print("================================")

missing = df.isnull().sum()

missing_percentage = (
    df.isnull().mean() * 100
).round(2)

missing_report = pd.DataFrame({
    "missing_count": missing,
    "missing_percentage": missing_percentage
})

print(
    missing_report[
        missing_report["missing_count"] > 0
    ]
)


# --------------------------------
# Data types
# --------------------------------

print("\n================================")
print("DATA TYPES")
print("================================")

print(df.dtypes)


# --------------------------------
# Duplicate rows
# --------------------------------

print("\n================================")
print("DUPLICATES")
print("================================")

print(
    "Duplicate rows:",
    df.duplicated().sum()
)


# --------------------------------
# Numerical summary
# --------------------------------

print("\n================================")
print("NUMERICAL SUMMARY")
print("================================")

print(
    df.describe().T
)