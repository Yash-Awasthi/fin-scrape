import { runFullDebate } from "../azure/debate";
import { searchTeardownReports } from "../datasources/websearch";
import {
  createProduct,
  createTree,
  insertNodes,
  updateProductStatus,
} from "../db/queries";
import type { Product, SupplyTree } from "@/types";

// Orchestrates the full analysis pipeline

export async function generateSupplyChain(
  company: string,
  product: string
): Promise<{ product: Product; tree: SupplyTree }> {
  // Create product record
  const productRecord = await createProduct(company, product);

  try {
    // Update status to analyzing
    await updateProductStatus(productRecord.id, "analyzing");

    // Get research context for researcher persona
    const researchContext = await searchTeardownReports(company, product);

    // Run the full council debate pipeline
    const { nodes, confidences } = await runFullDebate(
      company,
      product,
      researchContext
    );

    // Create tree record
    const tree = await createTree(productRecord.id);

    // Insert nodes and edges into DB
    await insertNodes(tree.id, nodes, confidences);

    // Update status to ready
    await updateProductStatus(productRecord.id, "ready");

    return { product: productRecord, tree };
  } catch (err) {
    console.error("[Generator] Pipeline failed:", err);
    await updateProductStatus(productRecord.id, "error");
    throw err;
  }
}
