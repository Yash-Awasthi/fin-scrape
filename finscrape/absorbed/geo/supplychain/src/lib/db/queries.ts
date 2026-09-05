import { eq, desc } from "drizzle-orm";
import { db } from "./index";
import {
  products,
  supplyTrees,
  supplyNodes,
  supplyNodeEdges,
  nodeCompanies,
  disruptionEvents,
  userContributions,
} from "./schema";
import type {
  Product,
  SupplyTree,
  SupplyNode,
  SupplyNodeEdge,
  NodeCompany,
  DisruptionEvent,
  ProposedSupplyNode,
  ImportanceLevel,
} from "@/types";

// ----- Products -----

export async function createProduct(
  company: string,
  product: string
): Promise<Product> {
  const [row] = await db
    .insert(products)
    .values({ company, product, status: "pending" })
    .returning();
  return row as unknown as Product;
}

export async function updateProductStatus(
  id: string,
  status: string
): Promise<void> {
  await db
    .update(products)
    .set({ status, updatedAt: new Date().toISOString() })
    .where(eq(products.id, id));
}

export async function listProducts(): Promise<Product[]> {
  const rows = await db
    .select()
    .from(products)
    .orderBy(desc(products.createdAt));
  return rows as unknown as Product[];
}

export async function getProduct(id: string): Promise<Product | null> {
  const [row] = await db
    .select()
    .from(products)
    .where(eq(products.id, id));
  return (row as unknown as Product) ?? null;
}

// ----- Trees -----

export async function createTree(productId: string): Promise<SupplyTree> {
  const [row] = await db
    .insert(supplyTrees)
    .values({ productId })
    .returning();
  return row as unknown as SupplyTree;
}

export async function getTreeForProduct(
  productId: string
): Promise<SupplyTree | null> {
  const [row] = await db
    .select()
    .from(supplyTrees)
    .where(eq(supplyTrees.productId, productId))
    .orderBy(desc(supplyTrees.version))
    .limit(1);
  return (row as unknown as SupplyTree) ?? null;
}

// ----- Nodes -----

export async function insertNodes(
  treeId: string,
  proposedNodes: ProposedSupplyNode[],
  confidences: Map<
    string,
    { confidence: number; importance: ImportanceLevel; reasoning: string }
  >
): Promise<{ nodeMap: Map<string, string>; nodes: SupplyNode[] }> {
  const nodeMap = new Map<string, string>(); // tempId → real id
  const insertedNodes: SupplyNode[] = [];

  // Insert level by level so parents exist before children
  for (let level = 1; level <= 3; level++) {
    const levelNodes = proposedNodes.filter((n) => n.level === level);

    for (const node of levelNodes) {
      const vote = confidences.get(node.tempId);
      const [row] = await db
        .insert(supplyNodes)
        .values({
          treeId,
          label: node.label,
          category: node.category,
          level: node.level,
          confidence: vote?.confidence ?? 0.6,
          importance: vote?.importance ?? node.importance,
          reasoning: vote?.reasoning ?? node.reasoning,
        })
        .returning();

      nodeMap.set(node.tempId, row.id);
      insertedNodes.push(row as unknown as SupplyNode);
    }
  }

  // Create edges based on parentTempId
  for (const node of proposedNodes) {
    if (node.parentTempId) {
      const sourceId = nodeMap.get(node.parentTempId);
      const targetId = nodeMap.get(node.tempId);
      if (sourceId && targetId) {
        await db.insert(supplyNodeEdges).values({
          treeId,
          sourceId,
          targetId,
        });
      }
    }
  }

  return { nodeMap, nodes: insertedNodes };
}

export async function getNodesForTree(
  treeId: string
): Promise<SupplyNode[]> {
  const rows = await db
    .select()
    .from(supplyNodes)
    .where(eq(supplyNodes.treeId, treeId));
  return rows as unknown as SupplyNode[];
}

export async function getEdgesForTree(
  treeId: string
): Promise<SupplyNodeEdge[]> {
  const rows = await db
    .select()
    .from(supplyNodeEdges)
    .where(eq(supplyNodeEdges.treeId, treeId));
  return rows as unknown as SupplyNodeEdge[];
}

export async function getNode(id: string): Promise<SupplyNode | null> {
  const [row] = await db
    .select()
    .from(supplyNodes)
    .where(eq(supplyNodes.id, id));
  return (row as unknown as SupplyNode) ?? null;
}

export async function markNodeExpanded(id: string): Promise<void> {
  await db
    .update(supplyNodes)
    .set({ expanded: true })
    .where(eq(supplyNodes.id, id));
}

// ----- Companies -----

export async function insertCompanies(
  nodeId: string,
  companies: {
    name: string;
    country?: string;
    city?: string;
    lat?: number;
    lon?: number;
    status: string;
    source?: string;
  }[]
): Promise<NodeCompany[]> {
  if (companies.length === 0) return [];

  const rows = await db
    .insert(nodeCompanies)
    .values(
      companies.map((c) => ({
        nodeId,
        name: c.name,
        country: c.country ?? null,
        city: c.city ?? null,
        lat: c.lat ?? null,
        lon: c.lon ?? null,
        status: c.status,
        source: c.source ?? null,
      }))
    )
    .returning();

  return rows as unknown as NodeCompany[];
}

export async function getCompaniesForNode(
  nodeId: string
): Promise<NodeCompany[]> {
  const rows = await db
    .select()
    .from(nodeCompanies)
    .where(eq(nodeCompanies.nodeId, nodeId));
  return rows as unknown as NodeCompany[];
}

export async function getAllCompaniesForTree(
  treeId: string
): Promise<NodeCompany[]> {
  const nodes = await getNodesForTree(treeId);
  const nodeIds = nodes.map((n) => n.id);
  if (nodeIds.length === 0) return [];

  const allCompanies: NodeCompany[] = [];
  for (const nodeId of nodeIds) {
    const companies = await getCompaniesForNode(nodeId);
    allCompanies.push(...companies);
  }
  return allCompanies;
}

// ----- Disruptions -----

export async function insertDisruptions(
  nodeId: string,
  disruptions: {
    name: string;
    description: string;
    year: number;
    severity: string;
  }[]
): Promise<DisruptionEvent[]> {
  if (disruptions.length === 0) return [];

  const rows = await db
    .insert(disruptionEvents)
    .values(
      disruptions.map((d) => ({
        nodeId,
        name: d.name,
        description: d.description,
        year: d.year,
        severity: d.severity,
      }))
    )
    .returning();

  return rows as unknown as DisruptionEvent[];
}

export async function getDisruptionsForNode(
  nodeId: string
): Promise<DisruptionEvent[]> {
  const rows = await db
    .select()
    .from(disruptionEvents)
    .where(eq(disruptionEvents.nodeId, nodeId));
  return rows as unknown as DisruptionEvent[];
}

// ----- Contributions -----

export async function createContribution(
  userId: string,
  treeId: string,
  nodeId: string | null,
  type: string,
  data: Record<string, unknown>
): Promise<void> {
  await db.insert(userContributions).values({
    userId,
    treeId,
    nodeId,
    type,
    data,
  });
}

// ----- Node update helpers -----

export async function updateNodeRisk(
  id: string,
  riskScore: number
): Promise<void> {
  await db
    .update(supplyNodes)
    .set({ riskScore })
    .where(eq(supplyNodes.id, id));
}

export async function updateNodeCost(
  id: string,
  costPercent: number
): Promise<void> {
  await db
    .update(supplyNodes)
    .set({ costPercent })
    .where(eq(supplyNodes.id, id));
}
