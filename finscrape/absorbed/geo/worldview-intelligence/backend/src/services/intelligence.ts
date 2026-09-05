import {
  LayerData,
  AnomalyAlert,
  SituationReport,
  ConflictEvent,
  GeoPosition,
} from '../types/index';

function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

function distanceKm(a: GeoPosition, b: GeoPosition): number {
  const R = 6371;
  const dLat = ((b.lat - a.lat) * Math.PI) / 180;
  const dLng = ((b.lng - a.lng) * Math.PI) / 180;
  const sinLat = Math.sin(dLat / 2);
  const sinLng = Math.sin(dLng / 2);
  const h =
    sinLat * sinLat +
    Math.cos((a.lat * Math.PI) / 180) *
      Math.cos((b.lat * Math.PI) / 180) *
      sinLng * sinLng;
  return R * 2 * Math.atan2(Math.sqrt(h), Math.sqrt(1 - h));
}

export function generateSituationReport(
  region: string,
  data: Partial<LayerData>,
): SituationReport {
  const threats: string[] = [];
  const recommendations: string[] = [];
  let escalation = 0;

  const conflicts = data.conflicts || [];
  const earthquakes = data.earthquakes || [];
  const missiles = data.missiles || [];
  const news = data.news || [];

  if (conflicts.length > 0) {
    const redEvents = conflicts.filter((c) => c.severity === 'red');
    const totalFatalities = conflicts.reduce((s, c) => s + c.fatalities, 0);

    if (redEvents.length > 0) {
      threats.push(
        `${redEvents.length} high-severity conflict event(s) detected in ${region}`,
      );
      escalation += redEvents.length * 0.15;
    }
    if (totalFatalities > 50) {
      threats.push(`Significant fatality count: ${totalFatalities}`);
      escalation += 0.1;
    }
    recommendations.push('Monitor conflict zones with increased frequency');
  }

  if (earthquakes.length > 0) {
    const major = earthquakes.filter((e) => e.magnitude >= 6);
    const tsunamiRisk = earthquakes.filter((e) => e.tsunami);
    if (major.length > 0) {
      threats.push(
        `${major.length} major earthquake(s) (M6+) in ${region}`,
      );
      escalation += 0.05;
    }
    if (tsunamiRisk.length > 0) {
      threats.push(`Tsunami warning issued for ${tsunamiRisk.length} event(s)`);
      recommendations.push('Issue coastal evacuation advisories');
    }
  }

  if (missiles.length > 0) {
    threats.push(`${missiles.length} missile/launch event(s) detected`);
    escalation += missiles.length * 0.2;
    recommendations.push('Activate air-defense monitoring protocols');
  }

  const negativeNews = news.filter((n) => n.sentiment < -0.3);
  if (negativeNews.length > 3) {
    threats.push(
      `Elevated negative sentiment across ${negativeNews.length} news reports`,
    );
    escalation += 0.05;
  }

  if (recommendations.length === 0) {
    recommendations.push('Continue standard monitoring procedures');
  }

  const summaryParts = [
    `Situation report for ${region} generated at ${new Date().toISOString()}.`,
  ];
  if (threats.length === 0) {
    summaryParts.push('No significant threats detected at this time.');
  } else {
    summaryParts.push(
      `${threats.length} threat indicator(s) identified. Escalation probability: ${Math.round(Math.min(escalation, 1) * 100)}%.`,
    );
  }

  return {
    id: generateId(),
    region,
    summary: summaryParts.join(' '),
    threats,
    escalationProbability: Math.min(escalation, 1),
    recommendations,
    timestamp: Date.now(),
  };
}

export function detectAnomalies(
  currentData: Partial<LayerData>,
  previousData: Partial<LayerData>,
): AnomalyAlert[] {
  const alerts: AnomalyAlert[] = [];

  const curAircraft = currentData.aircraft || [];
  const prevAircraft = previousData.aircraft || [];
  if (prevAircraft.length > 0) {
    const ratio = curAircraft.length / prevAircraft.length;
    if (ratio > 1.5 && curAircraft.length - prevAircraft.length > 20) {
      const center = curAircraft.reduce(
        (acc, a) => ({
          lat: acc.lat + a.position.lat / curAircraft.length,
          lng: acc.lng + a.position.lng / curAircraft.length,
        }),
        { lat: 0, lng: 0 },
      );
      alerts.push({
        id: generateId(),
        type: 'aircraft_surge',
        severity: ratio > 2 ? 'high' : 'medium',
        title: 'Sudden aircraft increase detected',
        description: `Aircraft count jumped from ${prevAircraft.length} to ${curAircraft.length} (${Math.round((ratio - 1) * 100)}% increase)`,
        position: center,
        relatedEntities: curAircraft.slice(0, 5).map((a) => a.callsign),
        timestamp: Date.now(),
      });
    }
  }

  const curQuakes = currentData.earthquakes || [];
  const prevQuakes = previousData.earthquakes || [];
  const newQuakeIds = new Set(prevQuakes.map((q) => q.id));
  const freshQuakes = curQuakes.filter((q) => !newQuakeIds.has(q.id));
  if (freshQuakes.length >= 3) {
    const clustered = freshQuakes.filter((q) =>
      freshQuakes.some(
        (other) =>
          q.id !== other.id && distanceKm(q.position, other.position) < 200,
      ),
    );
    if (clustered.length >= 3) {
      const center = clustered.reduce(
        (acc, q) => ({
          lat: acc.lat + q.position.lat / clustered.length,
          lng: acc.lng + q.position.lng / clustered.length,
        }),
        { lat: 0, lng: 0 },
      );
      alerts.push({
        id: generateId(),
        type: 'earthquake_cluster',
        severity: clustered.some((q) => q.magnitude >= 6) ? 'critical' : 'high',
        title: 'Earthquake cluster detected',
        description: `${clustered.length} earthquakes within 200 km radius. Max magnitude: ${Math.max(...clustered.map((q) => q.magnitude)).toFixed(1)}`,
        position: center,
        relatedEntities: clustered.map((q) => q.id),
        timestamp: Date.now(),
      });
    }
  }

  const curConflicts = currentData.conflicts || [];
  const prevConflicts = previousData.conflicts || [];
  const prevConflictIds = new Set(prevConflicts.map((c) => c.id));
  const newConflicts = curConflicts.filter((c) => !prevConflictIds.has(c.id));
  const redEscalations = newConflicts.filter((c) => c.severity === 'red');
  if (redEscalations.length >= 2) {
    const center = redEscalations.reduce(
      (acc, c) => ({
        lat: acc.lat + c.position.lat / redEscalations.length,
        lng: acc.lng + c.position.lng / redEscalations.length,
      }),
      { lat: 0, lng: 0 },
    );
    alerts.push({
      id: generateId(),
      type: 'conflict_escalation',
      severity: 'critical',
      title: 'Conflict escalation detected',
      description: `${redEscalations.length} new high-severity conflict events in ${redEscalations[0].region}`,
      position: center,
      relatedEntities: redEscalations.map((c) => c.id),
      timestamp: Date.now(),
    });
  }

  return alerts;
}

export function predictEscalation(conflictEvents: ConflictEvent[]): number {
  if (conflictEvents.length === 0) return 0;

  let probability = 0;

  const redCount = conflictEvents.filter((c) => c.severity === 'red').length;
  const orangeCount = conflictEvents.filter((c) => c.severity === 'orange').length;
  probability += redCount * 0.15 + orangeCount * 0.05;

  const totalFatalities = conflictEvents.reduce((s, c) => s + c.fatalities, 0);
  if (totalFatalities > 100) probability += 0.15;
  else if (totalFatalities > 20) probability += 0.08;

  const battles = conflictEvents.filter((c) => c.eventType === 'battle').length;
  const explosions = conflictEvents.filter((c) => c.eventType === 'explosion').length;
  probability += (battles + explosions) * 0.04;

  const now = Date.now();
  const recentWindow = 24 * 60 * 60 * 1000;
  const recent = conflictEvents.filter((c) => now - c.timestamp < recentWindow);
  if (recent.length > conflictEvents.length * 0.6 && conflictEvents.length > 5) {
    probability += 0.1;
  }

  const regions = new Set(conflictEvents.map((c) => c.region));
  if (regions.size >= 3 && conflictEvents.length > 10) {
    probability += 0.1;
  }

  return Math.min(probability, 1);
}
