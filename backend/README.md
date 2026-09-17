# Backend — Truck Trip Planner

Django + DRF backend for a truck trip planner that takes a trip request, fetches the driving route from OpenRouteService, and produces:

* A full schedule of driving, break, rest, fuel, pickup, and dropoff events.
* A per-day grouping of those events suitable for drawing ELD log sheets.

The backend owns two things:

1. **The HOS scheduling engine** — pure Python, framework-agnostic.
2. **A thin HTTP API** — exposes the engine to the React frontend.

---

## Architecture

```text
┌─────────────────────────────────────────────────────────────────┐
│ HTTP layer (DRF)                                                │
│ api/views.py                                                    │
│ api/serializers.py                                              │
│                                                                 │
│ - validates input                                               │
│ - maps domain errors to HTTP status codes                       │
│ - does NOT contain business rules                               │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│ Application services                                            │
│ api/services/trip_service.py — orchestrates the pipeline        │
│ api/services/ors_client.py — wraps OpenRouteService             │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│ Domain layer (pure)                                              │
│ trip_planner/domain/ — HOSConfig, DriverState, events...         │
│ trip_planner/services/ — scheduler, planner, splitter            │
│                                                                 │
│ - no Django, no HTTP, no network                                │
│ - fully unit-tested                                              │
└─────────────────────────────────────────────────────────────────┘
```

The domain layer can be extracted into a standalone Python package and used by any other system (CLI, background worker, etc.) without changes.

---

## Business Rules — Hours of Service

All rules are configurable via `trip_planner/domain/config.py:HOSConfig`.

The defaults below reflect the assessment's assumptions.

### Limits

| Rule                           |         Default | Config field               |
| ------------------------------ | --------------: | -------------------------- |
| Max driving per shift          |        11 hours | `max_driving_time`         |
| Max duty window per shift      |        14 hours | `max_duty_window`          |
| Max cycle time (8-day rolling) |        70 hours | `cycle_limit`              |
| Required daily rest            |        10 hours | `required_rest_time`       |
| Break required after           | 8 hours driving | `break_after_driving_time` |
| Break duration                 |      30 minutes | `break_duration`           |
| Fuel interval                  |     1,000 miles | `fuel_interval_miles`      |
| Fuel stop duration             |      30 minutes | `fuel_duration`            |
| Pickup duration                |          1 hour | `pickup_duration`          |
| Dropoff duration               |          1 hour | `dropoff_duration`         |

### How a Duty Status Maps to State Changes

| Status     | Counts toward driving? | Counts toward duty? | Counts toward cycle? | Resets break clock? | Resets daily counters? |
| ---------- | ---------------------- | ------------------- | -------------------- | ------------------- | ---------------------- |
| `DRIVING`  | Yes                    | Yes                 | Yes                  | Yes (adds to clock) | No                     |
| `ON_DUTY`  | No                     | Yes                 | Yes                  | No                  | No                     |
| `OFF_DUTY` | No                     | No                  | No                   | Yes (if ≥ 30 min)   | No                     |
| `SLEEPER`  | No                     | No                  | No                   | Yes (if ≥ 30 min)   | Yes (if ≥ 10 hours)    |

### What a 10-Hour Rest Resets

| Field                 | Reset by 10h rest?    |
| --------------------- | --------------------- |
| `driving_today`       | Yes                   |
| `duty_today`          | Yes                   |
| `driving_since_break` | Yes                   |
| `shift_start`         | Yes (set to rest end) |
| `cycle_used`          | **No**                |
| `distance_since_fuel` | **No**                |

**Rationale:** The 70-hour cycle is a rolling 8-day total, not a daily budget. A rest does not refuel the truck, so fuel distance is preserved.

### What a Fuel Stop Resets

* `distance_since_fuel` → `0`
* Nothing else

### Stop Priority

When the driver has driven as far as allowed, exactly one stop is required.

The planner picks the first matching rule in this order:

1. **Fuel** — if `remaining_distance_before_fuel <= 0`
2. **Break** — if `driving_since_break >= 8 hours`
3. **Rest** — if the 11-hour driving limit or the 14-hour duty window is exhausted
4. **Cycle exhausted** — the trip is impossible; raise `TripImpossibleError`

Fuel is first because it is the shortest stop (30 minutes) and does not consume rest budget. Rest is last because it is the most expensive.

### Assignment-Specific Assumptions

These are the assessment's assumptions, encoded in the domain:

* **Property-carrying driver, 70 hrs / 8 days.** The 70-hour cycle limit is enforced as an absolute cap.
* **No adverse driving conditions.** No weather or traffic multipliers.
* **Fuel at least once every 1,000 miles.** Enforced as a hard limit.
* **1 hour for pickup and 1 hour for dropoff.** Both count as `ON_DUTY`.
* **Average speed.** The planner is parameterized by `miles_per_hour` (default 55). It is used only to convert distance limits into time limits, and vice versa.

### Datetime Policy

**All datetimes in the domain are timezone-aware.**

UTC is used as the canonical day boundary for ELD log grouping. The domain explicitly rejects naive datetimes at construction time.

This is a deliberate simplification: a production ELD would group by the driver's home-terminal time zone, which can shift the day boundary by an hour or two when crossing time zones. For this assessment, UTC is sufficient and unambiguous.

---

## The Scheduling Algorithm

Given a route (two legs: current → pickup, pickup → dropoff), the planner:

1. Builds a `DriverState` from the trip request (start time and current cycle usage).
2. For each leg, repeatedly asks the state:

   > "What is the maximum continuous driving time available right now?"

   This is the minimum of all active constraints.
3. Drives as far as allowed, or until the leg ends, whichever comes first.
4. If the leg is not finished, takes the required stop (fuel / break / rest) and loops.
5. Between legs, schedules the operational activity (pickup, then dropoff).
6. Returns the full list of `ScheduleEvent`s.

The algorithm is deterministic and produces a contiguous timeline: each event starts exactly when the previous one ends.

---

## Project Layout

```text
backend/
├── manage.py
├── config/                         # Django project (settings, urls, wsgi)
├── api/                            # DRF app
│   ├── serializers.py             # Request + response serializers
│   ├── views.py                   # POST /api/plan-trip/
│   ├── urls.py
│   └── services/
│       ├── ors_client.py           # OpenRouteService wrapper
│       └── trip_service.py         # Pipeline orchestration
├── trip_planner/                   # Pure-Python domain (no Django)
│   ├── domain/
│   │   ├── config.py               # HOSConfig (all limits)
│   │   ├── enums.py               # Activity, DutyStatus
│   │   └── models.py              # Location, Route, RouteLeg,
│   │                                # ScheduleEvent, DriverState,
│   │                                # TripRequest
│   └── services/
│       ├── scheduler.py            # HOSScheduler (primitive operations)
│       ├── trip_planner.py         # TripPlanner (whole-trip algorithm)
│       └── daily_splitter.py       # Split events by calendar day
├── tests/                          # Pytest suite (all layers)
├── pytest.ini
├── requirements.txt
└── .env                            # ORS_API_KEY (never committed)
```

---

## Setup

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env              # Then edit .env
python manage.py migrate
python manage.py runserver
```

### Environment Variables

| Variable            | Purpose                                   |
| ------------------- | ----------------------------------------- |
| `ORS_API_KEY`       | OpenRouteService API key (required)       |
| `DJANGO_DEBUG`      | `True` for local development              |
| `DJANGO_SECRET_KEY` | Django secret (any string in development) |

Get a free ORS key from [OpenRouteService](https://openrouteservice.org/dev/#/signup).

---

## Testing

```bash
pytest
```

The suite covers:

* **Domain:** state transitions, constraint queries, event validation
* **Scheduler:** each primitive operation and its failure modes
* **Planner:** whole-trip scheduling, stop insertion, float safety
* **Splitter:** per-day grouping, midnight spanning
* **ORS client:** unit conversion, error handling (mocked)
* **Trip service:** full pipeline with a fake ORS client
* **API:** request validation, success response shape, error mapping

No test hits the network. All external calls are mocked or faked.

---

## Error Mapping

| Domain error          | HTTP status | Body shape                                      |
| --------------------- | ----------: | ----------------------------------------------- |
| Validation failure    |         400 | `{"field": ["error message"]}`                  |
| `RoutingError`        |         400 | `{"error": "routing_failed", "detail": "..."}`  |
| `TripImpossibleError` |         422 | `{"error": "trip_impossible", "detail": "..."}` |

`422` is used for `TripImpossibleError` because the input is valid — the trip simply cannot be completed under HOS rules. For example, the current cycle usage may already exceed the available 70-hour cycle.

---

## What This Backend Does Not Do

* **Geocoding.** Locations are expected to be provided as `{name, latitude, longitude}`. The frontend is responsible for turning user input into coordinates.
* **Persistence.** There is no database. Requests are stateless.
* **Authentication.** No authentication — this is a demo/assessment backend.
* **Time zone conversion for display.** All datetimes are returned in UTC. The frontend can convert them for display if desired.

---

## API Documentation

The REST API has its own documentation in [`API.md`](API.md).

For an assessment project, a concise Markdown API reference is sufficient. Interactive Swagger/OpenAPI documentation can be added later with `drf-spectacular`.
