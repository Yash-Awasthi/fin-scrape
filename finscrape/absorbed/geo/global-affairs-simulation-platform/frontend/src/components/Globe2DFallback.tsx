import { useEffect, useRef } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import type { GlobePoint } from '../types'

const STAGE_COLORS: Record<string, string> = {
  latent: '#64748b',
  emergence: '#3b82f6',
  escalation: '#f59e0b',
  crisis: '#ef4444',
  de_escalation: '#10b981',
  resolution: '#14b8a6',
  post_crisis: '#64748b',
}

interface Props {
  points: GlobePoint[]
  onSelectPoint?: (point: GlobePoint) => void
}

export default function Globe2DFallback({ points, onSelectPoint }: Props) {
  const mapRef = useRef<HTMLDivElement>(null)
  const mapInstanceRef = useRef<L.Map | null>(null)

  useEffect(() => {
    if (!mapRef.current || mapInstanceRef.current) return

    const map = L.map(mapRef.current).setView([20, 0], 2)
    mapInstanceRef.current = map

    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; <a href="https://carto.com/">CARTO</a>',
      maxZoom: 18,
    }).addTo(map)

    return () => {
      map.remove()
      mapInstanceRef.current = null
    }
  }, [])

  useEffect(() => {
    const map = mapInstanceRef.current
    if (!map) return

    map.eachLayer(layer => {
      if (layer instanceof L.CircleMarker) map.removeLayer(layer)
    })

    points.forEach(pt => {
      if (pt.lat == null || pt.lng == null) return
      const color = STAGE_COLORS[pt.stage_of_crisis || ''] || '#6366f1'
      const marker = L.circleMarker([pt.lat, pt.lng], {
        radius: 6,
        fillColor: color,
        color: color,
        weight: 1,
        opacity: 0.8,
        fillOpacity: 0.6,
      }).addTo(map)

      marker.bindPopup(`<b>${pt.event_title || 'Event'}</b><br/>${pt.stage_of_crisis || ''}`)
      if (onSelectPoint) {
        marker.on('click', () => onSelectPoint(pt))
      }
    })
  }, [points, onSelectPoint])

  return (
    <div className="w-full h-full relative">
      <div ref={mapRef} className="w-full h-full" />
      <div className="absolute top-3 left-3 bg-surface-900/80 text-xs text-amber-400 px-3 py-1.5 rounded-lg border border-amber-500/30">
        2D 模式（WebGL 不可用）
      </div>
    </div>
  )
}
