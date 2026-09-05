"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import type { Product } from "@/types";

export default function HomePage() {
  const router = useRouter();
  const [company, setCompany] = useState("");
  const [product, setProduct] = useState("");
  const [loading, setLoading] = useState(false);
  const [products, setProducts] = useState<Product[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchProducts() {
      try {
        const res = await fetch("/api/products");
        if (res.ok) {
          const data = await res.json();
          setProducts(data.products ?? []);
        }
      } catch {
        // DB may not be configured yet
      }
    }
    fetchProducts();
  }, []);

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!company.trim() || !product.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const res = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ company: company.trim(), product: product.trim() }),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.error ?? "Analysis failed");
      }

      const data = await res.json();
      router.push(`/product/${data.productId}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-56px)] flex flex-col">
      {/* Hero */}
      <div className="flex-1 flex flex-col items-center justify-center px-6 py-20">
        <div className="max-w-2xl w-full text-center space-y-8">
          <div>
            <h1 className="text-4xl sm:text-5xl font-extrabold leading-tight">
              <span className="block text-[#F5F5F5]">Supply Chain</span>
              <span className="block text-[#7CB9E8]">Intelligence</span>
            </h1>
            <p className="mt-4 text-[#8B9098] text-base max-w-md mx-auto leading-relaxed">
              Enter a company and product. A council of 5 AI personas will
              decompose its entire supply chain — every component, material, and
              supplier.
            </p>
          </div>

          <form onSubmit={handleAnalyze} className="space-y-4">
            <div className="flex flex-col sm:flex-row gap-3">
              <input
                type="text"
                placeholder="Company (e.g. Apple)"
                value={company}
                onChange={(e) => setCompany(e.target.value)}
                className="flex-1 bg-[#0D0D0D] border border-[#2A2A2A] rounded-lg px-4 py-3 text-sm text-[#F5F5F5] placeholder:text-[#6B7280] focus:outline-none focus:border-[#7CB9E8] transition-colors"
              />
              <input
                type="text"
                placeholder="Product (e.g. iPhone 16 Pro)"
                value={product}
                onChange={(e) => setProduct(e.target.value)}
                className="flex-1 bg-[#0D0D0D] border border-[#2A2A2A] rounded-lg px-4 py-3 text-sm text-[#F5F5F5] placeholder:text-[#6B7280] focus:outline-none focus:border-[#7CB9E8] transition-colors"
              />
            </div>

            <button
              type="submit"
              disabled={loading || !company.trim() || !product.trim()}
              className="w-full sm:w-auto px-8 py-3 bg-transparent border border-[#7CB9E8] text-[#7CB9E8] rounded-lg text-sm font-semibold hover:bg-[#7CB9E8]/10 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="w-4 h-4 border-2 border-[#7CB9E8] border-t-transparent rounded-full animate-spin" />
                  Analyzing...
                </span>
              ) : (
                "Analyze Supply Chain"
              )}
            </button>

            {error && (
              <p className="text-sm text-[#E63946]">{error}</p>
            )}
          </form>

          {/* How it works */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-8 border-t border-[#2A2A2A]">
            <div className="text-center p-4">
              <div className="text-2xl font-bold text-[#7CB9E8] mb-1">5</div>
              <div className="text-xs text-[#6B7280] uppercase tracking-wider">
                AI Personas
              </div>
              <p className="text-xs text-[#8B9098] mt-2">
                Manufacturing, materials, logistics, research, contrarian
              </p>
            </div>
            <div className="text-center p-4">
              <div className="text-2xl font-bold text-[#7CB9E8] mb-1">3</div>
              <div className="text-xs text-[#6B7280] uppercase tracking-wider">
                Step Pipeline
              </div>
              <p className="text-xs text-[#8B9098] mt-2">
                Generate, merge/dedup, vote for consensus
              </p>
            </div>
            <div className="text-center p-4">
              <div className="text-2xl font-bold text-[#7CB9E8] mb-1">6+</div>
              <div className="text-xs text-[#6B7280] uppercase tracking-wider">
                Data Sources
              </div>
              <p className="text-xs text-[#8B9098] mt-2">
                UN Comtrade, OpenCorporates, Wikidata, EDGAR, OSH
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Recent analyses */}
      {products.length > 0 && (
        <div className="max-w-4xl mx-auto w-full px-6 pb-16">
          <h2 className="text-xs uppercase tracking-widest text-[#6B7280] mb-4 font-semibold">
            Recent Analyses
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {products.map((p) => (
              <a
                key={p.id}
                href={`/product/${p.id}`}
                className="block bg-[#0D0D0D] border border-[#2A2A2A] rounded-lg p-4 hover:border-[#7CB9E8] transition-colors group"
              >
                <div className="text-sm font-semibold text-[#F5F5F5] group-hover:text-[#7CB9E8] transition-colors">
                  {p.product}
                </div>
                <div className="text-xs text-[#6B7280] mt-1">{p.company}</div>
                <div className="flex items-center gap-2 mt-2">
                  <span
                    className="text-[9px] px-2 py-0.5 rounded-full font-semibold"
                    style={{
                      color:
                        p.status === "ready"
                          ? "#2ECC71"
                          : p.status === "analyzing"
                          ? "#F4A261"
                          : p.status === "error"
                          ? "#E63946"
                          : "#6B7280",
                      background:
                        p.status === "ready"
                          ? "rgba(46, 204, 113, 0.1)"
                          : p.status === "analyzing"
                          ? "rgba(244, 162, 97, 0.1)"
                          : p.status === "error"
                          ? "rgba(230, 57, 70, 0.1)"
                          : "rgba(107, 114, 128, 0.1)",
                    }}
                  >
                    {p.status}
                  </span>
                </div>
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
