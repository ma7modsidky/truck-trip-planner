from datetime import datetime, timedelta, timezone

import pytest

from trip_planner.domain.enums import Activity, DutyStatus
from trip_planner.domain.models import (
    DriverState,
    Location,
    ScheduleEvent,
)
from trip_planner.domain.config import HOSConfig


def test_schedule_event_calculates_duration():
    event = ScheduleEvent(
        start=datetime(2026, 9, 18, 8, 0, tzinfo=timezone.utc),
        end=datetime(2026, 9, 18, 9, 30, tzinfo=timezone.utc),
        status=DutyStatus.ON_DUTY,
        activity=Activity.PICKUP,
    )

    assert event.duration == timedelta(hours=1, minutes=30)

def test_schedule_event_rejects_invalid_time_range():
    with pytest.raises(ValueError):
        ScheduleEvent(
            start=datetime(2026, 9, 18, 9, 0, tzinfo=timezone.utc),
            end=datetime(2026, 9, 18, 8, 0, tzinfo=timezone.utc),
            status=DutyStatus.ON_DUTY,
            activity=Activity.PICKUP,
        )

def test_driver_state_starts_with_zero_daily_counters():
    state = DriverState(
        current_time=datetime(2026, 9, 18, 8, 0, tzinfo=timezone.utc),
        shift_start=datetime(2026, 9, 18, 8, 0, tzinfo=timezone.utc),
        cycle_used=timedelta(hours=25),
    )

    assert state.driving_today == timedelta(0)
    assert state.duty_today == timedelta(0)
    assert state.driving_since_break == timedelta(0)
    assert state.distance_since_fuel == 0
    assert state.cycle_used == timedelta(hours=25)


def test_applying_driving_event_updates_driving_counters():
    state = DriverState(
        current_time=datetime(2026, 9, 18, 8, 0, tzinfo=timezone.utc),
        shift_start=datetime(2026, 9, 18, 8, 0, tzinfo=timezone.utc),
        cycle_used=timedelta(hours=25),
    )

    event = ScheduleEvent(
        start=datetime(2026, 9, 18, 8, 0, tzinfo=timezone.utc),
        end=datetime(2026, 9, 18, 12, 0, tzinfo=timezone.utc),
        status=DutyStatus.DRIVING,
        activity=Activity.DRIVING,
        distance_miles=250,
    )

    state.apply_event(event)

    assert state.current_time == datetime(2026, 9, 18, 12, 0, tzinfo=timezone.utc)
    assert state.driving_today == timedelta(hours=4)
    assert state.duty_today == timedelta(hours=4)
    assert state.cycle_used == timedelta(hours=29)
    assert state.driving_since_break == timedelta(hours=4)
    assert state.distance_since_fuel == 250


def test_applying_on_duty_event_does_not_increase_driving_time():
    state = DriverState(
        current_time=datetime(2026, 9, 18, 8, 0, tzinfo=timezone.utc),
        shift_start=datetime(2026, 9, 18, 8, 0, tzinfo=timezone.utc),
        cycle_used=timedelta(hours=25),
    )

    event = ScheduleEvent(
        start=datetime(2026, 9, 18, 8, 0, tzinfo=timezone.utc),
        end=datetime(2026, 9, 18, 9, 0, tzinfo=timezone.utc),
        status=DutyStatus.ON_DUTY,
        activity=Activity.PICKUP,
    )

    state.apply_event(event)

    assert state.current_time == datetime(2026, 9, 18, 9, 0, tzinfo=timezone.utc)
    assert state.driving_today == timedelta(0)
    assert state.duty_today == timedelta(hours=1)
    assert state.cycle_used == timedelta(hours=26)
    assert state.driving_since_break == timedelta(0)

def test_applying_break_resets_driving_since_break():
    state = DriverState(
        current_time=datetime(2026, 9, 18, 13, 0, tzinfo=timezone.utc),
        shift_start=datetime(2026, 9, 18, 8, 0, tzinfo=timezone.utc),
        driving_today=timedelta(hours=8),
        duty_today=timedelta(hours=8),
        cycle_used=timedelta(hours=33),
        driving_since_break=timedelta(hours=8),
    )

    event = ScheduleEvent(
        start=datetime(2026, 9, 18, 13, 0, tzinfo=timezone.utc),
        end=datetime(2026, 9, 18, 13, 30, tzinfo=timezone.utc),
        status=DutyStatus.OFF_DUTY,
        activity=Activity.BREAK,
    )

    state.apply_event(event)

    assert state.current_time == datetime(2026, 9, 18, 13, 30, tzinfo=timezone.utc)

    assert state.driving_today == timedelta(hours=8)
    assert state.duty_today == timedelta(hours=8)
    assert state.cycle_used == timedelta(hours=33)

    assert state.driving_since_break == timedelta(0)

def test_event_must_start_at_current_driver_time():
    state = DriverState(
        current_time=datetime(2026, 9, 18, 8, 0, tzinfo=timezone.utc),
        shift_start=datetime(2026, 9, 18, 8, 0, tzinfo=timezone.utc),
    )

    event = ScheduleEvent(
        start=datetime(2026, 9, 18, 9, 0, tzinfo=timezone.utc),
        end=datetime(2026, 9, 18, 10, 0, tzinfo=timezone.utc),
        status=DutyStatus.DRIVING,
        activity=Activity.DRIVING,
    )

    with pytest.raises(ValueError):
        state.apply_event(event)

def test_remaining_driving_time():
    state = DriverState(
        current_time=datetime(2026, 9, 18, 8, 0, tzinfo=timezone.utc),
        shift_start=datetime(2026, 9, 18, 8, 0, tzinfo=timezone.utc),
        driving_today=timedelta(hours=4),
    )

    config = HOSConfig()

    assert state.remaining_driving_time(config) == timedelta(hours=7)

def test_remaining_driving_time_cannot_be_negative():
    state = DriverState(
        current_time=datetime(2026, 9, 18, 8, 0, tzinfo=timezone.utc),
        shift_start=datetime(2026, 9, 18, 8, 0, tzinfo=timezone.utc),
        driving_today=timedelta(hours=12),
    )

    config = HOSConfig()

    assert state.remaining_driving_time(config) == timedelta(0)

def test_remaining_duty_window_is_based_on_shift_start():
    state = DriverState(
        current_time=datetime(2026, 9, 18, 17, 0, tzinfo=timezone.utc),
        shift_start=datetime(2026, 9, 18, 8, 0, tzinfo=timezone.utc),
        duty_today=timedelta(hours=6),
    )

    config = HOSConfig()

    assert state.remaining_duty_window(config) == timedelta(hours=5)

def test_remaining_duty_window_cannot_be_negative():
    state = DriverState(
        current_time=datetime(2026, 9, 18, 23, 0, tzinfo=timezone.utc),
        shift_start=datetime(2026, 9, 18, 8, 0, tzinfo=timezone.utc),
    )

    config = HOSConfig()

    assert state.remaining_duty_window(config) == timedelta(0)

def test_remaining_cycle_time():
    state = DriverState(
        current_time=datetime(2026, 9, 18, 8, 0, tzinfo=timezone.utc),
        shift_start=datetime(2026, 9, 18, 8, 0, tzinfo=timezone.utc),
        cycle_used=timedelta(hours=25),
    )

    config = HOSConfig()

    assert state.remaining_cycle_time(config) == timedelta(hours=45)

def test_remaining_cycle_time_cannot_be_negative():
    state = DriverState(
        current_time=datetime(2026, 9, 18, 8, 0, tzinfo=timezone.utc),
        shift_start=datetime(2026, 9, 18, 8, 0, tzinfo=timezone.utc),
        cycle_used=timedelta(hours=72),
    )

    config = HOSConfig()

    assert state.remaining_cycle_time(config) == timedelta(0)

def test_break_not_required_before_threshold():
    state = DriverState(
        current_time=datetime(2026, 9, 18, 12, 0, tzinfo=timezone.utc),
        shift_start=datetime(2026, 9, 18, 8, 0, tzinfo=timezone.utc),
        driving_since_break=timedelta(hours=7),
    )

    config = HOSConfig()

    assert state.break_required(config) is False

def test_break_required_at_threshold():
    state = DriverState(
        current_time=datetime(2026, 9, 18, 16, 0, tzinfo=timezone.utc),
        shift_start=datetime(2026, 9, 18, 8, 0, tzinfo=timezone.utc),
        driving_since_break=timedelta(hours=8),
    )

    config = HOSConfig()

    assert state.break_required(config) is True

def test_short_off_duty_period_does_not_reset_break_counter():
    state = DriverState(
        current_time=datetime(2026, 9, 18, 13, 0, tzinfo=timezone.utc),
        shift_start=datetime(2026, 9, 18, 8, 0, tzinfo=timezone.utc),
        driving_since_break=timedelta(hours=7),
    )

    event = ScheduleEvent(
        start=datetime(2026, 9, 18, 13, 0, tzinfo=timezone.utc),
        end=datetime(2026, 9, 18, 13, 15, tzinfo=timezone.utc),
        status=DutyStatus.OFF_DUTY,
        activity=Activity.BREAK,
    )

    state.apply_event(event)

    assert state.driving_since_break == timedelta(hours=7)

def test_thirty_minute_break_resets_break_counter():
    state = DriverState(
        current_time=datetime(2026, 9, 18, 13, 0, tzinfo=timezone.utc),
        shift_start=datetime(2026, 9, 18, 8, 0, tzinfo=timezone.utc),
        driving_since_break=timedelta(hours=8),
    )

    event = ScheduleEvent(
        start=datetime(2026, 9, 18, 13, 0, tzinfo=timezone.utc),
        end=datetime(2026, 9, 18, 13, 30, tzinfo=timezone.utc),
        status=DutyStatus.OFF_DUTY,
        activity=Activity.BREAK,
    )

    state.apply_event(event)

    assert state.driving_since_break == timedelta(0)

def test_remaining_distance_before_fuel():
    state = DriverState(
        current_time=datetime(2026, 9, 18, 8, 0, tzinfo=timezone.utc),
        shift_start=datetime(2026, 9, 18, 8, 0, tzinfo=timezone.utc),
        distance_since_fuel=300,
    )

    config = HOSConfig()

    assert state.remaining_distance_before_fuel(config) == 700

def test_remaining_distance_before_fuel_cannot_be_negative():
    state = DriverState(
        current_time=datetime(2026, 9, 18, 8, 0, tzinfo=timezone.utc),
        shift_start=datetime(2026, 9, 18, 8, 0, tzinfo=timezone.utc),
        distance_since_fuel=1200,
    )

    config = HOSConfig()

    assert state.remaining_distance_before_fuel(config) == 0

def test_schedule_event_rejects_negative_distance():
    with pytest.raises(ValueError):
        ScheduleEvent(
            start=datetime(2026, 9, 18, 8, 0, tzinfo=timezone.utc),
            end=datetime(2026, 9, 18, 9, 0, tzinfo=timezone.utc),
            status=DutyStatus.DRIVING,
            activity=Activity.DRIVING,
            distance_miles=-10,
        )

def test_ten_hour_rest_resets_daily_state():
    state = DriverState(
        current_time=datetime(2026, 9, 18, 22, 0, tzinfo=timezone.utc),
        shift_start=datetime(2026, 9, 18, 8, 0, tzinfo=timezone.utc),
        driving_today=timedelta(hours=8),
        duty_today=timedelta(hours=10),
        cycle_used=timedelta(hours=35),
        driving_since_break=timedelta(hours=8),
        distance_since_fuel=500,
    )

    event = ScheduleEvent(
        start=datetime(2026, 9, 18, 22, 0, tzinfo=timezone.utc),
        end=datetime(2026, 9, 19, 8, 0, tzinfo=timezone.utc),
        status=DutyStatus.SLEEPER,
        activity=Activity.REST,
    )

    state.apply_event(event)

    assert state.current_time == datetime(2026, 9, 19, 8, 0, tzinfo=timezone.utc)

    assert state.shift_start == datetime(2026, 9, 19, 8, 0, tzinfo=timezone.utc)

    assert state.driving_today == timedelta(0)
    assert state.duty_today == timedelta(0)
    assert state.driving_since_break == timedelta(0)

    # These should NOT reset.
    assert state.cycle_used == timedelta(hours=35)
    assert state.distance_since_fuel == 500

def test_rest_less_than_ten_hours_does_not_reset_daily_state():
    state = DriverState(
        current_time=datetime(2026, 9, 18, 22, 0, tzinfo=timezone.utc),
        shift_start=datetime(2026, 9, 18, 8, 0, tzinfo=timezone.utc ),
        driving_today=timedelta(hours=8),
        duty_today=timedelta(hours=10),
        cycle_used=timedelta(hours=35),
        driving_since_break=timedelta(hours=8),
        distance_since_fuel=500,
    )

    event = ScheduleEvent(
        start=datetime(2026, 9, 18, 22, 0, tzinfo=timezone.utc),
        end=datetime(2026, 9, 19, 7, 0, tzinfo=timezone.utc),
        status=DutyStatus.SLEEPER,
        activity=Activity.REST,
    )

    state.apply_event(event)

    assert state.current_time == datetime(2026, 9, 19, 7, 0, tzinfo=timezone.utc)

    assert state.driving_today == timedelta(hours=8)
    assert state.duty_today == timedelta(hours=10)
    assert state.driving_since_break == timedelta(hours=8)

    assert state.cycle_used == timedelta(hours=35)
    assert state.distance_since_fuel == 500

def test_max_drivable_now_limited_by_driving_time():
    state = DriverState(
        current_time=datetime(2026, 9, 18, 8, 0, tzinfo=timezone.utc),
        shift_start=datetime(2026, 9, 18, 8, 0, tzinfo=timezone.utc),
        driving_today=timedelta(hours=9),
    )
    config = HOSConfig()

    # 11h limit - 9h used = 2h left. All other limits are larger.
    assert state.max_drivable_now(config, miles_per_hour=55) == timedelta(hours=2)


def test_max_drivable_now_limited_by_duty_window():
    state = DriverState(
        current_time=datetime(2026, 9, 18, 20, 0, tzinfo=timezone.utc),
        shift_start=datetime(2026, 9, 18, 8, 0, tzinfo=timezone.utc),
    )
    config = HOSConfig()

    # Duty window ends at 22:00 -> 2h left.
    assert state.max_drivable_now(config, miles_per_hour=55) == timedelta(hours=2)


def test_max_drivable_now_limited_by_break():
    state = DriverState(
        current_time=datetime(2026, 9, 18, 8, 0, tzinfo=timezone.utc),
        shift_start=datetime(2026, 9, 18, 8, 0, tzinfo=timezone.utc),
        driving_since_break=timedelta(hours=7),
    )
    config = HOSConfig()

    # Break required after 8h. 1h left.
    assert state.max_drivable_now(config, miles_per_hour=55) == timedelta(hours=1)


def test_max_drivable_now_limited_by_fuel():
    state = DriverState(
        current_time=datetime(2026, 9, 18, 8, 0, tzinfo=timezone.utc),
        shift_start=datetime(2026, 9, 18, 8, 0, tzinfo=timezone.utc),
        distance_since_fuel=900,
    )
    config = HOSConfig()

    # 100 miles left -> 100/55 hours ≈ 1h49m.
    # All other limits are much larger.
    result = state.max_drivable_now(config, miles_per_hour=55)
    assert result == timedelta(hours=100 / 55)


def test_max_drivable_now_returns_zero_when_cycle_exhausted():
    state = DriverState(
        current_time=datetime(2026, 9, 18, 8, 0, tzinfo=timezone.utc),
        shift_start=datetime(2026, 9, 18, 8, 0, tzinfo=timezone.utc),
        cycle_used=timedelta(hours=70),
    )
    config = HOSConfig()

    assert state.max_drivable_now(config, miles_per_hour=55) == timedelta(0)