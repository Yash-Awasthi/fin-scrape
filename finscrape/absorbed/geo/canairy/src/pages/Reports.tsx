import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  Download,
  FileText,
  BarChart3,
  Printer,
} from 'lucide-react';
import { useStore } from '../store';
import { DOMAIN_META } from '../types';
import { cn } from '../utils/cn';

export const Reports: React.FC = () => {
  const { indicators, hopiScore, currentPhase } = useStore();

  const redCount = indicators.filter(i => i.status.level === 'red').length;
  const amberCount = indicators.filter(i => i.status.level === 'amber').length;
  const greenCount = indicators.filter(i => i.status.level === 'green').length;

  const domainSummary = useMemo(() => {
    return Object.entries(DOMAIN_META).map(([key, meta]) => {
      const domainIndicators = indicators.filter(i => i.domain === key);
      const red = domainIndicators.filter(i => i.status.level === 'red').length;
      const amber = domainIndicators.filter(i => i.status.level === 'amber').length;
      return { key, label: meta.label, total: domainIndicators.length, red, amber };
    });
  }, [indicators]);

  const handleExportCSV = () => {
    const header = 'ID,Name,Domain,Status,Value,Unit,Trend,Data Source,Last Update\n';
    const rows = indicators.map(i =>
      `${i.id},${i.name},${i.domain},${i.status.level},${i.status.value},${i.unit},${i.status.trend ?? 'stable'},${i.status.dataSource},${i.status.lastUpdate}`
    ).join('\n');
    const blob = new Blob([header + rows], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `canairy-report-${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleExportJSON = () => {
    const report = {
      generated: new Date().toISOString(),
      hopiScore: hopiScore?.score,
      phase: currentPhase?.number,
      summary: { total: indicators.length, red: redCount, amber: amberCount, green: greenCount },
      indicators: indicators.map(i => ({
        id: i.id, name: i.name, domain: i.domain,
        status: i.status.level, value: i.status.value, unit: i.unit,
        trend: i.status.trend, dataSource: i.status.dataSource,
      })),
    };
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `canairy-report-${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handlePrint = () => window.print();

  const reportCards = [
    {
      title: 'Detailed Spreadsheet',
      description: 'All the things we monitor, saved as a spreadsheet you can open in Excel or Google Sheets',
      icon: <FileText className="w-6 h-6 text-white/40" />,
      action: handleExportCSV,
      actionLabel: 'Download Spreadsheet',
    },
    {
      title: 'Data Backup',
      description: 'A complete backup of all your family\'s monitoring data',
      icon: <BarChart3 className="w-6 h-6 text-blue-400" />,
      action: handleExportJSON,
      actionLabel: 'Download Backup',
    },
    {
      title: 'Fridge Sheet',
      description: 'Print this summary and put it on your fridge — a quick reference for your whole family',
      icon: <Printer className="w-6 h-6 text-green-400" />,
      action: handlePrint,
      actionLabel: 'Print for Fridge',
    },
  ];

  return (
    <>
      {/* Header */}
      <div className="border-b border-white/[0.04]">
        <div className="px-4 sm:px-6 lg:px-8 py-4 sm:py-6">
          <h1 className="text-2xl sm:text-3xl font-semibold text-white">Reports</h1>
          <p className="text-white/30 mt-1">Save, print, or share your family's preparedness status</p>
        </div>
      </div>

      <div className="px-4 sm:px-6 lg:px-8 py-4 sm:py-8 space-y-8">
        {/* Quick Stats — Print target */}
        <div className="glass-card p-6" id="print-summary">
          <h2 className="text-sm font-medium text-white/20 uppercase tracking-wider mb-4">Your Family's Current Status</h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
            <div className="text-center">
              <div className="text-3xl font-bold text-white">{hopiScore ? Math.round(hopiScore.score) : '—'}</div>
              <div className="text-xs text-white/20">HOPI Score</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-white">{currentPhase?.number ?? '—'}</div>
              <div className="text-xs text-white/20">Phase</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-red-400">{redCount}</div>
              <div className="text-xs text-white/20">Red Alerts</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-amber-400">{amberCount}</div>
              <div className="text-xs text-white/20">Amber Warnings</div>
            </div>
          </div>

          {/* Domain summary table */}
          <h3 className="text-xs font-medium text-white/20 uppercase tracking-wider mb-3">Domains</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-white/20 text-xs uppercase tracking-wider">
                  <th className="text-left py-2 pr-4">Domain</th>
                  <th className="text-center py-2 px-2">Total</th>
                  <th className="text-center py-2 px-2">Red</th>
                  <th className="text-center py-2 px-2">Amber</th>
                </tr>
              </thead>
              <tbody>
                {domainSummary.map(d => (
                  <tr key={d.key} className="border-t border-white/[0.04]">
                    <td className="py-2 pr-4 text-white/50">{d.label}</td>
                    <td className="py-2 px-2 text-center text-white/30">{d.total}</td>
                    <td className={cn('py-2 px-2 text-center', d.red > 0 ? 'text-red-400 font-medium' : 'text-white/15')}>{d.red}</td>
                    <td className={cn('py-2 px-2 text-center', d.amber > 0 ? 'text-amber-400 font-medium' : 'text-white/15')}>{d.amber}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Export Options */}
        <div>
          <h2 className="text-sm font-medium text-white/20 uppercase tracking-wider mb-4">Export Options</h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {reportCards.map((card, idx) => (
              <motion.div
                key={card.title}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.05 }}
                className="glass-card p-6 flex flex-col"
              >
                <div className="mb-4">{card.icon}</div>
                <h3 className="text-white font-medium mb-1">{card.title}</h3>
                <p className="text-sm text-white/30 mb-6 flex-1">{card.description}</p>
                <button
                  onClick={card.action}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-white/5 text-white/50 rounded-xl hover:bg-white/10 transition-colors text-sm font-medium"
                >
                  <Download className="w-4 h-4" />
                  {card.actionLabel}
                </button>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </>
  );
};
