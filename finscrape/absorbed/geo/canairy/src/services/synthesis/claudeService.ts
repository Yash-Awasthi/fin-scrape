/**
 * Claude LLM Service for Canairy Synthesis Engine
 *
 * Enhances pattern-detected cards with natural language synthesis
 * using Claude API for "coffee test" quality messaging.
 */

import { ScoredPattern } from './cardScorer';
import { IndicatorData } from '../../types';

// Cache for synthesis results (15-minute TTL)
interface CacheEntry {
  result: SynthesisResult;
  timestamp: number;
}

const synthesisCache = new Map<string, CacheEntry>();
const CACHE_TTL = 15 * 60 * 1000; // 15 minutes

export interface SynthesisResult {
  headline: string;
  body: string;                    // What's happening (legacy, maps to whatsHappening)
  whyItMatters: string;            // Family impact
  whatToDo: string;                // Quick action summary
  outcomeSentence: string;
  urgencyTag: 'Do this today' | 'This week' | 'Worth knowing';
}


/**
 * Generate cache key from pattern and indicator state
 */
function getCacheKey(scoredPattern: ScoredPattern): string {
  const indicatorKey = scoredPattern.matchedIndicators
    .map(i => `${i.id}:${i.status.level}`)
    .sort()
    .join('|');
  return `${scoredPattern.pattern.id}:${indicatorKey}`;
}

/**
 * Check if cache entry is still valid
 */
function isCacheValid(entry: CacheEntry): boolean {
  return Date.now() - entry.timestamp < CACHE_TTL;
}

/**
 * Build prompt for Claude synthesis
 */
function buildSynthesisPrompt(
  scoredPattern: ScoredPattern,
  allIndicators: IndicatorData[]
): string {
  const pattern = scoredPattern.pattern;
  const matched = scoredPattern.matchedIndicators;

  // Build indicator context
  const indicatorContext = matched
    .map(i => {
      return `- ${i.name}: ${i.status.level.toUpperCase()} (${i.status.trend || 'stable'})${i.status.value !== undefined ? `, current: ${i.status.value}${i.unit || ''}` : ''}`;
    })
    .join('\n');

  // Overall situation context
  const redCount = allIndicators.filter(i => i.status.level === 'red').length;
  const amberCount = allIndicators.filter(i => i.status.level === 'amber').length;

  return `You are writing household preparedness alerts for a family monitoring system called Canairy.

CONTEXT:
Pattern detected: ${pattern.name}
Base severity: ${pattern.baseSeverity}/10
${pattern.historicalPrecedent ? `Historical precedent: ${pattern.historicalPrecedent}` : ''}

Triggering indicators:
${indicatorContext}

Overall system state: ${redCount} red, ${amberCount} amber indicators

TEMPLATE CONTENT (use as foundation):
Headline: ${pattern.headlineTemplate}
Outcome: ${pattern.outcomeTemplate}
${pattern.actionTemplate ? `Action: ${pattern.actionTemplate}` : ''}

INSTRUCTIONS:
1. Write a headline (5-8 words) that clearly states what's happening
2. Write a body (2-3 sentences) starting with "Here's what I'm seeing:" that explains the situation conversationally
3. Write whyItMatters (1-2 sentences) explaining how this affects the family specifically
4. Write whatToDo (1 sentence) with a clear, actionable summary
5. Write an outcome sentence (1 sentence) for the dashboard summary
6. Assign urgency: "Do this today" (severity 8+), "This week" (severity 5-7), "Worth knowing" (severity <5)

REQUIREMENTS:
- "Coffee test": A busy parent reading over coffee should understand in 5 seconds
- Be specific with numbers and timeframes when possible
- No alarmism, but don't downplay genuine risks
- Write like a trusted neighbor explaining the situation
- No technical jargon

Respond in JSON format:
{
  "headline": "...",
  "body": "...",
  "whyItMatters": "...",
  "whatToDo": "...",
  "outcomeSentence": "...",
  "urgencyTag": "Do this today" | "This week" | "Worth knowing"
}`;
}

// Track if we've already logged the API key warning
let hasLoggedApiKeyWarning = false;

/**
 * Call Claude API for synthesis
 */
async function callClaudeAPI(prompt: string): Promise<SynthesisResult | null> {
  // Canairy AI synthesis is disabled to stop Anthropic token usage.
  // Re-enable by setting VITE_CANAIRY_AI_ENABLED=true at build time.
  if (import.meta.env.VITE_CANAIRY_AI_ENABLED !== 'true') {
    if (!hasLoggedApiKeyWarning) {
      console.info('Canairy AI synthesis disabled - using pre-written insights');
      hasLoggedApiKeyWarning = true;
    }
    return null;
  }

  const apiKey = import.meta.env.VITE_ANTHROPIC_API_KEY;

  if (!apiKey) {
    if (!hasLoggedApiKeyWarning) {
      console.info('Claude API key not configured - using pre-written insights');
      hasLoggedApiKeyWarning = true;
    }
    return null;
  }

  try {
    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01',
        'anthropic-dangerous-direct-browser-access': 'true',
      },
      body: JSON.stringify({
        model: 'claude-3-haiku-20240307',
        max_tokens: 500,
        messages: [
          {
            role: 'user',
            content: prompt,
          },
        ],
      }),
    });

    if (!response.ok) {
      console.error('Claude API error:', response.status, await response.text());
      return null;
    }

    const data = await response.json();
    const content = data.content?.[0]?.text;

    if (!content) {
      console.error('No content in Claude response');
      return null;
    }

    // Parse JSON response
    const jsonMatch = content.match(/\{[\s\S]*\}/);
    if (!jsonMatch) {
      console.error('Could not parse JSON from Claude response');
      return null;
    }

    return JSON.parse(jsonMatch[0]) as SynthesisResult;
  } catch (error) {
    console.error('Claude API call failed:', error);
    return null;
  }
}

/**
 * Generate fallback synthesis from templates
 */
function generateFallback(scoredPattern: ScoredPattern): SynthesisResult {
  const pattern = scoredPattern.pattern;
  const severity = scoredPattern.severityScore;

  let urgencyTag: SynthesisResult['urgencyTag'];
  if (severity >= 70) {
    urgencyTag = 'Do this today';
  } else if (severity >= 40) {
    urgencyTag = 'This week';
  } else {
    urgencyTag = 'Worth knowing';
  }

  return {
    headline: pattern.headlineTemplate,
    body: pattern.outcomeTemplate,
    whyItMatters: pattern.outcomeTemplate,
    whatToDo: pattern.actionTemplate || 'Review the situation and consider your options.',
    outcomeSentence: pattern.outcomeTemplate.split('.')[0] + '.',
    urgencyTag,
  };
}

/**
 * Synthesize enhanced content for a scored pattern
 */
export async function synthesizePattern(
  scoredPattern: ScoredPattern,
  allIndicators: IndicatorData[],
  useCache = true
): Promise<SynthesisResult> {
  // Check cache first
  if (useCache) {
    const cacheKey = getCacheKey(scoredPattern);
    const cached = synthesisCache.get(cacheKey);

    if (cached && isCacheValid(cached)) {
      return cached.result;
    }
  }

  // Try Claude API
  const prompt = buildSynthesisPrompt(scoredPattern, allIndicators);
  const claudeResult = await callClaudeAPI(prompt);

  if (claudeResult) {
    // Cache the result
    const cacheKey = getCacheKey(scoredPattern);
    synthesisCache.set(cacheKey, {
      result: claudeResult,
      timestamp: Date.now(),
    });
    return claudeResult;
  }

  // Fallback to template
  return generateFallback(scoredPattern);
}

/**
 * Batch synthesize multiple patterns efficiently
 */
export async function synthesizeBatch(
  scoredPatterns: ScoredPattern[],
  allIndicators: IndicatorData[]
): Promise<Map<string, SynthesisResult>> {
  const results = new Map<string, SynthesisResult>();

  // Process in parallel with rate limiting
  const batchSize = 3;
  for (let i = 0; i < scoredPatterns.length; i += batchSize) {
    const batch = scoredPatterns.slice(i, i + batchSize);

    const batchResults = await Promise.all(
      batch.map(async pattern => {
        const result = await synthesizePattern(pattern, allIndicators);
        return { id: pattern.pattern.id, result };
      })
    );

    for (const { id, result } of batchResults) {
      results.set(id, result);
    }

    // Small delay between batches to avoid rate limits
    if (i + batchSize < scoredPatterns.length) {
      await new Promise(resolve => setTimeout(resolve, 100));
    }
  }

  return results;
}

/**
 * Clear the synthesis cache
 */
export function clearSynthesisCache(): void {
  synthesisCache.clear();
}

/**
 * Get cache statistics
 */
export function getCacheStats(): { size: number; validEntries: number } {
  let validEntries = 0;
  synthesisCache.forEach(entry => {
    if (isCacheValid(entry)) validEntries++;
  });
  return { size: synthesisCache.size, validEntries };
}
