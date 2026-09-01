import requests

url = "https://api.open-meteo.com/v1/forecast"

params = {
    "latitude": 28.6692,
    "longitude": 77.4538,
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

response = requests.get(url, params=params)

print("Status code:", response.status_code)
print("Response:")
print(response.json())