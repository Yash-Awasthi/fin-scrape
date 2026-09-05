"use client";

import { useEffect, useState } from "react";
import type {
  SupplyNode,
  NodeCompany,
  DisruptionEvent,
  NewsArticle,
} from "@/types";

interface NodeDetailPanelProps {
  nodeId: string;
  onClose: () => void;
}

interface NodeDetail {
  node: SupplyNode;
  companies: NodeCompany[];
  disruptions: DisruptionEvent[];
  news: NewsArticle[];
}

const STATUS_COLORS: Record<string, string> = {
  confirmed_supplier: "#2ECC71",
  known_producer: "#7CB9E8",
  crowdsourced: "#F4A261",
};

const STATUS_LABELS: Record<string, string> = {
  confirmed_supplier: "Confirmed",
  known_producer: "Known Producer",
  crowdsourced: "Crowdsourced",
};

export function NodeDetailPanel({ nodeId, onClose }: NodeDetailPanelProps) {
  const [data, setData] = useState<NodeDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchDetail() {
      setLoading(true);
      try {
        const res = await fetch(`/api/nodes/${nodeId}`);
        if (res.ok) {
          setData(await res.json());
        }
      } catch (err) {
        console.error("Failed to fetch node detail:", err);
      } finally {
        setLoading(false);
      }
    }

    fetchDetail();
  }, [nodeId]);

  if (loading) {
    return (
      <div className="w-96 bg-[#0D0D0D] border-l border-[#2A2A2A] p-6 overflow-y-auto">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-[#2A2A2A] rounded w-3/4" />
          <div className="h-4 bg-[#2A2A2A] rounded w-1/2" />
          <div className="h-20 bg-[#2A2A2A] rounded" />
        </div>
      </div>
    );
  }

  if (!data) return null;

  const { node, companies, disruptions, news } = data;

  return (
    <div className="w-96 bg-[#0D0D0D] border-l border-[#2A2A2A] overflow-y-auto flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-[#2A2A2A] flex items-start justify-between">
        <div>
          <h3 className="text-lg font-semibold text-[#F5F5F5]">
            {node.label}
          </h3>
          <span className="text-xs uppercase tracking-wider text-[#8B9098]">
            {node.category.replace("-", " ")}
          </span>
        </div>
        <button
          onClick={onClose}
          className="text-[#6B7280] hover:text-[#F5F5F5] transition-colors text-xl"
        >
          x
        </button>
      </div>

      {/* Content */}
      <div className="p-4 space-y-6 flex-1">
        {/* Reasoning */}
        <div>
          <h4 className="text-xs uppercase tracking-wider text-[#7CB9E8] mb-2 font-semibold">
            Analysis
          </h4>
          <p className="text-sm text-[#8B9098] leading-relaxed">
            {node.reasoning}
          </p>
        </div>

        {/* Metrics */}
        <div className="grid grid-cols-3 gap-3">
          <div className="bg-[#1a1a1a] rounded-lg p-3 text-center">
            <div className="text-lg font-bold text-[#F5F5F5]">
              {Math.round(node.confidence * 100)}%
            </div>
            <div className="text-[10px] text-[#6B7280] uppercase">
              Confidence
            </div>
          </div>
          {node.riskScore != null && (
            <div className="bg-[#1a1a1a] rounded-lg p-3 text-center">
              <div
                className="text-lg font-bold"
                style={{
                  color:
                    node.riskScore > 0.7
                      ? "#E63946"
                      : node.riskScore > 0.4
                      ? "#F4A261"
                      : "#2ECC71",
                }}
              >
                {(node.riskScore * 100).toFixed(0)}%
              </div>
              <div className="text-[10px] text-[#6B7280] uppercase">Risk</div>
            </div>
          )}
          {node.costPercent != null && (
            <div className="bg-[#1a1a1a] rounded-lg p-3 text-center">
              <div className="text-lg font-bold text-[#F5F5F5]">
                {node.costPercent.toFixed(1)}%
              </div>
              <div className="text-[10px] text-[#6B7280] uppercase">Cost</div>
            </div>
          )}
        </div>

        {/* Companies */}
        <div>
          <h4 className="text-xs uppercase tracking-wider text-[#7CB9E8] mb-2 font-semibold">
            Companies ({companies.length})
          </h4>
          {companies.length === 0 ? (
            <p className="text-sm text-[#6B7280]">
              No suppliers discovered yet. Click &quot;Discover Suppliers&quot; to search.
            </p>
          ) : (
            <div className="space-y-2">
              {companies.map((c) => (
                <div
                  key={c.id}
                  className="bg-[#1a1a1a] rounded-lg p-3 border border-[#2A2A2A]"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-[#F5F5F5]">
                      {c.name}
                    </span>
                    <span
                      className="text-[9px] px-2 py-0.5 rounded-full font-semibold"
                      style={{
                        color: STATUS_COLORS[c.status] ?? "#8B9098",
                        background: `${STATUS_COLORS[c.status] ?? "#8B9098"}15`,
                        border: `1px solid ${STATUS_COLORS[c.status] ?? "#8B9098"}30`,
                      }}
                    >
                      {STATUS_LABELS[c.status] ?? c.status}
                    </span>
                  </div>
                  {(c.country || c.city) && (
                    <div className="text-xs text-[#6B7280] mt-1">
                      {[c.city, c.country].filter(Boolean).join(", ")}
                    </div>
                  )}
                  {c.source && (
                    <div className="text-[10px] text-[#3A3A3A] mt-1">
                      via {c.source}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Disruptions */}
        {disruptions.length > 0 && (
          <div>
            <h4 className="text-xs uppercase tracking-wider text-[#E63946] mb-2 font-semibold">
              Historical Disruptions
            </h4>
            <div className="space-y-2">
              {disruptions.map((d) => (
                <div
                  key={d.id}
                  className="bg-[#1a1a1a] rounded-lg p-3 border border-[#2A2A2A] border-l-2"
                  style={{
                    borderLeftColor:
                      d.severity === "critical"
                        ? "#E63946"
                        : d.severity === "high"
                        ? "#F4A261"
                        : "#6B7280",
                  }}
                >
                  <div className="text-sm font-medium text-[#F5F5F5]">
                    {d.name}
                  </div>
                  <div className="text-xs text-[#6B7280] mt-1">
                    {d.year} &middot; {d.severity} severity
                  </div>
                  {d.description && (
                    <div className="text-xs text-[#8B9098] mt-1">
                      {d.description}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* News */}
        {news.length > 0 && (
          <div>
            <h4 className="text-xs uppercase tracking-wider text-[#7CB9E8] mb-2 font-semibold">
              Recent News
            </h4>
            <div className="space-y-2">
              {news.map((article, i) => (
                <a
                  key={i}
                  href={article.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block bg-[#1a1a1a] rounded-lg p-3 border border-[#2A2A2A] hover:border-[#7CB9E8] transition-colors"
                >
                  <div className="text-sm text-[#F5F5F5] leading-snug">
                    {article.title}
                  </div>
                  <div className="text-[10px] text-[#6B7280] mt-1">
                    {article.source} &middot;{" "}
                    {new Date(article.publishedAt).toLocaleDateString()}
                  </div>
                </a>
              ))}
            </div>
          </div>
        )}

        {/* Suggest correction */}
        <div className="border-t border-[#2A2A2A] pt-4">
          <button
            className="w-full text-sm text-[#6B7280] hover:text-[#7CB9E8] transition-colors py-2 border border-[#2A2A2A] rounded-lg hover:border-[#7CB9E8]"
            onClick={() => {
              // TODO: open contribution modal (requires auth)
              alert("Sign in with GitHub to suggest corrections");
            }}
          >
            Suggest Correction
          </button>
        </div>
      </div>
    </div>
  );
}
