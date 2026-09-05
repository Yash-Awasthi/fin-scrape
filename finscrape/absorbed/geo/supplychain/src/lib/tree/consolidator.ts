import { chatCompletionJson } from "../azure/client";
import { getNodesForTree, getEdgesForTree } from "../db/queries";
import { db } from "../db/index";
import { supplyNodeEdges, supplyNodes } from "../db/schema";
import { eq } from "drizzle-orm";
import type { SupplyNode } from "@/types";

// Cross-branch deduplication + council merge vote

interface MergeCandidate {
  nodeA: SupplyNode;
  nodeB: SupplyNode;
  shouldMerge: boolean;
  reasoning: string;
}

export async function consolidateTree(treeId: string): Promise<void> {
  const nodes = await getNodesForTree(treeId);
  const edges = await getEdgesForTree(treeId);

  // Find potential duplicates: same level, similar labels
  const candidates: { nodeA: SupplyNode; nodeB: SupplyNode }[] = [];

  for (let i = 0; i < nodes.length; i++) {
    for (let j = i + 1; j < nodes.length; j++) {
      const a = nodes[i];
      const b = nodes[j];
      if (a.level !== b.level) continue;

      // Quick similarity check: share any words?
      const wordsA = new Set(a.label.toLowerCase().split(/\s+/));
      const wordsB = new Set(b.label.toLowerCase().split(/\s+/));
      const overlap = Array.from(wordsA).filter((w) => wordsB.has(w) && w.length > 2);

      if (overlap.length > 0) {
        candidates.push({ nodeA: a, nodeB: b });
      }
    }
  }

  if (candidates.length === 0) return;

  // Ask LLM to decide on merges
  const result = await chatCompletionJson<{ merges: MergeCandidate[] }>(
    `You are a supply chain analyst. Given pairs of component nodes, decide if they refer to the same thing and should be merged.

Output JSON:
{
  "merges": [
    {
      "nodeAId": "id",
      "nodeBId": "id",
      "shouldMerge": true | false,
      "reasoning": "brief explanation"
    }
  ]
}`,
    `Evaluate these potential duplicate pairs:
${JSON.stringify(
  candidates.map((c) => ({
    nodeAId: c.nodeA.id,
    nodeALabel: c.nodeA.label,
    nodeBId: c.nodeB.id,
    nodeBLabel: c.nodeB.label,
  })),
  null,
  2
)}`,
    {}
  );

  // Apply merges: redirect edges from nodeB to nodeA, delete nodeB
  for (const merge of result.merges ?? []) {
    if (!merge.shouldMerge) continue;

    const nodeAId = (merge as unknown as { nodeAId: string }).nodeAId;
    const nodeBId = (merge as unknown as { nodeBId: string }).nodeBId;

    if (!nodeAId || !nodeBId) continue;

    // Redirect all edges pointing to nodeB → point to nodeA
    const nodeBEdges = edges.filter(
      (e) => e.sourceId === nodeBId || e.targetId === nodeBId
    );

    for (const edge of nodeBEdges) {
      if (edge.sourceId === nodeBId) {
        // nodeB was parent → make nodeA the parent
        await db
          .update(supplyNodeEdges)
          .set({ sourceId: nodeAId })
          .where(eq(supplyNodeEdges.id, edge.id));
      }
      if (edge.targetId === nodeBId) {
        // nodeB was child → make nodeA the child (creates spider-web)
        await db
          .update(supplyNodeEdges)
          .set({ targetId: nodeAId })
          .where(eq(supplyNodeEdges.id, edge.id));
      }
    }

    // Delete nodeB
    await db.delete(supplyNodes).where(eq(supplyNodes.id, nodeBId));
  }
}
