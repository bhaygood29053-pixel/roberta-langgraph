from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .pyramid import Exercise


CURRICULUM_ID = "mastering_blockchain_4e_2023_book01"
SOURCE_KEY = "mastering_blockchain_4e_2023"
LEVEL = 4
RUBRIC_ID = "MB4E-L4-RUBRIC-V1"
ORDINARY_VARIANTS_PER_TARGET = 13
INTEGRITY_COUNT = 50


@dataclass(frozen=True, slots=True)
class Level4Target:
    concept: str
    subconcept: str
    principle: str
    source_ref: str
    chapter: str
    section: str
    pdf_pages: tuple[int, ...]
    required_points: tuple[str, ...]
    forbidden_inferences: tuple[str, ...] = ()


QUESTION_TEMPLATES: tuple[str, ...] = (
    "Explain the source-supported cryptographic rule for {label}.",
    "What does the book establish about {label}?",
    "Give a precise technical explanation of {label}.",
    "A learner is confused about {label}. What should Roberta explain?",
    "State the key security mechanism involved in {label}.",
    "How should {label} be described without adding unsupported assumptions?",
    "What source-supported point must an answer about {label} include?",
    "Correct a vague explanation of {label} using the book's cryptography model.",
    "What would a correct operational summary of {label} say?",
    "Apply the book's explanation of {label} to a generic blockchain security scenario.",
    "What distinction is essential when reasoning about {label}?",
    "If auditing an answer about {label}, what core cryptographic point must be present?",
    "What conclusion about {label} follows from the source material?",
)


def _pages(start: int, end: int) -> tuple[int, ...]:
    return tuple(range(start, end + 1))


CH3_SERVICES = "MB4E-CH3-P85-87-CRYPTO-SERVICES"
CH3_HASHES = "MB4E-CH3-P88-100-RANDOMNESS-HASHES"
CH3_SYMMETRIC = "MB4E-CH3-P100-106-SYMMETRIC-MAC-MODES"
CH3_AES = "MB4E-CH3-P107-110-AES"
CH4_PUBLIC_KEY = "MB4E-CH4-P112-120-PUBLIC-KEY-RSA"
CH4_ECC = "MB4E-CH4-P120-130-ECC"
CH4_SIGNATURES = "MB4E-CH4-P131-142-DIGITAL-SIGNATURES"
CH4_ADVANCED = "MB4E-CH4-P142-151-ADVANCED-CRYPTO"
CH18_PRIVACY = "MB4E-CH18-P616-620-PRIVACY-FOUNDATIONS"
CH18_TECHNIQUES = "MB4E-CH18-P619-627-PRIVACY-TECHNIQUES"
CH18_ZK = "MB4E-CH18-P628-649-COMMITMENTS-ZK"


def level4_source_map() -> dict[str, dict[str, object]]:
    return {
        CH3_SERVICES: {
            "chapter": "Chapter 3",
            "section": "Cryptographic services and primitive taxonomy",
            "pdf_pages": _pages(85, 87),
        },
        CH3_HASHES: {
            "chapter": "Chapter 3",
            "section": "Randomness, hash functions, security properties, and blockchain uses",
            "pdf_pages": _pages(88, 100),
        },
        CH3_SYMMETRIC: {
            "chapter": "Chapter 3",
            "section": "Symmetric keys, KDFs, MAC/HMAC, stream and block ciphers, and modes",
            "pdf_pages": _pages(100, 106),
        },
        CH3_AES: {
            "chapter": "Chapter 3",
            "section": "AES design, rounds, modes, and blockchain wallet examples",
            "pdf_pages": _pages(107, 110),
        },
        CH4_PUBLIC_KEY: {
            "chapter": "Chapter 4",
            "section": "Public/private keys, asymmetric cryptography, hybrid encryption, and RSA",
            "pdf_pages": _pages(112, 120),
        },
        CH4_ECC: {
            "chapter": "Chapter 4",
            "section": "Elliptic curve cryptography and secp256k1 key generation",
            "pdf_pages": _pages(120, 130),
        },
        CH4_SIGNATURES: {
            "chapter": "Chapter 4",
            "section": "Digital signatures, ECDSA, multisignatures, threshold, aggregate, and ring signatures",
            "pdf_pages": _pages(131, 142),
        },
        CH4_ADVANCED: {
            "chapter": "Chapter 4",
            "section": "Homomorphic encryption, secret sharing, commitments, ZKPs, SNARKs, STARKs, range proofs, and VRFs",
            "pdf_pages": _pages(142, 151),
        },
        CH18_PRIVACY: {
            "chapter": "Chapter 18",
            "section": "Blockchain privacy, anonymity, confidentiality, and public-verifiability tension",
            "pdf_pages": _pages(616, 620),
        },
        CH18_TECHNIQUES: {
            "chapter": "Chapter 18",
            "section": "Network, encryption, multiparty, mixing, confidential-transaction, and anonymous-signature privacy techniques",
            "pdf_pages": _pages(619, 627),
        },
        CH18_ZK: {
            "chapter": "Chapter 18",
            "section": "Cryptographic commitments, Pedersen commitments, range proofs, and zero-knowledge systems",
            "pdf_pages": _pages(628, 649),
        },
    }


def _target(
    concept: str,
    subconcept: str,
    principle: str,
    source_ref: str,
    *required_points: str,
    forbidden: Sequence[str] = (),
) -> Level4Target:
    source = level4_source_map()[source_ref]
    return Level4Target(
        concept=concept,
        subconcept=subconcept,
        principle=principle,
        source_ref=source_ref,
        chapter=str(source["chapter"]),
        section=str(source["section"]),
        pdf_pages=tuple(int(page) for page in source["pdf_pages"]),
        required_points=tuple(required_points) or (principle,),
        forbidden_inferences=tuple(forbidden),
    )


def level4_targets() -> tuple[Level4Target, ...]:
    return (
        _target("crypto_foundations", "security_services", "Cryptography is a building block that can provide confidentiality, integrity, authentication, non-repudiation, and accountability when combined with appropriate protocols and system controls.", CH3_SERVICES, "Distinguish the security services rather than treating cryptography as encryption only.", "Cryptography is a component of a wider security system."),
        _target("crypto_foundations", "primitive_taxonomy", "The source groups cryptographic building blocks into keyless, symmetric-key, and asymmetric-key primitives; a security protocol combines suitable primitives to achieve its security goals.", CH3_SERVICES, "Name the three primitive categories.", "Connect primitives to protocol-level security goals."),
        _target("randomness_hashes", "rng_vs_prng", "Cryptographic protocols need sufficiently unpredictable randomness; RNGs draw on physical sources while PRNGs deterministically expand a seed into random-looking output and are commonly used for key generation.", CH3_HASHES, "RNG and PRNG sources differ.", "A PRNG is deterministic from its seed but must still be suitable for cryptographic use."),
        _target("randomness_hashes", "hash_function_role", "A cryptographic hash maps arbitrary-length input to a fixed-length digest, is efficiently computable, and is used as a one-way integrity primitive and as a component of MACs, digital signatures, and blockchain structures such as Merkle trees.", CH3_HASHES, "Hash output is fixed length for arbitrary-length input.", "Hashes support integrity and construction of other primitives."),
        _target("randomness_hashes", "hash_security_properties", "Pre-image resistance makes inversion computationally infeasible, second-preimage resistance makes finding a different input matching a given input's digest infeasible, and collision resistance makes finding any two distinct inputs with the same digest infeasible.", CH3_HASHES, "Keep pre-image, second-preimage, and collision resistance distinct.", forbidden=("Do not claim collisions are mathematically impossible.",)),
        _target("randomness_hashes", "avalanche_and_collisions", "A secure cryptographic hash should make discovered collisions computationally impractical and exhibit an avalanche effect in which a small input change produces a substantially different digest.", CH3_HASHES, "Collisions can exist in a finite digest space but should be impractical to find.", "Avalanche behavior changes the output substantially after small input changes."),
        _target("symmetric_crypto", "shared_key_model", "Symmetric cryptography uses the same shared secret key for encryption and decryption, so the key must be established securely before protected communication.", CH3_SYMMETRIC, "The encryption and decryption key is shared.", "Secure key establishment is a prerequisite."),
        _target("symmetric_crypto", "key_types_and_derivation", "Keys may be random, password-derived through a KDF, or established through a key-agreement protocol; ephemeral keys are short-lived, static keys are long-lived, and master keys protect or derive other keys.", CH3_SYMMETRIC, "Distinguish random generation, KDF derivation, and agreement.", "Distinguish ephemeral, static, and master-key roles."),
        _target("symmetric_crypto", "nonce_iv_salt", "A nonce is a value intended for one-time use, an IV is an initialization value whose unpredictability matters for applicable encryption modes, and a salt is random input used with hashing or password derivation to frustrate precomputed dictionary or rainbow attacks.", CH3_SYMMETRIC, "Nonce, IV, and salt have different purposes.", forbidden=("Do not treat nonce, IV, and salt as interchangeable labels.",)),
        _target("symmetric_crypto", "mac_hmac", "MACs and HMACs use a shared key to provide message integrity and data-origin authentication; unlike public-key digital signatures, their symmetric nature does not provide the same non-repudiation property.", CH3_SYMMETRIC, "MAC/HMAC uses a shared secret.", "MACs provide integrity and origin authentication.", "Do not equate symmetric MAC verification with public non-repudiation."),
        _target("symmetric_crypto", "stream_vs_block", "Stream ciphers apply a keystream to data progressively, while block ciphers process fixed-size blocks; the security of stream ciphers depends critically on the keystream, while block ciphers use repeated substitution/permutation or related round structures.", CH3_SYMMETRIC, "Distinguish progressive keystream operation from fixed-size block processing."),
        _target("symmetric_crypto", "ecb_cbc_ctr", "ECB encrypts blocks independently and can reveal patterns, CBC chains blocks and uses an IV for the first block, and CTR combines a nonce and counter to generate a keystream from a block cipher.", CH3_SYMMETRIC, "ECB, CBC, and CTR have different chaining/state behavior.", forbidden=("Do not recommend ECB for sensitive repeated-pattern data.",)),
        _target("symmetric_crypto", "aes_design", "AES uses a 128-bit block size with 128-, 192-, or 256-bit keys and applies repeated rounds built from AddRoundKey, SubBytes, ShiftRows, and MixColumns, with the final round omitting MixColumns.", CH3_AES, "AES block size is 128 bits.", "Key sizes determine 10, 12, or 14 rounds.", "Identify the four core round transformations."),
        _target("public_key_crypto", "public_private_keys", "Asymmetric cryptography uses a public/private key pair: public keys can be distributed, private keys must remain secret, and the pair supports encryption/decryption, signatures, identification, and key establishment depending on the scheme.", CH4_PUBLIC_KEY, "Public and private keys have different disclosure requirements.", "Private-key compromise breaks the security assumption."),
        _target("public_key_crypto", "hybrid_encryption", "Public-key algorithms are computationally heavier than symmetric ciphers, so hybrid schemes commonly use public-key mechanisms to establish or encapsulate a key and symmetric encryption for bulk data.", CH4_PUBLIC_KEY, "Explain the efficiency/convenience tradeoff.", "Hybrid encryption combines public-key key establishment with symmetric data encryption."),
        _target("public_key_crypto", "rsa_hardness", "RSA relies on the practical difficulty of factoring a modulus formed from large primes; the public key can be shared while the private key depends on secret information derived from the prime factors.", CH4_PUBLIC_KEY, "RSA security is tied to integer factorization hardness.", "Public disclosure must not reveal the secret prime factors/private key."),
        _target("public_key_crypto", "ecc_hardness_efficiency", "ECC is based on the elliptic-curve discrete logarithm problem over finite fields and can provide comparable security with much smaller keys than RSA, which is valuable in blockchain systems with space and performance constraints.", CH4_ECC, "ECC relies on an elliptic-curve discrete-log hardness assumption.", "Smaller ECC keys can provide comparable security strength to much larger RSA keys."),
        _target("digital_signatures", "sign_and_verify", "Digital signatures bind a message to a signer: a digest is signed with the private key and the corresponding public key is used to verify authenticity and integrity, supporting non-repudiation when the key and identity assumptions hold.", CH4_SIGNATURES, "Signing uses the private key and verification uses the corresponding public key.", "Hashing the message is part of the secure signing construction described by the source."),
        _target("digital_signatures", "ecdsa_ephemeral_key", "ECDSA derives signatures from elliptic-curve keys and a per-signature ephemeral secret; reusing that ephemeral value across signatures can expose the private key, so it must be fresh and suitably random.", CH4_SIGNATURES, "ECDSA requires a per-signature ephemeral value.", forbidden=("Do not imply the same ephemeral signing value can be safely reused.",)),
        _target("digital_signatures", "multi_threshold_aggregate_ring", "Multisignatures retain multiple signer signatures, threshold signatures use shares to produce one verifiable signature from an authorized subset, aggregate signatures compress multiple signatures, and ring signatures hide which member of a group actually signed.", CH4_SIGNATURES, "Keep multisignature, threshold, aggregate, and ring-signature mechanics distinct."),
        _target("advanced_crypto", "homomorphic_and_secret_sharing", "Homomorphic encryption allows selected computations on encrypted data without first decrypting it, while secret sharing splits a secret into shares so an authorized set can reconstruct it without any one share revealing the secret by itself.", CH4_ADVANCED, "Homomorphic encryption operates on ciphertext.", "Secret sharing distributes reconstruction capability across shares."),
        _target("advanced_crypto", "commitment_hiding_binding", "A cryptographic commitment lets a party commit to a value without revealing it and later open it; hiding prevents premature disclosure while binding prevents changing the committed value after commitment.", CH4_ADVANCED, "A commitment has commit and open/unveil phases.", "Hiding and binding solve different security problems."),
        _target("advanced_crypto", "zkp_properties", "A zero-knowledge proof allows a prover to convince a verifier that a statement is valid without revealing the underlying secret; the source identifies completeness, soundness, and zero-knowledge as the essential properties.", CH4_ADVANCED, "Completeness, soundness, and zero-knowledge must all be distinguished.", "The proof conveys validity without revealing the witness/secret itself."),
        _target("advanced_crypto", "snark_stark_range", "zk-SNARKs emphasize succinct non-interactive proofs but traditionally require trusted setup, while zk-STARKs avoid trusted setup and use transparent/hash-based techniques at the cost of larger proofs; range proofs establish that a hidden value lies within a permitted range.", CH4_ADVANCED, "Contrast trusted setup and proof-size tradeoffs.", "Explain the purpose of a zero-knowledge range proof."),
        _target("blockchain_privacy", "anonymity_vs_confidentiality", "The source separates anonymity from confidentiality: anonymity hides participant identity or linkability, while confidentiality hides transaction information such as values; blockchain transparency creates tension because data must remain verifiable while privacy is preserved.", CH18_PRIVACY, "Distinguish identity privacy from data/value privacy.", "Public verifiability must not simply be discarded."),
        _target("blockchain_privacy", "privacy_technique_layers", "Blockchain privacy techniques can operate at network, on-chain, or off-chain layers and include anonymous routing, homomorphic encryption, secure multiparty computation, trusted execution, mixing, confidential transactions, and anonymous signatures; each protects different metadata or data surfaces.", CH18_TECHNIQUES, "Privacy mechanisms act at different layers and protect different information."),
        _target("blockchain_privacy", "confidential_transactions", "Confidential transactions use commitments, notably Pedersen commitments, to hide transferred values while retaining binding and hiding properties; their homomorphic behavior helps support verification over committed values without revealing the values themselves.", CH18_TECHNIQUES, "Pedersen commitments provide hiding and binding properties.", "Committed values can participate in useful algebraic verification without plaintext disclosure."),
        _target("blockchain_privacy", "commitments_and_range_proofs", "For private value transfers, a commitment can hide the amount but must be paired with proof constraints such as range proofs so hidden values can still be shown to satisfy validity rules without revealing the amount.", CH18_ZK, "A value commitment hides the amount.", "A range proof establishes an allowed range such as non-negativity without revealing the value."),
    )


ORDINARY_COUNT = len(level4_targets()) * ORDINARY_VARIANTS_PER_TARGET
TOTAL_COUNT = ORDINARY_COUNT + INTEGRITY_COUNT + 1


def _label(target: Level4Target) -> str:
    return f"{target.concept.replace('_', ' ')} / {target.subconcept.replace('_', ' ')}"


def build_level4_bank(curriculum_id: str = CURRICULUM_ID) -> tuple[Exercise, ...]:
    exercises: list[Exercise] = []
    sequence = 1
    targets = level4_targets()

    for target in targets:
        for template in QUESTION_TEMPLATES:
            exercises.append(
                Exercise(
                    exercise_id=f"MB4E-L04-{sequence:05d}",
                    curriculum_id=curriculum_id,
                    level=LEVEL,
                    concept=target.concept,
                    subconcept=target.subconcept,
                    question=template.format(label=_label(target)),
                    expected_answer=target.principle,
                    source_refs=(SOURCE_KEY, target.source_ref),
                    question_type="application",
                    difficulty=4,
                    required_reasoning_points=target.required_points,
                    forbidden_inferences=target.forbidden_inferences,
                    grading_rubric_id=RUBRIC_ID,
                )
            )
            sequence += 1

    for index in range(INTEGRITY_COUNT):
        target = targets[index % len(targets)]
        question = (
            f"Integrity check: State the source-supported cryptographic rule for {_label(target)} and reject any claim that confuses its security property, key role, or privacy guarantee."
            if index % 2 == 0
            else f"Integrity check: An analyst overstates {_label(target)}. Give the precise source-grounded correction without inventing stronger cryptographic guarantees than the book supports."
        )
        exercises.append(
            Exercise(
                exercise_id=f"MB4E-L04-{sequence:05d}",
                curriculum_id=curriculum_id,
                level=LEVEL,
                concept=target.concept,
                subconcept=target.subconcept,
                question=question,
                expected_answer=target.principle,
                source_refs=(SOURCE_KEY, target.source_ref),
                question_type="integrity",
                difficulty=4,
                required_reasoning_points=target.required_points,
                forbidden_inferences=target.forbidden_inferences,
                grading_rubric_id=RUBRIC_ID,
                integrity_question=True,
            )
        )
        sequence += 1

    boss_refs = (
        SOURCE_KEY,
        CH3_SERVICES,
        CH3_HASHES,
        CH3_SYMMETRIC,
        CH3_AES,
        CH4_PUBLIC_KEY,
        CH4_ECC,
        CH4_SIGNATURES,
        CH4_ADVANCED,
        CH18_PRIVACY,
        CH18_TECHNIQUES,
        CH18_ZK,
    )
    exercises.append(
        Exercise(
            exercise_id=f"MB4E-L04-{sequence:05d}",
            curriculum_id=curriculum_id,
            level=LEVEL,
            concept="cryptography",
            subconcept="boss_synthesis",
            question=(
                "Boss: Design a source-grounded cryptographic explanation for a blockchain system that must protect keys, authenticate transactions, preserve data integrity, encrypt sensitive data, and selectively hide transaction values while keeping them verifiable. "
                "Choose and distinguish hashes, symmetric encryption, public-key cryptography, digital signatures, commitments, and zero-knowledge techniques, and state the limits of each rather than treating cryptography as one interchangeable mechanism."
            ),
            expected_answer=(
                "Use cryptographic hashes for fixed-length integrity commitments and as building blocks, while preserving the distinctions among pre-image, second-preimage, and collision resistance. "
                "Use symmetric encryption such as AES for efficient confidentiality when a shared key has been securely established; nonce, IV, salt, and MAC roles must remain distinct. "
                "Use public/private key cryptography for key establishment or public-key operations, and digital signatures for sender authentication, integrity, and non-repudiation assumptions; private keys must remain secret and ECDSA ephemeral values must not be reused. "
                "For privacy-preserving blockchain values, commitments hide a value while binding the committer, and range/zero-knowledge proofs can establish validity properties without exposing the hidden value. "
                "Anonymity and confidentiality are separate goals, and no single primitive automatically provides every security or privacy property."
            ),
            source_refs=boss_refs,
            question_type="boss",
            difficulty=4,
            required_reasoning_points=(
                "Explain the distinct integrity role and security properties of cryptographic hashes.",
                "Explain symmetric encryption and the separate roles of keys, nonce/IV/salt, and MACs.",
                "Explain public/private key roles and digital-signature verification without exposing private keys.",
                "Explain hiding/binding commitments and how zero-knowledge or range proofs preserve verifiability of hidden values.",
                "Keep anonymity, confidentiality, integrity, authentication, and non-repudiation distinct.",
            ),
            forbidden_inferences=(
                "Do not claim hashing encrypts data or provides confidentiality by itself.",
                "Do not claim symmetric MACs provide the same public non-repudiation property as digital signatures.",
                "Do not claim zero-knowledge means no verification occurs.",
                "Do not claim cryptographic privacy removes the need for key management or protocol-level validation.",
            ),
            grading_rubric_id=RUBRIC_ID,
            boss_question=True,
        )
    )

    if len(exercises) != TOTAL_COUNT:
        raise AssertionError(f"total Level-4 bank count drifted: {len(exercises)}")
    if sum(item.integrity_question for item in exercises) != INTEGRITY_COUNT:
        raise AssertionError("Level-4 integrity count drifted")
    if sum(item.boss_question for item in exercises) != 1:
        raise AssertionError("Level-4 Boss count drifted")
    if len({item.exercise_id for item in exercises}) != TOTAL_COUNT:
        raise AssertionError("Level-4 exercise IDs are not unique")
    return tuple(exercises)


def level4_provenance_records(
    exercises: Sequence[Exercise], *, source_key: str = SOURCE_KEY
) -> tuple[dict[str, object], ...]:
    if source_key != SOURCE_KEY:
        raise ValueError(f"Level-4 provenance source_key must be canonical {SOURCE_KEY!r}")
    targets = {(item.concept, item.subconcept): item for item in level4_targets()}
    source_map = level4_source_map()
    records: list[dict[str, object]] = []
    for exercise in exercises:
        locations = []
        for source_ref in exercise.source_refs:
            if source_ref == SOURCE_KEY:
                continue
            raw = source_map[source_ref]
            locations.append(
                {
                    "chapter": raw["chapter"],
                    "section": raw["section"],
                    "pdf_pages": list(raw["pdf_pages"]),
                    "legacy_source_ref": source_ref,
                }
            )
        if not exercise.boss_question:
            target = targets.get((exercise.concept, exercise.subconcept))
            if target is None or exercise.source_refs != (SOURCE_KEY, target.source_ref):
                raise AssertionError(f"Level-4 provenance target mismatch: {exercise.exercise_id}")
        records.append(
            {
                "exercise_id": exercise.exercise_id,
                "source_key": SOURCE_KEY,
                "supports": ["question", "expected_answer", "required_reasoning_points"],
                "locations": locations,
            }
        )
    return tuple(records)
