import { chatCompletionJson } from "../azure/client";
import { getNodesForTree, getCompaniesForNode, updateNodeRisk } from "../db/queries";

// Risk scoring per node: geopolitical, single-supplier, shipping distance, natural disaster

interface RiskAssessment {
  nodeId: string;
  riskScore: number; // 0-1
  factors: {
    geopolitical: number;
    supplierConcentration: number;
    shippingRisk: number;
    naturalDisaster: number;
  };
}

export async function scoreRisksForTree(treeId: string): Promise<void> {
  const nodes = await getNodesForTree(treeId);

  // Get companies for each node
  const nodeCompanyInfo: {
    id: string;
    label: string;
    category: string;
    companies: string[];
    countries: string[];
  }[] = [];

  for (const node of nodes) {
    const companies = await getCompaniesForNode(node.id);
    nodeCompanyInfo.push({
      id: node.id,
      label: node.label,
      category: node.category,
      companies: companies.map((c) => c.name),
      countries: companies.map((c) => c.country).filter(Boolean) as string[],
    });
  }

  // Ask LLM for risk scoring
  const result = await chatCompletionJson<{ risks: RiskAssessment[] }>(
    `You are a supply chain risk analyst. For each component node, assess risk on a 0-1 scale.

Consider:
- Geopolitical risk: Are suppliers in politically unstable regions? Trade war exposure?
- Supplier concentration: Single-source vs many suppliers?
- Shipping risk: Long shipping distances? Chokepoint routes (Suez, Malacca)?
- Natural disaster risk: Earthquake, typhoon, flood zones?

Output JSON:
{
  "risks": [
    {
      "nodeId": "id",
      "riskScore": 0.0 to 1.0,
      "factors": {
        "geopolitical": 0.0 to 1.0,
        "supplierConcentration": 0.0 to 1.0,
        "shippingRisk": 0.0 to 1.0,
        "naturalDisaster": 0.0 to 1.0
      }
    }
  ]
}`,
    `Score risks for these supply chain nodes:
${JSON.stringify(nodeCompanyInfo, null, 2)}`,
    {}
  );

  // Update DB
  for (const risk of result.risks ?? []) {
    await updateNodeRisk(risk.nodeId, risk.riskScore);
  }
}
