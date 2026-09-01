LOCATIONS = {
    "Delhi": {
        "latitude": 28.6139,
        "longitude": 77.2090
    },
    "Mumbai": {
        "latitude": 19.0760,
        "longitude": 72.8777
    },
    "Bengaluru": {
        "latitude": 12.9716,
        "longitude": 77.5946
    },
    "Chennai": {
        "latitude": 13.0827,
        "longitude": 80.2707
    },
    "Kolkata": {
        "latitude": 22.5726,
        "longitude": 88.3639
    },
    "Hyderabad": {
        "latitude": 17.3850,
        "longitude": 78.4867
    },
    "Lucknow": {
        "latitude": 26.8467,
        "longitude": 80.9462
    },
    "Ghaziabad": {
        "latitude": 28.6692,
        "longitude": 77.4538
    }
}

import requests


WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"


def fetch_weather(latitude, longitude):
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "apparent_temperature,"
            "precipitation,"
            "rain,"
            "precipitation_probability,"
            "weather_code,"
            "wind_speed_10m,"
            "visibility"
        ),
        "daily": "sunrise,sunset",
        "timezone": "Asia/Kolkata"
    }

    response = requests.get(WEATHER_API_URL, params=params)

    response.raise_for_status()

    return response.json()

AIR_QUALITY_API_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"


def fetch_air_quality(latitude, longitude):
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": (
            "european_aqi,"
            "us_aqi,"
            "uv_index,"
            "pm2_5,"
            "pm10"
        ),
        "timezone": "Asia/Kolkata"
    }

    response = requests.get(AIR_QUALITY_API_URL, params=params)

    response.raise_for_status()

    return response.json()

if __name__ == "__main__":
    ghaziabad = LOCATIONS["Ghaziabad"]

    latitude = ghaziabad["latitude"]
    longitude = ghaziabad["longitude"]

    weather = fetch_weather(latitude, longitude)
    air_quality = fetch_air_quality(latitude, longitude)

    print("WEATHER DATA:")
    print(weather)

    print("\nAIR QUALITY DATA:")
    print(air_quality)