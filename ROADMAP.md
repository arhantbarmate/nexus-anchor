# Stylus Hardware Anchor (SHA) — Roadmap

## Overview

Stylus Hardware Anchor (SHA) is a reusable hardware identity verification primitive for Arbitrum Stylus contracts. It binds immutable silicon identifiers (ESP32 eFuse values) to on-chain logic, enabling deterministic device identity, replay-safe receipt validation, and firmware-governed execution.

This roadmap reflects **Phase 1 only**.

---

# Phase 1 — Current Grant Scope

**Total Grant Request:** $49,000 USD  
**Duration:** 6 months  
**Network Scope:** Arbitrum Sepolia (testnet only)  
**Milestones:** 2  

Phase 1 focuses strictly on:

- Security hardening of the existing Sepolia prototype  
- Reproducible validation artifacts  
- Developer SDK and integration tooling  
- Testnet deployment support  

No professional third-party audit, mainnet deployment, or ecosystem expansion is included in this scope.

---

# Milestone 1 — Security Hardening (Months 1–3)

**Allocation:** $24,000 USD  
**Scope:** Testnet-only (Arbitrum Sepolia)

## Objective

Strengthen the existing prototype through internal security hardening, systematic fuzz testing, reproducible benchmarking, and formal documentation of security assumptions.

No paid external consulting or professional third-party audit is included in this milestone.

---

## Deliverables

### 1. Hardened Stylus Verification Contract

- Input size enforcement and DoS mitigation  
- Deterministic replay protection using monotonic counters  
- Firmware hash validation gating  
- Clear failure-state handling  

---

### 2. Coverage-Guided Fuzz Testing

- `cargo-fuzz` harness targeting receipt validation logic  
- ≥1,000,000 execution cycles  
- Published fuzz logs and reproduction instructions  
- Edge-case documentation  

---

### 3. Cryptographic Parity Validation

- ≥10,000 device ↔ contract test vectors  
- Deterministic hash equivalence proof  
- Reproducible validation scripts  

---

### 4. Gas Benchmark Documentation

- Preliminary benchmark (~45k gas on Arbitrum Sepolia under controlled test conditions)  
- Reproducible benchmark scripts  
- Published cost profile documentation  

---

### 5. Threat Model & Security Documentation

- Attack surface analysis  
- Trust boundary mapping  
- Explicit security assumptions  
- Known limitations & mitigation notes  

---

## Milestone 1 Budget Breakdown

| Category | Cost (USD) |
|-----------|------------|
| Internal Development & Security Hardening | $20,000 |
| Minimal Hardware (3–5 ESP32-S3 boards for validation testing) | $1,000 |
| Contingency (technical remediation buffer) | $3,000 |
| **Total Milestone 1** | **$24,000** |

**Note:**  
No professional third-party audit, paid external review, consulting services, or audit subsidy applications are included in Phase 1.

---

# Milestone 2 — Developer SDK & Integration Tooling (Months 4–6)

**Allocation:** $25,000 USD  
**Scope:** Testnet-only (Arbitrum Sepolia)

## Objective

Deliver integration-ready developer tooling enabling reproducible hardware-to-contract flows on testnet.

---

## Deliverables

### 1. Python SDK (`anchor-verifier`)

- Published to PyPI  
- Async interface with configurable RPC  
- Authorization flow examples  
- Quickstart documentation  

---

### 2. Rust Crate (`stylus-hardware-primitives`)

- Published to crates.io  
- Modular traits:
  - Identity gating  
  - Replay protection  
  - Firmware governance  
- Integration examples  

---

### 3. Reference Integration Templates (3)

Deployable on Sepolia:

- DePIN sensor verification  
- Hardware-bound access control  
- Firmware governance enforcement  

Each template will include step-by-step deployment instructions.

---

### 4. Minimal Developer Dashboard

- Verification event visibility  
- Gas analytics display  
- Load testing with ≥100 simulated devices  
- Documented results  

---

## Milestone 2 Budget Breakdown

| Category | Cost (USD) |
|-----------|------------|
| Internal SDK & Tooling Development | $23,000 |
| Documentation & Technical Writing | $2,000 |
| **Total Milestone 2** | **$25,000** |

**Note:**  
No external consulting, professional audit, or paid third-party services are included in Phase 1.

---

# Phase 1 Summary

- Milestone 1: $24,000 USD  
- Milestone 2: $25,000 USD  

**Total Phase 1 Grant Request: $49,000 USD**  
**Duration: 6 months (testnet-only)**

---

# Completion Criteria (Phase 1)

Phase 1 will be considered complete when:

- Hardened contract version publicly tagged  
- ≥1,000,000 fuzzing executions completed  
- ≥10,000 cryptographic test vectors published  
- Gas benchmarks reproducible by third parties  
- Python SDK published to PyPI  
- Rust crate published to crates.io  
- 3+ reference integrations deployable on Sepolia  

All deliverables will be publicly verifiable through GitHub releases, package registries, and on-chain testnet deployments.

---

# Risk Management (Phase 1)

## Smart Contract Vulnerabilities

Mitigation:

- Coverage-guided fuzz testing  
- Internal security hardening  
- Public repository transparency  
- Professional third-party audit planned for Phase 2 (future grant)

---

## Cryptographic Implementation Risk

Mitigation:

- Deterministic test vectors  
- Cross-platform hash equivalence verification  
- Reproducible validation scripts  

---

## Execution Risk (Solo Founder)

Mitigation:

- Sequential milestone structure  
- Testnet-only scope  
- Clearly bounded deliverables  
- Artifact-based completion metrics  

---

# Phase 2 (Future Grant — Not Included in Current Scope)

Planned future scope (subject to separate grant approval):

- Professional third-party security audit  
- Mainnet deployment  
- Hardware reference design  
- Expanded ecosystem integrations  
- Governance exploration (subject to community approval)  

No Phase 2 budget is included in the current $49,000 USD request.

---

# Strategic Positioning

SHA aims to provide a reusable hardware identity primitive for Stylus-based contracts, enabling secure hardware-bound execution patterns on Arbitrum.

Phase 1 focuses exclusively on:

- Security hardening  
- Testnet validation  
- Developer tooling  

Mainnet deployment and professional audit are explicitly deferred to Phase 2.
