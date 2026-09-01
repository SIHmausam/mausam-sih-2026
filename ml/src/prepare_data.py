import pandas as pd
from sklearn.model_selection import train_test_split


INPUT_FILE = "data/processed/training_data.csv"


# ============================================================
# Load data
# ============================================================

df = pd.read_csv(INPUT_FILE)

df["timestamp"] = pd.to_datetime(df["timestamp"])


# ============================================================
# Create time features
# ============================================================

df["hour"] = df["timestamp"].dt.hour

df["day_of_week"] = df["timestamp"].dt.dayofweek

df["month"] = df["timestamp"].dt.month


# ============================================================
# Sort chronologically
# ============================================================

df = df.sort_values("timestamp")


# ============================================================
# Time-based split
# ============================================================

unique_dates = sorted(
    df["timestamp"].dt.date.unique()
)

test_date = unique_dates[-1]

train_df = df[
    df["timestamp"].dt.date < test_date
].copy()

test_df = df[
    df["timestamp"].dt.date == test_date
].copy()


# ============================================================
# Remove raw timestamp
# ============================================================

train_df = train_df.drop(columns=["timestamp"])

test_df = test_df.drop(columns=["timestamp"])


# ============================================================
# Save
# ============================================================

train_df.to_csv(
    "data/processed/train.csv",
    index=False
)

test_df.to_csv(
    "data/processed/test.csv",
    index=False
)


# ============================================================
# Summary
# ============================================================

print("\n================================")
print("DATA PREPARATION COMPLETE")
print("================================")

print("Training rows:", len(train_df))
print("Testing rows:", len(test_df))

print("\nTraining date range:")
print(
    unique_dates[0],
    "to",
    unique_dates[-2]
)

print("\nTesting date:")
print(test_date)

print("\nTraining columns:")
print(train_df.columns.tolist())

print("\nSaved:")
print("data/processed/train.csv")
print("data/processed/test.csv")