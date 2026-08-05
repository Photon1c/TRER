# TRER — Temporal Relational Event Reconstruction

TRER is an engine for reconstructing event timelines, relationship graphs, and competing hypotheses from observations over time.

The near-term goal is to build a small, deterministic core before extending plugins, visualizers, or domain-specific prisms.

## Core Invariant

> TRER core should be able to reconstruct a simple temporal event graph from plain JSON fixtures without any external AI system.

This invariant is the anchor for the project. Falcon Vision, GEPA-viz, LLMs, and domain plugins may improve or visualize the workflow, but the core engine must remain independently testable and explainable.

## Design Pressure

TRER is expanding conceptually toward:

```text
Pressure
  ↓
Routing
  ↓
Dissipation
  ↓
State Transition
```

This pressure-routing-dissipation-transition model is a useful analytical frame; however, the software core must remain narrow. Pressure tracking, ambiguity routing, and domain-specific interpretation should be expressed through fixtures and prisms until the core has earned more abstraction.

## Core Shape

```text
trer/
├── core/
│   ├── nodes.py           # entities and observations
│   ├── edges.py           # relationships
│   ├── events.py          # reconstructed state changes
│   ├── timelines.py       # timelines and hypotheses
│   └── reconstruction.py  # deterministic transforms over plain JSON-compatible input
│
└── prisms/
    ├── perception/        # Falcon Vision-style observations
    ├── workflow/          # Pixel Office-style queues/tasks/state
    ├── market/            # Gamma Reflexivity-style market pressure timelines
    ├── inventory/         # inventory reconciliation and queue growth
    ├── criminology/       # burglary-ring timelines and uncertainty scoring
    ├── infrastructure/    # dependency/failure investigation timelines
    └── narrative/         # human-readable explanations
```

Compatibility modules `trer.core.models` and `trer.core.reconstructor` remain available while the layout stabilizes.

## Initial Development Strategy

1. **Keep the core deterministic**
   - No model calls.
   - No required plugins.
   - No visualizer dependency.
   - First target: observations → events → relationships → timeline/hypotheses.

2. **Define behavior with fixtures**
   - Use small, human-readable JSON fixtures.
   - Every new abstraction should be justified by a fixture and a test.

3. **Let prisms adapt domains, not redefine core**
   - Falcon Vision becomes a perception prism.
   - Pixel Office becomes a workflow prism.
   - Gamma Reflexivity becomes a market prism.
   - Critical Dependency Observatory becomes an infrastructure prism.

4. **Add adapters only after core tests pass**
   - Falcon Vision adapter: convert detections into TRER observations.
   - GEPA-viz adapter: render hypothesis/evaluation traces.
   - Domain prisms: inventory, criminology, market, infrastructure, workflow, narrative, etc.

## Candidate Demo Paths

These demos should exercise the same core engine from different prism angles:

- **Starbucks Inventory Test**
  - ambiguity routing
  - inventory reconciliation
  - queue growth

- **Burglary Ring Timeline**
  - TRER reconstruction
  - temporal linking
  - uncertainty scoring

- **SPY Reflexivity Timeline**
  - news event
  - options pressure
  - price response
  - execution decoupling / `BID_SPREAD_FALSE_STOP` events
  - false-stop cost / missed P&L
  - post-event dissipation

- **Critical Dependency Observatory / CDN Index**
  - high-flow civic/residential/industrial node discovery
  - dependency, flow, consequence, and dissipation signals
  - unresolved-pressure ranking without treating age as automatic risk
  - later public-record enrichment and vector similarity search

## Current Test Gate

```bash
python3 -m unittest discover -s tests -v
```

---

## Related Apps

TRER is part of the [Systems Lab App Registry](~/docs/landing_zone/app-registry.md).

| App | Relationship |
|-----|-------------|
| [Systems Lab Health Dashboard](~/.openclaw/workspace-main/tools/dashboard/) | TRER reconstruction outputs can feed the Lab Health tab for confidence/gap analysis |
| [Nightwatchauton](../nightwatchauton/) | Shared observer layer; both visualize system state |
| [Explorer Agents](~/.openclaw/workspace-main/tools/exploreragents/) | Scout scan data can feed TRER reconstruction prisms |
| [Custodians](~/.openclaw/workspace-main/tools/custodians/) | Custodian health events can be reconstructed as temporal timelines |
| [Security Guards](~/.openclaw/workspace-main/tools/securityguards/) | Security events are natural inputs for TRER's infrastructure prism |
