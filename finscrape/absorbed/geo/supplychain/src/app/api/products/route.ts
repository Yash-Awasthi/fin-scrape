import { NextResponse } from "next/server";
import { listProducts } from "@/lib/db/queries";
import { isDbConfigured } from "@/lib/db/index";

export async function GET() {
  try {
    if (!isDbConfigured()) {
      return NextResponse.json({ products: [] });
    }

    const products = await listProducts();
    return NextResponse.json({ products });
  } catch (err) {
    console.error("[API /products] Error:", err);
    return NextResponse.json({ products: [] });
  }
}
