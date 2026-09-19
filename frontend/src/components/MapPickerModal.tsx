import { useEffect, useState } from 'react'
import { MapContainer, TileLayer, Marker, useMapEvents } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

import { reverseGeocode } from '../api/geocode'
import type { Location } from '../types/api'
import { createPortal } from 'react-dom'
import { ScrollWheelManager } from './ScrollWheelManager'
interface Props {
  title: string
  initialCenter: [number, number]
  onSelect: (loc: Location) => void
  onClose: () => void
}

const pickIcon = L.icon({
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
})

function ClickHandler({
  onPick,
}: {
  onPick: (lat: number, lng: number) => void
}) {
  useMapEvents({
    click(e) {
      onPick(e.latlng.lat, e.latlng.lng)
    },
  })
  return null
}

export function MapPickerModal({
  title,
  initialCenter,
  onSelect,
  onClose,
}: Props) {
  const [picked, setPicked] = useState<{ lat: number; lng: number } | null>(null)
  const [name, setName] = useState<string | null>(null)
  const [resolving, setResolving] = useState(false)

  // Reverse-geocode when the marker moves, debounced.
  useEffect(() => {
    if (!picked) return

    const controller = new AbortController()
    const id = setTimeout(async () => {
      setResolving(true)
      try {
        const result = await reverseGeocode(picked.lat, picked.lng, controller.signal)
        if (result) setName(result.name)
      } finally {
        setResolving(false)
      }
    }, 500)

    return () => {
      clearTimeout(id)
      controller.abort()
    }
  }, [picked])

  function confirm() {
    if (!picked) return
    onSelect({
      name: name ?? `${picked.lat.toFixed(4)}, ${picked.lng.toFixed(4)}`,
      latitude: picked.lat,
      longitude: picked.lng,
    })
    onClose()
  }

  return createPortal(
    <div className="fixed inset-0 z-[1100] flex items-center justify-center bg-slate-900/50 p-4">
      <div className="flex h-[80vh] w-full max-w-4xl flex-col overflow-hidden rounded-lg bg-white shadow-xl">
        <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3">
          <h2 className="text-sm font-semibold text-slate-900">{title}</h2>
          <button
            type="button"
            onClick={onClose}
            className="rounded p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
          >
            ✕
          </button>
        </div>

        <div className="flex-1">
                  
          <MapContainer
            center={initialCenter}
            zoom={10}
            scrollWheelZoom
            style={{ height: '100%', width: '100%' }}
          > 
          <div className="pointer-events-none absolute bottom-2 left-2 z-[500] rounded bg-white/85 px-2 py-1 text-xs text-slate-600 shadow-sm">
        Hold ⌘/Ctrl + scroll to zoom
      </div>
            <ScrollWheelManager />
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            <ClickHandler onPick={(lat, lng) => setPicked({ lat, lng })} />
            {picked && (
              <Marker position={[picked.lat, picked.lng]} icon={pickIcon} />
            )}
          </MapContainer>
        </div>

        <div className="border-t border-slate-200 px-4 py-3">
          <div className="mb-3 text-xs text-slate-500">
            {picked ? (
              resolving ? (
                'Looking up the address…'
              ) : (
                name ?? `${picked.lat.toFixed(4)}, ${picked.lng.toFixed(4)}`
              )
            ) : (
              'Click anywhere on the map to pick a location.'
            )}
          </div>
          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-md border border-slate-300 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50"
            >
              Cancel
            </button>
            <button
              type="button"
              disabled={!picked}
              onClick={confirm}
              className="rounded-md bg-slate-900 px-3 py-1.5 text-sm text-white hover:bg-slate-800 disabled:bg-slate-400"
            >
              Use this location
            </button>
          </div>
        </div>
      </div>
    </div>,document.body
  )
}

