import pytest
from datetime import datetime, timedelta

from trip_planner.domain.enums import Activity
from trip_planner.domain.models import DriverState, Location, Route, RouteLeg
from trip_planner.services.trip_planner import TripPlanner, TripImpossibleError

def test_trip_planner_completes_short_trip():
    la = Location("Los Angeles", 34.05, -118.24)
    phoenix = Location("Phoenix", 33.45, -112.07)
    tucson = Location("Tucson", 32.22, -110.97)

    route = Route(legs=[
        RouteLeg(origin=la, destination=phoenix,
                 distance_miles=370,
                 duration=timedelta(hours=6, minutes=45)),
        RouteLeg(origin=phoenix, destination=tucson,
                 distance_miles=120,
                 duration=timedelta(hours=2, minutes=10)),
    ])

    state = DriverState(
        current_time=datetime(2026, 9, 18, 8, 0),
        shift_start=datetime(2026, 9, 18, 8, 0),
    )

    planner = TripPlanner(route, state, miles_per_hour=55)
    events = planner.plan()

    activities = [e.activity for e in events]

    # PICKUP happens after the first leg, DROPOFF after the second.
    assert Activity.PICKUP in activities
    assert Activity.DROPOFF in activities
    assert activities.index(Activity.PICKUP) < activities.index(Activity.DROPOFF)
    assert activities[-1] == Activity.DROPOFF

    # Total mileage is preserved across all DRIVING events.
    total_driven = sum(
        e.distance_miles for e in events if e.activity == Activity.DRIVING
    )
    assert total_driven == pytest.approx(490, rel=1e-3)

    # A break was inserted because the driver hit 8h cumulative driving.
    assert Activity.BREAK in activities


def test_trip_planner_inserts_rest_on_long_trip():
    la = Location("Los Angeles", 34.05, -118.24)
    phoenix = Location("Phoenix", 33.45, -112.07)
    dallas = Location("Dallas", 32.78, -96.80)

    route = Route(legs=[
        RouteLeg(origin=la, destination=phoenix,
                 distance_miles=370,
                 duration=timedelta(hours=6, minutes=45)),
        RouteLeg(origin=phoenix, destination=dallas,
                 distance_miles=1070,
                 duration=timedelta(hours=19, minutes=30)),
    ])

    state = DriverState(
        current_time=datetime(2026, 9, 18, 6, 0),
        shift_start=datetime(2026, 9, 18, 6, 0),
    )

    planner = TripPlanner(route, state, miles_per_hour=55)
    events = planner.plan()

    activities = [e.activity for e in events]

    assert Activity.REST in activities
    assert Activity.FUEL in activities
    assert Activity.BREAK in activities
    assert activities[-1] == Activity.DROPOFF

    # Every mile of the route is accounted for.
    total_driven = sum(
        e.distance_miles for e in events if e.activity == Activity.DRIVING
    )
    assert total_driven == pytest.approx(1440, rel=1e-3)


def test_events_are_contiguous():
    la = Location("Los Angeles", 34.05, -118.24)
    phoenix = Location("Phoenix", 33.45, -112.07)
    dallas = Location("Dallas", 32.78, -96.80)

    route = Route(legs=[
        RouteLeg(origin=la, destination=phoenix,
                 distance_miles=370,
                 duration=timedelta(hours=6, minutes=45)),
        RouteLeg(origin=phoenix, destination=dallas,
                 distance_miles=1070,
                 duration=timedelta(hours=19, minutes=30)),
    ])

    state = DriverState(
        current_time=datetime(2026, 9, 18, 6, 0),
        shift_start=datetime(2026, 9, 18, 6, 0),
    )

    planner = TripPlanner(route, state, miles_per_hour=55)
    events = planner.plan()
    for prev, curr in zip(events, events[1:]):
        assert curr.start == prev.end, (
            f"Gap between {prev.activity} (ends {prev.end}) "
            f"and {curr.activity} (starts {curr.start})"
        )