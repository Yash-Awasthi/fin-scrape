import { NextResponse } from "next/server";
import {
  getNode,
  getCompaniesForNode,
  getDisruptionsForNode,
} from "@/lib/db/queries";
import { fetchNewsForNode } from "@/lib/news/enrichment";

export async function GET(
  _req: Request,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params;

    const node = await getNode(id);
    if (!node) {
      return NextResponse.json({ error: "Node not found" }, { status: 404 });
    }

    const [companies, disruptions] = await Promise.all([
      getCompaniesForNode(id),
      getDisruptionsForNode(id),
    ]);

    // Fetch news (non-blocking, best-effort)
    let news: Awaited<ReturnType<typeof fetchNewsForNode>> = [];
    try {
      const companyNames = companies.map((c) => c.name);
      news = await fetchNewsForNode(node.label, companyNames);
    } catch {
      news = [];
    }

    return NextResponse.json({
      node,
      companies,
      disruptions,
      news,
    });
  } catch (err) {
    console.error("[API /nodes/:id] Error:", err);
    return NextResponse.json(
      { error: err instanceof Error ? err.message : "Failed to load node" },
      { status: 500 }
    );
  }
}
