import { chatCompletionJson } from "./client";
import { personas } from "./personas";
import type {
  PersonaProposal,
  ProposedSupplyNode,
  ImportanceLevel,
} from "@/types";

// ============================================================
// Supply chain debate pipeline: generate → merge → vote
// ============================================================

interface RawProposal {
  nodes: ProposedSupplyNode[];
}

/**
 * Step 1: Each persona independently generates a 3-level supply chain decomposition.
 */
export async function generatePersonaTrees(
  company: string,
  product: string,
  researchContext?: string
): Promise<PersonaProposal[]> {
  const researchSection = researchContext
    ? `\n\nResearch context (from web search / teardown reports):\n${researchContext}`
    : "";

  const userPrompt = `Company: ${company}
Product: ${product}${researchSection}

Decompose this product's complete supply chain into a 3-level component tree.
Identify every major component, sub-component, intermediary material, and raw material.
Be as specific and comprehensive as possible.`;

  const proposals = await Promise.all(
    personas.map(async (persona) => {
      try {
        const result = await chatCompletionJson<RawProposal>(
          persona.systemPrompt,
          userPrompt,
          {}
        );

        return {
          persona: persona.role,
          nodes: result.nodes ?? [],
        } as PersonaProposal;
      } catch (err) {
        console.error(`Persona ${persona.role} failed:`, err);
        return { persona: persona.role, nodes: [] } as PersonaProposal;
      }
    })
  );

  return proposals;
}

/**
 * Step 2: Merge/deduplicate trees from all 5 personas into a unified tree.
 */
export async function mergePersonaTrees(
  company: string,
  product: string,
  proposals: PersonaProposal[]
): Promise<ProposedSupplyNode[]> {
  const systemPrompt = `You are a supply chain moderator merging component trees from 5 analysts.

Your job:
1. Identify nodes across all 5 trees that refer to the SAME component/material (even if worded differently).
2. Merge duplicates into a single node with the clearest, most specific label.
3. Keep unique nodes from each persona that add value.
4. Maintain the 3-level hierarchy: Level 1 (major components), Level 2 (sub-components), Level 3 (raw materials/intermediaries).
5. Aim for 5-8 Level 1 nodes, 2-4 Level 2 per parent, 1-3 Level 3 per parent.
6. Preserve the most specific category assignments.

Output valid JSON:
{
  "nodes": [
    {
      "tempId": "merged-1",
      "parentTempId": null | "parent-id",
      "label": "Component label",
      "level": 1 | 2 | 3,
      "category": "component" | "sub-component" | "raw-material" | "intermediary",
      "importance": "low" | "medium" | "high" | "critical",
      "reasoning": "Merged reasoning from relevant personas"
    }
  ]
}

For importance of merged nodes, use the MAJORITY view across personas.`;

  const userPrompt = `Company: ${company}
Product: ${product}

Here are the 5 persona proposals:

${proposals
  .map(
    (p) => `=== ${p.persona.toUpperCase()} ===
${JSON.stringify(p.nodes, null, 2)}`
  )
  .join("\n\n")}

Merge these into a single unified supply chain component tree.`;

  const result = await chatCompletionJson<RawProposal>(
    systemPrompt,
    userPrompt,
    { maxCompletionTokens: 16384 }
  );

  return result.nodes ?? [];
}

/**
 * Step 3: All 5 personas vote on each merged node.
 * Returns a map of tempId → { accurate (true/false), importance, confidence (votes/5) }
 */
export async function voteOnNodes(
  company: string,
  product: string,
  mergedNodes: ProposedSupplyNode[]
): Promise<
  Map<
    string,
    {
      confidence: number;
      importance: ImportanceLevel;
      reasoning: string;
    }
  >
> {
  const systemPrompt = `You are voting on supply chain component nodes for "${company} ${product}".

For EACH node, assess:
1. accuracy: Is this actually a component/material in this product? (true/false)
2. importance: How critical is this to the final product? (low/medium/high/critical)

Output valid JSON:
{
  "votes": [
    {
      "tempId": "node-id",
      "accurate": true | false,
      "importance": "low" | "medium" | "high" | "critical",
      "reasoning": "Brief justification"
    }
  ]
}`;

  const nodeList = mergedNodes.map((n) => ({
    tempId: n.tempId,
    label: n.label,
    level: n.level,
    category: n.category,
  }));

  const userPrompt = `Vote on each of these supply chain nodes for ${company} ${product}:
${JSON.stringify(nodeList, null, 2)}`;

  const allVotes = await Promise.all(
    personas.map(async (persona) => {
      try {
        const result = await chatCompletionJson<{
          votes: {
            tempId: string;
            accurate: boolean;
            importance: ImportanceLevel;
            reasoning: string;
          }[];
        }>(
          `${persona.systemPrompt}\n\n${systemPrompt}`,
          userPrompt,
          {}
        );
        return result.votes ?? [];
      } catch (err) {
        console.error(`Vote failed for ${persona.role}:`, err);
        return [];
      }
    })
  );

  // Aggregate votes per node
  const consensusMap = new Map<
    string,
    { confidence: number; importance: ImportanceLevel; reasoning: string }
  >();

  for (const node of mergedNodes) {
    const nodeVotes = allVotes
      .flat()
      .filter((v) => v.tempId === node.tempId);

    if (nodeVotes.length === 0) {
      consensusMap.set(node.tempId, {
        confidence: 0.6,
        importance: node.importance,
        reasoning: node.reasoning,
      });
      continue;
    }

    // Confidence = accurate votes / total votes
    const accurateCount = nodeVotes.filter((v) => v.accurate).length;
    const confidence = accurateCount / nodeVotes.length;

    // Majority importance
    const impCounts: Record<ImportanceLevel, number> = {
      low: 0,
      medium: 0,
      high: 0,
      critical: 0,
    };
    for (const v of nodeVotes) impCounts[v.importance]++;
    const importance = (
      Object.entries(impCounts) as [ImportanceLevel, number][]
    ).sort((a, b) => b[1] - a[1])[0][0];

    const bestVote = nodeVotes.find((v) => v.accurate);
    const reasoning = bestVote?.reasoning ?? node.reasoning;

    consensusMap.set(node.tempId, { confidence, importance, reasoning });
  }

  return consensusMap;
}

/**
 * Full debate pipeline: generate → merge → vote → filter by consensus
 */
export async function runFullDebate(
  company: string,
  product: string,
  researchContext?: string
): Promise<{
  nodes: ProposedSupplyNode[];
  confidences: Map<
    string,
    { confidence: number; importance: ImportanceLevel; reasoning: string }
  >;
}> {
  console.log(`[Debate] Starting for: "${company} ${product}"`);

  // Step 1: Generate
  console.log("[Debate] Step 1: Generating persona trees...");
  const proposals = await generatePersonaTrees(company, product, researchContext);
  const totalNodes = proposals.reduce((sum, p) => sum + p.nodes.length, 0);
  console.log(`[Debate] Generated ${totalNodes} nodes across ${proposals.length} personas`);

  // Step 2: Merge
  console.log("[Debate] Step 2: Merging trees...");
  const mergedNodes = await mergePersonaTrees(company, product, proposals);
  console.log(`[Debate] Merged into ${mergedNodes.length} nodes`);

  // Step 3: Vote
  console.log("[Debate] Step 3: Voting on nodes...");
  const confidences = await voteOnNodes(company, product, mergedNodes);

  // Filter: include if confidence >= 0.6 (3/5 agree)
  const filteredNodes = mergedNodes.filter((node) => {
    const vote = confidences.get(node.tempId);
    return vote && vote.confidence >= 0.6;
  });

  console.log(
    `[Debate] Complete. ${filteredNodes.length}/${mergedNodes.length} nodes passed consensus.`
  );

  return { nodes: filteredNodes, confidences };
}
