export interface Location {
  name: string
  latitude: number
  longitude: number
}

export interface RouteLeg {
  origin: Location
  destination: Location
  distance_miles: number
  duration_hours: number
}

export interface RouteResponse {
  legs: RouteLeg[]
  total_distance_miles: number
  total_duration_hours: number
}

export type DutyStatus = 'OFF_DUTY' | 'SLEEPER' | 'DRIVING' | 'ON_DUTY'

export type Activity =
  | 'DRIVING'
  | 'PICKUP'
  | 'DROPOFF'
  | 'FUEL'
  | 'BREAK'
  | 'REST'

export interface ScheduleEvent {
  start: string        // ISO 8601
  end: string          // ISO 8601
  status: DutyStatus
  activity: Activity
  location: Location | null
  distance_miles: number
  duration_minutes: number
}

export interface DayTotals {
  off_duty_hours: number
  sleeper_hours: number
  driving_hours: number
  on_duty_hours: number
  total_miles: number
}

export interface DayPlan {
  date: string         // "YYYY-MM-DD"
  events: ScheduleEvent[]
  totals: DayTotals
}

export interface TripPlanResponse {
  route: RouteResponse
  events: ScheduleEvent[]
  days: DayPlan[]
}

export interface TripRequestInput {
  current_location: Location
  pickup_location: Location
  dropoff_location: Location
  current_cycle_used_hours: number
  start_time?: string
}

export interface ApiError {
  error?: string
  detail?: string
  [field: string]: unknown
}

export interface RouteLeg {
  origin: Location
  destination: Location
  distance_miles: number
  duration_hours: number
  geometry: [number, number][]   // [lat, lng] pairs
}