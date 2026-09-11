"""Native-XNT interpretation layer for ROBERTA's Instant X1 Scan.

CMIS already verifies native XNT through ``identity_key=native:xnt`` and keeps
native account concentration separate from token-holder semantics.  This module
makes that verified identity explicit in the human/product layer so a missing
SPL-style mint is never reframed as missing evidence.

The layer does not invent supply, market, history, risk, or concentration facts.
It only marks token-contract concepts as not applicable once CMIS has verified
the canonical native-XNT identity.
"""

from __future__ import annotations

from copy import deepcopy
from functools import wraps
from types import ModuleType
from typing import Any, Mapping


NATIVE_XNT_SCAN_CONTRACT = "x1_native_asset_scan/v1"
NATIVE_XNT_OUTPUT_MARKER = "ROBERTA NATIVE XNT SEMANTICS v1"
_PATCH_MARKER = "_roberta_native_xnt_semantics_v1_applied"

_NATIVE_XNT_OUTPUT_APPENDIX = f"""

{NATIVE_XNT_OUTPUT_MARKER}
When CMIS Instant X1 Scan verifies identity_key=native:xnt for XNT:
- Treat XNT as the canonical chain-native X1 currency, not as an SPL-style token.
- A token mint address is NOT APPLICABLE, not missing. Never ask the user for an
  exact X1 mint for native XNT and never list a missing token mint under WHAT
  ROBERTA STILL NEEDS.
- Mint authority and freeze authority are NOT APPLICABLE to native XNT. Do not
  describe them as absent token-contract authorities and do not count their
  non-applicability as an evidence gap or structural token-contract positive.
- Describe the native supply/issuance section as Native Economics rather than
  generic token Tokenomics. Preserve any genuine WARN from missing native
  issuance, supply, distribution, history, or freshness evidence and explain the
  actual verified reason for that WARN.
- Token-holder count is NOT APPLICABLE. Use CMIS native-account concentration
  evidence when available; unavailable native concentration remains unknown.
- A wrapped-XNT mint used to bind an XDEX market pair or supported-pair history
  is a market representation/evidence route. It is not the identity of native
  XNT and must never be requested from the user as native XNT's mint.
- If a separate specialist contract only accepts token mints, do not ask the
  user to invent/provide a mint for native XNT. State that the token-mint-only
  specialist is not applicable until CMIS exposes a native-compatible evidence
  route.
"""


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _is_verified_native_xnt(view: Mapping[str, Any]) -> bool:
    identity = _mapping(view.get("identity"))
    return bool(
        identity.get("verified") is True
        and identity.get("identity_key") == "native:xnt"
        and str(identity.get("symbol") or "").strip().upper() == "XNT"
    )


def enrich_native_xnt_product_view(view: Mapping[str, Any]) -> dict[str, object]:
    """Add explicit N/A semantics to an already-verified native-XNT product view."""

    result: dict[str, object] = deepcopy(dict(view))
    if not _is_verified_native_xnt(result):
        return result

    identity = dict(_mapping(result.get("identity")))
    identity.update(
        {
            "canonical_id": "x1:native:XNT",
            "asset_class": "native",
            "mint": None,
            "mint_applicable": False,
            "mint_state": "not_applicable",
            "token_contract_authorities_applicable": False,
        }
    )
    result["identity"] = identity

    tokenomics = dict(_mapping(result.get("tokenomics")))
    tokenomics.update(
        {
            "section_label": "Native Economics",
            "scope": tokenomics.get("scope") or "native_network",
            "asset_type": "native",
            "mint_authority": {
                "value": None,
                "verified": True,
                "applicable": False,
                "state": "not_applicable",
            },
            "mint_authority_state": "not_applicable",
            "freeze_authority": {
                "value": None,
                "verified": True,
                "applicable": False,
                "state": "not_applicable",
            },
            "freeze_authority_state": "not_applicable",
            "token_contract_authorities_applicable": False,
        }
    )
    result["tokenomics"] = tokenomics

    holder = dict(_mapping(result.get("holder_concentration")))
    holder["holder_count_applicable"] = False
    holder["holders_state"] = "not_applicable"
    result["holder_concentration"] = holder

    risk = dict(_mapping(result.get("risk")))
    risk["native_component_label"] = "Native Economics"
    risk["tokenomics_component_semantics"] = "native_economics"
    result["risk"] = risk

    result["native_asset_scan"] = {
        "contract_version": NATIVE_XNT_SCAN_CONTRACT,
        "embedded_in": "instant_x1_scan",
        "canonical_id": "x1:native:XNT",
        "symbol": "XNT",
        "asset_class": "native",
        "token_mint_address_applicable": False,
        "token_contract_authorities_applicable": False,
        "token_holder_count_applicable": False,
        "wrapped_market_representation_is_native_identity": False,
        "execution_authorized": False,
    }
    return result


def _render_native_xnt_text(text: str) -> str:
    lines = str(text).splitlines()
    rendered: list[str] = []
    identity_detail_added = False
    representation_note_added = False

    for line in lines:
        if line == "Tokenomics":
            rendered.append("Native Economics")
            continue
        if line.startswith("Mint Authority:"):
            rendered.append(
                "Mint Authority: NOT APPLICABLE — native XNT has no token mint authority."
            )
            continue
        if line.startswith("Freeze Authority:"):
            rendered.append(
                "Freeze Authority: NOT APPLICABLE — native XNT has no token-contract freeze authority."
            )
            continue

        rendered.append(line)
        if line.startswith("Identity:") and not identity_detail_added:
            rendered.extend(
                [
                    "Asset class: native X1 currency",
                    "Canonical identity: x1:native:XNT",
                    "Token mint address: NOT APPLICABLE",
                ]
            )
            identity_detail_added = True
        if (
            line.startswith("Native XNT distribution is evaluated")
            and not representation_note_added
        ):
            rendered.append(
                "Wrapped XNT market representations are evidence routes, not native XNT identity."
            )
            representation_note_added = True

    return "\n".join(rendered)


def apply_native_xnt_product_semantics(product_module: ModuleType) -> None:
    """Patch the public product projection once, before Scout graph imports use it."""

    if getattr(product_module, _PATCH_MARKER, False):
        return

    original_build = product_module.build_instant_x1_scan_product_view
    original_render = product_module.render_instant_x1_scan_product_text

    @wraps(original_build)
    def build_with_native_semantics(report: Mapping[str, Any]):
        view = original_build(report)
        if view is None:
            return None
        return enrich_native_xnt_product_view(view)

    @wraps(original_render)
    def render_with_native_semantics(view: Mapping[str, Any]) -> str:
        enriched = enrich_native_xnt_product_view(view)
        text = original_render(enriched)
        if not _is_verified_native_xnt(enriched):
            return text
        return _render_native_xnt_text(text)

    product_module.build_instant_x1_scan_product_view = build_with_native_semantics
    product_module.render_instant_x1_scan_product_text = render_with_native_semantics
    setattr(product_module, _PATCH_MARKER, True)


def apply_native_xnt_output_contract(chat_module: ModuleType) -> None:
    """Keep the LLM/human response layer from turning native N/A into missing data."""

    current = str(getattr(chat_module, "HUMAN_ROBERTA_PRESENTATION_POLICY", ""))
    if NATIVE_XNT_OUTPUT_MARKER not in current:
        chat_module.HUMAN_ROBERTA_PRESENTATION_POLICY = (
            current + _NATIVE_XNT_OUTPUT_APPENDIX
        )

    single = str(getattr(chat_module, "SINGLE_ASSET_TERMINAL_STYLE", ""))
    if NATIVE_XNT_OUTPUT_MARKER not in single:
        chat_module.SINGLE_ASSET_TERMINAL_STYLE = (
            single + _NATIVE_XNT_OUTPUT_APPENDIX
        )


__all__ = [
    "NATIVE_XNT_OUTPUT_MARKER",
    "NATIVE_XNT_SCAN_CONTRACT",
    "apply_native_xnt_output_contract",
    "apply_native_xnt_product_semantics",
    "enrich_native_xnt_product_view",
]
