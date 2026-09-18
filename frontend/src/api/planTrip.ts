import type { TripPlanResponse, TripRequestInput, ApiError } from '../types/api'

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

export class PlanTripError extends Error {
  readonly status: number
  readonly payload: ApiError

  constructor(status: number, payload: ApiError) {
    super(payload.detail ?? `Request failed with status ${status}`)
    this.status = status
    this.payload = payload
  }
}

export async function planTrip(
  input: TripRequestInput,
): Promise<TripPlanResponse> {
  const response = await fetch(`${API_BASE_URL}/api/plan-trip/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })

  const payload = await response.json()

  if (!response.ok) {
    throw new PlanTripError(response.status, payload as ApiError)
  }

  return payload as TripPlanResponse
}