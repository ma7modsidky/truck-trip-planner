from datetime import timedelta

import pytest

from api.services.ors_client import ORSClient, RoutingError
from trip_planner.domain.models import Location


def _fake_geojson_response(
    distance_meters: float,
    duration_seconds: float,
    coords: list[list[float]] | None = None,
) -> dict:
    return {
        "features": [
            {
                "geometry": {
                    "type": "LineString",
                    "coordinates": coords or [[-118.24, 34.05], [-112.07, 33.45]],
                },
                "properties": {
                    "summary": {
                        "distance": distance_meters,
                        "duration": duration_seconds,
                    }
                },
            }
        ]
    }


def test_get_leg_converts_meters_to_miles(monkeypatch):
    la = Location("Los Angeles", 34.05, -118.24)
    phoenix = Location("Phoenix", 33.45, -112.07)

    client = ORSClient(api_key="dummy")

    monkeypatch.setattr(
        client._client,
        "directions",
        lambda **kwargs: _fake_geojson_response(
            distance_meters=1609.344 * 370,
            duration_seconds=6 * 3600 + 45 * 60,
        ),
    )

    leg = client.get_leg(la, phoenix)

    assert leg.distance_miles == pytest.approx(370.0, rel=1e-6)
    assert leg.duration == timedelta(hours=6, minutes=45)
    # [lng, lat] → (lat, lng)
    assert leg.geometry == [(34.05, -118.24), (33.45, -112.07)]



def test_get_leg_raises_routing_error_on_malformed_response(monkeypatch):
    la = Location("Los Angeles", 34.05, -118.24)
    phoenix = Location("Phoenix", 33.45, -112.07)

    client = ORSClient(api_key="dummy")

    monkeypatch.setattr(
        client._client,
        "directions",
        lambda **kwargs: {},  # missing "routes"
    )

    with pytest.raises(RoutingError):
        client.get_leg(la, phoenix)


def test_client_requires_api_key(monkeypatch):
    monkeypatch.delenv("ORS_API_KEY", raising=False)

    with pytest.raises(RoutingError):
        ORSClient()