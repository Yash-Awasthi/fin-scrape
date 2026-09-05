"use client";

import { memo } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import type { SupplyNodeData, NodeCategory } from "@/types";

const CATEGORY_COLORS: Record<NodeCategory, string> = {
  component: "#7CB9E8",         // blue
  "sub-component": "#2DD4BF",   // teal
  "raw-material": "#F4A261",    // amber
  intermediary: "#A78BFA",      // purple
};

const CATEGORY_BG: Record<NodeCategory, string> = {
  component: "rgba(124, 185, 232, 0.08)",
  "sub-component": "rgba(45, 212, 191, 0.08)",
  "raw-material": "rgba(244, 162, 97, 0.08)",
  intermediary: "rgba(167, 139, 250, 0.08)",
};

const IMPORTANCE_ICONS: Record<string, string> = {
  low: "",
  medium: "",
  high: "!",
  critical: "!!",
};

function SupplyNodeComponent({ data }: NodeProps) {
  const nodeData = data as unknown as SupplyNodeData;
  const color = CATEGORY_COLORS[nodeData.category] ?? "#7CB9E8";
  const bgColor = CATEGORY_BG[nodeData.category] ?? "rgba(124, 185, 232, 0.08)";
  const isUncertain = nodeData.confidence < 0.8;
  const borderStyle = isUncertain ? "dashed" : "solid";

  return (
    <div
      className="relative group"
      style={{
        minWidth: nodeData.isRoot ? 220 : 180,
        maxWidth: 260,
      }}
    >
      {/* Input handle (top) */}
      {!nodeData.isRoot && (
        <Handle
          type="target"
          position={Position.Top}
          className="!bg-transparent !border-0 !w-3 !h-3"
          style={{ background: color }}
        />
      )}

      {/* Node body */}
      <div
        className="rounded-lg px-3 py-2 cursor-pointer transition-all duration-200 hover:scale-105"
        style={{
          background: bgColor,
          border: `2px ${borderStyle} ${color}`,
          boxShadow: `0 0 ${nodeData.isRoot ? "20px" : "10px"} ${color}22`,
        }}
      >
        {/* Category badge */}
        <div className="flex items-center justify-between mb-1">
          <span
            className="text-[9px] uppercase tracking-wider font-semibold"
            style={{ color }}
          >
            {nodeData.category.replace("-", " ")}
          </span>
          {nodeData.importance !== "low" && (
            <span
              className="text-[9px] font-bold px-1 rounded"
              style={{
                color: nodeData.importance === "critical" ? "#E63946" : color,
                background:
                  nodeData.importance === "critical"
                    ? "rgba(230, 57, 70, 0.15)"
                    : `${color}15`,
              }}
            >
              {IMPORTANCE_ICONS[nodeData.importance]}
              {nodeData.importance.toUpperCase()}
            </span>
          )}
        </div>

        {/* Label */}
        <div
          className="text-sm font-semibold leading-tight"
          style={{ color: "#F5F5F5" }}
        >
          {nodeData.label}
        </div>

        {/* Metrics row */}
        <div className="flex items-center gap-2 mt-1.5">
          {/* Confidence */}
          <span className="text-[10px]" style={{ color: "#8B9098" }}>
            {Math.round(nodeData.confidence * 100)}%
          </span>

          {/* Risk score */}
          {nodeData.riskScore != null && (
            <span
              className="text-[10px] font-medium"
              style={{
                color:
                  nodeData.riskScore > 0.7
                    ? "#E63946"
                    : nodeData.riskScore > 0.4
                    ? "#F4A261"
                    : "#2ECC71",
              }}
            >
              Risk: {(nodeData.riskScore * 100).toFixed(0)}%
            </span>
          )}

          {/* Cost */}
          {nodeData.costPercent != null && (
            <span className="text-[10px]" style={{ color: "#8B9098" }}>
              {nodeData.costPercent.toFixed(1)}%
            </span>
          )}
        </div>
      </div>

      {/* Output handle (bottom) */}
      <Handle
        type="source"
        position={Position.Bottom}
        className="!bg-transparent !border-0 !w-3 !h-3"
        style={{ background: color }}
      />
    </div>
  );
}

export const SupplyNodeMemo = memo(SupplyNodeComponent);
