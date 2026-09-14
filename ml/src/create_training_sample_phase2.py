import pandas as pd

INPUT_FILE = "data/processed/train_phase2.csv"
OUTPUT_FILE = "data/processed/train_phase2_sample.csv"

TARGET_ROWS = 500_000
RANDOM_STATE = 42

print("\n================================")
print("CREATING PHASE 2 TRAINING SAMPLE")
print("================================")

df = pd.read_csv(INPUT_FILE)

print("Full training rows:", len(df))

# Stratify by persona + card.
# This preserves the relative representation of every eligible
# persona/card combination while sampling from the full training corpus.
group_cols = ["persona", "card"]

groups = df.groupby(group_cols, sort=False)

group_sizes = groups.size()

# Proportional allocation with a minimum of 1 row per group.
allocations = (
    group_sizes / group_sizes.sum() * TARGET_ROWS
).round().astype(int)

# Correct rounding difference so the final sample is exactly TARGET_ROWS.
difference = TARGET_ROWS - allocations.sum()

if difference != 0:
    order = allocations.sort_values(ascending=False).index
    step = 1 if difference > 0 else -1

    for idx in order[:abs(difference)]:
        allocations.loc[idx] += step

samples = []

for key, group in groups:
    n = int(allocations.loc[key])
    n = min(n, len(group))

    samples.append(
        group.sample(
            n=n,
            random_state=RANDOM_STATE
        )
    )

sample_df = pd.concat(
    samples,
    ignore_index=True
)

# Shuffle the final sample.
sample_df = sample_df.sample(
    frac=1,
    random_state=RANDOM_STATE
).reset_index(drop=True)

sample_df.to_csv(
    OUTPUT_FILE,
    index=False
)

print("\n================================")
print("PHASE 2 SAMPLE CREATED")
print("================================")

print("Sample rows:", len(sample_df))
print("Columns:", len(sample_df.columns))

print("\nPersona/card distribution:")
print(
    sample_df.groupby(["persona", "card"]).size().to_string()
)

print("\nSaved:")
print(OUTPUT_FILE)
