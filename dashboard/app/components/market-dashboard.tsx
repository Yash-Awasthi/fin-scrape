import { useEffect, useState } from 'react';

interface Stock {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  sparkline: number[];
}

const mockStocks: Stock[] = [
  { symbol: 'AAPL', name: 'Apple Inc.', price: 178.52, change: 2.34, changePercent: 1.33, sparkline: [170, 172, 175, 173, 176, 178, 177, 179, 178, 178.52] },
  { symbol: 'GOOGL', name: 'Alphabet Inc.', price: 141.80, change: -0.92, changePercent: -0.64, sparkline: [145, 144, 143, 142, 141, 140, 141, 142, 141, 141.80] },
  { symbol: 'MSFT', name: 'Microsoft Corp.', price: 378.91, change: 4.12, changePercent: 1.10, sparkline: [370, 372, 375, 374, 376, 378, 377, 379, 378, 378.91] },
  { symbol: 'AMZN', name: 'Amazon.com Inc.', price: 178.25, change: 1.87, changePercent: 1.06, sparkline: [172, 174, 176, 175, 177, 178, 177, 179, 178, 178.25] },
  { symbol: 'NVDA', name: 'NVIDIA Corp.', price: 875.28, change: 12.45, changePercent: 1.44, sparkline: [850, 855, 860, 858, 865, 870, 868, 875, 873, 875.28] },
];

function Sparkline({ data, positive }: { data: number[]; positive: boolean }) {
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  
  const points = data.map((value, index) => {
    const x = (index / (data.length - 1)) * 60;
    const y = 20 - ((value - min) / range) * 16;
    return `${x},${y}`;
  }).join(' ');

  return (
    <svg width="60" height="20" className="inline-block">
      <polyline
        points={points}
        fill="none"
        stroke={positive ? 'var(--green, #22c55e)' : 'var(--destructive, #ef4444)'}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function MarketDashboard() {
  const [stocks, setStocks] = useState<Stock[]>(mockStocks);

  // Simulate live updates
  useEffect(() => {
    const interval = setInterval(() => {
      setStocks(prev => prev.map(stock => {
        const delta = (Math.random() - 0.5) * 2;
        const newPrice = Math.max(0, stock.price + delta);
        const newChange = newPrice - stock.price;
        const newChangePercent = (newChange / stock.price) * 100;
        
        return {
          ...stock,
          price: newPrice,
          change: newChange,
          changePercent: newChangePercent,
          sparkline: [...stock.sparkline.slice(1), newPrice],
        };
      }));
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6">
      {/* Portfolio Summary */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-lg border bg-card p-4">
          <p className="text-xs font-medium text-muted-foreground">Total Value</p>
          <p className="text-2xl font-bold">$124,532.00</p>
          <p className="text-xs text-green-500">+$2,341.20 (1.91%)</p>
        </div>
        <div className="rounded-lg border bg-card p-4">
          <p className="text-xs font-medium text-muted-foreground">Day Change</p>
          <p className="text-2xl font-bold text-green-500">+$1,234.56</p>
          <p className="text-xs text-muted-foreground">+0.99%</p>
        </div>
        <div className="rounded-lg border bg-card p-4">
          <p className="text-xs font-medium text-muted-foreground">Positions</p>
          <p className="text-2xl font-bold">5</p>
          <p className="text-xs text-muted-foreground">3 winners, 2 losers</p>
        </div>
        <div className="rounded-lg border bg-card p-4">
          <p className="text-xs font-medium text-muted-foreground">Cash Balance</p>
          <p className="text-2xl font-bold">$12,450.00</p>
          <p className="text-xs text-muted-foreground">Available to trade</p>
        </div>
      </div>

      {/* Watchlist */}
      <div className="rounded-lg border bg-card">
        <div className="border-b p-4">
          <h3 className="font-semibold">Watchlist</h3>
        </div>
        <div className="divide-y">
          {stocks.map((stock) => (
            <div key={stock.symbol} className="flex items-center justify-between p-4 hover:bg-muted/50 transition-colors">
              <div className="flex items-center gap-4">
                <div className="h-10 w-10 rounded-full bg-muted flex items-center justify-center text-sm font-bold">
                  {stock.symbol.slice(0, 2)}
                </div>
                <div>
                  <p className="font-medium">{stock.symbol}</p>
                  <p className="text-xs text-muted-foreground">{stock.name}</p>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <Sparkline data={stock.sparkline} positive={stock.change >= 0} />
                <div className="text-right">
                  <p className="font-mono font-medium">${stock.price.toFixed(2)}</p>
                  <p className={`text-xs font-mono ${stock.change >= 0 ? 'text-green-500' : 'text-destructive'}`}>
                    {stock.change >= 0 ? '+' : ''}{stock.change.toFixed(2)} ({stock.changePercent.toFixed(2)}%)
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
