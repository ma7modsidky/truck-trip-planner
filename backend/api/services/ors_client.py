import os

from datetime import timedelta

import openrouteservice
from openrouteservice.exceptions import ApiError, HTTPError

from trip_planner.domain.models import Location, RouteLeg


METERS_PER_MILE = 1609.344


class RoutingError(Exception):
    """Raised when a route cannot be obtained from the routing provider."""


class ORSClient:
    """
    Thin wrapper around the OpenRouteService directions API.

    Converts ORS's meter/second response into our domain's
    mile/timedelta representation.
    """

    def __init__(self, api_key: str | None = None):
        key = api_key or os.environ.get("ORS_API_KEY")
        if not key:
            raise RoutingError(
                "ORS_API_KEY is not configured. "
                "Set it in the environment or pass it explicitly."
            )
        self._client = openrouteservice.Client(key=key)

    def get_leg(
        self,
        origin: Location,
        destination: Location,
    ) -> RouteLeg:
        """
        Ask ORS for the driving route between two locations.
        Returns a RouteLeg with distance in miles and duration
        as a timedelta.
        """
        # ORS expects [longitude, latitude] (GeoJSON convention).
        coordinates = [
            [origin.longitude, origin.latitude],
            [destination.longitude, destination.latitude],
        ]

        try:
            response = self._client.directions(
                coordinates=coordinates,
                profile="driving-hgv",  # heavy goods vehicle — this is a trucking app
                format="json",
                units="m",
            )
        except (ApiError, HTTPError) as exc:
            raise RoutingError(
                f"Routing failed for {origin.name} → {destination.name}: {exc}"
            ) from exc

        return self._parse_response(response, origin, destination)

    def _parse_response(
        self,
        response: dict,
        origin: Location,
        destination: Location,
    ) -> RouteLeg:
        try:
            route = response["routes"][0]
            summary = route["summary"]
            distance_meters = summary["distance"]
            duration_seconds = summary["duration"]
        except (KeyError, IndexError) as exc:
            raise RoutingError(
                "Unexpected response shape from ORS."
            ) from exc

        distance_miles = distance_meters / METERS_PER_MILE
        duration = timedelta(seconds=duration_seconds)

        return RouteLeg(
            origin=origin,
            destination=destination,
            distance_miles=distance_miles,
            duration=duration,
        )