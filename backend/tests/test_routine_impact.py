from app.core.enums import (
    ActivityContext,
    RoutineImpactLevel,
)
from app.schemas.alert import OfficialAlert
from app.schemas.routine import RoutineWeatherSnapshot
from app.services.routine_impact_service import (
    RoutineImpactService,
)


def weather_snapshot(
    *,
    temperature: float | None = 28.0,
    apparent_temperature: float | None = 30.0,
    humidity: float | None = 60.0,
    rain: float | None = 0.0,
    rain_probability: float | None = 10.0,
    wind_speed: float | None = 10.0,
    visibility: float | None = 10000.0,
    aqi: float | None = 50.0,
    uv_index: float | None = 3.0,
    surface_soil_moisture: float | None = 0.2,
) -> RoutineWeatherSnapshot:
    return RoutineWeatherSnapshot(
        temperature=temperature,
        apparent_temperature=apparent_temperature,
        humidity=humidity,
        rain=rain,
        rain_probability=rain_probability,
        wind_speed=wind_speed,
        visibility=visibility,
        aqi=aqi,
        uv_index=uv_index,
        surface_soil_moisture=surface_soil_moisture,
    )


def official_alert(
    severity: str,
) -> OfficialAlert:
    return OfficialAlert(
        identifier="TEST-ALERT-001",
        event="Thunderstorm",
        headline=None,
        description=None,
        instruction=None,
        severity=severity,
        urgency=None,
        certainty=None,
        effective_at=None,
        onset_at=None,
        expires_at=None,
        area_description="Delhi",
        areas=[],
        sender_name=None,
    )


def test_safe_outdoor_activity():
    service = RoutineImpactService()

    result = service.evaluate(
        activity_context=ActivityContext.OUTDOOR_HEALTH,
        weather=weather_snapshot(),
        alerts=[],
    )

    assert result.level == RoutineImpactLevel.SAFE
    assert result.reasons
    assert result.recommendation


def test_severe_official_alert_overrides_weather():
    service = RoutineImpactService()

    result = service.evaluate(
        activity_context=ActivityContext.OUTDOOR_HEALTH,
        weather=weather_snapshot(),
        alerts=[
            official_alert("Severe"),
        ],
    )

    assert result.level == RoutineImpactLevel.AVOID

    assert any("official alert" in reason.lower() for reason in result.reasons)


def test_extreme_official_alert_returns_avoid():
    service = RoutineImpactService()

    result = service.evaluate(
        activity_context=ActivityContext.COMMUTE,
        weather=weather_snapshot(),
        alerts=[
            official_alert("Extreme"),
        ],
    )

    assert result.level == RoutineImpactLevel.AVOID


def test_moderate_official_alert_returns_caution():
    service = RoutineImpactService()

    result = service.evaluate(
        activity_context=ActivityContext.GENERAL,
        weather=weather_snapshot(),
        alerts=[
            official_alert("Moderate"),
        ],
    )

    assert result.level == RoutineImpactLevel.CAUTION


def test_very_poor_aqi_returns_avoid():
    service = RoutineImpactService()

    result = service.evaluate(
        activity_context=ActivityContext.OUTDOOR_HEALTH,
        weather=weather_snapshot(
            aqi=220.0,
        ),
        alerts=[],
    )

    assert result.level == RoutineImpactLevel.AVOID

    assert any("air quality" in reason.lower() for reason in result.reasons)


def test_unhealthy_aqi_returns_caution():
    service = RoutineImpactService()

    result = service.evaluate(
        activity_context=ActivityContext.OUTDOOR_HEALTH,
        weather=weather_snapshot(
            aqi=130.0,
        ),
        alerts=[],
    )

    assert result.level == RoutineImpactLevel.CAUTION


def test_extreme_uv_returns_avoid():
    service = RoutineImpactService()

    result = service.evaluate(
        activity_context=ActivityContext.OUTDOOR_HEALTH,
        weather=weather_snapshot(
            uv_index=12.0,
        ),
        alerts=[],
    )

    assert result.level == RoutineImpactLevel.AVOID

    assert any("uv" in reason.lower() for reason in result.reasons)


def test_high_apparent_temperature_returns_avoid():
    service = RoutineImpactService()

    result = service.evaluate(
        activity_context=ActivityContext.OUTDOOR_HEALTH,
        weather=weather_snapshot(
            apparent_temperature=44.0,
        ),
        alerts=[],
    )

    assert result.level == RoutineImpactLevel.AVOID


def test_low_visibility_returns_avoid_for_commute():
    service = RoutineImpactService()

    result = service.evaluate(
        activity_context=ActivityContext.COMMUTE,
        weather=weather_snapshot(
            visibility=700.0,
        ),
        alerts=[],
    )

    assert result.level == RoutineImpactLevel.AVOID

    assert any("visibility" in reason.lower() for reason in result.reasons)


def test_strong_wind_returns_caution():
    service = RoutineImpactService()

    result = service.evaluate(
        activity_context=ActivityContext.TRAVEL,
        weather=weather_snapshot(
            wind_speed=45.0,
        ),
        alerts=[],
    )

    assert result.level == RoutineImpactLevel.CAUTION


def test_dangerous_wind_returns_avoid():
    service = RoutineImpactService()

    result = service.evaluate(
        activity_context=ActivityContext.TRAVEL,
        weather=weather_snapshot(
            wind_speed=65.0,
        ),
        alerts=[],
    )

    assert result.level == RoutineImpactLevel.AVOID


def test_high_rain_probability_avoids_irrigation():
    service = RoutineImpactService()

    result = service.evaluate(
        activity_context=ActivityContext.IRRIGATION,
        weather=weather_snapshot(
            rain_probability=85.0,
        ),
        alerts=[],
    )

    assert result.level == RoutineImpactLevel.AVOID

    assert any("irrigation" in reason.lower() for reason in result.reasons)


def test_high_soil_moisture_returns_caution():
    service = RoutineImpactService()

    result = service.evaluate(
        activity_context=ActivityContext.IRRIGATION,
        weather=weather_snapshot(
            surface_soil_moisture=0.5,
        ),
        alerts=[],
    )

    assert result.level == RoutineImpactLevel.CAUTION


def test_high_rain_probability_affects_farming():
    service = RoutineImpactService()

    result = service.evaluate(
        activity_context=ActivityContext.FARMING,
        weather=weather_snapshot(
            rain_probability=90.0,
        ),
        alerts=[],
    )

    assert result.level == RoutineImpactLevel.CAUTION
