import json
import tempfile
import unittest
from pathlib import Path

from trer.prisms.repos.dashboard import (
    RepoPressureNode,
    compute_repo_scores,
    load_repo_nodes,
    rank_repos,
    write_html_dashboard,
    write_json_export,
)


FIXTURE = Path(__file__).parent / "fixtures" / "repos" / "repo_reports.json"


class RepoPressureDashboardTests(unittest.TestCase):
    def test_old_repo_is_not_automatically_bad(self):
        old = RepoPressureNode.from_dict(
            {
                "repo_name": "old-reference",
                "last_commit_date": "2020-01-01",
                "readme_quality_score": 0.9,
                "issue_count": 0,
                "open_pr_count": 0,
                "dependency_count": 0,
                "downstream_dependency_count": 0,
                "complexity_score": 0.1,
                "maintenance_activity_score": 0.0,
            }
        )

        scored = compute_repo_scores(old)

        self.assertLess(scored.pressure_score, 0.2)
        self.assertEqual(scored.recommended_action, "archive candidate")

    def test_platform_repos_can_rank_high_by_pressure(self):
        nodes = load_repo_nodes(FIXTURE)
        ranked = rank_repos(nodes, "pressure")

        self.assertEqual(ranked[0].repo_name, "openclaw-workspace-main")
        self.assertGreater(ranked[0].pressure_score, 0.7)
        self.assertIn(ranked[0].recommended_action, {"prioritize immediately", "monitor"})

    def test_busy_underdocumented_service_ranks_high_by_documentation_gap(self):
        nodes = load_repo_nodes(FIXTURE)
        ranked = rank_repos(nodes, "documentation")

        self.assertEqual(ranked[0].repo_name, "underdocumented-busy-service")
        self.assertGreater(ranked[0].documentation_gap_score, 0.8)
        self.assertIn(ranked[0].recommended_action, {"improve README", "add tests", "prioritize immediately", "monitor"})

    def test_dependency_rank_includes_future_dependency_importance(self):
        nodes = load_repo_nodes(FIXTURE)
        ranked = rank_repos(nodes, "dependency")

        self.assertEqual(ranked[0].repo_name, "openclaw-workspace-main")
        self.assertGreater(ranked[0].dependency_density_score, ranked[-1].dependency_density_score)

    def test_foundational_project_raises_trer_criticality_and_managed_pressure(self):
        nodes = load_repo_nodes(FIXTURE)
        ranked = rank_repos(nodes, "criticality")
        trer = next(node for node in ranked if node.repo_name == "TRER")
        old = next(node for node in ranked if node.repo_name == "old-reference-prototype")

        self.assertGreater(trer.criticality_score, old.criticality_score)
        self.assertGreater(trer.pressure_score, 0.5)
        self.assertGreater(trer.urgency_score, 0.3)
        self.assertGreaterEqual(trer.architectural_importance_score, 0.9)
        self.assertGreaterEqual(trer.consequence_density_score, 0.8)

    def test_urgency_is_pressure_times_criticality(self):
        nodes = load_repo_nodes(FIXTURE)
        ranked = rank_repos(nodes, "urgency")
        top = ranked[0]

        self.assertEqual(top.repo_name, "openclaw-workspace-main")
        self.assertAlmostEqual(top.urgency_score, round(top.pressure_score * top.criticality_score, 4))

    def test_platform_score_is_criticality_times_architecture(self):
        nodes = load_repo_nodes(FIXTURE)
        ranked = rank_repos(nodes, "platform")
        top = ranked[0]
        trer = next(node for node in ranked if node.repo_name == "TRER")

        self.assertEqual(top.repo_name, "openclaw-workspace-main")
        self.assertAlmostEqual(top.platform_score, round(top.criticality_score * top.architectural_importance_score, 4))
        self.assertGreater(trer.platform_score, 0.5)

    def test_json_and_html_exports(self):
        nodes = rank_repos(load_repo_nodes(FIXTURE), "criticality")
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            json_path = tmp_path / "dashboard.json"
            html_path = tmp_path / "dashboard.html"

            write_json_export(nodes, json_path)
            write_html_dashboard(nodes, html_path)

            exported = json.loads(json_path.read_text())
            self.assertEqual(len(exported), len(nodes))
            self.assertIn("Repo Pressure Dashboard", html_path.read_text())


if __name__ == "__main__":
    unittest.main()
