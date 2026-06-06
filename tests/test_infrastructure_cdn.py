import json
import unittest
from pathlib import Path

from trer.prisms.infrastructure.cdn import (
    CriticalDependencyNode,
    compute_pressure_mismatch_score,
    node_text_summary,
    rank_flow_first,
)


FIXTURE = Path(__file__).parent / "fixtures" / "infrastructure" / "dc_cdn_sample.json"


class CriticalDependencyNodeTests(unittest.TestCase):
    def test_pressure_score_requires_visible_dissipation_evidence(self):
        self.assertIsNone(
            compute_pressure_mismatch_score(
                static_dependency_density=0.8,
                dynamic_flow_density=0.7,
                consequence_density=0.9,
                dissipation_capacity=None,
            )
        )

    def test_pressure_score_is_unresolved_pressure_not_age_risk(self):
        score = compute_pressure_mismatch_score(
            static_dependency_density=0.9,
            dynamic_flow_density=0.85,
            consequence_density=0.95,
            dissipation_capacity=0.55,
        )
        self.assertEqual(score, 0.35)

    def test_fixture_packets_rank_by_flow_first(self):
        raw_nodes = json.loads(FIXTURE.read_text())
        nodes = [CriticalDependencyNode.from_dict(item) for item in raw_nodes]

        ranked = rank_flow_first(nodes)

        self.assertEqual(ranked[0].node_id, "dc-retail-sample-001")
        self.assertEqual(ranked[1].node_id, "dc-medical-sample-001")
        self.assertIsNone(ranked[2].pressure_mismatch_score)

    def test_packet_summary_contains_embedding_relevant_structure(self):
        node = CriticalDependencyNode.from_dict(json.loads(FIXTURE.read_text())[0])
        summary = node_text_summary(node)

        self.assertIn("Critical dependency node", summary)
        self.assertIn("Dynamic flow density", summary)
        self.assertIn("Dissipation capacity", summary)
        self.assertIn("Confidence", summary)

    def test_invalid_node_class_rejected(self):
        with self.assertRaises(ValueError):
            CriticalDependencyNode.from_dict(
                {
                    "node_id": "bad",
                    "name": "Bad packet",
                    "city": "Washington D.C.",
                    "address": "unknown",
                    "node_class": "old_building",
                }
            )


if __name__ == "__main__":
    unittest.main()
