# Technical Challenges & Solutions — Stylus Hardware Anchor

This document outlines the critical engineering hurdles encountered during prototype development, from initial environment setup to on-chain verification.

---

## 1. Cross-Environment Networking (WSL 2 vs. WSL 1)

**Problem:** Initial development on WSL 2 encountered persistent `HTTPClient` timeouts and connection resets when downloading the PlatformIO toolchain and Espressif ESP32-S3 drivers.

**Impact:** Total block on firmware compilation.

**Solution:** Migrated the entire build environment to **WSL 1**. Unlike WSL 2, which uses a virtualized network bridge, WSL 1 shares the native Windows network stack, allowing the build tools to bypass virtual NIC bottlenecks and correctly utilize the system's internet connection.

**Resolution Status:** ✅ Resolved; baseline parity achieved.

---

## 2. Windows UNC Pathing & Permission Conflict

**Problem:** When building through the VS Code UI, PlatformIO attempted to utilize the Windows `cmd.exe` over a UNC path (`\\wsl.localhost\Ubuntu...`). This resulted in `PermissionError: [WinError 5] Access is denied`.

**Impact:** Firmware could not be linked or flashed.

**Solution:** Bypassed the Windows GUI entirely for build tasks. Successfully implemented a **Native Ubuntu Build Flow** where all `pio run` commands are executed directly in the Linux shell, ensuring Linux-native pathing and permission headers.

**Resolution Status:** ✅ Resolved; baseline parity achieved.

---

## 3. Rust Ruint 1.17.2 Dependency Conflict

**Problem:** The Arbitrum Stylus SDK pulled a transitive dependency for `ruint v1.17.2`, which requires the unstable `edition2024` (Cargo edition). The stable Stylus toolchain (Rust 1.82.0) does not yet support this.

**Impact:** Smart contract compilation failed with `feature edition2024 is required`.

**Solution:** Implemented a dependency override using a **Git Patch** in the `Cargo.toml`:

```toml
[patch.crates-io]
ruint = { git = "https://github.com/recmo/uint", tag = "v1.12.3" }
```

This forced the project to use the stable v1.12.3 version, restoring the build.

**Resolution Status:** ✅ Resolved; baseline parity achieved.

---

## 4. Keccak-256 vs. NIST SHA-3 Incompatibility

**Problem:** Most standard ESP32 libraries provide SHA-3. However, Ethereum and Arbitrum Stylus utilize **Keccak-256**. While the algorithms are similar, the padding schemes are different (`0x01` vs `0x06`).

**Impact:** The Hardware ID generated on the chip would never match the digest reconstructed on-chain.

**Solution:** Developed and integrated a custom **Keccak-256 implementation** on the ESP32-S3 that specifically uses the Ethereum-standard padding, ensuring 1:1 parity with the blockchain verifier.

**Resolution Status:** ✅ Resolved; baseline parity achieved.

---

## 5. Stylus SDK API Shift (0.4.x → 0.6.x)

**Problem:** During development, a version jump in the Stylus SDK changed how `StorageU64` maps to native Rust types. The compiler expected `u64` but the SDK provided `Uint<64, 1>`.

**Impact:** Type-mismatch errors during contract verification logic.

**Solution:** Refactored the storage interaction to use explicit type conversions:

```rust
let counter_uint: U64 = U64::from(counter);
let last_counter: U64 = self.counters.get(hw_id);
if counter_uint <= last_counter {
    return Err(b"Replay Detected".to_vec());
}
```

And for reading:

```rust
pub fn get_counter(&self, node_id: FixedBytes<32>) -> u64 {
    let counter_uint: U64 = self.counters.get(node_id);
    counter_uint.try_into().unwrap_or(u64::MAX)
}
```

**Resolution Status:** ✅ Resolved; baseline parity achieved.

---

## 6. Git Credential & SSL Handshaking

**Problem:** The development machine's local ISP/Router configuration caused SSL handshaking failures when cloning large Rust crates via Git.

**Impact:** Incomplete dependency trees.

**Solution:** Implemented global Git overrides and configured Cargo to use the system CLI for fetching, bypassing the internal `libgit2` implementation:

```bash
git config --global url."https://".insteadOf git://
export CARGO_NET_GIT_FETCH_WITH_CLI=true
```

**Resolution Status:** ✅ Resolved; baseline parity achieved.

---

## 7. Cargo Stylus Deployment Workflow

**Problem:** Multiple issues during contract deployment:
- cargo-stylus v0.10.0 (development version) had incomplete `Stylus.toml` schema requirements
- Workspace detection in monorepo structure caused deployment failures
- Missing `rust-toolchain.toml` prevented reproducible builds
- Constructor detection required binary target even for library-only contracts
- Gas price estimation too low for network conditions

**Impact:** Contract deployment blocked despite successful compilation and validation.

**Solution:** Systematic resolution of deployment blockers:

1. **Downgraded to stable version:**
```bash
cargo uninstall cargo-stylus
cargo install cargo-stylus --version 0.6.3
```

2. **Created required configuration files:**

`rust-toolchain.toml`:
```toml
[toolchain]
channel = "1.93.0"
targets = ["wasm32-unknown-unknown"]
```

3. **Added binary target for constructor detection:**

`src/main.rs`:
```rust
fn main() {
    // No constructor - Stylus contract uses storage initialization
}
```

`Cargo.toml`:
```toml
[[bin]]
name = "anchor_anchor"
path = "src/main.rs"
```

4. **Fixed private key format:**
- Created separate `private_key.txt` with only the hex key (no quotes, no variable names)
- Format: `0x<64_character_hex_string>`

5. **Adjusted gas parameters:**
```bash
cargo stylus deploy \
  --private-key-path=./private_key.txt \
  --endpoint=https://sepolia-rollup.arbitrum.io/rpc \
  --no-verify \
  --max-fee-per-gas-gwei=0.1
```

**Resolution Status:** ✅ Fully resolved. Contract successfully deployed and activated at `0x34645ff1dd8af86176fe6b28812aaa4d85e33b0d` on Arbitrum Sepolia.

**Deployment Details:**
- Contract Size: 7.1 KB (compressed)
- Deployment Tx: `0x68d5be22f488320d2e35709104cfc9187a13c1a6428543d3b8a8a79f1d21ce41`
- Activation Tx: `0x2c4d91831c5e6541fec0b35531fb0790ed9ee435653835e0a331e2db6da93910`
- Status: Active and verified on-chain

---

© 2026 Stylus Hardware Anchor · Arbitrum Foundation Grant Submission
