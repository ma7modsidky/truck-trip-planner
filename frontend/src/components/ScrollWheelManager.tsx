import { useEffect } from 'react'
import { useMap } from 'react-leaflet'


export function ScrollWheelManager() {
  const map = useMap()

  useEffect(() => {
    map.scrollWheelZoom.disable()

    const container = map.getContainer()

    const onWheel = (e: WheelEvent) => {
      if (e.ctrlKey || e.metaKey) {
        e.preventDefault()

        const delta = -Math.sign(e.deltaY)  // up = zoom in, down = zoom out
        const newZoom = map.getZoom() + delta
        const latlng = map.mouseEventToLatLng(e)

        map.setZoomAround(latlng, newZoom)
      }
    }

    const onMouseLeave = () => {
      // Nothing to do; scrollWheelZoom stays disabled.
    }

    container.addEventListener('wheel', onWheel, { passive: false })
    container.addEventListener('mouseleave', onMouseLeave)

    return () => {
      container.removeEventListener('wheel', onWheel)
      container.removeEventListener('mouseleave', onMouseLeave)
    }
  }, [map])

  return null
}