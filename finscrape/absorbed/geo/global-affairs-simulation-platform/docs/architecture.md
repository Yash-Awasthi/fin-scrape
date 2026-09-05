# Architecture Guide

## High-Level Design

The IR Intelligence Platform follows a **layered service architecture** with a clear separation between API routing, business logic, and data persistence.

```
┌──────────────────────────────────────────────────┐
│                   Frontend (React)                 │
│  Pages: Globe, Pipeline, Events, Scenarios, etc.  │
│  State: Zustand stores                            │
│  Routing: React Router v6                         │
├──────────────────────────────────────────────────┤
│                  REST API (FastAPI)                │
│  /api/v1/auth/*    /api/v1/events/*               │
│  /api/v1/pipeline/* /api/v1/scenarios/*           │
│  /api/v1/analogies/* /api/v1/calibration/*        │
├──────────────────────────────────────────────────┤
│              Service Layer (Business Logic)        │
│  IngestionService  ClusteringService               │
│  EventAbstractionService  TheoryAnalysisService    │
│  ScenarioScriptEngine  BranchEngine                │
│  AnalogyEngine  CalibrationService                 │
│  PDFExportService  InferenceLayerService           │
├──────────────────────────────────────────────────┤
│                   Core Layer                       │
│  LLMRouter (Anthropic)  Auth (JWT)                 │
│  Config  RateLimiter  Logging                      │
├──────────────────────────────────────────────────┤
│              Data Layer (SQLAlchemy ORM)           │
│  Models: IRGEvent, ScenarioScript, PredictionRun   │
│  ActualOutcome, HistoricalCase, etc.               │
├──────────────────────────────────────────────────┤
│          Database (SQLite / PostgreSQL)            │
└──────────────────────────────────────────────────┘
```

## Key Design Decisions

### 1. SQLAlchemy 2.0 + Alembic
- **Why not Django ORM?** FastAPI + SQLAlchemy gives finer control and async support
- **Why Alembic?** Industry-standard migration management for schema evolution
- **SQLite for dev, PostgreSQL for prod** — transparent switching via DATABASE_URL

### 2. Service-Oriented Backend
Each domain concern is a separate service class:
- Services are **independently testable**
- Services accept **dependency injection** (LLM router, DB session)
- Services never import from routers (avoids circular dependencies)

### 3. LLM Router Pattern
The `LLMRouter` centralizes all Claude API calls:
```python
class LLMRouter:
    def chat_completion(self, system_prompt: str, user_message: str) -> str
    def chat_completion_json(self, system_prompt: str, user_message: str) -> dict
```
Benefits:
- Single place for API key management, error handling, retry logic
- Easy to mock in tests
- Model configuration in one place

### 4. Modular Frontend Pages
Each page is a self-contained React component with:
- Its own data fetching (useEffect + service API)
- Local state (useState) for UI concerns
- Shared state (Zustand) for cross-page concerns (events list)
- Full i18n support

### 5. Shared UI Component Library
- `LoadingSpinner` — animated spinner with i18n ARIA labels
- `ErrorState` — error display with i18n title, message, retry
- `EmptyState` — empty placeholder with icon, title, description
- `Charts` — SimpleLineChart, SimpleBarChart, CalibrationCurve (Recharts wrappers)
- `useFocusTrap` — modal accessibility hook

## Data Models

### Core Entity: AbstractIRGEvent
The central data model representing a structured geopolitical event:
- `event_id` — UUID primary key
- `event_title` — short descriptive title
- `event_type` — classified type (military_escalation, diplomatic_negotiation, etc.)
- `crisis_stage` — latent, emergence, escalation, crisis, de_escalation, resolution
- `key_actors` — list of involved actors
- `strategic_dimensions` — military, economic, diplomatic, informational
- `summary` — LLM-generated event summary
- `rule_of_engagement_triggers` — classified triggers for scenario generation

### Scenario Scripts
Each event has scripts in three directions (escalation, stalemate, de_escalation):
- `probability_low/central/high` — forecast probability ranges
- `confidence_level` — high/medium/low
- `trigger_conditions` — what would cause this script to play out
- `invalidation_conditions` — what would disprove this script
- `steps` — step-by-step timeline with actor motivations and evidence

### Prediction Runs
Each analysis run produces a `PredictionRun`:
- Links an event to a set of generated scripts
- Stores the analysis summary
- Tracks actual outcomes and evaluations when available

### Calibration
Continuous accuracy tracking:
- `script_hit_rate` — was the closest matching script correct?
- `node_hit_rate` — were individual scenario steps correct?
- `avg_brier_score` — probabilistic accuracy (0 = perfect, 0.25 = random)
- `calibration_grade` — A to F letter grade

## Pipeline Flow

```
1. RSS Ingestion
   ├── Fetch from configured RSS feeds
   ├── Parse and normalize articles
   └── Store as RawNews records

2. Clustering (LLM-powered)
   ├── Bundle RawNews into semantic clusters
   ├── Merge with existing clusters if similar
   └── Produce NewsCluster records

3. Event Abstraction (LLM-powered)
   ├── Extract structured events from clusters
   ├── Classify event type, crisis stage, actors
   ├── Identify trigger rules and constraints
   └── Store AbstractIRGEvent records

4. Theory Analysis (LLM-powered)
   ├── Apply multiple IR theories to the event
   ├── Generate theory-specific insights
   └── Store TheoryAnalysis records

5. Scenario Generation (LLM-powered)
   ├── Generate scripts for each direction
   ├── Estimate probability ranges
   ├── Build step-by-step timelines
   └── Store ScenarioScript + ScenarioStep records

6. Historical Analogy (LLM-powered)
   ├── Search historical case database
   ├── Compute structural similarity
   ├── Extract base rates and lessons
   └── Store AnalogyResult records

7. Calibration Loop (human + automated)
   ├── Record actual outcomes
   ├── Run automated evaluation
   ├── Update calibration metrics
   └── Generate improvement suggestions
```

## File Organization

```
ir-intel-platform/
├── backend/
│   ├── main.py              # FastAPI app entry point
│   ├── routers/             # API route handlers
│   │   ├── api.py           # Mounts all sub-routers
│   │   ├── auth.py          # Authentication endpoints
│   │   ├── pipeline.py      # Pipeline trigger & status
│   │   └── annotations.py   # Annotation endpoints
│   ├── services/            # Business logic
│   │   ├── ingestion_service.py
│   │   ├── clustering_service.py
│   │   ├── event_abstraction_service.py
│   │   ├── theory_analysis_service.py
│   │   ├── scenario_script_engine.py
│   │   ├── branch_engine.py
│   │   ├── analogy_engine.py
│   │   ├── calibration_service.py
│   │   └── pdf_export_service.py
│   ├── core/                # Cross-cutting concerns
│   │   ├── llm_router.py    # Anthropic API wrapper
│   │   ├── config.py        # Settings management
│   │   ├── auth.py          # JWT + password hashing
│   │   ├── logging_config.py
│   │   ├── rate_limiter.py
│   │   └── prompts/         # LLM prompt templates
│   ├── models/              # SQLAlchemy ORM models
│   │   ├── ir_event.py
│   │   ├── scenario.py
│   │   ├── prediction.py
│   │   ├── outcome.py
│   │   ├── historical_case.py
│   │   ├── analogy.py
│   │   └── ...
│   └── db/                  # Database setup
│       └── database.py      # Engine, session, Base
├── frontend/
│   └── src/
│       ├── main.tsx          # App entry, routing
│       ├── App.tsx           # Layout, auth check
│       ├── pages/            # Page components
│       │   ├── GlobePage.tsx
│       │   ├── PipelinePage.tsx
│       │   ├── EventsPage.tsx
│       │   ├── TheoriesPage.tsx
│       │   ├── ScenariosPage.tsx
│       │   ├── BranchPage.tsx
│       │   ├── AnalogiesPage.tsx
│       │   ├── HistoryPage.tsx
│       │   ├── CalibrationPage.tsx
│       │   └── ReportPage.tsx
│       ├── components/       # Shared components
│       ├── services/         # API client (axios)
│       ├── store/            # Zustand stores
│       ├── hooks/            # Custom hooks
│       ├── i18n/             # Translations
│       └── types/            # TypeScript types
├── tests/                    # Backend tests
├── docs/                     # Documentation
├── alembic/                  # DB migrations
├── Dockerfile
├── docker-compose.yml
└── README.md
```
