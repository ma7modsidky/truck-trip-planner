import { useState } from 'react'
import { LocationInput } from './LocationInput'
import { planTrip, PlanTripError } from '../api/planTrip'
import type { Location, TripPlanResponse } from '../types/api'

interface Props {
  onPlan: (plan: TripPlanResponse) => void
}

export function TripForm({ onPlan }: Props) {
  const [current, setCurrent] = useState<Location | null>(null)
  const [pickup, setPickup] = useState<Location | null>(null)
  const [dropoff, setDropoff] = useState<Location | null>(null)
  const [cycleHours, setCycleHours] = useState<number>(0)

  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const canSubmit =
    current !== null &&
    pickup !== null &&
    dropoff !== null &&
    cycleHours >= 0 &&
    cycleHours <= 70 &&
    !submitting

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!canSubmit || !current || !pickup || !dropoff) return

    setSubmitting(true)
    setError(null)

    try {
      const plan = await planTrip({
        current_location: current,
        pickup_location: pickup,
        dropoff_location: dropoff,
        current_cycle_used_hours: cycleHours,
      })
      onPlan(plan)
    } catch (err) {
      if (err instanceof PlanTripError) {
        setError(describeError(err))
      } else {
        setError('Unexpected error. Check the console for details.')
        console.error(err)
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-5 rounded-lg border border-slate-200 bg-white p-6 shadow-sm"
    >
      <div className="space-y-3">
        <LocationInput
          label="Current location"
          value={current}
          onChange={setCurrent}
          placeholder="Where is the driver now?"
          allowGeolocation
        />
        <LocationInput
          label="Pickup location"
          value={pickup}
          onChange={setPickup}
          placeholder="Where is the load picked up?"
          allowGeolocation
        />
        <LocationInput
          label="Dropoff location"
          value={dropoff}
          onChange={setDropoff}
          placeholder="Where is the load delivered?"
          allowGeolocation
        />
      </div>

      <div>
        <label className="mb-1 block text-sm font-medium text-slate-700">
          Current cycle used (hours)
        </label>
        <input
          type="number"
          min={0}
          max={70}
          step={0.5}
          value={cycleHours}
          onChange={(e) => setCycleHours(parseFloat(e.target.value) || 0)}
          className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm
                     shadow-sm outline-none focus:border-slate-500 focus:ring-1
                     focus:ring-slate-500"
        />
        <p className="mt-1 text-xs text-slate-500">
          How many hours of the 70-hour cycle the driver has already used.
        </p>
      </div>

      {error && (
        <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-800">
          {error}
        </div>
      )}

      <button
        type="submit"
        disabled={!canSubmit}
        className="w-full rounded-md bg-slate-900 px-4 py-2.5 text-sm font-medium
                   text-white shadow-sm transition hover:bg-slate-800
                   disabled:cursor-not-allowed disabled:bg-slate-400"
      >
        {submitting ? 'Planning trip…' : 'Plan trip'}
      </button>
    </form>
  )
}

function describeError(err: PlanTripError): string {
  if (err.payload.error === 'routing_failed') {
    return "We couldn't find a driving route between those locations. Check that all three are reachable by road."
  }
  if (err.payload.error === 'trip_impossible') {
    return (
      err.payload.detail ??
      'This trip cannot be completed under Hours of Service rules.'
    )
  }
  if (err.status === 400) {
    // DRF field errors
    const messages = Object.entries(err.payload)
      .flatMap(([field, value]) =>
        Array.isArray(value) ? value.map((v) => `${field}: ${v}`) : [],
      )
    if (messages.length > 0) return messages.join('\n')
  }
  return err.message || 'Something went wrong.'
}