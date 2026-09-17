from enum import Enum


class DutyStatus(str, Enum):
    OFF_DUTY = "OFF_DUTY"
    SLEEPER = "SLEEPER"
    DRIVING = "DRIVING"
    ON_DUTY = "ON_DUTY"


class Activity(str, Enum):
    DRIVING = "DRIVING"
    PICKUP = "PICKUP"
    DROPOFF = "DROPOFF"
    FUEL = "FUEL"
    BREAK = "BREAK"
    REST = "REST"