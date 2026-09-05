# User Guide

## Getting Started

### First Launch

1. Start the platform (see [Quick Start](../README.md#-quick-start))
2. Open your browser to `http://localhost:5173`
3. Register a new account on the login page
4. Set your Anthropic API key in `.env` (required for AI features)

### Navigation

The sidebar provides access to all platform features:

| Page | Purpose |
|------|---------|
| 🌐 **Globe View** | 3D visualization of geopolitical events |
| 📡 **Pipeline** | Run the end-to-end analysis pipeline |
| 📰 **Clusters** | Browse news clusters |
| ⚡ **Events** | Browse abstract IR events |
| 🧠 **Theories** | Multi-theory analysis per event |
| 🌿 **Scenarios** | Scenario scripts & probability forecasts |
| 🔀 **Branches** | Counterfactual simulation branches |
| 📜 **Analogies** | Historical case matching |
| 📝 **History** | Prediction run records & evaluations |
| 📈 **Calibration** | Prediction accuracy dashboard |
| 📄 **Reports** | PDF report generation |

## Core Workflow

### Step 1: Run the Pipeline

The pipeline is the engine of the platform. It transforms raw news into structured intelligence.

1. Go to **Pipeline** page
2. Select news sources (RSS feeds)
3. Click "Run Pipeline"
4. Watch the progress as the system:
   - Ingests and normalizes news articles
   - Clusters related stories
   - Abstracts structured events
   - Applies IR theories
   - Generates scenario scripts

> **Note:** Pipeline runs consume Claude API credits. Each run processes all unprocessed news.

### Step 2: Explore Events

After pipeline completion, visit the **Events** page to see all abstracted IR events.

- Each event card shows: title, event type, crisis stage, key actors, and summary
- Click to expand for full detail including theoretical analyses and scenario scripts
- Events are linked to their original news clusters

### Step 3: Analyze Scenarios

The **Scenarios** page shows the most valuable output: probability-weighted future scenarios.

1. Select an event from the dropdown
2. Optionally filter by a specific prediction run
3. View scripts organized in three columns:
   - 🔴 **Escalation** — scenarios where conflict intensifies
   - 🟡 **Stalemate** — scenarios where status quo persists
   - 🟢 **De-escalation** — scenarios where tensions resolve
4. Click a script to see step-by-step details:
   - Which actor acts first
   - Why each step happens
   - How other actors react
   - Supporting and counter evidence
   - Uncertainty and impact assessments

### Step 4: Create Branches (Optional)

Want to explore "what if" alternatives? Use the **Branch** engine.

1. Select a base prediction run
2. Choose a hypothesis type (counterfactual actor, changed constraint, external shock)
3. Describe your hypothetical change
4. The system generates new scenario scripts diverging from the base run
5. Compare branches in the mind map visualization

### Step 5: Record Actual Outcomes

This is the **most important step** for the platform to improve.

1. Go to **History** page
2. Find a completed prediction run
3. Click expand (▼) and then "+ Record Actual Outcome"
4. Fill in:
   - **Actual summary** — what really happened
   - **Actual event type** — the real outcome
   - **Matched script** (optional) — which predicted script was closest
5. Submit

### Step 6: Generate Evaluations

After recording outcomes, generate automated evaluations:

1. On the **History** page, expanded run view
2. Click "Auto-Evaluate"
3. The system analyzes prediction vs. reality and computes:
   - Accuracy rate
   - Error types
   - Improvement notes

### Step 7: Monitor Calibration

The **Calibration** page provides a comprehensive dashboard:

- **Calibration Grade** (A-F) — overall prediction quality
- **Hit Rate** — percentage of correct scenario predictions
- **Brier Score** — probabilistic accuracy (0 = perfect, 0.25 = random)
- **By Direction** — how well you predict escalation vs. de-escalation
- **By Theory** — which theoretical lenses are most accurate
- **By Crisis Stage** — prediction accuracy at different conflict phases
- **Trend Chart** — hit rate over time
- **Error Distribution** — what types of errors are most common
- **Improvement Suggestions** — AI-generated recommendations

## Historical Analogy Engine

The **Analogies** page helps ground current analysis in historical precedent:

1. **Left panel:** Select a current event and generate/regenerate analogies
   - View matched historical cases ranked by similarity
   - See historical base rates and structured comparisons
2. **Right panel:** Browse and manage the historical case library
   - Search, filter by type and region
   - Add new cases, edit existing ones, or delete outdated ones
3. Click any case to see full detail including triggers, escalation paths, resolutions, and lessons

## Report Generation

Generate professional PDF reports from the **Reports** page:

1. Select a report type:
   - **Event Brief** — single event summary with scenario previews
   - **Scenario Report** — full scenario details for a specific run
   - **Thematic Report** — cross-event thematic analysis
   - **Review Report** — post-mortem review of a prediction run
2. Select the target event and/or run
3. Click "Export PDF"
4. Download the generated report

## Tips & Best Practices

### Getting the Most from the Platform

1. **Run the pipeline regularly** — daily or weekly to keep event data current
2. **Always record actual outcomes** — without ground truth, calibration is meaningless
3. **Use multiple theories** — each theory reveals different dynamics
4. **Branch aggressively** — counterfactuals reveal what assumptions matter most
5. **Build your case library** — the more historical cases, the better the analogies
6. **Watch the calibration trend** — if hit rate declines, your models may be overfitting

### Interpreting Brier Scores

| Score | Quality |
|-------|---------|
| ≤ 0.10 | Excellent — predictions significantly better than random |
| ≤ 0.18 | Good — useful predictive power |
| ≤ 0.22 | Fair — some skill, needs improvement |
| > 0.22 | Poor — near or below random chance |

### Interpreting Calibration Grades

| Grade | Meaning |
|-------|---------|
| A | Predictions significantly outperform random baseline |
| B | Good quality predictions with some room for improvement |
| C | Moderate quality — needs systematic improvement |
| D | Below expectations — approaching random performance |
| F | Worse than random — fundamental model issues |

## Troubleshooting

### Pipeline fails to run
- Check `ANTHROPIC_API_KEY` in `.env` is valid
- Check backend logs for specific error messages
- Ensure internet connectivity for RSS feed fetching

### No events appear
- Run the pipeline first — events are generated from news clusters
- Check that RSS feeds are accessible from your network

### Calibration page shows no data
- You need at least one completed prediction run with a recorded actual outcome
- Follow steps 5-6 above and return to Calibration

### PDF export fails
- Ensure Chinese fonts are installed (WenQuanYi Zen Hei or Noto CJK)
- Docker image includes fonts by default
- Check disk space for PDF generation

### Frontend shows "Offline"
- Backend is not running or not reachable
- Check `VITE_API_BASE_URL` in frontend environment
- Verify CORS settings in `.env`
