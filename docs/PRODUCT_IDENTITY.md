# ROBERTA — Verified On-Chain Intelligence Product Identity

Status: **repository-authoritative product naming decision**

Effective: **2026-08-28**

## Canonical public name

The canonical public-facing product name is:

# ROBERTA — Verified On-Chain Intelligence

**ROBERTA — Verified On-Chain Intelligence** is the canonical public-facing product name used for the product, user-facing experience, public documentation, ecosystem listings, demos, and external communications.

The former working name **X1 Intelligence Service** is retired and must not be used as the current product name. This naming decision reduces confusion with similarly named X1 ecosystem products and gives Roberta an independent identity that can extend beyond one chain.

The phrase **Verified On-Chain Intelligence** is part of the canonical public-facing name, not an optional tagline.

## Architecture names that do not change

This is a product-name change, not an architecture rename.

```text
User / transport
  -> Roberta
    -> Chain Scout
      -> CMIS
        -> Chain Provider / verified source
```

The following component names remain valid:

- **Roberta** — public product, top-level coordinator, learning-workflow coordinator, and final user-facing voice.
- **X1 Scout** — X1 chain specialist.
- **Solana Scout** — Solana chain specialist.
- **CMIS** — deterministic verification, evidence, risk, historical-intelligence, and capability backend.

Repository names, package namespaces, service units, endpoints, and compatibility identifiers such as `roberta-langgraph` or `liquidity_scout` do not need to be renamed solely because of this product decision. Any technical rename requires its own migration plan.

## Naming rules

1. Use **ROBERTA — Verified On-Chain Intelligence** as the current public/product name.
2. Do not use **X1 Intelligence Service** as a current brand, product, umbrella, or front-facing service name.
3. Do not shorten the retired name to **X1 Intelligence** as a substitute product name.
4. Refer to X1 Scout, Solana Scout, and CMIS as components/specialists beneath Roberta unless a separate accepted architecture decision changes that boundary.
5. Preserve clearly historical references when they are needed to explain repository or implementation history.
6. Do not imply that a similarly named third-party or ecosystem product is Roberta, or that Roberta is that product, without an explicit accepted integration/affiliation statement.

## Scope and authority are unchanged

This naming decision does **not**:

- change the Roberta -> Chain Scout -> CMIS -> Provider authority path;
- promote a new CMIS capability;
- change evidence, Proof Score, risk, identity, or historical-data semantics;
- authorize a provider bypass;
- grant wallet, transaction, trading, custody, bridge, or execution authority;
- start Controlled Execution.

**ROBERTA — Verified On-Chain Intelligence is the public product name. X1 and other chain names describe specialist coverage, not ownership of the ROBERTA brand.**
