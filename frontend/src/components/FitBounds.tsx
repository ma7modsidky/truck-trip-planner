import { useEffect } from 'react'
import { useMap } from 'react-leaflet'
import L from 'leaflet'
export function FitBounds({
  positions,
}: {
  positions: [number, number][]
}) {
  const map = useMap()

  useEffect(() => {
    if (positions.length === 0) return

    const bounds = L.latLngBounds(positions)
    map.fitBounds(bounds, { padding: [40, 40] })
  }, [map, positions])

  return null
}