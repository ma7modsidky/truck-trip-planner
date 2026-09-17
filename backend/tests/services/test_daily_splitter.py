from datetime import date, datetime, timedelta

from trip_planner.domain.enums import Activity, DutyStatus
from trip_planner.domain.models import ScheduleEvent
from trip_planner.services.daily_splitter import split_events_by_day


def test_event_within_one_day_stays_on_one_day():
    events = [
        ScheduleEvent(
            start=datetime(2026, 9, 18, 8, 0),
            end=datetime(2026, 9, 18, 12, 0),
            status=DutyStatus.DRIVING,
            activity=Activity.DRIVING,
            distance_miles=220,
        ),
    ]

    result = split_events_by_day(events)

    assert list(result.keys()) == [date(2026, 9, 18)]
    assert len(result[date(2026, 9, 18)]) == 1
    assert result[date(2026, 9, 18)][0].distance_miles == 220


def test_event_crossing_midnight_is_split():
    events = [
        ScheduleEvent(
            start=datetime(2026, 9, 18, 22, 0),
            end=datetime(2026, 9, 19, 8, 0),
            status=DutyStatus.SLEEPER,
            activity=Activity.REST,
        ),
    ]

    result = split_events_by_day(events)

    assert list(result.keys()) == [date(2026, 9, 18), date(2026, 9, 19)]

    day18 = result[date(2026, 9, 18)]
    day19 = result[date(2026, 9, 19)]

    assert len(day18) == 1
    assert len(day19) == 1

    assert day18[0].start == datetime(2026, 9, 18, 22, 0)
    assert day18[0].end == datetime(2026, 9, 19, 0, 0)

    assert day19[0].start == datetime(2026, 9, 19, 0, 0)
    assert day19[0].end == datetime(2026, 9, 19, 8, 0)

    # Same status/activity carried across the split.
    assert day18[0].status == DutyStatus.SLEEPER
    assert day19[0].status == DutyStatus.SLEEPER
    assert day18[0].activity == Activity.REST
    assert day19[0].activity == Activity.REST


def test_event_spanning_three_days_is_split_into_three():
    events = [
        ScheduleEvent(
            start=datetime(2026, 9, 18, 20, 0),
            end=datetime(2026, 9, 21, 4, 0),
            status=DutyStatus.SLEEPER,
            activity=Activity.REST,
        ),
    ]

    result = split_events_by_day(events)

    assert list(result.keys()) == [
        date(2026, 9, 18),
        date(2026, 9, 19),
        date(2026, 9, 20),
        date(2026, 9, 21),
    ]

    assert len(result[date(2026, 9, 19)]) == 1
    assert result[date(2026, 9, 19)][0].duration == timedelta(days=1)
    assert len(result[date(2026, 9, 20)]) == 1
    assert result[date(2026, 9, 20)][0].duration == timedelta(days=1)


def test_multiple_events_are_grouped_by_day():
    events = [
        ScheduleEvent(
            start=datetime(2026, 9, 18, 8, 0),
            end=datetime(2026, 9, 18, 12, 0),
            status=DutyStatus.DRIVING,
            activity=Activity.DRIVING,
            distance_miles=220,
        ),
        ScheduleEvent(
            start=datetime(2026, 9, 18, 12, 0),
            end=datetime(2026, 9, 18, 13, 0),
            status=DutyStatus.ON_DUTY,
            activity=Activity.PICKUP,
        ),
        ScheduleEvent(
            start=datetime(2026, 9, 19, 2, 0),
            end=datetime(2026, 9, 19, 5, 0),
            status=DutyStatus.DRIVING,
            activity=Activity.DRIVING,
            distance_miles=165,
        ),
    ]

    result = split_events_by_day(events)

    assert set(result.keys()) == {date(2026, 9, 18), date(2026, 9, 19)}
    assert len(result[date(2026, 9, 18)]) == 2
    assert len(result[date(2026, 9, 19)]) == 1


def test_event_starting_exactly_at_midnight_belongs_to_new_day():
    events = [
        ScheduleEvent(
            start=datetime(2026, 9, 19, 0, 0),
            end=datetime(2026, 9, 19, 6, 0),
            status=DutyStatus.DRIVING,
            activity=Activity.DRIVING,
            distance_miles=330,
        ),
    ]

    result = split_events_by_day(events)

    assert list(result.keys()) == [date(2026, 9, 19)]
    assert len(result[date(2026, 9, 19)]) == 1


def test_event_ending_exactly_at_midnight_does_not_create_next_day_piece():
    events = [
        ScheduleEvent(
            start=datetime(2026, 9, 18, 22, 0),
            end=datetime(2026, 9, 19, 0, 0),
            status=DutyStatus.SLEEPER,
            activity=Activity.REST,
        ),
    ]

    result = split_events_by_day(events)

    assert list(result.keys()) == [date(2026, 9, 18)]
    assert len(result[date(2026, 9, 18)]) == 1
    assert result[date(2026, 9, 18)][0].end == datetime(2026, 9, 19, 0, 0)