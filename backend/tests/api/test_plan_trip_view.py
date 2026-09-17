import pytest
from unittest.mock import patch
from datetime import datetime, timedelta

from rest_framework.test import APIClient

from trip_planner.domain.models import Location, RouteLeg


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def valid_request_payload():
    return {
        "current_location": {
            "name": "Los Angeles, CA",
            "latitude": 34.05,
            "longitude": -118.24,
        },
        "pickup_location": {
            "name": "Phoenix, AZ",
            "latitude": 33.45,
            "longitude": -112.07,
        },
        "dropoff_location": {
            "name": "Tucson, AZ",
            "latitude": 32.22,
            "longitude": -110.97,
        },
        "current_cycle_used_hours": 5.0,
        "start_time": "2026-09-18T08:00:00",
    }


@pytest.mark.django_db
def test_plan_trip_returns_plan(api_client, valid_request_payload):
    la = Location("Los Angeles, CA", 34.05, -118.24)
    phoenix = Location("Phoenix, AZ", 33.45, -112.07)
    tucson = Location("Tucson, AZ", 32.22, -110.97)

    fake_legs = [
        RouteLeg(
            origin=la, destination=phoenix,
            distance_miles=370,
            duration=timedelta(hours=6, minutes=45),
        ),
        RouteLeg(
            origin=phoenix, destination=tucson,
            distance_miles=120,
            duration=timedelta(hours=2, minutes=10),
        ),
    ]

    with patch(
        "api.services.ors_client.ORSClient.get_leg",
        side_effect=lambda origin, destination: next(
            leg for leg in fake_legs
            if leg.origin.name == origin.name
            and leg.destination.name == destination.name
        ),
    ):
        response = api_client.post(
            "/api/plan-trip/",
            valid_request_payload,
            format="json",
        )

    assert response.status_code == 200
    body = response.json()

    assert "route" in body
    assert "events" in body
    assert "days" in body

    assert len(body["route"]["legs"]) == 2
    assert body["route"]["total_distance_miles"] == pytest.approx(490, rel=1e-3)

    assert len(body["events"]) > 0
    assert len(body["days"]) >= 1

    first_day = body["days"][0]
    assert "date" in first_day
    assert "events" in first_day
    assert "totals" in first_day


@pytest.mark.django_db
def test_plan_trip_rejects_invalid_input(api_client):
    response = api_client.post(
        "/api/plan-trip/",
        {"current_location": {"name": "LA"}},  # missing fields
        format="json",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_plan_trip_returns_400_on_routing_error(
    api_client,
    valid_request_payload,
):
    from api.services.ors_client import RoutingError

    with patch(
        "api.services.ors_client.ORSClient.get_leg",
        side_effect=RoutingError("no route"),
    ):
        response = api_client.post(
            "/api/plan-trip/",
            valid_request_payload,
            format="json",
        )

    assert response.status_code == 400
    assert response.json()["error"] == "routing_failed"