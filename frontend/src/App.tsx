import { useState } from 'react'
import { TripForm } from './components/TripForm'
import { MapView } from './components/MapView'
import type { TripPlanResponse } from './types/api'
import { LogSheet } from './components/LogSheet'
import { StopList } from './components/StopList'

function App() {
  const [plan, setPlan] = useState<TripPlanResponse | null>(null)

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-6xl px-6 py-4">
          <h1 className="text-xl font-semibold">Truck Trip Planner</h1>
          <p className="text-sm text-slate-500">
            Plan a trip, generate the route and the ELD log sheets.
          </p>
        </div>
      </header>

      <main className="mx-auto max-w-6xl space-y-8 px-6 py-8">
        <div className="grid gap-8 lg:grid-cols-[380px_1fr]">
          <TripForm onPlan={setPlan} />

          <div>
            {plan ? (
              <MapView plan={plan} />
            ) : (
              <div className="flex h-[500px] items-center justify-center rounded-lg border border-dashed border-slate-300 bg-white text-slate-400">
                Submit a trip to see the route.
              </div>
            )}
          </div>
        </div>

        {plan && (
          <section>
            <h2 className="mb-4 text-lg font-semibold">Trip summary</h2>
            <div className="grid gap-4 sm:grid-cols-3">
              <SummaryCard
                label="Total distance"
                value={`${plan.route.total_distance_miles.toFixed(0)} mi`}
              />
              <SummaryCard
                label="Total drive time"
                value={`${plan.route.total_duration_hours.toFixed(1)} h`}
              />
              <SummaryCard
                label="Log sheets"
                value={`${plan.days.length}`}
              />
            </div>
          </section>
        )}
        {plan && (
          <section className="space-y-6">
            <div className="flex items-baseline justify-between">
              <h2 className="text-lg font-semibold">Daily log sheets</h2>
              <span className="text-sm text-slate-500">
                {plan.days.length} {plan.days.length === 1 ? 'day' : 'days'}
              </span>
            </div>
            {plan && (
                <section>
                  <h3 className="mb-4 text-lg font-semibold">Stops</h3>
                  <StopList events={plan.events} />
                </section>
              )}
            <div className="space-y-6">
              {plan.days.map((day, i) => (
                <LogSheet
                  key={day.date}
                  day={day}
                  dayNumber={i + 1}
                  totalDays={plan.days.length}
                />
              ))}
            </div>
          </section>
        )}
      </main>
    </div>
  )
}

function SummaryCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="text-xs uppercase tracking-wide text-slate-500">
        {label}
      </div>
      <div className="mt-1 text-2xl font-semibold">{value}</div>
    </div>
  )
}

export default App