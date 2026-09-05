# CANAIRY — UX / UI Audit & Polish Plan

**Transforming a monitoring tool into a consumer-grade preparedness dashboard**

| | |
|---|---|
| **Prepared for** | Manav Thaker |
| **Date** | February 26, 2026 |
| **Version** | 1.0 |

---

## Executive Summary

Canairy is an ambitious household resilience monitoring system that tracks 34+ societal risk indicators across 9 domains and translates them into actionable preparedness phases. The React/TypeScript frontend is architecturally sound, with good component decomposition, a Zustand state store, lazy-loaded routes, and a polished dark theme.

However, from a consumer UX perspective, the dashboard suffers from three systemic problems that undermine its core mission of making complex risk data feel actionable and approachable for a tech-forward family:

1. **Information overload without hierarchy.** The main dashboard stacks 8+ heavyweight panels vertically with no clear visual priority. A parent checking Canairy at 7am cannot answer the question "Am I okay?" without scrolling through 2,000+ pixels of content.

2. **Mobile experience is broken.** The SituationalStatusBar packs 12+ data points into a single horizontal flex row with no responsive breakpoints. On any screen under 1280px, critical information is clipped or invisible. Multiple pages lack the sidebar navigation entirely.

3. **Incomplete pages erode trust.** Three sidebar-linked pages (Alerts, Reports, Family Checklist) show "coming soon" placeholders. For a system meant to convey preparedness and reliability, broken navigation signals the opposite.

This audit identifies 28 specific findings across 7 categories, prioritized into a 3-phase implementation plan. The goal: make Canairy feel like a consumer product you trust with your family's safety, not a developer dashboard you tolerate.

---

## Current State Scorecard

| Dimension | Score | Target | Key Gap |
|---|:---:|:---:|---|
| Information Architecture | **5**/10 | 9/10 | No glanceable summary; 8 equal-weight panels compete |
| Mobile Responsiveness | **3**/10 | 9/10 | Status bar unusable <1280px; pages lack sidebar |
| Visual Hierarchy | **6**/10 | 9/10 | Good color system but no clear reading flow |
| Actionability | **7**/10 | 9/10 | Actions exist but buried below 3 scrolls of context |
| Trust & Polish | **4**/10 | 9/10 | 3 placeholder pages; random HOPI trend; no onboarding |
| Accessibility | **6**/10 | 8/10 | Skip-link exists; missing ARIA labels on key widgets |
| Performance | **7**/10 | 9/10 | Good code splitting; excessive re-renders in status bar |

---

## 1. Information Architecture & Content Hierarchy

*The dashboard must answer "Am I okay?" in under 3 seconds*

### Finding 1.1: Dashboard Cognitive Overload

The main `Dashboard.tsx` renders 8 distinct panels in a single vertical scroll: NewsTicker, TightenUpBanner, EnhancedExecutiveSummary, DomainBreakdown, PhaseDetailPanel, CriticalIndicators, RiskNarrativePanel, and ActionablePriorityActions. Each panel is visually equal-weight with similar card styling, making it impossible to establish a reading hierarchy.

- **Impact:** Users scroll past critical action items because they blend with informational panels.
- **Recommendation:** Restructure into a 3-tier layout: (1) A hero "Status Card" with HOPI score, phase, and top action — always visible above the fold. (2) A collapsible "Situation Room" with DomainBreakdown + CriticalIndicators side-by-side. (3) "Action Center" at the bottom with Priority Actions and Phase checklist. Remove RiskNarrativePanel — its content should be integrated into the Executive Summary as the subMessage field already does.

### Finding 1.2: Redundant Status Communication

The same risk status is communicated in 5 different places: SituationalStatusBar (threat level badge), EnhancedExecutiveSummary (mainMessage), TightenUpBanner (protocol active), CriticalIndicators, and sidebar system status. This isn't reinforcement — it's noise.

- **Recommendation:** Consolidate into 2 touchpoints: (1) The sticky header shows current threat level + phase as a single compact badge. (2) The hero Status Card provides the narrative explanation. Remove the separate SituationalStatusBar component and fold its essential data (indicator counts, data freshness) into the header and Status Card.

### Finding 1.3: News Ticker Competing with Alerts

NewsTicker renders above TightenUpBanner, meaning news headlines appear before a critical safety protocol. The ticker also uses animated transitions that draw the eye away from actionable content.

- **Recommendation:** Move news to a dedicated sidebar or bottom section. When TightenUpBanner is active, it should be the first thing visible after the header — no other content above it.

---

## 2. Mobile & Responsive Experience

*60%+ of household check-ins happen on phones*

### Finding 2.1: SituationalStatusBar is Desktop-Only

`SituationalStatusBar.tsx` renders a single horizontal flex row containing: threat level badge, phase status, HOPI score, time-to-act, indicator counts (3 colored badges), data freshness, and live data indicator. That's 12+ data points in one row with zero responsive breakpoints. On mobile, everything past the threat badge is clipped.

- **Recommendation:** Replace with a mobile-first compact status bar: threat level + phase on one line, with a tap-to-expand drawer showing details. Use the existing SituationalStatusBar only on `lg+` breakpoints. On mobile, show just a color-coded pill: "NORMAL" / "ELEVATED" / "CRITICAL" with tap-for-details.

### Finding 2.2: Pages Without Sidebar Navigation

Settings, ResiliencePlaybook, Alerts, and Reports render as standalone full-page layouts without the sidebar navigation from `Dashboard.tsx`. Users visiting `/settings` have no way to navigate back except the browser back button or the breadcrumb link.

- **Recommendation:** Extract the sidebar into a shared `Layout` component used by all routes. Use React Router's nested routes with an `Outlet` pattern. **This is the single highest-impact structural change.**

### Finding 2.3: Touch Targets Too Small

Checklist toggle buttons in TightenUpBanner and PhaseDetailPanel are 20×20px (`w-5 h-5`). The WCAG minimum for touch targets is 44×44px. The news ticker pagination dots are 8×4px — nearly impossible to tap.

- **Recommendation:** Increase all interactive elements to 44px minimum touch targets. For checklist items, make the entire row clickable (already done, but increase padding). Replace ticker dots with swipe gestures on mobile.

---

## 3. Visual Design & Polish

*Trust is built in the details*

### Finding 3.1: Dark Theme Lacks Depth

The current palette uses 3 near-identical dark values: `#0A0A0A` (bg), `#111111` (cards), `#1A1A1A` (borders/surfaces). The 11% luminance difference between layers is too subtle — cards don't visually "lift" from the background, making the hierarchy feel flat.

- **Recommendation:** Introduce a 5-tier elevation system: Level 0 (`#09090B`), Level 1 (`#0F0F12`), Level 2 (`#18181B`), Level 3 (`#27272A`), Level 4 (`#3F3F46`). Add subtle box-shadows to elevated cards (`0 1px 3px rgba(0,0,0,0.5)`). Use the glass effect class more strategically for overlays.

### Finding 3.2: Inconsistent Component Styling

The codebase has two parallel design systems: the dark "bmb" theme (Dashboard, Indicators) and the light "canairy" theme (CanairyDashboard, FamilyChecklist). The CanairyDashboard at `/family` uses completely different colors, layout patterns, and component styles. Users switching between routes experience jarring visual discontinuity.

- **Recommendation:** Pick one design language and commit to it. The dark theme is more mature — deprecate the light "canairy" theme or make it a user-togglable preference in Settings. If keeping both, unify the component API so NestEggCard and EnhancedIndicatorCard share the same data contract.

### 🚨 Finding 3.3: Random Data in Production Components

`SituationalStatusBar.tsx` line 118 uses `Math.random()` to determine the HOPI trend direction. `EnhancedIndicatorCard.tsx` line 266 generates a random percentage for trend display. This means **every render shows different data** — a critical trust violation for a safety-oriented tool.

- **Recommendation:** Remove all `Math.random()` from production components **immediately**. Compute trend from actual historical data (compare current HOPI to previous snapshot). If data isn't available, show "N/A" rather than fabricating numbers. **This is a P0 bug.**

### Finding 3.4: HOPI Gauge Rendering Bug

`HOPIGauge.tsx` applies `className="transform -rotate-90"` to the SVG, then adds `className="mt-6 transform rotate-90"` to the text container to counter-rotate it. This causes text to render at odd angles on certain viewport sizes and creates layout instability.

- **Recommendation:** Rewrite the gauge using a proper semicircular arc that doesn't require rotation hacks. Use a 180-degree arc (bottom-up) with the score displayed centered below. Reference the design of Nest thermostat or Apple Health gauges for proven patterns.

---

## 4. Actionability & User Flows

*Every screen should end with a clear next step*

### Finding 4.1: Actions Are Buried Below the Fold

ActionablePriorityActions renders as the 7th panel in the dashboard scroll order. A user in a genuine crisis must scroll past the executive summary, domain breakdown, phase details, critical indicators, and risk narrative before reaching the actual "here's what to do" section.

- **Recommendation:** Promote the #1 priority action into the hero Status Card. Show a single, large "TOP ACTION" button with the urgency badge. Full action list moves to the second scroll section. During TIGHTEN-UP, the checklist becomes the primary content.

### Finding 4.2: Checklist State Not Persisted

Both TightenUpBanner and PhaseDetailPanel use `useState` for completed actions. Refreshing the page resets all progress. For a 48-hour emergency checklist, this is a serious usability failure.

- **Recommendation:** Persist checklist state in localStorage (at minimum) or backend. Add timestamps to completions so the 48-hour deadline shows accurate progress. Consider adding family member assignment ("Dad: fill gas, Mom: check meds").

### Finding 4.3: No Guided Onboarding

A new user landing on the dashboard sees 34 indicators, 9 domains, 10 phases, and no explanation of what any of it means. The system assumes familiarity with terms like HOPI, trip-wires, and TIGHTEN-UP protocol.

- **Recommendation:** Add a first-run setup wizard: (1) "What phase are you starting from?" (2) "Which domains matter most to your family?" (3) "How do you want to be notified?" Follow with tooltips on key components during the first session. The CanairyMascot "thinking" state is perfect for this — use it as the onboarding guide.

---

## 5. Trust & Completeness

*Incomplete features destroy credibility in a safety tool*

### Finding 5.1: Three Placeholder Pages

`Alerts.tsx`, `Reports.tsx`, and `FamilyChecklist.tsx` all render "coming soon" placeholders. These are all linked from the primary sidebar navigation. A user encountering a "coming soon" page on a safety tool will immediately question whether the rest of the system is equally incomplete.

- **Recommendation:** Either (a) build minimal functional versions of these pages, or (b) remove them from the sidebar until ready. Option (a) is preferred: Alerts can show a simple chronological feed of status changes. Reports can offer a one-click "export current status as PDF." FamilyChecklist should mirror the TightenUpBanner checklist with persisted state.

### Finding 5.2: Mock Data Isn't Transparent

The API service silently falls back to mock data when the backend is unavailable. The Settings page shows Live vs Mock counts, but the main dashboard gives no indication that data may be fabricated. A user could make safety decisions based on mock data.

- **Recommendation:** Add a persistent banner when running on mock data: "Demo Mode — showing sample data. Connect backend for live monitoring." Mark individual indicators with a visual badge when their data source is MOCK vs LIVE.

### Finding 5.3: No Data Provenance on Indicators

Indicator cards show a small "dataSource" text but don't link to the actual source. Users cannot verify claims like "Treasury tail at 8.5 bps" without doing their own research.

- **Recommendation:** Add a "Source" link on each indicator card that opens the actual data source (Treasury API page, Reuters article, etc.). Include the last-fetched timestamp. This builds trust through transparency.

---

## 6. Accessibility & Performance

### Finding 6.1: Status Conveyed Only by Color

Green/amber/red status is communicated exclusively through color in DomainBreakdown progress bars, indicator cards, and status dots. Approximately 8% of men have some form of color vision deficiency.

- **Recommendation:** Add shape or text redundancy: use circle/triangle/diamond icons alongside colors. Add text labels ("OK", "WATCH", "ACT") to status badges. The StatusBadge component partially does this — ensure it's used everywhere, not just on indicator cards.

### Finding 6.2: Animations Without Reduced-Motion Respect

While `globals.css` includes a `prefers-reduced-motion` media query, framer-motion animations throughout the codebase don't check this preference. The pulsing AlertCircle in TightenUpBanner and the scale animation on threat badges will still play for users who've requested reduced motion.

- **Recommendation:** Create a `useReducedMotion()` hook that checks the media query. Wrap all framer-motion animations with conditional props. For critical alerts, use a static visual treatment (bold border + icon) rather than animation.

### Finding 6.3: Status Bar Re-renders Every Minute

`SituationalStatusBar.tsx` creates a timer that updates state every 60 seconds, but the displayed time comes from data freshness, not the clock. The `setCurrentTime` state setter causes a full re-render of the status bar and all child components every minute for no visual change.

- **Recommendation:** Remove the unnecessary timer. Compute data freshness from the store's last update timestamp reactively. This eliminates ~1,440 unnecessary re-renders per day.

---

## 7. Implementation Roadmap

*3 phases, prioritized by impact-to-effort ratio*

### Phase 1: Foundation Fixes (1–2 weeks)

High-impact changes that require minimal architectural rework. Ship these before anything else.

| Change | Impact | Details | Priority |
|---|---|---|:---:|
| Remove `Math.random()` | Trust: eliminates fake data | Delete random trend/percentage in StatusBar + IndicatorCard. Show "N/A" or compute from history. | **P0** |
| Extract shared Layout | Nav: consistent sidebar | Create `Layout.tsx` with sidebar + Outlet. Wrap all routes. Fix mobile nav. | **P0** |
| Fix StatusBar responsive | Mobile: usable on phones | Compact pill on mobile, full bar on desktop. Tap-to-expand drawer. | **P0** |
| Persist checklist state | Safety: progress survives refresh | localStorage for completed items with timestamps. 48hr countdown. | **P0** |
| Kill placeholder pages | Trust: no dead ends | Hide from nav or build minimal: Alerts=feed, Reports=export, Checklist=shared. | **P1** |
| Add mock data banner | Trust: transparent data source | Persistent banner when API unreachable. Per-indicator MOCK badge. | **P1** |

### Phase 2: Experience Polish (2–3 weeks)

Restructure the dashboard information architecture and upgrade visual design.

| Change | Impact | Details | Priority |
|---|---|---|:---:|
| Hero Status Card | IA: answer "Am I ok?" instantly | Combine HOPI + phase + top action into one above-fold card. 3-second answer. | **P0** |
| Reorder dashboard panels | IA: action before information | Status Card → Actions → Domains → Details. News to sidebar/bottom. | **P1** |
| Elevation system | Visual: depth and hierarchy | 5-tier surface system with subtle shadows. Cards lift from background. | **P1** |
| Rewrite HOPI Gauge | Visual: clean, trustworthy | Semicircular arc without rotation hacks. Nest-thermostat inspired. | **P1** |
| Color-blind accessibility | A11y: shape + text + color | Icons for status levels. Text labels on all badges. High-contrast mode. | **P1** |
| Source links on indicators | Trust: verifiable data | Each card links to raw data source. Shows fetch timestamp. | **P2** |

### Phase 3: Delight & Differentiation (3–4 weeks)

Features that transform Canairy from a monitoring tool into a household safety companion.

| Change | Impact | Details | Priority |
|---|---|---|:---:|
| Onboarding wizard | Adoption: guided first run | 3-step setup: phase, domains, notifications. Mascot-guided tooltips. | **P1** |
| Family member profiles | Actionability: assigned tasks | Each member gets assigned checklist items. "Dad: gas. Mom: meds." | **P1** |
| Unified theme system | Visual: one design language | Dark/light toggle in settings. Remove parallel canairy CSS. Shared components. | **P2** |
| Reduced-motion support | A11y: respect user prefs | `useReducedMotion()` hook. Static fallbacks for all animations. | **P2** |
| Performance: kill timer | Perf: eliminate wasted renders | Remove `setInterval` in StatusBar. Reactive freshness from store. | **P2** |
| Weekly digest email | Engagement: passive monitoring | Automated summary: "This week: 2 indicators changed. Phase stable." | **P2** |

---

## 8. Design Principles for Canairy

*Guardrails for every future design decision*

1. **3-Second Rule.** Every page must answer its primary question in under 3 seconds. Dashboard: "Am I okay?" Indicators: "What's red?" Playbook: "What do I do next?"

2. **Action Over Information.** If showing data, always pair it with what to do about it. A red indicator without a recommended action is just anxiety.

3. **Calm by Default, Loud When It Matters.** Green state should feel serene and minimal. Red state should feel urgent but not panicked. The transition between them should be unmistakable.

4. **Mobile First, Desktop Enhanced.** Design for the phone check at 7am. Desktop is for deep dives. Never show desktop-only content.

5. **Trust Through Transparency.** Show your sources. Show when data is stale. Show when you're using mock data. Never fabricate numbers.

6. **Family, Not Just User.** This tool serves households. Design for shared understanding: a teenager and a grandparent should both be able to read the Status Card.

---

## Next Steps

This audit is the diagnosis. The prescription is to start with Phase 1, which delivers the highest trust and usability impact with the least architectural disruption. I recommend tackling the 6 Phase 1 items as a focused sprint, then reviewing the dashboard with fresh eyes before proceeding to Phase 2.

The bones of Canairy are excellent — the component architecture, state management, type system, and data model are all well-structured. The polish plan above is about elevating the presentation layer to match the quality of the underlying system.
