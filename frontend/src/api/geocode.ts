const NOMINATIM_REVERSE = 'https://nominatim.openstreetmap.org/reverse'
const NOMINATIM_SEARCH = 'https://nominatim.openstreetmap.org/search'

export interface GeocodeResult {
  name: string
  latitude: number
  longitude: number
}

export async function reverseGeocode(
  latitude: number,
  longitude: number,
  signal?: AbortSignal,
): Promise<GeocodeResult | null> {
  const url = `${NOMINATIM_REVERSE}?lat=${latitude}&lon=${longitude}&format=json`
  const res = await fetch(url, {
    signal,
    headers: { 'Accept-Language': 'en' },
  })
  if (!res.ok) return null
  const data = await res.json()
  if (!data.display_name) return null
  return {
    name: data.display_name,
    latitude,
    longitude,
  }
}

export async function searchPlaces(
  query: string,
  signal?: AbortSignal,
): Promise<GeocodeResult[]> {
  const url = `${NOMINATIM_SEARCH}?q=${encodeURIComponent(
    query,
  )}&format=json&limit=5&addressdetails=1`
  const res = await fetch(url, {
    signal,
    headers: { 'Accept-Language': 'en' },
  })
  if (!res.ok) return []
  const results = await res.json()
  return results.map(
    (r: { display_name: string; lat: string; lon: string }) => ({
      name: r.display_name,
      latitude: parseFloat(r.lat),
      longitude: parseFloat(r.lon),
    }),
  )
}