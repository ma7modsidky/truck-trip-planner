import { MapContainer, TileLayer, Polyline, Marker, Popup } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
// import L from 'leaflet'
import type { DivIcon } from 'leaflet'
import type { Location,ScheduleEvent, TripPlanResponse } from '../types/api'
import { ScrollWheelManager } from './ScrollWheelManager'
import { FitBounds } from './FitBounds'
import { currentIcon, pickupIcon, dropoffIcon, stopIcon, combinedIcon} from './markerIcons'

interface Props {
  plan: TripPlanResponse
}

// ---- helpers ----
function stopLabel(event: ScheduleEvent): string {
  const place = event.location?.name ?? 'En route'
  return `${event.activity} · ${place}`
}

type KeyMarker = {
  key: string
  position: [number, number]
  icon: DivIcon
  title: string
  subtitle: string
}

function samePoint(a: Location, b: Location): boolean {
  return (
    Math.abs(a.latitude - b.latitude) < 1e-4 &&
    Math.abs(a.longitude - b.longitude) < 1e-4
  )
}

type Role = 'A' | 'B' | 'C'   // A=Current, B=Pickup, C=Dropoff

interface PointGroup {
  position: [number, number]
  roles: Role[]
  names: string[]   // the human-readable names to show in the popup
}

function buildKeyMarkers(plan: TripPlanResponse): KeyMarker[] {
  const start = plan.route.legs[0].origin
  const pickup = plan.route.legs[0].destination
  const dropoff = plan.route.legs[1].destination

  const points: { role: Role; location: Location }[] = [
    { role: 'A', location: start },
    { role: 'B', location: pickup },
    { role: 'C', location: dropoff },
  ]

  // Group by coordinate proximity.
  const groups: PointGroup[] = []

  for (const point of points) {
    // Find an existing group within tolerance.
    const existing = groups.find((g) =>
      samePoint(
        {
          name: '',
          latitude: g.position[0],
          longitude: g.position[1],
        },
        point.location,
      ),
    )

    if (existing) {
      existing.roles.push(point.role)
      if (!existing.names.includes(point.location.name)) {
        existing.names.push(point.location.name)
      }
    } else {
      groups.push({
        position: [point.location.latitude, point.location.longitude],
        roles: [point.role],
        names: [point.location.name],
      })
    }
  }

  // Convert each group to a KeyMarker with the right icon and label.
  return groups.map((group) => {
    const roleLabel = group.roles.join('/')   // "A", "A/B", "A/B/C"
    const title = titleForRoles(group.roles)
    const subtitle = group.names.join(' · ')

    const icon =
      group.roles.length === 1
        ? singleRoleIcon(group.roles[0])
        : combinedIcon(colorForRoles(group.roles), roleLabel)

    return {
      key: roleLabel,
      position: group.position,
      icon,
      title,
      subtitle,
    }
  })
}

function singleRoleIcon(role: Role): DivIcon {
  switch (role) {
    case 'A': return currentIcon
    case 'B': return pickupIcon
    case 'C': return dropoffIcon
  }
}

function colorForRoles(roles: Role[]): string {
  // If A is in the group, use the current-location color.
  // Otherwise use the pickup color.
  if (roles.includes('A')) return '#0ea5e9'
  if (roles.includes('B')) return '#16a34a'
  return '#dc2626'
}

function titleForRoles(roles: Role[]): string {
  if (roles.length === 1) {
    return (
      roles[0] === 'A' ? 'Current location' :
      roles[0] === 'B' ? 'Pickup' :
      'Dropoff'
    )
  }
  // Combined
  if (roles.length === 3) return 'Current + Pickup + Dropoff'
  if (roles.includes('A') && roles.includes('B')) return 'Current + Pickup'
  if (roles.includes('A') && roles.includes('C')) return 'Current + Dropoff'
  return 'Pickup + Dropoff'
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



  const leg0 = plan.route.legs[0].geometry
  const leg1 = plan.route.legs[1].geometry
  const allPositions = [...leg0, ...leg1]



  const keyMarkers = buildKeyMarkers(plan)
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
        {keyMarkers.map((m) => (
          <Marker key={m.key} position={m.position} icon={m.icon}>
            <Popup>
              <div className="text-xs">
                <div className="font-semibold">{m.title}</div>
                <div>{m.subtitle}</div>
              </div>
            </Popup>
          </Marker>
        ))}

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