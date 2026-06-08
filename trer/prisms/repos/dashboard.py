"""Private repository pressure dashboard prism.

A repository is treated as a pressure-bearing node. The goal is not to judge old
repos as bad; age is context only. The key distinction is:

- pressure: work/load currently being carried
- criticality: importance to the ecosystem
- velocity: how fast it is changing
- stability: how well maintenance is keeping up
- urgency: pressure × criticality
- platform: criticality × architectural importance
"""

from __future__ import annotations

import argparse
import html
import json
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Literal, Optional

RankMode = Literal["pressure", "criticality", "urgency", "velocity", "stability", "platform", "stale", "documentation", "dependency"]
Confidence = Literal["low", "medium", "high"]

ACTIONS = {
    "prioritize immediately",
    "improve README",
    "add tests",
    "archive candidate",
    "monitor",
    "low priority",
}

DEPENDENCY_WEIGHT = 0.4
ARCHITECTURE_WEIGHT = 0.4
CONSEQUENCE_WEIGHT = 0.2


@dataclass(frozen=True)
class RepoPressureNode:
    repo_name: str
    repo_url: str = ""
    primary_language: str = ""
    last_commit_date: str = ""
    days_since_last_commit: Optional[int] = None
    readme_quality_score: Optional[float] = None
    issue_count: int = 0
    open_pr_count: int = 0
    dependency_count: int = 0
    downstream_dependency_count: int = 0
    strategic_importance_score: Optional[float] = None
    future_dependency_score: Optional[float] = None
    architectural_importance_score: Optional[float] = None
    foundational_project: bool = False
    complexity_score: Optional[float] = None
    maintenance_activity_score: Optional[float] = None
    documentation_gap_score: Optional[float] = None
    change_velocity_score: Optional[float] = None
    demand_score: Optional[float] = None
    complexity_growth_score: Optional[float] = None
    stability_score: Optional[float] = None
    pressure_score: Optional[float] = None
    pressure_input_score: Optional[float] = None
    dissipation_capacity_score: Optional[float] = None
    dependency_density_score: Optional[float] = None
    consequence_density_score: Optional[float] = None
    pressure_mismatch_score: Optional[float] = None
    criticality_score: Optional[float] = None
    urgency_score: Optional[float] = None
    platform_score: Optional[float] = None
    recommended_action: str = "monitor"
    confidence: Confidence = "low"
    notes: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RepoPressureNode":
        return cls(
            repo_name=str(data.get("repo_name", "")),
            repo_url=str(data.get("repo_url", "")),
            primary_language=str(data.get("primary_language", "")),
            last_commit_date=str(data.get("last_commit_date", "")),
            days_since_last_commit=data.get("days_since_last_commit"),
            readme_quality_score=data.get("readme_quality_score"),
            issue_count=int(data.get("issue_count", 0) or 0),
            open_pr_count=int(data.get("open_pr_count", 0) or 0),
            dependency_count=int(data.get("dependency_count", 0) or 0),
            downstream_dependency_count=int(data.get("downstream_dependency_count", 0) or 0),
            strategic_importance_score=data.get("strategic_importance_score"),
            future_dependency_score=data.get("future_dependency_score"),
            architectural_importance_score=data.get("architectural_importance_score"),
            foundational_project=bool(data.get("foundational_project", False)),
            complexity_score=data.get("complexity_score"),
            maintenance_activity_score=data.get("maintenance_activity_score"),
            documentation_gap_score=data.get("documentation_gap_score"),
            change_velocity_score=data.get("change_velocity_score"),
            demand_score=data.get("demand_score"),
            complexity_growth_score=data.get("complexity_growth_score"),
            stability_score=data.get("stability_score"),
            pressure_score=data.get("pressure_score"),
            pressure_input_score=data.get("pressure_input_score"),
            dissipation_capacity_score=data.get("dissipation_capacity_score"),
            dependency_density_score=data.get("dependency_density_score"),
            consequence_density_score=data.get("consequence_density_score"),
            pressure_mismatch_score=data.get("pressure_mismatch_score"),
            criticality_score=data.get("criticality_score"),
            urgency_score=data.get("urgency_score"),
            platform_score=data.get("platform_score"),
            recommended_action=str(data.get("recommended_action", "monitor")),
            confidence=data.get("confidence", "low"),
            notes=list(data.get("notes", [])),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def clamp_0_1(value: float) -> float:
    return max(0.0, min(1.0, value))


def normalize_count(value: float, cap: float) -> float:
    if cap <= 0:
        return 0.0
    return clamp_0_1(value / cap)


def days_since(iso_date: str, *, today: Optional[date] = None) -> Optional[int]:
    if not iso_date:
        return None
    today = today or datetime.now(timezone.utc).date()
    try:
        if iso_date.endswith("Z"):
            stamp = datetime.fromisoformat(iso_date.replace("Z", "+00:00")).date()
        else:
            stamp = date.fromisoformat(iso_date[:10])
    except ValueError:
        return None
    return (today - stamp).days


def infer_architectural_importance(node: RepoPressureNode) -> float:
    """Infer a conservative architecture score when one is not supplied.

    Manual `architectural_importance_score` is preferred. This fallback is only
    for rough private triage over large repo inventories.
    """

    if node.architectural_importance_score is not None:
        return clamp_0_1(float(node.architectural_importance_score))
    if node.foundational_project:
        return 0.9

    text = " ".join([node.repo_name, node.repo_url, node.primary_language, *node.notes]).lower()
    if any(term in text for term in ["openclaw", "trer", "framework", "platform", "substrate", "engine"]):
        return 0.75
    if any(term in text for term in ["toolkit", "utility", "library", "harness", "dashboard"]):
        return 0.5
    if any(term in text for term in ["experiment", "prototype", "sandbox", "sim"]):
        return 0.25
    return 0.25


def compute_repo_scores(node: RepoPressureNode) -> RepoPressureNode:
    """Fill derived pressure-dashboard scores.

    Pressure is gross load being carried, not merely unresolved mismatch. A
    healthy maintained platform can have high pressure and high stability.
    """

    readme_quality = clamp_0_1(float(node.readme_quality_score if node.readme_quality_score is not None else 0.0))

    documentation_gap = node.documentation_gap_score
    if documentation_gap is None:
        documentation_gap = 1.0 - readme_quality
    documentation_gap = clamp_0_1(float(documentation_gap))

    complexity = clamp_0_1(float(node.complexity_score if node.complexity_score is not None else 0.0))
    maintenance = clamp_0_1(
        float(node.maintenance_activity_score if node.maintenance_activity_score is not None else 0.0)
    )

    age_days = node.days_since_last_commit
    if age_days is None:
        age_days = days_since(node.last_commit_date)
    recent_activity = 0.0 if age_days is None else 1.0 - normalize_count(age_days, 365)

    strategic_importance = clamp_0_1(
        float(node.strategic_importance_score if node.strategic_importance_score is not None else 0.0)
    )
    future_dependency = clamp_0_1(
        float(node.future_dependency_score if node.future_dependency_score is not None else 0.0)
    )
    architectural_importance = infer_architectural_importance(node)
    if node.foundational_project:
        strategic_importance = max(strategic_importance, 0.8)
        future_dependency = max(future_dependency, 0.65)
        architectural_importance = max(architectural_importance, 0.9)

    issue_pressure = normalize_count(node.issue_count, 25)
    pr_pressure = normalize_count(node.open_pr_count, 10)

    velocity = node.change_velocity_score
    if velocity is None:
        velocity = recent_activity
    velocity = round(clamp_0_1(float(velocity)), 4)

    demand = node.demand_score
    if demand is None:
        demand = (issue_pressure + pr_pressure + future_dependency + strategic_importance) / 4.0
    demand = round(clamp_0_1(float(demand)), 4)

    complexity_growth = node.complexity_growth_score
    if complexity_growth is None:
        complexity_growth = (complexity + future_dependency + architectural_importance) / 3.0
    complexity_growth = round(clamp_0_1(float(complexity_growth)), 4)

    test_signal = 0.0
    for note in node.notes:
        lowered = str(note).lower()
        if "needs test" in lowered or "no test" in lowered or "missing test" in lowered:
            continue
        if "tests passing" in lowered or "test coverage" in lowered or "coverage:" in lowered:
            test_signal = max(test_signal, 0.5)

    stability = node.stability_score
    if stability is None:
        stability = node.dissipation_capacity_score
    if stability is None:
        stability = (recent_activity + readme_quality + test_signal + maintenance) / 4.0
    stability = round(clamp_0_1(float(stability)), 4)

    pressure = node.pressure_score
    if pressure is None:
        pressure = (velocity * 0.4) + (demand * 0.3) + (complexity_growth * 0.3)
    pressure = round(clamp_0_1(float(pressure)), 4)

    # Backward-compatible field: now represents unresolved pressure after
    # stability, while `pressure_score` is gross load.
    mismatch = node.pressure_mismatch_score
    if mismatch is None:
        mismatch = max(0.0, pressure - stability)
    mismatch = round(clamp_0_1(float(mismatch)), 4)

    dependency_density = node.dependency_density_score
    if dependency_density is None:
        dependency_density = (
            normalize_count(node.dependency_count, 80)
            + normalize_count(node.downstream_dependency_count, 20)
            + future_dependency
        ) / 3.0
    dependency_density = round(clamp_0_1(float(dependency_density)), 4)

    consequence = node.consequence_density_score
    if consequence is None:
        observed_consequence = normalize_count(node.downstream_dependency_count, 20)
        if "strategic" in " ".join(node.notes).lower():
            strategic_importance = max(strategic_importance, 0.75)
        consequence = max(observed_consequence, strategic_importance)
    consequence = round(clamp_0_1(float(consequence)), 4)

    criticality = node.criticality_score
    if criticality is None:
        criticality = (
            dependency_density * DEPENDENCY_WEIGHT
            + architectural_importance * ARCHITECTURE_WEIGHT
            + consequence * CONSEQUENCE_WEIGHT
        )
    criticality = round(clamp_0_1(float(criticality)), 4)

    urgency = node.urgency_score
    if urgency is None:
        urgency = pressure * criticality
    urgency = round(clamp_0_1(float(urgency)), 4)

    platform = node.platform_score
    if platform is None:
        platform = criticality * architectural_importance
    platform = round(clamp_0_1(float(platform)), 4)

    confidence = node.confidence
    known = sum(
        value is not None
        for value in [
            node.readme_quality_score,
            node.complexity_score,
            node.maintenance_activity_score,
            node.days_since_last_commit or node.last_commit_date,
        ]
    )
    if confidence == "low" and known >= 3:
        confidence = "medium"

    scored = RepoPressureNode(
        **{
            **node.to_dict(),
            "days_since_last_commit": age_days,
            "documentation_gap_score": documentation_gap,
            "change_velocity_score": velocity,
            "demand_score": demand,
            "complexity_growth_score": complexity_growth,
            "stability_score": stability,
            "pressure_score": pressure,
            "pressure_input_score": pressure,
            "dissipation_capacity_score": stability,
            "dependency_density_score": dependency_density,
            "consequence_density_score": consequence,
            "architectural_importance_score": architectural_importance,
            "pressure_mismatch_score": mismatch,
            "criticality_score": criticality,
            "urgency_score": urgency,
            "platform_score": platform,
            "confidence": confidence,
        }
    )
    return RepoPressureNode(**{**scored.to_dict(), "recommended_action": recommended_action(scored)})

def recommended_action(node: RepoPressureNode) -> str:
    """Choose a conservative next action from derived scores."""

    pressure = node.pressure_score or node.pressure_input_score or 0.0
    mismatch = node.pressure_mismatch_score or 0.0
    criticality = node.criticality_score or 0.0
    urgency = node.urgency_score or 0.0
    doc_gap = node.documentation_gap_score or 0.0
    dissipation = node.dissipation_capacity_score or 0.0
    age = node.days_since_last_commit

    if urgency >= 0.35 or (pressure >= 0.7 and criticality >= 0.55 and dissipation < 0.5):
        return "prioritize immediately"
    if doc_gap >= 0.65 and pressure >= 0.25:
        return "improve README"
    if dissipation < 0.35 and pressure >= 0.3:
        return "add tests"
    if age is not None and age >= 730 and pressure < 0.2 and criticality < 0.25:
        return "archive candidate"
    if pressure < 0.15 and criticality < 0.25:
        return "low priority"
    return "monitor"


def rank_repos(nodes: Iterable[RepoPressureNode], mode: RankMode = "pressure") -> list[RepoPressureNode]:
    scored = [compute_repo_scores(node) for node in nodes]

    def key(node: RepoPressureNode) -> tuple[float, float, float, float]:
        if mode == "criticality":
            return (
                node.criticality_score or 0.0,
                node.architectural_importance_score or 0.0,
                node.consequence_density_score or 0.0,
                node.dependency_density_score or 0.0,
            )
        if mode == "urgency":
            return (
                node.urgency_score or 0.0,
                node.pressure_score or 0.0,
                node.criticality_score or 0.0,
                node.change_velocity_score or 0.0,
            )
        if mode == "velocity":
            return (
                node.change_velocity_score or 0.0,
                node.pressure_score or 0.0,
                node.criticality_score or 0.0,
                node.urgency_score or 0.0,
            )
        if mode == "stability":
            return (
                node.stability_score or 0.0,
                node.criticality_score or 0.0,
                node.pressure_score or 0.0,
                node.urgency_score or 0.0,
            )
        if mode == "platform":
            return (
                node.platform_score or 0.0,
                node.criticality_score or 0.0,
                node.architectural_importance_score or 0.0,
                node.pressure_score or 0.0,
            )
        if mode == "stale":
            return (
                float(node.days_since_last_commit or -1),
                node.pressure_score or 0.0,
                node.criticality_score or 0.0,
                node.documentation_gap_score or 0.0,
            )
        if mode == "documentation":
            return (
                node.documentation_gap_score or 0.0,
                node.pressure_score or 0.0,
                node.criticality_score or 0.0,
                node.readme_quality_score or 0.0,
            )
        if mode == "dependency":
            return (
                node.dependency_density_score or 0.0,
                node.consequence_density_score or 0.0,
                node.criticality_score or 0.0,
                node.pressure_score or 0.0,
            )
        return (
            node.pressure_score or 0.0,
            node.urgency_score or 0.0,
            node.criticality_score or 0.0,
            node.change_velocity_score or 0.0,
        )

    return sorted(scored, key=key, reverse=True)


def load_repo_nodes(path: Path) -> list[RepoPressureNode]:
    raw = json.loads(path.read_text())
    if not isinstance(raw, list):
        raise ValueError("repo report input must be a JSON list")
    return [RepoPressureNode.from_dict(item) for item in raw]


def write_json_export(nodes: list[RepoPressureNode], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps([node.to_dict() for node in nodes], indent=2, sort_keys=True) + "\n")


def write_html_dashboard(nodes: list[RepoPressureNode], path: Path) -> None:
    """Write a self-contained, phone-friendly HTML repo dashboard.

    The exported file intentionally has no API calls, external CSS, external
    fonts, or build step. It can be copied to a phone and opened directly.
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [node.to_dict() for node in nodes]
    generated_at = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M %Z")
    safe_payload = json.dumps(rows, sort_keys=True).replace("</", "<\\/")
    total = len(rows)
    prioritize = sum(1 for row in rows if row.get("recommended_action") == "prioritize immediately")
    monitor = sum(1 for row in rows if row.get("recommended_action") == "monitor")
    avg_pressure = sum(float(row.get("pressure_score") or 0) for row in rows) / total if total else 0.0
    avg_criticality = sum(float(row.get("criticality_score") or 0) for row in rows) / total if total else 0.0

    doc = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
  <title>Repo Pressure Dashboard — Portable</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #111427;
      --panel: rgba(28, 35, 62, 0.88);
      --panel-2: rgba(18, 24, 45, 0.94);
      --line: rgba(164, 174, 204, 0.18);
      --text: #eef3ff;
      --muted: #9aa8c7;
      --dim: #687694;
      --cyan: #7dd3fc;
      --green: #7ee787;
      --orange: #f6ad55;
      --red: #fb7185;
      --pink: #f687b3;
      --purple: #c084fc;
      --blue: #63b3ed;
      --yellow: #f6e05e;
      --shadow: 0 18px 45px rgba(0, 0, 0, 0.28);
    }}
    * {{ box-sizing: border-box; }}
    html {{ min-height: 100%; background: var(--bg); }}
    body {{
      margin: 0;
      min-height: 100vh;
      font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--text);
      background:
        radial-gradient(circle at 10% 0%, rgba(125, 211, 252, 0.18), transparent 28rem),
        radial-gradient(circle at 90% 8%, rgba(192, 132, 252, 0.16), transparent 26rem),
        linear-gradient(145deg, #101225 0%, #171b32 52%, #111427 100%);
      padding: max(16px, env(safe-area-inset-top)) max(14px, env(safe-area-inset-right)) max(24px, env(safe-area-inset-bottom)) max(14px, env(safe-area-inset-left));
    }}
    .shell {{ max-width: 1180px; margin: 0 auto; }}
    header {{
      position: sticky;
      top: 0;
      z-index: 5;
      padding: 10px 0 12px;
      margin-bottom: 8px;
      background: linear-gradient(180deg, rgba(17,20,39,0.98), rgba(17,20,39,0.78) 72%, transparent);
      backdrop-filter: blur(12px);
    }}
    h1 {{ margin: 0; font-size: clamp(1.55rem, 5.5vw, 2.7rem); letter-spacing: -0.04em; }}
    .subtitle {{ margin: 4px 0 0; color: var(--muted); font-size: 0.94rem; line-height: 1.35; }}
    .topline {{ display: flex; justify-content: space-between; align-items: end; gap: 12px; }}
    .pill {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      border: 1px solid var(--line);
      color: var(--cyan);
      background: rgba(125, 211, 252, 0.08);
      border-radius: 999px;
      padding: 5px 10px;
      font-size: 0.75rem;
      white-space: nowrap;
    }}
    .stats {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; margin: 12px 0; }}
    .stat {{ background: var(--panel); border: 1px solid var(--line); border-radius: 16px; padding: 10px; box-shadow: var(--shadow); }}
    .stat b {{ display: block; font-size: 1.22rem; }}
    .stat span {{ color: var(--muted); font-size: 0.75rem; }}
    .controls {{ display: grid; gap: 8px; margin: 12px 0 14px; }}
    .rank-tabs {{ display: flex; overflow-x: auto; gap: 6px; padding-bottom: 2px; scrollbar-width: thin; }}
    button, input, select {{ font: inherit; }}
    .rank-tab, .utility-btn {{
      border: 1px solid var(--line);
      background: rgba(255,255,255,0.045);
      color: var(--muted);
      border-radius: 999px;
      padding: 8px 11px;
      min-height: 36px;
      white-space: nowrap;
    }}
    .rank-tab.active {{ color: #09111e; background: var(--cyan); border-color: var(--cyan); font-weight: 800; }}
    .filter-row {{ display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 8px; }}
    #search {{
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 14px;
      background: rgba(0,0,0,0.22);
      color: var(--text);
      padding: 11px 12px;
      min-height: 42px;
    }}
    #limit {{
      border: 1px solid var(--line);
      border-radius: 14px;
      background: rgba(0,0,0,0.22);
      color: var(--text);
      padding: 0 8px;
      min-height: 42px;
    }}
    .status-line {{ color: var(--muted); font-size: 0.83rem; margin: 2px 2px 10px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(310px, 1fr)); gap: 10px; }}
    .card {{
      background: linear-gradient(180deg, var(--panel), var(--panel-2));
      border: 1px solid var(--line);
      border-left: 5px solid var(--cyan);
      border-radius: 18px;
      padding: 12px;
      box-shadow: var(--shadow);
    }}
    .card.priority {{ border-left-color: var(--red); }}
    .card.docs {{ border-left-color: var(--purple); }}
    .card.tests {{ border-left-color: var(--yellow); }}
    .card.low {{ border-left-color: var(--dim); }}
    .card-head {{ display: flex; justify-content: space-between; gap: 10px; align-items: flex-start; }}
    .repo-name {{ font-weight: 850; line-height: 1.15; font-size: 1.02rem; overflow-wrap: anywhere; }}
    .repo-name a {{ color: var(--text); text-decoration: none; }}
    .repo-name a:hover {{ color: var(--cyan); text-decoration: underline; }}
    .meta {{ margin-top: 5px; display: flex; flex-wrap: wrap; gap: 5px; color: var(--muted); font-size: 0.75rem; }}
    .tag {{ border: 1px solid var(--line); background: rgba(255,255,255,0.05); border-radius: 999px; padding: 2px 7px; }}
    .action {{ border-radius: 999px; padding: 4px 8px; font-size: 0.72rem; border: 1px solid var(--line); white-space: nowrap; }}
    .action-prioritize {{ color: var(--red); background: rgba(251,113,133,0.13); border-color: rgba(251,113,133,0.42); }}
    .action-monitor {{ color: var(--green); background: rgba(126,231,135,0.10); border-color: rgba(126,231,135,0.32); }}
    .action-docs {{ color: var(--purple); background: rgba(192,132,252,0.12); border-color: rgba(192,132,252,0.34); }}
    .action-tests {{ color: var(--yellow); background: rgba(246,224,94,0.12); border-color: rgba(246,224,94,0.34); }}
    .action-low, .action-archive {{ color: var(--muted); background: rgba(154,168,199,0.08); }}
    .scores {{ display: grid; gap: 7px; margin-top: 12px; }}
    .score {{ display: grid; grid-template-columns: 86px minmax(0, 1fr) 44px; gap: 8px; align-items: center; }}
    .score label {{ color: var(--muted); font-size: 0.74rem; }}
    .track {{ height: 9px; border-radius: 999px; background: rgba(255,255,255,0.08); overflow: hidden; }}
    .fill {{ height: 100%; width: 0%; border-radius: inherit; }}
    .score output {{ color: var(--text); font-size: 0.74rem; text-align: right; font-variant-numeric: tabular-nums; }}
    details {{ margin-top: 10px; color: var(--muted); font-size: 0.78rem; }}
    summary {{ cursor: pointer; color: var(--cyan); }}
    .notes {{ margin-top: 7px; display: flex; flex-wrap: wrap; gap: 5px; }}
    .empty {{ color: var(--muted); text-align: center; padding: 34px 8px; border: 1px dashed var(--line); border-radius: 18px; }}
    footer {{ color: var(--dim); font-size: 0.75rem; margin: 22px 2px 0; line-height: 1.45; }}
    @media (max-width: 720px) {{
      body {{ padding-left: 10px; padding-right: 10px; }}
      .topline {{ align-items: start; flex-direction: column; }}
      .stats {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .grid {{ grid-template-columns: 1fr; }}
      .card {{ border-radius: 16px; }}
      .score {{ grid-template-columns: 76px minmax(0, 1fr) 42px; }}
    }}
    @media print {{ header {{ position: static; }} body {{ background: #fff; color: #111; }} .card, .stat {{ box-shadow: none; }} }}
  </style>
</head>
<body>
  <div class="shell">
    <header>
      <div class="topline">
        <div>
          <h1>📊 Repo Pressure Dashboard</h1>
          <p class="subtitle">Portable, self-contained repo pressure view. Copy this file anywhere; no Pixel Me server required.</p>
        </div>
        <span class="pill">Generated {html.escape(generated_at)}</span>
      </div>
      <section class="stats" aria-label="summary stats">
        <div class="stat"><b>{total}</b><span>repos</span></div>
        <div class="stat"><b>{prioritize}</b><span>prioritize</span></div>
        <div class="stat"><b>{monitor}</b><span>monitor</span></div>
        <div class="stat"><b>{avg_pressure:.2f} / {avg_criticality:.2f}</b><span>avg pressure / criticality</span></div>
      </section>
      <section class="controls">
        <div class="rank-tabs" id="tabs"></div>
        <div class="filter-row">
          <input id="search" type="search" placeholder="Filter repo, language, action, notes…" autocomplete="off" />
          <select id="limit" aria-label="Limit rows">
            <option value="25">Top 25</option>
            <option value="50" selected>Top 50</option>
            <option value="100">Top 100</option>
            <option value="0">All</option>
          </select>
        </div>
      </section>
      <div class="status-line" id="status"></div>
    </header>
    <main class="grid" id="grid"></main>
    <footer>
      Source: TRER repo pressure dashboard export. Pressure, criticality, urgency, platform, documentation, dependency, velocity, and stability are separate triage signals. Age is context, not automatic risk.
    </footer>
  </div>

  <script id="repo-data" type="application/json">{safe_payload}</script>
  <script>
    const rows = JSON.parse(document.getElementById('repo-data').textContent || '[]');
    const ranks = [
      ['urgency_score', 'Urgency', '#fb7185'],
      ['pressure_score', 'Pressure', '#f6ad55'],
      ['criticality_score', 'Criticality', '#f687b3'],
      ['platform_score', 'Platform', '#c084fc'],
      ['stability_score', 'Stability', '#7ee787'],
      ['documentation_gap_score', 'Docs Gap', '#a78bfa'],
      ['dependency_density_score', 'Dependency', '#63b3ed'],
      ['change_velocity_score', 'Velocity', '#f6e05e'],
      ['days_since_last_commit', 'Stale', '#9aa8c7'],
    ];
    const scoreFields = [
      ['urgency_score', 'Urgency', '#fb7185'],
      ['pressure_score', 'Pressure', '#f6ad55'],
      ['criticality_score', 'Criticality', '#f687b3'],
      ['platform_score', 'Platform', '#c084fc'],
      ['stability_score', 'Stability', '#7ee787'],
      ['documentation_gap_score', 'Doc Gap', '#a78bfa'],
      ['dependency_density_score', 'Dep', '#63b3ed'],
      ['change_velocity_score', 'Velocity', '#f6e05e'],
    ];
    let rankField = 'urgency_score';
    let filterText = '';
    let limit = 50;

    function esc(value) {{
      return String(value ?? '').replace(/[&<>"']/g, ch => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[ch]));
    }}
    function num(value) {{
      const n = Number(value ?? 0);
      return Number.isFinite(n) ? n : 0;
    }}
    function actionClass(action) {{
      if (action === 'prioritize immediately') return 'action-prioritize';
      if (action === 'improve README') return 'action-docs';
      if (action === 'add tests') return 'action-tests';
      if (action === 'low priority') return 'action-low';
      if (action === 'archive candidate') return 'action-archive';
      return 'action-monitor';
    }}
    function cardClass(action) {{
      if (action === 'prioritize immediately') return 'priority';
      if (action === 'improve README') return 'docs';
      if (action === 'add tests') return 'tests';
      if (action === 'low priority' || action === 'archive candidate') return 'low';
      return '';
    }}
    function searchBlob(row) {{
      return [row.repo_name, row.primary_language, row.recommended_action, row.confidence, ...(row.notes || [])].join(' ').toLowerCase();
    }}
    function renderTabs() {{
      const tabs = document.getElementById('tabs');
      tabs.innerHTML = ranks.map(([field, label]) => `<button type="button" class="rank-tab ${{field === rankField ? 'active' : ''}}" data-field="${{field}}">${{label}}</button>`).join('');
      tabs.querySelectorAll('button').forEach(btn => btn.addEventListener('click', () => {{
        rankField = btn.dataset.field;
        renderTabs();
        render();
      }}));
    }}
    function scoreRow(row, field, label, color) {{
      const value = num(row[field]);
      const pct = Math.max(0, Math.min(100, Math.round(value * 100)));
      return `<div class="score"><label>${{label}}</label><div class="track"><div class="fill" style="width:${{pct}}%;background:${{color}}"></div></div><output>${{value.toFixed(3)}}</output></div>`;
    }}
    function renderCard(row) {{
      const action = row.recommended_action || 'monitor';
      const notes = (row.notes || []).slice(0, 8).map(n => `<span class="tag">${{esc(n)}}</span>`).join('');
      const url = row.repo_url || '';
      const repoName = url ? `<a href="${{esc(url)}}">${{esc(row.repo_name || 'unknown')}}</a>` : esc(row.repo_name || 'unknown');
      const age = row.days_since_last_commit != null ? `${{esc(row.days_since_last_commit)}} days ago` : esc(row.last_commit_date || 'unknown age');
      return `<article class="card ${{cardClass(action)}}">
        <div class="card-head">
          <div>
            <div class="repo-name">${{repoName}}</div>
            <div class="meta">
              ${{row.primary_language ? `<span class="tag">${{esc(row.primary_language)}}</span>` : ''}}
              <span class="tag">${{age}}</span>
              <span class="tag">confidence: ${{esc(row.confidence || 'low')}}</span>
            </div>
          </div>
          <span class="action ${{actionClass(action)}}">${{esc(action)}}</span>
        </div>
        <div class="scores">${{scoreFields.map(([field, label, color]) => scoreRow(row, field, label, color)).join('')}}</div>
        <details>
          <summary>Details</summary>
          <div class="notes">${{notes || '<span class="tag">no notes</span>'}}</div>
          <div style="margin-top:7px">Issues: ${{esc(row.issue_count ?? 0)}} · PRs: ${{esc(row.open_pr_count ?? 0)}} · Dependencies: ${{esc(row.dependency_count ?? 0)}} · Downstream: ${{esc(row.downstream_dependency_count ?? 0)}}</div>
        </details>
      </article>`;
    }}
    function render() {{
      let data = rows.slice().sort((a, b) => num(b[rankField]) - num(a[rankField]));
      if (filterText) data = data.filter(row => searchBlob(row).includes(filterText));
      const totalFiltered = data.length;
      if (limit > 0) data = data.slice(0, limit);
      document.getElementById('status').textContent = `Showing ${{data.length}} of ${{totalFiltered}} matching repos · ranked by ${{ranks.find(r => r[0] === rankField)?.[1] || rankField}}`;
      document.getElementById('grid').innerHTML = data.length ? data.map(renderCard).join('') : '<div class="empty">No repos match this filter.</div>';
    }}
    document.getElementById('search').addEventListener('input', event => {{
      filterText = event.target.value.trim().toLowerCase();
      render();
    }});
    document.getElementById('limit').addEventListener('change', event => {{
      limit = Number(event.target.value || 0);
      render();
    }});
    renderTabs();
    render();
  </script>
</body>
</html>
"""
    path.write_text(doc, encoding="utf-8")

def console_table(nodes: list[RepoPressureNode]) -> str:
    headers = ["repo", "age", "press", "crit", "urg", "plat", "vel", "stab", "arch", "docs", "dep", "action", "conf"]
    lines = [
        f"{headers[0]:28} {headers[1]:>5} {headers[2]:>6} {headers[3]:>6} {headers[4]:>6} {headers[5]:>6} {headers[6]:>6} {headers[7]:>6} {headers[8]:>6} {headers[9]:>6} {headers[10]:>6} {headers[11]:22} {headers[12]}",
        "-" * 140,
    ]
    for node in nodes:
        name = node.repo_name[:28]
        age = "?" if node.days_since_last_commit is None else str(node.days_since_last_commit)
        lines.append(
            f"{name:28} {age:>5} "
            f"{(node.pressure_score or 0):>6.3f} "
            f"{(node.criticality_score or 0):>6.3f} "
            f"{(node.urgency_score or 0):>6.3f} "
            f"{(node.platform_score or 0):>6.3f} "
            f"{(node.change_velocity_score or 0):>6.3f} "
            f"{(node.stability_score or 0):>6.3f} "
            f"{(node.architectural_importance_score or 0):>6.3f} "
            f"{(node.documentation_gap_score or 0):>6.3f} "
            f"{(node.dependency_density_score or 0):>6.3f} "
            f"{node.recommended_action[:22]:22} {node.confidence}"
        )
    return "\n".join(lines)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Private TRER/OpenClaw repo pressure dashboard.")
    parser.add_argument("repo_reports", type=Path, help="JSON list of repository pressure packets")
    parser.add_argument(
        "--rank",
        choices=["pressure", "criticality", "urgency", "velocity", "stability", "platform", "stale", "documentation", "dependency"],
        default="pressure",
    )
    parser.add_argument("--json-out", type=Path, default=None, help="Optional scored JSON export path")
    parser.add_argument("--html-out", type=Path, default=None, help="Optional self-contained HTML dashboard export path")
    parser.add_argument("--phone-html-out", type=Path, default=None, help="Alias for --html-out; writes phone-friendly standalone HTML")
    parser.add_argument(
        "--export-phone-html",
        nargs="?",
        const="__DEFAULT__",
        default=None,
        metavar="PATH",
        help="Write phone-friendly standalone HTML. If PATH is omitted, writes <input-stem>.phone.html next to the input.",
    )
    args = parser.parse_args(argv)

    ranked = rank_repos(load_repo_nodes(args.repo_reports), args.rank)
    print(console_table(ranked))
    if args.json_out:
        write_json_export(ranked, args.json_out)

    html_outputs: list[Path] = []
    for candidate in (args.html_out, args.phone_html_out):
        if candidate and candidate not in html_outputs:
            html_outputs.append(candidate)
    if args.export_phone_html:
        export_path = (
            args.repo_reports.with_name(f"{args.repo_reports.stem}.phone.html")
            if args.export_phone_html == "__DEFAULT__"
            else Path(args.export_phone_html)
        )
        if export_path not in html_outputs:
            html_outputs.append(export_path)
    for output in html_outputs:
        write_html_dashboard(ranked, output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
