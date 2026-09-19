import { MapContainer, TileLayer, Polyline, Marker, Popup } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'

import type { ScheduleEvent, TripPlanResponse } from '../types/api'
import { ScrollWheelManager } from './ScrollWheelManager'
import { FitBounds } from './FitBounds'
import { currentIcon, pickupIcon, dropoffIcon, stopIcon } from './markerIcons'

interface Props {
  plan: TripPlanResponse
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
  (e) =>
    e.location !== null &&
    (e.activity === 'FUEL' || e.activity === 'BREAK' || e.activity === 'REST'),
  )

  const center: [number, number] =
  fullRoute.length > 0 ? fullRoute[Math.floor(fullRoute.length / 2)] : [39.5, -98.35]
  // The three key locations from the route itself.
  const startLocation = plan.route.legs[0].origin
  const pickupLocation = plan.route.legs[0].destination
  const dropoffLocation = plan.route.legs[1].destination

  const leg0 = plan.route.legs[0].geometry
  const leg1 = plan.route.legs[1].geometry
  const allPositions = [...leg0, ...leg1]
  return (
      <div className="h-[500px] w-full overflow-hidden rounded-lg border border-slate-200">
        
      <MapContainer
        center={center}
        zoom={5}
        scrollWheelZoom
        style={{ height: '100%', width: '100%' }}
      >
        <div className="pointer-events-none absolute bottom-2 left-2 z-[500] rounded bg-white/85 px-2 py-1 text-xs text-slate-600 shadow-sm">
        Hold ⌘/Ctrl + scroll to zoom
        </div>
        <ScrollWheelManager />
        <FitBounds positions={allPositions} />
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {fullRoute.length > 1 && (
          <>
          <Polyline positions={leg0} pathOptions={{ color: '#0f172a', weight: 4, opacity: 0.85 }} />
          <Polyline positions={leg1} pathOptions={{ color: '#0f172a', weight: 4, opacity: 0.85, dashArray: '8 6' }} />
          </>
        )}
        {/* Markers for the three key locations. */}
        <Marker position={[startLocation.latitude, startLocation.longitude]} icon={currentIcon}>
          <Popup>
            <div className="text-xs">
              <div className="font-semibold">Current location</div>
              <div>{startLocation.name}</div>
            </div>
          </Popup>
        </Marker>

        <Marker position={[pickupLocation.latitude, pickupLocation.longitude]} icon={pickupIcon}>
          <Popup>
            <div className="text-xs">
              <div className="font-semibold">Pickup</div>
              <div>{pickupLocation.name}</div>
            </div>
          </Popup>
        </Marker>

        <Marker position={[dropoffLocation.latitude, dropoffLocation.longitude]} icon={dropoffIcon}>
          <Popup>
            <div className="text-xs">
              <div className="font-semibold">Dropoff</div>
              <div>{dropoffLocation.name}</div>
            </div>
          </Popup>
        </Marker>

        {/* Secondary stops with a smaller, neutral marker. */}
        {stops.map((stop, i) => (
          <Marker
            key={i}
            position={[stop.location!.latitude, stop.location!.longitude]}
            icon={stopIcon}
          >
            <Popup>{stopLabel(stop)}</Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  )
}