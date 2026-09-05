import { useEffect, useState, useRef } from 'react';
import { getTraders, getDecisions, API_BASE, getStoredAccessKey } from '../lib/api';
import type { Trader, Decision } from '../types';
import { RefreshCw, Terminal, Activity, FileText } from 'lucide-react';

interface LogMessage {
  timestamp: string;
  message: string;
}

export default function Logs() {
  const [viewMode, setViewMode] = useState<'decisions' | 'system'>('decisions');
  const [traders, setTraders] = useState<Trader[]>([]);
  const [selectedTrader, setSelectedTrader] = useState<string | null>(null);
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [loading, setLoading] = useState(true);

  // System logs state
  const [systemLogs, setSystemLogs] = useState<LogMessage[]>([]);
  const [autoScroll, setAutoScroll] = useState(true);
  const logsEndRef = useRef<HTMLDivElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    loadTraders();

    return () => {
      // Cleanup SSE on unmount
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  useEffect(() => {
    if (selectedTrader && viewMode === 'decisions') {
      loadDecisions();
    }
  }, [selectedTrader, viewMode]);

  // Connect to system logs stream
  useEffect(() => {
    if (viewMode === 'system') {
      const accessKey = getStoredAccessKey();
      // Construct URL with access key query param if it exists
      const url = `${API_BASE}/logs/stream${accessKey ? `?access_key=${accessKey}` : ''}`;

      const evtSource = new EventSource(url);

      evtSource.onopen = () => {
        console.log('Connected to log stream');
      };

      evtSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setSystemLogs(prev => {
            // Keep last 1000 logs
            const newState = [...prev, data];
            if (newState.length > 1000) {
              return newState.slice(newState.length - 1000);
            }
            return newState;
          });
        } catch (e) {
          console.error('Failed to parse log message', e);
        }
      };

      evtSource.onerror = (err) => {
        console.error('Log stream error:', err);
        evtSource.close();
      };

      eventSourceRef.current = evtSource;

      return () => {
        evtSource.close();
      };
    }
  }, [viewMode]);

  // Auto-scroll logic
  useEffect(() => {
    if (autoScroll && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [systemLogs, autoScroll, viewMode]);

  const loadTraders = async () => {
    try {
      const res = await getTraders();
      const traderList = res.data.traders || [];
      setTraders(traderList);
      if (traderList.length > 0) {
        setSelectedTrader(traderList[0].id);
      }
    } catch (err) {
      console.error('Failed to load traders:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadDecisions = async () => {
    if (!selectedTrader) return;
    try {
      const res = await getDecisions(selectedTrader);
      setDecisions(res.data.decisions || []);
    } catch (err) {
      console.error('Failed to load decisions:', err);
    }
  };

  // Check if a decision is an error/failed entry
  const isErrorDecision = (dec: any): boolean => {
    const reasoning = (dec.reasoning || dec.error || '').toLowerCase();
    const errorPatterns = [
      'failed',
      'error',
      'timeout',
      'context deadline exceeded',
      'unable to',
      'could not',
    ];
    return (
      errorPatterns.some(pattern => reasoning.includes(pattern)) ||
      ((!dec.confidence || dec.confidence === 0) && (!dec.action || dec.action === 'NONE'))
    );
  };

  const parseDecisions = (decisionsJson: string) => {
    try {
      const parsed = JSON.parse(decisionsJson);
      // Filter out error entries
      return parsed.filter((dec: any) => !isErrorDecision(dec));
    } catch {
      return [];
    }
  };

  if (loading) {
    return <div className="p-8 text-center">Loading...</div>;
  }

  return (
    <div className="p-4 lg:p-6 space-y-4 lg:space-y-6 h-[calc(100vh-4rem)] flex flex-col">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 shrink-0">
        <div className="flex items-center gap-4">
          <h1 className="text-2xl font-bold">Logs</h1>
          <div className="flex bg-slate-800 rounded-lg p-1">
            <button
              onClick={() => setViewMode('decisions')}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${viewMode === 'decisions'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-white'
                }`}
            >
              <Activity size={16} />
              Decisions
            </button>
            <button
              onClick={() => setViewMode('system')}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${viewMode === 'system'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-white'
                }`}
            >
              <Terminal size={16} />
              System
            </button>
          </div>
        </div>

        {viewMode === 'decisions' && (
          <div className="flex items-center gap-4">
            <select
              value={selectedTrader || ''}
              onChange={(e) => setSelectedTrader(e.target.value)}
              className="bg-slate-700 rounded px-3 py-2 text-sm"
            >
              {traders.map((trader) => (
                <option key={trader.id} value={trader.id}>{trader.name}</option>
              ))}
            </select>
            <button
              onClick={loadDecisions}
              className="p-2 hover:bg-slate-700 rounded text-slate-400 hover:text-white"
            >
              <RefreshCw size={20} />
            </button>
          </div>
        )}

        {viewMode === 'system' && (
          <div className="flex items-center gap-2">
            <label className="flex items-center gap-2 text-sm text-slate-300 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={autoScroll}
                onChange={(e) => setAutoScroll(e.target.checked)}
                className="rounded bg-slate-700 border-slate-600 text-blue-600 focus:ring-blue-500"
              />
              Auto-scroll
            </label>
            <button
              onClick={() => setSystemLogs([])}
              className="px-3 py-1.5 text-xs bg-slate-700 hover:bg-slate-600 rounded text-slate-300 transition-colors"
            >
              Clear
            </button>
          </div>
        )}
      </div>

      <div className="flex-1 min-h-0 relative">
        {viewMode === 'decisions' ? (
          <div className="h-full overflow-y-auto pr-2 space-y-4">
            {traders.length === 0 ? (
              <div className="bg-slate-800 rounded-lg p-8 text-center text-slate-400">
                No traders configured. Go to Config to create one.
              </div>
            ) : decisions.length === 0 ? (
              <div className="bg-slate-800 rounded-lg p-8 text-center text-slate-400">
                No decisions recorded yet. Start a trader to generate logs.
              </div>
            ) : (
              decisions.map((decision) => {
                const parsed = parseDecisions(decision.decisions);
                if (parsed.length === 0) return null;
                return (
                  <div key={decision.id} className="bg-slate-800 rounded-lg p-4 transition-colors hover:bg-slate-750">
                    <div className="flex justify-between items-center mb-3">
                      <span className="text-slate-400 text-sm flex items-center gap-2">
                        <FileText size={14} />
                        {new Date(decision.timestamp).toLocaleString()}
                      </span>
                      <span className={`px-2 py-0.5 text-xs rounded font-medium ${decision.executed ? 'bg-green-500/10 text-green-400' : 'bg-slate-600/20 text-slate-400'
                        }`}>
                        {decision.executed ? 'Executed' : 'Skipped'}
                      </span>
                    </div>
                    <div className="space-y-2">
                      {parsed.map((dec: any, i: number) => (
                        <div key={i} className="bg-slate-900/50 rounded p-3 border border-slate-700/50">
                          <div className="flex justify-between items-center mb-2">
                            <span className="font-medium text-slate-200">{dec.symbol}</span>
                            <span className={`px-2 py-0.5 rounded text-xs font-bold ${dec.action === 'BUY' ? 'bg-green-500/20 text-green-400' :
                              dec.action === 'SELL' ? 'bg-red-500/20 text-red-400' :
                                dec.action === 'CLOSE' ? 'bg-yellow-500/20 text-yellow-400' :
                                  'bg-slate-600/20 text-slate-400'
                              }`}>
                              {dec.action}
                            </span>
                          </div>
                          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs text-slate-400">
                            <span title="Confidence">Conf: <span className="text-slate-300">{dec.confidence}%</span></span>
                            {dec.entry_price && <span title="Entry Price">Entry: <span className="text-slate-300">${dec.entry_price}</span></span>}
                            {dec.stop_loss && <span title="Stop Loss" className="text-red-400/80">SL: ${dec.stop_loss}</span>}
                            {dec.take_profit && <span title="Take Profit" className="text-green-400/80">TP: ${dec.take_profit}</span>}
                          </div>
                          {dec.reasoning && (
                            <p className="text-sm text-slate-400 mt-2 leading-relaxed border-t border-slate-700/50 pt-2">{dec.reasoning}</p>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })
            )}
          </div>
        ) : (
          <div className="h-full bg-[#0d1117] rounded-lg border border-slate-800 flex flex-col font-mono text-sm overflow-hidden shadow-inner">
            <div className="flex-1 overflow-y-auto p-4 space-y-1 scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-transparent">
              {systemLogs.length === 0 ? (
                <div className="text-slate-500 italic text-center mt-10">Waiting for system logs...</div>
              ) : (
                systemLogs.map((log, i) => {
                  const msg = log.message.toLowerCase();
                  let textColor = 'text-slate-300';

                  if (/(error|fail|failed|panic|fatal|exception|timeout)/.test(msg)) {
                    textColor = 'text-red-400 font-medium';
                  } else if (/(warn|warning)/.test(msg)) {
                    textColor = 'text-yellow-400';
                  } else if (/(success|started|connected)/.test(msg)) {
                    textColor = 'text-green-400';
                  }

                  return (
                    <div key={i} className="flex gap-3 hover:bg-slate-800/50 px-2 py-0.5 rounded -mx-2">
                      <span className="text-slate-500 shrink-0 select-none">
                        {new Date(log.timestamp).toLocaleTimeString()}
                      </span>
                      <span className={`${textColor} break-all whitespace-pre-wrap`}>{log.message}</span>
                    </div>
                  );
                })
              )}
              {/* Dummy element for auto-scrolling */}
              <div ref={logsEndRef} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
