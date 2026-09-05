import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  CheckCircle2,
  Package,
  DollarSign,
  Zap,
  Shield,
  Users,
  Phone,
  ExternalLink,
  Clock,
  AlertTriangle,
  Copy,
  Check
} from 'lucide-react';
import { cn } from '../../utils/cn';
import { useStore } from '../../store';
import { Badge } from '../core/Badge';

interface DetailedAction {
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

export const ActionablePriorityActions: React.FC = () => {
  const { indicators, currentPhase } = useStore();
  const [completedActions, setCompletedActions] = useState<Set<string>>(new Set());
  const [copiedId, setCopiedId] = useState<string | null>(null);
  
  const generateDetailedActions = (): DetailedAction[] => {
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
          ? 'Banking system showing severe stress - protect your money before potential bank runs'
          : 'Treasury markets unstable - banks may restrict access to funds',
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
        why: 'Supply chain disruptions imminent - prices will spike 20-40% within days',
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
        why: 'Grid instability detected - rolling blackouts possible',
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
        why: 'Social tensions rising - ensure family can reconnect if separated',
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
  };
  
  const actions = generateDetailedActions();
  
  const toggleComplete = (actionId: string) => {
    setCompletedActions(prev => {
      const next = new Set(prev);
      if (next.has(actionId)) {
        next.delete(actionId);
      } else {
        next.add(actionId);
      }
      return next;
    });
  };
  
  const copyToClipboard = (text: string, actionId: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(actionId);
    setTimeout(() => setCopiedId(null), 2000);
  };
  
  const getUrgencyStyle = (urgency: DetailedAction['urgency']) => {
    switch (urgency) {
      case 'immediate':
        return 'bg-red-500/10 border-red-500/30';
      case 'today':
        return 'bg-amber-500/10 border-amber-500/30';
      case 'this-week':
        return 'bg-blue-500/10 border-blue-500/30';
    }
  };
  
  const getUrgencyBadge = (urgency: DetailedAction['urgency']) => {
    switch (urgency) {
      case 'immediate':
        return <Badge variant="red" size="sm">DO NOW</Badge>;
      case 'today':
        return <Badge variant="amber" size="sm">TODAY</Badge>;
      case 'this-week':
        return <Badge variant="default" size="sm">THIS WEEK</Badge>;
    }
  };
  
  if (actions.length === 0) {
    return (
      <div className="bg-white/[0.03] rounded-2xl border border-white/[0.04] p-8">
        <h3 className="text-lg font-semibold text-white mb-4">You're All Set!</h3>
        <p className="text-white/30">No urgent actions needed. Continue monitoring and stay prepared.</p>
      </div>
    );
  }
  
  const completionRate = Math.round((completedActions.size / actions.length) * 100);
  
  return (
    <div className="bg-white/[0.03] rounded-2xl border border-white/[0.04] p-4 sm:p-8">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <h3 className="text-lg font-display font-semibold text-white">Priority Actions</h3>
        <div className="flex items-center gap-2">
          <div className="text-sm text-white/30">{completionRate}% Complete</div>
          <div className="w-24 h-2 bg-white/5 rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-green-500 rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${completionRate}%` }}
              transition={{ duration: 0.5 }}
            />
          </div>
        </div>
      </div>
      
      <div className="space-y-4">
        {actions.map((action, index) => {
          const isCompleted = completedActions.has(action.id);
          
          return (
            <motion.div
              key={action.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className={cn(
                "relative rounded-xl border p-6 transition-all",
                getUrgencyStyle(action.urgency),
                isCompleted && "opacity-60"
              )}
            >
              {/* Header */}
              <div className="flex items-start gap-4 mb-4">
                <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-white/5 flex items-center justify-center">
                  <action.icon className="w-5 h-5" />
                </div>
                <div className="flex-1">
                  <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
                    <div className="flex-1">
                      <h4 className="font-display font-medium text-white flex flex-wrap items-center gap-2">
                        {action.title}
                        {isCompleted && <CheckCircle2 className="w-4 h-4 text-green-400" />}
                      </h4>
                      <p className="text-sm font-body text-white/30 mt-1">{action.why}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      {getUrgencyBadge(action.urgency)}
                      <button
                        onClick={() => toggleComplete(action.id)}
                        className={cn(
                          "w-5 h-5 rounded border-2 transition-colors",
                          isCompleted 
                            ? "bg-green-500 border-green-500" 
                            : "border-white/15 hover:border-white/30"
                        )}
                      >
                        {isCompleted && <Check className="w-3 h-3 text-white" />}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Impact and Time */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4 mb-4">
                <div className="bg-white/[0.03] rounded-lg p-3">
                  <div className="text-xs text-white/20 mb-1">Impact</div>
                  <div className="text-sm text-white/50">{action.impact}</div>
                </div>
                <div className="bg-white/[0.03] rounded-lg p-3">
                  <div className="text-xs text-white/20 mb-1 flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    Time Required
                  </div>
                  <div className="text-sm text-white/50">{action.timeRequired}</div>
                </div>
              </div>
              
              {/* Steps */}
              <div className="mb-4">
                <h5 className="text-sm font-medium text-white/50 mb-2">Steps to Take:</h5>
                <ul className="space-y-2">
                  {action.steps.map((step, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm">
                      <span className="text-white/20 mt-0.5">{i + 1}.</span>
                      <span className={cn("text-white/50", isCompleted && "line-through")}>
                        {step}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
              
              {/* Resources */}
              {action.resources && action.resources.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {action.resources.map((resource, i) => (
                    <button
                      key={i}
                      onClick={() => {
                        if (resource.type === 'phone') {
                          window.location.href = `tel:${resource.value}`;
                        } else if (resource.type === 'link') {
                          window.open(resource.value, '_blank');
                        } else {
                          copyToClipboard(resource.value, `${action.id}-${i}`);
                        }
                      }}
                      className="inline-flex items-center gap-2 px-3 py-1.5 bg-white/5 hover:bg-white/10 rounded-lg text-xs text-white/50 transition-colors"
                    >
                      {resource.type === 'phone' && <Phone className="w-3 h-3" />}
                      {resource.type === 'link' && <ExternalLink className="w-3 h-3" />}
                      {resource.type === 'checklist' && (
                        copiedId === `${action.id}-${i}` 
                          ? <Check className="w-3 h-3 text-green-400" /> 
                          : <Copy className="w-3 h-3" />
                      )}
                      {resource.label}
                    </button>
                  ))}
                </div>
              )}
            </motion.div>
          );
        })}
      </div>
      
      {/* Quick Stats */}
      <div className="mt-6 pt-6 border-t border-white/[0.04] flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 text-sm">
        <div className="flex items-center gap-2 text-white/30">
          <AlertTriangle className="w-4 h-4" />
          <span>{actions.filter(a => a.urgency === 'immediate').length} immediate actions</span>
        </div>
        <a href="/action-plan" className="text-white/20 hover:text-white/50 transition-colors">
          View full action plan →
        </a>
      </div>
    </div>
  );
};