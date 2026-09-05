import { NextResponse } from "next/server";
import {
  getProduct,
  getTreeForProduct,
  getNodesForTree,
  getEdgesForTree,
  getAllCompaniesForTree,
} from "@/lib/db/queries";

export async function GET(req: Request) {
  try {
    const { searchParams } = new URL(req.url);
    const productId = searchParams.get("productId");

    if (!productId) {
      return NextResponse.json(
        { error: "productId is required" },
        { status: 400 }
      );
    }

    const product = await getProduct(productId);
    if (!product) {
      return NextResponse.json({ error: "Product not found" }, { status: 404 });
    }

    const tree = await getTreeForProduct(productId);
    if (!tree) {
      return NextResponse.json({
        product,
        tree: null,
        nodes: [],
        edges: [],
        companies: [],
      });
    }

    const [nodes, edges, companies] = await Promise.all([
      getNodesForTree(tree.id),
      getEdgesForTree(tree.id),
      getAllCompaniesForTree(tree.id),
    ]);

    return NextResponse.json({
      product,
      tree,
      nodes,
      edges,
      companies,
    });
  } catch (err) {
    console.error("[API /trees] Error:", err);
    return NextResponse.json(
      { error: err instanceof Error ? err.message : "Failed to load tree" },
      { status: 500 }
    );
  }
}
