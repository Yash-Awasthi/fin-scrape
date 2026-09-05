import { useEffect, useMemo, useState, useCallback } from 'react';
import {
  Plane, Satellite, Ship, Activity, AlertTriangle,
  Rocket, Newspaper, Car, Cloud, Shield, ArrowRight,
  Globe, Eye, Zap, Radio, Lock, Terminal, Hexagon, Cpu,
} from 'lucide-react';
import { useAppStore } from '../../stores/appStore';
import { connectWebSocket } from '../../services/websocket';

interface LandingPageProps {
  onEnter: () => void;
}

type Theme = 'command' | 'cyber' | 'nexus';

const CATEGORIES = [
  { key: 'aircraft', label: 'Aircraft', desc: 'Live global flight tracking', icon: Plane, color: '#00b8f0' },
  { key: 'satellites', label: 'Satellites', desc: 'Orbital position monitoring', icon: Satellite, color: '#8066ff' },
  { key: 'ships', label: 'Ships', desc: 'Maritime vessel tracking', icon: Ship, color: '#00c5b0' },
  { key: 'earthquakes', label: 'Earthquakes', desc: 'Seismic activity monitoring', icon: Activity, color: '#f07030' },
  { key: 'conflicts', label: 'War Zones', desc: 'Global conflict intelligence', icon: AlertTriangle, color: '#ff3b5c' },
  { key: 'missiles', label: 'Missiles', desc: 'Launch detection & tracking', icon: Rocket, color: '#e02060' },
  { key: 'news', label: 'News Intel', desc: 'Global event monitoring', icon: Newspaper, color: '#f0a030' },
  { key: 'traffic', label: 'Traffic', desc: 'Urban congestion analysis', icon: Car, color: '#70c040' },
  { key: 'weather', label: 'Weather', desc: 'Global weather conditions', icon: Cloud, color: '#50b0e0' },
] as const;

const THEME_META: { key: Theme; label: string; icon: typeof Eye }[] = [
  { key: 'command', label: 'Command', icon: Shield },
  { key: 'cyber', label: 'Cyber', icon: Cpu },
  { key: 'nexus', label: 'Nexus', icon: Hexagon },
];

export function LandingPage({ onEnter }: LandingPageProps) {
  const layers = useAppStore((s) => s.layers);
  const [theme, setTheme] = useState<Theme>('command');
  const [hovered, setHovered] = useState<string | null>(null);
  const [entered, setEntered] = useState(false);

  useEffect(() => { connectWebSocket(); }, []);

  const counts = useMemo(() => {
    const c: Record<string, number> = {};
    let total = 0;
    for (const cat of CATEGORIES) {
      const len = (layers as any)[cat.key]?.length ?? 0;
      c[cat.key] = len;
      total += len;
    }
    c.total = total;
    return c;
  }, [layers]);

  const handleEnter = useCallback(() => {
    setEntered(true);
    setTimeout(onEnter, 600);
  }, [onEnter]);

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 9999,
      background: theme === 'nexus' ? '#020510' : theme === 'cyber' ? '#03060a' : '#05080d',
      transition: 'background 0.5s, opacity 0.5s',
      opacity: entered ? 0 : 1,
      overflow: 'auto',
    }}>
      {/* Background effects per theme */}
      {theme === 'command' && <CommandBg />}
      {theme === 'cyber' && <CyberBg />}
      {theme === 'nexus' && <NexusBg />}

      {/* Main content */}
      <div style={{
        position: 'relative', zIndex: 2, minHeight: '100%',
        display: 'flex', flexDirection: 'column', alignItems: 'center',
        padding: '32px 24px',
      }}>
        {/* Theme selector */}
        <div style={{
          display: 'flex', gap: 4, marginBottom: 40,
          background: 'rgba(255,255,255,0.02)', borderRadius: 6,
          border: '1px solid rgba(255,255,255,0.05)', padding: 3,
        }}>
          {THEME_META.map(t => {
            const Icon = t.icon;
            const active = theme === t.key;
            return (
              <button key={t.key} onClick={() => setTheme(t.key)} className="mono" style={{
                padding: '6px 16px', borderRadius: 4, border: 'none', cursor: 'pointer',
                fontSize: 10, letterSpacing: '0.08em', fontWeight: 600,
                display: 'flex', alignItems: 'center', gap: 5,
                background: active ? 'rgba(0,184,240,0.1)' : 'transparent',
                color: active ? '#00b8f0' : '#3a4a5a',
                transition: 'all 0.2s',
              }}>
                <Icon size={12} />{t.label.toUpperCase()}
              </button>
            );
          })}
        </div>

        {/* Header section — varies by theme */}
        {theme === 'command' && <CommandHeader counts={counts} />}
        {theme === 'cyber' && <CyberHeader counts={counts} />}
        {theme === 'nexus' && <NexusHeader counts={counts} />}

        {/* Category grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: theme === 'nexus' ? 16 : 12,
          width: '100%', maxWidth: 780, marginBottom: 36,
        }}>
          {CATEGORIES.map((cat, i) => (
            <CategoryCard key={cat.key} cat={cat} index={i} count={counts[cat.key] ?? 0}
              hovered={hovered === cat.key} theme={theme}
              onHover={() => setHovered(cat.key)} onLeave={() => setHovered(null)}
            />
          ))}
        </div>

        {/* Enter button — varies by theme */}
        <EnterButton theme={theme} onClick={handleEnter} />

        {/* Footer */}
        <div className="mono" style={{
          fontSize: 9, color: '#1a2030', letterSpacing: '0.12em', marginTop: 28,
        }}>
          {theme === 'nexus' ? 'NEXUS PROTOCOL // AUTHORIZED ACCESS ONLY' :
           theme === 'cyber' ? 'ENCRYPTED CHANNEL // AES-256-GCM' :
           'CLASSIFICATION: TOP SECRET // SI // NOFORN'}
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════
   THEME 1: COMMAND — Military command center
   ═══════════════════════════════════════════════════════════════ */

function CommandBg() {
  return <>
    <div style={{
      position: 'absolute', inset: 0, opacity: 0.025, pointerEvents: 'none',
      backgroundImage: 'linear-gradient(rgba(0,184,240,0.3) 1px, transparent 1px), linear-gradient(90deg, rgba(0,184,240,0.3) 1px, transparent 1px)',
      backgroundSize: '60px 60px',
    }} />
    <div style={{
      position: 'absolute', inset: 0, pointerEvents: 'none',
      background: 'radial-gradient(ellipse at center, transparent 30%, #05080d 75%)',
    }} />
  </>;
}

function CommandHeader({ counts }: { counts: Record<string, number> }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginBottom: 32 }}>
      <Shield size={28} color="#00b8f0" style={{ marginBottom: 16, filter: 'drop-shadow(0 0 12px rgba(0,184,240,0.3))' }} />
      <h1 className="mono" style={{
        fontSize: 38, fontWeight: 700, color: '#e0e8f0', margin: 0,
        textShadow: '0 0 40px rgba(0,184,240,0.25)',
        letterSpacing: '0.2em',
      }}>WORLDVIEW</h1>
      <div className="mono" style={{ fontSize: 12, color: '#00b8f0', letterSpacing: '0.35em', marginTop: 6 }}>INTELLIGENCE</div>
      <Divider color="rgba(0,184,240,0.2)" />
      <StatusLine count={counts.total} color="#00b8f0" label="ENTITIES TRACKING" icon={<Radio size={10} />} />
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════
   THEME 2: CYBER — Dark hacker / cyberpunk
   ═══════════════════════════════════════════════════════════════ */

function CyberBg() {
  return <>
    <div style={{
      position: 'absolute', inset: 0, opacity: 0.03, pointerEvents: 'none',
      backgroundImage: `repeating-linear-gradient(0deg, rgba(0,255,136,0.15) 0px, transparent 1px, transparent 3px)`,
      backgroundSize: '100% 3px',
    }} />
    <div style={{
      position: 'absolute', inset: 0, pointerEvents: 'none',
      background: 'radial-gradient(ellipse at 50% 30%, rgba(0,255,136,0.03) 0%, transparent 60%)',
    }} />
  </>;
}

function CyberHeader({ counts }: { counts: Record<string, number> }) {
  const [typed, setTyped] = useState('');
  const full = 'WORLDVIEW_INTELLIGENCE';
  useEffect(() => {
    let i = 0;
    const iv = setInterval(() => {
      i++;
      setTyped(full.slice(0, i));
      if (i >= full.length) clearInterval(iv);
    }, 60);
    return () => clearInterval(iv);
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginBottom: 32 }}>
      <Terminal size={28} color="#00e87b" style={{ marginBottom: 16, filter: 'drop-shadow(0 0 12px rgba(0,232,123,0.3))' }} />
      <h1 className="mono" style={{
        fontSize: 32, fontWeight: 700, color: '#00e87b', margin: 0,
        textShadow: '0 0 30px rgba(0,232,123,0.4), 0 0 60px rgba(0,232,123,0.1)',
        letterSpacing: '0.12em',
      }}>
        {typed}<span style={{ animation: 'blink 1s step-end infinite', color: '#00e87b' }}>_</span>
      </h1>
      <style>{`@keyframes blink { 50% { opacity: 0; } }`}</style>
      <div className="mono" style={{ fontSize: 10, color: '#0a5a30', letterSpacing: '0.2em', marginTop: 8 }}>
        {'>'} SECURE OSINT PLATFORM v3.1.0
      </div>
      <Divider color="rgba(0,232,123,0.15)" />
      <StatusLine count={counts.total} color="#00e87b" label="NODES ACTIVE" icon={<Zap size={10} />} />
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════
   THEME 3: NEXUS — Holographic / futuristic sci-fi
   ═══════════════════════════════════════════════════════════════ */

function NexusBg() {
  return <>
    <div style={{
      position: 'absolute', inset: 0, opacity: 0.02, pointerEvents: 'none',
      backgroundImage: `radial-gradient(circle at 50% 50%, rgba(128,102,255,0.2) 0%, transparent 70%)`,
    }} />
    <div style={{
      position: 'absolute', inset: 0, opacity: 0.015, pointerEvents: 'none',
      backgroundImage: `
        linear-gradient(30deg, rgba(128,102,255,0.3) 12%, transparent 12.5%, transparent 87%, rgba(128,102,255,0.3) 87.5%),
        linear-gradient(150deg, rgba(128,102,255,0.3) 12%, transparent 12.5%, transparent 87%, rgba(128,102,255,0.3) 87.5%),
        linear-gradient(30deg, rgba(128,102,255,0.3) 12%, transparent 12.5%, transparent 87%, rgba(128,102,255,0.3) 87.5%),
        linear-gradient(150deg, rgba(128,102,255,0.3) 12%, transparent 12.5%, transparent 87%, rgba(128,102,255,0.3) 87.5%)
      `,
      backgroundSize: '80px 140px',
      backgroundPosition: '0 0, 0 0, 40px 70px, 40px 70px',
    }} />
    <div style={{
      position: 'absolute', inset: 0, pointerEvents: 'none',
      background: 'radial-gradient(ellipse at center, transparent 25%, #020510 70%)',
    }} />
  </>;
}

function NexusHeader({ counts }: { counts: Record<string, number> }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginBottom: 32 }}>
      <div style={{
        width: 52, height: 52, borderRadius: '50%', marginBottom: 16,
        background: 'radial-gradient(circle, rgba(128,102,255,0.15) 0%, transparent 70%)',
        border: '1px solid rgba(128,102,255,0.2)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        boxShadow: '0 0 30px rgba(128,102,255,0.15), inset 0 0 20px rgba(128,102,255,0.05)',
      }}>
        <Globe size={24} color="#8066ff" style={{ filter: 'drop-shadow(0 0 8px rgba(128,102,255,0.4))' }} />
      </div>
      <h1 className="mono" style={{
        fontSize: 36, fontWeight: 300, color: '#d0c8f0', margin: 0,
        textShadow: '0 0 40px rgba(128,102,255,0.3)',
        letterSpacing: '0.3em',
      }}>WORLDVIEW</h1>
      <div className="mono" style={{ fontSize: 11, color: '#8066ff', letterSpacing: '0.4em', marginTop: 8, fontWeight: 300 }}>
        N E X U S
      </div>
      <Divider color="rgba(128,102,255,0.15)" />
      <StatusLine count={counts.total} color="#8066ff" label="CONNECTED SOURCES" icon={<Eye size={10} />} />
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════
   SHARED COMPONENTS
   ═══════════════════════════════════════════════════════════════ */

function Divider({ color }: { color: string }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 12, margin: '24px 0' }}>
      <div style={{ width: 80, height: 1, background: `linear-gradient(90deg, transparent, ${color})` }} />
      <div style={{ width: 4, height: 4, borderRadius: '50%', background: color, opacity: 0.6 }} />
      <div style={{ width: 80, height: 1, background: `linear-gradient(270deg, transparent, ${color})` }} />
    </div>
  );
}

function StatusLine({ count, color, label, icon }: { count: number; color: string; label: string; icon: React.ReactNode }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
      <div style={{ color, opacity: 0.8 }}>{icon}</div>
      <span className="mono" style={{ fontSize: 11, color, letterSpacing: '0.06em', fontWeight: 600 }}>
        {count.toLocaleString()}
      </span>
      <span className="mono" style={{ fontSize: 10, color, opacity: 0.5, letterSpacing: '0.08em' }}>{label}</span>
    </div>
  );
}

function CategoryCard({ cat, index, count, hovered, theme, onHover, onLeave }: {
  cat: typeof CATEGORIES[number]; index: number; count: number; hovered: boolean;
  theme: Theme; onHover: () => void; onLeave: () => void;
}) {
  const Icon = cat.icon;
  const accent = theme === 'cyber' ? '#00e87b' : theme === 'nexus' ? '#8066ff' : cat.color;
  const borderColor = hovered ? `${cat.color}50` : theme === 'nexus' ? 'rgba(128,102,255,0.08)' : theme === 'cyber' ? 'rgba(0,232,123,0.06)' : 'rgba(0,184,240,0.06)';

  const bg = hovered
    ? theme === 'nexus' ? 'rgba(128,102,255,0.04)' : theme === 'cyber' ? 'rgba(0,232,123,0.03)' : 'rgba(0,184,240,0.03)'
    : theme === 'nexus' ? 'rgba(5,8,20,0.8)' : theme === 'cyber' ? 'rgba(3,8,12,0.8)' : 'rgba(11,16,24,0.9)';

  return (
    <div onMouseEnter={onHover} onMouseLeave={onLeave} style={{
      background: bg, border: `1px solid ${borderColor}`,
      borderRadius: theme === 'nexus' ? 8 : 4,
      padding: '16px 14px', cursor: 'pointer',
      transition: 'all 0.2s', position: 'relative', overflow: 'hidden',
      transform: hovered ? 'translateY(-2px)' : 'translateY(0)',
      boxShadow: hovered ? `0 8px 24px ${cat.color}10` : 'none',
    }}>
      {/* Top accent */}
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0, height: hovered ? 2 : 0,
        background: `linear-gradient(90deg, transparent, ${cat.color}, transparent)`,
        transition: 'height 0.2s', opacity: 0.6,
      }} />

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 32, height: 32, borderRadius: theme === 'nexus' ? '50%' : 6,
            background: `${cat.color}08`, border: `1px solid ${cat.color}15`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            transition: 'all 0.2s',
            boxShadow: hovered ? `0 0 12px ${cat.color}20` : 'none',
          }}>
            <Icon size={15} color={cat.color} />
          </div>
          <div>
            <div className="mono" style={{ fontSize: 11, fontWeight: 600, color: '#c0c8d4', letterSpacing: '0.04em' }}>
              {cat.label.toUpperCase()}
            </div>
            <div style={{ fontSize: 10, color: '#3a4a5a', marginTop: 1, lineHeight: 1.3 }}>{cat.desc}</div>
          </div>
        </div>
        <div className="mono" style={{
          fontSize: 20, fontWeight: 700, color: cat.color,
          textShadow: hovered ? `0 0 12px ${cat.color}40` : 'none',
          transition: 'text-shadow 0.2s',
        }}>
          {count}
        </div>
      </div>
    </div>
  );
}

function EnterButton({ theme, onClick }: { theme: Theme; onClick: () => void }) {
  const [hover, setHover] = useState(false);
  const color = theme === 'cyber' ? '#00e87b' : theme === 'nexus' ? '#8066ff' : '#00b8f0';
  const label = theme === 'cyber' ? 'INITIALIZE SYSTEM' : theme === 'nexus' ? 'ENTER NEXUS' : 'ENTER COMMAND CENTER';

  return (
    <button onClick={onClick} onMouseEnter={() => setHover(true)} onMouseLeave={() => setHover(false)}
      className="mono" style={{
        background: hover ? `${color}15` : `${color}06`,
        border: `1px solid ${hover ? `${color}60` : `${color}25`}`,
        borderRadius: theme === 'nexus' ? 30 : theme === 'cyber' ? 2 : 100,
        padding: theme === 'cyber' ? '12px 36px' : '13px 36px',
        color: hover ? '#e8ecf0' : color,
        fontSize: 12, fontWeight: 600, letterSpacing: '0.14em',
        cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 10,
        transition: 'all 0.25s',
        boxShadow: hover ? `0 0 24px ${color}15` : 'none',
        textTransform: 'uppercase',
      }}>
      {theme === 'cyber' ? <Lock size={14} /> : null}
      {label}
      <ArrowRight size={14} style={{
        transition: 'transform 0.2s',
        transform: hover ? 'translateX(4px)' : 'translateX(0)',
      }} />
    </button>
  );
}
