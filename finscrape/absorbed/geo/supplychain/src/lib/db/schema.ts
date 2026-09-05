import {
  pgTable,
  text,
  timestamp,
  real,
  integer,
  boolean,
  uuid,
  jsonb,
} from "drizzle-orm/pg-core";

// ----- Products -----
export const products = pgTable("products", {
  id: uuid("id").primaryKey().defaultRandom(),
  company: text("company").notNull(),
  product: text("product").notNull(),
  status: text("status").notNull().default("pending"), // pending | analyzing | ready | error
  createdAt: timestamp("created_at", { mode: "string" }).notNull().defaultNow(),
  updatedAt: timestamp("updated_at", { mode: "string" }).notNull().defaultNow(),
});

// ----- Supply Trees -----
export const supplyTrees = pgTable("supply_trees", {
  id: uuid("id").primaryKey().defaultRandom(),
  productId: uuid("product_id")
    .notNull()
    .references(() => products.id, { onDelete: "cascade" }),
  version: integer("version").notNull().default(1),
  createdAt: timestamp("created_at", { mode: "string" }).notNull().defaultNow(),
});

// ----- Supply Nodes -----
export const supplyNodes = pgTable("supply_nodes", {
  id: uuid("id").primaryKey().defaultRandom(),
  treeId: uuid("tree_id")
    .notNull()
    .references(() => supplyTrees.id, { onDelete: "cascade" }),
  label: text("label").notNull(),
  category: text("category").notNull().default("component"), // component | sub-component | raw-material | intermediary
  level: integer("level").notNull(),
  confidence: real("confidence").notNull().default(1),
  importance: text("importance").notNull().default("medium"), // low | medium | high | critical
  costPercent: real("cost_percent"),
  riskScore: real("risk_score"),
  reasoning: text("reasoning").notNull().default(""),
  expanded: boolean("expanded").notNull().default(false),
  createdAt: timestamp("created_at", { mode: "string" }).notNull().defaultNow(),
});

// ----- Supply Node Edges (DAG) -----
export const supplyNodeEdges = pgTable("supply_node_edges", {
  id: uuid("id").primaryKey().defaultRandom(),
  treeId: uuid("tree_id")
    .notNull()
    .references(() => supplyTrees.id, { onDelete: "cascade" }),
  sourceId: uuid("source_id")
    .notNull()
    .references(() => supplyNodes.id, { onDelete: "cascade" }),
  targetId: uuid("target_id")
    .notNull()
    .references(() => supplyNodes.id, { onDelete: "cascade" }),
});

// ----- Node Companies -----
export const nodeCompanies = pgTable("node_companies", {
  id: uuid("id").primaryKey().defaultRandom(),
  nodeId: uuid("node_id")
    .notNull()
    .references(() => supplyNodes.id, { onDelete: "cascade" }),
  name: text("name").notNull(),
  country: text("country"),
  city: text("city"),
  lat: real("lat"),
  lon: real("lon"),
  status: text("status").notNull().default("known_producer"), // confirmed_supplier | known_producer | crowdsourced
  source: text("source"), // data source that found this company
  createdAt: timestamp("created_at", { mode: "string" }).notNull().defaultNow(),
});

// ----- Disruption Events -----
export const disruptionEvents = pgTable("disruption_events", {
  id: uuid("id").primaryKey().defaultRandom(),
  nodeId: uuid("node_id")
    .notNull()
    .references(() => supplyNodes.id, { onDelete: "cascade" }),
  name: text("name").notNull(),
  description: text("description").notNull().default(""),
  year: integer("year").notNull(),
  severity: text("severity").notNull().default("medium"), // low | medium | high | critical
});

// ----- User Contributions -----
export const userContributions = pgTable("user_contributions", {
  id: uuid("id").primaryKey().defaultRandom(),
  userId: text("user_id").notNull(),
  nodeId: uuid("node_id"),
  treeId: uuid("tree_id")
    .notNull()
    .references(() => supplyTrees.id, { onDelete: "cascade" }),
  type: text("type").notNull(), // add_node | correct_node | add_company | report_issue
  data: jsonb("data"),
  status: text("status").notNull().default("pending"), // pending | approved | rejected
  createdAt: timestamp("created_at", { mode: "string" }).notNull().defaultNow(),
});

// ----- NextAuth Tables -----
export const users = pgTable("users", {
  id: uuid("id").primaryKey().defaultRandom(),
  name: text("name"),
  email: text("email").unique(),
  emailVerified: timestamp("email_verified", { mode: "string" }),
  image: text("image"),
});

export const accounts = pgTable("accounts", {
  id: uuid("id").primaryKey().defaultRandom(),
  userId: uuid("user_id")
    .notNull()
    .references(() => users.id, { onDelete: "cascade" }),
  type: text("type").notNull(),
  provider: text("provider").notNull(),
  providerAccountId: text("provider_account_id").notNull(),
  refreshToken: text("refresh_token"),
  accessToken: text("access_token"),
  expiresAt: integer("expires_at"),
  tokenType: text("token_type"),
  scope: text("scope"),
  idToken: text("id_token"),
  sessionState: text("session_state"),
});

export const sessions = pgTable("sessions", {
  id: uuid("id").primaryKey().defaultRandom(),
  sessionToken: text("session_token").unique().notNull(),
  userId: uuid("user_id")
    .notNull()
    .references(() => users.id, { onDelete: "cascade" }),
  expires: timestamp("expires", { mode: "string" }).notNull(),
});
