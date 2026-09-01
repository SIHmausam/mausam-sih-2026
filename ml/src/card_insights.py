import math


# ============================================================
# Card-specific contextual insights
# ============================================================

def get_card_insight(card, weather):
    """
    Generate a short contextual sentence for a weather card.

    The insight is based on the current environmental value.
    """

    # --------------------------------------------------------
    # AQI
    # --------------------------------------------------------

    if card == "aqi":

        aqi = weather["us_aqi"]

        if aqi <= 50:
            return "Air quality is good for outdoor activities."
        elif aqi <= 100:
            return "Air quality is acceptable for most people."
        elif aqi <= 150:
            return "Air quality may affect sensitive individuals."
        elif aqi <= 200:
            return "Air quality is unhealthy; consider limiting prolonged outdoor activity."
        elif aqi <= 300:
            return "Air quality is very unhealthy; avoid prolonged outdoor activity."
        else:
            return "Air quality is hazardous; avoid outdoor exposure."


    # --------------------------------------------------------
    # UV
    # --------------------------------------------------------

    if card == "uv":

        uv = weather["uv_index"]

        if uv < 3:
            return "UV levels are low right now."
        elif uv < 6:
            return "UV levels are moderate; sun protection is recommended."
        elif uv < 8:
            return "UV levels are high; use sun protection outdoors."
        elif uv < 11:
            return "UV levels are very high; minimize direct sun exposure."
        else:
            return "UV levels are extreme; avoid prolonged direct sunlight."


    # --------------------------------------------------------
    # Temperature
    # --------------------------------------------------------

    if card == "temperature":

        temp = weather["temperature_2m"]

        if temp < 10:
            return "It is quite cold right now."
        elif temp < 20:
            return "Temperatures are cool and comfortable."
        elif temp < 30:
            return "Temperatures are comfortable for most outdoor activities."
        elif temp < 35:
            return "It is warm outside; stay hydrated during outdoor activity."
        else:
            return "It is very hot; avoid prolonged outdoor exposure."


    # --------------------------------------------------------
    # Humidity
    # --------------------------------------------------------

    if card == "humidity":

        humidity = weather["relative_humidity_2m"]

        if humidity < 30:
            return "Humidity is low; the air may feel dry."
        elif humidity < 60:
            return "Humidity levels are comfortable."
        elif humidity < 75:
            return "Humidity is slightly elevated."
        elif humidity < 90:
            return "Humidity is high and may make it feel warmer."
        else:
            return "Humidity is very high; conditions may feel uncomfortable."


    # --------------------------------------------------------
    # Rain
    # --------------------------------------------------------

    if card == "rain":

        rain = weather["rain"]

        if rain == 0:
            return "No rain is currently being recorded."
        elif rain < 2.5:
            return "Light rain is currently occurring."
        elif rain < 7.5:
            return "Moderate rain is currently occurring."
        else:
            return "Heavy rain is currently occurring."


    # --------------------------------------------------------
    # Wind
    # --------------------------------------------------------

    if card == "wind":

        wind = weather["wind_speed_10m"]

        if wind < 5:
            return "Winds are light right now."
        elif wind < 15:
            return "Moderate winds are currently blowing."
        elif wind < 25:
            return "Strong winds are currently blowing."
        else:
            return "Very strong winds are currently blowing."


    # --------------------------------------------------------
    # Soil moisture
    # --------------------------------------------------------

    if card == "soil_moisture":

        moisture = weather["soil_moisture_0_to_7cm"]

        if moisture < 0.15:
            return "Soil moisture is low; crops may need water."
        elif moisture < 0.25:
            return "Soil moisture is somewhat low."
        elif moisture < 0.35:
            return "Soil moisture is at a moderate level."
        elif moisture < 0.45:
            return "Soil moisture is good for maintaining healthy soil conditions."
        else:
            return "Soil moisture is high; monitor for excess water."


    # --------------------------------------------------------
    # Weather condition
    # --------------------------------------------------------

    if card == "weather_condition":

        code = int(weather["weather_code"])

        if code == 0:
            return "The sky is clear right now."

        elif code in [1, 2]:
            return "The weather is partly cloudy with some sunshine."

        elif code == 3:
            return "Cloudy conditions are currently present."

        elif code in [51, 53, 55]:
            return "Drizzle is currently occurring."

        elif code in [61, 63, 65]:
            return "Rain is currently occurring."

        else:
            return "Changing weather conditions are currently present."


    # --------------------------------------------------------
    # Fallback
    # --------------------------------------------------------

    return "Current weather conditions are available."


# ============================================================
# Test
# ============================================================

if __name__ == "__main__":

    import pandas as pd

    df = pd.read_csv(
        "data/processed/test.csv"
    )

    weather = df.iloc[0]

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

    print("\n================================")
    print("CARD INSIGHT TEST")
    print("================================")

    print(
        "City:",
        weather["city"]
    )

    print()

    for card in cards:

        insight = get_card_insight(
            card,
            weather
        )

        print(
            f"{card:20s} → {insight}"
        )