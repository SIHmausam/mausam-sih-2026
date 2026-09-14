import os
import numpy as np
import pandas as pd

from src.phase2_config import PERSONAS, CARDS, ELIGIBILITY


INPUT_FILE = "data/raw/historical_data_phase2.csv"
OUTPUT_FILE = "data/processed/training_data_phase2.csv"


# ============================================================
# Persona affinity
# ============================================================

AFFINITY = {
    "temperature": {
        "health_conscious": 0.85,
        "fitness": 0.90,
        "surfer": 0.75,
        "traveler": 0.85,
        "parents_families": 0.80,
        "farmer": 0.90,
        "commuter": 0.70,
        "event_planner": 0.90,
    },

    "weather_conditions": {
        "health_conscious": 0.90,
        "fitness": 0.75,
        "surfer": 0.65,
        "traveler": 0.90,
        "parents_families": 0.90,
        "farmer": 0.85,
        "commuter": 0.90,
        "event_planner": 0.90,
    },

    "humidity": {
        "health_conscious": 1.00,
        "fitness": 0.70,
        "surfer": 0.50,
        "traveler": 0.55,
        "parents_families": 0.65,
        "farmer": 0.85,
        "commuter": 0.55,
        "event_planner": 0.70,
    },

    "rain_forecast": {
        "health_conscious": 0.90,
        "fitness": 0.85,
        "surfer": 0.70,
        "traveler": 0.90,
        "parents_families": 0.95,
        "farmer": 0.95,
        "commuter": 0.95,
        "event_planner": 0.95,
    },

    "wind": {
        "health_conscious": 0.65,
        "fitness": 0.85,
        "surfer": 0.90,
        "traveler": 0.80,
        "parents_families": 0.75,
        "farmer": 0.75,
        "commuter": 0.85,
        "event_planner": 0.80,
    },

    "air_quality": {
        "health_conscious": 1.00,
        "fitness": 0.95,
        "surfer": 0.70,
        "traveler": 0.70,
        "parents_families": 0.90,
        "commuter": 0.80,
        "event_planner": 0.75,
    },

    "uv_allergy": {
        "health_conscious": 1.00,
        "fitness": 0.90,
        "surfer": 0.85,
        "traveler": 0.80,
        "parents_families": 0.80,
        "farmer": 0.65,
        "event_planner": 0.70,
    },

    "running_conditions": {
        "fitness": 1.00,
    },

    "surf_conditions": {
        "surfer": 1.00,
    },

    "tide_water": {
        "surfer": 1.00,
    },

    "farm_garden": {
        "farmer": 1.00,
    },

    "commute_conditions": {
        "traveler": 0.80,
        "parents_families": 0.90,
        "commuter": 1.00,
        "event_planner": 0.65,
    },

    "travel_conditions": {
        "traveler": 1.00,
    },

    "family_school": {
        "parents_families": 1.00,
    },

    "event_conditions": {
        "event_planner": 1.00,
    },
}


# ============================================================
# Helpers
# ============================================================

def clip01(value):
    return float(np.clip(value, 0.0, 1.0))


def scale(value, low, high):
    if high == low:
        return 0.0
    return clip01((value - low) / (high - low))


def inverse_scale(value, low, high):
    return 1.0 - scale(value, low, high)


def mean_score(*values):
    values = [clip01(v) for v in values]
    return clip01(sum(values) / len(values))


# ============================================================
# Derived environmental signals
# ============================================================

def heat_risk(row):
    temp = row["apparent_temperature"]
    return scale(temp, 28.0, 40.0)


def frost_risk(row):
    temp = row["temperature_2m"]
    return inverse_scale(temp, 0.0, 8.0)


def fog_risk(row):
    visibility = row["visibility"]
    humidity = row["relative_humidity_2m"]

    visibility_risk = inverse_scale(visibility, 1000.0, 10000.0)
    humidity_risk = scale(humidity, 75.0, 100.0)

    return mean_score(visibility_risk, humidity_risk)


def storm_risk(row):
    weather = row["weather_code"]
    wind_gust = row["wind_gusts_10m"]
    rain = row["rain"]

    weather_signal = 1.0 if weather in {
        95, 96, 99
    } else 0.0

    gust_signal = scale(wind_gust, 35.0, 70.0)
    rain_signal = scale(rain, 5.0, 30.0)

    return mean_score(
        weather_signal,
        gust_signal,
        rain_signal
    )


def rain_risk(row):
    probability = row["precipitation_probability"]
    precipitation = row["precipitation"]
    showers = row["showers"]
    hours = row["precipitation_hours"]

    probability_score = scale(probability, 20.0, 90.0)
    intensity_score = scale(
        max(precipitation, showers),
        0.5,
        10.0
    )
    duration_score = scale(hours, 2.0, 12.0)

    return mean_score(
        probability_score,
        intensity_score,
        duration_score
    )


def air_quality_risk(row):
    aqi = max(
        row["us_aqi"],
        row["european_aqi"]
    )

    aqi_score = scale(aqi, 50.0, 200.0)
    pm25_score = scale(row["pm2_5"], 15.0, 75.0)
    pm10_score = scale(row["pm10"], 30.0, 150.0)

    return mean_score(
        aqi_score,
        pm25_score,
        pm10_score
    )


def uv_risk(row):
    uv = max(
        row["uv_index"],
        row["uv_index_clear_sky"]
    )

    return scale(uv, 2.0, 10.0)


def comfort_index(row):
    temperature_comfort = 1.0 - scale(
        abs(row["apparent_temperature"] - 22.0),
        0.0,
        18.0
    )

    humidity_comfort = 1.0 - scale(
        abs(row["relative_humidity_2m"] - 55.0),
        0.0,
        45.0
    )

    return mean_score(
        temperature_comfort,
        humidity_comfort
    )


def running_score(row):
    heat = heat_risk(row)
    rain = rain_risk(row)
    wind = scale(row["wind_gusts_10m"], 15.0, 50.0)
    uv = uv_risk(row)

    suitability = (
        0.35 * (1.0 - heat)
        + 0.30 * (1.0 - rain)
        + 0.20 * (1.0 - wind)
        + 0.15 * (1.0 - uv)
    )

    return clip01(suitability)


def surf_score(row):
    wave = scale(row["wave_height"], 0.5, 3.0)
    period = scale(row["wave_period"], 6.0, 14.0)
    swell = scale(row["swell_wave_height"], 0.3, 2.5)
    wind = inverse_scale(row["wind_speed_10m"], 5.0, 30.0)
    gust = inverse_scale(row["wind_gusts_10m"], 10.0, 50.0)

    return clip01(
        0.30 * wave
        + 0.25 * period
        + 0.20 * swell
        + 0.15 * wind
        + 0.10 * gust
    )


def soil_status(row):
    moisture = row["soil_moisture_0_to_7cm"]

    if moisture < 0.15:
        return 1.0
    if moisture > 0.40:
        return 0.8

    return 0.5


def water_stress(row):
    moisture = row["soil_moisture_0_to_7cm"]
    et0 = row["et0_fao_evapotranspiration"]

    dryness = inverse_scale(moisture, 0.10, 0.40)
    evap_demand = scale(et0, 0.02, 0.30)

    return mean_score(
        dryness,
        evap_demand
    )


def planting_condition(row):
    moisture = row["soil_moisture_0_to_7cm"]
    frost = frost_risk(row)
    rain = rain_risk(row)
    heat = heat_risk(row)

    moisture_suitability = 1.0 - abs(
        scale(moisture, 0.10, 0.45) - 0.60
    )

    return clip01(
        0.40 * moisture_suitability
        + 0.25 * (1.0 - frost)
        + 0.20 * (1.0 - rain)
        + 0.15 * (1.0 - heat)
    )


def commute_score(row):
    visibility = scale(row["visibility"], 1000.0, 10000.0)
    rain = rain_risk(row)
    fog = fog_risk(row)
    storm = storm_risk(row)
    wind = scale(row["wind_gusts_10m"], 15.0, 50.0)

    return clip01(
        0.30 * visibility
        + 0.25 * (1.0 - rain)
        + 0.20 * (1.0 - fog)
        + 0.15 * (1.0 - storm)
        + 0.10 * (1.0 - wind)
    )


def travel_risk(row):
    rain = rain_risk(row)
    storm = storm_risk(row)
    fog = fog_risk(row)
    visibility = inverse_scale(
        row["visibility"],
        1000.0,
        10000.0
    )
    wind = scale(row["wind_gusts_10m"], 20.0, 60.0)

    return mean_score(
        rain,
        storm,
        fog,
        visibility,
        wind
    )


def family_school_score(row):
    rain = rain_risk(row)
    storm = storm_risk(row)
    fog = fog_risk(row)
    visibility = inverse_scale(
        row["visibility"],
        1000.0,
        10000.0
    )

    return clip01(
        0.30 * (1.0 - rain)
        + 0.25 * (1.0 - storm)
        + 0.20 * (1.0 - fog)
        + 0.25 * (1.0 - visibility)
    )


def event_score(row):
    comfort = comfort_index(row)
    rain = rain_risk(row)
    storm = storm_risk(row)
    wind = scale(row["wind_gusts_10m"], 15.0, 50.0)

    return clip01(
        0.40 * comfort
        + 0.30 * (1.0 - rain)
        + 0.20 * (1.0 - storm)
        + 0.10 * (1.0 - wind)
    )


# ============================================================
# Card-specific condition relevance + urgency
# ============================================================

def card_signals(row, card):
    heat = heat_risk(row)
    rain = rain_risk(row)
    wind = scale(row["wind_gusts_10m"], 15.0, 50.0)
    fog = fog_risk(row)
    storm = storm_risk(row)
    air = air_quality_risk(row)
    uv = uv_risk(row)
    comfort = comfort_index(row)

    if card == "temperature":
        relevance = mean_score(
            scale(abs(row["temperature_2m"] - 22.0), 0.0, 18.0),
            scale(abs(row["apparent_temperature"] - 22.0), 0.0, 18.0)
        )
        urgency = heat

    elif card == "weather_conditions":
        relevance = mean_score(
            scale(row["cloud_cover"], 20.0, 90.0),
            rain,
            wind
        )
        urgency = mean_score(storm, fog, rain)

    elif card == "humidity":
        humidity_deviation = abs(
            row["relative_humidity_2m"] - 55.0
        )

        relevance = scale(
            humidity_deviation,
            10.0,
            40.0
        )

        urgency = scale(
            humidity_deviation,
            20.0,
            45.0
        )

    elif card == "rain_forecast":
        relevance = rain
        urgency = mean_score(
            rain,
            storm
        )

    elif card == "wind":
        relevance = scale(
            row["wind_speed_10m"],
            5.0,
            30.0
        )
        urgency = mean_score(
            wind,
            scale(row["wind_gusts_10m"], 25.0, 60.0)
        )

    elif card == "air_quality":
        relevance = air
        urgency = air

    elif card == "uv_allergy":
        relevance = mean_score(
            uv,
            air,
            scale(row["relative_humidity_2m"], 40.0, 100.0)
        )
        urgency = mean_score(uv, air)

    elif card == "running_conditions":
        suitability = running_score(row)
        relevance = suitability
        urgency = mean_score(
            heat,
            rain,
            wind,
            uv
        )

    elif card == "surf_conditions":
        suitability = surf_score(row)
        relevance = suitability
        urgency = mean_score(
            wind,
            scale(row["wave_height"], 2.0, 5.0)
        )

    elif card == "tide_water":
        sea_level_change_signal = 0.5
        water_temp_signal = scale(
            abs(row["sea_surface_temperature"] - 25.0),
            0.0,
            10.0
        )

        relevance = mean_score(
            sea_level_change_signal,
            water_temp_signal
        )
        urgency = water_temp_signal

    elif card == "farm_garden":
        farm_suitability = planting_condition(row)
        relevance = mean_score(
            farm_suitability,
            water_stress(row),
            soil_status(row)
        )
        urgency = mean_score(
            frost_risk(row),
            water_stress(row),
            heat
        )

    elif card == "commute_conditions":
        suitability = commute_score(row)
        relevance = 1.0 - suitability
        urgency = mean_score(
            fog,
            storm,
            rain
        )

    elif card == "travel_conditions":
        risk = travel_risk(row)
        relevance = risk
        urgency = risk

    elif card == "family_school":
        suitability = family_school_score(row)
        relevance = 1.0 - suitability
        urgency = mean_score(
            rain,
            storm,
            fog
        )

    elif card == "event_conditions":
        suitability = event_score(row)
        relevance = 1.0 - suitability
        urgency = mean_score(
            rain,
            storm,
            wind
        )

    else:
        raise ValueError(f"Unknown card: {card}")

    return clip01(relevance), clip01(urgency)


# ============================================================
# Final deterministic relevance label
# ============================================================

def calculate_relevance(row, persona, card):
    affinity = AFFINITY[card][persona]

    condition_relevance, urgency = card_signals(
        row,
        card
    )

    return round(
        clip01(
            0.40 * affinity
            + 0.40 * condition_relevance
            + 0.20 * urgency
        ),
        4
    )


# ============================================================
# Generate eligible training examples
# ============================================================


def main():

    print("\n================================")
    print("CREATING PHASE 2 TRAINING DATA")
    print("================================")

    df = pd.read_csv(INPUT_FILE)

    print("Input rows:", len(df))
    print("Input columns:", len(df.columns))

    training_rows = []

    for _, row in df.iterrows():

        for persona in PERSONAS:

            for card in CARDS:

                if persona not in ELIGIBILITY[card]:
                    continue

                # Marine cards require actual marine data.
                if card in {"surf_conditions", "tide_water"}:
                    if not bool(row["marine_data_available"]):
                        continue

                training_rows.append({
                    "timestamp": row["timestamp"],
                    "city": row["city"],
                    "persona": persona,
                    "card": card,

                    "temperature_2m": row["temperature_2m"],
                    "relative_humidity_2m": row["relative_humidity_2m"],
                    "dew_point_2m": row["dew_point_2m"],
                    "apparent_temperature": row["apparent_temperature"],
                    "precipitation": row["precipitation"],
                    "rain": row["rain"],
                    "showers": row["showers"],
                    "precipitation_probability": row["precipitation_probability"],
                    "precipitation_hours": row["precipitation_hours"],
                    "weather_code": row["weather_code"],
                    "cloud_cover": row["cloud_cover"],
                    "visibility": row["visibility"],
                    "wind_speed_10m": row["wind_speed_10m"],
                    "wind_direction_10m": row["wind_direction_10m"],
                    "wind_gusts_10m": row["wind_gusts_10m"],

                    "soil_moisture_0_to_7cm": row["soil_moisture_0_to_7cm"],
                    "soil_moisture_7_to_28cm": row["soil_moisture_7_to_28cm"],
                    "soil_moisture_28_to_100cm": row["soil_moisture_28_to_100cm"],
                    "soil_moisture_100_to_255cm": row["soil_moisture_100_to_255cm"],
                    "soil_temperature_0_to_7cm": row["soil_temperature_0_to_7cm"],
                    "soil_temperature_7_to_28cm": row["soil_temperature_7_to_28cm"],
                    "soil_temperature_28_to_100cm": row["soil_temperature_28_to_100cm"],
                    "soil_temperature_100_to_255cm": row["soil_temperature_100_to_255cm"],
                    "et0_fao_evapotranspiration": row["et0_fao_evapotranspiration"],

                    "us_aqi": row["us_aqi"],
                    "european_aqi": row["european_aqi"],
                    "pm2_5": row["pm2_5"],
                    "pm10": row["pm10"],
                    "nitrogen_dioxide": row["nitrogen_dioxide"],
                    "sulphur_dioxide": row["sulphur_dioxide"],
                    "carbon_monoxide": row["carbon_monoxide"],
                    "ozone": row["ozone"],
                    "uv_index": row["uv_index"],
                    "uv_index_clear_sky": row["uv_index_clear_sky"],

                    "wave_height": row["wave_height"],
                    "wave_direction": row["wave_direction"],
                    "wave_period": row["wave_period"],
                    "swell_wave_height": row["swell_wave_height"],
                    "swell_wave_direction": row["swell_wave_direction"],
                    "swell_wave_period": row["swell_wave_period"],
                    "sea_level_height_msl": row["sea_level_height_msl"],
                    "sea_surface_temperature": row["sea_surface_temperature"],
                    "marine_data_available": row["marine_data_available"],

                    "is_daylight": row["is_daylight"],

                    "relevance_score": calculate_relevance(
                        row,
                        persona,
                        card
                    ),
                })


    training_df = pd.DataFrame(training_rows)


    # ============================================================
    # Save
    # ============================================================

    os.makedirs(
        os.path.dirname(OUTPUT_FILE),
        exist_ok=True
    )

    training_df.to_csv(
        OUTPUT_FILE,
        index=False
    )


    # ============================================================
    # Summary
    # ============================================================

    print("\n================================")
    print("PHASE 2 TRAINING DATA CREATED")
    print("================================")

    print("Rows:", len(training_df))
    print("Columns:", len(training_df.columns))

    print("\nPersonas:")
    print(training_df["persona"].value_counts().to_string())

    print("\nCards:")
    print(training_df["card"].value_counts().to_string())

    print("\nMarine training rows:")
    print(
        training_df[
            training_df["card"].isin(
                ["surf_conditions", "tide_water"]
            )
        ].groupby(["persona", "card"]).size().to_string()
    )

    print("\nRelevance score range:")
    print(
        training_df["relevance_score"].min(),
        "to",
        training_df["relevance_score"].max()
    )

    print("\nSaved to:")
    print(OUTPUT_FILE)



if __name__ == "__main__":
    main()
