import { useCallback, useState } from 'react'

interface Coordinates {
  latitude: number
  longitude: number
}

interface UseGeolocationResult {
  loading: boolean
  error: string | null
  request: () => Promise<Coordinates | null>
}

export function useGeolocation(): UseGeolocationResult {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const request = useCallback(async (): Promise<Coordinates | null> => {
    if (!('geolocation' in navigator)) {
      setError('Geolocation is not supported by this browser.')
      return null
    }

    setLoading(true)
    setError(null)

    return new Promise((resolve) => {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setLoading(false)
          resolve({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
          })
        },
        (err) => {
          setLoading(false)
          let message = 'Could not get your location.'
          if (err.code === err.PERMISSION_DENIED) {
            message = 'Location permission denied.'
          } else if (err.code === err.POSITION_UNAVAILABLE) {
            message = 'Location unavailable.'
          } else if (err.code === err.TIMEOUT) {
            message = 'Location request timed out.'
          }
          setError(message)
          resolve(null)
        },
        {
          enableHighAccuracy: false,
          timeout: 10000,
          maximumAge: 60000,
        },
      )
    })
  }, [])

  return { loading, error, request }
}