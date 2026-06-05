# TRER — Temporal Relational Event Reconstruction

TRER is an engine for reconstructing event timelines, relationship graphs, and competing hypotheses from observations over time.

The near-term goal is to build a small, deterministic core before extending plugins, visualizers, or domain-specific prisms.

## Core Invariant

> TRER core should be able to reconstruct a simple temporal event graph from plain JSON fixtures without any external AI system.

This invariant is the anchor for the project. Falcon Vision, GEPA-viz, LLMs, and domain plugins may improve or visualize the workflow, but the core engine must remain independently testable and explainable.

## Initial Development Strategy

1. **Commit the seed state**
   - Keep the initial repo structure and intent under version control.
   - Make every structural change traceable.

2. **Define the core contract before implementation**
   - Start with a minimal data model:
     - `Entity`
     - `Event`
     - `Relationship`
     - `Observation`
     - `Hypothesis`
     - `Timeline`
   - Decide what TRER accepts and emits before binding it to Falcon Vision, GEPA-viz, or any other tool.

3. **Build the deterministic core first**
   - No model calls.
   - No plugins.
   - No visualizers.
   - First target: observations → events → relationships → timeline/hypotheses.

4. **Add tests immediately**
   - Use small, human-readable fixtures.
   - Early test cases should include:
     - two detections over time becoming a movement event
     - object A near object B creating a spatial relationship
     - contradictory observations producing competing hypotheses

5. **Add adapters/plugins only after the core passes tests**
   - Falcon Vision adapter: convert detections into TRER observations.
   - GEPA-viz adapter: render hypothesis/evaluation traces.
   - Domain prisms: criminology, biology, markets, genealogy, infrastructure, civilization, clerical, etc.

## Proposed Project Structure

```text
trer/
│
├── core/
│   ├── compression.py
│   ├── decompression.py
│   ├── event_graph.py
│   ├── timeline_builder.py
│   └── narrative_reconstructor.py
│
├── prisms/
│   ├── genealogy/
│   ├── criminology/
│   ├── markets/
│   ├── infrastructure/
│   ├── civilization/
│   ├── clerical/
│   └── biology/
│
└── outputs/
```
