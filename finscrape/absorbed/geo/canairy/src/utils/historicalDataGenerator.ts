import { DataPoint, IndicatorData } from '../types';
import { subHours, subDays } from 'date-fns';

interface GeneratorConfig {
  baseValue: number;
  volatility: number;
  trend: number;
  seasonality?: {
    period: number; // hours or days
    amplitude: number;
  };
  events?: {
    timestamp: Date;
    impact: number;
    duration: number; // hours or days
  }[];
}

// Indicator-specific configurations
const indicatorConfigs: Record<string, GeneratorConfig> = {
  treasury_tail: {
    baseValue: 2.5,
    volatility: 0.3,
    trend: 0.01,
    seasonality: {
      period: 24,
      amplitude: 0.2
    }
  },
  ice_detention: {
    baseValue: 75,
    volatility: 2,
    trend: 0.1,
    events: [
      {
        timestamp: subDays(new Date(), 5),
        impact: 15,
        duration: 48
      }
    ]
  },
  taiwan_zone: {
    baseValue: 0,
    volatility: 0,
    trend: 0,
    events: [
      {
        timestamp: subDays(new Date(), 3),
        impact: 2,
        duration: 12
      },
      {
        timestamp: subDays(new Date(), 10),
        impact: 1,
        duration: 24
      }
    ]
  },
  hormuz_war_risk: {
    baseValue: 0.025,
    volatility: 0.005,
    trend: 0.0001,
    seasonality: {
      period: 168, // weekly
      amplitude: 0.003
    }
  },
  vix_volatility: {
    baseValue: 20,
    volatility: 3,
    trend: 0.05,
    seasonality: {
      period: 24,
      amplitude: 2
    }
  },
  unemployment_rate: {
    baseValue: 4.5,
    volatility: 0.1,
    trend: 0.02,
    seasonality: {
      period: 720, // monthly
      amplitude: 0.2
    }
  },
  global_conflict_index: {
    baseValue: 65,
    volatility: 5,
    trend: 0.2,
    events: [
      {
        timestamp: subDays(new Date(), 7),
        impact: 20,
        duration: 72
      }
    ]
  },
  mbridge_settlement: {
    baseValue: 15,
    volatility: 2,
    trend: 0.5,
    seasonality: {
      period: 168,
      amplitude: 3
    }
  }
};

export function generateHistoricalData(
  indicator: IndicatorData,
  timeRange: '24h' | '7d' | '30d' | '90d' = '24h'
): DataPoint[] {
  const config = indicatorConfigs[indicator.id] || {
    baseValue: typeof indicator.status.value === 'number' ? indicator.status.value : 50,
    volatility: 5,
    trend: 0
  };

  const now = new Date();
  const points: DataPoint[] = [];
  
  // Determine time parameters
  let startTime: Date;
  let stepSize: number; // in milliseconds
  let totalSteps: number;
  
  switch (timeRange) {
    case '24h':
      startTime = subHours(now, 24);
      stepSize = 3600000; // 1 hour
      totalSteps = 24;
      break;
    case '7d':
      startTime = subDays(now, 7);
      stepSize = 3600000 * 4; // 4 hours
      totalSteps = 42;
      break;
    case '30d':
      startTime = subDays(now, 30);
      stepSize = 86400000; // 1 day
      totalSteps = 30;
      break;
    case '90d':
      startTime = subDays(now, 90);
      stepSize = 86400000; // 1 day
      totalSteps = 90;
      break;
  }

  let currentValue = config.baseValue;
  const random = seedRandom(indicator.id);

  for (let i = 0; i <= totalSteps; i++) {
    const timestamp = new Date(startTime.getTime() + i * stepSize);
    
    // Base random walk
    const randomChange = (random() - 0.5) * config.volatility;
    
    // Add trend
    const trendChange = config.trend * (i / totalSteps);
    
    // Add seasonality
    let seasonalChange = 0;
    if (config.seasonality) {
      const phase = (i % config.seasonality.period) / config.seasonality.period;
      seasonalChange = Math.sin(2 * Math.PI * phase) * config.seasonality.amplitude;
    }
    
    // Check for events
    let eventImpact = 0;
    if (config.events) {
      for (const event of config.events) {
        const timeSinceEvent = timestamp.getTime() - event.timestamp.getTime();
        const eventDurationMs = event.duration * 3600000;
        if (timeSinceEvent >= 0 && timeSinceEvent <= eventDurationMs) {
          const progress = timeSinceEvent / eventDurationMs;
          eventImpact += event.impact * (1 - progress); // Decay over time
        }
      }
    }
    
    // Calculate final value
    currentValue = Math.max(0, currentValue + randomChange + trendChange + seasonalChange + eventImpact);
    
    // For binary indicators, convert to 0 or 1
    if (indicator.id === 'taiwan_zone') {
      currentValue = currentValue > 0.5 ? Math.floor(currentValue) : 0;
    }
    
    // Determine alert level based on thresholds
    let level: 'green' | 'amber' | 'red' = 'green';
    const redThreshold = indicator.thresholds?.threshold_red;
    const amberThreshold = indicator.thresholds?.threshold_amber;

    if (redThreshold !== undefined && currentValue >= redThreshold) {
      level = 'red';
    } else if (amberThreshold !== undefined && currentValue >= amberThreshold) {
      level = 'amber';
    }
    
    // For greenFlag indicators, invert the logic
    if (indicator.greenFlag) {
          const redThresholdMax = indicator.thresholds?.threshold_red; // Assuming max is also threshold_red for greenFlag
          const amberThresholdMax = indicator.thresholds?.threshold_amber; // Assuming max is also threshold_amber for greenFlag

          if (redThresholdMax !== undefined && currentValue <= redThresholdMax) {
            level = 'red';
          } else if (amberThresholdMax !== undefined && currentValue <= amberThresholdMax) {
            level = 'amber';
          }
        }
    
    points.push({
      timestamp: timestamp.toISOString(),
      value: parseFloat(currentValue.toFixed(2)),
      level
    });
  }
  
  // Ensure the last point matches current status
  if (points.length > 0 && typeof indicator.status.value === 'number') {
    points[points.length - 1].value = indicator.status.value;
    points[points.length - 1].level = indicator.status.level as 'green' | 'amber' | 'red';
  }
  
  return points;
}

// Seeded random number generator for consistent results
function seedRandom(seed: string): () => number {
  let hash = 0;
  for (let i = 0; i < seed.length; i++) {
    const char = seed.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash;
  }
  
  return function() {
    hash = (hash * 9301 + 49297) % 233280;
    return hash / 233280;
  };
}