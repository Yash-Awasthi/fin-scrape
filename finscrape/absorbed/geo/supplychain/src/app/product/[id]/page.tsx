"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import dynamic from "next/dynamic";
import { SupplyTreeView } from "@/components/supply-tree/SupplyTree";
import type { Product, SupplyNode, SupplyNodeEdge, NodeCompany, GlobePin } from "@/types";

// Dynamic import for Globe (needs client-only, no SSR)
const GlobeView = dynamic(() => import("@/components/globe/GlobeView"), {
  ssr: false,
  loading: () => (
    <div className="w-full h-[calc(100vh-200px)] flex items-center justify-center bg-[#0A0A0A]">
      <div className="text-[#6B7280] text-sm">Loading globe...</div>
    </div>
  ),
});

type Tab = "tree" | "globe";

export default function ProductPage() {
  const params = useParams();
  const id = params.id as string;

  const [tab, setTab] = useState<Tab>("tree");
  const [product, setProduct] = useState<Product | null>(null);
  const [nodes, setNodes] = useState<SupplyNode[]>([]);
  const [edges, setEdges] = useState<SupplyNodeEdge[]>([]);
  const [companies, setCompanies] = useState<NodeCompany[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      try {
        const res = await fetch(`/api/trees?productId=${id}`);
        if (!res.ok) {
          throw new Error("Failed to load supply chain data");
        }
        const data = await res.json();
        setProduct(data.product);
        setNodes(data.nodes ?? []);
        setEdges(data.edges ?? []);
        setCompanies(data.companies ?? []);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load");
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, [id]);

  // Convert companies to globe pins
  const globePins: GlobePin[] = companies
    .filter((c) => c.lat != null && c.lon != null)
    .map((c) => {
      // Find the node for this company to get risk score
      const node = nodes.find((n) => n.id === c.nodeId);
      const riskScore = node?.riskScore ?? 0.3;

      return {
        lat: c.lat!,
        lon: c.lon!,
        color: riskScore > 0.7 ? "red" : riskScore > 0.4 ? "amber" : "green",
        label: c.name,
        company: c.name,
        country: c.country ?? "Unknown",
      };
    });

  if (loading) {
    return (
      <div className="min-h-[calc(100vh-56px)] flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="w-8 h-8 border-2 border-[#7CB9E8] border-t-transparent rounded-full animate-spin mx-auto" />
          <div className="text-sm text-[#6B7280]">Loading supply chain...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-[calc(100vh-56px)] flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="text-[#E63946] text-sm">{error}</div>
          <a
            href="/"
            className="text-sm text-[#7CB9E8] hover:underline"
          >
            Back to home
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-[calc(100vh-56px)]">
      {/* Product header */}
      <div className="border-b border-[#2A2A2A] px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-[#F5F5F5]">
              {product?.product}
            </h1>
            <div className="text-sm text-[#6B7280]">{product?.company}</div>
          </div>

          <div className="flex items-center gap-4">
            {/* Stats */}
            <div className="hidden sm:flex items-center gap-4 text-xs text-[#6B7280]">
              <span>{nodes.length} nodes</span>
              <span>{edges.length} edges</span>
              <span>{companies.length} companies</span>
            </div>

            {/* Tab switcher */}
            <div className="flex bg-[#0D0D0D] border border-[#2A2A2A] rounded-lg overflow-hidden">
              <button
                onClick={() => setTab("tree")}
                className={`px-4 py-2 text-xs font-semibold transition-colors ${
                  tab === "tree"
                    ? "bg-[#7CB9E8]/10 text-[#7CB9E8] border-b-2 border-[#7CB9E8]"
                    : "text-[#6B7280] hover:text-[#F5F5F5]"
                }`}
              >
                Supply Chain
              </button>
              <button
                onClick={() => setTab("globe")}
                className={`px-4 py-2 text-xs font-semibold transition-colors ${
                  tab === "globe"
                    ? "bg-[#7CB9E8]/10 text-[#7CB9E8] border-b-2 border-[#7CB9E8]"
                    : "text-[#6B7280] hover:text-[#F5F5F5]"
                }`}
              >
                Globe View
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="px-6 py-4">
        <div className="max-w-7xl mx-auto">
          {tab === "tree" && nodes.length > 0 && (
            <SupplyTreeView supplyNodes={nodes} supplyEdges={edges} />
          )}

          {tab === "tree" && nodes.length === 0 && (
            <div className="h-[calc(100vh-200px)] flex items-center justify-center">
              <div className="text-center space-y-2">
                <div className="text-[#6B7280]">
                  {product?.status === "analyzing"
                    ? "Analysis in progress..."
                    : "No supply chain data yet"}
                </div>
                {product?.status === "analyzing" && (
                  <div className="w-6 h-6 border-2 border-[#7CB9E8] border-t-transparent rounded-full animate-spin mx-auto" />
                )}
              </div>
            </div>
          )}

          {tab === "globe" && <GlobeView pins={globePins} />}
        </div>
      </div>
    </div>
  );
}
