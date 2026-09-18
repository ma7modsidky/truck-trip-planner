import { MapContainer, TileLayer, Polyline, Marker, Popup } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

import type { ScheduleEvent, TripPlanResponse } from '../types/api'

interface Props {
  plan: TripPlanResponse
}

// Leaflet's default marker icons reference images by URL. With Vite's
// bundler, those URLs don't resolve. We replace them with a CDN URL.
const defaultIcon = L.icon({
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
})

function stopColor(activity: ScheduleEvent['activity']): string {
  switch (activity) {
    case 'PICKUP':  return '#16a34a'  // green
    case 'DROPOFF': return '#dc2626'  // red
    case 'FUEL':    return '#ca8a04'  // amber
    case 'BREAK':   return '#0891b2'  // cyan
    case 'REST':    return '#7c3aed'  // violet
    default:        return '#64748b'  // slate
  }
}

function stopLabel(event: ScheduleEvent): string {
  const place = event.location?.name ?? 'En route'
  return `${event.activity} · ${place}`
}

export function MapView({ plan }: Props) {
  // Concatenate all leg geometries into one polyline for visual continuity.
  const fullRoute: [number, number][] = plan.route.legs.flatMap(
    (leg) => leg.geometry,
  )

  // Collect every event that has a location and is not a plain
  // driving event. Those are the stops we want to show.
  const stops = plan.events.filter(
    (e) => e.location !== null && e.activity !== 'DRIVING',
  )

  // Also mark the endpoints of each leg, so the map shows current,
  // pickup, and dropoff even if the itinerary has no explicit event
  // with those locations.
  const startPoint = fullRoute[0]
  const endPoint = fullRoute[fullRoute.length - 1]

  const center: [number, number] =
    fullRoute.length > 0 ? fullRoute[Math.floor(fullRoute.length / 2)] : [39.5, -98.35]

  return (
    <div className="h-[500px] w-full overflow-hidden rounded-lg border border-slate-200">
      <MapContainer
        center={center}
        zoom={5}
        scrollWheelZoom
        style={{ height: '100%', width: '100%' }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {fullRoute.length > 1 && (
          <Polyline
            positions={fullRoute}
            pathOptions={{ color: '#0f172a', weight: 4, opacity: 0.85 }}
          />
        )}

        {startPoint && (
          <Marker position={startPoint} icon={defaultIcon}>
            <Popup>Start · {plan.route.legs[0].origin.name}</Popup>
          </Marker>
        )}

        {stops.map((stop, i) => (
          <Marker
            key={i}
            position={[stop.location!.latitude, stop.location!.longitude]}
            icon={defaultIcon}
          >
            <Popup>
              <div className="text-xs">
                <div className="font-semibold">{stopLabel(stop)}</div>
                <div className="text-slate-500">
                  {new Date(stop.start).toLocaleString()}
                </div>
              </div>
            </Popup>
          </Marker>
        ))}

        {endPoint && (
          <Marker position={endPoint} icon={defaultIcon}>
            <Popup>
              End ·{' '}
              {plan.route.legs[plan.route.legs.length - 1].destination.name}
            </Popup>
          </Marker>
        )}
      </MapContainer>
    </div>
  )
}