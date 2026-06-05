import unittest
from pathlib import Path

from trer.prisms.market.simulations import BrokerStopRule, OptionQuoteFrame, Position, simulate_stop_execution
from trer.prisms.market.simulations.execution_decoupling import load_simulation_payload


FIXTURE = Path(__file__).parent / "fixtures" / "market" / "spy_put_execution_decoupling.json"


class ExecutionDecouplingTests(unittest.TestCase):
    def test_bid_trigger_can_create_false_stop_while_thesis_remains_valid(self):
        position, stop_rule, frames = load_simulation_payload(FIXTURE)

        result = simulate_stop_execution(position, stop_rule, frames)

        self.assertTrue(result.stopped)
        self.assertTrue(result.false_stop)
        self.assertIsNotNone(result.stop_event)
        self.assertEqual(result.stop_event.timestamp, "2026-06-05T10:02:00-07:00")
        self.assertEqual(result.stop_event.trigger_value, 0.49)
        self.assertEqual(result.stop_event.fill_price, 0.49)
        self.assertEqual(result.stop_event.realized_pnl, 52.0)
        self.assertGreater(result.stop_event.spread_pct_of_mid, 0.45)

    def test_midpoint_trigger_survives_same_quote_path(self):
        position, _, frames = load_simulation_payload(FIXTURE)
        midpoint_rule = BrokerStopRule(stop_price=0.50, trigger_field="mid", order_type="stop_market")

        result = simulate_stop_execution(position, midpoint_rule, frames)

        self.assertFalse(result.stopped)
        self.assertFalse(result.false_stop)

    def test_same_nickel_spread_distorts_cheap_contract_more(self):
        cheap = OptionQuoteFrame(
            timestamp="t1",
            underlying_price=750,
            bid=0.20,
            ask=0.25,
            thesis_valid=True,
        )
        expensive = OptionQuoteFrame(
            timestamp="t1",
            underlying_price=750,
            bid=5.00,
            ask=5.05,
            thesis_valid=True,
        )

        self.assertGreater(cheap.spread_pct_of_mid, expensive.spread_pct_of_mid * 20)

    def test_stop_limit_may_trigger_without_fill_when_bid_is_below_limit(self):
        position = Position(symbol="SPY put contract", option_type="put", entry_price=0.23)
        rule = BrokerStopRule(stop_price=0.50, trigger_field="bid", order_type="stop_limit", limit_price=0.50)
        frames = [
            OptionQuoteFrame(
                timestamp="2026-06-05T10:02:00-07:00",
                underlying_price=750.80,
                bid=0.49,
                ask=0.80,
                thesis_valid=True,
            )
        ]

        result = simulate_stop_execution(position, rule, frames)

        self.assertTrue(result.stopped)
        self.assertTrue(result.false_stop)
        self.assertIsNone(result.stop_event.fill_price)
        self.assertIsNone(result.stop_event.realized_pnl)


if __name__ == "__main__":
    unittest.main()
