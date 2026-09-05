import { chatCompletionJson } from "../azure/client";
import { getNodesForTree, insertDisruptions } from "../db/queries";

// Link nodes to historical disruptions

const HISTORICAL_DISRUPTIONS = [
  { name: "COVID-19 Semiconductor Shortage", year: 2020, description: "Global chip shortage caused by pandemic-related factory shutdowns and demand surges" },
  { name: "Suez Canal Blockage", year: 2021, description: "Ever Given container ship blocked Suez Canal for 6 days, disrupting global trade" },
  { name: "Texas Winter Storm Uri", year: 2021, description: "Extreme cold shut down Texas petrochemical plants, affecting resin/polymer supply" },
  { name: "Fukushima Earthquake/Tsunami", year: 2011, description: "Devastated Japanese manufacturing, especially automotive and electronics" },
  { name: "Thailand Floods", year: 2011, description: "Major flooding destroyed hard drive manufacturing capacity" },
  { name: "US-China Trade War", year: 2018, description: "Tariffs and restrictions on technology exports between US and China" },
  { name: "Rare Earth Export Restrictions", year: 2010, description: "China restricted rare earth element exports, affecting electronics and defense" },
  { name: "Russia-Ukraine War", year: 2022, description: "Disrupted neon gas supply (critical for chip lithography) and palladium/nickel markets" },
  { name: "COVID-19 Shipping Container Crisis", year: 2021, description: "Severe container shortage and port congestion causing global shipping delays" },
  { name: "Renesas Factory Fire", year: 2021, description: "Fire at major automotive chip factory in Japan worsened global chip shortage" },
  { name: "ASML Supply Chain", year: 2023, description: "Export restrictions on advanced lithography equipment to China" },
  { name: "Cobalt Mining Ethics", year: 2019, description: "DRC cobalt mining human rights concerns affecting battery supply chains" },
];

export async function linkDisruptionsForTree(
  treeId: string,
  company: string,
  product: string
): Promise<void> {
  const nodes = await getNodesForTree(treeId);

  const result = await chatCompletionJson<{
    links: {
      nodeId: string;
      disruptions: { name: string; severity: string }[];
    }[];
  }>(
    `You are a supply chain historian. Link supply chain nodes to relevant historical disruptions.

Historical disruptions:
${JSON.stringify(HISTORICAL_DISRUPTIONS, null, 2)}

For each node in the ${company} ${product} supply chain, identify which historical disruptions would have affected it.

Output JSON:
{
  "links": [
    {
      "nodeId": "id",
      "disruptions": [
        { "name": "exact disruption name from list", "severity": "low" | "medium" | "high" | "critical" }
      ]
    }
  ]
}

Only link disruptions that are genuinely relevant. Not every node will have disruptions.`,
    `Link these nodes to relevant disruptions:
${JSON.stringify(
  nodes.map((n) => ({ id: n.id, label: n.label, category: n.category })),
  null,
  2
)}`,
    {}
  );

  for (const link of result.links ?? []) {
    const disruptions = link.disruptions.map((d) => {
      const historical = HISTORICAL_DISRUPTIONS.find(
        (h) => h.name === d.name
      );
      return {
        name: d.name,
        description: historical?.description ?? "",
        year: historical?.year ?? 2020,
        severity: d.severity,
      };
    });

    await insertDisruptions(link.nodeId, disruptions);
  }
}
