import pytest
from datetime import datetime, timedelta

from trip_planner.domain.enums import Activity, DutyStatus
from trip_planner.domain.models import DriverState
from trip_planner.services.scheduler import (
    HOSScheduler,
    SchedulingError,
)

def test_schedule_driving():
    state = DriverState(
        current_time=datetime(2026, 9, 18, 8, 0),
        shift_start=datetime(2026, 9, 18, 8, 0),
    )

    scheduler = HOSScheduler(state)

    event = scheduler.schedule_driving(
        duration=timedelta(hours=4),
        distance_miles=250,
    )

    assert event.start == datetime(2026, 9, 18, 8, 0)
    assert event.end == datetime(2026, 9, 18, 12, 0)

    assert state.current_time == datetime(
        2026, 9, 18, 12, 0
    )

    assert state.driving_today == timedelta(hours=4)
    assert state.duty_today == timedelta(hours=4)
    assert state.cycle_used == timedelta(hours=4)
    assert state.driving_since_break == timedelta(hours=4)
    assert state.distance_since_fuel == 250

def test_schedule_driving_rejects_exceeding_driving_limit():
    state = DriverState(
        current_time=datetime(2026, 9, 18, 8, 0),
        shift_start=datetime(2026, 9, 18, 8, 0),
        driving_today=timedelta(hours=10),
    )

    scheduler = HOSScheduler(state)

    with pytest.raises(SchedulingError):
        scheduler.schedule_driving(
            duration=timedelta(hours=2),
            distance_miles=100,
        )

def test_schedule_driving_rejects_exceeding_duty_window():
    state = DriverState(
        current_time=datetime(2026, 9, 18, 21, 0),
        shift_start=datetime(2026, 9, 18, 8, 0),
    )

    scheduler = HOSScheduler(state)

    with pytest.raises(SchedulingError):
        scheduler.schedule_driving(
            duration=timedelta(hours=2),
            distance_miles=100,
        )

def test_schedule_driving_rejects_exceeding_cycle_limit():
    state = DriverState(
        current_time=datetime(2026, 9, 18, 8, 0),
        shift_start=datetime(2026, 9, 18, 8, 0),
        cycle_used=timedelta(hours=69),
    )

    scheduler = HOSScheduler(state)

    with pytest.raises(SchedulingError):
        scheduler.schedule_driving(
            duration=timedelta(hours=2),
            distance_miles=100,
        )

def test_schedule_driving_rejects_exceeding_fuel_interval():
    state = DriverState(
        current_time=datetime(2026, 9, 18, 8, 0),
        shift_start=datetime(2026, 9, 18, 8, 0),
        distance_since_fuel=900,
    )

    scheduler = HOSScheduler(state)

    with pytest.raises(SchedulingError):
        scheduler.schedule_driving(
            duration=timedelta(hours=2),
            distance_miles=200,
        )

def test_schedule_driving_rejects_zero_duration():
    state = DriverState(
        current_time=datetime(2026, 9, 18, 8, 0),
        shift_start=datetime(2026, 9, 18, 8, 0),
    )

    scheduler = HOSScheduler(state)

    with pytest.raises(SchedulingError):
        scheduler.schedule_driving(
            duration=timedelta(0),
            distance_miles=100,
        )

def test_schedule_driving_rejects_negative_distance():
    state = DriverState(
        current_time=datetime(2026, 9, 18, 8, 0),
        shift_start=datetime(2026, 9, 18, 8, 0),
    )

    scheduler = HOSScheduler(state)

    with pytest.raises(SchedulingError):
        scheduler.schedule_driving(
            duration=timedelta(hours=1),
            distance_miles=-10,
        )

def test_schedule_break():
    state = DriverState(
        current_time=datetime(2026, 9, 18, 16, 0),
        shift_start=datetime(2026, 9, 18, 8, 0),
        driving_today=timedelta(hours=8),
        duty_today=timedelta(hours=8),
        cycle_used=timedelta(hours=8),
        driving_since_break=timedelta(hours=8),
        distance_since_fuel=500,
    )

    scheduler = HOSScheduler(state)

    event = scheduler.schedule_break()

    assert event.start == datetime(2026, 9, 18, 16, 0)
    assert event.end == datetime(2026, 9, 18, 16, 30)

    assert event.status == DutyStatus.OFF_DUTY
    assert event.activity == Activity.BREAK

    assert state.current_time == datetime(2026, 9, 18, 16, 30)
    assert state.driving_since_break == timedelta(0)

    # These shouldn't change.
    assert state.driving_today == timedelta(hours=8)
    assert state.duty_today == timedelta(hours=8)
    assert state.cycle_used == timedelta(hours=8)
    assert state.distance_since_fuel == 500

def test_schedule_break_can_be_taken_before_break_is_required():
    state = DriverState(
        current_time=datetime(2026, 9, 18, 10, 0),
        shift_start=datetime(2026, 9, 18, 8, 0),
        driving_since_break=timedelta(hours=2),
    )

    scheduler = HOSScheduler(state)

    scheduler.schedule_break()

    assert state.current_time == datetime(2026, 9, 18, 10, 30)
    assert state.driving_since_break == timedelta(0)

def test_schedule_rest():
    state = DriverState(
        current_time=datetime(2026, 9, 18, 22, 0),
        shift_start=datetime(2026, 9, 18, 8, 0),
        driving_today=timedelta(hours=8),
        duty_today=timedelta(hours=10),
        cycle_used=timedelta(hours=35),
        driving_since_break=timedelta(hours=8),
        distance_since_fuel=500,
    )

    scheduler = HOSScheduler(state)

    event = scheduler.schedule_rest()

    assert event.start == datetime(2026, 9, 18, 22, 0)
    assert event.end == datetime(2026, 9, 19, 8, 0)

    assert event.status == DutyStatus.SLEEPER
    assert event.activity == Activity.REST

    assert state.current_time == datetime(2026, 9, 19, 8, 0)

    assert state.shift_start == datetime(2026, 9, 19, 8, 0)

    assert state.driving_today == timedelta(0)
    assert state.duty_today == timedelta(0)
    assert state.driving_since_break == timedelta(0)

    assert state.cycle_used == timedelta(hours=35)
    assert state.distance_since_fuel == 500