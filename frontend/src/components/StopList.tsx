import type { Activity, ScheduleEvent } from '../types/api'

interface Props {
  events: ScheduleEvent[]
}

const STOP_ACTIVITIES: Activity[] = [
  'PICKUP',
  'DROPOFF',
  'FUEL',
  'BREAK',
  'REST',
]

const ACTIVITY_LABEL: Record<Activity, string> = {
  PICKUP: 'Pickup',
  DROPOFF: 'Dropoff',
  FUEL: 'Fuel stop',
  BREAK: 'Break',
  REST: 'Rest (10h)',
  DRIVING: 'Driving',
}

const ACTIVITY_STYLE: Record<Activity, string> = {
  PICKUP: 'bg-green-50 text-green-800 ring-green-200',
  DROPOFF: 'bg-red-50 text-red-800 ring-red-200',
  FUEL: 'bg-amber-50 text-amber-800 ring-amber-200',
  BREAK: 'bg-cyan-50 text-cyan-800 ring-cyan-200',
  REST: 'bg-violet-50 text-violet-800 ring-violet-200',
  DRIVING: 'bg-slate-50 text-slate-700 ring-slate-200',
}

function formatTime(iso: string): string {
  const d = new Date(iso)
  const hh = String(d.getUTCHours()).padStart(2, '0')
  const mm = String(d.getUTCMinutes()).padStart(2, '0')
  return `${hh}:${mm}`
}

function formatDate(iso: string): string {
  return iso.slice(0, 10)
}

function formatDuration(minutes: number): string {
  const h = Math.floor(minutes / 60)
  const m = Math.round(minutes % 60)
  if (h === 0) return `${m}m`
  if (m === 0) return `${h}h`
  return `${h}h ${m}m`
}

export function StopList({ events }: Props) {
  const stops = events.filter((e) =>
    STOP_ACTIVITIES.includes(e.activity),
  )

  if (stops.length === 0) {
    return (
      <div className="rounded-lg border border-slate-200 bg-white p-6 text-sm text-slate-500 shadow-sm">
        No stops on this trip.
      </div>
    )
  }

  return (
    <div className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
      <table className="w-full text-sm">
        <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
          <tr>
            <th className="px-4 py-3 font-medium">When</th>
            <th className="px-4 py-3 font-medium">Type</th>
            <th className="px-4 py-3 font-medium">Location</th>
            <th className="px-4 py-3 font-medium">Duration</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {stops.map((stop, i) => (
            <tr key={i} className="hover:bg-slate-50">
              <td className="px-4 py-3 text-slate-700">
                <div className="font-medium">{formatTime(stop.start)}</div>
                <div className="text-xs text-slate-500">
                  {formatDate(stop.start)}
                </div>
              </td>
              <td className="px-4 py-3">
                <span
                  className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${
                    ACTIVITY_STYLE[stop.activity]
                  }`}
                >
                  {ACTIVITY_LABEL[stop.activity]}
                </span>
              </td>
              <td className="px-4 py-3 text-slate-700">
                {stop.location?.name ?? (
                  <span className="text-slate-400">En route</span>
                )}
              </td>
              <td className="px-4 py-3 text-slate-700">
                {formatDuration(stop.duration_minutes)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}