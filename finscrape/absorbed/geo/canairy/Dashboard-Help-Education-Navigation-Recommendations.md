# Help Text, Education & Navigation Recommendations for the Canairy Dashboard

**Date:** March 10, 2026
**Scope:** Dashboard, Indicators, Action Plan, Alerts, Settings pages
**Goal:** Make the dashboard more self-explanatory, educational, and navigable — especially for first-time users who arrive curious but unfamiliar with resilience monitoring.

---

## Current State: What's Already Working

Before diving into gaps, it's worth noting that Canairy already has some solid educational foundations in place.

The **Action Plan page** is the strongest example. It has a clear intro paragraph explaining how the page works, "Why this matters" expandable sections on each action item, time and cost estimates on every task in "The Basics," and a rich "How this works" section at the bottom that explains the monitoring methodology, the phase system, and how phases change. This is excellent work — the recommendations below are about bringing this same level of care to the rest of the dashboard.

The **dashboard cards** also do a good job of explaining *why* in their expanded state — the cash buffer card explains that ATMs fail first, the investment card contextualizes daily swings at 2-3%. This voice is a major asset.

The **Alerts page** has a clean three-tier summary (Need action / Worth knowing / Watching) and filter tabs (All / Critical / Warning / Info).

---

## The Gaps: Where Users Get Lost

### 1. Broken Internal Links — /playbook and /checklist Return 404s

**The problem:** The "Also worth noting" section on the dashboard links to items that appear to navigate to `/playbook` and `/checklist` routes. Both return an empty dashboard — no error message, no 404 page, no explanation. Users click, see nothing useful, and lose trust.

**Recommendation:** Either build out these routes or remove the links. If the content isn't ready yet, show a "Coming soon" placeholder with a brief description of what will live there. Never let a user click something and land on what looks like a broken page.

**Priority:** Critical — broken links on the primary page undermine confidence in a tool whose entire value proposition is reliability.

---

### 2. No Onboarding Flow Beyond the Welcome Modal

**The problem:** First-time visitors see a dismissable welcome modal with a "Got it" button. Once dismissed, there's no way to re-access it, no guided tour, and no progressive introduction to the five main sections (Dashboard, Indicators, Action Plan, Alerts, Settings). A new user is dropped into the dashboard and left to figure out what everything means.

**Recommendation — Lightweight Onboarding Tour:**

Add an optional 4-5 step guided walkthrough that highlights key areas on first visit:

- **Step 1:** "This is your alert status" → points to the Stay Alert banner. Explains green/amber/red.
- **Step 2:** "These are your action items" → points to the card grid. "Expand any card for details and context."
- **Step 3:** "Here's the bigger picture" → points to "Also Monitoring" domain chips. "Each domain tracks multiple signals. Click to explore."
- **Step 4:** "Your action plan" → points to the nav. "This is your personal checklist — organized by what matters most right now."
- **Step 5:** "Check in weekly" → "Most families check Canairy once a week. You'll get alerts if anything needs attention sooner."

Include a "Skip tour" option and make it re-accessible from Settings or a "?" help icon in the header.

**Priority:** High — this is the single biggest educational improvement you can make with modest development effort.

---

### 3. No Explanation of Alert Levels on the Alerts Page

**The problem:** The Alerts page shows three count boxes — "Need action" (red), "Worth knowing" (amber), "Watching" (blue/green) — and four filter tabs (All, Critical, Warning, Info). But there's no explanation of what these levels mean or how they differ. A new user looking at "14 Watching" alerts doesn't know whether that's normal or alarming.

**Recommendation:** Add a small help section or tooltip cluster at the top of the Alerts page:

> **How alert levels work:**
> - **Need action** — Something has crossed a critical threshold. Review the recommended actions now.
> - **Worth knowing** — A signal has changed enough to be noteworthy, but no immediate action needed.
> - **Watching** — Elevated but stable. We're keeping an eye on it so you don't have to.

Also add a one-line contextual note: "14 signals at 'Watching' level is typical during moderate uncertainty. You'll see this number drop as conditions normalize."

**Priority:** High — the Alerts page is where anxious users land. Context reduces anxiety.

---

### 4. No Tooltips on Domain Chips

**The problem:** The "Also Monitoring" section on the dashboard shows domain chips — Economy (3), Global Conflict (3), Security & Infra (2), etc. — but there's no explanation of what each domain covers. The chip names are clear enough for repeat users but opaque for newcomers. What signals does "Oil Axis" track? What falls under "Domestic Control"?

**Recommendation:** Add hover tooltips (desktop) or tap-to-reveal (mobile) on each domain chip:

- **Economy** → "Inflation, market volatility, GDP, employment trends"
- **Global Conflict** → "Active conflicts, military activity, defense spending"
- **Security & Infra** → "Cyber threats, drug shortages, power grid status"
- **Domestic Control** → "Civil liberties cases, travel advisories, surveillance"
- **Jobs & Labor** → "Employment data, pharmacy/drug supply, labor market"
- **Rights & Gov** → "Legislation tracking, surveillance bills, judicial activity"
- **Oil Axis** → "Strategic petroleum reserves, energy geopolitics"
- **Supply Chain** → "Semiconductor lead times, shipping, manufacturing"
- **AI Window** → "AI-related policy, development milestones, risk signals"

**Priority:** Medium — improves comprehension without blocking functionality.

---

### 5. No Methodology or FAQ Page

**The problem:** There's no standalone page explaining how Canairy works — how indicators are scored, what data sources are used, how thresholds are set, or how recommendations are generated. The "How this works" section at the bottom of the Action Plan page is good but hidden (collapsed by default, at the very bottom of a long page). A tech-savvy user who wants to understand and trust the system has nowhere to go.

**Recommendation — Create a /methodology or /how-it-works page:**

Structure it in three sections:

**Section 1: "How we monitor"**
- We track 50+ real-world indicators across economy, supply chains, energy, security, and more
- Each indicator has thresholds based on historical data
- When an indicator crosses from "normal" to "elevated" or "alert," it shows up in your recommendations
- All data sources are public and linked

**Section 2: "How we score"**
- Green = within normal historical range
- Amber = elevated beyond typical variance — worth watching
- Red = significantly elevated — action recommended
- Show an example indicator card with annotations explaining each element

**Section 3: "How actions are recommended"**
- Explain the phase system (The Basics → Financial + Connected → Storage & Shelter → etc.)
- Explain how phases change based on indicator status
- Reference the existing "How this works" content from the Action Plan page (or share it)

Link to this page from the Settings page, the footer, and the Indicators page header.

**Priority:** Medium-high — builds trust with the tech-savvy parent persona who will want to verify the methodology before recommending it to friends.

---

### 6. No Help or "?" Icon in the Header

**The problem:** There's no persistent help entry point anywhere in the dashboard chrome. The header shows "Canairy" (left) and "Household Resilience Monitor" (right), and the sidebar has 5 nav items (Home, Indicators, Action Plan, Alerts, Settings). But there's no "?" icon, no "Help" link, no way to get assistance at any point.

**Recommendation:** Add a small "?" icon to the header bar (or bottom of the sidebar). Clicking it should open a slide-out panel or modal with:

- **"New here?"** → Link to the onboarding tour
- **"How Canairy works"** → Link to methodology page
- **"What do the colors mean?"** → Quick reference for green/amber/red
- **"How often should I check?"** → "Most families check weekly. We'll alert you if something needs attention sooner."
- **"Is my data private?"** → "We don't collect any personal data. No account needed. No tracking."
- **"Who built this?"** → Brief founder note (builds trust)

This should be lightweight — a quick-reference panel, not a full help center.

**Priority:** High — provides a safety net for confused users without cluttering the main interface.

---

### 7. Indicator Cards Lack Educational Depth

**The problem:** The Indicators page shows cards with a title, domain/source, value, trend line, one-sentence description, and timestamp. This is functional for monitoring, but there's no way to learn *more* about any specific indicator. What's a normal value for "Market Volatility: 24.3 bp"? What does the trend line represent — last week, last month, last year? Is 28 aircraft/day in the Taiwan Strait high or low historically?

**Recommendation — Add an expandable detail panel to each indicator card:**

When a user clicks an indicator card (or clicks a "Learn more" link), show:

- **Historical context:** "Normal range: 5-15 bp. Current: 24.3 bp." Or a simple sparkline with a shaded "normal" band.
- **What this means for your family:** One sentence (already partially there in the description, but could be richer).
- **Data source:** Already present as text (e.g., "Bloomberg"), but make it a clickable link to the actual source.
- **Last 30 days trend:** A small chart showing recent trajectory.
- **Related actions:** "Because this indicator is elevated, we recommend: [link to relevant action plan item]"

This connects the monitoring layer (Indicators) to the action layer (Action Plan) — right now these feel like separate products.

**Priority:** Medium — enriches the experience for engaged users without changing the default view.

---

### 8. No Cross-Navigation Between Related Content

**The problem:** The dashboard, indicators, action plan, and alerts are four parallel pages with no cross-linking between related content. If I'm looking at the "Grocery CPI" alert on the Alerts page, there's no link to the corresponding indicator card, and no link to the relevant action item ("Stock up on essentials"). Similarly, the dashboard card "Stock 2 weeks of shelf-stable essentials" doesn't link to the Grocery CPI indicator or the Action Plan.

**Recommendation — Add contextual cross-links:**

- **Dashboard cards → Indicators:** "This recommendation is based on: Grocery CPI (Amber) [→ View indicator]"
- **Dashboard cards → Action Plan:** "Part of: The Basics [→ See full plan]"
- **Alert items → Indicators:** Each alert should link to its indicator card for full context
- **Alert items → Actions:** Each alert should suggest relevant actions: "What to do about this → [link]"
- **Indicator cards → Actions:** "Recommended action: Stock 2 weeks of shelf-stable essentials [→ View in Action Plan]"
- **Action Plan items → Indicators:** The "Why this matters" sections should reference the specific indicators driving each recommendation

This creates a *web* of understanding rather than siloed pages. A user can start anywhere and follow their curiosity to deeper context.

**Priority:** High — this is probably the highest-impact navigation improvement. It turns five separate pages into one cohesive experience.

---

### 9. The "Also Worth Noting" Section Needs Context

**The problem:** The dashboard's "Also worth noting" section lists 6 numbered items with a category label (Global Conflict, Economy, Security Infrastructure). But there's no explanation of what this section is. Is it secondary to the main cards? Is it less urgent? Is it a different type of recommendation?

**Recommendation:** Add a brief section header explanation:

> **Also worth noting** — These are additional recommendations based on current conditions. They're important but not as time-sensitive as the actions above.

Or differentiate it more clearly from the main action cards — perhaps visually de-emphasize it, or add a "Lower priority" label. The numbered list format already helps, but a single line of context would clarify the hierarchy.

**Priority:** Low-medium — nice clarity improvement.

---

### 10. The "Deeper Analysis" Section is a Black Box

**The problem:** At the bottom of the dashboard, there's a "DEEPER ANALYSIS" section with a collapse/expand chevron and the text "Intelligence briefing powered by Canairy." It's not clear what this is, whether it's a premium feature, or what the user will get if they expand it.

**Recommendation:** Add a one-line description before/after the heading:

> **Deeper Analysis** — A weekly AI-generated briefing connecting the dots between current indicators. Plain language, no jargon.

If this is a feature-in-progress, say so: "Coming soon: weekly intelligence briefing connecting the signals."

**Priority:** Low — but easy to add.

---

### 11. Settings Page Has No Educational Content

**The problem:** The Settings page has notification controls, data source information, system status, and privacy info, but nothing that helps users understand the product better. It's purely functional.

**Recommendation:** Add two sections to Settings:

**"About Canairy"** — A brief section with:
- Version/last update date
- Link to methodology page
- Link to the "How this works" section (or embed it)
- "Built by [founder name]" — humanizes the product

**"Help & Learning"** — Links to:
- Re-launch the onboarding tour
- FAQ / methodology page
- "What do the colors mean?" quick reference
- A "Give feedback" mechanism (email link, form, or GitHub issues link)

**Priority:** Medium — Settings is where power users go to understand a product.

---

### 12. No "Last Updated" or Data Freshness Indicator on the Dashboard

**The problem:** The Indicators page shows "Last refresh: Just now" and individual cards show "Updated Just now." But the main dashboard — the page most users see — has no visible timestamp. Users can't tell if they're looking at fresh data or something cached from last Tuesday. This is especially problematic given the known API reliability issues where the dashboard silently falls back to mock data.

**Recommendation:** Add a subtle "Last updated: [timestamp]" indicator in the dashboard header, near "Household Resilience Monitor." During API fallback, change this to "Last updated: [timestamp] · Using cached data" with a distinct visual treatment (amber text or a small warning icon).

**Priority:** High — for a monitoring tool, data freshness is a core trust signal.

---

## Summary: Implementation Roadmap

### Sprint 1 (This Week) — Fix What's Broken

1. Fix or remove /playbook and /checklist broken links
2. Add a data freshness timestamp to the dashboard header
3. Add a banner when displaying mock/fallback data (from previous UX audit)

### Sprint 2 (Next Week) — Add Contextual Help

4. Add alert level explanations to the Alerts page header
5. Add tooltips to domain chips on the dashboard
6. Add a "?" help icon to the header with quick-reference panel
7. Add a one-line description to the "Also worth noting" and "Deeper Analysis" sections

### Sprint 3 — Build the Onboarding Tour

8. Build a 4-5 step guided walkthrough for first-time visitors
9. Make the welcome modal re-accessible from Settings and the "?" menu
10. Add "About Canairy" and "Help & Learning" sections to Settings

### Sprint 4 — Cross-Navigation & Education

11. Add cross-links between dashboard cards ↔ indicators ↔ action plan ↔ alerts
12. Add expandable detail panels to indicator cards (historical context, related actions)
13. Create a /methodology or /how-it-works page

### Sprint 5 — Polish

14. Promote the "How this works" content from the Action Plan page bottom to somewhere more discoverable
15. Add a "Who built this?" section (humanizes the product, builds trust)
16. Add a feedback mechanism

---

## The Core Principle

The dashboard's *content* is already excellent — the writing is clear, specific, and family-oriented. The gap isn't in what Canairy says, it's in how well it *teaches users to use it.* Every improvement above follows one idea: meet users where they are, not where you hope they'll be. A first-time visitor should be able to understand the dashboard's value, navigate between related information, and trust the data — all within their first two-minute session.

The Action Plan's "How this works" section proves the team can write great educational content. The task now is to distribute that quality across the entire experience.
