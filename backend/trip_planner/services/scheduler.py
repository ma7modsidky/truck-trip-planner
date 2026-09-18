from datetime import timedelta

from trip_planner.domain.config import HOSConfig
from trip_planner.domain.enums import Activity, DutyStatus
from trip_planner.domain.models import DriverState, Location, ScheduleEvent


class SchedulingError(Exception):
    """Raised when an activity cannot be scheduled."""


class HOSScheduler:

    def __init__(
        self,
        state: DriverState,
        config: HOSConfig | None = None,
    ):
        self.state = state
        self.config = config or HOSConfig()

    def schedule_driving(
        self,
        duration: timedelta,
        distance_miles: float,
        location: Location | None = None,
    ) -> ScheduleEvent:

        if duration <= timedelta(0):
            raise SchedulingError(
                "Driving duration must be greater than zero."
            )

        if distance_miles <= 0:
            raise SchedulingError(
                "Driving distance must be greater than zero."
            )

        if duration > self.state.remaining_driving_time(
            self.config
        ):
            raise SchedulingError(
                "Driving duration exceeds remaining driving time."
            )

        if duration > self.state.remaining_duty_window(
            self.config
        ):
            raise SchedulingError(
                "Driving duration exceeds remaining duty window."
            )

        if duration > self.state.remaining_cycle_time(
            self.config
        ):
            raise SchedulingError(
                "Driving duration exceeds remaining cycle time."
            )

        if distance_miles > self.state.remaining_distance_before_fuel(
            self.config
        ):
            raise SchedulingError(
                "Driving distance exceeds remaining fuel interval."
            )

        event = ScheduleEvent(
            start=self.state.current_time,
            end=self.state.current_time + duration,
            status=DutyStatus.DRIVING,
            activity=Activity.DRIVING,
            location=location,
            distance_miles=distance_miles,
        )

        self.state.apply_event(event)

        return event

    def schedule_break(self) -> ScheduleEvent:
        duration = self.config.break_duration

        event = ScheduleEvent(
            start=self.state.current_time,
            end=self.state.current_time + duration,
            status=DutyStatus.OFF_DUTY,
            activity=Activity.BREAK,
        )

        self.state.apply_event(event)

        return event

    def schedule_rest(self) -> ScheduleEvent:
        duration = self.config.required_rest_time

        event = ScheduleEvent(
            start=self.state.current_time,
            end=self.state.current_time + duration,
            status=DutyStatus.SLEEPER,
            activity=Activity.REST,
        )

        self.state.apply_event(event)

        return event

    def schedule_fuel(self) -> ScheduleEvent:
        return self._schedule_on_duty_activity(
        activity=Activity.FUEL,
        duration=self.config.fuel_duration,
        description="Fuel stop",
    )

    def schedule_pickup(
    self,
    location: Location | None = None,
    ) -> ScheduleEvent:
        return self._schedule_on_duty_activity(
            activity=Activity.PICKUP,
            duration=self.config.pickup_duration,
            description="Pickup",
            location=location,
        )

    def schedule_dropoff(
        self,
        location: Location | None = None,
    ) -> ScheduleEvent:
        return self._schedule_on_duty_activity(
            activity=Activity.DROPOFF,
            duration=self.config.dropoff_duration,
            description="Dropoff",
            location=location,
        )


    def _schedule_on_duty_activity(
        self,
        activity: Activity,
        duration: timedelta,
        description: str,
        location: Location | None = None,
    ) -> ScheduleEvent:
        if duration > self.state.remaining_duty_window(self.config):
            raise SchedulingError(
                f"{description} exceeds remaining duty window."
            )

        if duration > self.state.remaining_cycle_time(self.config):
            raise SchedulingError(
                f"{description} exceeds remaining cycle time."
            )

        event = ScheduleEvent(
            start=self.state.current_time,
            end=self.state.current_time + duration,
            status=DutyStatus.ON_DUTY,
            activity=activity,
            location=location,
        )

        self.state.apply_event(event)

        return event