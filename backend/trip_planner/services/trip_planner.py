from datetime import timedelta

from trip_planner.domain.config import HOSConfig
from trip_planner.domain.models import (
    DriverState,
    Route,
    ScheduleEvent,
)
from trip_planner.services.scheduler import (
    HOSScheduler,
    SchedulingError,
)

EPSILON_MILES = 1e-6

class TripImpossibleError(Exception):
    """Raised when the trip cannot be completed under HOS rules."""


class TripPlanner:
    def __init__(
    self,
    route: Route,
    state: DriverState,
    config: HOSConfig | None = None,
    miles_per_hour: float = 55.0,
):
        if len(route.legs) != 2:
            raise ValueError(
                "TripPlanner expects exactly 2 legs: "
                "current→pickup and pickup→dropoff."
            )

        self.route = route
        self.state = state
        self.config = config or HOSConfig()
        self.miles_per_hour = miles_per_hour
        self.scheduler = HOSScheduler(state, config)
        self.events: list[ScheduleEvent] = []

    def plan(self) -> list[ScheduleEvent]:
        current_to_pickup = self.route.legs[0]
        pickup_to_dropoff = self.route.legs[1]

        self._drive_leg(current_to_pickup)
        self._record(self.scheduler.schedule_pickup())

        self._drive_leg(pickup_to_dropoff)
        self._record(self.scheduler.schedule_dropoff())

        return self.events

    def _drive_leg(self, leg) -> None:
        EPSILON = 1e-6
        remaining_miles = leg.distance_miles

        while remaining_miles > EPSILON:
            available_time = self.state.max_drivable_now(
                self.config, self.miles_per_hour
            )

            if available_time <= timedelta(0):
                # Driver can't drive at all right now. Take the
                # required stop and try again.
                self._insert_required_stop()
                continue

            max_miles = available_time.total_seconds() / 3600 * self.miles_per_hour
            chunk_miles = min(remaining_miles, max_miles)

            # Guard against microscopic chunks from float drift.
            if chunk_miles < EPSILON:
                # Something is wrong: max_drivable_now says we can
                # drive, but the distance is negligible. Snap to done
                # and let the stop logic handle it.
                self._insert_required_stop()
                continue

            chunk_time = timedelta(hours=chunk_miles / self.miles_per_hour)

            is_final_chunk = chunk_miles >= remaining_miles - EPSILON

            self._record(
                self.scheduler.schedule_driving(
                    duration=chunk_time,
                    distance_miles=chunk_miles,
                    location=leg.destination if is_final_chunk else None,
                )
            )
            remaining_miles -= chunk_miles

    def _insert_required_stop(self) -> None:
        """
        Take the stop required by the current binding constraint.
        Order: fuel > break > rest > cycle (impossible).
        """
        # 1. Fuel?
        if self.state.remaining_distance_before_fuel(self.config) <= EPSILON_MILES:
            self._record(self.scheduler.schedule_fuel())
            return

        # 2. Break?
        if self.state.break_required(self.config):
            self._record(self.scheduler.schedule_break())
            return

        # 3. Rest? (11h or 14h exhausted)
        if (
            self.state.remaining_driving_time(self.config) <= timedelta(0)
            or self.state.remaining_duty_window(self.config) <= timedelta(0)
        ):
            self._record(self.scheduler.schedule_rest())
            return

        # 4. Cycle exhausted? Trip is impossible.
        if self.state.remaining_cycle_time(self.config) <= timedelta(0):
            raise TripImpossibleError("70-hour cycle exhausted.")

        raise TripImpossibleError(
            "Driving stopped but no HOS reason was identified. "
            f"State: driving_today={self.state.driving_today}, "
            f"duty_today={self.state.duty_today}, "
            f"driving_since_break={self.state.driving_since_break}, "
            f"cycle_used={self.state.cycle_used}, "
            f"distance_since_fuel={self.state.distance_since_fuel}"
        )

    def _record(self, event: ScheduleEvent) -> None:
        self.events.append(event)