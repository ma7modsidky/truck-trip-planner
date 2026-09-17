# Truck Trip Planner

A full-stack app that plans a trucking trip and generates the corresponding ELD (Electronic Logging Device) daily log sheets.

Enter a current location, a pickup, a dropoff, and how many hours the driver has already used in their 70-hour cycle. The app returns:

* **A map** showing the route and all stops (fuel, break, rest, pickup, dropoff).
* **Daily log sheets** filled out to match FMCSA format, one per day of the trip.

Built as a technical assessment.

---

## Live Demo

* **Frontend:** *add Vercel URL here*
* **Backend API:** *add Render/Railway URL here*

---

## Stack

| Layer    | Technology                                   |
| -------- | -------------------------------------------- |
| Backend  | Django 5 + Django REST Framework             |
| Routing  | OpenRouteService (`driving-hgv` profile)     |
| Domain   | Pure Python HOS scheduling engine            |
| Frontend | React + TypeScript + Vite                    |
| Map      | Leaflet + OpenStreetMap tiles                |
| Hosting  | Vercel (frontend) + Render/Railway (backend) |

---

## Repo Layout

```text
.
├── backend/                         # Django + DRF + HOS scheduling engine
│   ├── api/                         # HTTP layer (serializers, views, services)
│   ├── trip_planner/                # Pure-Python domain (no Django)
│   ├── tests/                       # Pytest suite
│   ├── README.md                    # Backend architecture and business rules
│   └── API.md                       # API reference
├── frontend/                        # React + TypeScript app (map + ELD sheets)
└── README.md                        # This file
```

The backend and frontend are independent: the backend is a JSON API, while the frontend is a static SPA. They can be deployed separately.

---

## Running Locally

### Backend

```bash
cd backend

python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env            # Add your ORS_API_KEY

python manage.py migrate
python manage.py runserver      # http://127.0.0.1:8000
```

### Frontend

```bash
cd frontend

npm install
cp .env.example .env            # Set VITE_API_BASE_URL

npm run dev                     # http://localhost:5173
```

The frontend expects the backend at `http://127.0.0.1:8000` by default.

---

## How It Works

1. The user submits a trip request from the React form.
2. The frontend sends the request to `POST /api/plan-trip/`.
3. The backend calls OpenRouteService twice:

   * Current location → pickup
   * Pickup → dropoff
4. The HOS scheduling engine walks the route legs and inserts fuel, break, rest, pickup, and dropoff events as required by the configured Hours of Service rules.
5. Events are grouped by calendar day (UTC).
6. The backend returns:

   * The calculated route
   * The complete flat list of schedule events
   * The per-day event grouping
7. The frontend:

   * Draws the route on a Leaflet map
   * Displays all stops
   * Renders one ELD log sheet per day

For the scheduling rules and algorithm in detail, see [`backend/README.md`](backend/README.md).

For the HTTP API reference, see [`backend/API.md`](backend/API.md).

---

## Assumptions

The assessment uses the following assumptions:

* Property-carrying driver, 70 hrs / 8 days cycle.
* No adverse driving conditions.
* Fuel at least once every 1,000 miles.
* 1 hour for pickup and 1 hour for dropoff.
* Average speed of 55 mph, used only to convert between distance and time.
* All times are computed and returned in UTC.

---

## Testing

```bash
cd backend
pytest
```

All layers are unit-tested.

No test hits the network — OpenRouteService is mocked or replaced with a fake client during testing.

The test suite covers:

* Domain models and HOS state transitions
* Scheduling primitives
* Full trip planning
* Daily event splitting
* OpenRouteService integration logic
* Trip service orchestration
* API validation and error handling

---

## What's Next

The following features are intentionally out of scope for the assessment but could be added in a production version:

* Time-zone-aware day grouping based on the driver's home terminal
* Persistence and user accounts
* Authentication and authorization
* Real-time traffic and adverse driving conditions
* Exporting ELD log sheets as PDF
* Multi-day trip planning with driver teams
* Configurable HOS rules per driver
* Historical trip storage and reporting

---
