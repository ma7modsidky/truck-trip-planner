# Frontend — Truck Trip Planner

React + TypeScript SPA for the Truck Trip Planner.

The frontend submits a trip request to the backend and renders:

* A **map** showing the route and all stops.
* A **summary** showing distance, drive time, and number of log sheets.
* A **stop list** showing every pickup, dropoff, fuel, break, and rest event.
* One **ELD daily log sheet** per day of the trip, drawn as SVG.

---

## Stack

| Layer      | Choice                                        |
| ---------- | --------------------------------------------- |
| Framework  | React 18 + TypeScript                         |
| Build tool | Vite                                          |
| Styling    | Tailwind CSS v4                               |
| Map        | Leaflet + react-leaflet (OpenStreetMap tiles) |
| Geocoding  | Nominatim (OpenStreetMap)                     |

No state library, router, or UI kit is used.

The application is small enough that plain React `useState` and Tailwind CSS cover the current requirements.

---

## Project Layout

```text
frontend/
├── src/
│   ├── api/
│   │   └── planTrip.ts              # Typed fetch client + PlanTripError
│   ├── components/
│   │   ├── LocationInput.tsx        # Geocoding autocomplete
│   │   ├── TripForm.tsx             # Trip input form
│   │   ├── MapView.tsx              # Route polyline + stop markers
│   │   ├── StopList.tsx             # Table of stops
│   │   └── LogSheet.tsx             # One SVG ELD sheet per day
│   ├── types/
│   │   └── api.ts                   # Mirrored backend types
│   ├── App.tsx                      # Page composition
│   ├── main.tsx
│   └── index.css                    # Tailwind entry
├── .env                             # VITE_API_BASE_URL
├── vite.config.ts
└── package.json
```

---

## Setup

```bash
npm install

cp .env.example .env

npm run dev
```

The development server runs at:

`http://localhost:5173`

The backend must also be running. See [`../backend/README.md`](../backend/README.md).

The backend's CORS settings must include the frontend origin.

### Environment Variables

| Variable            | Purpose                     | Default                 |
| ------------------- | --------------------------- | ----------------------- |
| `VITE_API_BASE_URL` | Base URL of the backend API | `http://127.0.0.1:8000` |

Vite only exposes environment variables prefixed with `VITE_` to the browser.

---

## How It Works

### 1. Trip Input

`TripForm` collects:

* Current location
* Pickup location
* Dropoff location
* Current cycle usage

The location fields use `LocationInput` to provide geocoding autocomplete through Nominatim.

### 2. API Request

The `planTrip` function sends the trip request to:

```text
POST /api/plan-trip/
```

The backend calculates the route and generates the complete HOS schedule.

### 3. Rendering the Trip

`App` receives the `TripPlanResponse` and renders three main pieces of information.

#### MapView

`MapView`:

* Draws the concatenated route geometry as a polyline.
* Displays markers at the leg endpoints.
* Displays markers for every located stop.
* Shows the complete trip visually.

#### StopList

`StopList` displays a table containing every non-driving event, including:

* Pickup
* Dropoff
* Fuel
* Break
* Rest

Each stop includes its time, type, location, and duration.

#### LogSheet

`LogSheet` renders one ELD log sheet for each day of the trip.

Each sheet is an SVG representation of the FMCSA-style daily log and includes:

* 24-hour time ruler
* Four duty-status rows
* Event segments
* Vertical connectors between status changes
* Remarks
* Per-day totals

---

## Datetimes

All datetimes returned by the backend are ISO 8601 values containing timezone information.

The backend currently uses UTC as the canonical timezone, and the UI displays dates and times in UTC to match.

If local-time display is required in the future, conversion should happen at the presentation boundary, primarily in:

* `LogSheet.tsx`
* `StopList.tsx`

Keeping the API/domain representation in UTC avoids timezone ambiguity between the backend and frontend.

---

## Geocoding

`LocationInput` uses Nominatim from OpenStreetMap for address/place lookup.

The implementation:

* Debounces requests by 350 ms.
* Displays the top 5 results.
* Requires no API key.

Nominatim is free to use but has a usage policy, including rate limits and requirements around identifying the application with a valid User-Agent.

For production traffic, geocoding requests should be proxied through the backend or another appropriate geocoding service rather than relying directly on the public Nominatim service from the browser.

---

## The ELD Log Sheet

`LogSheet.tsx` draws a fixed `1200 × 420` SVG.

### Timeline Positioning

The x-axis is calculated relative to the day's midnight (`dayStart`) rather than simply reading the hour component from each timestamp.

This is important for events that span midnight.

For example, an event ending exactly at the next day's midnight should be positioned at the **right edge** of the current day's chart rather than being interpreted as hour `00:00` at the left edge.

### Full-Day Coverage

Gaps at the beginning and end of the day are padded with synthetic `OFF_DUTY` events.

This ensures that the chart always covers the complete 24-hour period.

Synthetic padding is not included in the remarks displayed to the user.

### Duty Status Connectors

Vertical connectors are drawn whenever the duty status changes.

This keeps the ELD graph visually continuous and represents transitions between:

* `OFF_DUTY`
* `SLEEPER`
* `DRIVING`
* `ON_DUTY`

### Daily Totals

The recap totals are calculated from the padded events.

As a result, the four duty-status categories sum to a complete 24-hour day.

---

## Building for Production

```bash
npm run build
```

The production build is generated in:

```text
dist/
```

The output is a static bundle and can be deployed to any suitable static hosting provider.

### Vercel

Vercel works with the project using the following configuration:

1. Connect the repository.
2. Set the project root directory to `frontend`.
3. Set `VITE_API_BASE_URL` to the deployed backend URL.
4. Build the project with `npm run build`.

---

## Scripts

| Command           | Purpose                                   |
| ----------------- | ----------------------------------------- |
| `npm run dev`     | Start the development server with HMR     |
| `npm run build`   | Type-check and produce a production build |
| `npm run preview` | Serve the production build locally        |
| `npm run lint`    | Run ESLint over `src/`                    |

---

## Related Documentation

* [`../README.md`](../README.md) — Full-stack project overview
* [`../backend/README.md`](../backend/README.md) — Backend architecture and HOS business rules
* [`../backend/API.md`](../backend/API.md) — Backend API reference

---
