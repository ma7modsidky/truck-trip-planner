import { useEffect, useRef, useState } from 'react'
import type { Location } from '../types/api'

interface Suggestion {
  name: string
  latitude: number
  longitude: number
}

interface Props {
  label: string
  value: Location | null
  onChange: (loc: Location | null) => void
  placeholder?: string
}

const NOMINATIM_URL = 'https://nominatim.openstreetmap.org/search'

function useDebounced<T>(value: T, delayMs: number): T {
  const [debounced, setDebounced] = useState(value)

  useEffect(() => {
    const id = setTimeout(() => setDebounced(value), delayMs)
    return () => clearTimeout(id)
  }, [value, delayMs])

  return debounced
}

export function LocationInput({ label, value, onChange, placeholder }: Props) {
  const [query, setQuery] = useState(value?.name ?? '')
  const [suggestions, setSuggestions] = useState<Suggestion[]>([])
  const [open, setOpen] = useState(false)
  const debouncedQuery = useDebounced(query, 350)
  const skipNextFetch = useRef(false)

  useEffect(() => {
    // When the parent sets a value (e.g., the user picked a suggestion),
    // don't re-fetch suggestions for the same text.
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

    fetch(
      `${NOMINATIM_URL}?q=${encodeURIComponent(debouncedQuery)}&format=json&limit=5&addressdetails=1`,
      { signal: controller.signal, headers: { 'Accept-Language': 'en' } },
    )
      .then((r) => r.json())
      .then((results: Array<{ display_name: string; lat: string; lon: string }>) => {
        setSuggestions(
          results.map((r) => ({
            name: r.display_name,
            latitude: parseFloat(r.lat),
            longitude: parseFloat(r.lon),
          })),
        )
        setOpen(true)
      })
      .catch((err) => {
        if (err.name !== 'AbortError') console.error(err)
      })

    return () => controller.abort()
  }, [debouncedQuery])

  function handleSelect(s: Suggestion) {
    onChange({ name: s.name, latitude: s.latitude, longitude: s.longitude })
    setQuery(s.name)
    setSuggestions([])
    setOpen(false)
  }

  function handleClear() {
    onChange(null)
    setQuery('')
    setSuggestions([])
    setOpen(false)
  }

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
          className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm
                     shadow-sm outline-none focus:border-slate-500 focus:ring-1
                     focus:ring-slate-500"
        />
        {value && (
          <button
            type="button"
            onClick={handleClear}
            className="rounded-md border border-slate-300 px-2 py-1 text-xs
                       text-slate-600 hover:bg-slate-100"
          >
            Clear
          </button>
        )}
      </div>

      {open && suggestions.length > 0 && (
        <ul
          className="absolute z-10 mt-1 max-h-64 w-full overflow-auto rounded-md
                     border border-slate-200 bg-white shadow-lg"
        >
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
    </div>
  )
}