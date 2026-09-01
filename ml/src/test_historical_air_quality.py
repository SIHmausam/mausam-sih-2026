import requests

url = "https://air-quality-api.open-meteo.com/v1/air-quality"

params = {
    "latitude": 28.6692,
    "longitude": 77.4538,
    "start_date": "2026-08-25",
    "end_date": "2026-08-30",
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

response = requests.get(url, params=params)

print("Status code:", response.status_code)

response.raise_for_status()

data = response.json()

print("Timezone:", data["timezone"])
print("Number of hourly records:", len(data["hourly"]["time"]))
print("First 5 timestamps:", data["hourly"]["time"][:5])
print("First 5 PM2.5 values:", data["hourly"]["pm2_5"][:5])
print("First 5 PM10 values:", data["hourly"]["pm10"][:5])
print("First 5 NO2 values:", data["hourly"]["nitrogen_dioxide"][:5])