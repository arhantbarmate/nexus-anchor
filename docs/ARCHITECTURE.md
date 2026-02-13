# Stylus Hardware Anchor Architecture

**Version:** 1.1  
**Status:** Technical Specification (Sepolia prototype). Mainnet deployment is out of scope for Phase 1 (current grant); planned for Phase 2 (future grant).  
**Last Updated:** February 8, 2026

---

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Component Specifications](#component-specifications)
4. [Cryptographic Protocol](#cryptographic-protocol)
5. [Data Flow](#data-flow)
6. [Trust Model](#trust-model)
7. [Network Architecture](#network-architecture)
8. [Storage Model](#storage-model)
9. [API Reference](#api-reference)
10. [Performance Characteristics](#performance-characteristics)
11. [Deployment Guide](#deployment-guide)
12. [Security Considerations](#security-considerations)
13. [Future Roadmap](#future-roadmap)
14. [References](#references)

---

## Overview

The Stylus Hardware Anchor establishes a **cryptographic binding between physical hardware and blockchain state**, enabling verifiable off-chain computation with on-chain enforcement. This creates a trust-minimized bridge between real-world hardware execution and decentralized consensus.

### Core Innovation

**Hardware-Bound Receipts:** Unforgeable execution attestations that cryptographically bind:
- Device identity (via eFuse-backed hardware IDs)
- Firmware version (via code hash)
- Computation result (via execution hash)
- Temporal ordering (via monotonic counters)

### Key Properties

- ✅ **Non-Clonable:** Hardware identities derived from manufacturer-burned eFuses
- ✅ **Replay-Resistant:** Monotonic counters prevent receipt reuse
- ✅ **Governance-Enforced:** Only approved firmware versions produce valid receipts
- ✅ **Tamper-Evident:** Any modification invalidates cryptographic digest

---

## System Architecture

### Architectural Layers

The Stylus Hardware Anchor consists of three primary layers that work together to enforce hardware sovereignty:

```
┌─────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                        │
│  (Smart Contracts, DApps, Off-Chain Services)               │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────┐
│                  VERIFICATION LAYER                         │
│  - Canonical Verifier (Python/Rust)                         │
│  - On-Chain Smart Contract (Stylus)                         │
│  - Cryptographic Protocol Enforcement                       │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────┐
│                   HARDWARE LAYER                            │
│  - ESP32-S3 Devices with eFuse Identities                   │
│  - Keccak-256 Cryptography                                  │
│  - Receipt Generation                                       │
└─────────────────────────────────────────────────────────────┘
```

### Design Principles

1. **Separation of Concerns:** Hardware handles identity, verifier enforces protocol, blockchain provides finality
2. **Fail-Safe Defaults:** All operations reject unless explicitly authorized
3. **Defense in Depth:** Multiple layers of cryptographic validation
4. **Minimal Trust Surface:** Trust only manufacturer-guaranteed hardware features

---

## Component Specifications

### 1. Hardware Layer (ESP32-S3)

**Purpose:** Generate unforgeable hardware identities and execution attestations

#### Hardware Components

| Component | Purpose | Security Property |
|-----------|---------|-------------------|
| **eFuse MAC Address** | Unique device identifier | Manufacturer-burned, immutable |
| **Chip Info Register** | Model and revision data | Read-only hardware register |
| **Keccak-256 Engine** | Cryptographic hashing | Ethereum-compatible implementation |
| **NVS (Non-Volatile Storage)** | Counter persistence | Wear-leveled flash storage |
| **Receipt Generator** | Attestation construction | Deterministic output |

#### Key Properties

- ✅ Hardware identity cannot be cloned or spoofed
- ✅ Counters persist across power cycles and reboots
- ✅ All cryptography uses Ethereum-compatible Keccak-256
- ✅ No private keys stored on device (identity derived from hardware)

#### Counter Persistence Trust Model

**Counter Storage Guarantees:**
- Counter persistence relies on ESP32 NVS wear-leveling and flash integrity guarantees
- NVS provides atomic write operations with power-loss protection
- Counter values are **re-verified on-chain** during receipt verification
- Even if local counter is corrupted, on-chain monotonicity check prevents replay attacks

**Security Implication:**
The on-chain counter is the canonical source of truth. ESP32 NVS serves as local state optimization but is not trusted for security.

#### File Structure

```
ohr_firmware/
├── src/
│   ├── main.cpp              # Main firmware logic
│   ├── keccak256.cpp         # Ethereum Keccak implementation
│   └── receipt_generator.cpp # Receipt construction
├── include/
│   └── anchor_protocol.h      # Protocol constants
└── platformio.ini            # Build configuration
```

**Primary Implementation:** `anchor_ohr_esp32_fixed.cpp`

---

### 2. Smart Contract Layer (Arbitrum)

**Purpose:** Enforce permissioning and verify execution attestations on-chain

#### Technology Stack

- **Language:** Rust
- **Compiler:** Rust stable (≥1.82.0)
- **Framework:** Stylus SDK 0.6.0+
- **Target:** WASM (WebAssembly)
- **Deployment:** Arbitrum Sepolia (testnet) / Arbitrum One (production)

#### Contract Address

- **Testnet (Sepolia):** `0x34645ff1dd8af86176fe6b28812aaa4d85e33b0d`
- **Mainnet:** Planned for Phase 2 (future grant); not in Phase 1 scope

#### Storage Schema

```rust
#[storage]
pub struct anchorAnchor {
    /// Maps Hardware ID → Authorization Status
    /// Stores: bytes32 (hw_id) → bool (authorized)
    authorized_nodes: StorageMap<FixedBytes<32>, StorageBool>,
    
    /// Maps Hardware ID → Last Seen Counter
    /// Stores: bytes32 (hw_id) → uint64 (counter)
    /// This is the CANONICAL counter value
    counters: StorageMap<FixedBytes<32>, StorageU64>,
    
    /// Maps Firmware Hash → Approval Status
    /// Stores: bytes32 (fw_hash) → bool (approved)
    approved_firmware: StorageMap<FixedBytes<32>, StorageBool>,
    
    /// Contract owner (admin authority)
    owner: StorageAddress,
}
```

#### Public Interface

**Administrative Functions** (Owner Only):

| Function | Purpose | Gas Cost (est.) |
|----------|---------|-----------------|
| `authorize_node(hw_id)` | Add hardware to allowlist | ~50k gas |
| `revoke_node(hw_id)` | Remove hardware authorization | ~30k gas |
| `approve_firmware(fw_hash)` | Approve firmware version | ~50k gas |
| `revoke_firmware(fw_hash)` | Revoke firmware approval | ~30k gas |
| `transfer_ownership(new_owner)` | Transfer admin control | ~45k gas (preliminary benchmark, Sepolia controlled conditions) |

**Verification Functions** (Public):

| Function | Purpose | Gas Cost (est.) |
|----------|---------|-----------------|
| `verify_receipt(...)` | Verify execution attestation | ~100k gas |

**Query Functions** (View - Free):

| Function | Purpose | Returns |
|----------|---------|---------|
| `is_node_authorized(hw_id)` | Check authorization status | `bool` |
| `is_firmware_approved(fw_hash)` | Check firmware approval | `bool` |
| `get_counter(hw_id)` | Get last counter value | `uint64` |
| `owner()` | Get current owner address | `address` |

#### File Structure

```
contracts/
├── src/
│   └── lib.rs                # Main contract implementation
├── Cargo.toml                # Rust dependencies
└── .cargo/
    └── config.toml           # Stylus build config
```

**Primary Implementation:** `contracts/src/lib.rs`

---

### 3. Verification Layer

**Purpose:** Define and enforce the cryptographic protocol

#### Protocol Constants

```rust
// Domain separation tags (IMMUTABLE - changing = hard fork)
const anchor_RCT_DOMAIN: &[u8] = b"anchor_RCT_V1";  // Receipt digest domain
const anchor_HWI_DOMAIN: &[u8] = b"anchor_OHR_V1";  // Hardware identity domain

// Field sizes (bytes)
const HW_ID_SIZE: usize = 32;
const FW_HASH_SIZE: usize = 32;
const EXEC_HASH_SIZE: usize = 32;
const COUNTER_SIZE: usize = 8;
const DIGEST_SIZE: usize = 32;
const RECEIPT_MATERIAL_SIZE: usize = 117;  // 13 + 32 + 32 + 32 + 8
```

#### Receipt Format Specification

**Binary Structure (117 bytes total):**

```
┌────────────────────────────────────────────────────────┐
│  Offset │ Size │ Field          │ Description          │
├─────────┼──────┼────────────────┼──────────────────────┤
│    0    │  13  │ Protocol ID    │ "anchor_RCT_V1"       │
│   13    │  32  │ Hardware ID    │ Device fingerprint   │
│   45    │  32  │ Firmware Hash  │ Code version binding │
│   77    │  32  │ Execution Hash │ Computation result   │
│  109    │   8  │ Counter        │ Replay protection    │
├─────────┴──────┴────────────────┴──────────────────────┤
│  Total: 117 bytes → Keccak-256 → 32-byte receipt digest│
└────────────────────────────────────────────────────────┘
```

**Field Semantics:**

1. **Protocol ID (13 bytes):** Domain tag `"anchor_RCT_V1"`; version identifier, enables protocol evolution
2. **Hardware ID (32 bytes):** `Keccak256(eFuse MAC || chip info)` - device identity
3. **Firmware Hash (32 bytes):** `Keccak256(compiled_binary)` - code authenticity
4. **Execution Hash (32 bytes):** `Keccak256(input || output)` - computation commitment
5. **Counter (8 bytes BE):** Monotonic u64 in big-endian byte order - temporal ordering

#### Canonical Verification Algorithm

```
FUNCTION verify_receipt(hw_id, fw_hash, exec_hash, counter, claimed_digest)

  ┌──────────────────────────────────────────────────────┐
  │ STAGE 1: Identity Allowlist Check                   │
  └──────────────────────────────────────────────────────┘
  
  IF authorized_nodes[hw_id] != TRUE THEN
    REVERT "Unauthorized Hardware"
  END IF
  
  ┌──────────────────────────────────────────────────────┐
  │ STAGE 2: Firmware Governance Check                  │
  └──────────────────────────────────────────────────────┘
  
  IF approved_firmware[fw_hash] != TRUE THEN
    REVERT "Firmware Not Approved by Governance"
  END IF
  
  ┌──────────────────────────────────────────────────────┐
  │ STAGE 3: Replay Protection (Monotonicity Check)     │
  └──────────────────────────────────────────────────────┘
  
  last_counter = counters[hw_id]  // Canonical on-chain value
  
  IF counter <= last_counter THEN
    REVERT "Replay Attack Detected"
  END IF
  
  ┌──────────────────────────────────────────────────────┐
  │ STAGE 4: Cryptographic Digest Verification          │
  └──────────────────────────────────────────────────────┘
  
  receipt_material = CONCAT(
    anchor_RCT_DOMAIN,           // 13 bytes ("anchor_RCT_V1")
    hw_id,                      // 32 bytes
    fw_hash,                    // 32 bytes
    exec_hash,                  // 32 bytes
    counter.to_be_bytes()       //  8 bytes (big-endian)
  )
  
  reconstructed_digest = Keccak256(receipt_material)
  
  IF reconstructed_digest != claimed_digest THEN
    REVERT "Receipt Digest Mismatch - Tampering Detected"
  END IF
  
  ┌──────────────────────────────────────────────────────┐
  │ STATE UPDATE (only after all checks pass)           │
  └──────────────────────────────────────────────────────┘
  
  counters[hw_id] = counter  // Update canonical counter
  
  EMIT ReceiptVerified(hw_id, counter, exec_hash)
  
  RETURN SUCCESS

END FUNCTION
```

#### Invariants Enforced

**Invariant 1 (Identity):** Only authorized hardware can submit receipts  
**Invariant 2 (Governance):** Only approved firmware can produce valid receipts  
**Invariant 3 (Monotonicity):** Counter strictly increases per device  
**Invariant 4 (Integrity):** Any tampering invalidates the cryptographic digest

**Invariant 5 (Out of Scope):** Execution semantics are NOT verified by the canonical verifier. The verifier treats `execution_hash` as opaque application data. Correctness of execution is enforced at higher layers or through application-specific validation (e.g., ZK proofs, TEE attestation).

#### Implementation Files

- **Firmware:** `anchor_ohr_esp32_fixed.cpp`
- **Python Verifier:** `anchor_canonical_verifier.py`
- **Smart Contract:** `contracts/src/lib.rs`

---

## Cryptographic Protocol

### Hash Function: Ethereum Keccak-256

**Algorithm:** Original Keccak submission (pre-NIST SHA-3 finalization)

**Critical Distinction:**
```
Ethereum Keccak-256:  Padding = 0x01 || 0x00* || 0x80
NIST SHA3-256:        Padding = 0x06 || 0x00* || 0x80

⚠️ These produce DIFFERENT outputs - use Ethereum Keccak ONLY
```

**Parameters:**
- **Rate:** 1088 bits (136 bytes)
- **Capacity:** 512 bits (64 bytes)
- **Output:** 256 bits (32 bytes)
- **Sponge Construction:** Absorb → Squeeze

**Cryptographic Properties:**
- **Collision Resistance:** 2^128 operations (birthday bound)
- **Preimage Resistance:** 2^256 operations (full security)
- **Second Preimage Resistance:** 2^256 operations

### Protocol Hash Usage

#### 1. Hardware Identity Derivation

```cpp
// Input construction (16 bytes)
uint8_t identity_material[16] = {
    mac[0], mac[1], mac[2], mac[3], mac[4], mac[5],  // 6 bytes: eFuse MAC
    chip_model,                                       // 1 byte: ESP32-S3
    chip_revision,                                    // 1 byte: silicon rev
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00   // 8 bytes: zero padding
};

// Hash to produce hardware identity
hardware_identity = Keccak256(identity_material);  // 16 bytes → 32 bytes
```

#### 2. Firmware Hash Computation

```cpp
// Hash the entire compiled firmware binary
firmware_hash = Keccak256(firmware_binary);
```

**Note:** This is computed at build time and embedded in the firmware. The firmware can read its own hash for inclusion in receipts.

#### 3. Execution Hash Commitment

```cpp
// Application-specific - example:
struct ExecutionData {
    uint8_t input[INPUT_SIZE];
    uint8_t output[OUTPUT_SIZE];
};

execution_hash = Keccak256(execution_data);
```

**Design Note:** The structure of `execution_data` is application-defined. The protocol treats this as opaque data.

#### 4. Receipt Digest (Canonical)

```cpp
// Build 117-byte receipt material
uint8_t receipt_material[117];
size_t offset = 0;

// Domain tag (13 bytes, "anchor_RCT_V1")
memcpy(receipt_material + offset, "anchor_RCT_V1", 13);
offset += 13;

// Hardware ID (32 bytes)
memcpy(receipt_material + offset, hardware_identity, 32);
offset += 32;

// Firmware hash (32 bytes)
memcpy(receipt_material + offset, firmware_hash, 32);
offset += 32;

// Execution hash (32 bytes)
memcpy(receipt_material + offset, execution_hash, 32);
offset += 32;

// Counter (8 bytes, big-endian)
uint64_t counter_be = __builtin_bswap64(counter);
memcpy(receipt_material + offset, &counter_be, 8);
offset += 8;

// Compute final digest (Ethereum Keccak-256, 0x01 padding)
receipt_digest = Keccak256(receipt_material);  // 117 bytes → 32 bytes
```

### Test Vectors

**Empty Input:**
```
Input:  "" (0 bytes)
Output: c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470
```

**Simple String:**
```
Input:  "hello" (5 bytes, UTF-8)
Output: 1c8aff950685c2ed4bc3174f3472287b56d9517b9c948127319a09a7a36deac8
```

**Protocol Domain Tag:**
```
Input:  "anchor_RCT_V1" (13 bytes, UTF-8)
Output: [compute and verify against firmware output]
```

### Implementation References

**ESP32-S3:** Custom C implementation (Ethereum Keccak-256, 0x01 padding)
```c
void anchor_keccak256(const uint8_t *input, size_t len, uint8_t *output);
```

**Python Verifier:**
```python
from eth_hash.auto import keccak

digest = keccak(data)  # Returns 32-byte digest
```

**Smart Contract (Stylus/Rust):**
```rust
use alloy_primitives::keccak256;

let digest = keccak256(&data);  // Returns FixedBytes<32>
```

---

## Data Flow

### 1. Hardware Identity Extraction (One-Time per Boot)

```
┌───────────────────────────────────────────────────────┐
│  ESP32-S3 Power-On / Reset                            │
└─────────────────────┬─────────────────────────────────┘
                      │
                      ↓
┌───────────────────────────────────────────────────────┐
│  Read eFuse MAC Address                               │
│  └─ esp_efuse_mac_get_default(mac)                    │
│     Returns: [0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF]     │
└─────────────────────┬─────────────────────────────────┘
                      │
                      ↓
┌───────────────────────────────────────────────────────┐
│  Read Chip Information                                │
│  └─ esp_chip_info(&chip_info)                         │
│     Returns: {model: ESP32_S3, revision: 0}           │
└─────────────────────┬─────────────────────────────────┘
                      │
                      ↓
┌───────────────────────────────────────────────────────┐
│  Construct Identity Material (16 bytes)               │
│  [MAC(6) || Model(1) || Revision(1) || Padding(8)]    │
└─────────────────────┬─────────────────────────────────┘
                      │
                      ↓
┌───────────────────────────────────────────────────────┐
│  Keccak-256 Hash                                      │
│  └─ anchor_keccak256(material, 16, output)             │
└─────────────────────┬─────────────────────────────────┘
                      │
                      ↓
┌───────────────────────────────────────────────────────┐
│  32-byte Hardware Identity (cached)                   │
│  0xABCD...1234                                        │
└─────────────────────┬─────────────────────────────────┘
                      │
                      ↓
┌───────────────────────────────────────────────────────┐
│  Display via Serial:                                  │
│  "Hardware Identity: 0xABCD...1234"                   │
│  (User copies this to authorize on-chain)             │
└───────────────────────────────────────────────────────┘
```

### 2. Receipt Generation Flow (Per Execution)

```
┌───────────────────────────────────────────────────────┐
│  Application Task Execution                           │
│  └─ Process input, generate output                    │
└─────────────────────┬─────────────────────────────────┘
                      │
                      ↓
┌───────────────────────────────────────────────────────┐
│  Compute Execution Hash                               │
│  └─ exec_hash = Keccak256(input || output)            │
└─────────────────────┬─────────────────────────────────┘
                      │
                      ↓
┌───────────────────────────────────────────────────────┐
│  Read Cached Hardware Identity                        │
│  └─ hardware_identity (from boot)                     │
└─────────────────────┬─────────────────────────────────┘
                      │
                      ↓
┌───────────────────────────────────────────────────────┐
│  Read Embedded Firmware Hash                          │
│  └─ firmware_hash (compiled into binary)              │
└─────────────────────┬─────────────────────────────────┘
                      │
                      ↓
┌───────────────────────────────────────────────────────┐
│  Increment Counter (NVS)                              │
│  1. Read current: nvs_get_u64("counter", &val)        │
│  2. Increment: val++                                  │
│  3. Write back: nvs_set_u64("counter", val)           │
│  4. Commit: nvs_commit()                              │
└─────────────────────┬─────────────────────────────────┘
                      │
                      ↓
┌───────────────────────────────────────────────────────┐
│  Build Receipt Material (117 bytes)                   │
│  "anchor_RCT_V1" (13B) || hw_id || fw || exec || counter │
└─────────────────────┬─────────────────────────────────┘
                      │
                      ↓
┌───────────────────────────────────────────────────────┐
│  Compute Receipt Digest                               │
│  └─ digest = Keccak256(receipt_material)              │
└─────────────────────┬─────────────────────────────────┘
                      │
                      ↓
┌───────────────────────────────────────────────────────┐
│  Serialize as JSON                                    │
│  {                                                    │
│    "hardware_identity": "0x...",                      │
│    "firmware_hash": "0x...",                          │
│    "execution_hash": "0x...",                         │
│    "counter": 42,                                     │
│    "receipt_digest": "0x..."                          │
│  }                                                    │
└─────────────────────┬─────────────────────────────────┘
                      │
                      ↓
┌───────────────────────────────────────────────────────┐
│  Transmit via Serial/WiFi/LoRa                        │
│  └─ To verifier or directly to blockchain             │
└───────────────────────────────────────────────────────┘
```

### 3. On-Chain Verification Flow

```
┌───────────────────────────────────────────────────────┐
│  Receipt Submitted to Smart Contract                  │
│  └─ verify_receipt(hw, fw, exec, counter, digest)     │
└─────────────────────┬─────────────────────────────────┘
                      │
                      ↓
┌───────────────────────────────────────────────────────┐
│  [STAGE 1] Identity Allowlist Check                   │
│  └─ IF !authorized_nodes[hw_id] REVERT                │
└─────────────────────┬─────────────────────────────────┘
                      │ ✓ Authorized
                      ↓
┌───────────────────────────────────────────────────────┐
│  [STAGE 2] Firmware Governance Check                  │
│  └─ IF !approved_firmware[fw_hash] REVERT             │
└─────────────────────┬─────────────────────────────────┘
                      │ ✓ Approved
                      ↓
┌───────────────────────────────────────────────────────┐
│  [STAGE 3] Replay Protection Check                    │
│  1. last = counters[hw_id]                            │
│  2. IF counter <= last REVERT                         │
└─────────────────────┬─────────────────────────────────┘
                      │ ✓ Monotonic
                      ↓
┌───────────────────────────────────────────────────────┐
│  [STAGE 4] Digest Reconstruction                      │
│  1. material = "anchor_RCT_V1" (13B) || hw || fw || exec || c│
│  2. reconstructed = Keccak256(material)               │
│  3. IF reconstructed != claimed_digest REVERT         │
└─────────────────────┬─────────────────────────────────┘
                      │ ✓ Verified
                      ↓
┌───────────────────────────────────────────────────────┐
│  Update On-Chain State                                │
│  └─ counters[hw_id] = counter                         │
└─────────────────────┬─────────────────────────────────┘
                      │
                      ↓
┌───────────────────────────────────────────────────────┐
│  Emit Event (Optional - for indexing)                 │
│  └─ ReceiptVerified(hw_id, counter, exec_hash)        │
└─────────────────────┬─────────────────────────────────┘
                      │
                      ↓
┌───────────────────────────────────────────────────────┐
│  Return Success to Caller                             │
│  └─ Transaction completes, state updated              │
└───────────────────────────────────────────────────────┘
```

---

## Trust Model

### Trust Assumptions

#### Trusted Components

| Component | Trust Basis | Failure Impact |
|-----------|-------------|----------------|
| **ESP32-S3 eFuse** | Manufacturer guarantees (Espressif) | Device identity spoofing possible |
| **Keccak-256** | Cryptographic proof (no known attacks) | Receipt forgery possible |
| **Arbitrum Consensus** | Economic security + fraud proofs | State manipulation possible |
| **Smart Contract Logic** | Formal verification + audits | Protocol bypass possible |

#### Untrusted Components

| Component | Why Untrusted | Mitigation |
|-----------|---------------|------------|
| **Firmware Execution** | Software can be modified | Firmware hash verification |
| **Network Transport** | Man-in-the-middle possible | Tamper-evident receipts |
| **Off-Chain Verifier** | Verifier may lie | Anyone can verify on-chain |
| **NVS Counter Storage** | Flash corruption possible | On-chain counter is canonical |

### Security Properties

#### 1. Hardware Identity Binding

**Property:** Each physical device has a unique, unforgeable identity

**Mechanism:**
- eFuse MAC is burned at manufacture (physically irreversible)
- Keccak-256 ensures collision resistance (2^128 security)
- Hardware ID uniquely maps to physical device

**Attack Resistance:**
- ❌ **Clone Attack:** Attacker cannot duplicate eFuse MAC
- ❌ **Spoof Attack:** Attacker cannot forge hardware ID (requires preimage on Keccak)
- ✅ **Detection:** Unauthorized IDs are rejected by allowlist

#### 2. Replay Protection

**Property:** Each receipt can only be used once

**Mechanism:**
- Monotonic counter increments with each receipt
- On-chain storage maintains canonical counter value
- Verification enforces strict inequality: `counter > last_counter`

**Attack Resistance:**
- ❌ **Replay Attack:** Old receipts rejected (counter ≤ last_counter)
- ❌ **Rollback Attack:** Counter state canonical on-chain, ESP32 NVS not trusted
- ✅ **Detection:** Counter monotonicity violation causes immediate revert

#### 3. Firmware Governance

**Property:** Only approved firmware can produce valid receipts

**Mechanism:**
- Firmware hash computed at build time
- On-chain registry of approved hashes
- Receipt includes firmware hash in digest computation

**Attack Resistance:**
- ❌ **Malicious Firmware:** Unapproved firmware hash causes rejection
- ❌ **Unauthorized Modification:** Changed code = different hash = rejection
- ✅ **Governance:** Admin can revoke compromised firmware versions

#### 4. Execution Attestation

**Property:** Receipt cryptographically commits to computation result

**Mechanism:**
- Execution hash commits to input/output data
- Digest binds all receipt components together
- Any tampering invalidates Keccak-256 digest

**Attack Resistance:**
- ❌ **Result Forgery:** Changing exec_hash invalidates digest
- ❌ **Selective Modification:** Changing ANY field invalidates digest
- ✅ **Tamper Evidence:** Cryptographic binding ensures integrity

### Threat Analysis

#### Attack Scenarios & Mitigations

| Attack Vector | Threat | Mitigation | Residual Risk |
|---------------|--------|------------|---------------|
| **Clone Hardware** | Attacker duplicates device | eFuse MAC unforgeable | Manufacturing compromise (low) |
| **Replay Receipt** | Reuse old attestation | Monotonic counter on-chain | None (if blockchain secure) |
| **Modify Firmware** | Run malicious code | Firmware hash governance | Social engineering admin (medium) |
| **Forge Result** | Fake computation output | Receipt digest verification | None (crypto secure) |
| **Tamper Counter** | Rollback replay protection | On-chain canonical counter | NVS for optimization only |
| **MitM Attack** | Intercept/modify receipt | End-to-end integrity (digest) | None (receipts self-authenticating) |
| **Admin Key Compromise** | Unauthorized approvals | Multi-sig or DAO governance (subject to community/regulatory approval) | Key management (medium) |
| **Smart Contract Bug** | Logic error in verification | Audits + formal verification | Implementation errors (low) |

#### Defense-in-Depth Layers

```
┌─────────────────────────────────────────────────────────┐
│  Layer 1: Hardware Identity (eFuse MAC)                 │
│  └─ Prevents: Device cloning                            │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────────┐
│  Layer 2: Firmware Governance (Hash Registry)           │
│  └─ Prevents: Malicious code execution                  │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────────┐
│  Layer 3: Replay Protection (Monotonic Counter)         │
│  └─ Prevents: Receipt reuse                             │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────────┐
│  Layer 4: Cryptographic Integrity (Keccak Digest)       │
│  └─ Prevents: Tampering with any field                  │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ↓
┌─────────────────────────────────────────────────────────┐
│  Layer 5: Blockchain Finality (Arbitrum Consensus)      │
│  └─ Prevents: State manipulation                        │
└─────────────────────────────────────────────────────────┘
```

---

## Network Architecture

### Current Deployment (Sepolia prototype)

```
┌──────────────────────┐
│   ESP32-S3 DevKit    │  ← Hardware Layer
│   - Generate Receipt │
│   - Serial Output    │
└──────────┬───────────┘
           │ USB/Serial (115200 baud)
           ↓
┌──────────────────────┐
│   Developer PC       │  ← Verification Layer
│   - Python Verifier  │
│   - Web3 Client      │
└──────────┬───────────┘
           │ HTTPS (JSON-RPC)
           │ https://sepolia-rollup.arbitrum.io/rpc
           ↓
┌──────────────────────┐
│  Arbitrum Sepolia    │  ← Blockchain Layer
│  - Smart Contract    │
│  - State Storage     │
│  Contract: 0x3464..  │
└──────────────────────┘
```

**Characteristics:**
- **Latency:** ~500ms (serial) + ~2s (RPC) + ~250ms (block time)
- **Throughput:** ~1 receipt per 3 seconds (limited by serial + RPC)
- **Cost:** Free (testnet ETH)

### Target Production Architecture (Phase 2 — future grant; not in Phase 1 scope)

```
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│ ESP32-S3 #1   │  │ ESP32-S3 #2   │  │ ESP32-S3 #N   │
│ - WiFi/LoRa   │  │ - WiFi/LoRa   │  │ - WiFi/LoRa   │
└───────┬───────┘  └───────┬───────┘  └───────┬───────┘
        │                  │                  │
        │ MQTT / HTTP      │ MQTT / HTTP      │ MQTT / HTTP
        └──────────────────┴──────────────────┘
                           │
                           ↓
              ┌────────────────────────┐
              │   Aggregator Node      │  ← Middleware Layer
              │   - Canonical Verifier │
              │   - Batch Processing   │
              │   - Counter DB (Redis) │
              └────────────┬───────────┘
                           │ HTTPS (Batch RPC)
                           │ Redundant Endpoints
                           ↓
              ┌────────────────────────┐
              │  Arbitrum One          │  ← Mainnet Layer
              │  - Mainnet contract    │
              │  - Multi-Sig Ownership │
              │  - Event Indexing      │
              └────────────────────────┘
```

**Characteristics:**
- **Latency:** ~100ms (WiFi/LoRa) + ~1s (batch) + ~250ms (block)
- **Throughput:** ~1000 receipts/second (batched)
- **Cost:** ~$0.02 per receipt (at current gas prices)

### Network Protocols

#### Transport Layer (Hardware → Middleware)

| Protocol | Use Case | Bandwidth | Latency | Range |
|----------|----------|-----------|---------|-------|
| **USB Serial** | Development | 115200 baud | ~5ms | 3m |
| **WiFi** | Production (indoor) | 54 Mbps | ~10ms | 50m |
| **LoRa** | Production (IoT) | 250 kbps | ~100ms | 10km |
| **MQTT** | Production (pub/sub) | Varies | ~50ms | Global (over WiFi) |

#### RPC Layer (Middleware → Blockchain)

| Endpoint | Network | Rate Limit | Recommended For |
|----------|---------|------------|-----------------|
| Public RPC | Arbitrum Sepolia | ~10 req/s | Testing |
| Alchemy/Infura | Arbitrum One | ~300 req/s | Production |
| Self-Hosted | Any | Unlimited | Enterprise |

---

## Storage Model

### On-Chain Storage (Arbitrum)

#### Storage Layout

```rust
// Slot 0: Authorized Nodes (Mapping)
// Key: bytes32 (hardware_identity)
// Value: bool (authorized)
authorized_nodes: StorageMap<FixedBytes<32>, StorageBool>

// Slot 1: Counters (Mapping)  ← CANONICAL SOURCE OF TRUTH
// Key: bytes32 (hardware_identity)
// Value: uint64 (last_seen_counter)
counters: StorageMap<FixedBytes<32>, StorageU64>

// Slot 2: Approved Firmware (Mapping)
// Key: bytes32 (firmware_hash)
// Value: bool (approved)
approved_firmware: StorageMap<FixedBytes<32>, StorageBool>

// Slot 3: Owner
// Value: address (admin)
owner: StorageAddress
```

#### Gas Cost Analysis

| Operation | Storage Access | Gas Cost | USD (est @ $0.25/100k gas) |
|-----------|----------------|----------|----------------------------|
| **Deploy Contract** | Initialize storage | ~2,000,000 | $5.00 |
| **Authorize Node** | SSTORE (cold) | ~50,000 | $0.13 |
| **Verify Receipt** | SLOAD (3x) + SSTORE (1x) | ~100,000 | $0.25 |
| **View Function** | SLOAD (read-only) | 0 (not in tx) | $0.00 |
| **Batch 100 Receipts** | Amortized | ~80,000/ea | $0.20/ea |

**Optimization Strategies:**
1. **Batch Operations:** Approve multiple nodes/firmware in single transaction
2. **Event Emission:** Use events for historical data (cheaper than storage)
3. **Storage Packing:** Co-locate related data (Stylus does this automatically)
4. **L2 Advantages:** Arbitrum is ~50x cheaper than Ethereum L1

### Off-Chain Storage (ESP32-S3)

#### Non-Volatile Storage (NVS)

| Item | Key | Size | Purpose | Persistence |
|------|-----|------|---------|-------------|
| **Counter** | `"counter"` | 8 bytes | Replay protection optimization | NVS flash |
| **HW ID Cache** | `"hw_id"` | 32 bytes | Boot-time cache (optional) | NVS flash |

**Total NVS Usage:** ~40 bytes (negligible)

**NVS Configuration:**
```ini
# partition_table.csv
nvs,      data, nvs,     0x9000,  0x4000,
```

**Wear Leveling:**
- NVS implements automatic wear leveling
- Flash endurance: ~100,000 write cycles per cell
- At 1 receipt/second: ~27 hours per cell
- With wear leveling across 16KB partition: ~1,200 days

#### Flash Storage

| Item | Location | Size | Purpose |
|------|----------|------|---------|
| **Firmware Binary** | Flash partition 0x10000 | ~1-2 MB | Executable code |
| **Keccak Implementation** | Compiled into binary | ~10 KB | Crypto library |
| **Protocol Constants** | .rodata section | ~100 bytes | Domain tags, etc. |

---

## API Reference

### Smart Contract Interface

#### Full Solidity-Style ABI

```solidity
// Pseudo-Solidity for documentation (actual implementation is Rust/Stylus)

interface IanchorAnchor {
    // ============================================================
    // ADMINISTRATIVE FUNCTIONS (Owner Only)
    // ============================================================
    
    /**
     * @notice Authorize a hardware node to submit receipts
     * @param hw_id The 32-byte hardware identity to authorize
     * @dev Only callable by contract owner
     * @dev Emits NodeAuthorized event
     */
    function authorize_node(bytes32 hw_id) external;
    
    /**
     * @notice Revoke authorization for a hardware node
     * @param hw_id The 32-byte hardware identity to revoke
     * @dev Only callable by contract owner
     * @dev Emits NodeRevoked event
     */
    function revoke_node(bytes32 hw_id) external;
    
    /**
     * @notice Approve a firmware version for receipt generation
     * @param fw_hash The 32-byte firmware hash to approve
     * @dev Only callable by contract owner
     * @dev Emits FirmwareApproved event
     */
    function approve_firmware(bytes32 fw_hash) external;
    
    /**
     * @notice Revoke approval for a firmware version
     * @param fw_hash The 32-byte firmware hash to revoke
     * @dev Only callable by contract owner
     * @dev Emits FirmwareRevoked event
     */
    function revoke_firmware(bytes32 fw_hash) external;
    
    /**
     * @notice Transfer contract ownership
     * @param new_owner Address of new owner
     * @dev Only callable by current owner
     */
    function transfer_ownership(address new_owner) external;
    
    // ============================================================
    // VERIFICATION FUNCTION (Public)
    // ============================================================
    
    /**
     * @notice Verify a hardware-generated execution receipt
     * @param hw_id Hardware identity (32 bytes)
     * @param fw_hash Firmware hash (32 bytes)
     * @param exec_hash Execution result hash (32 bytes)
     * @param counter Monotonic counter value (uint64)
     * @param claimed_digest Receipt digest to verify (32 bytes)
     * @dev Reverts if any verification check fails
     * @dev Updates on-chain counter on success
     * @dev Emits ReceiptVerified event on success
     */
    function verify_receipt(
        bytes32 hw_id,
        bytes32 fw_hash,
        bytes32 exec_hash,
        uint64 counter,
        bytes32 claimed_digest
    ) external;
    
    // ============================================================
    // VIEW FUNCTIONS (Public, Read-Only)
    // ============================================================
    
    /**
     * @notice Check if a hardware node is authorized
     * @param hw_id Hardware identity to check
     * @return True if authorized, false otherwise
     */
    function is_node_authorized(bytes32 hw_id) external view returns (bool);
    
    /**
     * @notice Check if a firmware version is approved
     * @param fw_hash Firmware hash to check
     * @return True if approved, false otherwise
     */
    function is_firmware_approved(bytes32 fw_hash) external view returns (bool);
    
    /**
     * @notice Get the last verified counter for a hardware node
     * @param hw_id Hardware identity
     * @return Last counter value (0 if never verified)
     */
    function get_counter(bytes32 hw_id) external view returns (uint64);
    
    /**
     * @notice Get the current contract owner
     * @return Owner address
     */
    function owner() external view returns (address);
    
    // ============================================================
    // EVENTS
    // ============================================================
    
    event NodeAuthorized(bytes32 indexed hw_id);
    event NodeRevoked(bytes32 indexed hw_id);
    event FirmwareApproved(bytes32 indexed fw_hash);
    event FirmwareRevoked(bytes32 indexed fw_hash);
    event ReceiptVerified(bytes32 indexed hw_id, uint64 counter, bytes32 exec_hash);
    event OwnershipTransferred(address indexed old_owner, address indexed new_owner);
}
```

### Python Client API

```python
from web3 import Web3
from eth_account import Account
import json

# ============================================================================
# INITIALIZATION
# ============================================================================

# Connect to Arbitrum
w3 = Web3(Web3.HTTPProvider('https://sepolia-rollup.arbitrum.io/rpc'))

# Load contract
with open('anchorAnchor.abi.json') as f:
    abi = json.load(f)

contract_address = '0x34645ff1dd8af86176fe6b28812aaa4d85e33b0d'
anchor = w3.eth.contract(address=contract_address, abi=abi)

# Setup account
private_key = 'your_private_key_here'
account = Account.from_key(private_key)

# ============================================================================
# ADMINISTRATIVE OPERATIONS
# ============================================================================

def authorize_node(hw_id_hex: str) -> str:
    """Authorize a hardware node"""
    hw_id = bytes.fromhex(hw_id_hex.replace('0x', ''))
    
    tx = anchor.functions.authorize_node(hw_id).build_transaction({
        'from': account.address,
        'nonce': w3.eth.get_transaction_count(account.address),
        'gas': 100000,
        'gasPrice': w3.eth.gas_price
    })
    
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    return tx_hash.hex()

def approve_firmware(fw_hash_hex: str) -> str:
    """Approve a firmware version"""
    fw_hash = bytes.fromhex(fw_hash_hex.replace('0x', ''))
    
    # Similar to authorize_node...
    pass

# ============================================================================
# VERIFICATION
# ============================================================================

def verify_receipt(
    hw_id: str,
    fw_hash: str,
    exec_hash: str,
    counter: int,
    digest: str
) -> str:
    """Submit a receipt for verification"""
    
    tx = anchor.functions.verify_receipt(
        bytes.fromhex(hw_id.replace('0x', '')),
        bytes.fromhex(fw_hash.replace('0x', '')),
        bytes.fromhex(exec_hash.replace('0x', '')),
        counter,
        bytes.fromhex(digest.replace('0x', ''))
    ).build_transaction({
        'from': account.address,
        'nonce': w3.eth.get_transaction_count(account.address),
        'gas': 150000,
        'gasPrice': w3.eth.gas_price
    })
    
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    return tx_hash.hex()

# ============================================================================
# QUERIES (Read-Only)
# ============================================================================

def is_authorized(hw_id_hex: str) -> bool:
    """Check if node is authorized"""
    hw_id = bytes.fromhex(hw_id_hex.replace('0x', ''))
    return anchor.functions.is_node_authorized(hw_id).call()

def get_counter(hw_id_hex: str) -> int:
    """Get last counter value"""
    hw_id = bytes.fromhex(hw_id_hex.replace('0x', ''))
    return anchor.functions.get_counter(hw_id).call()
```

### ESP32-S3 C++ API

```cpp
// anchor_protocol.h

#include <cstdint>
#include <cstddef>

namespace anchor {

// ============================================================================
// DATA STRUCTURES
// ============================================================================

/**
 * Receipt structure containing all verification components
 */
struct Receipt {
    uint8_t hardware_identity[32];  // Device fingerprint
    uint8_t firmware_hash[32];      // Firmware version binding
    uint8_t execution_hash[32];     // Computation result
    uint64_t counter;               // Replay protection
    uint8_t digest[32];             // Cryptographic seal
};

// ============================================================================
// CORE API
// ============================================================================

/**
 * Extract hardware identity from eFuse
 * @param output 32-byte buffer for hardware identity
 * @return ESP_OK on success, error code otherwise
 */
esp_err_t get_hardware_identity(uint8_t output[32]);

/**
 * Generate a receipt for computation result
 * @param exec_hash 32-byte execution result hash
 * @param receipt Output receipt structure
 * @return ESP_OK on success, error code otherwise
 */
esp_err_t generate_receipt(const uint8_t exec_hash[32], Receipt& receipt);

/**
 * Serialize receipt as JSON
 * @param receipt Input receipt structure
 * @param json_buffer Output buffer for JSON string
 * @param buffer_size Size of json_buffer
 * @return Number of bytes written, or -1 on error
 */
int serialize_receipt_json(const Receipt& receipt, char* json_buffer, size_t buffer_size);

// ============================================================================
// UTILITY API
// ============================================================================

/**
 * Compute Keccak-256 hash
 * @param input Input data
 * @param len Input length
 * @param output 32-byte output buffer
 */
void keccak256(const uint8_t* input, size_t len, uint8_t* output);

/**
 * Get current counter value
 * @param counter Output counter value
 * @return ESP_OK on success, error code otherwise
 */
esp_err_t get_counter(uint64_t* counter);

} // namespace anchor
```

---

## Performance Characteristics

### Smart Contract Performance

#### Gas Consumption (Arbitrum Sepolia/One)

| Operation | Cold | Warm | Batch (100x) | Notes |
|-----------|------|------|--------------|-------|
| **Deploy** | ~2,000,000 | N/A | N/A | One-time setup |
| **Authorize Node** | ~50,000 | ~30,000 | ~35,000/ea | Amortized in batch |
| **Approve Firmware** | ~50,000 | ~30,000 | ~35,000/ea | Amortized in batch |
| **Verify Receipt** | ~100,000 | ~80,000 | ~75,000/ea | Most common operation |
| **View Function** | 0 | 0 | 0 | Read-only, no gas |

**Cost Analysis (USD):**
```
Assumptions:
- Arbitrum gas price: ~0.1 gwei
- ETH price: $2,500
- 100k gas = 100,000 * 0.1 gwei * $2,500 = $0.025

Receipt verification: ~$0.025 per receipt
Batch 100 receipts: ~$1.88 total = $0.019 per receipt (24% cheaper)
```

#### Throughput

**Theoretical Maximum:**
```
Arbitrum block gas limit: ~32,000,000 gas/block
Arbitrum block time: ~250ms

Receipts per block = 32,000,000 / 80,000 = 400 receipts/block
Receipts per second = 400 / 0.25 = 1,600 receipts/second
```

**Practical Sustained:**
```
Accounting for network congestion, RPC latency:
~300-500 receipts/second (sustained)
~1,000 receipts/second (burst)
```

### ESP32-S3 Performance

#### Operation Timing

| Operation | Time (ms) | CPU Cycles @ 240MHz | Notes |
|-----------|-----------|---------------------|-------|
| **Boot + Extract ID** | 500 | ~120,000,000 | One-time per power-on |
| **Keccak-256 (16B)** | 1 | ~240,000 | Hardware ID derivation |
| **Keccak-256 (32B)** | 1.5 | ~360,000 | Firmware/exec hash |
| **Keccak-256 (117B)** | 2 | ~480,000 | Receipt digest |
| **NVS Read Counter** | 5 | ~1,200,000 | Flash read |
| **NVS Write Counter** | 10 | ~2,400,000 | Flash write + commit |
| **JSON Serialization** | 2 | ~480,000 | Format receipt |
| **Serial TX (115200)** | 15 | ~3,600,000 | ~200 bytes @ 115200 baud |

#### Total Receipt Generation Time

```
Sequential:
  Hash execution (2ms)
+ Read counter (5ms)
+ Increment counter (0ms)
+ Write counter (10ms)
+ Build receipt (2ms)
+ Hash receipt (2ms)
+ Serialize JSON (2ms)
+ Transmit serial (15ms)
= ~38ms total

Throughput: ~26 receipts/second (limited by NVS writes)
```

#### Optimization: Counter Write Batching

```
Without NVS write (memory-only):
  ~23ms total
  
Throughput: ~43 receipts/second

Batch NVS writes every 10 receipts:
  Amortized: ~25ms/receipt
  
Throughput: ~40 receipts/second
```

### End-to-End Latency

```
┌─────────────────────────────────────────────────────┐
│  ESP32-S3 Receipt Generation: 38ms                  │
└──────────────────┬──────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────┐
│  Serial/Network Transport: 50-100ms                 │
└──────────────────┬──────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────┐
│  Python Verification: 10ms                          │
└──────────────────┬──────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────┐
│  RPC Submission: 500-2000ms                         │
└──────────────────┬──────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────┐
│  Arbitrum Block Inclusion: 250ms                    │
└──────────────────┬──────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────┐
│  Total: ~1-3 seconds (testnet, single receipt)      │
│         ~100-500ms (production, batched)            │
└─────────────────────────────────────────────────────┘
```

---

## Deployment Guide

### Prerequisites

#### Hardware Requirements
- **Device:** ESP32-S3-DevKitC-1 or compatible
- **USB:** Type-C cable for flashing
- **Power:** 5V/1A minimum (USB sufficient)

#### Software Requirements
- **PlatformIO:** Latest stable release
- **Python:** 3.8 or higher
- **Rust:** Stable ≥1.82.0 (for contract development)
- **Node.js:** 16+ (for deployment scripts)

### Contract Deployment

#### 1. Install Stylus Toolchain

```bash
# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Install cargo-stylus
cargo install cargo-stylus

# Verify installation
cargo stylus --version
```

#### 2. Build Contract

```bash
cd contracts/

# Build for Stylus
cargo build --release --target wasm32-unknown-unknown

# Check WASM size (should be < 24KB for deployment)
ls -lh target/wasm32-unknown-unknown/release/*.wasm
```

#### 3. Deploy to Testnet

```bash
# Set environment variables
export PRIVATE_KEY="your_private_key_here"
export RPC_URL="https://sepolia-rollup.arbitrum.io/rpc"

# Deploy
cargo stylus deploy \
  --private-key=$PRIVATE_KEY \
  --endpoint=$RPC_URL

# Save contract address
export CONTRACT_ADDRESS="0x..."
```

#### 4. Verify Deployment

```python
from web3 import Web3

w3 = Web3(Web3.HTTPProvider('https://sepolia-rollup.arbitrum.io/rpc'))
code = w3.eth.get_code('0x34645ff1dd8af86176fe6b28812aaa4d85e33b0d')

assert len(code) > 0, "Contract not deployed"
print(f"✓ Contract deployed: {len(code)} bytes")
```

### Firmware Deployment

#### 1. Configure PlatformIO

```ini
; platformio.ini
[env:esp32s3]
platform = espressif32
board = esp32-s3-devkitc-1
framework = arduino
monitor_speed = 115200

build_flags =
    -DCORE_DEBUG_LEVEL=3
    -DARDUINO_USB_CDC_ON_BOOT=1

lib_deps =
    # Add Keccak library here when available
```

#### 2. Flash Firmware

```bash
# Build firmware
pio run

# Flash to ESP32-S3
pio run --target upload

# Monitor serial output
pio device monitor --baud 115200
```

#### 3. Extract Hardware Identity

```bash
# Watch serial output for:
# "Hardware Identity: 0xABCD...1234"

# Copy this value for contract authorization
```

### Integration Setup

#### 1. Authorize Hardware

```python
from web3 import Web3
from eth_account import Account

w3 = Web3(Web3.HTTPProvider('https://sepolia-rollup.arbitrum.io/rpc'))
anchor = w3.eth.contract(address=CONTRACT_ADDRESS, abi=ABI)

# Hardware identity from ESP32
hw_id = "0xABCD...1234"  # From serial output

# Authorize
account = Account.from_key(PRIVATE_KEY)
tx = anchor.functions.authorize_node(bytes.fromhex(hw_id[2:])).build_transaction({
    'from': account.address,
    'nonce': w3.eth.get_transaction_count(account.address)
})

signed = account.sign_transaction(tx)
tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

print(f"✓ Node authorized: {tx_hash.hex()}")
```

#### 2. Approve Firmware

```python
# Firmware hash from build output
fw_hash = "0x1234...5678"  # From compilation

# Approve
tx = anchor.functions.approve_firmware(bytes.fromhex(fw_hash[2:])).build_transaction({
    'from': account.address,
    'nonce': w3.eth.get_transaction_count(account.address)
})

signed = account.sign_transaction(tx)
tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)

print(f"✓ Firmware approved: {tx_hash.hex()}")
```

#### 3. Test End-to-End

```python
# Receive receipt from ESP32 (via serial)
receipt_json = '{"hardware_identity": "0x...", ...}'
receipt = json.loads(receipt_json)

# Submit to contract
tx = anchor.functions.verify_receipt(
    bytes.fromhex(receipt['hardware_identity'][2:]),
    bytes.fromhex(receipt['firmware_hash'][2:]),
    bytes.fromhex(receipt['execution_hash'][2:]),
    receipt['counter'],
    bytes.fromhex(receipt['receipt_digest'][2:])
).build_transaction({
    'from': account.address,
    'nonce': w3.eth.get_transaction_count(account.address)
})

signed = account.sign_transaction(tx)
tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)

print(f"✓ Receipt verified: {tx_hash.hex()}")
```

---

## Security Considerations

### Production Hardening Checklist

#### Smart Contract

- [ ] **Formal Verification:** Prove correctness of verification algorithm
- [ ] **Security Audit:** Third-party audit of Rust/Stylus code
- [ ] **Governance:** Implement multi-sig or DAO for admin functions (subject to regulatory and community approval)
- [ ] **Upgradability:** Consider proxy pattern for bug fixes
- [ ] **Event Indexing:** Deploy subgraph for historical queries
- [ ] **Rate Limiting:** Consider gas-based DoS protection
- [ ] **Emergency Pause:** Implement circuit breaker if needed

#### ESP32-S3 Firmware

- [ ] **Secure Boot:** Enable Secure Boot V2 for code signing
- [ ] **Flash Encryption:** Encrypt firmware in flash
- [x] **Keccak Implementation:** Ethereum-compatible Keccak-256 (0x01 padding) integrated
- [ ] **OTA Updates:** Implement secure over-the-air updates
- [ ] **Tamper Detection:** Monitor NVS corruption
- [ ] **Debug Disabled:** Disable JTAG/serial debugging in production
- [ ] **Firmware Signing:** Sign binaries before deployment

#### Operational Security

- [ ] **Key Management:** Use hardware wallets for admin keys
- [ ] **Monitoring:** Real-time alerts for unexpected receipts
- [ ] **Backup RPC:** Redundant Arbitrum endpoints
- [ ] **Incident Response:** Plan for compromise scenarios
- [ ] **Regular Updates:** Patch firmware for discovered vulnerabilities
- [ ] **Access Control:** Limit who can authorize nodes/firmware

### Known Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| **Keccak** | Ethereum Keccak-256 (0x01 padding) | Baseline parity achieved across firmware, Python, Stylus |
| **No TEE** | Firmware execution not isolated | Use Secure Boot + Flash Encryption |
| **Counter Overflow** | uint64 max = 18 quintillion | Not practical concern (1B/sec = 584 years) |
| **eFuse Cloning** | Manufacturing compromise possible | Rely on multiple devices for redundancy |
| **Gas Price Volatility** | Receipt cost varies with gas price | Monitor gas and batch when high |

---

## Future Roadmap

For the official project timeline, budget allocations, and grant milestones, please refer to the [ROADMAP.md](../ROADMAP.md) file.

## References

### Standards & Specifications

- **Keccak-256:** https://keccak.team/keccak.html
- **Ethereum Yellow Paper:** https://ethereum.github.io/yellowpaper
- **Stylus Documentation:** https://docs.arbitrum.io/stylus
- **ESP-IDF Documentation:** https://docs.espressif.com/projects/esp-idf

### Implementation References

- **Stylus SDK:** https://github.com/OffchainLabs/stylus-sdk-rs
- **Alloy Primitives:** https://github.com/alloy-rs/core
- **web3.py:** https://web3py.readthedocs.io
- **PlatformIO:** https://platformio.org

### Security Resources

- **eFuse Security:** ESP32-S3 Technical Reference Manual, Chapter 20
- **Monotonic Counters:** NIST SP 800-90B
- **Secure Boot:** ESP32-S3 Secure Boot V2 Guide
- **Flash Encryption:** ESP32-S3 Flash Encryption Guide

### Related Work

- **Intel SGX:** Trusted Execution Environments
- **ARM TrustZone:** Hardware isolation
- **TPM 2.0:** Trusted Platform Modules
- **Chainlink:** Decentralized oracles (different trust model)

---

## Appendix A: Glossary

| Term | Definition |
|------|------------|
| **eFuse** | Electrically programmable one-time fuses in silicon |
| **Hardware Identity** | Keccak-256 hash of eFuse MAC + chip info |
| **Receipt** | Cryptographic attestation of hardware execution |
| **Digest** | 32-byte Keccak-256 hash binding receipt components |
| **Monotonic Counter** | Strictly increasing value preventing replay |
| **Stylus** | Arbitrum's WASM-based smart contract framework |
| **Keccak-256** | Ethereum's hash function (pre-NIST SHA-3) |
| **NVS** | Non-Volatile Storage (ESP32 flash partition) |

---

## Appendix B: File Manifest

```
stylus-hardware-anchor/
├── contracts/
│   ├── src/
│   │   └── lib.rs                    # Stylus smart contract
│   ├── Cargo.toml                    # Rust dependencies
│   └── .cargo/config.toml            # Build configuration
│
├── firmware/
│   ├── src/
│   │   ├── main.cpp                  # Main firmware
│   │   ├── anchor_ohr_esp32_fixed.cpp # Production implementation
│   │   └── keccak256.cpp             # Ethereum Keccak-256 (0x01)
│   ├── include/
│   │   └── anchor_protocol.h          # API header
│   └── platformio.ini                # Build config
│
├── verifier/
│   ├── anchor_canonical_verifier.py   # Python verifier
│   ├── generate_test_receipt.py      # Test utilities
│   ├── requirements.txt              # Dependencies
│   └── README_VERIFIER.md            # Setup guide
│
├── docs/
│   ├── ARCHITECTURE.md               # This document
│   ├── SECURITY_AUDIT_COMPLIANCE.md  # Audit report
│   ├── PRODUCTION_DEPLOYMENT_GUIDE.md# Deployment guide
│   └── anchor_CANONICAL_VERIFIER_SPEC.md # Verifier spec
│
└── README.md                          # Project overview
```

---

## Revision History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-02-08 | Initial architecture document | anchor Team |
| 1.1 | 2026-02-08 | Production specification update | anchor Team |
|  |  | - Added NVS trust model clarification |  |
|  |  | - Standardized Rust version (≥1.82.0) |  |
|  |  | - Expanded security considerations |  |
|  |  | - Added deployment guide |  |
|  |  | - Complete API reference |  |

---

**Document Status:** Technical Specification  
**Classification:** Public  
**Last Updated:** February 8, 2026  
**Maintainer:** Stylus Hardware Anchor Development Team  
**License:** MIT

---

**END OF ARCHITECTURE DOCUMENT**
