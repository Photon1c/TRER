import unittest
from pathlib import Path

from trer.prisms.market.simulations import (
    BID_SPREAD_FALSE_STOP,
    BrokerStopRule,
    OptionQuoteFrame,
    Position,
    compare_stop_policies,
    default_policy_suite,
    simulate_stop_execution,
)
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
        self.assertEqual(result.stop_event.best_recovery_bid, 0.80)
        self.assertEqual(result.stop_event.recovery_pnl, 114.0)
        self.assertEqual(result.stop_event.missed_pnl, 62.0)
        self.assertEqual(result.stop_event.event_type, BID_SPREAD_FALSE_STOP)
        self.assertTrue(result.stop_event.spread_risk)
        self.assertGreater(result.stop_event.spread_pct_of_mid, 0.45)

    def test_midpoint_trigger_survives_same_quote_path(self):
        position, _, frames = load_simulation_payload(FIXTURE)
        midpoint_rule = BrokerStopRule(stop_price=0.50, trigger_field="mid", order_type="stop_market")

        result = simulate_stop_execution(position, midpoint_rule, frames)

        self.assertFalse(result.stopped)
        self.assertFalse(result.false_stop)

    def test_policy_comparison_shows_bid_stop_exits_while_thesis_policies_survive(self):
        position, stop_rule, frames = load_simulation_payload(FIXTURE)
        policies = default_policy_suite(stop_rule.stop_price, underlying_stop_price=752.00)

        comparison = compare_stop_policies(position, frames, policies)
        outcomes = {outcome.policy.name: outcome for outcome in comparison.outcomes}

        bid_stop = outcomes["Policy A: option bid stop"]
        self.assertTrue(bid_stop.stopped)
        self.assertTrue(bid_stop.false_stop)
        self.assertEqual(bid_stop.stop_event.event_type, BID_SPREAD_FALSE_STOP)
        self.assertEqual(bid_stop.stop_event.missed_pnl, 62.0)

        self.assertFalse(outcomes["Policy B: option mid stop"].stopped)
        self.assertFalse(outcomes["Policy C: underlying price invalidation"].stopped)
        self.assertFalse(outcomes["Policy D: thesis-validity stop"].stopped)
        self.assertFalse(outcomes["Policy E: bid stop AND thesis invalid"].stopped)
        self.assertEqual(outcomes["Policy D: thesis-validity stop"].terminal_pnl, 114.0)

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
