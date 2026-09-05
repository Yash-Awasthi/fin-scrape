import { neon, type NeonQueryFunction } from "@neondatabase/serverless";
import { drizzle, type NeonHttpDatabase } from "drizzle-orm/neon-http";
import * as schema from "./schema";

let dbInstance: NeonHttpDatabase<typeof schema> | null = null;
let sqlInstance: NeonQueryFunction<false, false> | null = null;

function getSql() {
  if (!sqlInstance) {
    const dbUrl = process.env.DATABASE_URL;
    if (!dbUrl) {
      throw new Error("DATABASE_URL environment variable is not set");
    }
    sqlInstance = neon(dbUrl);
  }
  return sqlInstance;
}

export function getDb(): NeonHttpDatabase<typeof schema> {
  if (!dbInstance) {
    dbInstance = drizzle(getSql(), { schema });
  }
  return dbInstance;
}

// Lazy proxy for backward compatibility
export const db: NeonHttpDatabase<typeof schema> = new Proxy(
  {} as NeonHttpDatabase<typeof schema>,
  {
    get(_target, prop) {
      const database = getDb();
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      return (database as any)[prop];
    },
  }
);

export { schema };

export function isDbConfigured(): boolean {
  return !!process.env.DATABASE_URL;
}
