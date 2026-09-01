import copy
import unittest

from roberta.x1_scout.burn_intelligence import (
    BURN_INTELLIGENCE_CONTRACT,
    X1BurnIntelligenceContractError,
    build_x1_burn_intelligence,
)


MINT = "7SXmUpcBGSAwW5LmtzQVF9jHswZ7xzmdKqWa4nDgL3ER"
OTHER_MINT = "So11111111111111111111111111111111111111112"


def window(label, *, burned="10", percent="25", change_state="AVAILABLE"):
    result = {
        "status": "ok",
        "window_seconds": {"1h": 3600, "24h": 86400, "7d": 604800, "30d": 2592000}[label],
        "start_exclusive": 100,
        "end_inclusive": 200,
        "coverage_verified": True,
        "burned_raw": burned,
        "burned_tokens": burned,
        "burn_events": 2,
        "minted_raw": "20",
        "minted_tokens": "20",
        "mint_events": 1,
        "burn_to_emission_ratio": "0.5",
        "net_issuance_raw": "10",
        "net_issuance_tokens": "10",
        "issuance_state": "INFLATIONARY",
    }
    if label != "1h":
        result["period_over_period"] = {
            "status": "ok",
            "prior_start_exclusive": 0,
            "prior_end_inclusive": 100,
            "prior_burned_raw": "8",
            "prior_burned_tokens": "8",
            "percent_change": percent,
            "change_state": change_state,
        }
    return result


def tokenomics_result():
    return {
        "service": "tokenomics",
        "chain": "x1",
        "status": "partial",
        "asset": {"symbol": "AGI", "name": "AGI", "mint": MINT},
        "data": {
            "mint": MINT,
            "symbol": "AGI",
            "burn_metrics": {
                "available": True,
                "status": "partial",
                "burn_events_observed": 7,
                "burned_raw_observed": "70",
                "burned_tokens_observed": "70",
                "observed_event_totals_verified": True,
                "verified_burned_raw_observed": "70",
                "verified_burned_observed": "70",
                "lifetime_total_burn_verified": False,
                "coverage_verified": True,
                "time_buckets_verified": True,
                "coverage_start_time": 0,
                "coverage_end_time": 200,
                "observed_at": 200,
                "windows": {
                    "1h": window("1h"),
                    "24h": window("24h"),
                    "7d": window("7d"),
                    "30d": window("30d"),
                },
                "valuation": {
                    "available": True,
                    "status": "partial",
                    "reason": "usd_valuation_coverage_incomplete",
                    "valuation_coverage_complete": False,
                    "native": {
                        "status": "ok",
                        "valuation_coverage_complete": True,
                        "verified_value_destroyed": "0.25",
                    },
                    "usd": {
                        "status": "partial",
                        "valuation_coverage_complete": False,
                        "verified_value_destroyed": "1.50",
                        "unvalued_burn_amount": "10",
                    },
                },
                "circulating_supply": {
                    "status": "ok",
                    "circulating_supply_verified": True,
                    "circulating_supply": "900",
                    "circulating_to_total_supply_ratio": "0.9",
                },
                "partial_reasons": ["usd_valuation_coverage_incomplete"],
            },
        },
        "risk": None,
        "confidence": {"status": "partial"},
        "sources": [{"provider": "x1_rpc"}],
        "observed_at": 200,
        "warnings": [{"code": "burn_time_valuation_incomplete"}],
        "errors": [],
        "evidence_receipt": {"receipt_id": "receipt-1"},
        "proof_score": {"state": "limited"},
    }


class X1BurnIntelligenceTests(unittest.TestCase):
    def test_projects_cmis_burn_metrics_without_recomputation(self):
        source = tokenomics_result()
        product = build_x1_burn_intelligence(source, requested_asset="AGI")

        self.assertEqual(product["contract_version"], BURN_INTELLIGENCE_CONTRACT)
        self.assertEqual(product["product"], "x1_burn_intelligence")
        self.assertEqual(product["chain"], "x1")
        self.assertEqual(product["requested_asset"], "AGI")
        self.assertEqual(product["asset"]["mint"], MINT)
        self.assertEqual(product["burn_metrics"], source["data"]["burn_metrics"])
        self.assertFalse(product["burn_metrics"]["lifetime_total_burn_verified"])
        self.assertEqual(
            product["burn_metrics"]["windows"]["7d"]["period_over_period"]["percent_change"],
            "25",
        )
        self.assertEqual(product["evidence_receipt"], source["evidence_receipt"])
        self.assertEqual(product["proof_score"], source["proof_score"])
        self.assertTrue(product["proof_score_separate_from_risk"])
        self.assertFalse(product["execution_authorized"])

    def test_projection_is_detached_from_mutable_cmis_payload(self):
        source = tokenomics_result()
        product = build_x1_burn_intelligence(source)
        source["data"]["burn_metrics"]["windows"]["24h"]["burned_raw"] = "999"
        source["warnings"].append({"code": "mutated"})

        self.assertEqual(product["burn_metrics"]["windows"]["24h"]["burned_raw"], "10")
        self.assertNotIn({"code": "mutated"}, product["warnings"])

    def test_exact_mint_identity_is_required_and_must_match_data(self):
        source = tokenomics_result()
        source["asset"]["mint"] = "AGI"
        with self.assertRaisesRegex(X1BurnIntelligenceContractError, "exact address-shaped"):
            build_x1_burn_intelligence(source)

        source = tokenomics_result()
        source["data"]["mint"] = OTHER_MINT
        with self.assertRaisesRegex(X1BurnIntelligenceContractError, "does not match"):
            build_x1_burn_intelligence(source)

    def test_new_burn_activity_preserves_null_percent_change(self):
        source = tokenomics_result()
        comparison = source["data"]["burn_metrics"]["windows"]["24h"]["period_over_period"]
        comparison["percent_change"] = None
        comparison["prior_burned_raw"] = "0"
        comparison["prior_burned_tokens"] = "0"
        comparison["change_state"] = "NEW_BURN_ACTIVITY"

        product = build_x1_burn_intelligence(source)
        projected = product["burn_metrics"]["windows"]["24h"]["period_over_period"]
        self.assertIsNone(projected["percent_change"])
        self.assertEqual(projected["change_state"], "NEW_BURN_ACTIVITY")

    def test_unavailable_comparison_preserves_insufficient_coverage(self):
        source = tokenomics_result()
        comparison = source["data"]["burn_metrics"]["windows"]["30d"]["period_over_period"]
        comparison.update({
            "status": "unavailable",
            "prior_burned_raw": None,
            "prior_burned_tokens": None,
            "percent_change": None,
            "change_state": "INSUFFICIENT_COVERAGE",
        })

        product = build_x1_burn_intelligence(source)
        projected = product["burn_metrics"]["windows"]["30d"]["period_over_period"]
        self.assertEqual(projected["status"], "unavailable")
        self.assertIsNone(projected["percent_change"])

    def test_unavailable_burn_metrics_are_preserved_without_zero_fabrication(self):
        source = tokenomics_result()
        source["status"] = "partial"
        source["data"]["burn_metrics"] = {
            "available": False,
            "status": "unavailable",
            "reason": "token_activity_not_supplied",
            "lifetime_total_burn_verified": False,
            "valuation": {"status": "unavailable"},
            "circulating_supply": {"status": "unavailable"},
        }

        product = build_x1_burn_intelligence(source)
        self.assertFalse(product["burn_metrics"]["available"])
        self.assertNotIn("verified_burned_observed", product["burn_metrics"])
        self.assertEqual(product["burn_metrics"]["reason"], "token_activity_not_supplied")

    def test_wrong_service_or_chain_fails_closed(self):
        for key, value in (("service", "market_report"), ("chain", "solana")):
            source = tokenomics_result()
            source[key] = value
            with self.subTest(key=key), self.assertRaises(X1BurnIntelligenceContractError):
                build_x1_burn_intelligence(source)

    def test_missing_burn_metrics_fails_closed(self):
        source = tokenomics_result()
        del source["data"]["burn_metrics"]
        with self.assertRaisesRegex(X1BurnIntelligenceContractError, "burn_metrics"):
            build_x1_burn_intelligence(source)

    def test_malformed_window_coverage_fails_closed(self):
        source = tokenomics_result()
        source["data"]["burn_metrics"]["windows"]["7d"]["coverage_verified"] = "yes"
        with self.assertRaisesRegex(X1BurnIntelligenceContractError, "coverage malformed"):
            build_x1_burn_intelligence(source)

    def test_numeric_percent_is_forbidden_for_new_activity_or_insufficient_coverage(self):
        for state in ("NEW_BURN_ACTIVITY", "INSUFFICIENT_COVERAGE"):
            source = tokenomics_result()
            comparison = source["data"]["burn_metrics"]["windows"]["24h"]["period_over_period"]
            comparison["change_state"] = state
            comparison["percent_change"] = "999"
            if state == "INSUFFICIENT_COVERAGE":
                comparison["status"] = "unavailable"
            with self.subTest(state=state), self.assertRaisesRegex(
                X1BurnIntelligenceContractError,
                "null percent",
            ):
                build_x1_burn_intelligence(source)

    def test_execution_authority_fails_closed(self):
        source = tokenomics_result()
        source["execution_authorized"] = True
        with self.assertRaisesRegex(X1BurnIntelligenceContractError, "execution_authorized=false"):
            build_x1_burn_intelligence(source)

    def test_projection_does_not_mutate_source(self):
        source = tokenomics_result()
        before = copy.deepcopy(source)
        build_x1_burn_intelligence(source)
        self.assertEqual(source, before)


if __name__ == "__main__":
    unittest.main()
