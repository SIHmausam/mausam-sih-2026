from datetime import datetime, timedelta

from app.schemas.routine import MyDayResponse, MyDayRoutineItem


class RoutineReminderService:
    def __init__(
        self,
        *,
        reminder_lead_minutes: int = 30,
    ):
        if reminder_lead_minutes <= 0:
            raise ValueError("reminder_lead_minutes must be greater than zero")

        self.reminder_lead_minutes = reminder_lead_minutes

    def get_approaching_routines(
        self,
        *,
        my_day: MyDayResponse,
        now: datetime,
    ) -> list[MyDayRoutineItem]:
        if now.tzinfo is None:
            raise ValueError("now must be timezone-aware")

        approaching: list[MyDayRoutineItem] = []

        for routine in my_day.routines:
            routine_start = datetime.combine(
                my_day.date,
                routine.start_time,
                tzinfo=now.tzinfo,
            )

            reminder_start = routine_start - timedelta(
                minutes=(self.reminder_lead_minutes)
            )

            if reminder_start <= now < routine_start:
                approaching.append(routine)

        return approaching
