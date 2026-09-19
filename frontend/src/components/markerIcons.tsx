import L from 'leaflet'

function makeMarkerIcon(color: string, label: string) {
  const size = 32
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 44" width="${size}" height="${size * 44 / 32}">
      <path d="M16 0C7.16 0 0 7.16 0 16c0 11 16 28 16 28s16-17 16-28C32 7.16 24.84 0 16 0z"
            fill="${color}" stroke="white" stroke-width="2"/>
      <circle cx="16" cy="16" r="7" fill="white"/>
      ${label ? `<text x="16" y="20" text-anchor="middle" font-size="10" font-weight="600" fill="${color}">${label}</text>` : ''}
    </svg>
  `

  return L.divIcon({
    html: svg,
    className: '',  // clear Leaflet's default divIcon styles
    iconSize: [size, size * 44 / 32],
    iconAnchor: [size / 2, size * 44 / 32],
    popupAnchor: [0, -size * 44 / 32],
  })
}
export const combinedIcon = (color: string, label: string) => {
  const size = 32
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 44" width="${size}" height="${size * 44 / 32}">
      <path d="M16 0C7.16 0 0 7.16 0 16c0 11 16 28 16 28s16-17 16-28C32 7.16 24.84 0 16 0z"
            fill="${color}" stroke="white" stroke-width="2"/>
      <circle cx="16" cy="16" r="8" fill="white"/>
      <text x="16" y="20" text-anchor="middle" font-size="9" font-weight="700" fill="${color}">${label}</text>
    </svg>
  `
  return L.divIcon({
    html: svg,
    className: '',
    iconSize: [size, size * 44 / 32],
    iconAnchor: [size / 2, size * 44 / 32],
    popupAnchor: [0, -size * 44 / 32],
  })
}
export const currentIcon  = makeMarkerIcon('#0ea5e9', 'A')   // sky blue
export const pickupIcon   = makeMarkerIcon('#16a34a', 'B')   // green
export const dropoffIcon  = makeMarkerIcon('#dc2626', 'C')   // red
export const stopIcon     = makeMarkerIcon('#64748b', '')    // slate, small