import copy
import unittest

from roberta.decision_object import (
    DECISION_OBJECT_CONTRACT,
    MACHINE_INTELLIGENCE_CONTRACT,
    build_roberta_decision_object,
    render_human_decision,
    render_machine_intelligence,
)
from roberta.x1_scout.instant_scan_product_ux import PRODUCT_VIEW_CONTRACT


MINT = "7SXmUpcBGSAwW5LmtzQVF9jHswZ7xzmdKqWa4nDgL3ER"


def verified(value):
    return {"value": value, "verified": True}


def unverified(value=None):
    return {"value": value, "verified": False}


def scan_view():
    return {
        "contract_version": PRODUCT_VIEW_CONTRACT,
        "product": "instant_x1_scan",
        "chain": "x1",
        "requested_asset": "AGI",
        "status": "partial",
        "observed_at": 1_788_200_000,
        "observed_at_iso": "2026-08-31T00:00:00Z",
        "observed_at_display": "2026-08-31 00:00 UTC",
        "identity": {
            "status": "ok",
            "verified": True,
            "symbol": "AGI",
            "name": "AGI",
            "mint": MINT,
            "resolved_by": "cmis",
            "match_quality": "exact_mint",
        },
        "market": {
            "status": "partial",
            "price_usd": verified(0.0000483),
            "liquidity_usd": verified(2062.0),
            "volume_24h_usd": verified(305.0),
            "transactions_24h": verified(250),
            "#LPs": 3,
        },
        "tokenomics": {
            "status": "partial",
            "current_total_supply": verified("1000000000"),
            "mint_authority": verified(None),
            "freeze_authority": verified(None),
            "circulating_supply": unverified(None),
            "future_minting_possible": False,
        },
        "holder_concentration": {
            "holders": verified(266),
            "holders_reported": 266,
            "holders_observed": 266,
            "holder_semantics": {"kind": "token_accounts"},
            "top_account_concentration": {
                "state": "unavailable",
                "verified": False,
                "value": None,
                "reason": "current_concentration_unverified",
            },
        },
        "history": {
            "status": "partial",
            "coverage_scope": "verified_observed_history",
            "full_asset_lifetime_verified": False,
            "continuous_coverage_verified": False,
            "metrics": {},
        },
        "risk": {
            "status": "warn",
            "recommendation": "CAUTION",
            "flags": ["thin_liquidity"],
            "reasons": ["Verified liquidity is limited."],
            "score": 42,
            "score_verified": True,
            "score_reason": None,
            "execution_authorized": False,
        },
        "evidence": {
            "proof_score_separate_from_risk": True,
            "component_statuses": {"market": "partial", "risk": "ok"},
            "component_source_count": 4,
            "evidence_context": {"proof_score": {"state": "limited"}},
        },
        "limitations": [
            "Complete asset lifetime is not verified.",
            "Current top-account concentration is unavailable.",
        ],
        "warnings": [{"code": "history_incomplete"}],
        "errors": [],
        "execution_authorized": False,
    }


class RobertaDecisionObjectTests(unittest.TestCase):
    def test_builds_canonical_object_without_recomputing_source_facts(self):
        source = scan_view()
        decision = build_roberta_decision_object(source, request_id="req-1")

        self.assertEqual(decision["contract_version"], DECISION_OBJECT_CONTRACT)
        self.assertEqual(decision["request_id"], "req-1")
        self.assertEqual(decision["chain"], "x1")
        self.assertEqual(decision["workflow"], "instant_x1_scan")
        self.assertEqual(decision["subject"]["mint"], MINT)
        self.assertTrue(decision["subject"]["identity_verified"])
        self.assertEqual(
            decision["facts"]["market"]["price_usd"],
            source["market"]["price_usd"],
        )
        self.assertEqual(
            decision["facts"]["market"]["liquidity_usd"],
            source["market"]["liquidity_usd"],
        )
        self.assertEqual(decision["risk"], source["risk"])
        self.assertEqual(decision["history"], source["history"])
        self.assertEqual(decision["evidence"], source["evidence"])
        self.assertEqual(decision["decision"]["recommendation"], "CAUTION")
        self.assertFalse(decision["decision"]["policy_applied"])
        self.assertFalse(decision["execution_authorized"])

    def test_unknowns_preserve_unverified_state_instead_of_zero_false_coercion(self):
        source = scan_view()
        source["market"]["volume_24h_usd"] = unverified(None)
        decision = build_roberta_decision_object(source)

        self.assertEqual(
            decision["facts"]["market"]["volume_24h_usd"],
            {"value": None, "verified": False},
        )
        paths = decision["unknowns"]["unverified_fact_paths"]
        self.assertIn("market.volume_24h_usd", paths)
        self.assertIn("tokenomics.circulating_supply", paths)
        self.assertIn("holder_concentration.top_account_concentration", paths)
        self.assertNotEqual(
            decision["facts"]["market"]["volume_24h_usd"]["value"],
            0,
        )

    def test_decision_object_is_detached_from_mutable_source_payload(self):
        source = scan_view()
        decision = build_roberta_decision_object(source)
        source["market"]["price_usd"]["value"] = 999
        source["risk"]["reasons"].append("mutated")
        source["limitations"].append("mutated")

        self.assertEqual(decision["facts"]["market"]["price_usd"]["value"], 0.0000483)
        self.assertEqual(decision["risk"]["reasons"], ["Verified liquidity is limited."])
        self.assertNotIn("mutated", decision["limitations"])

    def test_machine_renderer_preserves_canonical_values_and_nulls(self):
        source = scan_view()
        source["market"]["volume_24h_usd"] = unverified(None)
        decision = build_roberta_decision_object(source, request_id="req-machine")
        machine = render_machine_intelligence(decision)

        self.assertEqual(machine["schema"], MACHINE_INTELLIGENCE_CONTRACT)
        self.assertEqual(machine["request_id"], "req-machine")
        self.assertEqual(machine["subject"]["mint"], MINT)
        self.assertEqual(
            machine["facts"]["market"]["price_usd"],
            decision["facts"]["market"]["price_usd"],
        )
        self.assertIsNone(machine["facts"]["market"]["volume_24h_usd"]["value"])
        self.assertFalse(machine["facts"]["market"]["volume_24h_usd"]["verified"])
        self.assertEqual(machine["risk"], decision["risk"])
        self.assertEqual(machine["history"], decision["history"])
        self.assertEqual(machine["observed_at"], decision["observed_at"])
        self.assertEqual(machine["execution"], {"authorized": False})
        self.assertNotIn("source_contract", machine)

        full = render_machine_intelligence(decision, evidence_depth="full")
        self.assertEqual(full["source_contract"], PRODUCT_VIEW_CONTRACT)

    def test_human_renderer_is_answer_first_and_keeps_material_uncertainty(self):
        source = scan_view()
        source["market"]["volume_24h_usd"] = unverified(None)
        decision = build_roberta_decision_object(source)
        human = render_human_decision(decision)

        self.assertIn("ROBERTA — AGI", human)
        self.assertIn("Conclusion: CAUTION", human)
        self.assertIn("Price USD: 4.83e-05", human)
        self.assertIn("Liquidity USD: 2062.0", human)
        self.assertIn("24h Volume USD: unknown", human)
        self.assertIn("Risk score: 42", human)
        self.assertIn("Unverified: market.volume_24h_usd", human)
        self.assertIn("Complete asset lifetime is not verified.", human)
        self.assertIn("Execution authorized: false", human)

    def test_human_and_machine_renderers_share_same_canonical_basis(self):
        decision = build_roberta_decision_object(scan_view())
        before = copy.deepcopy(decision)
        human = render_human_decision(decision)
        machine = render_machine_intelligence(decision)

        self.assertEqual(decision, before)
        self.assertIn(str(decision["facts"]["market"]["liquidity_usd"]["value"]), human)
        self.assertEqual(
            machine["facts"]["market"]["liquidity_usd"],
            decision["facts"]["market"]["liquidity_usd"],
        )
        self.assertEqual(machine["decision"], decision["decision"])
        self.assertEqual(machine["risk"], decision["risk"])
        self.assertEqual(machine["observed_at"], decision["observed_at"])

    def test_wrong_source_contract_fails_closed(self):
        source = scan_view()
        source["contract_version"] = "other/v1"
        with self.assertRaisesRegex(ValueError, "accepted Instant X1 Scan"):
            build_roberta_decision_object(source)

    def test_wrong_chain_or_product_fails_closed(self):
        for key, value in (("chain", "solana"), ("product", "other")):
            source = scan_view()
            source[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                build_roberta_decision_object(source)

    def test_execution_authority_fails_closed_at_source_and_risk_boundaries(self):
        source = scan_view()
        source["execution_authorized"] = True
        with self.assertRaisesRegex(ValueError, "execution_authorized=false"):
            build_roberta_decision_object(source)

        source = scan_view()
        source["risk"]["execution_authorized"] = True
        with self.assertRaisesRegex(ValueError, "risk must preserve"):
            build_roberta_decision_object(source)

    def test_proof_risk_collapse_fails_closed(self):
        source = scan_view()
        source["evidence"]["proof_score_separate_from_risk"] = False
        with self.assertRaisesRegex(ValueError, "Proof Score separate"):
            build_roberta_decision_object(source)

    def test_malformed_required_sections_fail_closed(self):
        source = scan_view()
        source["history"] = None
        with self.assertRaisesRegex(ValueError, "history"):
            build_roberta_decision_object(source)

        source = scan_view()
        source["limitations"] = "none"
        with self.assertRaisesRegex(ValueError, "limitations"):
            build_roberta_decision_object(source)

    def test_renderers_reject_tampered_execution_authority(self):
        decision = build_roberta_decision_object(scan_view())
        decision["execution_authorized"] = True
        with self.assertRaisesRegex(ValueError, "execution_authorized=false"):
            render_human_decision(decision)
        with self.assertRaisesRegex(ValueError, "execution_authorized=false"):
            render_machine_intelligence(decision)

    def test_machine_evidence_depth_is_versioned_and_bounded(self):
        decision = build_roberta_decision_object(scan_view())
        with self.assertRaisesRegex(ValueError, "evidence depth"):
            render_machine_intelligence(decision, evidence_depth="secret")


if __name__ == "__main__":
    unittest.main()
