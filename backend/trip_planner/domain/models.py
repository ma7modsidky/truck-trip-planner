from dataclasses import dataclass
from datetime import datetime, timedelta

from .enums import Activity, DutyStatus
from .config import HOSConfig
from trip_planner.domain import config

@dataclass(frozen=True)
class Location:
    name: str
    latitude: float
    longitude: float


@dataclass(frozen=True)
class ScheduleEvent:
    start: datetime
    end: datetime
    status: DutyStatus
    activity: Activity
    location: Location | None = None
    distance_miles: float = 0.0

    def __post_init__(self):
        if self.end <= self.start:
            raise ValueError("Event end must be after event start.")

        if self.distance_miles < 0:
            raise ValueError("Distance cannot be negative.")

    @property
    def duration(self) -> timedelta:
        return self.end - self.start

@dataclass
class DriverState:
    current_time: datetime
    shift_start: datetime

    driving_today: timedelta = timedelta(0)
    duty_today: timedelta = timedelta(0)

    cycle_used: timedelta = timedelta(0)

    driving_since_break: timedelta = timedelta(0)

    distance_since_fuel: float = 0.0

    def apply_event(self, event: ScheduleEvent) -> None:
        if event.start != self.current_time:
            raise ValueError(
                "Event must start at the driver's current time."
            )
        duration = event.duration

        if event.status == DutyStatus.DRIVING:
            self._apply_driving(
                duration,
                event.distance_miles,
            )

        elif event.status == DutyStatus.ON_DUTY:
            self._apply_on_duty(duration)
            if event.activity == Activity.FUEL:
                self.distance_since_fuel = 0.0

        elif event.status == DutyStatus.OFF_DUTY:
            self._apply_off_duty(duration)

        elif event.status == DutyStatus.SLEEPER:
            self._apply_sleeper(duration, event.end)

        else:
            raise ValueError(
                f"Unsupported duty status: {event.status}"
            )

        self.current_time = event.end

    def _apply_driving(self, duration: timedelta, distance_miles: float,) -> None:
        self.driving_today += duration
        self.duty_today += duration
        self.cycle_used += duration
        self.driving_since_break += duration
        self.distance_since_fuel += distance_miles

    def _apply_on_duty(self, duration: timedelta) -> None:
        self.duty_today += duration
        self.cycle_used += duration

    def _apply_off_duty(self, duration: timedelta) -> None:
        if duration >= timedelta(minutes=30):
            self.driving_since_break = timedelta(0)

    def _apply_sleeper(self,duration: timedelta,rest_end: datetime,) -> None:
        if duration >= timedelta(hours=10):
            self.driving_today = timedelta(0)
            self.duty_today = timedelta(0)
            self.driving_since_break = timedelta(0)
            self.shift_start = rest_end

    def remaining_driving_time(self, config: HOSConfig) -> timedelta:
        remaining = config.max_driving_time - self.driving_today
        return max(remaining, timedelta(0))

    def remaining_duty_window(self, config: HOSConfig) -> timedelta:
        window_end = self.shift_start + config.max_duty_window
        remaining = window_end - self.current_time
        return max(remaining, timedelta(0))

    def remaining_cycle_time(self, config: HOSConfig) -> timedelta:
        remaining = config.cycle_limit - self.cycle_used
        return max(remaining, timedelta(0))

    def break_required(self, config: HOSConfig) -> bool:
        return self.driving_since_break >= config.break_after_driving_time

    def remaining_distance_before_fuel(self, config: HOSConfig,) -> float:
        remaining = config.fuel_interval_miles - self.distance_since_fuel
        return max(remaining, 0.0)

    def remaining_distance_before_break(self, config: HOSConfig) -> timedelta:
        """
        How much more driving time is allowed before a 30-minute break is required?
        """
        remaining = config.break_after_driving_time - self.driving_since_break
        return max(remaining, timedelta(0))

    def max_drivable_now(
            self,
            config: HOSConfig,
            miles_per_hour: float,
        ) -> timedelta:
        """
        The maximum continuous driving time available right now,
        before ANY HOS constraint forces a stop.

        miles_per_hour is needed to convert the fuel-distance limit
        into a time limit.
        """
        if miles_per_hour <= 0:
            raise ValueError("miles_per_hour must be positive.")

        fuel_remaining_miles = self.remaining_distance_before_fuel(config)
        fuel_remaining_time = timedelta(
            hours=fuel_remaining_miles / miles_per_hour
        )

        break_remaining_time = self.remaining_distance_before_break(config)

        candidates = [
            self.remaining_driving_time(config),
            self.remaining_duty_window(config),
            self.remaining_cycle_time(config),
            break_remaining_time,
            fuel_remaining_time,
        ]

        return min(candidates)

@dataclass(frozen=True)
class RouteLeg:
    origin: Location
    destination: Location
    distance_miles: float
    duration: timedelta


@dataclass(frozen=True)
class Route:
    legs: list[RouteLeg]

    @property
    def total_distance_miles(self) -> float:
        return sum(leg.distance_miles for leg in self.legs)

    @property
    def total_duration(self) -> timedelta:
        return sum((leg.duration for leg in self.legs), timedelta(0))

@dataclass(frozen=True)
class TripRequest:
    current_location: Location
    pickup_location: Location
    dropoff_location: Location

    current_cycle_used: timedelta

    start_time: datetime