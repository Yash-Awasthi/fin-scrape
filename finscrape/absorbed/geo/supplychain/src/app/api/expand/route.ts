import { NextResponse } from "next/server";
import { expandNode } from "@/lib/tree/expander";
import { consolidateTree } from "@/lib/tree/consolidator";
import { getProduct } from "@/lib/db/queries";

export async function POST(req: Request) {
  try {
    const { nodeId, treeId, productId } = await req.json();

    if (!nodeId || !treeId || !productId) {
      return NextResponse.json(
        { error: "nodeId, treeId, and productId are required" },
        { status: 400 }
      );
    }

    const product = await getProduct(productId);
    if (!product) {
      return NextResponse.json({ error: "Product not found" }, { status: 404 });
    }

    // Expand the node
    await expandNode(nodeId, treeId, product.company, product.product);

    // Run consolidation after expansion
    await consolidateTree(treeId);

    return NextResponse.json({ success: true });
  } catch (err) {
    console.error("[API /expand] Error:", err);
    return NextResponse.json(
      { error: err instanceof Error ? err.message : "Expansion failed" },
      { status: 500 }
    );
  }
}
