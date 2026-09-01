import requests
import pandas as pd


LATITUDE = 28.6692
LONGITUDE = 77.4538

START_DATE = "2026-08-25"
END_DATE = "2026-08-30"

WEATHER_URL = "https://archive-api.open-meteo.com/v1/archive"
AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"


# -----------------------------
# 1. Fetch historical weather
# -----------------------------

weather_params = {
    "latitude": LATITUDE,
    "longitude": LONGITUDE,
    "start_date": START_DATE,
    "end_date": END_DATE,
    "hourly": (
        "temperature_2m,"
        "relative_humidity_2m,"
        "apparent_temperature,"
        "precipitation,"
        "rain,"
        "precipitation_probability,"
        "weather_code,"
        "wind_speed_10m,"
        "visibility,"
        "soil_moisture_0_to_7cm"
    ),
    "daily": "sunrise,sunset",
    "timezone": "Asia/Kolkata"
}

weather_response = requests.get(WEATHER_URL, params=weather_params)
weather_response.raise_for_status()

weather_data = weather_response.json()

print("\nSunrise:", weather_data["daily"]["sunrise"])
print("Sunset:", weather_data["daily"]["sunset"])


# -----------------------------
# 2. Fetch historical air quality
# -----------------------------

air_quality_params = {
    "latitude": LATITUDE,
    "longitude": LONGITUDE,
    "start_date": START_DATE,
    "end_date": END_DATE,
    "hourly": (
        "european_aqi,"
        "us_aqi,"
        "uv_index,"
        "pm2_5,"
        "pm10,"
        "nitrogen_dioxide,"
        "sulphur_dioxide,"
        "carbon_monoxide,"
        "ozone"
    ),
    "timezone": "Asia/Kolkata"
}

air_quality_response = requests.get(
    AIR_QUALITY_URL,
    params=air_quality_params
)

air_quality_response.raise_for_status()

air_quality_data = air_quality_response.json()


# -----------------------------
# 3. Convert weather to DataFrame
# -----------------------------

weather_df = pd.DataFrame(weather_data["hourly"])

weather_df["timestamp"] = pd.to_datetime(
    weather_df["time"]
)

weather_df = weather_df.drop(columns=["time"])


# -----------------------------
# 4. Convert air quality to DataFrame
# -----------------------------

air_quality_df = pd.DataFrame(air_quality_data["hourly"])

air_quality_df["timestamp"] = pd.to_datetime(
    air_quality_df["time"]
)

air_quality_df = air_quality_df.drop(columns=["time"])


# -----------------------------
# 5. Merge both datasets
# -----------------------------

df = pd.merge(
    weather_df,
    air_quality_df,
    on="timestamp",
    how="inner"
)

# Convert daily sunrise/sunset data into a DataFrame
sun_df = pd.DataFrame({
    "date": pd.to_datetime(weather_data["daily"]["time"]),
    "sunrise": pd.to_datetime(weather_data["daily"]["sunrise"]),
    "sunset": pd.to_datetime(weather_data["daily"]["sunset"])
})

# Create date column for matching
df["date"] = df["timestamp"].dt.date
sun_df["date"] = sun_df["date"].dt.date

# Merge sunrise/sunset into hourly data
df = pd.merge(
    df,
    sun_df[["date", "sunrise", "sunset"]],
    on="date",
    how="left"
)

# Determine whether each timestamp is during daylight
df["is_daylight"] = (
    (df["timestamp"] >= df["sunrise"]) &
    (df["timestamp"] <= df["sunset"])
)


# -----------------------------
# 6. Add location
# -----------------------------

df["city"] = "Ghaziabad"


# -----------------------------
# 7. Display result
# -----------------------------

print("\nCombined DataFrame:")
print(df.head())

print("\nShape:")
print(df.shape)

print("\nColumns:")
print(df.columns.tolist())

print("\nDaylight check:")
print(
    df[
        ["timestamp", "sunrise", "sunset", "is_daylight"]
    ].head(10)
)

print("\nDaylight counts:")
print(df["is_daylight"].value_counts())