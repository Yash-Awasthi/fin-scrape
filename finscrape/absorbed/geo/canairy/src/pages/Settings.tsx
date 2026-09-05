import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  Settings as SettingsIcon,
  Bell,
  Database,
  RefreshCw,
  ChevronDown,
  Save,
  RotateCcw,
  Mail,
  Smartphone,
  Monitor,
  Clock,
  Wifi,
  WifiOff,
  Info,
  HelpCircle,
  ExternalLink,
  BookOpen,
  Shield,
  MessageCircle,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { useStore } from '../store';
import { DOMAIN_META, Domain } from '../types';
import { cn } from '../utils/cn';

type NotifChannel = 'email' | 'sms' | 'desktop';

interface NotifSettings {
  channels: Record<NotifChannel, boolean>;
  emailAddress: string;
  phoneNumber: string;
  onPhaseChange: boolean;
  onRedAlert: boolean;
  onTightenUp: boolean;
  quietHoursEnabled: boolean;
  quietStart: string;
  quietEnd: string;
}

interface DataSettings {
  refreshInterval: number;
  mockFallback: boolean;
  autoRefresh: boolean;
}

const DEFAULT_NOTIF: NotifSettings = {
  channels: { email: false, sms: false, desktop: true },
  emailAddress: '',
  phoneNumber: '',
  onPhaseChange: true,
  onRedAlert: true,
  onTightenUp: true,
  quietHoursEnabled: false,
  quietStart: '22:00',
  quietEnd: '07:00',
};

const DEFAULT_DATA: DataSettings = {
  refreshInterval: 60,
  mockFallback: true,
  autoRefresh: true,
};

const REFRESH_OPTIONS = [
  { label: '30 seconds', value: 30 },
  { label: '1 minute', value: 60 },
  { label: '5 minutes', value: 300 },
  { label: '15 minutes', value: 900 },
  { label: '30 minutes', value: 1800 },
];

function Toggle({
  enabled,
  onToggle,
  label,
  description,
}: {
  enabled: boolean;
  onToggle: () => void;
  label: string;
  description?: string;
}) {
  return (
    <button
      onClick={onToggle}
      className="w-full flex items-center justify-between px-4 py-3 rounded-lg hover:bg-white/5 transition-colors text-left"
    >
      <div>
        <span className="text-sm text-white/70">{label}</span>
        {description && <p className="text-xs text-white/20 mt-0.5">{description}</p>}
      </div>
      <div
        className={cn(
          'w-10 h-6 rounded-full relative transition-colors',
          enabled ? 'bg-white/10' : 'bg-white/10'
        )}
      >
        <motion.div
          className="w-4 h-4 rounded-full bg-white absolute top-1"
          animate={{ left: enabled ? 20 : 4 }}
          transition={{ type: 'spring', stiffness: 500, damping: 30 }}
        />
      </div>
    </button>
  );
}

function Section({
  title,
  icon: Icon,
  children,
  defaultOpen = true,
}: {
  title: string;
  icon: React.ElementType;
  children: React.ReactNode;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="glass-card overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full px-5 py-4 flex items-center gap-3 text-left"
      >
        <div className="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center">
          <Icon className="w-4 h-4 text-white/30" />
        </div>
        <h3 className="text-sm font-semibold text-white flex-1">{title}</h3>
        <ChevronDown
          className={cn('w-4 h-4 text-white/20 transition-transform', open && 'rotate-180')}
        />
      </button>
      {open && <div className="px-5 pb-5 border-t border-white/[0.04] pt-4">{children}</div>}
    </div>
  );
}

export const Settings: React.FC = () => {
  const { indicators, refreshAll, loading, systemStatus } = useStore();
  const [notif, setNotif] = useState<NotifSettings>(DEFAULT_NOTIF);
  const [data, setData] = useState<DataSettings>(DEFAULT_DATA);
  const [saved, setSaved] = useState(false);

  const liveCount = indicators.filter((i) => i.status.dataSource === 'LIVE').length;
  const mockCount = indicators.filter((i) => i.status.dataSource === 'MOCK').length;
  const totalCount = indicators.length;

  const handleSave = () => {
    // In a real app this would persist to backend/localStorage
    localStorage.setItem('canairy_notif_settings', JSON.stringify(notif));
    localStorage.setItem('canairy_data_settings', JSON.stringify(data));
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const handleReset = () => {
    setNotif(DEFAULT_NOTIF);
    setData(DEFAULT_DATA);
  };

  // Collect domain stats
  const domainStats = Object.entries(DOMAIN_META).map(([key, meta]) => {
    const domainIndicators = indicators.filter((i) => i.domain === key);
    const redCount = domainIndicators.filter((i) => i.status.level === 'red').length;
    const amberCount = domainIndicators.filter((i) => i.status.level === 'amber').length;
    return { key: key as Domain, ...meta, count: domainIndicators.length, redCount, amberCount };
  });

  return (
    <>
      {/* Header */}
      <div className="border-b border-white/[0.04]">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
          <div className="flex items-center gap-3 mb-1">
            <Link
              to="/dashboard"
              className="text-white/20 hover:text-white/50 text-sm transition-colors"
            >
              Dashboard
            </Link>
            <ChevronDown className="w-3 h-3 text-white/15 rotate-[-90deg]" />
            <span className="text-white/50 text-sm">Settings</span>
          </div>
          <div className="flex items-center gap-4 mt-4">
            <div className="w-12 h-12 rounded-xl bg-gray-500/10 border border-gray-500/20 flex items-center justify-center">
              <SettingsIcon className="w-6 h-6 text-white/30" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">Settings</h1>
              <p className="text-white/30">How Canairy keeps you informed — notifications, data, and preferences</p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* ── Notifications ── */}
        <Section title="Notifications" icon={Bell}>
          <div className="space-y-1 mb-4">
            <h4 className="text-xs font-medium text-white/20 uppercase tracking-wider mb-2">
              Channels
            </h4>
            <Toggle
              enabled={notif.channels.desktop}
              onToggle={() =>
                setNotif((s) => ({
                  ...s,
                  channels: { ...s.channels, desktop: !s.channels.desktop },
                }))
              }
              label="Desktop notifications"
              description="Browser push notifications for alerts"
            />
            <Toggle
              enabled={notif.channels.email}
              onToggle={() =>
                setNotif((s) => ({
                  ...s,
                  channels: { ...s.channels, email: !s.channels.email },
                }))
              }
              label="Email alerts"
              description="Send alerts to your email address"
            />
            {notif.channels.email && (
              <div className="px-4 py-2">
                <div className="flex items-center gap-2">
                  <Mail className="w-4 h-4 text-white/20" />
                  <input
                    type="email"
                    value={notif.emailAddress}
                    onChange={(e) => setNotif((s) => ({ ...s, emailAddress: e.target.value }))}
                    placeholder="your@email.com"
                    className="flex-1 bg-white/[0.03] border border-white/[0.08] rounded-lg px-3 py-2 text-sm text-white/70 placeholder-gray-600 focus:outline-none focus:border-white/20"
                  />
                </div>
              </div>
            )}
            <Toggle
              enabled={notif.channels.sms}
              onToggle={() =>
                setNotif((s) => ({
                  ...s,
                  channels: { ...s.channels, sms: !s.channels.sms },
                }))
              }
              label="SMS alerts"
              description="Text message alerts via Twilio"
            />
            {notif.channels.sms && (
              <div className="px-4 py-2">
                <div className="flex items-center gap-2">
                  <Smartphone className="w-4 h-4 text-white/20" />
                  <input
                    type="tel"
                    value={notif.phoneNumber}
                    onChange={(e) => setNotif((s) => ({ ...s, phoneNumber: e.target.value }))}
                    placeholder="+1 (555) 000-0000"
                    className="flex-1 bg-white/[0.03] border border-white/[0.08] rounded-lg px-3 py-2 text-sm text-white/70 placeholder-gray-600 focus:outline-none focus:border-white/20"
                  />
                </div>
              </div>
            )}
          </div>

          <div className="space-y-1">
            <h4 className="text-xs font-medium text-white/20 uppercase tracking-wider mb-2">
              Alert Triggers
            </h4>
            <Toggle
              enabled={notif.onRedAlert}
              onToggle={() => setNotif((s) => ({ ...s, onRedAlert: !s.onRedAlert }))}
              label="Red alert threshold"
              description="Notify when any indicator turns red"
            />
            <Toggle
              enabled={notif.onPhaseChange}
              onToggle={() => setNotif((s) => ({ ...s, onPhaseChange: !s.onPhaseChange }))}
              label="Phase change"
              description="Notify when the HOPI phase changes"
            />
            <Toggle
              enabled={notif.onTightenUp}
              onToggle={() => setNotif((s) => ({ ...s, onTightenUp: !s.onTightenUp }))}
              label="Tighten-Up protocol"
              description="Notify when 2+ indicators hit red"
            />
          </div>

          <div className="mt-4 space-y-1">
            <h4 className="text-xs font-medium text-white/20 uppercase tracking-wider mb-2">
              Quiet Hours
            </h4>
            <Toggle
              enabled={notif.quietHoursEnabled}
              onToggle={() =>
                setNotif((s) => ({ ...s, quietHoursEnabled: !s.quietHoursEnabled }))
              }
              label="Enable quiet hours"
              description="Suppress non-critical notifications during set hours"
            />
            {notif.quietHoursEnabled && (
              <div className="px-4 py-2 flex items-center gap-3">
                <Clock className="w-4 h-4 text-white/20" />
                <input
                  type="time"
                  value={notif.quietStart}
                  onChange={(e) => setNotif((s) => ({ ...s, quietStart: e.target.value }))}
                  className="bg-white/[0.03] border border-white/[0.08] rounded-lg px-3 py-2 text-sm text-white/70 focus:outline-none focus:border-white/20"
                />
                <span className="text-white/20 text-sm">to</span>
                <input
                  type="time"
                  value={notif.quietEnd}
                  onChange={(e) => setNotif((s) => ({ ...s, quietEnd: e.target.value }))}
                  className="bg-white/[0.03] border border-white/[0.08] rounded-lg px-3 py-2 text-sm text-white/70 focus:outline-none focus:border-white/20"
                />
              </div>
            )}
          </div>
        </Section>

        {/* ── Data Sources ── */}
        <Section title="Data Sources" icon={Database}>
          {/* Status overview */}
          <div className="grid grid-cols-3 gap-3 mb-5">
            <div className="bg-white/[0.03] rounded-xl border border-white/[0.04] p-3 text-center">
              <div className="text-2xl font-bold text-white">{totalCount}</div>
              <div className="text-xs text-white/20">Total Indicators</div>
            </div>
            <div className="bg-white/[0.03] rounded-xl border border-green-500/10 p-3 text-center">
              <div className="flex items-center justify-center gap-1.5">
                <Wifi className="w-4 h-4 text-green-400" />
                <span className="text-2xl font-bold text-green-400">{liveCount}</span>
              </div>
              <div className="text-xs text-white/20">Live</div>
            </div>
            <div className="bg-white/[0.03] rounded-xl border border-amber-500/10 p-3 text-center">
              <div className="flex items-center justify-center gap-1.5">
                <WifiOff className="w-4 h-4 text-amber-400" />
                <span className="text-2xl font-bold text-amber-400">{mockCount}</span>
              </div>
              <div className="text-xs text-white/20">Mock / Offline</div>
            </div>
          </div>

          {/* Domain breakdown */}
          <h4 className="text-xs font-medium text-white/20 uppercase tracking-wider mb-3">
            Domains ({domainStats.length})
          </h4>
          <div className="space-y-2 mb-5">
            {domainStats.map((d) => (
              <div
                key={d.key}
                className="flex items-center justify-between px-3 py-2.5 bg-white/[0.03] rounded-lg"
              >
                <div>
                  <span className="text-sm text-white/70">{d.label}</span>
                  <span className="text-xs text-white/15 ml-2">
                    weight: {d.weight}×
                  </span>
                </div>
                <div className="flex items-center gap-3 text-xs">
                  <span className="text-white/20">{d.count} indicators</span>
                  {d.redCount > 0 && (
                    <span className="text-red-400">{d.redCount} red</span>
                  )}
                  {d.amberCount > 0 && (
                    <span className="text-amber-400">{d.amberCount} amber</span>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Refresh settings */}
          <h4 className="text-xs font-medium text-white/20 uppercase tracking-wider mb-3">
            Refresh
          </h4>
          <Toggle
            enabled={data.autoRefresh}
            onToggle={() => setData((s) => ({ ...s, autoRefresh: !s.autoRefresh }))}
            label="Auto-refresh"
            description="Automatically poll for new data"
          />
          {data.autoRefresh && (
            <div className="px-4 py-2">
              <label className="text-xs text-white/20 mb-1 block">Refresh interval</label>
              <select
                value={data.refreshInterval}
                onChange={(e) =>
                  setData((s) => ({ ...s, refreshInterval: Number(e.target.value) }))
                }
                className="bg-white/[0.03] border border-white/[0.08] rounded-lg px-3 py-2 text-sm text-white/70 focus:outline-none focus:border-white/20 w-full"
              >
                {REFRESH_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
          )}
          <Toggle
            enabled={data.mockFallback}
            onToggle={() => setData((s) => ({ ...s, mockFallback: !s.mockFallback }))}
            label="Mock data fallback"
            description="Use mock data when live APIs are unavailable"
          />

          <button
            onClick={() => refreshAll()}
            disabled={loading}
            className="mt-3 w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-white/5 text-white/50 rounded-xl hover:bg-white/20 transition-colors text-sm font-medium"
          >
            <RefreshCw className={cn('w-4 h-4', loading && 'animate-spin')} />
            {loading ? 'Refreshing...' : 'Refresh All Data Now'}
          </button>
        </Section>

        {/* ── System ── */}
        <Section title="System" icon={Monitor} defaultOpen={false}>
          <div className="space-y-3">
            <div className="flex items-center justify-between px-3 py-2 bg-white/[0.03] rounded-lg">
              <span className="text-sm text-white/30">System status</span>
              <span
                className={cn(
                  'text-sm font-medium',
                  systemStatus?.operational ? 'text-green-400' : 'text-red-400'
                )}
              >
                {systemStatus?.operational ? 'Operational' : 'Degraded'}
              </span>
            </div>
            <div className="flex items-center justify-between px-3 py-2 bg-white/[0.03] rounded-lg">
              <span className="text-sm text-white/30">Last update</span>
              <span className="text-sm text-white/50">
                {systemStatus?.lastUpdate
                  ? new Date(systemStatus.lastUpdate).toLocaleString()
                  : '—'}
              </span>
            </div>
            <div className="flex items-center justify-between px-3 py-2 bg-white/[0.03] rounded-lg">
              <span className="text-sm text-white/30">Data quality</span>
              <span className="text-sm text-white/50">
                {systemStatus?.dataQuality != null
                  ? `${Math.round(systemStatus.dataQuality * 100)}%`
                  : '—'}
              </span>
            </div>
            <div className="flex items-center justify-between px-3 py-2 bg-white/[0.03] rounded-lg">
              <span className="text-sm text-white/30">Active alerts</span>
              <span className="text-sm text-white/50">
                {systemStatus?.activeAlerts ?? '—'}
              </span>
            </div>
          </div>
        </Section>

        {/* ── About Canairy ── */}
        <Section title="About Canairy" icon={Info} defaultOpen={false}>
          <div className="space-y-4">
            <p className="text-sm text-white/50 leading-relaxed">
              Canairy is a free, open-source household resilience monitor. We track 35+ public data sources —
              government APIs, financial data, infrastructure reports — and translate them into simple,
              actionable recommendations for your family.
            </p>

            <div className="space-y-2">
              <div className="flex items-center justify-between px-3 py-2 bg-white/[0.03] rounded-lg">
                <span className="text-sm text-white/30">Version</span>
                <span className="text-sm text-white/50 font-mono">1.0.0</span>
              </div>
              <div className="flex items-center justify-between px-3 py-2 bg-white/[0.03] rounded-lg">
                <span className="text-sm text-white/30">Indicators tracked</span>
                <span className="text-sm text-white/50">{totalCount}</span>
              </div>
            </div>

            <div className="p-3 rounded-lg bg-amber-500/5 border border-amber-500/10">
              <p className="text-xs text-amber-200/70 leading-relaxed">
                <strong className="text-amber-300">Built by parents, for parents.</strong> We created Canairy because
                we were tired of doomscrolling the news trying to figure out what it meant for our families. Now we check
                once a week and know exactly what to do.
              </p>
            </div>
          </div>
        </Section>

        {/* ── Help & Learning ── */}
        <Section title="Help & Learning" icon={HelpCircle} defaultOpen={false}>
          <div className="space-y-3">
            <Link
              to="/action-plan#how-it-works"
              className="flex items-center gap-3 px-3 py-3 bg-white/[0.03] rounded-lg hover:bg-white/[0.06] transition-colors"
            >
              <BookOpen className="w-5 h-5 text-amber-400" />
              <div className="flex-1">
                <p className="text-sm text-white/70">How Canairy works</p>
                <p className="text-xs text-white/30">Learn about our methodology and data sources</p>
              </div>
              <ExternalLink className="w-4 h-4 text-white/20" />
            </Link>

            <div className="flex items-center gap-3 px-3 py-3 bg-white/[0.03] rounded-lg">
              <Shield className="w-5 h-5 text-green-400" />
              <div className="flex-1">
                <p className="text-sm text-white/70">What do the colors mean?</p>
                <p className="text-xs text-white/30">
                  <span className="text-emerald-400">Green</span> = normal,{' '}
                  <span className="text-amber-400">Amber</span> = watch,{' '}
                  <span className="text-red-400">Red</span> = act
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3 px-3 py-3 bg-white/[0.03] rounded-lg">
              <Clock className="w-5 h-5 text-blue-400" />
              <div className="flex-1">
                <p className="text-sm text-white/70">How often should I check?</p>
                <p className="text-xs text-white/30">Most families check weekly. We'll alert you if something needs attention sooner.</p>
              </div>
            </div>

            <a
              href="https://github.com/canairy/canairy/issues"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-3 px-3 py-3 bg-white/[0.03] rounded-lg hover:bg-white/[0.06] transition-colors"
            >
              <MessageCircle className="w-5 h-5 text-purple-400" />
              <div className="flex-1">
                <p className="text-sm text-white/70">Give feedback</p>
                <p className="text-xs text-white/30">Report issues or suggest improvements</p>
              </div>
              <ExternalLink className="w-4 h-4 text-white/20" />
            </a>
          </div>
        </Section>

        {/* ── Save / Reset ── */}
        <div className="flex items-center gap-3 pt-2">
          <button
            onClick={handleSave}
            className={cn(
              'flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-xl font-medium transition-colors',
              saved
                ? 'bg-green-600 text-white'
                : 'bg-white/10 text-white hover:bg-white/15'
            )}
          >
            <Save className="w-4 h-4" />
            {saved ? 'Saved!' : 'Save Settings'}
          </button>
          <button
            onClick={handleReset}
            className="flex items-center justify-center gap-2 px-4 py-3 bg-white/5 text-white/30 rounded-xl hover:bg-white/20 hover:text-white/50 transition-colors font-medium"
          >
            <RotateCcw className="w-4 h-4" />
            Reset
          </button>
        </div>
        <p className="text-center text-xs text-white/20 mt-3">
          Settings are saved to this device only
        </p>
      </div>
    </>
  );
};
