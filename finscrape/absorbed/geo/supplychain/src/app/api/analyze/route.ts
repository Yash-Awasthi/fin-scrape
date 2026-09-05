import { NextResponse } from "next/server";
import { generateSupplyChain } from "@/lib/tree/generator";
import { isDbConfigured } from "@/lib/db/index";

export async function POST(req: Request) {
  try {
    const { company, product } = await req.json();

    if (!company || !product) {
      return NextResponse.json(
        { error: "company and product are required" },
        { status: 400 }
      );
    }

    if (!isDbConfigured()) {
      return NextResponse.json(
        { error: "Database not configured. Set DATABASE_URL environment variable." },
        { status: 500 }
      );
    }

    // Start analysis pipeline (runs async, returns immediately with product ID)
    const { product: productRecord } = await generateSupplyChain(company, product);

    return NextResponse.json({
      productId: productRecord.id,
      status: "analyzing",
    });
  } catch (err) {
    console.error("[API /analyze] Error:", err);
    return NextResponse.json(
      { error: err instanceof Error ? err.message : "Analysis failed" },
      { status: 500 }
    );
  }
}
