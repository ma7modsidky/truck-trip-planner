from collections import defaultdict
from datetime import date, datetime, time, timedelta

from trip_planner.domain.models import ScheduleEvent


def _midnight_after(d: date) -> datetime:
    """The datetime of midnight starting the day AFTER `d`."""
    return datetime.combine(d + timedelta(days=1), time.min)


def split_events_by_day(
    events: list[ScheduleEvent],
) -> dict[date, list[ScheduleEvent]]:
    """
    Group ScheduleEvents by calendar day.

    Any event that spans midnight is split at each midnight into
    multiple events, one per day it touches. The first piece ends
    at 23:59:59.999999 on day N; the next piece starts at
    00:00:00.000000 on day N+1.
    """
    by_day: dict[date, list[ScheduleEvent]] = defaultdict(list)

    for event in events:
        _split_event_into_days(event, by_day)

    # Return a plain dict with sorted days and sorted events.
    return {
        day: sorted(by_day[day], key=lambda e: e.start)
        for day in sorted(by_day.keys())
    }


def _split_event_into_days(
    event: ScheduleEvent,
    by_day: dict[date, list[ScheduleEvent]],
) -> None:
    cursor = event.start

    while cursor < event.end:
        day = cursor.date()
        next_midnight = _midnight_after(day)

        piece_end = min(event.end, next_midnight)

        # Avoid creating a zero-length piece at exactly midnight.
        if piece_end > cursor:
            by_day[day].append(
                ScheduleEvent(
                    start=cursor,
                    end=piece_end,
                    status=event.status,
                    activity=event.activity,
                    location=event.location,
                    distance_miles=event.distance_miles,
                )
            )

        cursor = piece_end