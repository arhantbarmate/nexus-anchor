"""
anchorAnchor Canonical Receipt Verifier
Production-Grade Implementation

This is the "law of physics" that enforces network sovereignty.
Even if firmware leaks, middleware compromised, or attacker knows the protocol,
they CANNOT anchor to chain without passing these checks.

CANONICAL INVARIANTS ENFORCED:
1. Identity Allowlist      - Only authorized hardware can submit
2. Monotonic Counter       - No replay attacks possible
3. Firmware Governance     - Only approved firmware versions run
4. Receipt Reconstruction  - Cryptographic integrity verification

INVARIANT 5 (OUT OF SCOPE):
The Canonical Verifier does NOT interpret execution semantics.
It treats execution_hash as OPAQUE APPLICATION DATA.
Correctness of execution_hash is enforced at higher layers or by
application-specific logic. The verifier only ensures:
- It was bound to this specific receipt
- It cannot be replayed
- It came from authorized hardware running approved firmware

This separation of concerns is intentional and keeps the verifier minimal,
auditable, and defensible.
"""

import json
from eth_hash.auto import keccak  # Ethereum Keccak-256
from dataclasses import dataclass
from typing import Dict, Set, Tuple

# ============================================================================
# PROTOCOL CONSTANTS (IMMUTABLE - FROZEN)
# ============================================================================
# Domain tags are IMMUTABLE protocol constants.
# Changing them constitutes a HARD FORK.
# These must match firmware implementation exactly.
anchor_RCT_DOMAIN = b"anchor_RCT_V1"  # Receipt digest domain
anchor_HWI_DOMAIN = b"anchor_OHR_V1"  # Hardware identity domain (for reference)


@dataclass
class Receipt:
    """Parsed receipt structure from ESP32 OHR node"""

    hardware_identity: bytes  # 32 bytes - Device fingerprint
    firmware_hash: bytes  # 32 bytes - Firmware version binding
    execution_hash: bytes  # 32 bytes - Computation result
    counter: int  # 8 bytes BE - Replay protection
    receipt_digest: bytes  # 32 bytes - Claimed digest (to verify)


class anchorVerifier:
    """
    Canonical Receipt Verifier - Enforces Network Sovereignty

    Four Non-Negotiable Invariants:
    1. Identity Allowlist     - Only authorized hardware
    2. Monotonic Counter      - No replay attacks
    3. Firmware Governance    - Only approved firmware
    4. Receipt Reconstruction - Cryptographic integrity
    """

    def __init__(self):
        # 1. Sovereign Node Allowlist (Hardware Identity Registry)
        # In production: Load from secure database
        self.authorized_nodes: Dict[bytes, str] = {
            bytes.fromhex(
                "52fdfc072182654f163f5f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f"
            ): "Alpha_Node_S3",
            # Add your ESP32-S3 hardware identities here
        }

        # 2. Replay Protection State (Counter Database)
        # ⚠️ CRITICAL PRODUCTION REQUIREMENT:
        # In production, counter_db MUST be backed by persistent, crash-safe
        # storage (PostgreSQL, Redis with AOF, SQLite with WAL, etc.) to
        # preserve replay protection guarantees across verifier restarts.
        # Without persistence, a restarted verifier could accept replays.
        #
        # Deployment Invariant:
        # "Replay protection is enforced per verifier instance. Counter state
        # MUST be persisted atomically to maintain security guarantees."
        self.counter_db: Dict[bytes, int] = {}

        # 3. Governance-Approved Firmware Hashes
        # In production: On-chain governance or secure registry
        self.approved_firmware: Set[bytes] = {
            bytes.fromhex(
                "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
            ),
            # Add your approved firmware hashes here
        }

    # ========================================================================
    # CORE VERIFIER - THE LAW OF anchor
    # ========================================================================

    def verify_attestation(self, json_blob: str) -> Tuple[bool, str]:
        """
        Canonical verification flow - ALL checks must pass

        Args:
            json_blob: JSON receipt from ESP32 OHR node

        Returns:
            (success: bool, message: str)

        Raises:
            Exception on verification failure (fail-fast for security)
        """
        try:
            # Parse receipt
            receipt = self._parse_receipt(json_blob)

            print(f"\n{'='*70}")
            print(f"  anchor CANONICAL VERIFIER - Receipt Validation")
            print(f"{'='*70}")
            print(f"Node: {receipt.hardware_identity.hex()}")
            print(f"Counter: {receipt.counter}")
            print(f"{'='*70}\n")

            # Execute all four checks (fail-fast)
            self._check_identity(receipt)
            self._check_firmware(receipt)
            self._check_monotonicity(receipt)
            self._check_digest(receipt)  # ← CRITICAL: Cryptographic reconstruction

            # Update state ONLY after full verification
            self.counter_db[receipt.hardware_identity] = receipt.counter

            # ⚠️ PRODUCTION: Persist counter state atomically
            # Uncomment in production with proper storage backend:
            # self.save_counter_state()

            msg = "✓ VALID: Receipt authorized for Arbitrum anchoring"
            print(f"\n{msg}\n")
            return True, msg

        except Exception as e:
            error_msg = f"❌ REJECTED: {str(e)}"
            print(f"\n{error_msg}\n")
            return False, error_msg

    # ========================================================================
    # FOUR CANONICAL CHECKS
    # ========================================================================

    def _check_identity(self, receipt: Receipt) -> None:
        """
        Check 1: Identity Allowlist

        Ensures only authorized hardware can submit receipts.
        Prevents: Clone devices, unauthorized nodes
        """
        if receipt.hardware_identity not in self.authorized_nodes:
            raise Exception(
                f"Unauthorized hardware identity: {receipt.hardware_identity.hex()[:16]}..."
            )

        node_name = self.authorized_nodes[receipt.hardware_identity]
        print(f"[1/4] ✓ Identity Check Passed: {node_name}")

    def _check_firmware(self, receipt: Receipt) -> None:
        """
        Check 2: Firmware Governance

        Ensures only governance-approved firmware versions run.
        Prevents: Malicious firmware, unauthorized modifications
        """
        if receipt.firmware_hash not in self.approved_firmware:
            raise Exception(
                f"Firmware not approved by governance: {receipt.firmware_hash.hex()[:16]}..."
            )

        print(f"[2/4] ✓ Firmware Check Passed: {receipt.firmware_hash.hex()[:16]}...")

    def _check_monotonicity(self, receipt: Receipt) -> None:
        """
        Check 3: Monotonic Counter

        Ensures counter strictly increases per device.
        Prevents: Replay attacks, counter rollback
        """
        last_counter = self.counter_db.get(receipt.hardware_identity, 0)

        if receipt.counter <= last_counter:
            raise Exception(
                f"Replay attack detected: counter {receipt.counter} ≤ last seen {last_counter}"
            )

        print(f"[3/4] ✓ Monotonicity Check Passed: {receipt.counter} > {last_counter}")

    def _check_digest(self, receipt: Receipt) -> None:
        """
        Check 4: Receipt Reconstruction (CRITICAL)

        Cryptographically re-derives the receipt digest and compares.
        This is what makes the verifier canonical.

        Prevents: Forged receipts, tampered data, compromised middleware

        Formula (MUST match firmware):
        receipt_digest = keccak256(
            anchor_RCT_V1        ||  // 12 bytes - Domain tag
            hardware_identity   ||  // 32 bytes - Device ID
            firmware_hash       ||  // 32 bytes - Firmware binding
            execution_hash      ||  // 32 bytes - Computation result
            counter_be          ||  //  8 bytes - Replay protection
        )
        """
        # Serialize counter as big-endian (MUST match firmware)
        counter_be = receipt.counter.to_bytes(8, byteorder="big")

        # Reconstruct receipt material (EXACT order matters)
        receipt_material = (
            anchor_RCT_DOMAIN
            + receipt.hardware_identity
            + receipt.firmware_hash
            + receipt.execution_hash
            + counter_be
        )

        # Compute Ethereum Keccak-256 (NOT SHA3-256)
        reconstructed_digest = keccak(receipt_material)

        # Compare with claimed digest
        if reconstructed_digest != receipt.receipt_digest:
            raise Exception(
                f"Receipt digest mismatch!\n"
                f"  Expected: {reconstructed_digest.hex()}\n"
                f"  Received: {receipt.receipt_digest.hex()}"
            )

        print(f"[4/4] ✓ Digest Reconstruction Passed")
        print(f"      Verified: {reconstructed_digest.hex()[:32]}...")

    # ========================================================================
    # PARSING & UTILITIES
    # ========================================================================

    def _parse_receipt(self, json_blob: str) -> Receipt:
        """
        Parse JSON receipt from ESP32 OHR node

        Expected format:
        {
            "hardware_identity": "0x...",  // 32 bytes hex
            "firmware_hash": "0x...",      // 32 bytes hex (OPTIONAL - will be extracted from receipt if missing)
            "execution_hash": "0x...",     // 32 bytes hex
            "receipt_digest": "0x...",     // 32 bytes hex
            "counter": 123                 // uint64
        }
        """
        try:
            data = json.loads(json_blob)

            # Parse and validate hardware_identity
            hw_id_hex = (
                data["hardware_identity"][2:]
                if data["hardware_identity"].startswith("0x")
                else data["hardware_identity"]
            )
            hardware_identity = bytes.fromhex(hw_id_hex)
            assert (
                len(hardware_identity) == 32
            ), f"hardware_identity must be 32 bytes, got {len(hardware_identity)}"

            # Parse and validate firmware_hash
            firmware_hash = data.get("firmware_hash")
            if firmware_hash:
                fw_hex = (
                    firmware_hash[2:]
                    if firmware_hash.startswith("0x")
                    else firmware_hash
                )
                firmware_hash = bytes.fromhex(fw_hex)
                assert (
                    len(firmware_hash) == 32
                ), f"firmware_hash must be 32 bytes, got {len(firmware_hash)}"
            else:
                # If missing, use placeholder (will be checked against approved list anyway)
                firmware_hash = bytes(32)

            # Parse and validate execution_hash
            exec_hex = (
                data["execution_hash"][2:]
                if data["execution_hash"].startswith("0x")
                else data["execution_hash"]
            )
            execution_hash = bytes.fromhex(exec_hex)
            assert (
                len(execution_hash) == 32
            ), f"execution_hash must be 32 bytes, got {len(execution_hash)}"

            # Parse and validate receipt_digest
            digest_hex = (
                data["receipt_digest"][2:]
                if data["receipt_digest"].startswith("0x")
                else data["receipt_digest"]
            )
            receipt_digest = bytes.fromhex(digest_hex)
            assert (
                len(receipt_digest) == 32
            ), f"receipt_digest must be 32 bytes, got {len(receipt_digest)}"

            # Parse counter
            counter = int(data["counter"])
            assert counter >= 0, f"counter must be non-negative, got {counter}"
            assert counter <= 2**64 - 1, f"counter must fit in uint64, got {counter}"

            return Receipt(
                hardware_identity=hardware_identity,
                firmware_hash=firmware_hash,
                execution_hash=execution_hash,
                receipt_digest=receipt_digest,
                counter=counter,
            )
        except (json.JSONDecodeError, KeyError, ValueError, AssertionError) as e:
            raise Exception(f"Invalid receipt format: {e}")

    # ========================================================================
    # REGISTRY MANAGEMENT
    # ========================================================================

    def add_authorized_node(self, hardware_identity_hex: str, node_name: str) -> None:
        """Add a new authorized node to the allowlist"""
        hw_id = bytes.fromhex(hardware_identity_hex.replace("0x", ""))
        self.authorized_nodes[hw_id] = node_name
        print(f"✓ Authorized node added: {node_name}")

    def add_approved_firmware(self, firmware_hash_hex: str) -> None:
        """Add a new approved firmware version"""
        fw_hash = bytes.fromhex(firmware_hash_hex.replace("0x", ""))
        self.approved_firmware.add(fw_hash)
        print(f"✓ Approved firmware added: {firmware_hash_hex[:18]}...")

    def get_node_status(self, hardware_identity_hex: str) -> dict:
        """Get current status of a node"""
        hw_id = bytes.fromhex(hardware_identity_hex.replace("0x", ""))

        return {
            "authorized": hw_id in self.authorized_nodes,
            "node_name": self.authorized_nodes.get(hw_id, "Unknown"),
            "last_counter": self.counter_db.get(hw_id, 0),
        }

    # ========================================================================
    # PRODUCTION PERSISTENCE HELPERS
    # ========================================================================

    def save_counter_state(self, storage_backend: str = "json") -> None:
        """
        Save counter state to persistent storage

        Production implementations should use:
        - PostgreSQL with ACID guarantees
        - Redis with AOF persistence
        - SQLite with WAL mode

        This is a simple example using JSON for demonstration.
        """
        import json as json_lib

        state = {hw_id.hex(): counter for hw_id, counter in self.counter_db.items()}

        if storage_backend == "json":
            with open("anchor_counter_state.json", "w") as f:
                json_lib.dump(state, f, indent=2)

        # Production example (PostgreSQL):
        # cursor.execute(
        #     "INSERT INTO counter_state (hardware_identity, counter) VALUES (%s, %s)"
        #     "ON CONFLICT (hardware_identity) DO UPDATE SET counter = EXCLUDED.counter",
        #     [(hw_id.hex(), counter) for hw_id, counter in self.counter_db.items()]
        # )
        # conn.commit()

    def load_counter_state(self, storage_backend: str = "json") -> None:
        """
        Load counter state from persistent storage

        Should be called during verifier initialization to restore state
        after restarts and maintain replay protection guarantees.
        """
        import json as json_lib
        import os

        if storage_backend == "json":
            if os.path.exists("anchor_counter_state.json"):
                with open("anchor_counter_state.json", "r") as f:
                    state = json_lib.load(f)
                    self.counter_db = {
                        bytes.fromhex(hw_id): counter
                        for hw_id, counter in state.items()
                    }
                print(f"✓ Loaded {len(self.counter_db)} counter states from storage")

        # Production example (PostgreSQL):
        # cursor.execute("SELECT hardware_identity, counter FROM counter_state")
        # self.counter_db = {
        #     bytes.fromhex(row[0]): row[1]
        #     for row in cursor.fetchall()
        # }


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Initialize verifier
    verifier = anchorVerifier()

    # Example: Add your ESP32-S3 node
    verifier.add_authorized_node(
        "0x52fdfc072182654f163f5f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f",
        "Development_ESP32_S3_Alpha",
    )

    # Example: Add approved firmware
    verifier.add_approved_firmware(
        "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
    )

    # Example receipt from ESP32 (would come from serial/network)
    test_receipt = {
        "hardware_identity": "0x52fdfc072182654f163f5f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f",
        "firmware_hash": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
        "execution_hash": "0xdeadbeefcafebabe000000000000000000000000000000000000000000000001",
        "receipt_digest": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
        "counter": 5,
    }

    # Convert to JSON string (as it would come from ESP32)
    receipt_json = json.dumps(test_receipt)

    print("\n" + "=" * 70)
    print("  anchor VERIFIER - EXAMPLE VALIDATION")
    print("=" * 70 + "\n")

    # Verify the receipt
    success, message = verifier.verify_attestation(receipt_json)

    # Check node status
    status = verifier.get_node_status(test_receipt["hardware_identity"])
    print(f"\nNode Status After Verification:")
    print(f"  Authorized: {status['authorized']}")
    print(f"  Name: {status['node_name']}")
    print(f"  Last Counter: {status['last_counter']}")

    print("\n" + "=" * 70)
    print("  TESTING SECURITY INVARIANTS")
    print("=" * 70 + "\n")

    # Test 1: Replay attack (same counter)
    print("\n[TEST 1] Attempting replay attack (same counter)...")
    test_receipt["counter"] = 5  # Same as before
    test_receipt["receipt_digest"] = (
        "0x"
        + keccak(
            b"anchor_RCT_V1"
            + bytes.fromhex(test_receipt["hardware_identity"][2:])
            + bytes.fromhex(test_receipt["firmware_hash"][2:])
            + bytes.fromhex(test_receipt["execution_hash"][2:])
            + (5).to_bytes(8, "big")
        ).hex()
    )

    success, msg = verifier.verify_attestation(json.dumps(test_receipt))
    assert not success, "Should reject replay"
    print(f"Result: {msg}")

    # Test 2: Valid increment
    print("\n[TEST 2] Valid counter increment...")
    test_receipt["counter"] = 6  # Increment
    test_receipt["receipt_digest"] = (
        "0x"
        + keccak(
            b"anchor_RCT_V1"
            + bytes.fromhex(test_receipt["hardware_identity"][2:])
            + bytes.fromhex(test_receipt["firmware_hash"][2:])
            + bytes.fromhex(test_receipt["execution_hash"][2:])
            + (6).to_bytes(8, "big")
        ).hex()
    )

    success, msg = verifier.verify_attestation(json.dumps(test_receipt))
    assert success, "Should accept valid increment"
    print(f"Result: {msg}")

    # Test 3: Unauthorized node
    print("\n[TEST 3] Unauthorized hardware identity...")
    test_receipt["hardware_identity"] = "0x" + "ff" * 32

    success, msg = verifier.verify_attestation(json.dumps(test_receipt))
    assert not success, "Should reject unauthorized node"
    print(f"Result: {msg}")

    # Test 4: Forged digest
    print("\n[TEST 4] Forged receipt digest...")
    test_receipt["hardware_identity"] = (
        "0x52fdfc072182654f163f5f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f"
    )
    test_receipt["counter"] = 7
    test_receipt["receipt_digest"] = "0x" + "ab" * 32  # Forged

    success, msg = verifier.verify_attestation(json.dumps(test_receipt))
    assert not success, "Should reject forged digest"
    print(f"Result: {msg}")

    print("\n" + "=" * 70)
    print("  ALL SECURITY TESTS PASSED")
    print("=" * 70 + "\n")

    print("""
╔══════════════════════════════════════════════════════════════════╗
║                  anchor SOVEREIGNTY ENFORCED                      ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  ✓ Identity Allowlist       - Only authorized hardware          ║
║  ✓ Monotonic Counter        - No replay attacks                 ║
║  ✓ Firmware Governance      - Only approved firmware            ║
║  ✓ Receipt Reconstruction   - Cryptographic integrity           ║
║                                                                  ║
║  Even if firmware leaks, middleware compromised, or attacker    ║
║  knows the protocol, they CANNOT anchor to chain.               ║
║                                                                  ║
║  This is the law of anchor.                                      ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
    """)
