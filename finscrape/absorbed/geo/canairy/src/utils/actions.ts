import {
  Package,
  DollarSign,
  Zap,
  Shield,
  Users,
} from 'lucide-react';
import { IndicatorData, Phase } from '../types';

export interface DetailedAction {
  id: string;
  category: string;
  title: string;
  why: string;
  steps: string[];
  urgency: 'immediate' | 'today' | 'this-week';
  icon: React.ComponentType<any>;
  resources?: {
    type: 'phone' | 'link' | 'checklist';
    label: string;
    value: string;
  }[];
  impact: string;
  timeRequired: string;
}

export function generateDetailedActions(
  indicators: IndicatorData[],
  currentPhase: Phase | null,
): DetailedAction[] {
  const actions: DetailedAction[] = [];
  const redIndicators = indicators.filter(i => i.status.level === 'red');
  const criticalReds = redIndicators.filter(i => i.critical);

  // Financial Protection Actions
  if (redIndicators.some(i => i.id === 'econ_01_treasury_tail' || i.id === 'market_01_intraday_swing')) {
    const treasuryRed = redIndicators.find(i => i.id === 'econ_01_treasury_tail' || i.id === 'market_01_intraday_swing');
    actions.push({
      id: 'finance-1',
      category: 'Financial',
      title: 'Secure Bank Deposits NOW',
      why: treasuryRed?.critical
        ? 'Banking system showing severe stress — protect your money before potential bank runs'
        : 'Treasury markets unstable — banks may restrict access to funds',
      steps: [
        'Check all bank account balances immediately',
        'Move amounts over $250,000 to different FDIC-insured banks',
        'Withdraw 2 weeks of cash (small bills preferred)',
        'Screenshot all account balances for records'
      ],
      urgency: treasuryRed?.critical ? 'immediate' : 'today',
      icon: DollarSign,
      resources: [
        { type: 'phone', label: 'FDIC Hotline', value: '1-877-275-3342' },
        { type: 'link', label: 'Check FDIC Coverage', value: 'https://www.fdic.gov/edie/' }
      ],
      impact: 'Protects life savings from bank failures',
      timeRequired: '2-3 hours'
    });
  }

  // Supply Chain Actions
  if (redIndicators.some(i => i.id === 'taiwan_pla_activity' || i.domain === 'oil_axis')) {
    const urgencyLevel = criticalReds.length > 0 ? 'immediate' : 'today';
    actions.push({
      id: 'supply-1',
      category: 'Supplies',
      title: 'Stock Critical Items Before Shortages',
      why: 'Supply chain disruptions imminent — prices will spike 20-40% within days',
      steps: [
        'Fill all vehicles with gas TODAY',
        'Buy 2-week supply of shelf-stable food',
        'Stock critical medications (90-day supply if possible)',
        'Purchase backup electronics/batteries now',
        'Get cash from ATM (small bills)'
      ],
      urgency: urgencyLevel,
      icon: Package,
      resources: [
        { type: 'checklist', label: 'Emergency Supply List', value: 'food,water,meds,batteries,radio,cash' },
        { type: 'phone', label: 'Pharmacy Refill', value: 'Call your pharmacy' }
      ],
      impact: 'Avoids panic buying and price spikes',
      timeRequired: '3-4 hours today'
    });
  }

  // Energy/Power Actions
  if (redIndicators.some(i => i.domain === 'oil_axis' || i.id === 'grid_01_pjm_outages') || redIndicators.length >= 2) {
    actions.push({
      id: 'energy-1',
      category: 'Energy',
      title: 'Prepare for Power Disruptions',
      why: 'Grid instability detected — rolling blackouts possible',
      steps: [
        'Test backup power sources (generator/batteries)',
        'Charge all devices and backup batteries',
        'Fill propane tanks and gas cans (safely)',
        'Locate flashlights and check batteries',
        'Download offline maps and important documents'
      ],
      urgency: 'today',
      icon: Zap,
      resources: [
        { type: 'link', label: 'Outage Map', value: 'https://poweroutage.us' }
      ],
      impact: 'Maintains communication and basic needs during outages',
      timeRequired: '2 hours'
    });
  }

  // Security/Family Actions
  if (redIndicators.some(i => i.id === 'ice_detention_surge' || i.id === 'national_guard_metros' || i.domain === 'global_conflict')) {
    actions.push({
      id: 'security-1',
      category: 'Family Safety',
      title: 'Update Family Emergency Plan',
      why: 'Social tensions rising — ensure family can reconnect if separated',
      steps: [
        'Confirm meeting locations (primary and backup)',
        'Update emergency contact list with all family',
        'Share location with trusted family members',
        'Review evacuation routes from home/work/school',
        'Pack go-bags for each family member'
      ],
      urgency: 'this-week',
      icon: Users,
      resources: [
        { type: 'phone', label: 'Family Group Text', value: 'Create if needed' },
        { type: 'checklist', label: 'Go-Bag Items', value: 'documents,cash,meds,clothes,food,water' }
      ],
      impact: 'Ensures family unity during disruptions',
      timeRequired: '1-2 hours'
    });
  }

  // Community Actions
  if ((currentPhase?.number ?? 0) >= 2 || redIndicators.length >= 2) {
    actions.push({
      id: 'community-1',
      category: 'Community',
      title: 'Connect with Neighbors',
      why: 'Community support critical during extended disruptions',
      steps: [
        'Exchange contact info with 3-5 nearby neighbors',
        'Identify neighbors with medical skills or resources',
        'Discuss mutual aid during emergencies',
        'Share this app with trusted neighbors',
        'Plan communication without cell service'
      ],
      urgency: 'this-week',
      icon: Shield,
      resources: [
        { type: 'checklist', label: 'Neighbor Skills', value: 'medical,repair,security,food' }
      ],
      impact: 'Creates resilient support network',
      timeRequired: '30 minutes per neighbor'
    });
  }

  // Sort by urgency and limit
  const urgencyOrder = { immediate: 0, today: 1, 'this-week': 2 };
  return actions.sort((a, b) => urgencyOrder[a.urgency] - urgencyOrder[b.urgency]).slice(0, 5);
}
