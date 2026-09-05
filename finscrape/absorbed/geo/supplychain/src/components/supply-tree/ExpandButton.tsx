"use client";

import { useState } from "react";

interface ExpandButtonProps {
  nodeId: string;
  treeId: string;
  productId: string;
  onExpanded: () => void;
}

export function ExpandButton({
  nodeId,
  treeId,
  productId,
  onExpanded,
}: ExpandButtonProps) {
  const [loading, setLoading] = useState(false);

  const handleExpand = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/expand", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ nodeId, treeId, productId }),
      });

      if (res.ok) {
        onExpanded();
      }
    } catch (err) {
      console.error("Expand failed:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      onClick={handleExpand}
      disabled={loading}
      className="absolute -bottom-3 left-1/2 -translate-x-1/2 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold transition-all duration-200 hover:scale-110 z-10"
      style={{
        background: "#1a1a1a",
        border: "1px solid #7CB9E8",
        color: "#7CB9E8",
        cursor: loading ? "wait" : "pointer",
        opacity: loading ? 0.5 : 1,
      }}
    >
      {loading ? "..." : "+"}
    </button>
  );
}
