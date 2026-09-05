import React from 'react';
import { Eye } from 'lucide-react';

export const PageSkeleton: React.FC = () => {
  return (
    <div className="min-h-screen bg-[#09090B] flex flex-col items-center justify-center relative overflow-hidden">
      {/* Ambient glow */}
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 w-[500px] h-[300px] bg-green-500/5 rounded-full blur-[100px] pointer-events-none" />

      {/* Loading content */}
      <div className="relative z-10 flex flex-col items-center">
        {/* Logo with pulse */}
        <div className="relative mb-6">
          <div className="w-16 h-16 rounded-2xl bg-white/[0.04] border border-white/[0.08] flex items-center justify-center">
            <Eye className="w-8 h-8 text-green-400" />
          </div>
          {/* Pulse ring */}
          <div className="absolute inset-0 rounded-2xl border border-green-400/30 animate-ping" style={{ animationDuration: '1.5s' }} />
        </div>

        {/* Wordmark */}
        <h1 className="text-2xl font-display font-bold text-white mb-2 tracking-tight">
          Canairy
        </h1>

        {/* Loading indicator */}
        <div className="flex items-center gap-2 text-white/40 text-sm">
          <span>Loading dashboard</span>
          <span className="flex gap-1">
            <span className="w-1 h-1 rounded-full bg-white/40 animate-bounce" style={{ animationDelay: '0ms' }} />
            <span className="w-1 h-1 rounded-full bg-white/40 animate-bounce" style={{ animationDelay: '150ms' }} />
            <span className="w-1 h-1 rounded-full bg-white/40 animate-bounce" style={{ animationDelay: '300ms' }} />
          </span>
        </div>

        {/* Progress bar */}
        <div className="mt-6 w-48 h-1 bg-white/5 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-green-500/50 to-green-400/80 rounded-full"
            style={{
              animation: 'loading-progress 1.5s ease-in-out infinite',
            }}
          />
        </div>
      </div>

      {/* Skeleton preview hint */}
      <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-[#09090B] to-transparent pointer-events-none" />

      {/* Inline keyframes */}
      <style>{`
        @keyframes loading-progress {
          0% { width: 0%; margin-left: 0; }
          50% { width: 60%; margin-left: 20%; }
          100% { width: 0%; margin-left: 100%; }
        }
      `}</style>
    </div>
  );
};

// Skeleton components for inline loading states
export const CardSkeleton: React.FC<{ className?: string }> = ({ className = '' }) => (
  <div className={`glass-card p-6 animate-pulse ${className}`}>
    <div className="h-4 w-24 bg-white/5 rounded mb-4" />
    <div className="h-8 w-32 bg-white/5 rounded mb-2" />
    <div className="h-3 w-full bg-white/5 rounded" />
  </div>
);

export const ListSkeleton: React.FC<{ items?: number }> = ({ items = 5 }) => (
  <div className="space-y-3">
    {Array.from({ length: items }).map((_, i) => (
      <div
        key={i}
        className="glass-card p-4 animate-pulse flex items-center gap-4"
        style={{ animationDelay: `${i * 100}ms` }}
      >
        <div className="w-10 h-10 bg-white/5 rounded-xl flex-shrink-0" />
        <div className="flex-1">
          <div className="h-4 w-32 bg-white/5 rounded mb-2" />
          <div className="h-3 w-48 bg-white/5 rounded" />
        </div>
        <div className="h-6 w-16 bg-white/5 rounded-full" />
      </div>
    ))}
  </div>
);

export const ChartSkeleton: React.FC = () => (
  <div className="glass-card p-6 animate-pulse">
    <div className="flex justify-between items-center mb-6">
      <div className="h-5 w-32 bg-white/5 rounded" />
      <div className="h-8 w-24 bg-white/5 rounded-lg" />
    </div>
    <div className="h-48 bg-white/5 rounded-xl flex items-end justify-around p-4">
      {Array.from({ length: 7 }).map((_, i) => (
        <div
          key={i}
          className="w-8 bg-white/10 rounded-t"
          style={{ height: `${30 + Math.random() * 50}%` }}
        />
      ))}
    </div>
  </div>
);
