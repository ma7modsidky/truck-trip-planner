from datetime import datetime
from django.utils import timezone as django_timezone
from rest_framework import serializers

from trip_planner.domain.models import (
    Location,
    Route,
    RouteLeg,
    ScheduleEvent,
    TripRequest,
)

# --------------------------------------------------------------------
# Request
# --------------------------------------------------------------------
class LocationInputSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    latitude = serializers.FloatField(min_value=-90, max_value=90)
    longitude = serializers.FloatField(min_value=-180, max_value=180)


class TripRequestSerializer(serializers.Serializer):
    current_location = LocationInputSerializer()
    pickup_location = LocationInputSerializer()
    dropoff_location = LocationInputSerializer()

    current_cycle_used_hours = serializers.FloatField(min_value=0, max_value=70)
    start_time = serializers.DateTimeField(required=False)

    def to_trip_request(self) -> TripRequest:
        """Convert validated data into the domain TripRequest."""
        from datetime import timedelta

        data = self.validated_data

        def _location(key: str) -> Location:
            loc = data[key]
            return Location(
                name=loc["name"],
                latitude=loc["latitude"],
                longitude=loc["longitude"],
            )

        return TripRequest(
            current_location=_location("current_location"),
            pickup_location=_location("pickup_location"),
            dropoff_location=_location("dropoff_location"),
            current_cycle_used=timedelta(
                hours=data["current_cycle_used_hours"]
            ),
            start_time=data.get("start_time") or django_timezone.now(),
        )

# --------------------------------------------------------------------
# Response
# --------------------------------------------------------------------

class LocationOutputSerializer(serializers.Serializer):
    name = serializers.CharField()
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()


class RouteLegOutputSerializer(serializers.Serializer):
    origin = LocationOutputSerializer()
    destination = LocationOutputSerializer()
    distance_miles = serializers.FloatField()
    duration_hours = serializers.SerializerMethodField()

    def get_duration_hours(self, leg: RouteLeg) -> float:
        return leg.duration.total_seconds() / 3600


class RouteOutputSerializer(serializers.Serializer):
    legs = RouteLegOutputSerializer(many=True)
    total_distance_miles = serializers.FloatField()
    total_duration_hours = serializers.SerializerMethodField()

    def get_total_duration_hours(self, route: Route) -> float:
        return route.total_duration.total_seconds() / 3600


class ScheduleEventOutputSerializer(serializers.Serializer):
    start = serializers.DateTimeField()
    end = serializers.DateTimeField()
    status = serializers.CharField()
    activity = serializers.CharField()
    location = LocationOutputSerializer(allow_null=True)
    distance_miles = serializers.FloatField()

    def to_representation(self, event: ScheduleEvent):
        return {
            "start": event.start.isoformat(),
            "end": event.end.isoformat(),
            "status": event.status.value,
            "activity": event.activity.value,
            "location": (
                {
                    "name": event.location.name,
                    "latitude": event.location.latitude,
                    "longitude": event.location.longitude,
                }
                if event.location
                else None
            ),
            "distance_miles": event.distance_miles,
            "duration_minutes": event.duration.total_seconds() / 60,
        }


class DayPlanOutputSerializer(serializers.Serializer):
    date = serializers.DateField()
    events = ScheduleEventOutputSerializer(many=True)
    totals = serializers.SerializerMethodField()

    def get_totals(self, day_data) -> dict:
        """
        Compute the per-day duty-status totals for the ELD sheet.
        """
        from datetime import timedelta

        events = day_data["events"]

        totals = {
            "off_duty_hours": 0.0,
            "sleeper_hours": 0.0,
            "driving_hours": 0.0,
            "on_duty_hours": 0.0,
            "total_miles": 0.0,
        }

        for event in events:
            hours = event.duration.total_seconds() / 3600
            status = event.status.value

            if status == "OFF_DUTY":
                totals["off_duty_hours"] += hours
            elif status == "SLEEPER":
                totals["sleeper_hours"] += hours
            elif status == "DRIVING":
                totals["driving_hours"] += hours
            elif status == "ON_DUTY":
                totals["on_duty_hours"] += hours

            totals["total_miles"] += event.distance_miles

        return totals


class TripPlanResponseSerializer(serializers.Serializer):
    route = RouteOutputSerializer()
    events = ScheduleEventOutputSerializer(many=True)
    days = DayPlanOutputSerializer(many=True)