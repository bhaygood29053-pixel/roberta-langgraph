from roberta.cmis.contracts import CMISEnvelope, CMISEvidenceCompletion


def test_cmis_envelope_exposes_systemwide_evidence_completion_metadata():
    assert "evidence_completion" in CMISEnvelope.__optional_keys__
    assert CMISEvidenceCompletion.__required_keys__ == {
        "contract_version",
        "state",
        "primary_service",
        "service_status",
        "evidence_receipt_available",
        "proof_score_available",
        "receipt_freshness_checked",
        "receipt_freshness_verified",
        "verification_status",
        "unresolved_fields",
        "unknown_proof_categories",
        "missing_or_unavailable_evidence",
        "supporting_evidence_checked",
        "risk_separate_from_proof",
        "facts_recomputed",
        "risk_recomputed",
        "status_rewritten",
        "execution_authorized",
    }
