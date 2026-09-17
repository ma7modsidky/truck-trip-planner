from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.serializers import (
    TripPlanResponseSerializer,
    TripRequestSerializer,
)
from api.services.ors_client import ORSClient, RoutingError
from api.services.trip_service import TripService
from trip_planner.services.trip_planner import TripImpossibleError


@api_view(["POST"])
def plan_trip(request):
    serializer = TripRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    trip_request = serializer.to_trip_request()

    try:
        service = TripService(ors_client=ORSClient())
        result = service.plan(trip_request)
    except RoutingError as exc:
        return Response(
            {"error": "routing_failed", "detail": str(exc)},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except TripImpossibleError as exc:
        return Response(
            {"error": "trip_impossible", "detail": str(exc)},
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    # Build the response manually — see below.
    payload = _build_response_payload(result)
    response_serializer = TripPlanResponseSerializer(payload)
    return Response(response_serializer.data, status=status.HTTP_200_OK)


def _build_response_payload(result) -> dict:
    """
    Shape the TripPlanResult into a dict that the response
    serializers can consume.

    days is turned from dict[date, list[event]] into
    list[{"date": date, "events": [...]}].
    """
    return {
        "route": result.route,
        "events": result.events,
        "days": [
            {"date": day, "events": events}
            for day, events in result.days.items()
        ],
    }