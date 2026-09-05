// ============================================================
// Supply Chain Intelligence — TypeScript interfaces
// ============================================================

// --- Persona Types ---
export type PersonaRole =
  | "manufacturing"
  | "materials"
  | "logistics"
  | "researcher"
  | "contrarian";

export type NodeCategory =
  | "component"
  | "sub-component"
  | "raw-material"
  | "intermediary";

export type ImportanceLevel = "low" | "medium" | "high" | "critical";

export type SupplierStatus =
  | "confirmed_supplier"
  | "known_producer"
  | "crowdsourced";

export type AnalysisStatus =
  | "pending"
  | "analyzing"
  | "ready"
  | "error";

// --- Persona Proposal ---
export interface ProposedSupplyNode {
  tempId: string;
  parentTempId: string | null;
  label: string;
  level: number;
  category: NodeCategory;
  importance: ImportanceLevel;
  reasoning: string;
}

export interface PersonaProposal {
  persona: PersonaRole;
  nodes: ProposedSupplyNode[];
}

// --- Vote Result ---
export interface NodeVote {
  tempId: string;
  accurate: boolean;
  importance: ImportanceLevel;
  reasoning: string;
}

// --- Database Record Types ---
export interface Product {
  id: string;
  company: string;
  product: string;
  status: AnalysisStatus;
  createdAt: string;
  updatedAt: string;
}

export interface SupplyTree {
  id: string;
  productId: string;
  version: number;
  createdAt: string;
}

export interface SupplyNode {
  id: string;
  treeId: string;
  label: string;
  category: NodeCategory;
  level: number;
  confidence: number; // 0-1 (votes/5)
  importance: ImportanceLevel;
  costPercent: number | null;
  riskScore: number | null;
  reasoning: string;
  expanded: boolean;
  createdAt: string;
}

export interface SupplyNodeEdge {
  id: string;
  treeId: string;
  sourceId: string;
  targetId: string;
}

export interface NodeCompany {
  id: string;
  nodeId: string;
  name: string;
  country: string | null;
  city: string | null;
  lat: number | null;
  lon: number | null;
  status: SupplierStatus;
  source: string | null;
  createdAt: string;
}

export interface DisruptionEvent {
  id: string;
  nodeId: string;
  name: string;
  description: string;
  year: number;
  severity: string;
}

export interface UserContribution {
  id: string;
  userId: string;
  nodeId: string | null;
  treeId: string;
  type: "add_node" | "correct_node" | "add_company" | "report_issue";
  data: Record<string, unknown>;
  status: "pending" | "approved" | "rejected";
  createdAt: string;
}

// --- API Response Types ---
export interface TreeResponse {
  product: Product;
  tree: SupplyTree;
  nodes: SupplyNode[];
  edges: SupplyNodeEdge[];
}

export interface NodeDetailResponse {
  node: SupplyNode;
  companies: NodeCompany[];
  disruptions: DisruptionEvent[];
  news: NewsArticle[];
}

export interface NewsArticle {
  title: string;
  source: string;
  url: string;
  publishedAt: string;
  summary: string;
}

// --- Globe Pin ---
export interface GlobePin {
  lat: number;
  lon: number;
  color: "red" | "amber" | "green";
  label: string;
  company: string;
  country: string;
}

// --- React Flow Display ---
export interface SupplyNodeData {
  label: string;
  level: number;
  category: NodeCategory;
  confidence: number;
  importance: ImportanceLevel;
  costPercent: number | null;
  riskScore: number | null;
  reasoning: string;
  expanded: boolean;
  isRoot: boolean;
}
