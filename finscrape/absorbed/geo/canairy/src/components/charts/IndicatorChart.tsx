import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  RadialLinearScale,
  TimeScale,
} from 'chart.js';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import { IndicatorData } from '../../types';
import { format } from 'date-fns';
import 'chartjs-adapter-date-fns';
import { generateHistoricalData as generateSeededHistoricalData } from '../../utils/historicalDataGenerator';
import { formatUnit } from '../../data/indicatorDisplay';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  RadialLinearScale,
  TimeScale
);

interface IndicatorChartProps {
  indicator: IndicatorData;
  timeRange?: '24h' | '7d' | '30d' | '90d';
  height?: number;
  className?: string;
}

export const IndicatorChart: React.FC<IndicatorChartProps> = ({
  indicator,
  timeRange = '24h',
  height = 100,
  className
}) => {
  // Chart colors based on indicator status
  const getStatusColor = (level: string, alpha: number = 1) => {
    switch (level) {
      case 'green': return `rgba(16, 185, 129, ${alpha})`;
      case 'amber': return `rgba(245, 158, 11, ${alpha})`;
      case 'red': return `rgba(239, 68, 68, ${alpha})`;
      default: return `rgba(156, 163, 175, ${alpha})`;
    }
  };

  // Use seeded historical data generator for deterministic results
  const historicalData = indicator.history || generateSeededHistoricalData(indicator, timeRange);

  // Get chart type based on indicator
  const getChartType = () => {
    switch (indicator.id) {
      case 'ice_detention_surge':
        return 'gauge';
      case 'dhs_removal_expansion':
      case 'nato_high_readiness':
        return 'binary';
      case 'global_conflict_intensity':
        return 'heatmap';
      case 'market_01_intraday_swing':
      case 'econ_01_treasury_tail':
        return 'area';
      case 'oil_01_russian_brics':
      case 'oil_02_mbridge_settlements':
      case 'job_01_strike_days':
        return 'bar';
      case 'oil_04_refinery_ratio':
        return 'area-threshold';
      default:
        return 'line';
    }
  };

  const chartType = getChartType();

  // Common chart options
  const commonOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        backgroundColor: 'rgba(20, 20, 22, 0.95)',
        titleColor: '#fff',
        bodyColor: 'rgba(255,255,255,0.3)',
        borderColor: 'rgba(255,255,255,0.06)',
        borderWidth: 1,
        padding: 8,
        displayColors: false,
        callbacks: {
          label: (context: any) => {
            const value = context.parsed.y || context.parsed;
            const unit = formatUnit(indicator.unit);
            return `${value.toFixed(2)}${unit}`;
          }
        }
      },
    },
  };

  // Render gauge chart for capacity indicators
  if (chartType === 'gauge' && typeof indicator.status.value === 'number') {
    const value = indicator.status.value;
    const remaining = 100 - value;
    
    const data = {
      datasets: [{
        data: [value, remaining],
        backgroundColor: [
          getStatusColor(indicator.status.level),
          'rgba(26, 26, 26, 0.3)'
        ],
        borderWidth: 0,
      }],
    };

    const gaugeOptions = {
      ...commonOptions,
      cutout: '75%',
      rotation: -90,
      circumference: 180,
      plugins: {
        ...commonOptions.plugins,
        tooltip: {
          enabled: false
        }
      }
    };

    return (
      <div className={className} style={{ height, position: 'relative' }}>
        <Doughnut data={data} options={gaugeOptions} />
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center mt-8">
            <div className="text-2xl font-bold text-white">{value}%</div>
            <div className="text-xs text-white/30">Capacity</div>
          </div>
        </div>
      </div>
    );
  }

  // Render binary state chart for zone indicators
  if (chartType === 'binary') {
    const data = {
      labels: historicalData.map(d => format(new Date(d.timestamp), timeRange === '24h' ? 'HH:mm' : 'MMM dd')),
      datasets: [{
        label: indicator.name,
        data: historicalData.map(d => d.value > 0 ? 1 : 0),
        borderColor: getStatusColor(indicator.status.level),
        backgroundColor: getStatusColor(indicator.status.level, 0.1),
        stepped: true,
        fill: true,
      }],
    };

    const binaryOptions = {
      ...commonOptions,
      scales: {
        y: {
          min: 0,
          max: 1,
          ticks: {
            stepSize: 1,
            callback: (value: any) => value === 1 ? 'Active' : 'Inactive',
            color: 'rgba(255,255,255,0.2)',
          },
          grid: {
            color: 'rgba(255, 255, 255, 0.04)',
          }
        },
        x: {
          ticks: {
            color: 'rgba(255,255,255,0.2)',
            maxRotation: 0,
          },
          grid: {
            display: false,
          }
        }
      }
    };

    return (
      <div className={className} style={{ height }}>
        <Line data={data} options={binaryOptions} />
      </div>
    );
  }

  // Render area chart for volatility indicators
  if (chartType === 'area') {
    const data = {
      labels: historicalData.map(d => format(new Date(d.timestamp), timeRange === '24h' ? 'HH:mm' : 'MMM dd')),
      datasets: [{
        label: indicator.name,
        data: historicalData.map(d => d.value),
        borderColor: getStatusColor(indicator.status.level),
        backgroundColor: getStatusColor(indicator.status.level, 0.2),
        fill: true,
        tension: 0.4,
      }],
    };

    // Add threshold lines
    const thresholdDatasets: any[] = [];
    const chartAmberThreshold = indicator.thresholds?.threshold_amber;
    const chartRedThreshold = indicator.thresholds?.threshold_red;

    if (chartAmberThreshold !== undefined) {
      thresholdDatasets.push({
        label: 'Amber Threshold',
        data: Array(historicalData.length).fill(chartAmberThreshold),
        borderColor: getStatusColor('amber', 0.5),
        borderDash: [5, 5],
        pointRadius: 0,
        fill: false,
      });
    }
    if (chartRedThreshold !== undefined) {
      thresholdDatasets.push({
        label: 'Red Threshold',
        data: Array(historicalData.length).fill(chartRedThreshold),
        borderColor: getStatusColor('red', 0.5),
        borderDash: [5, 5],
        pointRadius: 0,
        fill: false,
      });
    }

    data.datasets.push(...thresholdDatasets);

    const areaOptions = {
      ...commonOptions,
      scales: {
        y: {
          ticks: {
            color: 'rgba(255,255,255,0.2)',
          },
          grid: {
            color: 'rgba(255, 255, 255, 0.04)',
          }
        },
        x: {
          ticks: {
            color: 'rgba(255,255,255,0.2)',
            maxRotation: 0,
          },
          grid: {
            display: false,
          }
        }
      }
    };

    return (
      <div className={className} style={{ height }}>
        <Line data={data} options={areaOptions} />
      </div>
    );
  }

  // Render bar chart for certain indicators
  if (chartType === 'bar') {
    const data = {
      labels: historicalData.slice(-10).map(d => format(new Date(d.timestamp), timeRange === '24h' ? 'HH:mm' : 'MMM dd')),
      datasets: [{
        label: indicator.name,
        data: historicalData.slice(-10).map(d => d.value),
        backgroundColor: historicalData.slice(-10).map(d => getStatusColor(d.level, 0.7)),
        borderColor: historicalData.slice(-10).map(d => getStatusColor(d.level)),
        borderWidth: 1,
      }],
    };

    const barOptions = {
      ...commonOptions,
      scales: {
        y: {
          ticks: {
            color: 'rgba(255,255,255,0.2)',
            callback: (value: any) => {
              if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
              if (value >= 1000) return `${(value / 1000).toFixed(1)}K`;
              if (Number.isInteger(value)) return value;
              return value.toFixed(1);
            },
          },
          grid: {
            color: 'rgba(255, 255, 255, 0.04)',
          }
        },
        x: {
          ticks: {
            color: 'rgba(255,255,255,0.2)',
          },
          grid: {
            display: false,
          }
        }
      }
    };

    return (
      <div className={className} style={{ height }}>
        <Bar data={data} options={barOptions} />
      </div>
    );
  }

  // Render area chart with threshold zones
  if (chartType === 'area-threshold') {
    const data = {
      labels: historicalData.map(d => format(new Date(d.timestamp), timeRange === '24h' ? 'HH:mm' : 'MMM dd')),
      datasets: [
        {
          label: indicator.name,
          data: historicalData.map(d => d.value),
          borderColor: getStatusColor(indicator.status.level),
          backgroundColor: getStatusColor(indicator.status.level, 0.2),
          fill: true,
          tension: 0.4,
        }
      ],
    };

    // Add colored zones for thresholds
    const areaAmberThreshold = indicator.thresholds?.threshold_amber;
    const areaRedThreshold = indicator.thresholds?.threshold_red;

    if (areaRedThreshold !== undefined && areaAmberThreshold !== undefined) {
      data.datasets.unshift({
        label: 'Critical Zone',
        data: Array(historicalData.length).fill(100), // Re-evaluate this '100' if it's not a universal max
        backgroundColor: getStatusColor('red', 0.1),
        fill: '+1',
        pointRadius: 0,
        borderWidth: 0,
      } as any);
      
      data.datasets.unshift({
        label: 'Warning Zone',
        data: Array(historicalData.length).fill(areaRedThreshold),
        backgroundColor: getStatusColor('amber', 0.1),
        fill: '+1',
        pointRadius: 0,
        borderWidth: 0,
      } as any);
      
      data.datasets.unshift({
        label: 'Safe Zone',
        data: Array(historicalData.length).fill(areaAmberThreshold),
        backgroundColor: getStatusColor('green', 0.1),
        fill: 'origin',
        pointRadius: 0,
        borderWidth: 0,
      } as any);
    }

    const areaThresholdOptions = {
      ...commonOptions,
      plugins: {
        ...commonOptions.plugins,
        legend: {
          display: false,
        },
        tooltip: {
          ...commonOptions.plugins.tooltip,
          filter: (item: any) => item.datasetIndex === data.datasets.length - 1,
        }
      },
      scales: {
        y: {
          max: indicator.id === 'oil_04_refinery_ratio' ? 2.0 : undefined,
          ticks: {
            color: 'rgba(255,255,255,0.2)',
            callback: (value: any) => {
              if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
              if (value >= 1000) return `${(value / 1000).toFixed(1)}K`;
              if (Number.isInteger(value)) return value;
              return value.toFixed(1);
            }
          },
          grid: {
            color: 'rgba(255, 255, 255, 0.04)',
          }
        },
        x: {
          ticks: {
            color: 'rgba(255,255,255,0.2)',
            maxRotation: 0,
          },
          grid: {
            display: false,
          }
        }
      }
    };

    return (
      <div className={className} style={{ height }}>
        <Line data={data} options={areaThresholdOptions} />
      </div>
    );
  }

  // Default line chart with threshold lines
  const lineAmberThreshold = indicator.thresholds?.threshold_amber;
  const lineRedThreshold = indicator.thresholds?.threshold_red;

  const data = {
    labels: historicalData.map(d => format(new Date(d.timestamp), timeRange === '24h' ? 'HH:mm' : 'MMM dd')),
    datasets: [
      {
        label: indicator.name,
        data: historicalData.map(d => d.value),
        borderColor: getStatusColor(indicator.status.level),
        backgroundColor: getStatusColor(indicator.status.level, 0.1),
        borderWidth: 2,
        pointRadius: 0,
        pointHoverRadius: 4,
        tension: 0.3,
      },
      // Add amber threshold line if defined
      ...(lineAmberThreshold !== undefined ? [{
        label: 'Amber',
        data: Array(historicalData.length).fill(lineAmberThreshold),
        borderColor: getStatusColor('amber', 0.4),
        borderDash: [4, 4],
        borderWidth: 1,
        pointRadius: 0,
        fill: false,
      }] : []),
      // Add red threshold line if defined
      ...(lineRedThreshold !== undefined ? [{
        label: 'Red',
        data: Array(historicalData.length).fill(lineRedThreshold),
        borderColor: getStatusColor('red', 0.4),
        borderDash: [4, 4],
        borderWidth: 1,
        pointRadius: 0,
        fill: false,
      }] : []),
    ],
  };

  const lineOptions = {
    ...commonOptions,
    scales: {
      y: {
        ticks: {
          color: 'rgba(255,255,255,0.2)',
          // Don't show units on every tick - just clean numbers
          callback: (value: any) => {
            if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
            if (value >= 1000) return `${(value / 1000).toFixed(1)}K`;
            if (Number.isInteger(value)) return value;
            return value.toFixed(1);
          },
        },
        grid: {
          color: 'rgba(255, 255, 255, 0.04)',
        }
      },
      x: {
        ticks: {
          color: 'rgba(255,255,255,0.2)',
          maxRotation: 0,
          autoSkip: true,
          maxTicksLimit: 6,
        },
        grid: {
          display: false,
        }
      }
    }
  };

  return (
    <div className={className} style={{ height }}>
      <Line data={data} options={lineOptions} />
    </div>
  );
};