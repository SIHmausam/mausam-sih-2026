import requests

url = "https://air-quality-api.open-meteo.com/v1/air-quality"

params = {
    "latitude": 28.6692,
    "longitude": 77.4538,
    "current": "european_aqi,us_aqi,uv_index,pm2_5,pm10",
    "timezone": "Asia/Kolkata"
}

response = requests.get(url, params=params)

print("Status code:", response.status_code)
print("Response:")
print(response.json())