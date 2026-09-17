from dataclasses import dataclass
from datetime import timedelta


@dataclass(frozen=True)
class HOSConfig:
    max_driving_time: timedelta = timedelta(hours=11)
    max_duty_window: timedelta = timedelta(hours=14)

    required_rest_time: timedelta = timedelta(hours=10)

    break_after_driving_time: timedelta = timedelta(hours=8)
    break_duration: timedelta = timedelta(minutes=30)

    cycle_limit: timedelta = timedelta(hours=70)

    fuel_interval_miles: float = 1000.0
    fuel_duration: timedelta = timedelta(minutes=30)
    pickup_duration: timedelta = timedelta(hours=1)
    dropoff_duration: timedelta = timedelta(hours=1)