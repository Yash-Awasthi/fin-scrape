import { NextResponse } from "next/server";
import { discoverSuppliersForNode } from "@/lib/tree/supplier-discovery";
import { getProduct } from "@/lib/db/queries";

export async function POST(req: Request) {
  try {
    const { nodeId, productId } = await req.json();

    if (!nodeId || !productId) {
      return NextResponse.json(
        { error: "nodeId and productId are required" },
        { status: 400 }
      );
    }

    const product = await getProduct(productId);
    if (!product) {
      return NextResponse.json({ error: "Product not found" }, { status: 404 });
    }

    await discoverSuppliersForNode(nodeId, product.company, product.product);

    return NextResponse.json({ success: true });
  } catch (err) {
    console.error("[API /suppliers] Error:", err);
    return NextResponse.json(
      { error: err instanceof Error ? err.message : "Supplier discovery failed" },
      { status: 500 }
    );
  }
}
