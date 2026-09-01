import pandas as pd
import numpy as np


INPUT_FILE = "data/raw/historical_data.csv"
OUTPUT_FILE = "data/processed/training_data.csv"


# ============================================================
# Load environmental dataset
# ============================================================

df = pd.read_csv(INPUT_FILE)


# ============================================================
# Normalize a value between 0 and 1
# ============================================================

def normalize(value, minimum, maximum):
    if maximum == minimum:
        return 0.0

    score = (value - minimum) / (maximum - minimum)

    return float(np.clip(score, 0, 1))


# ============================================================
# Generate relevance score
# ============================================================

def calculate_relevance(row, persona, card):

    temperature = row["temperature_2m"]
    humidity = row["relative_humidity_2m"]
    rain = row["rain"]
    wind = row["wind_speed_10m"]
    soil_moisture = row["soil_moisture_0_to_7cm"]
    aqi = row["us_aqi"]
    uv = row["uv_index"]
    weather_code = row["weather_code"]

    # ---------------------------------------------------------
    # Environmental severity scores
    # ---------------------------------------------------------

    aqi_score = normalize(aqi, 50, 250)

    uv_score = normalize(uv, 2, 10)

    rain_score = normalize(rain, 0, 5)

    wind_score = normalize(wind, 5, 20)

    humidity_score = normalize(humidity, 40, 100)

    soil_dryness_score = 1 - normalize(
        soil_moisture,
        0.10,
        0.45
    )

    heat_score = normalize(
        temperature,
        25,
        38
    )

    weather_score = 1.0 if weather_code >= 51 else 0.1


    # ---------------------------------------------------------
    # Persona-specific importance
    # ---------------------------------------------------------

    importance = {

        "fitness": {
            "aqi": 0.95,
            "uv": 0.90,
            "temperature": 0.85,
            "humidity": 0.75,
            "rain": 0.70,
            "wind": 0.60,
            "soil_moisture": 0.05,
            "weather_condition": 0.75
        },

        "farmer": {
            "aqi": 0.30,
            "uv": 0.35,
            "temperature": 0.80,
            "humidity": 0.85,
            "rain": 0.95,
            "wind": 0.70,
            "soil_moisture": 1.00,
            "weather_condition": 0.90
        },

        "traveler": {
            "aqi": 0.55,
            "uv": 0.65,
            "temperature": 0.90,
            "humidity": 0.70,
            "rain": 0.95,
            "wind": 0.75,
            "soil_moisture": 0.03,
            "weather_condition": 1.00
        }
    }


    # ---------------------------------------------------------
    # Environmental relevance
    # ---------------------------------------------------------

    environmental_score = {

        "aqi": aqi_score,

        "uv": uv_score,

        "temperature": heat_score,

        "humidity": humidity_score,

        "rain": rain_score,

        "wind": wind_score,

        "soil_moisture": soil_dryness_score,

        "weather_condition": weather_score
    }


    # ---------------------------------------------------------
    # Combine persona importance with current conditions
    # ---------------------------------------------------------

    base_importance = importance[persona][card]

    condition_score = environmental_score[card]

    relevance = (
        0.6 * base_importance
        +
        0.4 * condition_score
    )


    return round(
        float(np.clip(relevance, 0, 1)),
        4
    )


# ============================================================
# Cards used by the personalization system
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
# Generate training examples
# ============================================================

training_rows = []


for _, row in df.iterrows():

    for persona in personas:

        for card in cards:

            training_rows.append({
                "timestamp": row["timestamp"],
                "city": row["city"],
                "persona": persona,
                "card": card,

                "temperature_2m": row["temperature_2m"],
                "relative_humidity_2m": row["relative_humidity_2m"],
                "apparent_temperature": row["apparent_temperature"],
                "precipitation": row["precipitation"],
                "rain": row["rain"],
                "weather_code": row["weather_code"],
                "wind_speed_10m": row["wind_speed_10m"],
                "soil_moisture_0_to_7cm": row["soil_moisture_0_to_7cm"],

                "us_aqi": row["us_aqi"],
                "european_aqi": row["european_aqi"],
                "uv_index": row["uv_index"],
                "pm2_5": row["pm2_5"],
                "pm10": row["pm10"],
                "nitrogen_dioxide": row["nitrogen_dioxide"],
                "sulphur_dioxide": row["sulphur_dioxide"],
                "carbon_monoxide": row["carbon_monoxide"],
                "ozone": row["ozone"],

                "is_daylight": row["is_daylight"],

                "relevance_score": calculate_relevance(
                    row,
                    persona,
                    card
                )
            })


# ============================================================
# Create DataFrame
# ============================================================

training_df = pd.DataFrame(training_rows)


# ============================================================
# Save
# ============================================================

training_df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# Summary
# ============================================================

print("\n================================")
print("TRAINING DATA CREATED")
print("================================")

print("Rows:", len(training_df))
print("Columns:", len(training_df.columns))

print("\nPersonas:")
print(training_df["persona"].value_counts())

print("\nCards:")
print(training_df["card"].value_counts())

print("\nRelevance score range:")
print(
    training_df["relevance_score"].min(),
    "to",
    training_df["relevance_score"].max()
)

print("\nSaved to:")
print(OUTPUT_FILE)