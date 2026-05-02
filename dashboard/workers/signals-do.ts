import { DurableObject } from "cloudflare:workers";

export interface SignalEvent {
  id?: number;
  subject: string;
  event_type: string;
  tickers: string[];
  impact_direction: string;
  signal_score: number;
  confidence: number;
  verdict: string;
  heuristic_impact: number;
  divergence_flag: boolean;
  sources: string[];
  articles: string[];
  timestamp: string;
  created_at?: string;
  // Enriched fields
  reasoning?: string;
  magnitude?: string;
  novelty?: string;
  actionability?: string;
  sector_impact?: string;
}

export interface PortfolioPosition {
  ticker: string;
  shares: number;
  avg_cost: number;
  current_price: number;
  tags: string[];
}

export interface DashboardStats {
  total_events: number;
  invest_count: number;
  observe_count: number;
  cautious_count: number;
  pull_out_count: number;
  unique_tickers: number;
  sources_active: number;
  last_update: string | null;
}

export interface AIAnalysis {
  summary: string;
  ticker_impacts: Array<{ ticker: string; direction: string; estimated_pct: string; reason: string }>;
  verdict_reason: string;
}

export class SignalsDO extends DurableObject<Env> {
  private wsClients: Set<WebSocket> = new Set();

  constructor(ctx: DurableObjectState, env: Env) {
    super(ctx, env);
  }

  async ingestEvents(events: SignalEvent[]): Promise<{ inserted: number; duplicates: number; insertedIds: number[] }> {
    let inserted = 0;
    let duplicates = 0;
    const insertedEvents: SignalEvent[] = [];
    const insertedIds: number[] = [];

    for (const ev of events) {
      // Deduplicate by first article URL
      const articles = ev.articles || [];
      if (articles.length > 0) {
        const firstUrl = articles[0];
        const existing = await this.env.DB.prepare(
          "SELECT COUNT(*) as c FROM events WHERE instr(articles, ?) > 0"
        ).bind(firstUrl).first<{ c: number }>();
        
        if (existing && existing.c > 0) {
          duplicates++;
          continue;
        }
      }

      // Deduplicate by exact subject match on same day
      if (ev.subject) {
        const ts = ev.timestamp || new Date().toISOString();
        const day = ts.split("T")[0];
        const dayStart = day + "T00:00:00Z";
        const dayEnd = day + "T23:59:59Z";
        const subjectDup = await this.env.DB.prepare(
          "SELECT COUNT(*) as c FROM events WHERE subject = ? AND timestamp >= ? AND timestamp <= ?"
        ).bind(ev.subject, dayStart, dayEnd).first<{ c: number }>();
        
        if (subjectDup && subjectDup.c > 0) {
          duplicates++;
          continue;
        }
      }

      const result = await this.env.DB.prepare(
        `INSERT INTO events
         (subject, event_type, tickers, impact_direction, signal_score,
          confidence, verdict, heuristic_impact, divergence_flag,
          sources, articles, timestamp, reasoning, magnitude, novelty, actionability, sector_impact)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
      ).bind(
        ev.subject,
        ev.event_type || "other",
        JSON.stringify(ev.tickers || []),
        ev.impact_direction || "neutral",
        ev.signal_score || 0,
        ev.confidence || 0.5,
        ev.verdict || "OBSERVE",
        ev.heuristic_impact || 0.0,
        ev.divergence_flag ? 1 : 0,
        JSON.stringify(ev.sources || []),
        JSON.stringify(ev.articles || []),
        ev.timestamp || new Date().toISOString(),
        ev.reasoning || "",
        ev.magnitude || "",
        ev.novelty || "",
        ev.actionability || "",
        ev.sector_impact || ""
      ).run();

      if (result.success && result.meta.last_row_id) {
        const lastId = result.meta.last_row_id;
        insertedIds.push(lastId);
        insertedEvents.push({ ...ev, id: lastId });
        inserted++;
      }
    }

    // Broadcast new events to all connected WebSocket clients
    if (insertedEvents.length > 0) {
      this.broadcast({
        type: "new_events",
        events: insertedEvents,
        stats: await this.getStats(),
      });
    }

    return { inserted, duplicates, insertedIds };
  }

  async getEvents(opts: {
    limit?: number;
    verdict?: string;
    ticker?: string;
    source?: string;
    event_type?: string;
    offset?: number;
    date?: string; 
    sort_by?: string; 
    sort_dir?: string; 
  } = {}): Promise<SignalEvent[]> {
    const limit = opts.limit || 100;
    const offset = opts.offset || 0;
    const conditions: string[] = [];
    const params: unknown[] = [];

    if (opts.date) {
      const dayStart = opts.date + "T00:00:00Z";
      const d = new Date(dayStart);
      d.setUTCDate(d.getUTCDate() + 1);
      const dayEnd = d.toISOString().split("T")[0] + "T00:00:00Z";
      conditions.push("timestamp >= ? AND timestamp < ?");
      params.push(dayStart, dayEnd);
    }

    if (opts.verdict) {
      conditions.push("verdict = ?");
      params.push(opts.verdict);
    }
    if (opts.ticker) {
      conditions.push("tickers LIKE ?");
      params.push(`%"${opts.ticker}"%`);
    }
    if (opts.source) {
      conditions.push("sources LIKE ?");
      params.push(`%"${opts.source}"%`);
    }
    if (opts.event_type) {
      conditions.push("event_type = ?");
      params.push(opts.event_type);
    }

    const where = conditions.length > 0 ? `WHERE ${conditions.join(" AND ")}` : "";

    const allowedSorts: Record<string, string> = {
      timestamp: "timestamp",
      signal_score: "signal_score",
      confidence: "confidence",
      id: "id",
    };
    const sortCol = allowedSorts[opts.sort_by || ""] || "id";
    const sortDir = opts.sort_dir === "asc" ? "ASC" : "DESC";

    const { results } = await this.env.DB.prepare(
      `SELECT * FROM events ${where} ORDER BY ${sortCol} ${sortDir} LIMIT ? OFFSET ?`
    ).bind(...params, limit, offset).all<Record<string, unknown>>();

    return results.map(this.rowToEvent);
  }

  async getAvailableDates(): Promise<Array<{ day: string; count: number }>> {
    const { results } = await this.env.DB.prepare(
      `SELECT DATE(timestamp) as day, COUNT(*) as c FROM events GROUP BY day ORDER BY day DESC LIMIT 90`
    ).all<{ day: string; c: number }>();
    return results.map(r => ({ day: r.day, count: r.c as number }));
  }

  async getStats(): Promise<DashboardStats> {
    const total = await this.env.DB.prepare("SELECT COUNT(*) as c FROM events").first<{ c: number }>();
    const invest = await this.env.DB.prepare("SELECT COUNT(*) as c FROM events WHERE verdict = 'INVEST'").first<{ c: number }>();
    const observe = await this.env.DB.prepare("SELECT COUNT(*) as c FROM events WHERE verdict = 'OBSERVE'").first<{ c: number }>();
    const cautious = await this.env.DB.prepare("SELECT COUNT(*) as c FROM events WHERE verdict = 'CAUTIOUS'").first<{ c: number }>();
    const pullOut = await this.env.DB.prepare("SELECT COUNT(*) as c FROM events WHERE verdict = 'PULL_OUT'").first<{ c: number }>();
    const lastRow = await this.env.DB.prepare("SELECT timestamp FROM events ORDER BY id DESC LIMIT 1").first<{ timestamp: string }>();

    // Count unique tickers
    const { results: allTickers } = await this.env.DB.prepare("SELECT DISTINCT tickers FROM events").all<{ tickers: string }>();
    const tickerSet = new Set<string>();
    for (const row of allTickers) {
      try {
        const arr = JSON.parse(row.tickers);
        if (Array.isArray(arr)) arr.forEach((t: string) => tickerSet.add(t));
      } catch {}
    }

    const { results: allSources } = await this.env.DB.prepare("SELECT DISTINCT sources FROM events").all<{ sources: string }>();
    const sourceSet = new Set<string>();
    for (const row of allSources) {
      try {
        const arr = JSON.parse(row.sources);
        if (Array.isArray(arr)) arr.forEach((s: string) => sourceSet.add(s));
      } catch {}
    }

    return {
      total_events: total?.c || 0,
      invest_count: invest?.c || 0,
      observe_count: observe?.c || 0,
      cautious_count: cautious?.c || 0,
      pull_out_count: pullOut?.c || 0,
      unique_tickers: tickerSet.size,
      sources_active: sourceSet.size,
      last_update: lastRow?.timestamp || null,
    };
  }

  async registerTelegramChat(chatId: string, filters: Record<string, string> = {}): Promise<void> {
    await this.env.DB.prepare(
      `INSERT OR REPLACE INTO telegram_chats (chat_id, filters) VALUES (?, ?)`
    ).bind(chatId, JSON.stringify(filters)).run();
  }

  async getTelegramChats(): Promise<Array<{ chat_id: string; filters: Record<string, string> }>> {
    const { results } = await this.env.DB.prepare(
      "SELECT chat_id, filters FROM telegram_chats"
    ).all<{ chat_id: string; filters: string }>();
    return results.map(r => ({
      chat_id: r.chat_id,
      filters: JSON.parse(r.filters),
    }));
  }

  async removeTelegramChat(chatId: string): Promise<void> {
    await this.env.DB.prepare("DELETE FROM telegram_chats WHERE chat_id = ?").bind(chatId).run();
  }

  // --- Portfolio ---

  async setPosition(pos: PortfolioPosition): Promise<void> {
    await this.env.DB.prepare(
      `INSERT INTO portfolio_positions (ticker, shares, avg_cost, current_price, tags, updated_at)
       VALUES (?, ?, ?, ?, ?, datetime('now'))
       ON CONFLICT(ticker) DO UPDATE SET
         shares = excluded.shares,
         avg_cost = excluded.avg_cost,
         current_price = excluded.current_price,
         tags = excluded.tags,
         updated_at = datetime('now')`
    ).bind(pos.ticker.toUpperCase(), pos.shares, pos.avg_cost, pos.current_price, JSON.stringify(pos.tags || [])).run();
  }

  async removePosition(ticker: string): Promise<void> {
    await this.env.DB.prepare("DELETE FROM portfolio_positions WHERE ticker = ?").bind(ticker.toUpperCase()).run();
  }

  async getPositions(): Promise<PortfolioPosition[]> {
    const { results } = await this.env.DB.prepare(
      "SELECT ticker, shares, avg_cost, current_price, tags FROM portfolio_positions ORDER BY ticker"
    ).all<Record<string, unknown>>();
    return results.map(r => ({
      ticker: r.ticker as string,
      shares: r.shares as number,
      avg_cost: r.avg_cost as number,
      current_price: r.current_price as number,
      tags: JSON.parse(r.tags as string),
    }));
  }

  async setWatchlist(name: string, tickers: string[], description: string = ""): Promise<void> {
    await this.env.DB.prepare(
      `INSERT INTO portfolio_watchlists (name, tickers, description)
       VALUES (?, ?, ?)
       ON CONFLICT(name) DO UPDATE SET tickers = excluded.tickers, description = excluded.description`
    ).bind(name, JSON.stringify(tickers.map(t => t.toUpperCase())), description).run();
  }

  async getWatchlists(): Promise<Array<{ name: string; tickers: string[]; description: string }>> {
    const { results } = await this.env.DB.prepare(
      "SELECT name, tickers, description FROM portfolio_watchlists ORDER BY name"
    ).all<Record<string, unknown>>();
    return results.map(r => ({
      name: r.name as string,
      tickers: JSON.parse(r.tickers as string),
      description: r.description as string,
    }));
  }

  async deleteWatchlist(name: string): Promise<void> {
    await this.env.DB.prepare("DELETE FROM portfolio_watchlists WHERE name = ?").bind(name).run();
  }

  async getPortfolioSummary(): Promise<{
    positions: PortfolioPosition[];
    watchlists: Array<{ name: string; tickers: string[] }>;
    total_value: number;
    total_pnl: number;
  }> {
    const positions = await this.getPositions();
    const watchlists = await this.getWatchlists();
    const totalValue = positions.reduce((s, p) => s + p.shares * p.current_price, 0);
    const totalCost = positions.reduce((s, p) => s + p.shares * p.avg_cost, 0);
    return {
      positions,
      watchlists,
      total_value: Math.round(totalValue * 100) / 100,
      total_pnl: Math.round((totalValue - totalCost) * 100) / 100,
    };
  }

  // --- AI Analysis Cache ---

  async getEventById(eventId: number): Promise<SignalEvent | null> {
    const row = await this.env.DB.prepare(
      "SELECT * FROM events WHERE id = ? LIMIT 1"
    ).bind(eventId).first<Record<string, unknown>>();
    if (!row) return null;
    return this.rowToEvent(row);
  }

  async getAIAnalysis(eventId: number): Promise<AIAnalysis | null> {
    const row = await this.env.DB.prepare(
      "SELECT summary, ticker_impacts, verdict_reason FROM ai_analysis_cache WHERE event_id = ?"
    ).bind(eventId).first<Record<string, unknown>>();
    if (!row) return null;
    return {
      summary: row.summary as string,
      ticker_impacts: JSON.parse(row.ticker_impacts as string),
      verdict_reason: row.verdict_reason as string,
    };
  }

  async saveAIAnalysis(eventId: number, analysis: AIAnalysis): Promise<void> {
    await this.env.DB.prepare(
      `INSERT OR REPLACE INTO ai_analysis_cache (event_id, summary, ticker_impacts, verdict_reason)
       VALUES (?, ?, ?, ?)`
    ).bind(eventId, analysis.summary, JSON.stringify(analysis.ticker_impacts), analysis.verdict_reason).run();

    // Update event tickers from AI-detected ticker_impacts
    if (analysis.ticker_impacts && analysis.ticker_impacts.length > 0) {
      const existingRow = await this.env.DB.prepare(
        "SELECT tickers FROM events WHERE id = ?"
      ).bind(eventId).first<{ tickers: string }>();
      
      if (existingRow) {
        const existingTickers: string[] = JSON.parse(existingRow.tickers);
        const aiTickers = analysis.ticker_impacts.map(t => t.ticker).filter(t => t && t.length <= 6);
        const merged = [...new Set([...existingTickers, ...aiTickers])];
        if (merged.length > existingTickers.length) {
          await this.env.DB.prepare(
            "UPDATE events SET tickers = ? WHERE id = ?"
          ).bind(JSON.stringify(merged), eventId).run();
        }
      }
    }
  }

  // Notify clients that AI analysis has updated events
  async broadcastAIUpdate(): Promise<void> {
    this.broadcast({
      type: "ai_updated",
      stats: await this.getStats(),
    });
  }

  // --- WebSocket real-time stream ---

  async handleWebSocket(request: Request): Promise<Response> {
    const pair = new WebSocketPair();
    const [client, server] = Object.values(pair);

    this.ctx.acceptWebSocket(server);
    this.wsClients.add(server);

    // Send initial snapshot
    const stats = await this.getStats();
    const recentEvents = await this.getEvents({ limit: 20 });
    server.send(JSON.stringify({
      type: "init",
      stats,
      events: recentEvents,
    }));

    return new Response(null, { status: 101, webSocket: client });
  }

  webSocketClose(ws: WebSocket) {
    this.wsClients.delete(ws);
  }

  webSocketError(ws: WebSocket) {
    this.wsClients.delete(ws);
  }

  webSocketMessage(ws: WebSocket, message: string | ArrayBuffer) {
    try {
      const data = JSON.parse(typeof message === "string" ? message : new TextDecoder().decode(message));
      if (data.type === "ping") {
        ws.send(JSON.stringify({ type: "pong" }));
      }
    } catch {}
  }

  private broadcast(data: unknown): void {
    const msg = JSON.stringify(data);
    for (const ws of this.wsClients) {
      try {
        ws.send(msg);
      } catch {
        this.wsClients.delete(ws);
      }
    }
  }

  private rowToEvent(row: Record<string, unknown>): SignalEvent {
    return {
      id: row.id as number,
      subject: row.subject as string,
      event_type: row.event_type as string,
      tickers: JSON.parse(row.tickers as string),
      impact_direction: row.impact_direction as string,
      signal_score: row.signal_score as number,
      confidence: row.confidence as number,
      verdict: row.verdict as string,
      heuristic_impact: row.heuristic_impact as number,
      divergence_flag: !!(row.divergence_flag as number),
      sources: JSON.parse(row.sources as string),
      articles: JSON.parse(row.articles as string),
      timestamp: row.timestamp as string,
      created_at: row.created_at as string,
      reasoning: (row.reasoning as string) || undefined,
      magnitude: (row.magnitude as string) || undefined,
      novelty: (row.novelty as string) || undefined,
      actionability: (row.actionability as string) || undefined,
      sector_impact: (row.sector_impact as string) || undefined,
    };
  }
}
