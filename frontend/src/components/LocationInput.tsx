import { useEffect, useRef, useState } from 'react'
import type { Location } from '../types/api'
import { searchPlaces, reverseGeocode } from '../api/geocode'
import { MapPickerModal } from './MapPickerModal'
import { useGeolocation } from '../hooks/useGeolocation'
import { MapPin, LocateFixed } from 'lucide-react'


interface Props {
  label: string
  value: Location | null
  onChange: (loc: Location | null) => void
  placeholder?: string
  allowMapPick?: boolean
  allowGeolocation?: boolean
}


function useDebounced<T>(value: T, delayMs: number): T {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const id = setTimeout(() => setDebounced(value), delayMs)
    return () => clearTimeout(id)
  }, [value, delayMs])
  return debounced
}

export function LocationInput({
  label,
  value,
  onChange,
  placeholder,
  allowMapPick = true,
  allowGeolocation = false,
}: Props) {
  const [query, setQuery] = useState(value?.name ?? '')
  const [suggestions, setSuggestions] = useState<Location[]>([])
  const [open, setOpen] = useState(false)
  const [showMap, setShowMap] = useState(false)
  const [locating, setLocating] = useState(false)
  const debouncedQuery = useDebounced(query, 350)
  const skipNextFetch = useRef(false)
  const geolocation = useGeolocation()

  useEffect(() => {
    if (value && value.name === query) {
      skipNextFetch.current = true
    }
  }, [value, query])

  useEffect(() => {
    if (skipNextFetch.current) {
      skipNextFetch.current = false
      return
    }
    if (debouncedQuery.length < 3) {
      setSuggestions([])
      return
    }
    const controller = new AbortController()
    searchPlaces(debouncedQuery, controller.signal)
      .then((results) => {
        setSuggestions(results)
        setOpen(true)
      })
      .catch((err) => {
        if (err.name !== 'AbortError') console.error(err)
      })
    return () => controller.abort()
  }, [debouncedQuery])

  function handleSelect(loc: Location) {
    onChange(loc)
    setQuery(loc.name)
    setSuggestions([])
    setOpen(false)
  }

  function handleClear() {
    onChange(null)
    setQuery('')
    setSuggestions([])
    setOpen(false)
  }

  async function handleUseMyLocation() {
    setLocating(true)
    const coords = await geolocation.request()
    if (coords) {
      const named = await reverseGeocode(coords.latitude, coords.longitude)
      if (named) {
        handleSelect(named)
      } else {
        handleSelect({
          name: `${coords.latitude.toFixed(4)}, ${coords.longitude.toFixed(4)}`,
          latitude: coords.latitude,
          longitude: coords.longitude,
        })
      }
    }
    setLocating(false)
  }

  // Default map center: user's current value, or a wide view.
  const mapCenter: [number, number] = value
    ? [value.latitude, value.longitude]
    : [30.04, 31.24]  // Cairo — could be replaced with something better

  return (
    <div className="relative">
      <label className="mb-1 block text-sm font-medium text-slate-700">
        {label}
      </label>
      <div className="flex items-center gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value)
            onChange(null)
          }}
          onFocus={() => suggestions.length > 0 && setOpen(true)}
          placeholder={placeholder}
          className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm shadow-sm outline-none focus:border-slate-500 focus:ring-1 focus:ring-slate-500"
        />

        {allowMapPick && (
          <button
            type="button"
            title="Pick on map"
            onClick={() => setShowMap(true)}
            className="rounded-md border border-slate-300 px-2 py-1.5 text-xs text-slate-600 hover:bg-slate-100"
          >
            <MapPin className="h-4 w-4" />
          </button>
        )}

        {allowGeolocation && (
          <button
            type="button"
            title="Use my location"
            onClick={handleUseMyLocation}
            disabled={locating}
            className="rounded-md border border-slate-300 px-2 py-1.5 text-xs text-slate-600 hover:bg-slate-100 disabled:opacity-50"
          >
            <LocateFixed className="h-4 w-4" />
          </button>
        )}

        {value && (
          <button
            type="button"
            onClick={handleClear}
            className="rounded-md border border-slate-300 px-2 py-1.5 text-xs text-slate-600 hover:bg-slate-100"
          >
            Clear
          </button>
        )}
      </div>

      {geolocation.error && allowGeolocation && (
        <p className="mt-1 text-xs text-red-600">{geolocation.error}</p>
      )}

      {open && suggestions.length > 0 && (
        <ul className="absolute z-10 mt-1 max-h-64 w-full overflow-auto rounded-md border border-slate-200 bg-white shadow-lg">
          {suggestions.map((s, i) => (
            <li key={i}>
              <button
                type="button"
                onClick={() => handleSelect(s)}
                className="w-full px-3 py-2 text-left text-sm hover:bg-slate-50"
              >
                {s.name}
              </button>
            </li>
          ))}
        </ul>
      )}

      {showMap && (
        <MapPickerModal
          title={`Pick ${label.toLowerCase()}`}
          initialCenter={mapCenter}
          onSelect={handleSelect}
          onClose={() => setShowMap(false)}
        />
      )}
    </div>
  )
}