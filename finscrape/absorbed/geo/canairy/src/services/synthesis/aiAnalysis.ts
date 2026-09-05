/**
 * AI Analysis Service for Canairy
 *
 * This service uses Claude to ANALYZE indicator data and generate
 * contextual insights with full evidence chains for family-level action.
 *
 * Architecture:
 * - System prompt: Voice, rules, household context (static)
 * - User message: Indicator data + current state (dynamic)
 * - Post-processing: Computed confidence override, validation
 * - Fallback: Rich domain knowledge from INDICATOR_CONTEXT
 */

import { IndicatorData, UserContext } from '../../types';
import { getDisplayName, getImpact, getAction } from '../../data/indicatorTranslations';
import { getIndicatorContext } from './indicatorContext';

// Track if we've already logged the API key warning
let hasLoggedAIAnalysisWarning = false;

// ============================================================================
// TYPES
// ============================================================================

export interface EvidenceSource {
  claim: string;
  source: string;
  sourceType: 'government-official' | 'academic-research' | 'wire-service' | 'industry-data' | 'investigative-journalism';
  dataPoint?: string;
}

export interface ReasoningChain {
  observation: string;
  interpretation: string;
  familyImplication: string;
  recommendation: string;
  assumptions: string[];
  counterpoints: string[];
  updateTriggers: string[];
}

export interface ActionItem {
  task: string;
  why: string;
  effort: 'quick' | 'moderate' | 'involved';
  timeEstimate: string;
  priority: 'critical' | 'recommended' | 'optional';
}

export interface AIInsight {
  id: string;
  headline: string;
  body: string;
  urgency: 'today' | 'week' | 'knowing';
  confidence: 'high' | 'moderate' | 'low';
  confidenceReason: string;
  domains: string[];
  dataPoint: string;
  situationBrief: string;
  evidenceSources: EvidenceSource[];
  reasoning: ReasoningChain;
  actionItems: ActionItem[];
  peripheralImpacts: string[];
  phaseRelevance?: string;
  mPrepRelevance?: string;
}

export interface AIAnalysisResult {
  outcomeSentence: string;
  insights: AIInsight[];
  hiddenConnections: string[];
  familyFocusedSummary: string;
  phaseRelevance?: string;
  phaseGapAnalysis?: string;
  mPrepStatus?: string;
}

// ============================================================================
// HOUSEHOLD CONTEXT (Static - your specific family context)
// ============================================================================

const HOUSEHOLD_CONTEXT = `
## AUDIENCE PROFILE

You're writing for busy parents in their 30s-40s with young children (toddlers to elementary age). They have good jobs, own or rent a decent home, and are time-poor but resourceful. They care deeply about their kids' future but don't have hours to research prepping forums.

LIFE REALITY:
- Dual income, mortgage/rent, daycare/school costs
- Kids' activities, school schedules, pediatrician visits
- Maybe 30 minutes after kids' bedtime to think about this stuff
- Comfortable but not wealthy — $200-500 discretionary for prep
- Cars are essential (commute, school pickup, activities)
- Rely on grocery delivery, Amazon, normal supply chains

WHAT KEEPS THEM UP AT NIGHT:
- "Will I still have my job in 2 years?"
- "Can we afford this house if rates go up?"
- "What if the kids get sick and pharmacies are out of Tylenol?"
- "Is this a good time to buy a car/refinance/invest?"
- "Should we be doing something to prepare?"

WHAT THEY CAN ACTUALLY DO:
- Add $50 extra groceries to the weekly shop (not $500 stockpile runs)
- Fill up the gas tank when it's half full instead of empty
- Keep 2 weeks of kids' medications on hand
- Have $500-1000 cash at home
- Download important docs to phone/laptop
- Talk to spouse about "what if" scenarios
- Gradually build supplies over months, not panic-buy

WHAT THEY CANNOT DO:
- Quit their jobs to homestead
- Build a bunker or buy land
- Spend thousands on freeze-dried food
- Dedicate weekends to prepper activities
- Freak out their kids with apocalypse talk

ACTION TRANSLATION:
- "Secure 6 months of supplies" → "Add one extra bag of rice to your next grocery order"
- "Review your insurance coverage" → "Snap a photo of your policy docs for your phone"
- "Establish communication protocols" → "Make sure grandparents know your cell numbers by heart"
- "Stockpile critical medications" → "Ask your pediatrician for one extra refill of the kids' prescriptions"

TONE WITH THIS AUDIENCE:
- Practical, not paranoid
- Incremental steps, not overwhelming lists
- Acknowledge they're already stretched thin
- Connect to their actual worries (kids, jobs, money)
- Never make them feel they're failing if they haven't done everything
`;

// ============================================================================
// SYSTEM PROMPT (Static - defines voice, rules, persona)
// ============================================================================

const SYSTEM_PROMPT = `You are the intelligence analyst for Canairy, a household resilience monitoring system built for one specific family. You translate systemic risk data into family-level preparedness guidance that connects to their actual life, assets, phase progress, and decisions.

${HOUSEHOLD_CONTEXT}

## YOUR VOICE

You write like a trusted advisor who knows this family. Not a news anchor. Not a prepper influencer. Not a bureaucrat. You're the friend who works in intelligence and explains things clearly over coffee.

Tone: Calm competence. Specific numbers. Honest about uncertainty. The goal is CONFIDENCE through PREPARATION — never fear.

## WRITING RULES

HEADLINES: Lead with the action or the outcome. Never the domain or indicator name.
  GOOD: "Gas up before weekend — fuel prices climbing"
  GOOD: "Worth updating your resume this month"
  GOOD: "Grab extra kids' Tylenol on your next pharmacy run"
  GOOD: "Maybe hold off on that car purchase for now"
  BAD: "HormuzRisk: War risk premium elevated"
  BAD: "Economy domain showing stress patterns"
  BAD: "Secure 6 months of critical supplies"

BODY TEXT:
  Sentence 1: What's happening in the real world (with a number from the data).
  Sentence 2: What it means for a busy family with young kids.
  Sentence 3: One small, specific thing to do this week.

SPECIFICITY: Every claim needs a number, timeframe, or named source from the indicator data provided. If you're inferring beyond the data, say so.

CONNECT TO THEIR ACTUAL LIFE:
  - Mention things they already do: grocery runs, school pickup, pharmacy visits, gas station stops
  - Frame actions as add-ons to existing routines, not new projects
  - "Next time you're at Costco..." not "Establish a supply cache"
  - "When you fill up the car..." not "Maintain fuel reserves"
  - "Ask the pediatrician at your next visit..." not "Stockpile medications"

ACTION SIZING:
  - TODAY: 5-10 minutes, can do from phone or on existing errand
  - THIS WEEK: 30-60 minutes total, one errand or one evening task
  - THIS MONTH: A few hours spread across multiple sessions

REALISTIC BUDGET:
  - $20-50 for a "today" action
  - $100-200 for a "this week" action
  - Never assume unlimited funds

FORBIDDEN WORDS: indicators, elevated, metrics, domain, systemic, signal (in system sense), nominal, parameters, monitor (as sole action), "stockpile," "secure supplies," "establish protocols." Use words normal people use.

## CONFIDENCE SCORING

- HIGH: 3+ data points, ≥2 from government/institutional sources, data <48h old
- MODERATE: 1-2 data points, or single-source, or longer inference chain
- LOW: Inference based on pattern, limited direct data
Always state the specific reason.

## THE OUTCOME SENTENCE

The "outcomeSentence" sits at the top of the dashboard. It's read at 7am while making school lunches. Rules:
1. What might affect their family this week/month
2. One small thing they can actually do
3. 1-2 sentences max
4. Zero technical language
5. Acknowledge they're busy — make it feel manageable

GOOD: "Chip shortage is making car repairs harder to schedule. If your car needs work, book it soon rather than waiting."
GOOD: "Grocery prices likely to tick up next month. Good week to stock up on pantry staples when you see sales."
GOOD: "Job market getting tighter in tech. Might be worth freshening up your LinkedIn this weekend."
BAD: "Multiple indicators across economy and AI domains are elevated."
BAD: "Financial markets are flashing stress signals. Build your cash buffer immediately."

## OUTPUT

Respond with ONLY valid JSON. No markdown fences. No commentary outside the JSON.`;

// ============================================================================
// KNOWN PRECEDENT PATTERNS (Domain knowledge, hardcoded)
// ============================================================================

const PRECEDENT_PATTERNS = `
## KNOWN PRECEDENT PATTERNS

These are patterns documented from historical analysis:

- Economy (amber) + Supply Chain (amber) sustained 7+ days → retail shortages appeared within 2-3 weeks in 2021 (Suez), 2022 (Shanghai lockdowns), and 2024 (Red Sea rerouting)
- Energy (amber) + severe weather forecast → rolling blackouts occurred in TX Feb 2021, CA Aug 2020 when this combination appeared
- Global Conflict escalation + Oil Axis amber → fuel prices spiked 15-30% within 5 days in Feb 2022 (Ukraine), Oct 2023 (Israel-Hamas)
- CISA cyber advisory + grid stress → infrastructure disruption risk elevated; Colonial Pipeline (2021) followed this exact pattern
- 3+ domains at amber simultaneously → historically correlated with recession onset signals
- Domestic Control (amber) + Rights (amber) → travel disruption for affected communities within 1-2 weeks
- AI Window (red) + Economy (amber) → labor market disruption announcements tend to follow within 4-6 weeks
- Treasury tail > 5bps + market volatility → banking stress typically surfaces within 2-4 weeks (SVB 2023 pattern)
- Supply chain amber + energy amber → medication shortages (especially generics manufactured overseas) within 4-6 weeks
`;

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

function getSeason(): string {
  const month = new Date().getMonth();
  if (month >= 2 && month <= 4) return 'Spring';
  if (month >= 5 && month <= 7) return 'Summer';
  if (month >= 8 && month <= 10) return 'Fall';
  return 'Winter';
}

function daysSince(dateStr: string): number {
  const date = new Date(dateStr);
  const now = new Date();
  return Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
}

function hoursSince(dateStr: string): number {
  const date = new Date(dateStr);
  const now = new Date();
  return Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));
}

/**
 * Compute system phase based on indicator state
 */
export function computeSystemPhase(indicators: IndicatorData[]): number | 'tighten-up' {
  const red = indicators.filter(i => i.status.level === 'red');
  const amber = indicators.filter(i => i.status.level === 'amber');

  // High phase (7+): ≥2 reds simultaneously
  if (red.length >= 2) return 'tighten-up';

  // Check critical jump rules
  const hasNATORed = red.some(i => i.id === 'nato_high_readiness' || i.id === 'conf_02_russia_nato');
  const hasMarketRed = red.some(i => i.id === 'market_01_intraday_swing' || i.id === 'market_02_luxury_collapse');
  const hasGuardRed = red.some(i => i.id === 'national_guard_metros');
  const hasDHSRed = red.some(i => i.id === 'dhs_removal_expansion');
  const hasDeepfakeRed = red.some(i => i.id === 'info_02_deepfake_shocks');

  // Critical jumps
  if (hasMarketRed && hasDeepfakeRed) return 7;
  if (hasNATORed) return 6;
  if (hasGuardRed) return 5;
  if (hasDHSRed) return 5;

  // Normal progression
  if (red.length >= 1) return 3;

  const amberSustained7d = amber.filter(i => (i.status.daysSustained || 0) >= 7);
  if (amberSustained7d.length >= 2) return 3;
  if (amber.length >= 2) return 2;
  if (amber.length >= 1) return 2;

  return 1;
}

// ============================================================================
// COMPUTED CONFIDENCE (Hybrid approach)
// ============================================================================

interface ComputedConfidence {
  score: number;
  level: 'high' | 'moderate' | 'low';
  factors: string[];
}

function computeBaseConfidence(indicators: IndicatorData[]): ComputedConfidence {
  const factors: string[] = [];
  let score = 0;

  const elevated = indicators.filter(i => i.status.level === 'red' || i.status.level === 'amber');

  // Source authority
  const govSources = elevated.filter(i =>
    ['BLS', 'NERC', 'CISA', 'State Dept', 'Census', 'Treasury', 'Fed', 'EIA', 'USDA', 'FDA'].includes(i.source || '')
  );
  if (govSources.length >= 2) {
    score += 3;
    factors.push(`${govSources.length} government/institutional sources`);
  } else if (govSources.length === 1) {
    score += 1;
    factors.push('1 government source');
  }

  // Recency
  const freshIndicators = elevated.filter(i =>
    i.status.lastUpdate && hoursSince(i.status.lastUpdate) < 48
  );
  if (freshIndicators.length / Math.max(elevated.length, 1) > 0.7) {
    score += 2;
    factors.push('Most data updated within 48 hours');
  }

  // Corroboration
  const domains = [...new Set(elevated.map(i => i.domain))];
  if (domains.length >= 3) {
    score += 3;
    factors.push(`Corroborated across ${domains.length} independent domains`);
  } else if (domains.length === 2) {
    score += 2;
    factors.push('Corroborated across 2 domains');
  }

  // Trend consistency
  const worseningCount = elevated.filter(i => i.status.trend === 'up').length;
  if (worseningCount / Math.max(elevated.length, 1) > 0.5) {
    score += 1;
    factors.push('Majority of concerns trending worse');
  }

  // Sustained duration
  const sustained = elevated.filter(i => (i.status.daysSustained || 0) >= 3);
  if (sustained.length >= 2) {
    score += 1;
    factors.push('Multiple concerns sustained 3+ days');
  }

  const level: 'high' | 'moderate' | 'low' =
    score >= 7 ? 'high' :
    score >= 4 ? 'moderate' : 'low';

  return { score, level, factors };
}

// ============================================================================
// USER MESSAGE BUILDER
// ============================================================================

function formatIndicatorFull(ind: IndicatorData): string {
  const displayName = getDisplayName(ind.id) || ind.name;
  const ctx = getIndicatorContext(ind.id);
  const level = ind.status.level as 'amber' | 'red';
  const impact = ctx ? ctx.familyImpact[level] : (getImpact(ind.id, level) || '');

  const baselineStr = ind.baseline
    ? `Baseline: ${ind.baseline.value}${ind.unit || ''} (${ind.baseline.period})`
    : '';

  const thresholdStr = ind.thresholds?.threshold_amber !== undefined
    ? `Thresholds: amber=${ind.thresholds.threshold_amber}, red=${ind.thresholds.threshold_red}`
    : '';

  const sinceStr = ind.statusChangedDate
    ? `Changed: ${daysSince(ind.statusChangedDate)} days ago from ${ind.previousStatus || 'unknown'}`
    : '';

  const durationStr = ind.status.daysSustained
    ? `Sustained: ${ind.status.daysSustained} days at ${ind.status.level}`
    : '';

  return `  ${displayName} [${ind.domain}]
    Value: ${ind.status.value ?? 'N/A'}${ind.unit || ''} | ${thresholdStr}
    ${baselineStr}
    Trend: ${ind.status.trend || 'stable'} | ${durationStr} | ${sinceStr}
    Source: ${ind.source || ind.dataSource || 'Unknown'}
    Family impact: ${impact || 'No specific impact data available'}`;
}

function buildRecentChanges(indicators: IndicatorData[]): string {
  const recentChanges = indicators
    .filter((i): i is IndicatorData & { statusChangedDate: string } =>
      !!i.statusChangedDate && daysSince(i.statusChangedDate) <= 14
    )
    .map(i => `  - ${getDisplayName(i.id) || i.name}: ${i.previousStatus || 'unknown'} → ${i.status.level} (${daysSince(i.statusChangedDate)} days ago)`)
    .join('\n');

  return recentChanges || '  No status changes in the past 14 days';
}

function buildPhaseGap(userContext: UserContext, indicators: IndicatorData[]): string {
  const systemPhase = computeSystemPhase(indicators);
  const gap = userContext.phaseTasksTotal - userContext.phaseTasksCompleted;
  const pct = Math.round((userContext.phaseTasksCompleted / userContext.phaseTasksTotal) * 100);

  const phaseDisplay = systemPhase === 'tighten-up'
    ? 'Phase 7 (≥2 critical concerns)'
    : `Phase ${systemPhase}`;

  return `System assessment: ${phaseDisplay}
User progress: Phase ${userContext.currentPhase} (${userContext.phaseTasksCompleted}/${userContext.phaseTasksTotal} tasks, ${pct}%)
Gap: ${gap} tasks remaining to complete current phase`;
}

function buildUserMessage(
  indicators: IndicatorData[],
  userContext: UserContext
): string {
  const red = indicators.filter(i => i.status.level === 'red');
  const amber = indicators.filter(i => i.status.level === 'amber');
  const green = indicators.filter(i => i.status.level === 'green');

  const dateStr = new Date().toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });

  return `## BRIEFING REQUEST — ${dateStr}

### HOUSEHOLD STATUS
Location: ${userContext.region || 'Northeast US'}
Grid: ${userContext.gridOperator || 'PJM Interconnection'}
Season: ${getSeason()}
${userContext.householdDescription ? `Household: ${userContext.householdDescription}` : ''}

### INDICATOR STATE

CRITICAL (${red.length}):
${red.map(formatIndicatorFull).join('\n\n') || '  None'}

CAUTION (${amber.length}):
${amber.map(formatIndicatorFull).join('\n\n') || '  None'}

STABLE: ${green.length} within normal range

### RECENT SHIFTS (Last 14 Days)
${buildRecentChanges(indicators)}

${PRECEDENT_PATTERNS}

### PHASE GAP
${buildPhaseGap(userContext, indicators)}

### OUTPUT REQUESTED

Generate a JSON object with:

{
  "outcomeSentence": "The 1-2 sentence dashboard header. What to expect + what to do.",
  "insights": [
    {
      "id": "unique-string-id",
      "headline": "5-8 word action headline",
      "body": "2-3 specific sentences: what's happening → family impact → what to do",
      "dataPoint": "Key metric in plain format: 'Avg. delivery: 18 days (was 7 in Jan)'",
      "urgency": "today | week | knowing",
      "confidence": "high | moderate | low",
      "confidenceReason": "Why this confidence level",
      "domains": ["domain1", "domain2"],
      "situationBrief": "2-3 paragraph narrative for the detail panel.",
      "evidenceSources": [
        {
          "claim": "What specific claim this source supports",
          "source": "Source name",
          "sourceType": "government-official | academic-research | wire-service | industry-data | investigative-journalism",
          "dataPoint": "Specific number from this source"
        }
      ],
      "reasoning": {
        "observation": "What the data shows (facts only)",
        "interpretation": "What we think it means",
        "familyImplication": "How this reaches the household specifically",
        "recommendation": "What to do and why the timing matters",
        "assumptions": ["What this reasoning depends on"],
        "counterpoints": ["What could make this wrong"],
        "updateTriggers": ["What would change this assessment"]
      },
      "actionItems": [
        {
          "task": "Specific completable action",
          "why": "Why this action, why now",
          "effort": "quick | moderate | involved",
          "timeEstimate": "~15 min",
          "priority": "critical | recommended | optional"
        }
      ],
      "peripheralImpacts": ["Impact headlines miss: medication, childcare, pets, commute, etc."]
    }
  ],
  "hiddenConnections": ["Cross-indicator patterns that aren't obvious"],
  "familyFocusedSummary": "One paragraph summary for households with kids, elderly parents, or pets",
  "phaseGapAnalysis": "How current conditions relate to the user's phase progress"
}

Generate 3-5 insights. Prioritize by actionability and urgency. Every insight must cite at least one specific data point from the indicators above.`;
}

// ============================================================================
// API CALL
// ============================================================================

async function callClaudeForAnalysis(
  indicators: IndicatorData[],
  userContext: UserContext
): Promise<AIAnalysisResult | null> {
  // Canairy AI synthesis is disabled to stop Anthropic token usage.
  // Re-enable by setting VITE_CANAIRY_AI_ENABLED=true at build time.
  if (import.meta.env.VITE_CANAIRY_AI_ENABLED !== 'true') {
    if (!hasLoggedAIAnalysisWarning) {
      console.info('Canairy AI synthesis disabled - using pre-built insights');
      hasLoggedAIAnalysisWarning = true;
    }
    return null;
  }

  const apiKey = import.meta.env.VITE_ANTHROPIC_API_KEY;

  if (!apiKey) {
    if (!hasLoggedAIAnalysisWarning) {
      console.info('AI analysis unavailable - using pre-built insights');
      hasLoggedAIAnalysisWarning = true;
    }
    return null;
  }

  // Use proxy in development to avoid CORS
  const apiUrl = import.meta.env.DEV
    ? '/api/anthropic/v1/messages'
    : 'https://api.anthropic.com/v1/messages';

  console.log('Calling Claude API...', { isDev: import.meta.env.DEV, apiUrl });

  try {
    const requestBody = {
      model: 'claude-sonnet-4-5-20250929',
      max_tokens: 8192,
      temperature: 0.2,
      system: SYSTEM_PROMPT,
      messages: [
        {
          role: 'user',
          content: buildUserMessage(indicators, userContext),
        },
      ],
    };

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'x-api-key': apiKey,
      'anthropic-version': '2023-06-01',
    };

    // Only add browser access header for direct API calls (not through proxy)
    if (!import.meta.env.DEV) {
      headers['anthropic-dangerous-direct-browser-access'] = 'true';
    }

    const response = await fetch(apiUrl, {
      method: 'POST',
      headers,
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Claude API error:', response.status, errorText);
      return null;
    }

    const data = await response.json();
    const content = data.content?.[0]?.text;

    if (!content) {
      console.error('No content in Claude response');
      return null;
    }

    console.log('Claude response received, parsing JSON...');

    // Parse JSON response
    let parsed: AIAnalysisResult;
    try {
      parsed = JSON.parse(content);
    } catch {
      const jsonMatch = content.match(/\{[\s\S]*\}/);
      if (!jsonMatch) {
        console.error('Could not extract JSON from response:', content.substring(0, 200));
        return null;
      }
      parsed = JSON.parse(jsonMatch[0]);
    }

    // Validate required fields
    if (!parsed.outcomeSentence || !Array.isArray(parsed.insights)) {
      console.error('Response missing required fields');
      return null;
    }

    // Post-process: apply computed confidence override
    const baseConfidence = computeBaseConfidence(indicators);
    for (const insight of parsed.insights) {
      if (baseConfidence.level === 'high' && insight.confidence !== 'high') {
        insight.confidence = 'high';
        insight.confidenceReason += ` [Upgraded: ${baseConfidence.factors.join(', ')}]`;
      }
    }

    console.log('AI Analysis complete:', parsed.insights.length, 'insights generated');
    return parsed;
  } catch (error) {
    console.error('Claude API call failed:', error);
    return null;
  }
}

// ============================================================================
// CACHE
// ============================================================================

interface AnalysisCacheEntry {
  result: AIAnalysisResult;
  timestamp: number;
  indicatorHash: string;
}

let analysisCache: AnalysisCacheEntry | null = null;
const ANALYSIS_CACHE_TTL = 15 * 60 * 1000; // 15 minutes

function getIndicatorHash(indicators: IndicatorData[]): string {
  return indicators
    .map(i => `${i.id}:${i.status.level}:${i.status.value}`)
    .sort()
    .join('|');
}

// ============================================================================
// PUBLIC API
// ============================================================================

export function getDefaultUserContext(
  currentPhase: number,
  completedItems: number,
  totalItems: number
): UserContext {
  return {
    region: 'Northeast US',
    state: 'NJ',
    gridOperator: 'PJM Interconnection',
    nearestMetro: 'New York metro area',
    currentPhase,
    phaseTasksCompleted: completedItems,
    phaseTasksTotal: totalItems || 12,
    householdDescription: 'Family household',
  };
}

export async function analyzeIndicators(
  indicators: IndicatorData[],
  userContext?: UserContext
): Promise<AIAnalysisResult | null> {
  if (indicators.length === 0) {
    return null;
  }

  // Check cache
  const currentHash = getIndicatorHash(indicators);
  if (
    analysisCache &&
    analysisCache.indicatorHash === currentHash &&
    Date.now() - analysisCache.timestamp < ANALYSIS_CACHE_TTL
  ) {
    console.log('Using cached AI analysis');
    return analysisCache.result;
  }

  const context = userContext || getDefaultUserContext(1, 4, 12);
  const result = await callClaudeForAnalysis(indicators, context);

  if (result) {
    analysisCache = {
      result,
      timestamp: Date.now(),
      indicatorHash: currentHash,
    };
  }

  return result;
}

/**
 * Generate fallback insights using INDICATOR_CONTEXT
 * This provides rich, domain-specific content when AI is unavailable
 */
export function generateFallbackInsights(indicators: IndicatorData[]): AIAnalysisResult {
  const red = indicators.filter(i => i.status.level === 'red');
  const amber = indicators.filter(i => i.status.level === 'amber');
  const insights: AIInsight[] = [];
  const processed = new Set<string>();

  // Generate insights from INDICATOR_CONTEXT for each elevated indicator
  for (const ind of [...red, ...amber]) {
    const ctx = getIndicatorContext(ind.id);
    if (!ctx || processed.has(ind.id)) continue;
    processed.add(ind.id);

    const level = ind.status.level as 'amber' | 'red';

    // Build headline from the whatToDo (first sentence)
    const headline = ctx.whatToDo[level].split('.')[0].replace(/\.$/, '');

    insights.push({
      id: `fallback-${ind.id}`,
      headline,
      body: `${ctx.whatItMeans[level]}. ${ctx.familyImpact[level]}`,
      dataPoint: `${ctx.dataPointLabel}: ${ind.status.value ?? 'N/A'}${ind.unit || ''}`,
      urgency: level === 'red' ? 'today' : 'week',
      confidence: 'moderate',
      confidenceReason: `Based on ${ctx.source} threshold data (AI synthesis unavailable)`,
      domains: [ind.domain],
      situationBrief: `${ctx.whatItMeans[level]}\n\n${ctx.familyImpact[level]}`,
      evidenceSources: [{
        claim: ctx.whatItMeans[level],
        source: ctx.source,
        sourceType: 'government-official',
        dataPoint: `${ind.status.value ?? 'N/A'}${ind.unit || ''}`,
      }],
      reasoning: {
        observation: ctx.whatItMeans[level],
        interpretation: ctx.familyImpact[level],
        familyImplication: ctx.familyImpact[level],
        recommendation: ctx.whatToDo[level],
        assumptions: ['Current conditions persist for at least 1-2 weeks'],
        counterpoints: ['Situation could resolve faster than historical precedent suggests'],
        updateTriggers: [`When this concern returns to normal, this recommendation will be withdrawn`],
      },
      actionItems: ctx.whatToDo[level].split('. ').filter(Boolean).slice(0, 3).map((task, i) => ({
        task: task.replace(/\.$/, ''),
        why: i === 0 ? 'Primary action based on current conditions' : 'Supporting preparation',
        effort: 'moderate' as 'quick' | 'moderate' | 'involved',
        timeEstimate: '~30 min',
        priority: (level === 'red' ? 'critical' : 'recommended') as 'critical' | 'recommended' | 'optional',
      })),
      peripheralImpacts: ctx.peripheralImpacts,
    });

    // Cap at 12 insights (expanded to show more cards)
    if (insights.length >= 12) break;
  }

  // Add generic fallback for indicators without context
  for (const ind of [...red, ...amber]) {
    if (processed.has(ind.id) || insights.length >= 12) continue;
    processed.add(ind.id);

    const level = ind.status.level as 'amber' | 'red';
    const displayName = getDisplayName(ind.id) || ind.name;
    const impact = getImpact(ind.id, level) || `${displayName} conditions require attention.`;
    const action = getAction(ind.id, level) || `Review ${ind.domain} preparations`;

    insights.push({
      id: `fallback-generic-${ind.id}`,
      headline: action,
      body: impact,
      dataPoint: `${displayName}: ${ind.status.value ?? 'N/A'}${ind.unit || ''}`,
      urgency: level === 'red' ? 'today' : 'week',
      confidence: 'moderate',
      confidenceReason: 'Based on threshold data',
      domains: [ind.domain],
      situationBrief: impact,
      evidenceSources: [{
        claim: `${displayName} is at ${level} level`,
        source: ind.source || ind.dataSource || 'System data',
        sourceType: 'industry-data',
        dataPoint: String(ind.status.value),
      }],
      reasoning: {
        observation: `${displayName} is at ${level} threshold`,
        interpretation: impact,
        familyImplication: 'May affect household planning',
        recommendation: action,
        assumptions: ['Thresholds are calibrated correctly'],
        counterpoints: ['Conditions may improve'],
        updateTriggers: ['When this returns to normal'],
      },
      actionItems: [{
        task: action,
        why: 'Current conditions suggest action',
        effort: 'moderate',
        timeEstimate: '~30 min',
        priority: level === 'red' ? 'critical' : 'recommended',
      }],
      peripheralImpacts: ['Review household supplies', 'Check emergency contacts'],
    });
  }

  // Cross-domain pattern detection
  const elevatedDomains = new Set([...red, ...amber].map(i => i.domain));
  const economyElevated = elevatedDomains.has('economy');
  const supplyElevated = elevatedDomains.has('supply_chain');
  const energyElevated = elevatedDomains.has('energy');
  const conflictElevated = elevatedDomains.has('global_conflict');

  const hiddenConnections: string[] = [];
  if (economyElevated && supplyElevated) {
    hiddenConnections.push('Economy + Supply Chain stress often precedes retail shortages by 2-3 weeks');
  }
  if (energyElevated && conflictElevated) {
    hiddenConnections.push('Energy + Conflict stress can trigger rapid fuel price spikes');
  }
  if (elevatedDomains.size >= 3) {
    hiddenConnections.push('Multiple domains stressed simultaneously — historical correlation with broader economic stress');
  }

  // Compute system phase
  const systemPhase = computeSystemPhase(indicators);

  // Build outcome sentence using INDICATOR_CONTEXT where available
  let outcomeSentence = '';
  if (red.length >= 2 || systemPhase === 'tighten-up') {
    const topRed = red.slice(0, 2);
    const impacts = topRed.map(ind => {
      const ctx = getIndicatorContext(ind.id);
      return ctx?.familyImpact.red.split('.')[0] || getDisplayName(ind.id) || ind.name;
    }).filter(Boolean);
    outcomeSentence = `${impacts.join('. ')}. Focus on your emergency checklist and cash reserves this week.`;
  } else if (red.length === 1) {
    const ind = red[0];
    const ctx = getIndicatorContext(ind.id);
    const what = ctx?.familyImpact.red.split('.')[0] || `${getDisplayName(ind.id)} needs attention`;
    const action = ctx?.whatToDo.red.split('.')[0] || 'Review your preparations';
    outcomeSentence = `${what}. ${action}.`;
  } else if (amber.length >= 3) {
    outcomeSentence = 'Several areas showing stress. Good time to review supplies and advance your phase checklist.';
  } else if (amber.length > 0) {
    outcomeSentence = 'Conditions are manageable. Maintain routine preparations and keep supplies current.';
  } else {
    outcomeSentence = 'All clear for now. Continue routine preparedness maintenance.';
  }

  return {
    outcomeSentence,
    insights,
    hiddenConnections,
    familyFocusedSummary: insights.length > 0
      ? 'Current conditions suggest reviewing household supplies and emergency plans. Focus on medication refills, cash reserves, and vehicle readiness.'
      : 'No immediate actions needed. Continue routine preparedness maintenance.',
    phaseGapAnalysis: systemPhase === 'tighten-up'
      ? 'Phase 7 conditions (≥2 critical concerns). Prioritize your action plan now.'
      : `Conditions suggest Phase ${systemPhase}. Review your current phase progress and close the gap.`,
  };
}

export function clearAnalysisCache(): void {
  analysisCache = null;
}
