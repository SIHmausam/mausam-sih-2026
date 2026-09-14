# ============================================================
# Phase 2 deterministic contextual insights
# ============================================================

def get_card_insight(card, weather):
    """
    Generate a short deterministic contextual insight
    for a Phase 2 Mausam homepage card.

    LLM-generated insights can replace this implementation
    later without changing the caller interface.
    """

    # --------------------------------------------------------
    # Temperature
    # --------------------------------------------------------

    if card == "temperature":

        temp = float(weather["temperature_2m"])

        if temp < 10:
            return "It is quite cold right now; warmer clothing may be useful."
        elif temp < 20:
            return "Temperatures are cool and comfortable for most outdoor activities."
        elif temp < 30:
            return "Temperatures are comfortable for most outdoor activities."
        elif temp < 35:
            return "It is warm outside; stay hydrated during outdoor activity."
        else:
            return "It is very hot; avoid prolonged outdoor exposure."


    # --------------------------------------------------------
    # Weather Conditions
    # --------------------------------------------------------

    if card == "weather_conditions":

        code = int(weather["weather_code"])

        if code == 0:
            return "Clear skies are currently expected."
        elif code in [1, 2]:
            return "Partly cloudy conditions with some sunshine are present."
        elif code == 3:
            return "Cloudy conditions are currently present."
        elif code in [45, 48]:
            return "Foggy conditions may reduce visibility."
        elif code in [51, 53, 55]:
            return "Drizzle is currently occurring."
        elif code in [61, 63, 65]:
            return "Rain is currently occurring."
        elif code in [80, 81, 82]:
            return "Rain showers are currently possible."
        elif code in [95, 96, 99]:
            return "Thunderstorm conditions are currently present."
        else:
            return "Changing weather conditions are currently present."


    # --------------------------------------------------------
    # Humidity
    # --------------------------------------------------------

    if card == "humidity":

        humidity = float(weather["relative_humidity_2m"])

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
    # Rain Forecast
    # --------------------------------------------------------

    if card == "rain_forecast":

        probability = float(
            weather["precipitation_probability"]
        )

        rain = float(weather["rain"])

        if probability < 20 and rain == 0:
            return "Rain probability is low with no rain currently recorded."
        elif probability < 50:
            return "There is a moderate chance of rain; keep an eye on the forecast."
        elif probability < 80:
            return "Rain is increasingly likely; consider carrying an umbrella."
        else:
            return "Rain probability is high; plan outdoor activities accordingly."


    # --------------------------------------------------------
    # Wind
    # --------------------------------------------------------

    if card == "wind":

        wind = float(weather["wind_speed_10m"])

        if wind < 5:
            return "Winds are light right now."
        elif wind < 15:
            return "Moderate winds are currently blowing."
        elif wind < 25:
            return "Strong winds are currently blowing."
        else:
            return "Very strong winds are currently blowing."


    # --------------------------------------------------------
    # Air Quality
    # --------------------------------------------------------

    if card == "air_quality":

        aqi = float(weather["us_aqi"])

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
    # UV & Allergy
    # --------------------------------------------------------

    if card == "uv_allergy":

        uv = float(weather["uv_index"])
        aqi = float(weather["us_aqi"])
        humidity = float(weather["relative_humidity_2m"])

        if uv >= 8:
            return "UV exposure is very high; use strong sun protection outdoors."
        elif uv >= 6:
            return "UV levels are high; sun protection is recommended outdoors."
        elif aqi > 100:
            return "Air quality may affect sensitive users; consider limiting prolonged outdoor exposure."
        elif humidity >= 80:
            return "High humidity may increase discomfort for people sensitive to environmental conditions."
        elif uv >= 3:
            return "Moderate UV levels call for basic sun protection outdoors."
        else:
            return "UV exposure is currently low."


    # --------------------------------------------------------
    # Running Conditions
    # --------------------------------------------------------

    if card == "running_conditions":

        temp = float(weather["temperature_2m"])
        wind = float(weather["wind_speed_10m"])
        uv = float(weather["uv_index"])
        rain_probability = float(
            weather["precipitation_probability"]
        )

        if temp >= 35:
            return "High temperatures make running less comfortable; consider a cooler time."
        elif rain_probability >= 70:
            return "High rain probability may disrupt outdoor running plans."
        elif wind >= 25:
            return "Strong winds may make running more difficult."
        elif uv >= 8:
            return "Very high UV makes early morning or evening running preferable."
        elif 10 <= temp <= 25 and wind < 15:
            return "Cool temperatures and light winds make conditions favorable for running."
        else:
            return "Running conditions are moderate; choose a comfortable time based on the weather."


    # --------------------------------------------------------
    # Surf Conditions
    # --------------------------------------------------------

    if card == "surf_conditions":

        wave_height = weather.get("wave_height")

        if wave_height is None or str(wave_height) == "nan":
            return "Marine conditions are unavailable for this location."

        wave_height = float(wave_height)
        wave_period = weather.get("wave_period")

        if wave_period is not None and str(wave_period) != "nan":
            wave_period = float(wave_period)

        if wave_height >= 2.5:
            return "Large waves are present; surf conditions may be challenging."
        elif wave_height >= 1.5:
            return "Moderate waves are present with potentially active surf conditions."
        elif wave_height >= 0.8:
            return "Small to moderate waves are present for surfing."
        else:
            return "Wave heights are low, suggesting relatively calm surf conditions."


    # --------------------------------------------------------
    # Tide & Water
    # --------------------------------------------------------

    if card == "tide_water":

        water_temp = weather.get("sea_surface_temperature")

        if water_temp is None or str(water_temp) == "nan":
            return "Marine water information is unavailable for this location."

        water_temp = float(water_temp)

        if water_temp < 18:
            return "Sea water is relatively cool; consider appropriate thermal protection."
        elif water_temp < 26:
            return "Sea water temperature is moderate for water activities."
        else:
            return "Sea water is warm and suitable for many water activities."


    # --------------------------------------------------------
    # Farm & Garden
    # --------------------------------------------------------

    if card == "farm_garden":

        moisture = float(
            weather["soil_moisture_0_to_7cm"]
        )
        rain_probability = float(
            weather["precipitation_probability"]
        )

        if moisture < 0.15:
            return "Topsoil moisture is low; crops may need irrigation if rain is unlikely."
        elif moisture < 0.25:
            return "Topsoil moisture is somewhat low; monitor rainfall and irrigation needs."
        elif moisture < 0.45 and rain_probability >= 50:
            return "Soil moisture is moderate with rain possible, supporting current crop water needs."
        elif moisture < 0.45:
            return "Soil moisture is moderate; continue monitoring rainfall and irrigation needs."
        else:
            return "Topsoil moisture is high; monitor fields for excess water."


    # --------------------------------------------------------
    # Commute Conditions
    # --------------------------------------------------------

    if card == "commute_conditions":

        visibility = float(weather["visibility"])
        rain_probability = float(
            weather["precipitation_probability"]
        )
        wind = float(weather["wind_speed_10m"])
        weather_code = int(weather["weather_code"])

        if weather_code in [45, 48]:
            return "Fog may reduce visibility; allow extra time for your commute."
        elif visibility < 2000:
            return "Low visibility may make travel slower; use extra caution."
        elif rain_probability >= 70:
            return "High rain probability may slow your commute."
        elif wind >= 25:
            return "Strong winds may affect commuting conditions."
        else:
            return "Current visibility and weather conditions are generally favorable for commuting."


    # --------------------------------------------------------
    # Travel Conditions
    # --------------------------------------------------------

    if card == "travel_conditions":

        rain_probability = float(
            weather["precipitation_probability"]
        )
        wind = float(weather["wind_speed_10m"])
        visibility = float(weather["visibility"])

        if visibility < 2000:
            return "Reduced visibility may affect travel; allow extra time."
        elif rain_probability >= 70:
            return "High rain probability may affect travel plans."
        elif wind >= 25:
            return "Strong winds may affect outdoor travel activities."
        else:
            return "Current weather conditions are generally favorable for travel."


    # --------------------------------------------------------
    # Family & School
    # --------------------------------------------------------

    if card == "family_school":

        rain_probability = float(
            weather["precipitation_probability"]
        )
        weather_code = int(weather["weather_code"])

        if weather_code in [95, 96, 99]:
            return "Thunderstorm conditions may affect school commutes and outdoor activities."
        elif rain_probability >= 70:
            return "High rain probability may make school travel less convenient."
        elif weather_code in [45, 48]:
            return "Fog may reduce visibility during school travel."
        else:
            return "Current conditions are generally manageable for school travel."


    # --------------------------------------------------------
    # Event Conditions
    # --------------------------------------------------------

    if card == "event_conditions":

        rain_probability = float(
            weather["precipitation_probability"]
        )
        temp = float(weather["temperature_2m"])
        humidity = float(weather["relative_humidity_2m"])

        if rain_probability >= 70:
            return "High rain probability makes an indoor backup plan advisable."
        elif temp >= 35:
            return "High temperatures may reduce outdoor event comfort."
        elif humidity >= 80:
            return "High humidity may make outdoor events feel uncomfortable."
        else:
            return "Current conditions are generally favorable for outdoor events."


    # --------------------------------------------------------
    # Fallback
    # --------------------------------------------------------

    return "Current weather conditions are available."
