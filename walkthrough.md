# Council Backend Walkthrough

We have successfully completed multiple major feature sets for the Council backend!

## 1. Multi-turn Conversations
- **Threaded Conversations**: Chats are grouped into `Conversation` sessions to mimic LLM behavior.
- **Context memory**: The last 20 messages of a conversation are automatically injected.
- **Session Guards**: We explicitly enforce a **20-question limit** per conversation.

## 2. Streaming Resilience
- Added an SSE heartbeat interval emitting `:\n\n` strictly every 15 seconds to prevent proxies or firewalls from dropping the connection during slow AI inference.

## 3. JWT Revocation & Logout
- **Blocklist System**: Introduced a `RevokedToken` PostgreSQL table.
- **Logout Endpoint**: Added `POST /auth/logout` to strictly blacklist the active JWT.

## 4. Usage, Cost & Abuse Prevention
- **Usage Tracking**: Added global response time (`durationMs`) and precise per-model metrics tracking into `opinions`.
- **Daily Token Quotas**: Created a formal `DailyUsage` module. It enforces a strict limit (default: 100 queries/day) using UPSERT logic so malicious actors cannot bankrupt your AI providers.
- **Strict Payload Guards**: Added absolute upper limits (`2000`) for `maxTokens` globally across `askSchema` preventing clients from circumventing local limits.

## 5. Automated Database Maintenance (The Sweeper)
- **Background Sweeper**: Built a durable Node.js `setInterval` daemon ([src/lib/sweeper.ts](file:///home/yash/council-project/src/lib/sweeper.ts)) that initializes heavily isolated database cleanup loops when the express server starts.
- **Task 1**: Deletes expired sessions from `RevokedTokens` every 6 hours so the blocklist stays perfectly pruned.
- **Task 2**: Sweeps the schema for "Orphaned Conversations" (blank states older than 24h doing absolutely nothing but costing indexing power) and permanently drops them.

## 6. Provider Health Checks
- **Health Verification API**: Exported `POST /providers/test` utilizing a strict `maxTokens=10` limit to precisely validate API keys instantly without heavy cost structures.

---

> [!TIP]
> Architecture is extremely solid. The API is globally secured via limits, resilient behind proxies, cleanly monitored for cost/time metrics, and structurally sound for years of logging records via indices mapping. Next up, frontend integration!
