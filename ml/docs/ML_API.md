# Mausam Personalization ML API

## Base URL

http://127.0.0.1:8000

For deployment, replace this with the deployed ML service URL.

---

# 1. Health Check

## GET /

Checks whether the ML service is running.

### Response

{
  "service": "Mausam Personalization ML API",
  "status": "running"
}

---

# 2. Personalization

## POST /personalize

Returns personalized homepage cards based on:

- User persona
- Current weather/environment
- Stored user interaction history

### Request

{
  "user_id": "user_002",
  "persona": "fitness",
  "weather": {
    "city": "Srinagar",
    "timestamp": "2026-09-01T10:16:03",
    "temperature_2m": 20.0,
    "relative_humidity_2m": 70,
    "apparent_temperature": 20.5,
    "precipitation": 0.0,
    "rain": 0.0,
    "weather_code": 0,
    "wind_speed_10m": 5.0,
    "soil_moisture_0_to_7cm": 0.30,
    "us_aqi": 80,
    "european_aqi": 50,
    "uv_index": 1.0,
    "pm2_5": 20.0,
    "pm10": 35.0,
    "nitrogen_dioxide": 10.0,
    "sulphur_dioxide": 5.0,
    "carbon_monoxide": 300.0,
    "ozone": 70.0,
    "sunrise": "2026-09-01T05:58",
    "sunset": "2026-09-01T18:55",
    "is_daylight": true
  }
}

### Supported personas

fitness
farmer
traveler

### Response

{
  "city": "Srinagar",
  "persona": "fitness",
  "cards": [
    {
      "rank": 1,
      "card": "humidity",
      "score": 0.6367,
      "insight": "Humidity is slightly elevated."
    },
    {
      "rank": 2,
      "card": "aqi",
      "score": 0.5939,
      "insight": "Air quality is acceptable for most people."
    }
  ]
}

The response contains all 8 cards.

Cards are ordered by rank.

---

# 3. Record User Interaction

## POST /interaction

Records a user's interaction with a homepage card.

### Request

{
  "user_id": "user_002",
  "card_id": "uv",
  "action": "expand",
  "timestamp": "2026-09-01T10:20:00",
  "position": 3,
  "session_id": "session_002"
}

### Supported cards

aqi
uv
temperature
humidity
rain
wind
soil_moisture
weather_condition

### Example actions

expand
click
dismiss

### Response

{
  "status": "success",
  "message": "Interaction recorded",
  "interaction": {
    "user_id": "user_002",
    "card_id": "uv",
    "action": "expand",
    "timestamp": "2026-09-01T10:20:00",
    "position": 3,
    "session_id": "session_002"
  }
}

---

# 4. Personalization Flow

Mausam Backend
      |
      | POST /personalize
      ↓
ML API
      |
      ├── Current weather
      ├── User persona
      └── Stored interaction history
      |
      ↓
Cold-start model
      +
Behavioral preference
      |
      ↓
Hybrid ranking
      |
      ↓
Prioritized cards + insights
      |
      ↓
Mausam Backend

---

# 5. Learning Flow

When a user interacts with a card:

User expands card
       ↓
POST /interaction
       ↓
Interaction Store
       ↓
Behavioral Preference
       ↓
Hybrid Personalization
       ↓
Future /personalize request
       ↓
Updated card ranking

The system gradually shifts from cold-start personalization toward behavior-based personalization as interaction history increases.

---

# 6. Cold Start

For a new user:

Interactions = 0

the system automatically uses the cold-start/persona model.

No previous interaction history is required.

---

# 7. Error Responses

### Missing required request fields

Returns:

422 Unprocessable Entity

### Invalid persona

Only these values are accepted:

fitness
farmer
traveler

Invalid values return:

422 Unprocessable Entity

### Incomplete weather data

Returns:

422 Unprocessable Entity

with the missing weather fields listed.

---

# 8. Current ML Cards

The system currently ranks:

1. AQI
2. UV
3. Temperature
4. Humidity
5. Rain
6. Wind
7. Soil Moisture
8. Weather Condition

The ranking is dynamic and depends on:

- User persona
- Current environmental conditions
- Behavioral history

---

# 9. Integration Notes

The Mausam backend should:

1. Obtain current weather data.
2. Obtain the user's persona.
3. Send POST /personalize.
4. Use the returned cards array to construct the personalized homepage.
5. Send user interactions to POST /interaction.
6. Request personalization again when appropriate to obtain updated priorities.

The ML service should be treated as a personalization/ranking service.

It does not replace the weather data provider.