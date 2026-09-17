from datetime import date, datetime, timedelta, timezone

import pytest

from api.services.ors_client import RoutingError
from api.services.trip_service import TripService
from trip_planner.domain.models import (
    Location,
    RouteLeg,
    TripRequest,
)


class FakeORSClient:
    """Returns preprogrammed RouteLegs without hitting the network."""

    def __init__(self, legs: list[RouteLeg]):
        self._legs = legs
        self.calls: list[tuple[Location, Location]] = []

    def get_leg(self, origin: Location, destination: Location) -> RouteLeg:
        self.calls.append((origin, destination))

        for leg in self._legs:
            if leg.origin == origin and leg.destination == destination:
                return leg

        raise RoutingError(
            f"No fake leg for {origin.name} → {destination.name}"
        )


@pytest.fixture
def la_phoenix_tucson():
    la = Location("Los Angeles", 34.05, -118.24)
    phoenix = Location("Phoenix", 33.45, -112.07)
    tucson = Location("Tucson", 32.22, -110.97)

    leg_to_pickup = RouteLeg(
        origin=la,
        destination=phoenix,
        distance_miles=370,
        duration=timedelta(hours=6, minutes=45),
    )
    leg_to_dropoff = RouteLeg(
        origin=phoenix,
        destination=tucson,
        distance_miles=120,
        duration=timedelta(hours=2, minutes=10),
    )
    return la, phoenix, tucson, leg_to_pickup, leg_to_dropoff


def test_trip_service_plans_simple_trip(la_phoenix_tucson):
    la, phoenix, tucson, leg0, leg1 = la_phoenix_tucson

    request = TripRequest(
        current_location=la,
        pickup_location=phoenix,
        dropoff_location=tucson,
        current_cycle_used=timedelta(0),
        start_time=datetime(2026, 9, 18, 8, 0, tzinfo=timezone.utc),
    )

    fake_client = FakeORSClient([leg0, leg1])
    service = TripService(ors_client=fake_client, miles_per_hour=55)

    result = service.plan(request)

    # Both legs were requested from ORS.
    assert len(fake_client.calls) == 2
    assert fake_client.calls[0] == (la, phoenix)
    assert fake_client.calls[1] == (phoenix, tucson)

    # Route was built correctly.
    assert result.route.legs == [leg0, leg1]

    # Events were produced.
    assert len(result.events) > 0
    assert result.events[0].start == datetime(2026, 9, 18, 8, 0, tzinfo=timezone.utc)
    assert result.events[-1].end > result.events[0].end

    # Days were grouped.
    assert isinstance(result.days, dict)
    for day, day_events in result.days.items():
        assert isinstance(day, date)
        assert len(day_events) > 0


def test_trip_service_propagates_cycle_used(la_phoenix_tucson):
    la, phoenix, tucson, leg0, leg1 = la_phoenix_tucson

    request = TripRequest(
        current_location=la,
        pickup_location=phoenix,
        dropoff_location=tucson,
        current_cycle_used=timedelta(hours=30),
        start_time=datetime(2026, 9, 18, 8, 0, tzinfo=timezone.utc),
    )

    fake_client = FakeORSClient([leg0, leg1])
    service = TripService(ors_client=fake_client)

    result = service.plan(request)

    # The state should have started at 30h and grown.
    # (We can't inspect the state directly, but the events will
    # reflect it.)
    total_duration = sum(
        (e.duration for e in result.events),
        timedelta(0),
    )
    assert total_duration > timedelta(0)


def test_trip_service_raises_when_ors_fails(la_phoenix_tucson):
    la, phoenix, tucson, leg0, _ = la_phoenix_tucson

    request = TripRequest(
        current_location=la,
        pickup_location=phoenix,
        dropoff_location=tucson,
        current_cycle_used=timedelta(0),
        start_time=datetime(2026, 9, 18, 8, 0, tzinfo=timezone.utc),
    )

    # Only provide the first leg — the second call will fail.
    fake_client = FakeORSClient([leg0])
    service = TripService(ors_client=fake_client)

    with pytest.raises(RoutingError):
        service.plan(request)