![Nexus Protocol CI](https://github.com/arhantbarmate/nexus-anchor/actions/workflows/ci.yml/badge.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Arbitrum](https://img.shields.io/badge/Arbitrum-Sepolia-blue.svg)
![Rust](https://img.shields.io/badge/rust-1.93.0-orange.svg)
![ESP32](https://img.shields.io/badge/ESP32-S3-green.svg)

# Nexus Protocol/Anchor - Orthonode Hardware Root (OHR)

Hardware-to-Blockchain Identity Binding for Verifiable Off-Chain Computation

## 🎯 Milestone 1: COMPLETE (Milestone scope) ✅

- ✅ Smart Contract Deployed (Arbitrum Sepolia)
- ✅ Hardware Identity System Implemented (eFuse-backed)
- ✅ On-Chain Authorization Verified (CONFIRMED)
- ✅ Cryptographic Verification Protocol (Keccak-256)

## 🔗 Links

- **Contract:** [0x34645ff1dd8af86176fe6b28812aaa4d85e33b0d](https://sepolia.arbiscan.io/address/0x34645ff1dd8af86176fe6b28812aaa4d85e33b0d)
- **Authorization TX:** [0x84aa8ded972c43baefb711089c54d9730f7964e85444596137b76f4e5991551c](https://sepolia.arbiscan.io/tx/0x84aa8ded972c43baefb711089c54d9730f7964e85444596137b76f4e5991551c)

## 🏗️ Architecture

### Three-Layer Trust Model

**Layer 1: Hardware Identity**
- ESP32-S3 eFuse-backed MAC extraction
- Keccak-256 hashing (Ethereum-compatible)
- 32-byte Hardware Identity output

**Layer 2: Smart Contract**
- Rust/Stylus implementation
- On-chain allowlist enforcement
- Monotonic counter storage

**Layer 3: Verification Protocol**
- 116-byte receipt format
- Four-stage validation
- Cryptographic digest reconstruction

## 📊 Receipt Format (116 bytes)
```
"NEXUS_RCT_V1"  (12 bytes) - Protocol marker
HW_ID           (32 bytes) - Hardware identity
FW_HASH         (32 bytes) - Firmware hash
EXEC_HASH       (32 bytes) - Execution result hash
COUNTER         (8 bytes)  - Monotonic counter (Big-Endian)
────────────────────────────
Total: 116 bytes → Keccak-256 → 32-byte digest
```

## 🔒 Security Properties

- ✅ Manufacturer-burned unique identifiers (eFuse-backed)
- ✅ Identity cryptographically bound to chain state
- ✅ Authorization enforced on-chain
- ✅ Replay attacks prevented (monotonic counters)
- ✅ Firmware governance enforced

## 📖 Documentation

- [MILESTONE_1.md](docs/MILESTONE_1.md) - Complete technical submission
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - System design details
- [DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md) - Setup instructions
- [TECHNICAL_CHALLENGES.md](docs/TECHNICAL_CHALLENGES.md) - Problems solved

## 🚀 Quick Start

### Deploy Contract
```bash
cd contracts
cargo stylus deploy --private-key $PRIVATE_KEY
```

### Extract Hardware Identity
```bash
# Flash to ESP32-S3
arduino-cli upload -p /dev/ttyUSB0 hardware/ohr_identity
# View serial output for Hardware Identity
```

### Authorize Node
```python
python scripts/authorize_hardware.py --hw-id 0xabc123...
```

### Verify Authorization
```python
python scripts/test_contract.py
```

## 🛣️ Roadmap

- [x] **Milestone 1:** Hardware-to-Blockchain Identity Binding
- [ ] **Milestone 2:** Firmware Attestation Integration
- [ ] **Milestone 3:** Multi-Node Orchestration
- [ ] **Milestone 4:** Production Security Hardening

## 📄 License

MIT License - See [LICENSE](LICENSE) for details

## 🤝 Grant Support

This project is supported by the Arbitrum Foundation Grant Program.
