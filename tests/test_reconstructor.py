import json
import unittest
from pathlib import Path

from trer import reconstruct_timeline


FIXTURE_DIR = Path(__file__).parent / "fixtures"


class ReconstructorTests(unittest.TestCase):
    def test_two_observations_at_different_locations_create_movement_event(self):
        payload = json.loads((FIXTURE_DIR / "movement_basic.json").read_text())

        timeline = reconstruct_timeline(payload)

        self.assertEqual(len(timeline.entities), 1)
        self.assertEqual(timeline.entities[0].id, "entity-red-ball")
        self.assertEqual(len(timeline.events), 1)

        event = timeline.events[0]
        self.assertEqual(event.kind, "movement")
        self.assertEqual(event.entity_id, "entity-red-ball")
        self.assertEqual(event.evidence, ("obs-001", "obs-002"))
        self.assertEqual(event.attributes["from"], (10, 20))
        self.assertEqual(event.attributes["to"], (18, 24))


if __name__ == "__main__":
    unittest.main()
