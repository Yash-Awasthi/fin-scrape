import { useState, useRef, useEffect, useCallback } from 'react';
import { Search, MapPin, Plane, Ship, AlertTriangle, Newspaper, X, Crosshair } from 'lucide-react';
import { flyTo, flyToEntity } from '../../services/globe';
import { useAppStore } from '../../stores/appStore';

interface SearchResult {
  id: string;
  label: string;
  sublabel: string;
  type: 'city' | 'coordinate' | 'aircraft' | 'ship' | 'earthquake' | 'conflict' | 'news' | 'satellite';
  lat: number;
  lng: number;
  zoomAlt?: number;
}

const CITIES: { name: string; country: string; lat: number; lng: number }[] = [
  { name: 'New York', country: 'United States', lat: 40.7128, lng: -74.006 },
  { name: 'London', country: 'United Kingdom', lat: 51.5074, lng: -0.1278 },
  { name: 'Paris', country: 'France', lat: 48.8566, lng: 2.3522 },
  { name: 'Tokyo', country: 'Japan', lat: 35.6762, lng: 139.6503 },
  { name: 'Dubai', country: 'UAE', lat: 25.2048, lng: 55.2708 },
  { name: 'Singapore', country: 'Singapore', lat: 1.3521, lng: 103.8198 },
  { name: 'Sydney', country: 'Australia', lat: -33.8688, lng: 151.2093 },
  { name: 'Moscow', country: 'Russia', lat: 55.7558, lng: 37.6173 },
  { name: 'Beijing', country: 'China', lat: 39.9042, lng: 116.4074 },
  { name: 'Mumbai', country: 'India', lat: 19.076, lng: 72.8777 },
  { name: 'Cairo', country: 'Egypt', lat: 30.0444, lng: 31.2357 },
  { name: 'São Paulo', country: 'Brazil', lat: -23.5505, lng: -46.6333 },
  { name: 'Los Angeles', country: 'United States', lat: 34.0522, lng: -118.2437 },
  { name: 'Berlin', country: 'Germany', lat: 52.52, lng: 13.405 },
  { name: 'Istanbul', country: 'Turkey', lat: 41.0082, lng: 28.9784 },
  { name: 'Seoul', country: 'South Korea', lat: 37.5665, lng: 126.978 },
  { name: 'Mexico City', country: 'Mexico', lat: 19.4326, lng: -99.1332 },
  { name: 'Bangkok', country: 'Thailand', lat: 13.7563, lng: 100.5018 },
  { name: 'Toronto', country: 'Canada', lat: 43.6532, lng: -79.3832 },
  { name: 'Riyadh', country: 'Saudi Arabia', lat: 24.7136, lng: 46.6753 },
  { name: 'Lagos', country: 'Nigeria', lat: 6.5244, lng: 3.3792 },
  { name: 'Johannesburg', country: 'South Africa', lat: -26.2041, lng: 28.0473 },
  { name: 'Buenos Aires', country: 'Argentina', lat: -34.6037, lng: -58.3816 },
  { name: 'Nairobi', country: 'Kenya', lat: -1.2921, lng: 36.8219 },
  { name: 'Jakarta', country: 'Indonesia', lat: -6.2088, lng: 106.8456 },
  { name: 'Washington DC', country: 'United States', lat: 38.9072, lng: -77.0369 },
  { name: 'Chicago', country: 'United States', lat: 41.8781, lng: -87.6298 },
  { name: 'San Francisco', country: 'United States', lat: 37.7749, lng: -122.4194 },
  { name: 'Hong Kong', country: 'China', lat: 22.3193, lng: 114.1694 },
  { name: 'Taipei', country: 'Taiwan', lat: 25.033, lng: 121.5654 },
  { name: 'Manila', country: 'Philippines', lat: 14.5995, lng: 120.9842 },
  { name: 'Tehran', country: 'Iran', lat: 35.6892, lng: 51.389 },
  { name: 'Baghdad', country: 'Iraq', lat: 33.3152, lng: 44.3661 },
  { name: 'Kyiv', country: 'Ukraine', lat: 50.4501, lng: 30.5234 },
  { name: 'Ankara', country: 'Turkey', lat: 39.9334, lng: 32.8597 },
  { name: 'Rome', country: 'Italy', lat: 41.9028, lng: 12.4964 },
  { name: 'Madrid', country: 'Spain', lat: 40.4168, lng: -3.7038 },
  { name: 'Amsterdam', country: 'Netherlands', lat: 52.3676, lng: 4.9041 },
  { name: 'Doha', country: 'Qatar', lat: 25.2854, lng: 51.531 },
  { name: 'Tel Aviv', country: 'Israel', lat: 32.0853, lng: 34.7818 },
  { name: 'Kabul', country: 'Afghanistan', lat: 34.5553, lng: 69.2075 },
  { name: 'Khartoum', country: 'Sudan', lat: 15.5007, lng: 32.5599 },
  { name: 'Mogadishu', country: 'Somalia', lat: 2.0469, lng: 45.3182 },
  { name: 'Pyongyang', country: 'North Korea', lat: 39.0392, lng: 125.7625 },
  { name: 'Havana', country: 'Cuba', lat: 23.1136, lng: -82.3666 },
  { name: 'Caracas', country: 'Venezuela', lat: 10.4806, lng: -66.9036 },
];

function parseCoordinates(query: string): { lat: number; lng: number } | null {
  const cleaned = query.trim();

  // "40.71, -74.01" or "40.71 -74.01"
  const match = cleaned.match(/^(-?\d+\.?\d*)[,\s]+(-?\d+\.?\d*)$/);
  if (match) {
    const lat = parseFloat(match[1]);
    const lng = parseFloat(match[2]);
    if (lat >= -90 && lat <= 90 && lng >= -180 && lng <= 180) {
      return { lat, lng };
    }
  }

  // DMS: "40°42'N 74°00'W"
  const dms = cleaned.match(/(\d+)[°]\s*(\d+)?[']?\s*([NS])[,\s]+(\d+)[°]\s*(\d+)?[']?\s*([EW])/i);
  if (dms) {
    let lat = parseInt(dms[1]) + (parseInt(dms[2] || '0') / 60);
    let lng = parseInt(dms[4]) + (parseInt(dms[5] || '0') / 60);
    if (dms[3].toUpperCase() === 'S') lat = -lat;
    if (dms[6].toUpperCase() === 'W') lng = -lng;
    if (lat >= -90 && lat <= 90 && lng >= -180 && lng <= 180) {
      return { lat, lng };
    }
  }

  return null;
}

let searchTimeout: ReturnType<typeof setTimeout> | null = null;

export function SearchBar() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [selectedIdx, setSelectedIdx] = useState(-1);
  const [isLoading, setIsLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);

  const layers = useAppStore((s) => s.layers);

  const searchLocal = useCallback((q: string): SearchResult[] => {
    const lower = q.toLowerCase();
    const out: SearchResult[] = [];

    // Coordinate match
    const coords = parseCoordinates(q);
    if (coords) {
      out.push({
        id: `coord-${coords.lat}-${coords.lng}`,
        label: `${coords.lat.toFixed(4)}, ${coords.lng.toFixed(4)}`,
        sublabel: 'Coordinates',
        type: 'coordinate',
        lat: coords.lat,
        lng: coords.lng,
        zoomAlt: 500_000,
      });
    }

    // City matches
    for (const city of CITIES) {
      if (city.name.toLowerCase().includes(lower) || city.country.toLowerCase().includes(lower)) {
        out.push({
          id: `city-${city.name}`,
          label: city.name,
          sublabel: city.country,
          type: 'city',
          lat: city.lat,
          lng: city.lng,
          zoomAlt: 300_000,
        });
      }
      if (out.length > 6) break;
    }

    // Aircraft matches from live data
    for (const ac of layers.aircraft.slice(0, 2000)) {
      if (ac.callsign?.toLowerCase().includes(lower) || ac.icao24?.toLowerCase().includes(lower)) {
        out.push({
          id: `ac-${ac.icao24}`,
          label: ac.callsign || ac.icao24,
          sublabel: `${ac.originCountry} · ${ac.category} · ${Math.round(ac.position.alt ?? 0)}m`,
          type: 'aircraft',
          lat: ac.position.lat,
          lng: ac.position.lng,
          zoomAlt: 200_000,
        });
      }
      if (out.length > 12) break;
    }

    // Ship matches
    for (const ship of layers.ships) {
      if (ship.name?.toLowerCase().includes(lower) || ship.mmsi?.includes(q)) {
        out.push({
          id: `ship-${ship.mmsi}`,
          label: ship.name,
          sublabel: `${ship.shipType} · ${ship.flag}`,
          type: 'ship',
          lat: ship.position.lat,
          lng: ship.position.lng,
          zoomAlt: 200_000,
        });
      }
      if (out.length > 15) break;
    }

    // Earthquake matches
    for (const eq of layers.earthquakes) {
      if (eq.place?.toLowerCase().includes(lower)) {
        out.push({
          id: `eq-${eq.id}`,
          label: `M${eq.magnitude.toFixed(1)} ${eq.place}`,
          sublabel: `Depth: ${eq.depth.toFixed(0)}km · ${new Date(eq.time).toLocaleString()}`,
          type: 'earthquake',
          lat: eq.position.lat,
          lng: eq.position.lng,
          zoomAlt: 500_000,
        });
      }
      if (out.length > 18) break;
    }

    // Conflict matches
    for (const ev of layers.conflicts) {
      if (ev.country?.toLowerCase().includes(lower) || ev.region?.toLowerCase().includes(lower) || ev.description?.toLowerCase().includes(lower)) {
        out.push({
          id: `conf-${ev.id}`,
          label: `${ev.country} — ${ev.region}`,
          sublabel: ev.eventType.replace(/_/g, ' '),
          type: 'conflict',
          lat: ev.position.lat,
          lng: ev.position.lng,
          zoomAlt: 500_000,
        });
      }
      if (out.length > 20) break;
    }

    // Satellite matches
    for (const sat of layers.satellites) {
      if (sat.name?.toLowerCase().includes(lower)) {
        out.push({
          id: `sat-${sat.id}`,
          label: sat.name,
          sublabel: `${sat.category} · ${sat.orbitType} · ${Math.round(sat.position.alt ?? 0)}km`,
          type: 'satellite',
          lat: sat.position.lat,
          lng: sat.position.lng,
          zoomAlt: 5_000_000,
        });
      }
      if (out.length > 22) break;
    }

    return out.slice(0, 15);
  }, [layers]);

  const handleSearch = useCallback((q: string) => {
    setQuery(q);
    setSelectedIdx(-1);

    if (!q.trim()) {
      setResults([]);
      setIsOpen(false);
      return;
    }

    const localResults = searchLocal(q);
    setResults(localResults);
    setIsOpen(localResults.length > 0);

    // Also search backend for more results (debounced)
    if (searchTimeout) clearTimeout(searchTimeout);
    if (q.length >= 2) {
      setIsLoading(true);
      searchTimeout = setTimeout(async () => {
        try {
          const resp = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
          if (resp.ok) {
            const data = await resp.json();
            if (data.results?.length) {
              const apiResults: SearchResult[] = data.results.slice(0, 10).map((r: any, i: number) => {
                const item = r.item;
                const pos = item.position || item.launchSite || { lat: 0, lng: 0 };
                return {
                  id: `api-${r.type}-${i}`,
                  label: item.callsign || item.name || item.title || item.place || item.description?.slice(0, 50) || 'Unknown',
                  sublabel: r.type,
                  type: r.type as SearchResult['type'],
                  lat: pos.lat ?? 0,
                  lng: pos.lng ?? 0,
                  zoomAlt: 500_000,
                };
              }).filter((r: SearchResult) => r.lat !== 0 || r.lng !== 0);

              setResults((prev) => {
                const existingIds = new Set(prev.map((p) => p.label.toLowerCase()));
                const newOnes = apiResults.filter((r: SearchResult) => !existingIds.has(r.label.toLowerCase()));
                return [...prev, ...newOnes].slice(0, 15);
              });
              setIsOpen(true);
            }
          }
        } catch { /* ignore */ }
        setIsLoading(false);
      }, 300);
    }
  }, [searchLocal]);

  const handleSelect = useCallback((result: SearchResult) => {
    setQuery(result.label);
    setIsOpen(false);

    if (result.type === 'coordinate') {
      flyTo(result.lat, result.lng, result.zoomAlt);
    } else {
      flyToEntity(result.lat, result.lng, result.zoomAlt);
    }
  }, []);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (!isOpen) return;

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIdx((prev) => Math.min(prev + 1, results.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIdx((prev) => Math.max(prev - 1, -1));
    } else if (e.key === 'Enter' && selectedIdx >= 0) {
      e.preventDefault();
      handleSelect(results[selectedIdx]);
    } else if (e.key === 'Escape') {
      setIsOpen(false);
    }
  }, [isOpen, results, selectedIdx, handleSelect]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const typeIcon = (type: SearchResult['type']) => {
    switch (type) {
      case 'city': return <MapPin size={12} />;
      case 'coordinate': return <Crosshair size={12} />;
      case 'aircraft': return <Plane size={12} />;
      case 'ship': return <Ship size={12} />;
      case 'earthquake': return <AlertTriangle size={12} />;
      case 'conflict': return <AlertTriangle size={12} />;
      case 'news': return <Newspaper size={12} />;
      default: return <MapPin size={12} />;
    }
  };

  const typeColor = (type: SearchResult['type']) => {
    switch (type) {
      case 'city': return 'var(--primary)';
      case 'coordinate': return 'var(--secondary)';
      case 'aircraft': return '#00aaff';
      case 'ship': return '#00cccc';
      case 'earthquake': return '#ff6644';
      case 'conflict': return '#ff4444';
      case 'news': return '#ffaa00';
      case 'satellite': return '#aa88ff';
      default: return 'var(--text-secondary)';
    }
  };

  return (
    <div ref={panelRef} style={{ position: 'relative', flex: 1, maxWidth: 420 }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          background: 'rgba(0,0,0,0.3)',
          border: `1px solid ${isOpen ? 'var(--secondary)' : 'var(--border)'}`,
          borderRadius: isOpen ? '6px 6px 0 0' : 6,
          padding: '4px 12px',
          transition: 'border-color 0.2s',
        }}
      >
        <Search size={14} color={isOpen ? 'var(--secondary)' : 'var(--text-secondary)'} />
        <input
          ref={inputRef}
          type="text"
          placeholder="Search city, coordinates, flight, ship, satellite..."
          value={query}
          onChange={(e) => handleSearch(e.target.value)}
          onFocus={() => { if (results.length > 0) setIsOpen(true); }}
          onKeyDown={handleKeyDown}
          style={{
            flex: 1,
            background: 'transparent',
            border: 'none',
            outline: 'none',
            color: 'var(--text-primary)',
            fontSize: 12,
            fontFamily: 'inherit',
          }}
        />
        {isLoading && (
          <div style={{
            width: 12, height: 12,
            border: '2px solid var(--border)',
            borderTopColor: 'var(--secondary)',
            borderRadius: '50%',
            animation: 'spin 0.6s linear infinite',
          }} />
        )}
        {query && (
          <button
            onClick={() => { setQuery(''); setResults([]); setIsOpen(false); }}
            style={{
              background: 'none', border: 'none', cursor: 'pointer',
              color: 'var(--text-secondary)', display: 'flex', padding: 2,
            }}
          >
            <X size={12} />
          </button>
        )}
      </div>

      {isOpen && results.length > 0 && (
        <div
          style={{
            position: 'absolute',
            top: '100%',
            left: 0,
            right: 0,
            background: 'var(--bg-surface)',
            border: '1px solid var(--secondary)',
            borderTop: 'none',
            borderRadius: '0 0 6px 6px',
            maxHeight: 360,
            overflowY: 'auto',
            zIndex: 200,
          }}
        >
          {results.map((r, i) => (
            <div
              key={r.id}
              onClick={() => handleSelect(r)}
              onMouseEnter={() => setSelectedIdx(i)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                padding: '8px 14px',
                cursor: 'pointer',
                background: i === selectedIdx ? 'rgba(0, 170, 255, 0.1)' : 'transparent',
                borderBottom: '1px solid rgba(0,170,255,0.06)',
                transition: 'background 0.1s',
              }}
            >
              <div style={{ color: typeColor(r.type), flexShrink: 0 }}>
                {typeIcon(r.type)}
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{
                  fontSize: 12,
                  color: 'var(--text-primary)',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                }}>
                  {r.label}
                </div>
                <div style={{
                  fontSize: 10,
                  color: 'var(--text-secondary)',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                }}>
                  {r.sublabel}
                </div>
              </div>
              <div
                className="mono"
                style={{
                  fontSize: 9,
                  color: typeColor(r.type),
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                  flexShrink: 0,
                  opacity: 0.7,
                }}
              >
                {r.type}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
