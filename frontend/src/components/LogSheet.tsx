import type { DayPlan, DutyStatus, ScheduleEvent } from '../types/api'

const ROW_ORDER: DutyStatus[] = ['OFF_DUTY', 'SLEEPER', 'DRIVING', 'ON_DUTY']

const ROW_LABELS: Record<DutyStatus, string> = {
  OFF_DUTY: '1. Off Duty',
  SLEEPER: '2. Sleeper Berth',
  DRIVING: '3. Driving',
  ON_DUTY: '4. On Duty (not driving)',
}

const VIEWBOX_WIDTH = 1200
const VIEWBOX_HEIGHT = 420

const GRID_LEFT = 170
const GRID_RIGHT = 1160
const GRID_TOP = 110
const GRID_WIDTH = GRID_RIGHT - GRID_LEFT
const HOUR_WIDTH = GRID_WIDTH / 24
const ROW_HEIGHT = 36

function rowY(status: DutyStatus): number {
  const index = ROW_ORDER.indexOf(status)
  return GRID_TOP + index * ROW_HEIGHT
}

function timeToX(date: Date, dayStart: Date): number {
  const minutes = (date.getTime() - dayStart.getTime()) / 60000
  return GRID_LEFT + (minutes / 60) * HOUR_WIDTH
}

/**
 * Fill gaps at the start and end of the day with synthetic OFF_DUTY
 * events so the chart always covers the full 24 hours.
 */
function fillGaps(events: ScheduleEvent[], dayStart: Date): ScheduleEvent[] {
  const dayEnd = new Date(dayStart.getTime() + 24 * 3600 * 1000)
  const sorted = [...events].sort(
    (a, b) => new Date(a.start).getTime() - new Date(b.start).getTime(),
  )

  const result: ScheduleEvent[] = []
  let cursor = dayStart

  function synthetic(start: Date, end: Date): ScheduleEvent {
    return {
      start: start.toISOString(),
      end: end.toISOString(),
      status: 'OFF_DUTY',
      activity: 'REST',
      location: null,
      distance_miles: 0,
      duration_minutes: (end.getTime() - start.getTime()) / 60000,
    }
  }

  for (const event of sorted) {
    const start = new Date(event.start)
    if (start > cursor) result.push(synthetic(cursor, start))
    result.push(event)
    cursor = new Date(event.end)
  }

  if (cursor < dayEnd) result.push(synthetic(cursor, dayEnd))

  return result
}

function computeTotals(events: ScheduleEvent[]) {
  const totals = {
    off_duty_hours: 0,
    sleeper_hours: 0,
    driving_hours: 0,
    on_duty_hours: 0,
    total_miles: 0,
  }
  for (const e of events) {
    const hours = e.duration_minutes / 60
    if (e.status === 'OFF_DUTY') totals.off_duty_hours += hours
    else if (e.status === 'SLEEPER') totals.sleeper_hours += hours
    else if (e.status === 'DRIVING') totals.driving_hours += hours
    else if (e.status === 'ON_DUTY') totals.on_duty_hours += hours
    totals.total_miles += e.distance_miles
  }
  return totals
}

function HourRuler() {
  const labels: React.ReactNode[] = []
  const lines: React.ReactNode[] = []

  for (let h = 0; h <= 24; h++) {
    const x = GRID_LEFT + h * HOUR_WIDTH
    const isNoon = h === 12
    const isMajor = h === 0 || h === 12 || h === 24

    lines.push(
      <line
        key={`line-${h}`}
        x1={x}
        y1={GRID_TOP}
        x2={x}
        y2={GRID_TOP + ROW_HEIGHT * 4}
        stroke={isNoon ? '#475569' : '#cbd5e1'}
        strokeWidth={isNoon ? 1.2 : 0.5}
      />,
    )

    if (h < 24) {
      const label =
        h === 0 ? 'Mid' : h === 12 ? 'Noon' : String(h > 12 ? h - 12 : h)
      labels.push(
        <text
          key={`label-${h}`}
          x={x + HOUR_WIDTH / 2}
          y={GRID_TOP - 8}
          textAnchor="middle"
          fontSize={isMajor ? 11 : 10}
          fontWeight={isMajor ? 600 : 400}
          fill="#334155"
        >
          {label}
        </text>,
      )
    }
  }

  return (
    <>
      {lines}
      {labels}
    </>
  )
}

function EventSegments({
  events,
  dayStart,
}: {
  events: ScheduleEvent[]
  dayStart: Date
}) {
  const segments: React.ReactNode[] = []
  const connectors: React.ReactNode[] = []

  const sorted = [...events].sort(
    (a, b) => new Date(a.start).getTime() - new Date(b.start).getTime(),
  )

  let prevStatus: DutyStatus | null = null

  sorted.forEach((event, i) => {
    const start = new Date(event.start)
    const end = new Date(event.end)

    const x1 = timeToX(start, dayStart)
    const x2 = timeToX(end, dayStart)
    const y = rowY(event.status)

    segments.push(
      <line
        key={`seg-${i}`}
        x1={x1}
        y1={y}
        x2={x2}
        y2={y}
        stroke="#0f172a"
        strokeWidth={2.5}
        strokeLinecap="round"
      />,
    )

    if (prevStatus !== null && prevStatus !== event.status) {
      const prevY = rowY(prevStatus)
      connectors.push(
        <line
          key={`conn-${i}`}
          x1={x1}
          y1={prevY}
          x2={x1}
          y2={y}
          stroke="#0f172a"
          strokeWidth={2.5}
          strokeLinecap="round"
        />,
      )
    }

    prevStatus = event.status
  })

  return (
    <>
      {connectors}
      {segments}
    </>
  )
}

interface HeaderProps {
  day: DayPlan
  dayNumber: number
  totalDays: number
}

function Header({ day, dayNumber, totalDays }: HeaderProps) {
  const date = new Date(day.date + 'T00:00:00Z')
  const { from, to } = dayEndpoints(day.events)
  return (
    <g>
      <text x={40} y={30} fontSize={15} fontWeight={700} fill="#0f172a">
        Driver's Daily Log
      </text>
      <text x={40} y={48} fontSize={11} fill="#64748b">
        Day {dayNumber} of {totalDays}
      </text>

      <text x={340} y={30} fontSize={12} fill="#0f172a">
        Date: {date.toISOString().slice(0, 10)}
      </text>
      <text x={560} y={30} fontSize={12} fill="#0f172a">
        Total miles today: {day.totals.total_miles.toFixed(1)}
      </text>

      <text x={340} y={48} fontSize={11} fill="#64748b">
        From: {from ?? '—'}
      </text>
      <text x={560} y={48} fontSize={11} fill="#64748b">
        To: {to ?? '—'}
      </text>
    </g>
  )
}

function Remarks({ events }: { events: ScheduleEvent[] }) {
  const noteworthy = events.filter(
    (e, i) =>
      i === 0 ||
      e.status !== events[i - 1].status ||
      e.activity !== 'DRIVING',
  )

  const rows: React.ReactNode[] = []
  const maxRows = 6
  const rowHeight = 15
  const headerY = GRID_TOP + ROW_HEIGHT * 4 + 32
  const firstRowY = headerY + 16

  noteworthy.slice(0, maxRows).forEach((event, i) => {
    const start = new Date(event.start)
    const time = `${String(start.getUTCHours()).padStart(2, '0')}:${String(
      start.getUTCMinutes(),
    ).padStart(2, '0')}`

    const where = event.location?.name ?? '—'
    const label = `${time} · ${where} · ${event.activity}`

    rows.push(
      <text
        key={i}
        x={40}
        y={firstRowY + i * rowHeight}
        fontSize={10}
        fill="#334155"
      >
        {label}
      </text>,
    )
  })

  return (
    <g>
      <text x={40} y={headerY} fontSize={11} fontWeight={600} fill="#0f172a">
        Remarks
      </text>
      {rows}
    </g>
  )
}

function Recap({ totals }: { totals: ReturnType<typeof computeTotals> }) {
  const headerY = GRID_TOP + ROW_HEIGHT * 4 + 32
  const firstRowY = headerY + 16
  const x0 = 900
  const xValue = 1140

  const rows: [string, number][] = [
    ['Off Duty', totals.off_duty_hours],
    ['Sleeper', totals.sleeper_hours],
    ['Driving', totals.driving_hours],
    ['On Duty (ND)', totals.on_duty_hours],
  ]

  return (
    <g>
      <text x={x0} y={headerY} fontSize={11} fontWeight={600} fill="#0f172a">
        Today's totals
      </text>

      {rows.map(([label, value], i) => (
        <g key={label}>
          <text
            x={x0}
            y={firstRowY + i * 15}
            fontSize={10}
            fill="#475569"
          >
            {label}
          </text>
          <text
            x={xValue}
            y={firstRowY + i * 15}
            fontSize={10}
            fontWeight={500}
            fill="#0f172a"
            textAnchor="end"
          >
            {value.toFixed(1)} h
          </text>
        </g>
      ))}

      <line
        x1={x0}
        y1={firstRowY + rows.length * 15 + 2}
        x2={xValue}
        y2={firstRowY + rows.length * 15 + 2}
        stroke="#e2e8f0"
        strokeWidth={0.5}
      />
      <text
        x={x0}
        y={firstRowY + rows.length * 15 + 18}
        fontSize={10}
        fontWeight={600}
        fill="#0f172a"
      >
        Total
      </text>
      <text
        x={xValue}
        y={firstRowY + rows.length * 15 + 18}
        fontSize={10}
        fontWeight={600}
        fill="#0f172a"
        textAnchor="end"
      >
        {(
          totals.off_duty_hours +
          totals.sleeper_hours +
          totals.driving_hours +
          totals.on_duty_hours
        ).toFixed(1)}{' '}
        h
      </text>
    </g>
  )
}

interface Props {
  day: DayPlan
  dayNumber: number
  totalDays: number
}

export function LogSheet({ day, dayNumber, totalDays }: Props) {
  const dayStart = new Date(`${day.date}T00:00:00Z`)
  const filledEvents = fillGaps(day.events, dayStart)
  const totals = computeTotals(filledEvents)

  return (
    <div className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
      <svg
        viewBox={`0 0 ${VIEWBOX_WIDTH} ${VIEWBOX_HEIGHT}`}
        className="h-auto w-full"
        xmlns="http://www.w3.org/2000/svg"
      >
        <Header day={day} dayNumber={dayNumber} totalDays={totalDays} />

        <HourRuler />

        {/* Row background lines */}
        {ROW_ORDER.map((status) => (
          <line
            key={status}
            x1={GRID_LEFT}
            y1={rowY(status)}
            x2={GRID_RIGHT}
            y2={rowY(status)}
            stroke="#e2e8f0"
            strokeWidth={0.5}
          />
        ))}

        {/* Row labels */}
        {ROW_ORDER.map((status) => (
          <text
            key={status}
            x={GRID_LEFT - 12}
            y={rowY(status) + 4}
            fontSize={11}
            fill="#334155"
            textAnchor="end"
          >
            {ROW_LABELS[status]}
          </text>
        ))}

        <EventSegments events={filledEvents} dayStart={dayStart} />

        <Remarks events={day.events} />

        <Recap totals={totals} />
      </svg>
    </div>
  )
}

function dayEndpoints(events: ScheduleEvent[]): { from: string | null; to: string | null } {
  const located = events.filter((e) => e.location !== null)
  if (located.length === 0) return { from: null, to: null }
  return {
    from: located[0].location!.name,
    to: located[located.length - 1].location!.name,
  }
}