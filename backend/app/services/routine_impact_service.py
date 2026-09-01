from app.core.enums import (
    ActivityContext,
    RoutineImpactLevel,
)
from app.schemas.alert import OfficialAlert
from app.schemas.routine import (
    RoutineWeatherSnapshot,
)


class RoutineImpactResult:
    def __init__(
        self,
        level: RoutineImpactLevel,
        reasons: list[str],
        recommendation: str,
    ):
        self.level = level
        self.reasons = reasons
        self.recommendation = recommendation


class RoutineImpactService:
    @staticmethod
    def _has_severe_alert(
        alerts: list[OfficialAlert],
    ) -> bool:
        return any(
            (alert.severity or "").casefold()
            in {
                "severe",
                "extreme",
            }
            for alert in alerts
        )

    @staticmethod
    def _has_moderate_alert(
        alerts: list[OfficialAlert],
    ) -> bool:
        return any((alert.severity or "").casefold() == "moderate" for alert in alerts)

    def evaluate(
        self,
        activity_context: ActivityContext,
        weather: RoutineWeatherSnapshot,
        alerts: list[OfficialAlert],
    ) -> RoutineImpactResult:
        # Highest priority:
        # official safety warnings must override
        # personalization or routine preferences.
        if self._has_severe_alert(alerts):
            return RoutineImpactResult(
                level=RoutineImpactLevel.AVOID,
                reasons=[("A severe official alert is active for this location.")],
                recommendation=(
                    "Avoid this activity until the official warning has cleared."
                ),
            )

        reasons: list[str] = []

        caution = False
        avoid = False

        if self._has_moderate_alert(alerts):
            caution = True

            reasons.append("A moderate official alert is active for this location.")

        if activity_context == ActivityContext.OUTDOOR_HEALTH:
            if weather.aqi is not None and weather.aqi >= 200:
                avoid = True
                reasons.append("Air quality is very poor.")

            elif weather.aqi is not None and weather.aqi >= 100:
                caution = True
                reasons.append(
                    "Air quality may be unsuitable for prolonged outdoor activity."
                )

            if weather.uv_index is not None and weather.uv_index >= 11:
                avoid = True
                reasons.append("UV exposure is extremely high.")

            elif weather.uv_index is not None and weather.uv_index >= 8:
                caution = True
                reasons.append("UV exposure is very high.")

            if (
                weather.apparent_temperature is not None
                and weather.apparent_temperature >= 42
            ):
                avoid = True
                reasons.append("Heat stress risk is high.")

            elif (
                weather.apparent_temperature is not None
                and weather.apparent_temperature >= 36
            ):
                caution = True
                reasons.append("Conditions may cause heat stress.")

        if activity_context in {
            ActivityContext.COMMUTE,
            ActivityContext.TRAVEL,
            ActivityContext.OUTDOOR_HEALTH,
        }:
            if weather.rain_probability is not None and weather.rain_probability >= 80:
                caution = True
                reasons.append("Heavy rain is likely around the activity time.")

            if weather.visibility is not None and weather.visibility < 1000:
                avoid = True
                reasons.append("Visibility is dangerously low.")

            elif weather.visibility is not None and weather.visibility < 3000:
                caution = True
                reasons.append("Visibility is reduced.")

            if weather.wind_speed is not None and weather.wind_speed >= 60:
                avoid = True
                reasons.append("Wind conditions may be dangerous.")

            elif weather.wind_speed is not None and weather.wind_speed >= 40:
                caution = True
                reasons.append("Strong winds are expected.")

        if activity_context == ActivityContext.IRRIGATION:
            if weather.rain_probability is not None and weather.rain_probability >= 70:
                avoid = True
                reasons.append("Rain is likely, so irrigation may be unnecessary.")

            elif (
                weather.rain_probability is not None and weather.rain_probability >= 50
            ):
                caution = True
                reasons.append("Rain is possible; consider delaying irrigation.")

            if (
                weather.surface_soil_moisture is not None
                and weather.surface_soil_moisture >= 0.4
            ):
                caution = True
                reasons.append("Surface soil moisture is already high.")

        if activity_context == ActivityContext.FARMING:
            if weather.rain_probability is not None and weather.rain_probability >= 80:
                caution = True
                reasons.append("High rain probability may affect field work.")

            if weather.wind_speed is not None and weather.wind_speed >= 40:
                caution = True
                reasons.append("Strong winds may affect field work.")

        if avoid:
            return RoutineImpactResult(
                level=RoutineImpactLevel.AVOID,
                reasons=reasons,
                recommendation=("Consider postponing or rescheduling this activity."),
            )

        if caution:
            return RoutineImpactResult(
                level=RoutineImpactLevel.CAUTION,
                reasons=reasons,
                recommendation=(
                    "Proceed carefully and review conditions before starting."
                ),
            )

        return RoutineImpactResult(
            level=RoutineImpactLevel.SAFE,
            reasons=[("No significant weather or official alert risk was detected.")],
            recommendation=("Conditions currently look suitable for this activity."),
        )
