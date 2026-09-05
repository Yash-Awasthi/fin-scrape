"use client";

import { useCallback, useMemo, useState } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  type Node,
  type Edge,
  type NodeTypes,
  BackgroundVariant,
  MarkerType,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { SupplyNodeMemo } from "./SupplyNode";
import { NodeDetailPanel } from "./NodeDetailPanel";
import type {
  SupplyNode as SupplyNodeType,
  SupplyNodeEdge,
  SupplyNodeData,
  NodeCategory,
} from "@/types";

const nodeTypes: NodeTypes = {
  supply: SupplyNodeMemo,
};

const CATEGORY_COLORS: Record<NodeCategory, string> = {
  component: "#7CB9E8",
  "sub-component": "#2DD4BF",
  "raw-material": "#F4A261",
  intermediary: "#A78BFA",
};

/**
 * Layout supply nodes top-down: product at top, raw materials at bottom.
 */
function layoutNodes(supplyNodes: SupplyNodeType[], edges: SupplyNodeEdge[]): Node[] {
  const LEVEL_Y_GAP = 140;
  const NODE_X_GAP = 240;

  // Build parent-children map from edges
  const childrenOf = new Map<string, string[]>();
  const parentOf = new Map<string, string[]>();

  for (const edge of edges) {
    const children = childrenOf.get(edge.sourceId) ?? [];
    children.push(edge.targetId);
    childrenOf.set(edge.sourceId, children);

    const parents = parentOf.get(edge.targetId) ?? [];
    parents.push(edge.sourceId);
    parentOf.set(edge.targetId, parents);
  }

  const nodeMap = new Map<string, SupplyNodeType>();
  for (const n of supplyNodes) {
    nodeMap.set(n.id, n);
  }

  const positions = new Map<string, { x: number; y: number }>();

  function layoutSubtree(nodeId: string, level: number, xStart: number): number {
    const children = childrenOf.get(nodeId) ?? [];
    const y = level * LEVEL_Y_GAP;

    if (children.length === 0) {
      positions.set(nodeId, { x: xStart, y });
      return xStart + NODE_X_GAP;
    }

    let currentX = xStart;
    for (const childId of children) {
      if (!positions.has(childId)) {
        currentX = layoutSubtree(childId, level + 1, currentX);
      }
    }

    // Center parent above children
    const childPositions = children
      .map((id) => positions.get(id))
      .filter(Boolean) as { x: number; y: number }[];

    if (childPositions.length > 0) {
      const minX = Math.min(...childPositions.map((p) => p.x));
      const maxX = Math.max(...childPositions.map((p) => p.x));
      positions.set(nodeId, { x: (minX + maxX) / 2, y });
    } else {
      positions.set(nodeId, { x: xStart, y });
    }

    return currentX;
  }

  // Find root nodes (no parents in edges)
  const roots = supplyNodes.filter(
    (n) => !parentOf.has(n.id) || parentOf.get(n.id)!.length === 0
  );

  let xOffset = 0;
  for (const root of roots) {
    xOffset = layoutSubtree(root.id, 0, xOffset);
  }

  // Handle orphaned nodes
  for (const n of supplyNodes) {
    if (!positions.has(n.id)) {
      positions.set(n.id, { x: xOffset, y: n.level * LEVEL_Y_GAP });
      xOffset += NODE_X_GAP;
    }
  }

  return supplyNodes.map((n) => {
    const pos = positions.get(n.id) ?? { x: 0, y: 0 };
    return {
      id: n.id,
      type: "supply",
      position: pos,
      data: {
        label: n.label,
        level: n.level,
        category: n.category,
        confidence: n.confidence,
        importance: n.importance,
        costPercent: n.costPercent,
        riskScore: n.riskScore,
        reasoning: n.reasoning,
        expanded: n.expanded,
        isRoot: n.level === 0 || (!parentOf.has(n.id)),
      } satisfies SupplyNodeData,
    };
  });
}

function toReactFlowEdges(edges: SupplyNodeEdge[]): Edge[] {
  return edges.map((e) => ({
    id: e.id,
    source: e.sourceId,
    target: e.targetId,
    type: "smoothstep",
    style: { stroke: "#3A3A3A", strokeWidth: 2 },
    markerEnd: {
      type: MarkerType.ArrowClosed,
      color: "#3A3A3A",
      width: 14,
      height: 14,
    },
    animated: false,
  }));
}

export function SupplyTreeView({
  supplyNodes,
  supplyEdges,
}: {
  supplyNodes: SupplyNodeType[];
  supplyEdges: SupplyNodeEdge[];
}) {
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

  const initialNodes = useMemo(
    () => layoutNodes(supplyNodes, supplyEdges),
    [supplyNodes, supplyEdges]
  );
  const initialEdges = useMemo(
    () => toReactFlowEdges(supplyEdges),
    [supplyEdges]
  );

  const [nodes, , onNodesChange] = useNodesState(initialNodes);
  const [edges, , onEdgesChange] = useEdgesState(initialEdges);

  const handleNodeClick = useCallback((_: React.MouseEvent, node: Node) => {
    setSelectedNodeId(node.id);
  }, []);

  return (
    <div className="flex h-[calc(100vh-200px)] min-h-[500px]">
      <div className="flex-1 bg-[#0A0A0A] rounded-lg border border-[#2A2A2A]">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={handleNodeClick}
          nodeTypes={nodeTypes}
          fitView
          fitViewOptions={{ padding: 0.3 }}
          minZoom={0.1}
          maxZoom={2}
          proOptions={{ hideAttribution: true }}
        >
          <Background
            variant={BackgroundVariant.Dots}
            color="#1a1a1a"
            gap={20}
          />
          <Controls className="!bg-[#1a1a1a] !border-[#2A2A2A]" />
          <MiniMap
            className="!bg-[#0D0D0D] !border-[#2A2A2A]"
            nodeColor={(n) => {
              const d = (n.data as unknown as SupplyNodeData)?.category;
              return CATEGORY_COLORS[d] ?? "#3A3A3A";
            }}
            maskColor="rgba(0, 0, 0, 0.7)"
          />
        </ReactFlow>
      </div>

      {selectedNodeId && (
        <NodeDetailPanel
          nodeId={selectedNodeId}
          onClose={() => setSelectedNodeId(null)}
        />
      )}
    </div>
  );
}
