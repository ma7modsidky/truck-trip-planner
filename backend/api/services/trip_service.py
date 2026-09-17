from dataclasses import dataclass
from datetime import date, datetime

from trip_planner.domain.models import (
    DriverState,
    Route,
    ScheduleEvent,
    TripRequest,
)
from trip_planner.services.daily_splitter import split_events_by_day
from trip_planner.services.trip_planner import TripPlanner

from api.services.ors_client import ORSClient


@dataclass(frozen=True)
class TripPlanResult:
    request: TripRequest
    route: Route
    events: list[ScheduleEvent]
    days: dict[date, list[ScheduleEvent]]


class TripService:
    def __init__(
        self,
        ors_client: ORSClient,
        miles_per_hour: float = 55.0,
    ):
        self.ors_client = ors_client
        self.miles_per_hour = miles_per_hour

    def plan(self, request: TripRequest) -> TripPlanResult:
        route = self._build_route(request)
        state = self._build_state(request)
        events = self._build_events(route, state)
        days = split_events_by_day(events)

        return TripPlanResult(
            request=request,
            route=route,
            events=events,
            days=days,
        )

    def _build_route(self, request: TripRequest) -> Route:
        leg_to_pickup = self.ors_client.get_leg(
            origin=request.current_location,
            destination=request.pickup_location,
        )
        leg_to_dropoff = self.ors_client.get_leg(
            origin=request.pickup_location,
            destination=request.dropoff_location,
        )
        return Route(legs=[leg_to_pickup, leg_to_dropoff])

    def _build_state(self, request: TripRequest) -> DriverState:
        return DriverState(
            current_time=request.start_time,
            shift_start=request.start_time,
            cycle_used=request.current_cycle_used,
        )

    def _build_events(
        self,
        route: Route,
        state: DriverState,
    ) -> list[ScheduleEvent]:
        planner = TripPlanner(
            route=route,
            state=state,
            miles_per_hour=self.miles_per_hour,
        )
        return planner.plan()