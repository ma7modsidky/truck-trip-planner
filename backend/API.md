# API Reference

Base URL (local): `http://127.0.0.1:8000/api/`

All requests and responses use `application/json`.

---

## POST `/api/plan-trip/`

Plan a trip and generate the full ELD schedule.

### Request Body

```json
{
  "current_location": {
    "name": "Los Angeles, CA",
    "latitude": 34.05,
    "longitude": -118.24
  },
  "pickup_location": {
    "name": "Phoenix, AZ",
    "latitude": 33.45,
    "longitude": -112.07
  },
  "dropoff_location": {
    "name": "Tucson, AZ",
    "latitude": 32.22,
    "longitude": -110.97
  },
  "current_cycle_used_hours": 5.0,
  "start_time": "2026-09-18T08:00:00Z"
}
```

### Request Fields

| Field                      | Type   | Required | Notes                                               |
| -------------------------- | ------ | -------- | --------------------------------------------------- |
| `current_location`         | object | Yes      | `{name, latitude, longitude}`                       |
| `pickup_location`          | object | Yes      | `{name, latitude, longitude}`                       |
| `dropoff_location`         | object | Yes      | `{name, latitude, longitude}`                       |
| `current_cycle_used_hours` | number | Yes      | `0–70`, hours already used in the 70-hour cycle     |
| `start_time`               | string | No       | ISO 8601. Defaults to the server's current UTC time |

---

## Success Response — `200 OK`

```json
{
  "route": {
    "legs": [
      {
        "origin": {
          "name": "Los Angeles, CA",
          "latitude": 34.05,
          "longitude": -118.24
        },
        "destination": {
          "name": "Phoenix, AZ",
          "latitude": 33.45,
          "longitude": -112.07
        },
        "distance_miles": 370.4,
        "duration_hours": 6.75
      },
      {
        "origin": {
          "name": "Phoenix, AZ",
          "latitude": 33.45,
          "longitude": -112.07
        },
        "destination": {
          "name": "Tucson, AZ",
          "latitude": 32.22,
          "longitude": -110.97
        },
        "distance_miles": 119.8,
        "duration_hours": 2.15
      }
    ],
    "total_distance_miles": 490.2,
    "total_duration_hours": 8.9
  },
  "events": [
    {
      "start": "2026-09-18T08:00:00Z",
      "end": "2026-09-18T14:45:00Z",
      "status": "DRIVING",
      "activity": "DRIVING",
      "location": {
        "name": "Phoenix, AZ",
        "latitude": 33.45,
        "longitude": -112.07
      },
      "distance_miles": 370.4,
      "duration_minutes": 405.0
    },
    {
      "...": "more events"
    }
  ],
  "days": [
    {
      "date": "2026-09-18",
      "events": [
        {
          "...": "events for this day"
        }
      ],
      "totals": {
        "off_duty_hours": 0.0,
        "sleeper_hours": 0.0,
        "driving_hours": 8.5,
        "on_duty_hours": 1.0,
        "total_miles": 490.2
      }
    }
  ]
}
```

### Response Fields

| Field    | Description                                                        |
| -------- | ------------------------------------------------------------------ |
| `route`  | The two-leg route as returned by OpenRouteService                  |
| `events` | The full schedule as a flat list, ordered chronologically          |
| `days`   | The same events grouped by calendar day (UTC), with per-day totals |

---

## Event `status` Values

```text
OFF_DUTY
SLEEPER
DRIVING
ON_DUTY
```

## Event `activity` Values

```text
DRIVING
PICKUP
DROPOFF
FUEL
BREAK
REST
```

---

## Error Responses

### `400 Bad Request` — Validation Error

```json
{
  "current_cycle_used_hours": [
    "Ensure this value is less than or equal to 70."
  ]
}
```

### `400 Bad Request` — Routing Failure

Returned when OpenRouteService cannot calculate a route between the requested points.

```json
{
  "error": "routing_failed",
  "detail": "Routing failed for Los Angeles, CA → Phoenix, AZ: ..."
}
```

### `422 Unprocessable Entity` — Trip Impossible

Returned when the request is valid but the trip cannot be completed under the configured HOS rules.

```json
{
  "error": "trip_impossible",
  "detail": "70-hour cycle exhausted."
}
```

---

## Example

```bash
curl -X POST http://127.0.0.1:8000/api/plan-trip/ \
  -H "Content-Type: application/json" \
  -d '{
    "current_location": {
      "name": "Los Angeles, CA",
      "latitude": 34.05,
      "longitude": -118.24
    },
    "pickup_location": {
      "name": "Phoenix, AZ",
      "latitude": 33.45,
      "longitude": -112.07
    },
    "dropoff_location": {
      "name": "Dallas, TX",
      "latitude": 32.78,
      "longitude": -96.80
    },
    "current_cycle_used_hours": 5.0
  }'
```
