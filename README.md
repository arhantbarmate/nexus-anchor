# Stylus Hardware Anchor (SHA)

![CI Status](https://github.com/arhantbarmate/stylus-hardware-anchor/actions/workflows/ci.yml/badge.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Arbitrum](https://img.shields.io/badge/Arbitrum-Stylus-blue.svg)
![Rust](https://img.shields.io/badge/Rust-WASM-orange.svg)
![ESP32](https://img.shields.io/badge/Hardware--Bound-green.svg)

**A protocol-level bridge binding immutable silicon identity to Arbitrum Stylus.**

Stylus Hardware Anchor (SHA) is a reusable hardware identity verification primitive designed for Stylus smart contracts. It cryptographically binds immutable ESP32-S3 eFuse identifiers to on-chain execution logic, enabling deterministic device identity, replay-safe receipts, and firmware-governed access control.

Preliminary benchmark: ~45k gas per verification on Arbitrum Sepolia under controlled test conditions.

---

## 🏗️ Hardware Identity Primitive for Stylus

SHA provides a structured approach to hardware-bound execution in decentralized systems. By moving from software-only private keys to silicon-bound cryptographic proofs, it enables:

- **Device-Bound Identity:** 1 physical device ↔ 1 on-chain identity  
- **Replay-Safe Receipts:** Monotonic counter enforcement  
- **Firmware Governance:** Execution restricted to approved firmware versions  
- **Deterministic Verification:** Ethereum-compatible Keccak-256 (0x01 padding)

This project is focused on providing reusable infrastructure, not a standalone application.

---

## Current Status

- Prototype deployed on Arbitrum Sepolia  
- Firmware ↔ Python ↔ Stylus cryptographic parity achieved  
- ≥10,000 deterministic test vectors validated  
- Security hardening (Phase 1 — Milestone 1) pending grant approval  

No professional third-party audit has been conducted. Mainnet deployment is not part of the current scope.

---

## 🔗 Live Evidence (Sepolia)

| Artifact | Link |
|----------|------|
| Stylus Contract | [`0x34645ff1dd8af86176fe6b28812aaa4d85e33b0d`](https://sepolia.arbiscan.io/address/0x34645ff1dd8af86176fe6b28812aaa4d85e33b0d) |
| Verification TX | [`0x84aa8ded...991551c`](https://sepolia.arbiscan.io/tx/0x84aa8ded972c43baefb711089c54d9730f7964e85444596137b76f4e5991551c) |
| v1.0.0 Prototype Release | [View Release](https://github.com/arhantbarmate/stylus-hardware-anchor/releases/tag/v1.0.0) |

---

## 🛠️ Architecture Overview

### 1️⃣ Silicon Layer (ESP32-S3)

- Extracts manufacturer-burned identifiers (Base MAC + Chip Model)  
- Generates 32-byte Hardware Identity (HW_ID)  
- On-device Keccak-256 (Ethereum-compatible, 0x01 padding)

### 2️⃣ Verification Layer (Stylus / Rust / WASM)

- Reconstructs receipt digests  
- Enforces monotonic counter replay protection  
- Validates firmware hash gating  

### 3️⃣ Middleware Layer (Python SDK — Early Access)

- Device authorization flows  
- Receipt generation utilities  
- On-chain submission helpers  

---

## 🛣️ Roadmap

### Phase 1 — Current Grant Scope  
**$49,000 USD — 6 months — Testnet Only (Arbitrum Sepolia)**

- Milestone 1: Security Hardening  
- Milestone 2: Developer SDK & Integration Tooling  

No professional audit, mainnet deployment, or ecosystem expansion is included in Phase 1.

### Phase 2 — Future Grant (Not in Current Scope)

- Professional third-party security audit  
- Mainnet deployment  
- Hardware reference design  
- Broader ecosystem integrations  

See [ROADMAP.md](ROADMAP.md) for full details.

---

## 📖 Technical Documentation

- [ARCHITECTURE.md](docs/ARCHITECTURE.md) — Detailed system design  
- [TECHNICAL_CHALLENGES.md](docs/TECHNICAL_CHALLENGES.md) — Integration logs  
- [MILESTONE_1.md](docs/MILESTONE_1.md) — Prototype validation evidence  

---

## ⚖️ Scope Clarification

SHA is currently a testnet-deployed prototype.  

Phase 1 focuses on:

- Internal security hardening  
- Reproducible validation artifacts  
- Developer tooling  

Professional audit and mainnet deployment are explicitly deferred to Phase 2.

---

## 📄 License

MIT — See [LICENSE](LICENSE)

---

## 🤝 Development Focus

SHA is being developed as reusable infrastructure for the Arbitrum ecosystem, with a disciplined roadmap toward audit preparation and eventual mainnet deployment, contingent on successful Phase 1 completion.
