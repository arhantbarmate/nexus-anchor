#!/usr/bin/env python3
"""
anchor Test Receipt Generator
Generates cryptographically valid test receipts for verifier testing
"""

import json
from eth_hash.auto import keccak

anchor_RCT_DOMAIN = b"anchor_RCT_V1"


def generate_test_receipt(
    hardware_identity: str = None,
    firmware_hash: str = None,
    execution_hash: str = None,
    counter: int = 1,
) -> dict:
    """
    Generate a cryptographically valid test receipt

    Args:
        hardware_identity: 32-byte hex (defaults to test value)
        firmware_hash: 32-byte hex (defaults to test value)
        execution_hash: 32-byte hex (defaults to test value)
        counter: uint64 counter value

    Returns:
        dict: Valid receipt with correct digest
    """
    # Use defaults if not provided
    if hardware_identity is None:
        hardware_identity = (
            "52fdfc072182654f163f5f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f"
        )

    if firmware_hash is None:
        firmware_hash = (
            "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
        )

    if execution_hash is None:
        execution_hash = (
            "deadbeefcafebabe000000000000000000000000000000000000000000000001"
        )

    # Remove 0x prefix if present
    hardware_identity = hardware_identity.replace("0x", "")
    firmware_hash = firmware_hash.replace("0x", "")
    execution_hash = execution_hash.replace("0x", "")

    # Validate lengths
    assert (
        len(hardware_identity) == 64
    ), f"hardware_identity must be 64 hex chars, got {len(hardware_identity)}"
    assert (
        len(firmware_hash) == 64
    ), f"firmware_hash must be 64 hex chars, got {len(firmware_hash)}"
    assert (
        len(execution_hash) == 64
    ), f"execution_hash must be 64 hex chars, got {len(execution_hash)}"
    assert 0 <= counter < 2**64, f"counter must fit in uint64, got {counter}"

    # Convert to bytes
    hw_id_bytes = bytes.fromhex(hardware_identity)
    fw_hash_bytes = bytes.fromhex(firmware_hash)
    exec_hash_bytes = bytes.fromhex(execution_hash)
    counter_be = counter.to_bytes(8, "big")

    # Compute canonical receipt digest
    receipt_material = (
        anchor_RCT_DOMAIN + hw_id_bytes + fw_hash_bytes + exec_hash_bytes + counter_be
    )

    receipt_digest = keccak(receipt_material)

    # Build receipt
    receipt = {
        "hardware_identity": "0x" + hardware_identity,
        "firmware_hash": "0x" + firmware_hash,
        "execution_hash": "0x" + execution_hash,
        "receipt_digest": "0x" + receipt_digest.hex(),
        "counter": counter,
    }

    return receipt


def print_receipt(receipt: dict):
    """Pretty-print a receipt"""
    print(json.dumps(receipt, indent=2))


def verify_receipt_format(receipt: dict) -> bool:
    """Verify a receipt has the correct format"""
    required_fields = [
        "hardware_identity",
        "firmware_hash",
        "execution_hash",
        "receipt_digest",
        "counter",
    ]

    for field in required_fields:
        if field not in receipt:
            print(f"✗ Missing field: {field}")
            return False

    # Check lengths
    checks = [
        ("hardware_identity", 66),  # 0x + 64 hex chars
        ("firmware_hash", 66),
        ("execution_hash", 66),
        ("receipt_digest", 66),
    ]

    for field, expected_len in checks:
        actual_len = len(receipt[field])
        if actual_len != expected_len:
            print(f"✗ {field}: expected {expected_len} chars, got {actual_len}")
            return False

    if not isinstance(receipt["counter"], int):
        print(f"✗ counter must be int, got {type(receipt['counter'])}")
        return False

    print("✓ Receipt format is valid")
    return True


if __name__ == "__main__":
    print("=" * 70)
    print("  anchor TEST RECEIPT GENERATOR")
    print("=" * 70)
    print()

    # Generate default test receipt
    print("Generating test receipt with default values...")
    receipt = generate_test_receipt(counter=1)

    print("\nGenerated Receipt:")
    print_receipt(receipt)

    print("\n" + "=" * 70)
    print("Validating receipt format...")
    print("=" * 70)
    verify_receipt_format(receipt)

    print("\n" + "=" * 70)
    print("Testing counter sequence...")
    print("=" * 70)

    for i in range(1, 4):
        receipt = generate_test_receipt(counter=i)
        print(f"\nCounter {i}: digest = {receipt['receipt_digest'][:18]}...")

    print("\n" + "=" * 70)
    print("Custom receipt example:")
    print("=" * 70)

    custom = generate_test_receipt(
        hardware_identity="aa" * 32,
        firmware_hash="bb" * 32,
        execution_hash="cc" * 32,
        counter=42,
    )

    print_receipt(custom)

    print("\n" + "=" * 70)
    print("Usage in Python:")
    print("=" * 70)
    print("""
from generate_test_receipt import generate_test_receipt
import json

# Generate valid receipt
receipt = generate_test_receipt(
    hardware_identity="<your_hw_id>",
    firmware_hash="<your_fw_hash>",
    counter=1
)

# Convert to JSON string
receipt_json = json.dumps(receipt)

# Send to verifier
verifier.verify_attestation(receipt_json)
    """)
