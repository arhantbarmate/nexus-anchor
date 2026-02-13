import json
from dataclasses import dataclass
from typing import Dict, Tuple

from eth_utils import keccak

# ============================================================
# CONSTANTS (Must match firmware + contract)
# ============================================================

anchor_RCT_DOMAIN = b"anchor_RCT_V1"  # 13 bytes


# ============================================================
# DATA STRUCTURES
# ============================================================


@dataclass
class NodeState:
    name: str
    last_counter: int = 0


# ============================================================
# CANONICAL VERIFIER
# ============================================================


class AnchorVerifier:
    def __init__(self):
        self.authorized_nodes: Dict[bytes, NodeState] = {}
        self.approved_firmware: set[bytes] = set()

    # --------------------------------------------------------
    # ADMIN METHODS
    # --------------------------------------------------------

    def add_authorized_node(self, hardware_identity_hex: str, name: str):
        hw = self._parse_32byte_hex(hardware_identity_hex, "hardware_identity")
        self.authorized_nodes[hw] = NodeState(name=name)
        print(f"✓ Authorized node added: {name}")

    def add_approved_firmware(self, firmware_hash_hex: str):
        fw = self._parse_32byte_hex(firmware_hash_hex, "firmware_hash")
        self.approved_firmware.add(fw)
        print(f"✓ Approved firmware added: {firmware_hash_hex[:18]}...")

    # --------------------------------------------------------
    # VERIFICATION ENTRYPOINT
    # --------------------------------------------------------

    def verify_attestation(self, receipt_json: str) -> Tuple[bool, str]:
        print("\n" + "=" * 70)
        print("  anchor CANONICAL VERIFIER - Receipt Validation")
        print("=" * 70)

        try:
            receipt = json.loads(receipt_json)
        except Exception:
            return False, "Invalid JSON"

        required_fields = [
            "hardware_identity",
            "firmware_hash",
            "execution_hash",
            "receipt_digest",
            "counter",
        ]

        for field in required_fields:
            if field not in receipt:
                return False, f"Missing field: {field}"

        # Parse fields
        hw = self._parse_32byte_hex(receipt["hardware_identity"], "hardware_identity")
        fw = self._parse_32byte_hex(receipt["firmware_hash"], "firmware_hash")
        ex = self._parse_32byte_hex(receipt["execution_hash"], "execution_hash")
        digest_received = self._parse_32byte_hex(
            receipt["receipt_digest"], "receipt_digest"
        )

        counter = receipt["counter"]
        if not isinstance(counter, int) or counter < 0:
            return False, "Invalid counter"

        print(f"Node: {hw.hex()}")
        print(f"Counter: {counter}")
        print("-" * 70)

        # ----------------------------------------------------
        # 1️⃣ Identity Check
        # ----------------------------------------------------
        if hw not in self.authorized_nodes:
            return False, "Unauthorized hardware identity"

        node = self.authorized_nodes[hw]
        print(f"[1/4] ✓ Identity Check Passed: {node.name}")

        # ----------------------------------------------------
        # 2️⃣ Firmware Check
        # ----------------------------------------------------
        if fw not in self.approved_firmware:
            return False, "Unapproved firmware hash"

        print(f"[2/4] ✓ Firmware Check Passed")

        # ----------------------------------------------------
        # 3️⃣ Monotonic Counter Check
        # ----------------------------------------------------
        if counter <= node.last_counter:
            return False, "Replay detected (counter not strictly increasing)"

        print(f"[3/4] ✓ Monotonicity Check Passed: {counter} > {node.last_counter}")

        # ----------------------------------------------------
        # 4️⃣ Digest Reconstruction
        # ----------------------------------------------------
        expected_digest = keccak(
            anchor_RCT_DOMAIN + hw + fw + ex + counter.to_bytes(8, "big")
        )

        if expected_digest != digest_received:
            return False, "Receipt digest mismatch"

        print(f"[4/4] ✓ Digest Reconstruction Passed")

        # ----------------------------------------------------
        # STATE UPDATE (CRITICAL)
        # ----------------------------------------------------
        node.last_counter = counter

        print("✓ VALID: Receipt authorized for anchoring\n")
        return True, "Valid receipt"

    # --------------------------------------------------------
    # INTERNAL UTILITIES
    # --------------------------------------------------------

    def _parse_32byte_hex(self, value: str, field: str) -> bytes:
        if not isinstance(value, str) or not value.startswith("0x"):
            raise ValueError(f"{field} must be 0x-prefixed hex")

        raw = bytes.fromhex(value[2:])
        if len(raw) != 32:
            raise ValueError(f"{field} must be 32 bytes")

        return raw


# ============================================================
# SELF-TEST HARNESS
# ============================================================

if __name__ == "__main__":
    verifier = AnchorVerifier()

    hw_hex = "0x52fdfc072182654f163f5f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f"
    fw_hex = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"

    verifier.add_authorized_node(hw_hex, "Development_ESP32_S3_Alpha")
    verifier.add_approved_firmware(fw_hex)

    def build_receipt(counter: int):
        hw = bytes.fromhex(hw_hex[2:])
        fw = bytes.fromhex(fw_hex[2:])
        ex = bytes.fromhex(
            "deadbeefcafebabe000000000000000000000000000000000000000000000001"
        )

        digest = keccak(anchor_RCT_DOMAIN + hw + fw + ex + counter.to_bytes(8, "big"))

        return json.dumps(
            {
                "hardware_identity": hw_hex,
                "firmware_hash": fw_hex,
                "execution_hash": "0xdeadbeefcafebabe000000000000000000000000000000000000000000000001",
                "receipt_digest": "0x" + digest.hex(),
                "counter": counter,
            }
        )

    print("\nRunning Security Tests...\n")

    # First valid
    assert verifier.verify_attestation(build_receipt(5))[0]

    # Replay (should fail)
    assert not verifier.verify_attestation(build_receipt(5))[0]

    # Increment
    assert verifier.verify_attestation(build_receipt(6))[0]

    print("\nALL TESTS PASSED\n")
