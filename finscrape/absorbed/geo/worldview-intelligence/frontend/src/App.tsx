import { useEffect, useMemo, useState } from 'react';
import {
  Layers, ChevronLeft, ChevronRight, Shield, AlertTriangle,
  Play, Pause, Eye, Crosshair, Radar, Monitor, Moon,
  Flame, Plane, Satellite, Ship, Activity, Navigation, X,
} from 'lucide-react';
import { useAppStore } from './stores/appStore';
import { connectWebSocket, disconnectWebSocket } from './services/websocket';
import { GlobeView } from './components/Globe/GlobeView';
import { SearchBar } from './components/SearchBar/SearchBar';
import { LandingPage } from './components/LandingPage/LandingPage';
import { flyToEntity } from './services/globe';
import type { VisualMode, LayerData } from './types';

const MODES: { mode: VisualMode; label: string; icon: typeof Eye }[] = [
  { mode: 'tactical', label: 'TAC', icon: Crosshair },
  { mode: 'satellite', label: 'SAT', icon: Monitor },
  { mode: 'nightVision', label: 'NVG', icon: Moon },
  { mode: 'thermal', label: 'THR', icon: Flame },
  { mode: 'radar', label: 'RAD', icon: Radar },
];

const LAYER_CFG: { key: keyof LayerData; label: string; color: string }[] = [
  { key: 'aircraft', label: 'Aircraft', color: '#00b8f0' },
  { key: 'satellites', label: 'Satellites', color: '#8066ff' },
  { key: 'ships', label: 'Ships', color: '#00c5b0' },
  { key: 'earthquakes', label: 'Earthquakes', color: '#f07030' },
  { key: 'conflicts', label: 'War Zones', color: '#ff3b5c' },
  { key: 'missiles', label: 'Missiles', color: '#e02060' },
  { key: 'news', label: 'News Intel', color: '#f0a030' },
  { key: 'traffic', label: 'Traffic', color: '#70c040' },
  { key: 'weather', label: 'Weather', color: '#50b0e0' },
];

function useClockTick() {
  const [t, setT] = useState(Date.now());
  useEffect(() => {
    const id = setInterval(() => setT(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);
  return t;
}

export default function App() {
  const [showLanding, setShowLanding] = useState(true);
  const store = useAppStore();
  const now = useClockTick();
  const [hoveredLayer, setHoveredLayer] = useState<string | null>(null);

  useEffect(() => {
    connectWebSocket();
    return () => disconnectWebSocket();
  }, []);

  const counts = useMemo(() => {
    const c: Record<string, number> = {};
    let total = 0;
    for (const key of Object.keys(store.layers) as (keyof LayerData)[]) {
      c[key] = store.layers[key].length;
      total += c[key];
    }
    c.total = total;
    c.threats = (c.conflicts ?? 0) + (c.missiles ?? 0);
    return c;
  }, [store.layers]);

  const alerts = useMemo(
    () => store.anomalies.filter(a => a.severity === 'critical' || a.severity === 'high'),
    [store.anomalies],
  );

  const utc = new Date(now).toISOString().slice(11, 19);

  if (showLanding) {
    return <LandingPage onEnter={() => setShowLanding(false)} />;
  }

  const handleFlyToEntity = () => {
    if (store.selectedEntity) {
      flyToEntity(store.selectedEntity.position.lat, store.selectedEntity.position.lng, 200_000);
    }
  };

  const handleAlertClick = (alert: typeof store.anomalies[0]) => {
    if (alert.position) {
      flyToEntity(alert.position.lat, alert.position.lng, 500_000);
    }
  };

  const handleStatClick = (layer: keyof LayerData) => {
    store.toggleLayer(layer);
  };

  const handleLayerFlyTo = (key: keyof LayerData) => {
    const items = store.layers[key];
    if (items.length === 0) return;
    const first = items[0] as any;
    const pos = first.position || first.launchSite;
    if (pos) flyToEntity(pos.lat, pos.lng, 2_000_000);
  };

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative', background: 'var(--bg-primary)' }}>
      <GlobeView />

      {/* ═══ TOP BAR ═══════════════════════════════════════════ */}
      <header style={{
        position: 'absolute', top: 0, left: 0, right: 0, height: 48,
        background: 'linear-gradient(180deg, rgba(5,8,13,0.95) 0%, rgba(5,8,13,0.85) 100%)',
        borderBottom: '1px solid var(--border)',
        display: 'flex', alignItems: 'center', gap: 16, padding: '0 16px', zIndex: 100,
      }}>
        <div style={{
          position: 'absolute', top: 0, left: 0, width: '100%', height: 1,
          background: 'linear-gradient(90deg, transparent, var(--secondary), transparent)',
          opacity: 0.35,
        }} />

        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
          <Shield size={18} color="var(--primary)" style={{ opacity: 0.9 }} />
          <span className="mono text-glow" style={{
            fontSize: 13, fontWeight: 700, letterSpacing: '0.14em', color: 'var(--primary)',
          }}>WORLDVIEW</span>
          <span className="mono" style={{ fontSize: 9, color: 'var(--text-muted)', letterSpacing: '0.1em' }}>v2.0</span>
        </div>

        <div style={{ width: 1, height: 20, background: 'var(--border)', flexShrink: 0 }} />
        <SearchBar />

        <div style={{ display: 'flex', gap: 2, marginLeft: 'auto', flexShrink: 0 }}>
          {MODES.map(({ mode, label, icon: Icon }) => (
            <button key={mode} className={`btn ${store.visualMode === mode ? 'btn-active' : ''}`}
              onClick={() => store.setVisualMode(mode)} style={{ padding: '4px 8px', fontSize: 9 }}>
              <Icon size={12} />{label}
            </button>
          ))}
        </div>

        <div style={{ width: 1, height: 20, background: 'var(--border)', flexShrink: 0 }} />

        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexShrink: 0 }}>
          {alerts.length > 0 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 4, cursor: 'pointer' }}
              onClick={store.toggleRightPanel}>
              <AlertTriangle size={13} color="var(--danger)" className="anim-pulse" />
              <span className="badge badge-critical">{alerts.length}</span>
            </div>
          )}
          <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <div style={{
              width: 5, height: 5, borderRadius: '50%', background: 'var(--primary)',
              animation: 'liveDot 2s ease-in-out infinite',
            }} />
            <span className="mono" style={{ fontSize: 9, color: 'var(--primary)', letterSpacing: '0.08em' }}>LIVE</span>
          </div>
          <span className="mono" style={{ fontSize: 10, color: 'var(--text-muted)' }}>{utc}</span>
        </div>
      </header>

      {/* ═══ LEFT PANEL ════════════════════════════════════════ */}
      {store.leftPanelOpen ? (
        <aside className="surface anim-slide-l" style={{
          position: 'absolute', top: 56, left: 8, bottom: 52, width: 240,
          display: 'flex', flexDirection: 'column', zIndex: 90, borderRadius: 4, overflow: 'hidden',
        }}>
          <div className="surface-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <Layers size={12} /><span>Layers</span>
            </div>
            <button onClick={store.toggleLeftPanel} style={{
              background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', display: 'flex', padding: 2,
            }}><ChevronLeft size={14} /></button>
          </div>

          <div style={{ flex: 1, overflowY: 'auto', padding: '6px 8px' }}>
            {LAYER_CFG.map(({ key, label, color }) => {
              const on = store.layerVisibility[key];
              const count = counts[key] ?? 0;
              const hovered = hoveredLayer === key;
              return (
                <div key={key}
                  onMouseEnter={() => setHoveredLayer(key)}
                  onMouseLeave={() => setHoveredLayer(null)}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 8, padding: '7px 8px',
                    borderRadius: 3, cursor: 'pointer', marginBottom: 1,
                    background: hovered ? 'rgba(0,184,240,0.06)' : on ? 'rgba(0,184,240,0.03)' : 'transparent',
                    borderLeft: `2px solid ${on ? color : 'transparent'}`,
                    transition: 'all 0.12s',
                  }}>
                  <div onClick={() => store.toggleLayer(key)} style={{
                    width: 7, height: 7, borderRadius: '50%',
                    background: on ? color : 'transparent',
                    border: `1.5px solid ${on ? color : 'var(--text-muted)'}`,
                    opacity: on ? 1 : 0.4, transition: 'all 0.15s', flexShrink: 0,
                  }} />
                  <span onClick={() => store.toggleLayer(key)} style={{
                    flex: 1, fontSize: 11, color: on ? 'var(--text-primary)' : 'var(--text-muted)',
                  }}>{label}</span>
                  <span className="mono" style={{
                    fontSize: 10, color: on ? color : 'var(--text-muted)', fontWeight: 600, opacity: 0.8,
                  }}>{count}</span>
                  {hovered && count > 0 && (
                    <button onClick={(e) => { e.stopPropagation(); handleLayerFlyTo(key); }}
                      title={`Fly to ${label}`}
                      style={{
                        background: 'none', border: 'none', cursor: 'pointer', display: 'flex',
                        padding: 2, color: 'var(--secondary)', opacity: 0.7,
                      }}>
                      <Navigation size={11} />
                    </button>
                  )}
                </div>
              );
            })}
          </div>

          <div style={{
            padding: '8px 14px', borderTop: '1px solid var(--border)',
            display: 'flex', justifyContent: 'space-between', fontSize: 10,
          }}>
            <span className="mono" style={{ color: 'var(--text-muted)', letterSpacing: '0.06em' }}>TRACKING</span>
            <span className="mono" style={{ color: 'var(--primary)', fontWeight: 700 }}>{counts.total}</span>
          </div>
        </aside>
      ) : (
        <button className="btn" onClick={store.toggleLeftPanel} style={{
          position: 'absolute', top: 60, left: 8, zIndex: 90, padding: '6px 5px',
        }}><ChevronRight size={14} /></button>
      )}

      {/* ═══ RIGHT PANEL ═══════════════════════════════════════ */}
      {store.rightPanelOpen && (
        <aside className="surface anim-slide-r" style={{
          position: 'absolute', top: 56, right: 8, bottom: 52, width: 320,
          display: 'flex', flexDirection: 'column', zIndex: 90, borderRadius: 4, overflow: 'hidden',
        }}>
          <div className="surface-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              {store.selectedEntity ? <Activity size={12} /> : <Eye size={12} />}
              <span>{store.selectedEntity ? 'Intel Detail' : 'Threat Feed'}</span>
            </div>
            <button onClick={store.toggleRightPanel} style={{
              background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', display: 'flex', padding: 2,
            }}><ChevronRight size={14} /></button>
          </div>

          <div style={{ flex: 1, overflowY: 'auto', padding: 10 }}>
            {store.selectedEntity ? (
              <div className="anim-fade">
                {/* Entity type + close */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                  <span className="mono" style={{
                    fontSize: 9, color: 'var(--secondary)', textTransform: 'uppercase', letterSpacing: '0.1em',
                  }}>{store.selectedEntity.type}</span>
                  <button onClick={() => store.setSelectedEntity(null)} style={{
                    background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', display: 'flex', padding: 2,
                  }}><X size={12} /></button>
                </div>

                <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 8 }}>{store.selectedEntity.id}</div>

                {/* Action buttons */}
                <div style={{ display: 'flex', gap: 6, marginBottom: 10 }}>
                  <button className="btn" onClick={handleFlyToEntity}
                    style={{ flex: 1, justifyContent: 'center', padding: '6px 10px' }}>
                    <Navigation size={12} /> Fly To
                  </button>
                </div>

                {/* Position card */}
                <div className="surface-elevated" style={{ borderRadius: 3, padding: 10, marginBottom: 10, fontSize: 11 }}>
                  <Row label="LAT" value={store.selectedEntity.position.lat.toFixed(5)} />
                  <Row label="LNG" value={store.selectedEntity.position.lng.toFixed(5)} />
                  {store.selectedEntity.position.alt != null && (
                    <Row label="ALT" value={`${store.selectedEntity.position.alt.toFixed(0)}m`} />
                  )}
                </div>

                {/* Data fields */}
                {store.selectedEntity.data && (
                  <div className="surface-elevated" style={{ borderRadius: 3, padding: 10, marginBottom: 10 }}>
                    {renderEntityFields(store.selectedEntity.type, store.selectedEntity.data)}
                  </div>
                )}

                {/* Raw JSON collapsible */}
                <details style={{ marginTop: 4 }}>
                  <summary className="mono" style={{
                    fontSize: 9, color: 'var(--text-muted)', cursor: 'pointer', letterSpacing: '0.06em',
                    padding: '4px 0',
                  }}>RAW DATA</summary>
                  <pre className="mono" style={{
                    fontSize: 9, color: 'var(--text-muted)', background: 'var(--bg-surface)',
                    border: '1px solid var(--border)', borderRadius: 3, padding: 8, marginTop: 4,
                    overflowX: 'auto', whiteSpace: 'pre-wrap', wordBreak: 'break-all', lineHeight: 1.5,
                    maxHeight: 200,
                  }}>{JSON.stringify(store.selectedEntity.data, null, 2)}</pre>
                </details>
              </div>
            ) : (
              <div>
                {store.anomalies.length === 0 && (
                  <div style={{ textAlign: 'center', color: 'var(--text-muted)', fontSize: 11, padding: 30 }}>
                    All channels nominal
                  </div>
                )}
                {store.anomalies.slice(0, 25).map(a => (
                  <div key={a.id}
                    onClick={() => handleAlertClick(a)}
                    style={{
                      padding: '8px 10px', borderRadius: 3, marginBottom: 4,
                      background: 'var(--bg-elevated)', cursor: a.position ? 'pointer' : 'default',
                      borderLeft: `2px solid ${
                        a.severity === 'critical' ? 'var(--danger)' :
                        a.severity === 'high' ? 'var(--warning)' : 'var(--secondary)'
                      }`,
                      transition: 'background 0.1s',
                    }}
                    onMouseEnter={e => { (e.currentTarget as HTMLDivElement).style.background = 'rgba(0,184,240,0.04)'; }}
                    onMouseLeave={e => { (e.currentTarget as HTMLDivElement).style.background = 'var(--bg-elevated)'; }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 3 }}>
                      <span style={{ fontSize: 11, fontWeight: 600 }}>{a.title}</span>
                      <span className={`badge badge-${a.severity}`}>{a.severity}</span>
                    </div>
                    <div style={{ fontSize: 10, color: 'var(--text-muted)', lineHeight: 1.4 }}>{a.description}</div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 4 }}>
                      <span className="mono" style={{ fontSize: 9, color: 'var(--text-muted)', opacity: 0.6 }}>
                        {new Date(a.timestamp).toLocaleTimeString()}
                      </span>
                      {a.position && (
                        <span style={{ fontSize: 9, color: 'var(--secondary)', opacity: 0.6, display: 'flex', alignItems: 'center', gap: 2 }}>
                          <Navigation size={9} /> fly to
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </aside>
      )}

      {/* ═══ BOTTOM BAR ════════════════════════════════════════ */}
      <footer style={{
        position: 'absolute', bottom: 0, left: 0, right: 0, height: 44,
        background: 'linear-gradient(0deg, rgba(5,8,13,0.95) 0%, rgba(5,8,13,0.85) 100%)',
        borderTop: '1px solid var(--border)',
        display: 'flex', alignItems: 'center', gap: 12, padding: '0 14px', zIndex: 100,
      }}>
        <button className="btn" onClick={() => store.setIsPlaying(!store.isPlaying)} style={{ padding: '3px 7px' }}>
          {store.isPlaying ? <Pause size={12} /> : <Play size={12} />}
        </button>
        <div style={{
          width: 160, height: 3, background: 'rgba(255,255,255,0.04)', borderRadius: 2,
          position: 'relative', cursor: 'pointer', flexShrink: 0,
        }} onClick={e => {
          const r = e.currentTarget.getBoundingClientRect();
          store.setTimelinePosition((e.clientX - r.left) / r.width);
        }}>
          <div style={{
            position: 'absolute', top: 0, left: 0, height: '100%', borderRadius: 2,
            width: `${store.timelinePosition * 100}%`,
            background: 'linear-gradient(90deg, var(--secondary), var(--primary))',
          }} />
          <div style={{
            position: 'absolute', top: -3, left: `${store.timelinePosition * 100}%`,
            transform: 'translateX(-50%)', width: 9, height: 9, borderRadius: '50%',
            background: 'var(--primary)', border: '2px solid var(--bg-primary)',
          }} />
        </div>
        <span className="mono" style={{ fontSize: 9, color: 'var(--text-muted)', minWidth: 36, flexShrink: 0 }}>
          {store.timelinePosition >= 0.99
            ? <span style={{ color: 'var(--primary)' }}>LIVE</span>
            : `T-${Math.round((1 - store.timelinePosition) * 24)}h`}
        </span>

        <div style={{ flex: 1, display: 'flex', justifyContent: 'center', gap: 6 }}>
          <StatBtn icon={<Plane size={11} />} value={counts.aircraft ?? 0} label="ACF" color="var(--secondary)"
            active={store.layerVisibility.aircraft} onClick={() => handleStatClick('aircraft')} />
          <StatBtn icon={<Satellite size={11} />} value={counts.satellites ?? 0} label="SAT" color="var(--accent)"
            active={store.layerVisibility.satellites} onClick={() => handleStatClick('satellites')} />
          <StatBtn icon={<Ship size={11} />} value={counts.ships ?? 0} label="SHP" color="#00c5b0"
            active={store.layerVisibility.ships} onClick={() => handleStatClick('ships')} />
          <StatBtn icon={<AlertTriangle size={11} />} value={counts.threats ?? 0} label="THR" color="var(--danger)"
            active={store.layerVisibility.conflicts} onClick={() => handleStatClick('conflicts')} />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
          <div className="mono" style={{ fontSize: 11, color: 'var(--text-muted)', letterSpacing: '0.02em' }}>
            {utc}<span style={{ fontSize: 9, marginLeft: 3, opacity: 0.5 }}>UTC</span>
          </div>
        </div>
      </footer>

      {/* Floating entity count */}
      <div className="mono" style={{
        position: 'absolute', bottom: 52, right: 14, zIndex: 50, pointerEvents: 'none',
        display: 'flex', alignItems: 'center', gap: 6,
      }}>
        <div style={{
          width: 4, height: 4, borderRadius: '50%', background: 'var(--primary)',
          animation: 'liveDot 2s ease-in-out infinite',
        }} />
        <span style={{ fontSize: 9, color: 'var(--primary)', letterSpacing: '0.06em', opacity: 0.7 }}>
          {counts.total} ENTITIES
        </span>
      </div>
    </div>
  );
}

/* ── Helper components ──────────────────────────────────────── */

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '2px 0' }}>
      <span className="mono" style={{ fontSize: 9, color: 'var(--text-muted)', letterSpacing: '0.08em' }}>{label}</span>
      <span className="mono" style={{ fontSize: 11, color: 'var(--primary)' }}>{value}</span>
    </div>
  );
}

function StatBtn({ icon, value, label, color, active, onClick }: {
  icon: React.ReactNode; value: number; label: string; color: string; active: boolean; onClick: () => void;
}) {
  return (
    <button onClick={onClick} style={{
      display: 'flex', alignItems: 'center', gap: 5, padding: '3px 10px',
      background: active ? 'rgba(0,184,240,0.04)' : 'transparent',
      border: `1px solid ${active ? 'var(--border)' : 'transparent'}`,
      borderRadius: 3, cursor: 'pointer', transition: 'all 0.15s',
      opacity: active ? 1 : 0.4,
    }}>
      <div style={{ color, opacity: 0.8 }}>{icon}</div>
      <span className="mono" style={{ fontSize: 12, color, fontWeight: 700 }}>{value}</span>
      <span className="mono" style={{ fontSize: 8, color: 'var(--text-muted)', letterSpacing: '0.04em' }}>{label}</span>
    </button>
  );
}

function renderEntityFields(type: keyof LayerData, data: any): React.ReactNode {
  if (!data) return null;
  switch (type) {
    case 'aircraft': return <AircraftDetail data={data} />;
    case 'satellites': return <SatelliteDetail data={data} />;
    case 'ships': return <ShipDetail data={data} />;
    case 'earthquakes': return <EarthquakeDetail data={data} />;
    case 'conflicts': return <ConflictDetail data={data} />;
    case 'missiles': return <MissileDetail data={data} />;
    case 'news': return <NewsDetail data={data} />;
    case 'traffic': return <TrafficDetail data={data} />;
    case 'weather': return <WeatherDetail data={data} />;
    default: return null;
  }
}

function SatelliteDetail({ data }: { data: any }) {
  const altKm = data.position?.alt ? Math.round(data.position.alt) : null;
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {data.name && (
        <div style={{
          textAlign: 'center', padding: '10px', background: 'rgba(128,102,255,0.05)',
          border: '1px solid var(--border)', borderRadius: 4,
        }}>
          <div className="mono" style={{ fontSize: 16, fontWeight: 700, color: '#8066ff' }}>{data.name}</div>
          {data.noradId && <div className="mono" style={{ fontSize: 9, color: 'var(--text-muted)', marginTop: 2 }}>NORAD {data.noradId}</div>}
        </div>
      )}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
        {altKm != null && <TelemetryBox label="ALTITUDE" value={altKm.toLocaleString()} unit="km" color="#8066ff" />}
        {data.velocity != null && <TelemetryBox label="VELOCITY" value={data.velocity.toFixed(2)} unit="km/s" color="#8066ff" />}
        {data.inclination != null && <TelemetryBox label="INCLINATION" value={data.inclination.toFixed(1)} unit="°" color="#8066ff" />}
        {data.period != null && <TelemetryBox label="PERIOD" value={Math.round(data.period).toString()} unit="min" color="#8066ff" />}
      </div>
      {data.category && <Row label="TYPE" value={data.category.toUpperCase()} />}
      {data.orbitType && <Row label="ORBIT" value={data.orbitType} />}
    </div>
  );
}

function ShipDetail({ data }: { data: any }) {
  const typeColors: Record<string, string> = { cargo: '#00b8f0', tanker: '#f0a030', naval: '#ff3b5c', passenger: '#e0e8f0', fishing: '#70c040' };
  const col = typeColors[data.shipType] || 'var(--secondary)';
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      <div style={{
        padding: '10px', background: `${col}08`, border: '1px solid var(--border)', borderRadius: 4,
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      }}>
        <div>
          <div className="mono" style={{ fontSize: 14, fontWeight: 700, color: col }}>{data.name || 'UNKNOWN'}</div>
          <div className="mono" style={{ fontSize: 9, color: 'var(--text-muted)', marginTop: 2 }}>MMSI {data.mmsi}</div>
        </div>
        <div style={{
          padding: '3px 8px', borderRadius: 3, fontSize: 9, fontWeight: 700,
          background: `${col}15`, color: col, border: `1px solid ${col}30`,
          textTransform: 'uppercase', fontFamily: 'monospace',
        }}>{data.shipType || 'UNKNOWN'}</div>
      </div>
      {data.destination && (
        <div style={{ textAlign: 'center', padding: '8px', background: 'rgba(0,184,240,0.03)', borderRadius: 4, border: '1px solid var(--border)' }}>
          <div className="mono" style={{ fontSize: 8, color: 'var(--text-muted)', letterSpacing: '0.1em' }}>DESTINATION</div>
          <div className="mono" style={{ fontSize: 14, fontWeight: 600, color: col, marginTop: 2 }}>{data.destination}</div>
        </div>
      )}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
        {data.speed != null && <TelemetryBox label="SPEED" value={data.speed.toFixed(1)} unit="kn" color={col} />}
        {data.heading != null && <TelemetryBox label="HEADING" value={Math.round(data.heading).toString()} unit="°" color={col} />}
      </div>
      {data.flag && <Row label="FLAG" value={data.flag} />}
    </div>
  );
}

function EarthquakeDetail({ data }: { data: any }) {
  const magColor = data.magnitude >= 5 ? '#ff3b5c' : data.magnitude >= 3 ? '#f07030' : '#f0a030';
  const timeStr = data.time ? new Date(data.time).toLocaleString() : '';
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      <div style={{
        textAlign: 'center', padding: '14px', background: `${magColor}08`,
        border: `1px solid ${magColor}20`, borderRadius: 4,
      }}>
        <div className="mono" style={{ fontSize: 36, fontWeight: 700, color: magColor, lineHeight: 1 }}>
          M{data.magnitude?.toFixed(1)}
        </div>
        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 6 }}>{data.place}</div>
        {timeStr && <div className="mono" style={{ fontSize: 9, color: 'var(--text-muted)', marginTop: 4, opacity: 0.6 }}>{timeStr}</div>}
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
        <TelemetryBox label="DEPTH" value={data.depth?.toFixed(1) || '0'} unit="km" color={magColor} />
        <TelemetryBox label="SIGNIFICANCE" value={(data.significance || 0).toString()} unit="" color={magColor} />
      </div>
      {data.tsunami && (
        <div className="mono" style={{
          fontSize: 10, color: '#ff3b5c', background: 'rgba(255,59,92,0.1)',
          padding: '6px 10px', borderRadius: 3, textAlign: 'center', letterSpacing: '0.1em',
          border: '1px solid rgba(255,59,92,0.2)', fontWeight: 700,
        }}>⚠ TSUNAMI WARNING</div>
      )}
      {data.felt != null && data.felt > 0 && <Row label="FELT BY" value={`${data.felt} reports`} />}
      <Row label="STATUS" value={data.status || 'automatic'} />
    </div>
  );
}

function ConflictDetail({ data }: { data: any }) {
  const sevColor = data.severity === 'red' ? '#ff3b5c' : data.severity === 'orange' ? '#f0a030' : '#f0d030';
  const sevLabel = data.severity === 'red' ? 'ACTIVE WAR' : data.severity === 'orange' ? 'ESCALATION' : 'UNREST';
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      <div style={{
        padding: '10px', background: `${sevColor}08`, border: `1px solid ${sevColor}20`, borderRadius: 4,
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      }}>
        <div>
          <div style={{ fontSize: 13, fontWeight: 600 }}>{data.country}</div>
          <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 1 }}>{data.region}</div>
        </div>
        <div className="mono" style={{
          padding: '3px 8px', borderRadius: 3, fontSize: 9, fontWeight: 700,
          background: `${sevColor}15`, color: sevColor, border: `1px solid ${sevColor}30`,
        }}>{sevLabel}</div>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
        <TelemetryBox label="EVENT TYPE" value={data.eventType?.replace(/_/g, ' ').toUpperCase() || ''} unit="" color={sevColor} small />
        {data.fatalities > 0 && <TelemetryBox label="FATALITIES" value={data.fatalities.toString()} unit="" color="#ff3b5c" />}
      </div>
      {data.description && (
        <div style={{ fontSize: 11, color: 'var(--text-muted)', lineHeight: 1.5, padding: '6px 0' }}>{data.description}</div>
      )}
      {data.source && <Row label="SOURCE" value={data.source} />}
      {data.timestamp && <Row label="TIME" value={new Date(data.timestamp * 1000).toLocaleString()} />}
    </div>
  );
}

function MissileDetail({ data }: { data: any }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      <div style={{
        textAlign: 'center', padding: '12px', background: 'rgba(224,32,96,0.06)',
        border: '1px solid rgba(224,32,96,0.15)', borderRadius: 4,
      }}>
        <div className="mono" style={{
          fontSize: 9, color: '#e02060', letterSpacing: '0.12em', fontWeight: 700, marginBottom: 4,
        }}>⚠ LAUNCH DETECTED</div>
        <div className="mono" style={{ fontSize: 18, fontWeight: 700, color: '#e02060' }}>
          {data.type?.toUpperCase() || 'UNKNOWN'}
        </div>
        {data.country && <div className="mono" style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 4 }}>{data.country}</div>}
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
        {data.launchSite && <TelemetryBox label="LAUNCH LAT" value={data.launchSite.lat?.toFixed(3) || '0'} unit="°" color="#e02060" />}
        {data.launchSite && <TelemetryBox label="LAUNCH LNG" value={data.launchSite.lng?.toFixed(3) || '0'} unit="°" color="#e02060" />}
        {data.predictedImpact && <TelemetryBox label="IMPACT LAT" value={data.predictedImpact.lat?.toFixed(3) || '0'} unit="°" color="#ff3b5c" />}
        {data.predictedImpact && <TelemetryBox label="IMPACT LNG" value={data.predictedImpact.lng?.toFixed(3) || '0'} unit="°" color="#ff3b5c" />}
      </div>
      {data.trajectory?.length > 0 && <Row label="TRAJECTORY PTS" value={data.trajectory.length.toString()} />}
      {data.description && <div style={{ fontSize: 11, color: 'var(--text-muted)', lineHeight: 1.5 }}>{data.description}</div>}
      {data.timestamp && <Row label="DETECTED" value={new Date(data.timestamp * 1000).toLocaleString()} />}
    </div>
  );
}

function NewsDetail({ data }: { data: any }) {
  const catColor: Record<string, string> = { conflict: '#ff3b5c', disaster: '#f07030', politics: '#00b8f0', economic: '#70c040', protest: '#f0a030', technology: '#8066ff' };
  const col = catColor[data.category] || '#00b8f0';
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      <div style={{ padding: '10px', background: `${col}06`, border: '1px solid var(--border)', borderRadius: 4 }}>
        <div className="mono" style={{
          fontSize: 9, color: col, letterSpacing: '0.08em', fontWeight: 700, marginBottom: 6,
          textTransform: 'uppercase',
        }}>{data.category}</div>
        <div style={{ fontSize: 13, fontWeight: 600, lineHeight: 1.4 }}>{data.title}</div>
      </div>
      {data.description && (
        <div style={{ fontSize: 11, color: 'var(--text-muted)', lineHeight: 1.5 }}>{data.description}</div>
      )}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
        {data.source && <TelemetryBox label="SOURCE" value={data.source} unit="" color={col} small />}
        {data.sentiment != null && (
          <TelemetryBox label="SENTIMENT"
            value={data.sentiment > 0.1 ? 'POSITIVE' : data.sentiment < -0.1 ? 'NEGATIVE' : 'NEUTRAL'} unit=""
            color={data.sentiment > 0.1 ? '#70c040' : data.sentiment < -0.1 ? '#ff3b5c' : '#f0a030'} small />
        )}
      </div>
      {data.url && (
        <a href={data.url} target="_blank" rel="noopener noreferrer" className="mono" style={{
          fontSize: 10, color: 'var(--secondary)', textDecoration: 'none',
          padding: '6px 10px', background: 'rgba(0,184,240,0.04)', borderRadius: 3,
          border: '1px solid var(--border)', textAlign: 'center', letterSpacing: '0.04em',
        }}>OPEN SOURCE ARTICLE →</a>
      )}
      {data.timestamp && <Row label="PUBLISHED" value={new Date(data.timestamp * 1000).toLocaleString()} />}
    </div>
  );
}

function TrafficDetail({ data }: { data: any }) {
  const congColor = data.congestionLevel > 70 ? '#ff3b5c' : data.congestionLevel > 40 ? '#f0a030' : '#70c040';
  const congLabel = data.congestionLevel > 70 ? 'HEAVY' : data.congestionLevel > 40 ? 'MODERATE' : 'LIGHT';
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      <div style={{
        textAlign: 'center', padding: '12px', background: `${congColor}06`,
        border: `1px solid ${congColor}15`, borderRadius: 4,
      }}>
        <div className="mono" style={{ fontSize: 12, color: 'var(--text-muted)', letterSpacing: '0.08em' }}>{data.city}</div>
        <div className="mono" style={{ fontSize: 32, fontWeight: 700, color: congColor, lineHeight: 1, marginTop: 4 }}>
          {data.congestionLevel}%
        </div>
        <div className="mono" style={{ fontSize: 10, color: congColor, marginTop: 4, letterSpacing: '0.1em' }}>{congLabel} CONGESTION</div>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
        <TelemetryBox label="AVG SPEED" value={data.averageSpeed?.toString() || '0'} unit="km/h" color={congColor} />
        <TelemetryBox label="INCIDENTS" value={(data.incidents?.length || 0).toString()} unit="" color={congColor} />
      </div>
      {data.incidents?.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          <div className="mono" style={{ fontSize: 9, color: 'var(--text-muted)', letterSpacing: '0.08em', padding: '4px 0' }}>ACTIVE INCIDENTS</div>
          {data.incidents.slice(0, 5).map((inc: any, i: number) => (
            <div key={i} style={{
              fontSize: 10, color: 'var(--text-muted)', padding: '4px 8px',
              background: 'var(--bg-surface)', borderRadius: 2, border: '1px solid var(--border)',
              display: 'flex', justifyContent: 'space-between',
            }}>
              <span>{inc.description}</span>
              <span className="mono" style={{ color: congColor, fontSize: 9 }}>{inc.type}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function WeatherDetail({ data }: { data: any }) {
  const tempColor = data.temperature > 30 ? '#ff3b5c' : data.temperature > 20 ? '#f0a030' : data.temperature > 10 ? '#70c040' : data.temperature > 0 ? '#50b0e0' : '#8066ff';
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      <div style={{
        textAlign: 'center', padding: '14px', background: `${tempColor}06`,
        border: `1px solid ${tempColor}15`, borderRadius: 4,
      }}>
        <div className="mono" style={{ fontSize: 40, fontWeight: 300, color: tempColor, lineHeight: 1 }}>
          {data.temperature != null ? `${Math.round(data.temperature)}°` : '--°'}
        </div>
        <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 6 }}>{data.condition || 'Unknown'}</div>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
        {data.windSpeed != null && <TelemetryBox label="WIND" value={data.windSpeed.toFixed(0)} unit="km/h" color="#50b0e0" />}
        {data.windDirection != null && <TelemetryBox label="DIRECTION" value={Math.round(data.windDirection).toString()} unit="°" color="#50b0e0" />}
        {data.humidity != null && <TelemetryBox label="HUMIDITY" value={data.humidity.toString()} unit="%" color="#50b0e0" />}
        {data.visibility != null && <TelemetryBox label="VISIBILITY" value={(data.visibility / 1000).toFixed(1)} unit="km" color="#50b0e0" />}
      </div>
    </div>
  );
}

function AircraftDetail({ data }: { data: any }) {
  const speedKnots = data.velocity ? Math.round(data.velocity * 1.944) : null;
  const speedKmh = data.velocity ? Math.round(data.velocity * 3.6) : null;
  const altFt = data.position?.alt ? Math.round(data.position.alt * 3.281) : null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {/* Route display */}
      {(data.originAirport || data.destinationAirport) && (
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12,
          padding: '12px 10px', background: 'rgba(0,184,240,0.04)',
          border: '1px solid var(--border)', borderRadius: 4,
        }}>
          <div style={{ textAlign: 'center' }}>
            <div className="mono" style={{ fontSize: 20, fontWeight: 700, color: 'var(--secondary)' }}>
              {data.originAirport || '???'}
            </div>
            {data.departureTime && (
              <div className="mono" style={{ fontSize: 9, color: 'var(--text-muted)', marginTop: 2 }}>
                DEP {data.departureTime.slice(11, 16)}
              </div>
            )}
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2, flex: 1 }}>
            <Plane size={14} color="var(--secondary)" style={{ opacity: 0.6 }} />
            <div style={{
              width: '80%', height: 1,
              background: 'linear-gradient(90deg, var(--secondary), transparent, var(--secondary))',
              opacity: 0.3,
            }} />
          </div>

          <div style={{ textAlign: 'center' }}>
            <div className="mono" style={{ fontSize: 20, fontWeight: 700, color: 'var(--secondary)' }}>
              {data.destinationAirport || '???'}
            </div>
            {data.arrivalTime && (
              <div className="mono" style={{ fontSize: 9, color: 'var(--text-muted)', marginTop: 2 }}>
                ARR {data.arrivalTime.slice(11, 16)}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Flight info */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
        {data.airline && <Row label="AIRLINE" value={data.airline} />}
        {data.flightNumber && <Row label="FLIGHT" value={data.flightNumber} />}
        {data.callsign && <Row label="CALLSIGN" value={data.callsign} />}
        {data.aircraftType && <Row label="AIRCRAFT" value={data.aircraftType} />}
        {data.category && <Row label="CATEGORY" value={data.category.toUpperCase()} />}
        {data.originCountry && <Row label="COUNTRY" value={data.originCountry} />}
      </div>

      {/* Telemetry */}
      <div style={{
        display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6, marginTop: 4,
      }}>
        {speedKnots != null && (
          <TelemetryBox label="SPEED" value={`${speedKnots}`} unit="kts" sub={`${speedKmh} km/h`} />
        )}
        {altFt != null && (
          <TelemetryBox label="ALTITUDE" value={`${altFt.toLocaleString()}`} unit="ft"
            sub={`${Math.round(data.position.alt)}m`} />
        )}
        {data.heading != null && (
          <TelemetryBox label="HEADING" value={`${Math.round(data.heading)}`} unit="°" />
        )}
        {data.verticalRate != null && data.verticalRate !== 0 && (
          <TelemetryBox label="V/S" value={`${data.verticalRate > 0 ? '+' : ''}${Math.round(data.verticalRate * 196.85)}`} unit="fpm" />
        )}
      </div>

      {data.squawk && (
        <Row label="SQUAWK" value={data.squawk} />
      )}
      {data.onGround && (
        <div className="mono" style={{
          fontSize: 10, color: 'var(--primary)', background: 'rgba(0,232,123,0.08)',
          padding: '4px 8px', borderRadius: 3, textAlign: 'center', letterSpacing: '0.06em',
        }}>ON GROUND</div>
      )}
    </div>
  );
}

function TelemetryBox({ label, value, unit, sub, color, small }: {
  label: string; value: string; unit: string; sub?: string; color?: string; small?: boolean;
}) {
  const c = color || 'var(--secondary)';
  return (
    <div style={{
      background: 'var(--bg-surface)', border: '1px solid var(--border)',
      borderRadius: 3, padding: small ? '4px 6px' : '6px 8px', textAlign: 'center',
    }}>
      <div className="mono" style={{ fontSize: 8, color: 'var(--text-muted)', letterSpacing: '0.1em', marginBottom: 2 }}>
        {label}
      </div>
      <div className="mono" style={{ fontSize: small ? 10 : 16, fontWeight: 700, color: c, lineHeight: 1 }}>
        {value}{unit && <span style={{ fontSize: 9, fontWeight: 400, marginLeft: 2, opacity: 0.6 }}>{unit}</span>}
      </div>
      {sub && (
        <div className="mono" style={{ fontSize: 9, color: 'var(--text-muted)', marginTop: 2, opacity: 0.6 }}>{sub}</div>
      )}
    </div>
  );
}
