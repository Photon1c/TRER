# Critical Dependency Observatory / CDN Prism

## Purpose

Build a **Critical Dependency Node (CDN)** indexing system for high-flow industrial, civic, residential, and public-facing nodes.

The goal is **not** to predict failure directly. The first goal is to rank nodes by unresolved pressure:

> Which districts or nodes exhibit the greatest concentration of unresolved pressure?

Unresolved pressure means high people-flow, dependency density, and consequence density relative to visible dissipation capacity.

## Initial Geographic Scope

1. Washington D.C. first.
2. Chicago later as a stress-test city.

## Ranking Bias

Prioritize **flow concentration** over building age.

Building age is only a service-life context variable. It should not become a primary risk score. Old buildings are not automatically risky; the useful signal is a mismatch between load/flow/consequence and visible maintenance, renovation, redundancy, or management capacity.

## Primary Node Categories

- Large multifamily buildings
- Hospitals
- Transit stations
- Schools / universities
- Senior living facilities
- Government buildings
- Industrial facilities
- Public gathering places
- Large retail / mall / convention nodes

## Core Metrics

- **Static dependency density**: residents, beds, units, workers, tenants.
- **Dynamic flow density**: daily visitors, foot traffic, events, deliveries, transient use, service traffic.
- **Consequence density**: people displaced, services interrupted, economic impact, regional dependency.
- **Dissipation capacity**: maintenance, renovations, permits, repairs, management quality, redundancy.
- **Pressure mismatch**: high flow + high dependency + weak/unknown dissipation.

Unknown dissipation should trigger enrichment; it should not automatically be treated as proven weakness.

## Candidate Data Sources

### Discovery / proxy layer

- Google Places API for initial node discovery.
- Place type, review count, rating, hours, location.
- Nearby transit, parking, services.

Caveat: Google-derived signals are proxies, not ground truth. Official Places API may not expose actual foot traffic/popularity. Review count may reflect visibility, tourism, or review habits rather than real flow.

### Enrichment layer

Later public-record sources:

- permits
- violations
- property records
- inspections
- renovation history
- ownership / management records
- service interruption reports

## CDN JSON Packet

```json
{
  "node_id": "",
  "name": "",
  "city": "Washington D.C.",
  "address": "",
  "lat": null,
  "lng": null,
  "node_class": "housing | medical | transit | civic | education | industrial | retail",
  "place_types": [],
  "static_dependency_density": null,
  "dynamic_flow_density": null,
  "consequence_density": null,
  "dissipation_capacity": null,
  "pressure_mismatch_score": null,
  "review_count": null,
  "rating": null,
  "nearby_transit_count": null,
  "nearby_parking_count": null,
  "nearby_services_count": null,
  "known_public_records": [],
  "source_urls": [],
  "confidence": "low | medium | high"
}
```

Metric values should be normalized `0..1` once scoring begins. Raw data should remain available in source-specific records or enrichment artifacts.

## Vector Search Plan

1. Build CDN JSON packets.
2. Convert each packet into a text summary.
3. Embed each packet.
4. Store vectors in FAISS first as a baseline.
5. Test turbovec/turboquant compressed vector storage and retrieval later.
6. Query by structural similarity, not just keywords.

Example structural query:

> Find nodes similar to a large aging multifamily building with high visitor flow, limited renovation history, repeated service complaints, and high displacement consequence.

## Near-Term MVP

1. Pick D.C.
2. Pull top candidate nodes from 8–10 categories.
3. Deduplicate by `place_id`, name, and address.
4. Generate 100–500 CDN packets.
5. Rank by flow concentration first.
6. Enrich top 25 with public records.
7. Embed packets.
8. Build similarity search.
9. Compare FAISS vs turbovec/turboquant later.

## TRER Boundary

This belongs in the `infrastructure` prism. The TRER core should not learn about hospitals, malls, schools, permits, or Google Places. The prism should translate CDN evidence into generic nodes/events/relationships only when reconstruction behavior needs core support.
