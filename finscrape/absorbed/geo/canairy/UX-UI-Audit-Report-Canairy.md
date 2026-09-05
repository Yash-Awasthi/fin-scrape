# UX/UI Audit Report: Canairy

**URL:** https://canairy.news
**Date:** March 10, 2026
**Pages audited:** Landing page, Dashboard, Indicators, Action Plan, Alerts
**Viewport tested:** Desktop (1440x900). Mobile (390x844) — limited by browser minimum window constraints; mobile nav elements were verified via accessibility tree.

---

## Executive Summary

Canairy is a thoughtfully designed household resilience monitoring dashboard with strong information architecture, excellent color contrast, and a clear value proposition. The visual design is polished with a cohesive dark theme and well-organized content hierarchy. However, the site has **critical accessibility gaps** — zero focus indicators across all 64 interactive elements, duplicate navigation links in the accessibility tree, and no ARIA attributes — and a **major reliability problem** where the Indicators page returns empty due to API failures while the dashboard silently falls back to mock data. These issues need immediate attention.

**What's working well:** Semantic HTML structure (proper heading hierarchy, landmarks, skip link), outstanding text contrast ratios (14.88:1+), clear and actionable content writing, good empty states, and transparent source attribution on news items.

---

## Critical Issues

### 1. Zero Focus Indicators on All Interactive Elements
- **Heuristic/Category:** Accessibility (WCAG 2.1 AA — 2.4.7 Focus Visible)
- **Severity:** Critical
- **Evidence:** Programmatic check confirms all 41 links and all 23 buttons have `outline: none` or `0px`. After pressing Tab 5 times on the dashboard, no visual focus ring is visible on any element. Keyboard-only users cannot tell which element is currently focused.
- **Impact:** Keyboard-only users and many assistive technology users cannot navigate the site. This is a WCAG AA failure and a potential legal liability.
- **Claude Code prompt:**
  ```
  Add visible focus indicators to all interactive elements across the Canairy app. The site uses a dark theme (body bg: rgb(17, 20, 18)) with gold accent (rgb(251, 191, 36)). Add a global CSS rule:

  *:focus-visible {
    outline: 2px solid rgb(251, 191, 36);
    outline-offset: 2px;
  }

  Also remove any existing `outline: none` declarations on links, buttons, and interactive elements. The focus ring should use the gold accent color to match the existing design language. Test by tabbing through the sidebar nav, dashboard cards, news links, and domain status buttons.
  ```

### 2. API Failures — Indicators Page Completely Empty
- **Heuristic/Category:** Visibility of System Status (H1), Error Recovery (H9)
- **Severity:** Critical
- **Evidence:** Browser console shows repeated `WebSocket error: Event` warnings (4 occurrences), followed by `API Error: x` (2 occurrences), then `Using mock indicators due to API error` and `Using mock system status due to API error`. The Dashboard displays mock data without informing the user. The Indicators page (/indicators) shows "No indicators found — Try adjusting your filters" with "All 0, Red 0, Amber 0, Green 0" — a completely empty state that appears broken.
- **Impact:** Users on the Indicators page see zero data with no explanation. Users on the Dashboard see data that appears live but is actually mocked. For a resilience monitoring tool, silent data failures are especially dangerous — users may make decisions based on stale or fake data.
- **Claude Code prompt:**
  ```
  Fix the Indicators page to display mock/fallback data when the API fails, matching how the Dashboard already handles this. Currently the Dashboard catches API errors and shows mock data, but the Indicators page shows an empty state instead.

  1. In the indicators data fetching logic, implement the same mock data fallback pattern used by the dashboard
  2. Add a visible banner/toast when data is from mock/fallback sources, e.g.: "⚠ Live data unavailable — showing last known values. Retrying..."
  3. Add this same banner to the Dashboard when it falls back to mock data
  4. Include a manual "Retry" button in the banner
  5. Make the WebSocket reconnection logic more robust with exponential backoff

  The user should NEVER see real-looking data without knowing it might be stale.
  ```

### 3. Duplicate Navigation Links in Accessibility Tree
- **Heuristic/Category:** Accessibility, Consistency & Standards (H4)
- **Severity:** Major
- **Evidence:** The accessibility tree shows every sidebar navigation item rendered twice — "Home" appears as two separate links, "Indicators" as two separate links, etc. (refs 31-50 in the accessibility tree). This likely results from rendering both an icon-only and a text version of each link as separate `<a>` elements.
- **Impact:** Screen reader users hear every nav item announced twice, making navigation confusing and slow. The tab order is also doubled, requiring keyboard users to press Tab twice per nav item.
- **Claude Code prompt:**
  ```
  The sidebar navigation renders each nav item as two separate <a> links — one for the icon and one for the text label. This causes screen readers to announce each item twice and doubles the Tab key stops.

  Fix by combining each pair into a single <a> element that contains both the icon and the text label. For example, instead of:
    <a href="/dashboard"><Icon /></a>
    <a href="/dashboard"><span>Home</span></a>

  Use:
    <a href="/dashboard"><Icon aria-hidden="true" /><span>Home</span></a>

  Apply this pattern to all 5 nav items: Home, Indicators, Action Plan, Alerts, Settings. Also check the mobile bottom navigation (which has Home, Actions, Monitor, Alerts, More) for the same issue.
  ```

### 4. Inactive Nav Link Contrast Fails WCAG AA
- **Heuristic/Category:** Accessibility (WCAG 1.4.3 Contrast Minimum)
- **Severity:** Major
- **Evidence:** Inactive sidebar navigation links use `color: rgb(122, 120, 112)` on the dark sidebar background (~rgb(17, 20, 18)). This yields a contrast ratio of approximately 3.2:1, which fails the WCAG AA minimum of 4.5:1 for normal-sized text (16px).
- **Impact:** Users with low vision may struggle to read inactive nav labels, particularly "Indicators", "Action Plan", "Alerts", and "Settings".
- **Claude Code prompt:**
  ```
  The inactive sidebar navigation links use color rgb(122, 120, 112) which only has ~3.2:1 contrast against the dark background. WCAG AA requires 4.5:1 for 16px text.

  Change the inactive nav link color to at least rgb(163, 161, 154) (approximately 5.0:1 contrast against rgb(17, 20, 18)). Keep the active state as-is (gold: rgb(251, 191, 36), which passes at 8.5:1). This affects the sidebar nav links for: Indicators, Action Plan, Alerts, Settings when they are not the current page.
  ```

### 5. Landing Page Animation Blocks Content
- **Heuristic/Category:** Aesthetic & Minimalist Design (H8), Accessibility (WCAG 2.3.3 Animation from Interactions)
- **Severity:** Major
- **Evidence:** The landing page initially renders as a nearly black screen with a faint green glow animation for approximately 3-5 seconds before content appears. During the first screenshot capture, only the dark animation was visible with no text or interactive elements.
- **Impact:** Users on slow connections or devices may think the page is broken. Users with vestibular disorders may be affected by the animation. There is no way to skip or dismiss the animation.
- **Claude Code prompt:**
  ```
  The landing page has an intro animation that shows a dark screen with a green glow for 3-5 seconds before revealing content. This blocks access to content and may trigger vestibular issues.

  1. Respect `prefers-reduced-motion: reduce` by skipping the animation entirely and showing content immediately
  2. Reduce the animation duration to 1 second maximum for users who don't have reduced motion enabled
  3. Ensure text content is present in the DOM and readable even while the animation plays (use the animation as a background layer, not a blocking overlay)
  4. Consider removing the animation entirely — the landing page content is compelling enough on its own
  ```

---

## Full Findings

### Usability (Nielsen's Heuristics)

#### H1: Visibility of System Status
**Score: 2/5**

- **(Critical) Silent mock data fallback.** The dashboard shows data that looks live but is mocked due to API errors, with no user-facing indication. The console reveals `Using mock indicators due to API error` but users see no banner, toast, or warning.
- **(Major) No loading indicators on page transitions.** Navigating between Dashboard, Indicators, Action Plan, and Alerts shows no loading spinner or skeleton screen during data fetching.
- **(Good) Active nav state.** The sidebar correctly highlights the current page in gold (rgb(251, 191, 36)) with a left border indicator.
- **(Good) Alert badge.** The "Stay Alert" banner on the dashboard clearly shows "14 conditions worth watching" with an expandable "5 actions" count.

#### H2: Match Between System and the Real World
**Score: 5/5**

- **(Excellent) Plain-language writing.** Action items like "Build your cash cushion this week" and "Stock up on essentials" use everyday language, not financial jargon.
- **(Excellent) Traffic-light metaphor.** Green/Amber/Red status levels are universally understood.
- **(Excellent) Time framing.** Actions are tagged with urgency levels like "Do this today" and "This week" — tangible and actionable.
- **(Good) Tagline.** "Like a canary in a coal mine — for the modern world" immediately communicates the product's purpose.

#### H3: User Control and Freedom
**Score: 3/5**

- **(Good) Breadcrumbs.** The Action Plan page shows "Dashboard > Action Plan" breadcrumb navigation.
- **(Good) Dismissable welcome.** The welcome modal has a clear "Got it" button.
- **(Minor) No back/undo on action items.** If a user checks off an action plan item, there's no visible undo mechanism.
- **(Minor) No way to dismiss the "Stay Alert" banner** after acknowledging it.

#### H4: Consistency and Standards
**Score: 3/5**

- **(Major) Duplicate nav links.** As detailed above, each sidebar nav item renders as two separate links.
- **(Minor) Banner text inconsistency.** The desktop header banner contains the text "Canry" (ref_55 in accessibility tree) while the visible header shows "Canairy" correctly — likely an icon-only link with truncated alt text.
- **(Good) Consistent card design.** Dashboard action cards follow a uniform pattern: urgency tag, heading, description, expandable chevron.
- **(Good) Consistent color coding.** Gold/amber for warnings, green for normal status, red for critical — used consistently across all pages.

#### H5: Error Prevention
**Score: 3/5**

- **(Good) No destructive actions exposed.** The dashboard is read-heavy with no risky actions that could cause data loss.
- **(Minor) Indicators filter shows "All 0" rather than indicating the data source is unavailable.** Users may think they need to change filters when the real problem is an API failure.

#### H6: Recognition Rather Than Recall
**Score: 4/5**

- **(Good) Icon + label nav.** Sidebar navigation uses both icons and text labels.
- **(Good) Domain chips.** The "Also Monitoring" section uses labeled, color-coded chips (Economy, Global Conflict, etc.) with count badges.
- **(Good) News attribution.** Each news item shows the source (BLS, NYSE, BEA, EFF, Bloomberg) and timestamp.

#### H7: Flexibility and Efficiency of Use
**Score: 3/5**

- **(Good) Search on Indicators page.** A search field is available for filtering indicators.
- **(Good) Domain filter dropdown.** Users can filter indicators by domain category.
- **(Minor) No keyboard shortcuts** for power users to navigate between sections.
- **(Minor) No way to customize which domains appear in "Also Monitoring."**

#### H8: Aesthetic and Minimalist Design
**Score: 4/5**

- **(Excellent) Clean dark theme.** The dark background (rgb(17, 20, 18)) with gold accents creates a distinctive, professional look appropriate for a monitoring dashboard.
- **(Good) Information density.** The dashboard balances showing enough signals to be useful without overwhelming the user.
- **(Major) Landing page animation** adds 3-5 seconds of dark screen before content, which is unnecessary visual weight.
- **(Minor) The news sidebar shows "2h ago" for almost all items** — if timestamps are identical, they add visual noise without value.

#### H9: Help Users Recognize, Diagnose, and Recover from Errors
**Score: 2/5**

- **(Critical) Indicators empty state is misleading.** "No indicators found — Try adjusting your filters" suggests a user error when the real problem is an API failure.
- **(Good) Alerts empty state.** "Everything looks good — Nothing needs your attention right now" is a clear, friendly message.

#### H10: Help and Documentation
**Score: 3/5**

- **(Good) Welcome modal.** First-time users see a helpful onboarding message explaining what the dashboard does and where to start.
- **(Good) Contextual descriptions.** Each action card includes a brief explanation of why the action matters.
- **(Minor) No FAQ, help section, or methodology documentation** explaining how indicators are scored or what thresholds trigger each alert level.
- **(Minor) No tooltip or help icons** on domain status chips explaining what each domain covers.

---

### Visual Design
**Score: 4/5**

- **Typography:** Strong dual-font system — Space Grotesk (headings, 48px/700) and DM Sans (body, 16px/400). Heading hierarchy is clear and consistent. Line height of 24px for body text is appropriate.
- **Color:** Cohesive palette anchored by dark bg (rgb(17, 20, 18)), white text (rgb(255, 255, 255)), and gold accent (rgb(251, 191, 36)). Amber/red/green color coding for alert levels is intuitive.
- **Contrast:** Excellent — body text at 14.88:1, headings at 18.54:1, button text at 19.90:1. All far exceed WCAG AA requirements. Exception: inactive nav links at ~3.2:1 fail.
- **Spacing & Layout:** Clean three-column layout on dashboard (sidebar + main + news). Cards use consistent padding and rounded corners. Good use of whitespace between sections.
- **Visual Hierarchy:** Clear at a glance — the "Stay Alert" banner with its amber border is the obvious primary element. "Do this today" tags in red draw the eye to urgent items. Section headers ("WHAT'S HAPPENING", "ALSO WORTH NOTING", "ALSO MONITORING") create clear content groups.

---

### Accessibility
**Score: 2/5**

- **(Critical) No focus indicators.** Zero of 64 interactive elements show a visible focus ring. Keyboard navigation is essentially unusable.
- **(Major) Duplicate links.** Screen reader users hear every nav item twice.
- **(Major) Inactive nav contrast fails** (~3.2:1 vs 4.5:1 required).
- **(Major) No ARIA attributes.** Zero `role` attributes found on the page aside from one native `alert` element. Interactive cards, expandable sections, and domain status buttons lack `aria-expanded`, `aria-label`, and similar attributes.
- **(Good) Skip to main content link** is present.
- **(Good) Semantic HTML.** Proper use of `<main>`, `<nav>`, `<banner>`, heading levels (H1 → H2), and native `<button>` elements.
- **(Good) Language attribute.** `<html lang="en">` is set correctly.
- **(Good) Viewport meta tag** is present and correctly configured.

---

### Responsive Design
**Score: 3/5**

- **(Good) Mobile navigation exists.** The accessibility tree reveals a dedicated mobile bottom navigation with simplified labels: Home, Actions, Monitor, Alerts, More.
- **(Good) Sidebar collapses.** The desktop sidebar with icons + labels presumably collapses to icons-only or a hamburger menu on smaller screens (mobile nav presence confirms this).
- **(Minor) Landing page "What This Dashboard Tracks" section** renders three items side-by-side — at narrow widths these may crowd or overlap. The section doesn't appear to stack vertically.
- **(Note)** True mobile testing was limited by browser minimum window constraints. The site should be tested on actual mobile devices.

---

### Interactions
**Score: 3/5**

- **(Good) Expandable action cards.** Dashboard cards have chevron buttons for expanding/collapsing detail.
- **(Good) Clickable domain chips.** "Also Monitoring" chips link to filtered indicator views.
- **(Good) News links open external sources** with proper attribution.
- **(Minor) No visible hover states observed** on sidebar nav items or cards during testing — hover feedback may be subtle or missing.
- **(Minor) The CTA button "Enter the Dashboard"** has generous sizing (271x60px, 18px font) and good padding (16px 32px) — works well.
- **(Major) No loading state or skeleton screens** during page transitions or data fetching.

---

## Summary Scorecard

| Dimension | Score (1-5) | Key Issue |
|-----------|-------------|-----------|
| Visibility of System Status | 2 | Silent mock data fallback, no loading indicators |
| Match with Real World | 5 | Excellent plain-language writing throughout |
| User Control & Freedom | 3 | Good breadcrumbs, but no undo on actions |
| Consistency & Standards | 3 | Duplicate nav links, minor text inconsistency |
| Error Prevention | 3 | Misleading filter message on empty Indicators |
| Recognition over Recall | 4 | Good labeling, icons, and attribution |
| Flexibility & Efficiency | 3 | Search exists, but no keyboard shortcuts |
| Aesthetic & Minimalist | 4 | Beautiful dark theme, unnecessary landing animation |
| Error Recovery | 2 | Indicators empty state hides real error |
| Help & Documentation | 3 | Welcome modal good, no FAQ or methodology docs |
| Visual Design | 4 | Strong typography and color, inactive nav contrast fails |
| Accessibility | 2 | No focus indicators, duplicate links, no ARIA |
| Responsive Design | 3 | Mobile nav exists, needs real-device testing |
| Interactions | 3 | Expandable cards good, no loading states |

**Overall Score: 3.1 / 5** — Functional with notable gaps in accessibility and error handling.

---

## Prioritized Action Items

1. **(Critical)** Add visible focus indicators to all 64 interactive elements — blocks keyboard users entirely
2. **(Critical)** Fix Indicators page to show fallback data when API fails instead of misleading empty state
3. **(Critical)** Add user-facing banner when dashboard is showing mock/fallback data instead of live data
4. **(Major)** Merge duplicate sidebar navigation links into single elements (icon + text in one `<a>`)
5. **(Major)** Fix inactive nav link contrast from ~3.2:1 to ≥4.5:1
6. **(Major)** Add `prefers-reduced-motion` support and shorten/remove landing page animation
7. **(Major)** Add ARIA attributes to expandable cards (`aria-expanded`), domain buttons (`aria-label`), and alert banner
8. **(Major)** Add loading states/skeleton screens during page transitions and data fetching
9. **(Minor)** Fix "Canry" text in banner link to read "Canairy"
10. **(Minor)** Add undo mechanism for action plan checkboxes
11. **(Minor)** Add tooltips or help icons on domain status chips
12. **(Minor)** Add FAQ or methodology page explaining indicator scoring
13. **(Enhancement)** Add keyboard shortcuts for navigation between main sections
14. **(Enhancement)** Add ability to customize which domains show in "Also Monitoring"
15. **(Enhancement)** Add explicit timestamps or "last updated" indicator showing when data was last fetched successfully
