import { chatCompletionJson } from "../azure/client";
import { personas } from "../azure/personas";
import {
  getNode,
  markNodeExpanded,
  insertNodes,
} from "../db/queries";
import type { ProposedSupplyNode, ImportanceLevel } from "@/types";

// Expand a leaf node 1 level deeper using mini-council

export async function expandNode(
  nodeId: string,
  treeId: string,
  company: string,
  product: string
): Promise<void> {
  const node = await getNode(nodeId);
  if (!node) throw new Error("Node not found");
  if (node.expanded) throw new Error("Node already expanded");

  const systemPrompt = `You are analyzing the supply chain for ${company} ${product}.
You need to decompose the component "${node.label}" (category: ${node.category}) into its sub-components and raw materials.

Output valid JSON:
{
  "nodes": [
    {
      "tempId": "expand-1",
      "parentTempId": "parent",
      "label": "Sub-component name",
      "level": ${node.level + 1},
      "category": "sub-component" | "raw-material" | "intermediary",
      "importance": "low" | "medium" | "high" | "critical",
      "reasoning": "1-2 sentence explanation"
    }
  ]
}

Rules:
- All nodes should have parentTempId = "parent" (they are children of "${node.label}")
- Generate 2-5 child nodes
- Be specific about materials, chemicals, or sub-parts`;

  const userPrompt = `Decompose "${node.label}" into its constituent parts for ${company} ${product}.`;

  // Mini-council: all 5 personas propose, then merge via voting
  const allProposals = await Promise.all(
    personas.map(async (persona) => {
      try {
        const result = await chatCompletionJson<{ nodes: ProposedSupplyNode[] }>(
          `${persona.systemPrompt}\n\n${systemPrompt}`,
          userPrompt,
          {}
        );
        return result.nodes ?? [];
      } catch {
        return [];
      }
    })
  );

  // Simple merge: collect all unique labels, deduplicate, count votes
  const labelMap = new Map<
    string,
    {
      node: ProposedSupplyNode;
      count: number;
      importances: ImportanceLevel[];
    }
  >();

  for (const proposals of allProposals) {
    for (const n of proposals) {
      const key = n.label.toLowerCase().trim();
      const existing = labelMap.get(key);
      if (existing) {
        existing.count++;
        existing.importances.push(n.importance);
      } else {
        labelMap.set(key, {
          node: { ...n, parentTempId: "parent" },
          count: 1,
          importances: [n.importance],
        });
      }
    }
  }

  // Filter: include if 2+ personas mentioned it
  const filteredNodes: ProposedSupplyNode[] = [];
  const confidenceMap = new Map<
    string,
    { confidence: number; importance: ImportanceLevel; reasoning: string }
  >();

  let idx = 0;
  for (const [, entry] of Array.from(labelMap.entries())) {
    if (entry.count >= 2) {
      const tempId = `expand-${idx++}`;
      const node_data = { ...entry.node, tempId, parentTempId: "parent" };
      filteredNodes.push(node_data);

      // Most common importance
      const impCounts: Record<ImportanceLevel, number> = { low: 0, medium: 0, high: 0, critical: 0 };
      for (const imp of entry.importances) impCounts[imp]++;
      const importance = (Object.entries(impCounts) as [ImportanceLevel, number][])
        .sort((a, b) => b[1] - a[1])[0][0];

      confidenceMap.set(tempId, {
        confidence: entry.count / 5,
        importance,
        reasoning: entry.node.reasoning,
      });
    }
  }

  // Remap parentTempId to actual node ID
  const remappedNodes = filteredNodes.map((n) => ({
    ...n,
    parentTempId: null as string | null,
  }));

  // Insert into DB, creating edges from nodeId to each new child
  const { nodeMap } = await insertNodes(treeId, remappedNodes, confidenceMap);

  // Create edges from the parent node to each new child
  // (insertNodes creates edges based on parentTempId, but we set it to null above)
  // We need to manually create parent→child edges
  const { db } = await import("../db/index");
  const { supplyNodeEdges } = await import("../db/schema");

  for (const [, childId] of Array.from(nodeMap.entries())) {
    await db.insert(supplyNodeEdges).values({
      treeId,
      sourceId: nodeId,
      targetId: childId,
    });
  }

  // Mark original node as expanded
  await markNodeExpanded(nodeId);
}
