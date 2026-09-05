import { chatCompletionJson } from "../azure/client";
import { getNodesForTree, updateNodeCost } from "../db/queries";

// Cost % estimation per node (L1 nodes sum to ~100%)

export async function estimateCostsForTree(
  treeId: string,
  company: string,
  product: string
): Promise<void> {
  const nodes = await getNodesForTree(treeId);

  const nodeInfo = nodes.map((n) => ({
    id: n.id,
    label: n.label,
    level: n.level,
    category: n.category,
  }));

  const result = await chatCompletionJson<{
    costs: { nodeId: string; costPercent: number }[];
  }>(
    `You are a cost analyst for ${company} ${product}.
Estimate what percentage of the final product cost each component represents.

Rules:
- Level 1 nodes should sum to approximately 100%
- Level 2 nodes should sum to their parent's cost percentage
- Level 3 nodes should sum to their parent's cost percentage
- Use your knowledge of typical manufacturing costs for this product

Output JSON:
{
  "costs": [
    { "nodeId": "id", "costPercent": 0.0 to 100.0 }
  ]
}`,
    `Estimate cost percentages for:
${JSON.stringify(nodeInfo, null, 2)}`,
    {}
  );

  for (const cost of result.costs ?? []) {
    await updateNodeCost(cost.nodeId, cost.costPercent);
  }
}
