import unittest

import trer
from trer.core import Entity, Event, Hypothesis, Observation, Relationship, Timeline
from trer.core.models import Entity as CompatEntity
from trer.core.reconstructor import reconstruct_timeline as compat_reconstruct_timeline


class PublicApiTests(unittest.TestCase):
    def test_core_exports_remain_available(self):
        self.assertIs(trer.Entity, Entity)
        self.assertIs(trer.Event, Event)
        self.assertIs(trer.Hypothesis, Hypothesis)
        self.assertIs(trer.Observation, Observation)
        self.assertIs(trer.Relationship, Relationship)
        self.assertIs(trer.Timeline, Timeline)

    def test_early_compatibility_imports_remain_available(self):
        self.assertIs(CompatEntity, Entity)
        self.assertIs(compat_reconstruct_timeline, trer.reconstruct_timeline)


if __name__ == "__main__":
    unittest.main()
