/**
 * 共享 Recharts 图表组件
 * 提供项目统一风格的图表封装
 */
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
  LineChart, Line, CartesianGrid,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ScatterChart, Scatter, ReferenceLine,
} from 'recharts'

const COLORS = [
  '#6366f1', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6',
  '#06b6d4', '#f97316', '#ec4899', '#14b8a6', '#a855f7',
]

const CHART_MARGINS = { top: 8, right: 16, left: 8, bottom: 8 }

interface BarData { name: string; value: number; color?: string }

export function SimpleBarChart({ data, height = 200 }: {
  data: BarData[]; height?: number; showLabels?: boolean
}) {
  if (!data.length) return null
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={CHART_MARGINS}>
        <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} />
        <YAxis tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} width={32} />
        <Tooltip
          contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8, fontSize: 12 }}
          labelStyle={{ color: '#e2e8f0' }}
          itemStyle={{ color: '#94a3b8' }}
        />
        <Bar dataKey="value" radius={[4, 4, 0, 0]}>
          {data.map((entry, i) => (
            <Cell key={i} fill={entry.color || COLORS[i % COLORS.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

interface PieData { name: string; value: number; color?: string }

export function SimplePieChart({ data, height = 220, innerRadius = 50 }: {
  data: PieData[]; height?: number; innerRadius?: number
}) {
  if (!data.length) return null
  return (
    <ResponsiveContainer width="100%" height={height}>
      <PieChart margin={CHART_MARGINS}>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={innerRadius}
          outerRadius={innerRadius + 35}
          paddingAngle={2}
          dataKey="value"
          stroke="none"
        >
          {data.map((entry, i) => (
            <Cell key={i} fill={entry.color || COLORS[i % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8, fontSize: 12 }}
          itemStyle={{ color: '#94a3b8' }}
        />
        <Legend
          wrapperStyle={{ fontSize: 11, color: '#94a3b8' }}
          formatter={(value: string) => <span style={{ color: '#94a3b8' }}>{value}</span>}
        />
      </PieChart>
    </ResponsiveContainer>
  )
}

interface LineData { name: string; [key: string]: string | number }

export function SimpleLineChart({ data, lines, height = 200 }: {
  data: LineData[]; lines: { key: string; color: string; name: string }[]; height?: number
}) {
  if (!data.length) return null
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={CHART_MARGINS}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
        <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 11 }} axisLine={false} tickLine={false} />
        <YAxis tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} width={32} />
        <Tooltip
          contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8, fontSize: 12 }}
          labelStyle={{ color: '#e2e8f0' }}
        />
        {lines.map(l => (
          <Line key={l.key} type="monotone" dataKey={l.key} stroke={l.color} name={l.name}
                strokeWidth={2} dot={{ r: 3, fill: l.color }} />
        ))}
      </LineChart>
    </ResponsiveContainer>
  )
}

interface RadarData { dimension: string; [key: string]: string | number }

export function SimpleRadarChart({ data, dataKey, name, height = 260 }: {
  data: RadarData[]; dataKey: string; name: string; height?: number
}) {
  if (!data.length) return null
  return (
    <ResponsiveContainer width="100%" height={height}>
      <RadarChart data={data} margin={CHART_MARGINS}>
        <PolarGrid stroke="#334155" />
        <PolarAngleAxis dataKey="dimension" tick={{ fill: '#94a3b8', fontSize: 10 }} />
        <PolarRadiusAxis tick={{ fill: '#64748b', fontSize: 9 }} />
        <Radar name={name} dataKey={dataKey} stroke="#6366f1" fill="#6366f1" fillOpacity={0.2} />
        <Tooltip
          contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8, fontSize: 12 }}
        />
      </RadarChart>
    </ResponsiveContainer>
  )
}

interface CalibrationBin {
  bin: string
  predicted: number
  actual: number
  count: number
}

export function CalibrationCurve({ data, height = 280 }: {
  data: CalibrationBin[]; height?: number
}) {
  if (!data.length) return null

  const scatterData = data.map((d) => ({
    x: d.predicted,
    y: d.actual,
    count: d.count,
    bin: d.bin,
  }))

  return (
    <ResponsiveContainer width="100%" height={height}>
      <ScatterChart margin={{ top: 16, right: 16, left: 8, bottom: 16 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
        <XAxis
          type="number"
          dataKey="x"
          domain={[0, 1]}
          tick={{ fill: '#94a3b8', fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          label={{ value: 'Predicted Probability', position: 'insideBottom', offset: -4, fill: '#64748b', fontSize: 11 }}
        />
        <YAxis
          type="number"
          dataKey="y"
          domain={[0, 1]}
          tick={{ fill: '#64748b', fontSize: 10 }}
          axisLine={false}
          tickLine={false}
          width={36}
          label={{ value: 'Actual Frequency', angle: -90, position: 'insideLeft', offset: 8, fill: '#64748b', fontSize: 11 }}
        />
        <ReferenceLine
          segment={[{ x: 0, y: 0 }, { x: 1, y: 1 }]}
          stroke="#475569"
          strokeDasharray="6 3"
          label={{ value: 'Perfect', position: 'insideTopRight', fill: '#475569', fontSize: 10, offset: 4 }}
        />
        <Tooltip
          contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8, fontSize: 12 }}
          formatter={(value: unknown, name: unknown) => {
            const v = typeof value === 'number' ? value : 0
            const n = String(name ?? '')
            if (n === 'x') return [`${(v * 100).toFixed(0)}%`, 'Predicted']
            if (n === 'y') return [`${(v * 100).toFixed(0)}%`, 'Actual']
            return [v, n]
          }}
          labelFormatter={(_, payload) => {
            if (payload?.[0]?.payload) {
              const p = payload[0].payload as CalibrationBin
              return `${p.bin} (${p.count} predictions)`
            }
            return ''
          }}
        />
        <Scatter
          data={scatterData}
          fill="#6366f1"
          shape={(props: { cx?: number; cy?: number; count?: number }) => {
            const { cx = 0, cy = 0, count = 1 } = props
            const r = Math.max(4, Math.min(12, 3 + count * 0.8))
            return <circle cx={cx} cy={cy} r={r} fill="#6366f1" fillOpacity={0.7} stroke="#818cf8" strokeWidth={1.5} />
          }}
        />
      </ScatterChart>
    </ResponsiveContainer>
  )
}
