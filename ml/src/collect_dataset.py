import os
import requests
import pandas as pd


# ============================================
# Configuration
# ============================================

CITIES = {
    "Delhi": {
        "latitude": 28.6139,
        "longitude": 77.2090
    },
    "Mumbai": {
        "latitude": 19.0760,
        "longitude": 72.8777
    },
    "Hyderabad": {
        "latitude": 17.3850,
        "longitude": 78.4867
    },
    "Lucknow": {
        "latitude": 26.8467,
        "longitude": 80.9462
    },
    "Kolkata": {
        "latitude": 22.5726,
        "longitude": 88.3639
    },
    "Ghaziabad": {
        "latitude": 28.6692,
        "longitude": 77.4538
    },
    "Chennai": {
        "latitude": 13.0827,
        "longitude": 80.2707
    },
    "Bengaluru": {
        "latitude": 12.9716,
        "longitude": 77.5946
    },

    # West
    "Ahmedabad": {
        "latitude": 23.0225,
        "longitude": 72.5714
    },
    "Jaipur": {
        "latitude": 26.9124,
        "longitude": 75.7873
    },
    "Pune": {
        "latitude": 18.5204,
        "longitude": 73.8567
    },
    "Surat": {
        "latitude": 21.1702,
        "longitude": 72.8311
    },
    "Nagpur": {
        "latitude": 21.1458,
        "longitude": 79.0882
    },

    # Central
    "Bhopal": {
        "latitude": 23.2599,
        "longitude": 77.4126
    },
    "Indore": {
        "latitude": 22.7196,
        "longitude": 75.8577
    },
    "Raipur": {
        "latitude": 21.2514,
        "longitude": 81.6296
    },

    # North
    "Chandigarh": {
        "latitude": 30.7333,
        "longitude": 76.7794
    },
    "Amritsar": {
        "latitude": 31.6340,
        "longitude": 74.8723
    },
    "Srinagar": {
        "latitude": 34.0837,
        "longitude": 74.7973
    },
    "Dehradun": {
        "latitude": 30.3165,
        "longitude": 78.0322
    },
    "Shimla": {
        "latitude": 31.1048,
        "longitude": 77.1734
    },
    "Dharamshala": {
        "latitude": 32.2190,
        "longitude": 76.3234
    },

    # East / Northeast
    "Patna": {
        "latitude": 25.5941,
        "longitude": 85.1376
    },
    "Ranchi": {
        "latitude": 23.3441,
        "longitude": 85.3096
    },
    "Bhubaneswar": {
        "latitude": 20.2961,
        "longitude": 85.8245
    },
    "Guwahati": {
        "latitude": 26.1445,
        "longitude": 91.7362
    },
    "Shillong": {
        "latitude": 25.5788,
        "longitude": 91.8933
    },
    "Varanasi": {
        "latitude": 25.3176,
        "longitude": 82.9739
    },
    "Agra": {
        "latitude": 27.1767,
        "longitude": 78.0081
    },
    "Kanpur": {
        "latitude": 26.4499,
        "longitude": 80.3319
    }
}

START_DATE = "2026-08-25"
END_DATE = "2026-08-30"

WEATHER_URL = "https://archive-api.open-meteo.com/v1/archive"
AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

OUTPUT_FILE = "data/raw/historical_data.csv"


# ============================================
# Fetch historical weather
# ============================================

def fetch_weather(latitude, longitude):
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": START_DATE,
        "end_date": END_DATE,
        "hourly": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "apparent_temperature,"
            "precipitation,"
            "rain,"
            "weather_code,"
            "wind_speed_10m,"
            "soil_moisture_0_to_7cm"
        ),
        "daily": "sunrise,sunset",
        "timezone": "Asia/Kolkata"
    }

    response = requests.get(
        WEATHER_URL,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


# ============================================
# Fetch historical air quality
# ============================================

def fetch_air_quality(latitude, longitude):
    params = {
        "latitude": latitude,
        "longitude": longitude,
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

    response = requests.get(
        AIR_QUALITY_URL,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


# ============================================
# Convert one city into a DataFrame
# ============================================

def collect_city_data(city_name, latitude, longitude):

    print(f"\nCollecting data for {city_name}...")

    weather_data = fetch_weather(latitude, longitude)

    air_quality_data = fetch_air_quality(
        latitude,
        longitude
    )

    # -----------------------------
    # Weather DataFrame
    # -----------------------------

    weather_df = pd.DataFrame(
        weather_data["hourly"]
    )

    weather_df["timestamp"] = pd.to_datetime(
        weather_df["time"]
    )

    weather_df = weather_df.drop(
        columns=["time"]
    )

    # -----------------------------
    # Air Quality DataFrame
    # -----------------------------

    air_quality_df = pd.DataFrame(
        air_quality_data["hourly"]
    )

    air_quality_df["timestamp"] = pd.to_datetime(
        air_quality_df["time"]
    )

    air_quality_df = air_quality_df.drop(
        columns=["time"]
    )

    # -----------------------------
    # Merge weather + air quality
    # -----------------------------

    df = pd.merge(
        weather_df,
        air_quality_df,
        on="timestamp",
        how="inner"
    )

    # -----------------------------
    # Add sunrise/sunset
    # -----------------------------

    sun_df = pd.DataFrame({
        "date": pd.to_datetime(
            weather_data["daily"]["time"]
        ),
        "sunrise": pd.to_datetime(
            weather_data["daily"]["sunrise"]
        ),
        "sunset": pd.to_datetime(
            weather_data["daily"]["sunset"]
        )
    })

    df["date"] = df["timestamp"].dt.date
    sun_df["date"] = sun_df["date"].dt.date

    df = pd.merge(
        df,
        sun_df[["date", "sunrise", "sunset"]],
        on="date",
        how="left"
    )

    # -----------------------------
    # Derived daylight feature
    # -----------------------------

    df["is_daylight"] = (
        (df["timestamp"] >= df["sunrise"]) &
        (df["timestamp"] <= df["sunset"])
    )

    # -----------------------------
    # Add city
    # -----------------------------

    df["city"] = city_name

    # -----------------------------
    # Remove temporary date column
    # -----------------------------

    df = df.drop(
        columns=["date"]
    )

    return df


# ============================================
# Main
# ============================================

if __name__ == "__main__":

    all_city_data = []

    for city_name, location in CITIES.items():

        df = collect_city_data(
            city_name,
            location["latitude"],
            location["longitude"]
        )

        all_city_data.append(df)

        print(
            f"{city_name}: "
            f"{len(df)} records collected"
        )

    # Combine all cities
    final_df = pd.concat(
        all_city_data,
        ignore_index=True
    )

    # Create output directory if needed
    os.makedirs(
        os.path.dirname(OUTPUT_FILE),
        exist_ok=True
    )

    # Save dataset
    final_df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print("\n================================")
    print("Dataset collection complete!")
    print("================================")

    print(f"Total records: {len(final_df)}")
    print(f"Total columns: {len(final_df.columns)}")
    print(f"Saved to: {OUTPUT_FILE}")

    print("\nColumns:")
    print(final_df.columns.tolist())