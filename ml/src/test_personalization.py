import pandas as pd
import joblib


MODEL_FILE = "models/personalization_model.pkl"
DATA_FILE = "data/processed/test.csv"


# ============================================================
# Load model and test data
# ============================================================

model = joblib.load(MODEL_FILE)

df = pd.read_csv(DATA_FILE)


# ============================================================
# Select one environmental observation
# ============================================================

sample = df.iloc[0].copy()

city = sample["city"]

# Timestamp was removed during preprocessing.
# We use the hour/day/month already stored in the dataset.
hour = sample["hour"]
day_of_week = sample["day_of_week"]
month = sample["month"]


# ============================================================
# Cards to rank
# ============================================================

cards = [
    "aqi",
    "uv",
    "temperature",
    "humidity",
    "rain",
    "wind",
    "soil_moisture",
    "weather_condition"
]


personas = [
    "fitness",
    "farmer",
    "traveler"
]


# ============================================================
# Generate rankings
# ============================================================

print("\n================================")
print("PERSONALIZATION RANKING TEST")
print("================================")

print("City:", city)
print("Hour:", hour)
print("Day of week:", day_of_week)
print("Month:", month)


for persona in personas:

    rows = []

    for card in cards:

        row = sample.copy()

        row["persona"] = persona
        row["card"] = card

        rows.append(row)


    input_df = pd.DataFrame(rows)


    # ========================================================
    # Predict relevance
    # ========================================================

    scores = model.predict(input_df)

    scores = scores.clip(0, 1)


    results = pd.DataFrame({
        "card": cards,
        "score": scores
    })


    results = results.sort_values(
        "score",
        ascending=False
    ).reset_index(drop=True)


    # ========================================================
    # Display ranking
    # ========================================================

    print("\n--------------------------------")
    print(f"{persona.upper()} USER")
    print("--------------------------------")

    for index, result in results.iterrows():

        print(
            f"{index + 1}. "
            f"{result['card']:20s} "
            f"{result['score']:.4f}"
        )