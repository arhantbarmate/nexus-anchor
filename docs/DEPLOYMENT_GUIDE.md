# Stylus Hardware Anchor - Deployment Guide

**Version:** 1.0  
**Target Environment:** Windows 11 + WSL 1 (Ubuntu)  
**Last Updated:** February 8, 2026  
**Scope:** Sepolia prototype deployment (Phase 1 grant is testnet-only). Target production checklist is for Phase 2 (future grant); no mainnet or production deployment in Phase 1.

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Environment Setup](#environment-setup)
4. [Smart Contract Deployment](#smart-contract-deployment)
5. [Firmware Build & Flash](#firmware-build--flash)
6. [Hardware Provisioning](#hardware-provisioning)
7. [On-Chain Authorization](#on-chain-authorization)
8. [End-to-End Testing](#end-to-end-testing)
9. [Troubleshooting](#troubleshooting)
10. [Pre-Production Checklist](#production-checklist)

---

## Overview

This guide walks through deployment of the Stylus Hardware Anchor (Sepolia prototype) on the following stack:

```
┌─────────────────────────────────────────────────────┐
│  Windows 11                                         │
│  └─ WSL 1 (Ubuntu)                                  │
│     ├─ Rust 1.82.0+ (Stylus contract)               │
│     ├─ PlatformIO Core (ESP32-S3 firmware)          │
│     └─ Python 3.10+ (Deployment scripts)            │
└─────────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────┐
│  ESP32-S3-DevKitC-1                                 │
│  - Hardware Identity (eFuse MAC + Chip Info)        │
│  - Custom Keccak-256 (Ethereum-compatible)          │
└─────────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────┐
│  Arbitrum Sepolia Testnet                           │
│  - Contract: 0x34645ff1dd8af86176fe6b28812aaa4d... │
│  - Stylus WASM Smart Contract                       │
└─────────────────────────────────────────────────────┘
```

**Key Deployment Facts:**
- **Network:** Arbitrum Sepolia (testnet)
- **Contract Address:** `0x34645ff1dd8af86176fe6b28812aaa4d85e33b0d`
- **Example Authorization TX:** `0x84aa8ded972c43baefb711089c54d9730f7964e85444596137b76f4e5991551c`

---

## Prerequisites

### System Requirements

#### Operating System
- **Windows 11** with **WSL 1** (Ubuntu)
  
  ⚠️ **CRITICAL:** WSL 1 is required, not WSL 2
  
  **Reason:** WSL 1 provides native network stack access, preventing HTTPClient timeouts when communicating with Arbitrum RPC endpoints.
  
  **Verify WSL Version:**
  ```powershell
  # In PowerShell (Windows)
  wsl --list --verbose
  
  # Expected output:
  #   NAME      STATE           VERSION
  # * Ubuntu    Running         1
  ```
  
  **If you have WSL 2, downgrade to WSL 1:**
  ```powershell
  wsl --set-version Ubuntu 1
  ```

#### Hardware
- **ESP32-S3-DevKitC-1** development board
- USB-C cable (data + power)
- Stable internet connection (see network considerations below)

#### Software Versions

| Tool | Minimum Version | Verified Version | Notes |
|------|-----------------|------------------|-------|
| Rust | 1.82.0 | 1.82.0 | Compatible with ≥1.82.x stable |
| cargo-stylus | 0.5.0 | 0.5.0+ | Tested with 0.5.x–0.6.x |
| PlatformIO Core | 6.0+ | 6.1.15 | CLI-based build system |
| Python | 3.10 | 3.11.6 | Required for scripts |
| web3.py | 6.0+ | 6.11.3 | Ethereum library |

### Network Considerations

⚠️ **Known Issue:** Some ISPs (particularly mobile hotspots) throttle blockchain RPC traffic.

**Symptoms:**
- `cargo stylus check` fails with timeout errors
- Python scripts hang on transaction submission

**Workaround:**
- Use a stable broadband connection
- Consider VPN if persistent issues
- Use alternative RPC endpoints (see troubleshooting)

---

## Environment Setup

### 1. Install WSL 1 (Ubuntu)

```powershell
# In PowerShell (Administrator)

# Install WSL 1
wsl --install --no-distribution

# Install Ubuntu
wsl --install Ubuntu

# Set to WSL 1
wsl --set-default-version 1
wsl --set-version Ubuntu 1

# Verify
wsl --list --verbose
```

### 2. Install Rust & Cargo Stylus

```bash
# In WSL Ubuntu terminal

# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env

# Verify Rust version
rustc --version
# Should show: rustc 1.82.0 or higher

# Install cargo-stylus
cargo install cargo-stylus

# Verify installation
cargo stylus --version
```

### 3. Install PlatformIO Core

```bash
# Install Python 3 and pip (if not already installed)
sudo apt update
sudo apt install python3 python3-pip python3-venv -y

# Install PlatformIO Core
pip3 install platformio

# Add to PATH if needed
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Verify installation
pio --version
# Should show: PlatformIO Core, version 6.1.15 or higher
```

### 4. Install Python Dependencies

```bash
# Install web3.py and dependencies
pip3 install web3 eth-account eth-hash[pycryptodome]

# Verify installation
python3 -c "from web3 import Web3; print('✓ web3.py installed')"
python3 -c "from eth_hash.auto import keccak; print('✓ eth-hash installed')"
```

### 5. Clone Stylus Hardware Anchor Repository

```bash
# Clone the repository
cd ~
git clone https://github.com/your-org/stylus-hardware-anchor.git
cd stylus-hardware-anchor

# Verify directory structure
ls -la
# Expected:
# contracts/
# ohr_firmware/
# scripts/
# verifier/
# docs/
```

---

## Smart Contract Deployment

### 1. Navigate to Contracts Directory

```bash
cd ~/stylus-hardware-anchor/contracts
```

### 2. Review & Fix Dependencies

The contract uses a patched version of `ruint` to bypass Rust edition 2024 conflicts.

**Verify `Cargo.toml` contains BOTH dependency and patch sections:**

```toml
[package]
name = "anchor_anchor"
version = "0.1.0"
edition = "2021"

[dependencies]
stylus-sdk = "0.6.0"
alloy-primitives = "0.7.6"
alloy-sol-types = "0.7.6"

# ⚠️ CRITICAL: Specify exact ruint version with features
ruint = { version = "1.12.3", default-features = false, features = ["alloc"] }

[dev-dependencies]
tokio = { version = "1.12.0", features = ["full"] }
ethers = "2.0"
eyre = "0.6.8"

[features]
export-abi = ["stylus-sdk/export-abi"]

[lib]
crate-type = ["lib", "cdylib"]

# ⚠️ CRITICAL: Patch block MUST be at the end of Cargo.toml
# This prevents edition 2024 conflicts with ruint
[patch.crates-io]
ruint = { version = "1.12.3", default-features = false, features = ["alloc"] }
```

**Why the Patch is Needed:**

Without this patch, you'll get:
```
error: package `ruint v1.12.3` cannot be built because it requires rustc 1.82 or newer,
while the currently active rustc version is 1.82.0
```

The `[patch.crates-io]` block forces Cargo to use the exact version we specify, bypassing Rust edition 2024 pre-release checks.

**Complete Cargo.toml Template:**

Save this as `contracts/Cargo.toml`:

```toml
[package]
name = "anchor_anchor"
version = "0.1.0"
edition = "2021"
license = "MIT"

[dependencies]
stylus-sdk = "0.6.0"
alloy-primitives = { version = "0.7.6", default-features = false }
alloy-sol-types = { version = "0.7.6", default-features = false }
ruint = { version = "1.12.3", default-features = false, features = ["alloc"] }

[dev-dependencies]
tokio = { version = "1.12.0", features = ["full"] }
ethers = "2.0"
eyre = "0.6.8"

[features]
export-abi = ["stylus-sdk/export-abi"]

[lib]
crate-type = ["lib", "cdylib"]

[profile.release]
codegen-units = 1
strip = true
lto = true
panic = "abort"
opt-level = "z"

# CRITICAL: Patch to prevent edition 2024 conflicts
[patch.crates-io]
ruint = { version = "1.12.3", default-features = false, features = ["alloc"] }
```

### 3. Build Contract

```bash
# Build for WASM target
cargo build --release --target wasm32-unknown-unknown

# Expected output:
#    Compiling anchor_anchor v0.1.0 (/home/user/stylus-hardware-anchor/contracts)
#     Finished release [optimized] target(s) in X.XXs
```

**Verify WASM Output:**
```bash
ls -lh target/wasm32-unknown-unknown/release/*.wasm

# Expected: anchor_anchor.wasm (~20-30 KB)
```

### 4. Check Contract Compatibility

```bash
# Run Stylus compatibility check
cargo stylus check --endpoint https://sepolia-rollup.arbitrum.io/rpc

# Expected output:
# Checking contract compatibility...
# ✓ Contract is compatible with Arbitrum Stylus
```

⚠️ **If this fails with network timeout:**
- See [Troubleshooting - Network Issues](#network-issues)
- Try alternative RPC endpoint
- Verify WSL 1 is being used

### 5. Deploy to Arbitrum Sepolia

**⚠️ IMPORTANT:** You need Sepolia ETH for deployment (~0.01 ETH)

Get Sepolia ETH from faucets:
- https://sepolia-faucet.pk910.de/
- https://faucets.chain.link/arbitrum-sepolia

**Cargo Stylus Version Compatibility:**

This guide is tested with `cargo-stylus` 0.5.x–0.6.x. Older versions may require the `--no-verify` flag:

```bash
# For cargo-stylus < 0.5.0
cargo stylus deploy --private-key=$PRIVATE_KEY --endpoint=$RPC_URL --no-verify

# For cargo-stylus ≥ 0.5.0 (recommended)
cargo stylus deploy --private-key=$PRIVATE_KEY --endpoint=$RPC_URL
```

**Deploy Command:**
```bash
# Set environment variables
export PRIVATE_KEY="your_private_key_here"  # WITHOUT 0x prefix
export RPC_URL="https://sepolia-rollup.arbitrum.io/rpc"

# Verify cargo-stylus version
cargo stylus --version
# Should show: cargo-stylus 0.5.0 or higher

# Deploy contract
cargo stylus deploy \
  --private-key=$PRIVATE_KEY \
  --endpoint=$RPC_URL

# Expected output:
# Deploying contract...
# Contract deployed at: 0x34645ff1dd8af86176fe6b28812aaa4d85e33b0d
# Transaction hash: 0x...
```

**Save Contract Address:**
```bash
# Save for later use
export CONTRACT_ADDRESS="0x34645ff1dd8af86176fe6b28812aaa4d85e33b0d"
echo $CONTRACT_ADDRESS > ../CONTRACT_ADDRESS.txt
```

### 6. Verify Deployment

```bash
# Verify contract code exists
python3 << EOF
from web3 import Web3

w3 = Web3(Web3.HTTPProvider('https://sepolia-rollup.arbitrum.io/rpc'))
code = w3.eth.get_code('$CONTRACT_ADDRESS')

if len(code) > 0:
    print(f'✓ Contract deployed: {len(code)} bytes')
else:
    print('✗ Contract not found')
EOF
```

---

## Firmware Build & Flash

### 1. Navigate to Firmware Directory

```bash
cd ~/stylus-hardware-anchor/ohr_firmware
```

**⚠️ IMPORTANT: Firmware File Naming**

PlatformIO expects the main firmware file to be named `main.cpp` in the `src/` directory.

**Correct Structure:**
```
ohr_firmware/
├── src/
│   └── main.cpp              # ← Must be named main.cpp
├── include/
└── platformio.ini
```

**If your file is named differently:**
```bash
# Rename to main.cpp
cd ~/stylus-hardware-anchor/ohr_firmware/src
mv anchor_ohr_esp32_fixed.cpp main.cpp

# Or specify in platformio.ini:
# [env:esp32s3]
# build_src_filter = +<anchor_ohr_esp32_fixed.cpp>
```

For this guide, we assume **standard naming** with `main.cpp`.

### 2. Configure PlatformIO

**Verify `platformio.ini`:**
```ini
[env:esp32s3]
platform = espressif32
board = esp32-s3-devkitc-1
framework = arduino
monitor_speed = 115200

build_flags =
    -DCORE_DEBUG_LEVEL=3
    -DARDUINO_USB_CDC_ON_BOOT=1

monitor_filters = 
    direct
    
upload_speed = 921600
```

### 3. Build Firmware

⚠️ **CRITICAL PATH ISSUE:** PlatformIO may fail with UNC path errors in WSL

**Correct Approach:**
```bash
# Run from WSL Ubuntu (not Windows terminal)
cd ~/stylus-hardware-anchor/ohr_firmware

# Build
pio run

# Expected output:
# Building in release mode
# RAM:   [=         ]  XX.X% (used XXXXX bytes from XXXXXX bytes)
# Flash: [===       ]  XX.X% (used XXXXXX bytes from XXXXXXX bytes)
# ========================= [SUCCESS] Took X.XX seconds =========================
```

**If you get UNC path error:**
```
Error: The filename, directory name, or volume label syntax is incorrect: '\\\\wsl$\\...'
```

**Fix:**
```bash
# Ensure you're in native WSL path (NOT /mnt/c/...)
pwd
# Should show: /home/username/stylus-hardware-anchor/ohr_firmware

# If in /mnt/c/, move project:
cp -r /mnt/c/Users/YourName/stylus-hardware-anchor ~/
cd ~/stylus-hardware-anchor/ohr_firmware
```

### 4. Connect ESP32-S3

```bash
# Connect ESP32-S3 via USB-C cable

# Find serial port
ls /dev/ttyUSB* /dev/ttyACM*

# Common ports:
# /dev/ttyUSB0  (CP2102 USB-Serial chip)
# /dev/ttyACM0  (Native USB CDC)

# If no ports visible, install drivers:
# sudo apt install brltty-
# sudo usermod -a -G dialout $USER
# newgrp dialout
```

### 5. Flash Firmware

```bash
# Flash to ESP32-S3
pio run --target upload

# Expected output:
# Uploading .pio/build/esp32s3/firmware.bin
# esptool.py v4.5.1
# Serial port /dev/ttyUSB0
# Connecting....
# Chip is ESP32-S3 (revision v0.1)
# ...
# Hash of data verified.
# 
# Leaving...
# Hard resetting via RTS pin...
# ========================= [SUCCESS] Took X.XX seconds =========================
```

### 6. Monitor Serial Output

```bash
# Open serial monitor
pio device monitor --baud 115200

# Expected output:
# ═══════════════════════════════════════════════════════════
#   anchorAnchor OHR - Hardware Identity & Receipt System
#   Version: Phase-2 Security Audit Compliant
# ═══════════════════════════════════════════════════════════
# ✓ NVS initialized
# 
# ╔═══════════════════════════════════════════════════════════════╗
# ║          anchor OHR SECURITY STATUS REPORT                    ║
# ╠═══════════════════════════════════════════════════════════════╣
# ║ Chip: esp32s3                                                 ║
# ║ Unique ID: ✓ eFuse-backed                                ║
# ║ Secure Boot: ⚠️  DISABLED (development mode)                 ║
# ║ Flash Encryption: ⚠️  DISABLED (NVS vulnerable)              ║
# ║ Keccak-256: see note below (use Ethereum 0x01 padding)           ║
# ╠═══════════════════════════════════════════════════════════════╣
# ║ Status: ⚠️  DEVELOPMENT BUILD (security features pending)    ║
# ╚═══════════════════════════════════════════════════════════════╝
# 
# Hardware Identity: 0xABCDEF1234567890...

**Note on Keccak Implementation:**

Current prototype firmware uses Ethereum-compatible Keccak-256 (0x01 padding); baseline parity is achieved across firmware, Python, and Stylus. Domain tag is 13 bytes (`"anchor_RCT_V1"`); receipt material is 117 bytes.

**For target production deployment:**

Ensure Keccak-256 remains Ethereum-compatible before any mainnet use (mainnet is out of scope for Phase 1; planned for Phase 2). See `SECURITY_AUDIT_COMPLIANCE.md` for:
- Recommended Keccak libraries (tiny-keccak, XKCP)
- Test vectors for verification
- Integration instructions
```

---

## Hardware Provisioning

### 1. Extract Hardware Identity

**Via Serial Monitor:**
```bash
# The hardware identity is displayed on boot
# Look for line:
# Hardware Identity: 0x[64 hex characters]

# Example:
# Hardware Identity: 0x52fdfc072182654f163f5f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f
```

**Copy this value** - you'll need it for authorization.

**Save to file:**
```bash
# From another terminal (while monitor is running)
cd ~/stylus-hardware-anchor

# Extract from serial output
pio device monitor --baud 115200 2>&1 | grep "Hardware Identity" | head -1 | awk '{print $3}' > HARDWARE_ID.txt

cat HARDWARE_ID.txt
# Should show: 0x52fdfc...
```

### 2. Understanding Hardware Identity

The hardware identity is derived from:

```
Hardware Identity = Keccak256(
    eFuse_MAC (6 bytes)        || // Base MAC address
    Chip_Model (1 byte)         || // ESP32-S3 = 9
    Chip_Revision (1 byte)      || // Silicon revision
    Zero_Padding (8 bytes)         // Fixed padding
)
```

**🔴 CRITICAL: Keccak Implementation Mismatch**

⚠️ **THIS WILL CAUSE VERIFICATION FAILURES IN PROTOTYPE DEPLOYMENT**

**The Problem:**
- **ESP32 Firmware:** Must use Ethereum Keccak-256 (0x01 padding) for parity with verifier and contract
- **Python Scripts:** Use Ethereum Keccak-256 (`web3.py` / `eth-hash`)
- **Smart Contract:** Expects Ethereum Keccak-256 (Stylus)

**Different hash functions = Different hardware IDs**

**What This Means for You:**

| Operation | Status | Reason |
|-----------|--------|--------|
| Extract Hardware ID | ✅ Works | ESP32 computes with SHA3 |
| Authorize on-chain | ✅ Works | You authorize whatever ID firmware outputs |
| Generate Receipt | ✅ Works | ESP32 uses SHA3 consistently |
| **Verify Receipt** | ❌ **FAILS** | Python/Contract use Keccak, ESP32 uses SHA3 |

**Step-by-Step Solution:**

**Option A: Accept Limitation for Prototype (Development Only)**

1. **Extract hardware ID** from ESP32 (SHA3-based)
2. **Authorize that ID** on-chain (stores SHA3 result)
3. **Generate receipts** on ESP32 (uses SHA3 consistently)
4. ⚠️ **Skip receipt verification testing** until Keccak is implemented
5. **Document:** "Sepolia prototype deployed; Milestone 1 security hardening pending approval"

**Option B: Implement Ethereum Keccak Immediately**

1. **Replace firmware hash function:**
   ```cpp
   // Use tiny-keccak or XKCP instead of mbedTLS
   #include "keccak-tiny.h"  // Ethereum-compatible
   ```

2. **Rebuild firmware**
3. **Flash updated firmware**
4. **Extract NEW hardware ID** (now Keccak-based)
5. **Re-authorize** on-chain with Keccak-based ID
6. **Test full verification** (now works end-to-end)

**Recommended Approach for This Guide:**

Follow **Option A** for now. The hardware identity you extract is still:
- ✅ **Unique** per device
- ✅ **Stable** across reboots
- ✅ **Valid** for authorization testing

You just won't be able to test receipt verification until Keccak is upgraded.

**When to Upgrade:**

Before target production deployment, Option B (Ethereum Keccak in firmware) must be implemented if not already present. See `SECURITY_AUDIT_COMPLIANCE.md` Section "Critical Issue #1" for implementation guide.

**Current Status:** The hardware identity is still **unique and stable** (same eFuse inputs), but digest computation differs from Ethereum standard.

**Properties:**
- ✅ Unique per physical device
- ✅ Cannot be changed (eFuse is immutable)
- ✅ Same value after every reboot
- ⚠️ Hash function must match Ethereum Keccak for mainnet/production use
- ⚠️ Different firmware = same hardware ID (identity is hardware-based, not firmware-based)

### 3. Verify Identity Stability

```bash
# Reset ESP32-S3 (press RESET button)
# Or power cycle:
pio device monitor --baud 115200

# Hardware identity should be IDENTICAL after reboot
# If it changes, there's a firmware bug
```

---

## On-Chain Authorization

### 1. Prepare Authorization Script

**Create/Verify `scripts/authorize_hardware.py`:**

```python
#!/usr/bin/env python3
"""
Stylus Hardware Anchor - Hardware Authorization Script
Authorizes ESP32-S3 hardware identity on-chain
"""

import sys
import argparse
from web3 import Web3
from eth_account import Account

# Arbitrum Sepolia RPC
RPC_URL = "https://sepolia-rollup.arbitrum.io/rpc"

# Contract address (deployed earlier)
CONTRACT_ADDRESS = "0x34645ff1dd8af86176fe6b28812aaa4d85e33b0d"

# Minimal ABI (just authorize_node function)
ABI = [
    {
        "inputs": [{"internalType": "bytes32", "name": "hw_id", "type": "bytes32"}],
        "name": "authorize_node",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "bytes32", "name": "hw_id", "type": "bytes32"}],
        "name": "is_node_authorized",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    }
]

def authorize_hardware(hw_id_hex: str, private_key: str) -> str:
    """Authorize hardware identity on-chain"""
    
    # Connect to Arbitrum
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    
    if not w3.is_connected():
        raise Exception(f"Failed to connect to {RPC_URL}")
    
    print(f"✓ Connected to Arbitrum Sepolia")
    print(f"  Chain ID: {w3.eth.chain_id}")
    print(f"  Block: {w3.eth.block_number}")
    
    # Load contract
    contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=ABI)
    
    # Setup account
    account = Account.from_key(private_key)
    print(f"\n✓ Account loaded: {account.address}")
    
    # Check balance
    balance = w3.eth.get_balance(account.address)
    balance_eth = w3.from_wei(balance, 'ether')
    print(f"  Balance: {balance_eth} ETH")
    
    if balance == 0:
        raise Exception("Account has no ETH. Get testnet ETH from faucet.")
    
    # Parse hardware ID
    hw_id_bytes = bytes.fromhex(hw_id_hex.replace('0x', ''))
    
    if len(hw_id_bytes) != 32:
        raise Exception(f"Hardware ID must be 32 bytes (64 hex chars), got {len(hw_id_bytes)}")
    
    print(f"\n✓ Hardware ID: {hw_id_hex}")
    
    # Check if already authorized
    is_authorized = contract.functions.is_node_authorized(hw_id_bytes).call()
    
    if is_authorized:
        print(f"\n⚠️  Hardware already authorized")
        return None
    
    # Build transaction
    print(f"\n⏳ Building authorization transaction...")
    
    tx = contract.functions.authorize_node(hw_id_bytes).build_transaction({
        'from': account.address,
        'nonce': w3.eth.get_transaction_count(account.address),
        'gas': 100000,
        'gasPrice': w3.eth.gas_price
    })
    
    # Sign transaction
    signed_tx = account.sign_transaction(tx)
    
    # Send transaction
    print(f"⏳ Sending transaction...")
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    
    print(f"✓ Transaction sent: {tx_hash.hex()}")
    print(f"  Waiting for confirmation...")
    
    # Wait for receipt
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    
    if receipt['status'] == 1:
        print(f"\n✓ SUCCESS: Hardware authorized!")
        print(f"  Transaction: {tx_hash.hex()}")
        print(f"  Block: {receipt['blockNumber']}")
        print(f"  Gas used: {receipt['gasUsed']}")
        
        # Verify authorization
        is_authorized = contract.functions.is_node_authorized(hw_id_bytes).call()
        print(f"  Authorization verified: {is_authorized}")
        
        return tx_hash.hex()
    else:
        raise Exception(f"Transaction failed: {receipt}")

def main():
    parser = argparse.ArgumentParser(description='Authorize ESP32-S3 hardware on Stylus Hardware Anchor')
    parser.add_argument('--hw-id', required=True, help='Hardware identity (0x...)')
    parser.add_argument('--private-key', help='Private key (or use PRIVATE_KEY env var)')
    
    args = parser.parse_args()
    
    # Get private key
    private_key = args.private_key or os.environ.get('PRIVATE_KEY')
    
    if not private_key:
        print("Error: --private-key required or set PRIVATE_KEY env var")
        sys.exit(1)
    
    # Remove 0x prefix if present
    if private_key.startswith('0x'):
        private_key = private_key[2:]
    
    try:
        tx_hash = authorize_hardware(args.hw_id, private_key)
        
        if tx_hash:
            print(f"\n{'='*70}")
            print(f"  HARDWARE AUTHORIZATION COMPLETE")
            print(f"{'='*70}")
            print(f"\nYour ESP32-S3 is now authorized to submit receipts!")
            print(f"\nNext steps:")
            print(f"  1. Approve firmware hash")
            print(f"  2. Generate test receipt")
            print(f"  3. Verify receipt on-chain")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    import os
    main()
```

### 2. Set Environment Variables

```bash
# Set your private key (WITHOUT 0x prefix)
export PRIVATE_KEY="your_private_key_here"

# Verify it's set
echo ${PRIVATE_KEY:0:10}...  # Shows first 10 chars
```

### 3. Run Authorization

```bash
cd ~/stylus-hardware-anchor

# Read hardware ID from file (or copy manually)
HW_ID=$(cat HARDWARE_ID.txt)

# Authorize hardware
python3 scripts/authorize_hardware.py --hw-id $HW_ID

# Expected output:
# ✓ Connected to Arbitrum Sepolia
#   Chain ID: 421614
#   Block: 123456
# 
# ✓ Account loaded: 0xYourAddress
#   Balance: 0.05 ETH
# 
# ✓ Hardware ID: 0x52fdfc072182654f163f5f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f0f
# 
# ⏳ Building authorization transaction...
# ⏳ Sending transaction...
# ✓ Transaction sent: 0x84aa8ded972c43baefb711089c54d9730f7964e85444596137b76f4e5991551c
#   Waiting for confirmation...
# 
# ✓ SUCCESS: Hardware authorized!
#   Transaction: 0x84aa8ded972c43baefb711089c54d9730f7964e85444596137b76f4e5991551c
#   Block: 123457
#   Gas used: 48723
#   Authorization verified: True
```

### 4. Verify Authorization

```bash
# Query contract to verify
python3 << EOF
from web3 import Web3

w3 = Web3(Web3.HTTPProvider('https://sepolia-rollup.arbitrum.io/rpc'))

ABI = [{"inputs": [{"internalType": "bytes32", "name": "hw_id", "type": "bytes32"}], "name": "is_node_authorized", "outputs": [{"internalType": "bool", "name": "", "type": "bool"}], "stateMutability": "view", "type": "function"}]

contract = w3.eth.contract(address='$CONTRACT_ADDRESS', abi=ABI)

hw_id = bytes.fromhex('${HW_ID:2}')  # Remove 0x
is_authorized = contract.functions.is_node_authorized(hw_id).call()

print(f"Hardware ID: $HW_ID")
print(f"Authorized: {is_authorized}")
EOF
```

**View on Block Explorer:**
```
https://sepolia.arbiscan.io/tx/0x84aa8ded972c43baefb711089c54d9730f7964e85444596137b76f4e5991551c
```

---

## End-to-End Testing

**⚠️ CRITICAL LIMITATION FOR PROTOTYPE:**

Due to the Keccak implementation mismatch (ESP32 uses SHA3, verifier uses Keccak), **full receipt verification testing will fail**. This is expected and documented.

**What You CAN Test (Prototype):**
- ✅ Hardware identity extraction
- ✅ Hardware authorization on-chain
- ✅ Receipt generation on ESP32
- ✅ JSON formatting
- ✅ Counter increment

**What You CANNOT Test (Until Keccak Upgrade):**
- ❌ Receipt digest verification
- ❌ On-chain receipt submission
- ❌ Python canonical verifier (digest check will fail)

**Proceed with testing understanding this limitation.**

### 1. Generate Test Receipt

The firmware automatically generates a test receipt on boot.

**From Serial Monitor:**
```
═══════════════════════════════════════════════════════════
           anchor OHR ATTESTATION RECEIPT
═══════════════════════════════════════════════════════════
{
  "receipt_digest": "0x1234567890abcdef...",
  "hardware_identity": "0x52fdfc072182654f...",
  "counter": 1
}
═══════════════════════════════════════════════════════════
```

**⚠️ Note:** This receipt digest is computed with SHA3-256, not Ethereum Keccak-256.

### 2. Capture Receipt JSON

```bash
# Capture receipt from serial
pio device monitor --baud 115200 2>&1 | grep -A 5 "receipt_digest" > test_receipt.json

# Clean up JSON
cat test_receipt.json
```

### 3. Verify Receipt with Python Verifier (⚠️ Expected to Fail)

```bash
cd ~/stylus-hardware-anchor/verifier

# This WILL FAIL due to Keccak mismatch - this is EXPECTED
python3 anchor_canonical_verifier.py
```

**Expected Output:**
```
[4/4] ✗ Digest Reconstruction Failed
      Expected: 0xabcd1234... (computed with Keccak)
      Received: 0x5678efgh... (computed with SHA3)

❌ REJECTED: Receipt digest mismatch - Tampering Detected
```

**This is CORRECT behavior** because:
1. ESP32 computes digest with SHA3-256
2. Python verifier recomputes with Ethereum Keccak-256
3. Different hash functions = different digests
4. Verifier correctly rejects mismatched digest

**To "Pass" This Test:**

You must first implement Ethereum Keccak-256 in firmware. See `SECURITY_AUDIT_COMPLIANCE.md` Section "Critical Issue #1" for step-by-step Keccak implementation guide.

### 4. Submit Receipt to Blockchain (Skip Until Keccak Fixed)

```bash
# DO NOT RUN THIS YET - will fail with same Keccak mismatch
# Uncomment after Keccak upgrade:

# python3 scripts/submit_receipt.py \
#   --hw-id $HW_ID \
#   --receipt test_receipt.json
```

**Prototype Testing Complete:**

If you've successfully:
- ✅ Extracted hardware identity
- ✅ Authorized it on-chain
- ✅ Generated a receipt
- ✅ Observed the expected Keccak mismatch error

Then **prototype deployment is complete**. The Keccak mismatch is a known limitation, not a bug.

**Next Milestone:** Implement Ethereum Keccak-256 to enable full end-to-end verification.

---

## Troubleshooting

### Common Issues & Solutions

#### 1. WSL 1 vs WSL 2 Issues

**Problem:**
```
Error: Connection timeout to Arbitrum RPC
cargo stylus check fails
```

**Solution:**
```powershell
# In PowerShell (Administrator)
wsl --set-version Ubuntu 1

# Restart WSL
wsl --shutdown
wsl
```

**Verification:**
```powershell
wsl --list --verbose
# Ensure VERSION shows 1, not 2
```

#### 2. UNC Path Error (PlatformIO)

**Problem:**
```
Error: The filename, directory name, or volume label syntax is incorrect: '\\\\wsl$\\...'
```

**Root Cause:** Project is in `/mnt/c/` (Windows filesystem accessed via WSL)

**Solution:**
```bash
# Move project to native WSL filesystem
cp -r /mnt/c/Users/YourName/stylus-hardware-anchor ~/
cd ~/stylus-hardware-anchor/ohr_firmware

# Rebuild
pio run
```

#### 3. Network Timeout (ISP Throttling)

**Problem:**
```
cargo stylus check
Error: request timed out
```

**Root Cause:** ISP (especially mobile hotspots) throttles blockchain RPC traffic

**Solutions:**

A. **Try Alternative RPC Endpoint:**
```bash
export RPC_URL="https://arbitrum-sepolia.publicnode.com"
cargo stylus check --endpoint $RPC_URL
```

B. **Use VPN:**
```bash
# Install VPN client
sudo apt install openvpn

# Or use commercial VPN service
```

C. **Switch Network:**
- Try different WiFi network
- Use wired Ethernet if available
- Avoid mobile hotspots for deployment

#### 4. No Serial Port Detected

**Problem:**
```
ls /dev/ttyUSB*
ls: cannot access '/dev/ttyUSB*': No such file or directory
```

**Solution:**
```bash
# Remove brltty (conflicts with CP2102)
sudo apt remove brltty

# Add user to dialout group
sudo usermod -a -G dialout $USER

# Apply group changes
newgrp dialout

# Reconnect ESP32-S3

# Check again
ls /dev/ttyUSB* /dev/ttyACM*
```

#### 5. Rust Edition 2024 Conflict

**Problem:**
```
error: package `ruint v1.12.3` cannot be built because it requires rustc 1.82 or newer
```

**Solution:**

Already fixed in `Cargo.toml`:
```toml
[dependencies]
ruint = { version = "1.12.3", default-features = false, features = ["alloc"] }
```

If still occurs:
```bash
# Update Rust
rustup update stable

# Clean and rebuild
cargo clean
cargo build --release --target wasm32-unknown-unknown
```

#### 6. Insufficient Testnet ETH

**Problem:**
```
Error: insufficient funds for gas * price + value
```

**Solution:**

Get Sepolia ETH from faucets:

**Arbitrum Sepolia Faucets:**
1. https://sepolia-faucet.pk910.de/
   - Bridge Sepolia ETH to Arbitrum Sepolia
   
2. https://faucets.chain.link/arbitrum-sepolia
   - Direct Arbitrum Sepolia ETH
   
3. https://www.alchemy.com/faucets/arbitrum-sepolia
   - Requires Alchemy account

**Amount Needed:**
- Contract deployment: ~0.005 ETH
- Authorization: ~0.001 ETH per node
- Receipt verification: ~0.0002 ETH per receipt

#### 7. Hardware ID Changes After Reboot

**Problem:**
```
Hardware Identity: 0xABCD... (different each time)
```

**Root Cause:** Firmware bug in identity derivation

**Debug Steps:**
```bash
# Enable verbose logging
# In firmware, check:
# - eFuse MAC reading
# - Chip info reading
# - Hash computation

# Verify eFuse stability
esptool.py --port /dev/ttyUSB0 summary | grep MAC
# Should be same every time
```

#### 8. Receipt Verification Fails

**Problem:**
```
verify_attestation() → False
Message: "Receipt digest mismatch"
```

**Common Causes:**

A. **Keccak Implementation Mismatch**
- Firmware must use Ethereum Keccak-256 (0x01) for digest parity
- Verifier uses Ethereum Keccak-256
- **Fix:** Replace firmware hash function with true Keccak

B. **Counter Mismatch**
- On-chain counter is ahead of device
- **Fix:** Check counter state, may need to reset

C. **Hardware ID Not Authorized**
```
Message: "Unauthorized hardware identity"
```
- **Fix:** Re-run authorization script

#### 9. Serial Monitor Shows Garbage

**Problem:**
```
pio device monitor
��������������������
```

**Solution:**
```bash
# Wrong baud rate
pio device monitor --baud 115200

# Or reset ESP32-S3 after opening monitor
# (Press RESET button on board)
```

#### 10. Cannot Build Contract on Windows

**Problem:**
```
cargo build fails with Windows-specific errors
```

**Solution:**
- **Always use WSL 1 Ubuntu** for Rust/Stylus builds
- Never run `cargo stylus` from Windows Command Prompt or PowerShell
- All blockchain tooling should be in WSL

---

## Prototype Success Criteria

**Goal:** Deploy and test the core prototype infrastructure with known Keccak limitation.

### ✅ What Success Looks Like

You have completed prototype deployment if:

1. **Smart Contract Deployed** ✅
   - Contract deployed to Arbitrum Sepolia
   - Contract address recorded
   - Verified on Arbiscan (code visible)

2. **Firmware Flashed** ✅
   - ESP32-S3 boots successfully
   - Serial output shows hardware identity
   - Hardware identity is stable across reboots

3. **Hardware Authorized** ✅
   - `authorize_hardware.py` transaction confirmed
   - `is_node_authorized()` returns `true`
   - Transaction visible on Arbiscan

4. **Receipt Generated** ✅
   - ESP32 generates test receipt
   - JSON format correct
   - Counter increments on each boot

5. **Keccak Mismatch Observed** ✅
   - Python verifier rejects receipt with "digest mismatch"
   - You understand this is expected behavior
   - You know this will be addressed in future hardening

### ⚠️ Known Limitations (Acceptable for Prototype)

| Limitation | Status | Fix Required |
|------------|--------|--------------|
| **Keccak Mismatch** | Expected | Future hardening: Replace SHA3 with Ethereum Keccak |
| **No Secure Boot** | Expected | Future hardening: Enable Secure Boot V2 |
| **No Flash Encryption** | Expected | Future hardening: Enable flash encryption |
| **Receipt Verification Fails** | Expected | Future hardening: After Keccak upgrade |

### 🎯 Future Hardening Objectives

To unlock full verification:

1. **Implement Ethereum Keccak-256** (CRITICAL)
   - Replace mbedTLS SHA3 in firmware
   - Use tiny-keccak or XKCP library
   - Verify with test vectors

2. **Re-flash Firmware**
   - Build with new Keccak implementation
   - Flash to ESP32-S3

3. **Extract NEW Hardware ID**
   - Identity will change (different hash function)
   - Save new ID

4. **Re-authorize on Blockchain**
   - Authorize new Keccak-based identity
   - Can keep old SHA3 identity for comparison

5. **Test Full Verification**
   - Receipt verification now passes
   - On-chain submission works
   - End-to-end flow complete

### 📊 Prototype vs Future Hardening Comparison

| Feature | Prototype (Current) | Future Hardening (Planned) |
|---------|----------------------|-------------------|
| Hardware Identity | Keccak-256 (parity achieved) | Audited / formally verified |
| Authorization | ✅ Works | ✅ Works |
| Receipt Generation | ✅ Works | ✅ Works |
| Receipt Verification | ✅ Works (parity achieved) | ✅ Works (audited) |
| On-chain Submission | ✅ Works (Sepolia) | Planned for Phase 2 (future grant) |
| Audit-prepared | ❌ No (prototype) | ⚠️ Partial (contingent on Milestone 3 security) |

---

## Pre-Production / Deployment Checklist

### Pre-Deployment Verification

- [ ] **WSL 1 Confirmed**
  ```powershell
  wsl --list --verbose  # Shows VERSION = 1
  ```

- [ ] **Rust Version Correct**
  ```bash
  rustc --version  # ≥1.82.0
  ```

- [ ] **PlatformIO Working**
  ```bash
  pio run  # Builds successfully
  ```

- [ ] **Network Stable**
  ```bash
  ping -c 4 sepolia-rollup.arbitrum.io
  # No packet loss
  ```

- [ ] **Testnet ETH Available**
  ```bash
  # Check balance > 0.01 ETH
  ```

### Deployment Steps Completed

- [ ] **Contract Deployed**
  - [ ] `cargo stylus deploy` succeeded
  - [ ] Contract address saved: `$CONTRACT_ADDRESS`
  - [ ] Contract verified on Arbiscan

- [ ] **Firmware Flashed**
  - [ ] `pio run --target upload` succeeded
  - [ ] Serial monitor shows boot messages
  - [ ] Hardware identity extracted

- [ ] **Hardware Authorized**
  - [ ] `authorize_hardware.py` ran successfully
  - [ ] Transaction confirmed on-chain
  - [ ] Authorization verified with `is_node_authorized()`

- [ ] **Firmware Approved** (if needed)
  - [ ] Firmware hash computed
  - [ ] `approve_firmware()` called on contract
  - [ ] Approval verified

### Testing Completed

- [ ] **Receipt Generation**
  - [ ] Test receipt generated on ESP32
  - [ ] JSON format correct
  - [ ] Counter increments properly

- [ ] **Off-Chain Verification**
  - [ ] Python verifier runs
  - [ ] All 4 checks pass
  - [ ] Replay attack rejected

- [ ] **On-Chain Verification** (optional for testing)
  - [ ] `verify_receipt()` called
  - [ ] Transaction successful
  - [ ] Counter updated on-chain

### Documentation

- [ ] **Hardware ID Recorded**
  ```bash
  cat HARDWARE_ID.txt
  ```

- [ ] **Contract Address Recorded**
  ```bash
  cat CONTRACT_ADDRESS.txt
  ```

- [ ] **Authorization TX Recorded**
  ```
  https://sepolia.arbiscan.io/tx/0x84aa8ded...
  ```

---

## Next Steps

### Immediate (Before Target Production)

1. **⚠️ CRITICAL: Implement Ethereum Keccak-256**
   
   **Why:** Digest must match Ethereum Keccak-256 (0x01 padding). Mismatched hash implementation will cause verification failures.
   
   **Action Required:**
   ```bash
   # Replace mbedTLS SHA3 with Ethereum Keccak
   # Recommended libraries:
   # - tiny-keccak: https://github.com/coruus/keccak-tiny
   # - XKCP: https://github.com/XKCP/XKCP
   # - eth-keccak: Ethereum-specific implementations
   ```
   
   **Verification:**
   ```python
   # Test vector: empty string
   from eth_hash.auto import keccak
   assert keccak(b"").hex() == "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470"
   ```
   
   See `SECURITY_AUDIT_COMPLIANCE.md` for complete implementation guide.

### For Development

2. **Enable Secure Boot**
   - Configure ESP32-S3 Secure Boot V2
   - Sign firmware binaries
   - Extract real secure boot key digest

3. **Enable Flash Encryption**
   - Protect NVS counter storage
   - Prevent physical attacks
   - Enable NVS encryption

### For Target Production

4. **Deploy to Mainnet** (Phase 2 — not in Phase 1 scope; planned for future grant)
   - Use Arbitrum One
   - Implement multi-sig ownership
   - Set up monitoring

5. **Hardware Fleet Management**
   - Batch authorization
   - Firmware version tracking
   - Automated provisioning

6. **Monitoring & Alerts**
   - Track receipt submissions
   - Monitor gas costs
   - Alert on anomalies

---

## Quick Reference

### Essential Commands

```bash
# Build contract
cd ~/stylus-hardware-anchor/contracts
cargo stylus check --endpoint https://sepolia-rollup.arbitrum.io/rpc

# Build firmware
cd ~/stylus-hardware-anchor/ohr_firmware
pio run

# Flash firmware
pio run --target upload

# Monitor serial
pio device monitor --baud 115200

# Authorize hardware
python3 scripts/authorize_hardware.py --hw-id 0x...

# Run verifier
cd ~/stylus-hardware-anchor/verifier
python3 anchor_canonical_verifier.py
```

### Key Files

| File | Purpose | Location |
|------|---------|----------|
| `lib.rs` | Smart contract | `contracts/src/` |
| `anchor_ohr_esp32_fixed.cpp` | Firmware | `ohr_firmware/src/` |
| `authorize_hardware.py` | Authorization script | `scripts/` |
| `anchor_canonical_verifier.py` | Off-chain verifier | `verifier/` |
| `HARDWARE_ID.txt` | Your ESP32 identity | Project root |
| `CONTRACT_ADDRESS.txt` | Deployed contract | Project root |

### Important Addresses

| Item | Address |
|------|---------|
| **Contract (Sepolia)** | `0x34645ff1dd8af86176fe6b28812aaa4d85e33b0d` |
| **Example Auth TX** | `0x84aa8ded972c43baefb711089c54d9730f7964e85444596137b76f4e5991551c` |
| **Arbiscan (Sepolia)** | https://sepolia.arbiscan.io/ |

### Support Resources

- **Architecture:** `ARCHITECTURE.md`
- **Security Audit:** `SECURITY_AUDIT_COMPLIANCE.md`
- **Verifier Spec:** `anchor_CANONICAL_VERIFIER_SPEC.md`
- **Production Guide:** `PRODUCTION_DEPLOYMENT_GUIDE.md`

---

## Appendix A: Complete Authorization Script

Save as `scripts/authorize_hardware.py`:

```python
#!/usr/bin/env python3
"""
Stylus Hardware Anchor - Hardware Authorization Script
Complete implementation for authorizing ESP32-S3 devices
"""

import sys
import os
import argparse
from web3 import Web3
from eth_account import Account

# Configuration
RPC_URL = "https://sepolia-rollup.arbitrum.io/rpc"
CONTRACT_ADDRESS = "0x34645ff1dd8af86176fe6b28812aaa4d85e33b0d"

# Minimal ABI
ABI = [
    {
        "inputs": [{"internalType": "bytes32", "name": "hw_id", "type": "bytes32"}],
        "name": "authorize_node",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "bytes32", "name": "hw_id", "type": "bytes32"}],
        "name": "is_node_authorized",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    }
]

def authorize_hardware(hw_id_hex: str, private_key: str) -> str:
    """Authorize hardware identity on-chain"""
    
    print("="*70)
    print("  anchor PROTOCOL - HARDWARE AUTHORIZATION")
    print("="*70)
    print()
    
    # Connect to Arbitrum
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    
    if not w3.is_connected():
        raise Exception(f"Failed to connect to {RPC_URL}")
    
    print(f"✓ Connected to Arbitrum Sepolia")
    print(f"  RPC: {RPC_URL}")
    print(f"  Chain ID: {w3.eth.chain_id}")
    print(f"  Block: {w3.eth.block_number}")
    
    # Load contract
    contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=ABI)
    print(f"\n✓ Contract loaded: {CONTRACT_ADDRESS}")
    
    # Setup account
    account = Account.from_key(private_key)
    print(f"\n✓ Account: {account.address}")
    
    # Check balance
    balance = w3.eth.get_balance(account.address)
    balance_eth = w3.from_wei(balance, 'ether')
    print(f"  Balance: {balance_eth} ETH")
    
    if balance == 0:
        raise Exception("Insufficient ETH. Get testnet ETH from faucet.")
    
    # Parse hardware ID
    hw_id_bytes = bytes.fromhex(hw_id_hex.replace('0x', ''))
    
    if len(hw_id_bytes) != 32:
        raise Exception(f"Hardware ID must be 32 bytes (64 hex chars), got {len(hw_id_bytes)}")
    
    print(f"\n✓ Hardware ID: {hw_id_hex}")
    
    # Check if already authorized
    is_authorized = contract.functions.is_node_authorized(hw_id_bytes).call()
    
    if is_authorized:
        print(f"\n⚠️  Hardware already authorized")
        print(f"  No transaction needed")
        return None
    
    # Build transaction
    print(f"\n⏳ Building authorization transaction...")
    
    nonce = w3.eth.get_transaction_count(account.address)
    gas_price = w3.eth.gas_price
    
    tx = contract.functions.authorize_node(hw_id_bytes).build_transaction({
        'from': account.address,
        'nonce': nonce,
        'gas': 100000,
        'gasPrice': gas_price
    })
    
    estimated_cost = w3.from_wei(tx['gas'] * tx['gasPrice'], 'ether')
    print(f"  Estimated cost: {estimated_cost} ETH")
    
    # Sign transaction
    signed_tx = account.sign_transaction(tx)
    
    # Send transaction
    print(f"\n⏳ Sending transaction...")
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    
    print(f"✓ Transaction sent!")
    print(f"  TX Hash: {tx_hash.hex()}")
    print(f"  Explorer: https://sepolia.arbiscan.io/tx/{tx_hash.hex()}")
    print(f"\n⏳ Waiting for confirmation (this may take 10-30 seconds)...")
    
    # Wait for receipt
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    
    if receipt['status'] == 1:
        print(f"\n{'='*70}")
        print(f"  ✓ SUCCESS: HARDWARE AUTHORIZED")
        print(f"{'='*70}")
        print(f"\nTransaction Details:")
        print(f"  Hash: {tx_hash.hex()}")
        print(f"  Block: {receipt['blockNumber']}")
        print(f"  Gas Used: {receipt['gasUsed']:,}")
        print(f"  Actual Cost: {w3.from_wei(receipt['gasUsed'] * gas_price, 'ether')} ETH")
        
        # Verify authorization
        is_authorized = contract.functions.is_node_authorized(hw_id_bytes).call()
        print(f"\n✓ Authorization Verified: {is_authorized}")
        
        return tx_hash.hex()
    else:
        raise Exception(f"Transaction failed with status: {receipt['status']}")

def main():
    parser = argparse.ArgumentParser(
        description='Authorize ESP32-S3 hardware on Stylus Hardware Anchor',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Using environment variable for private key
  export PRIVATE_KEY="your_private_key"
  python3 authorize_hardware.py --hw-id 0x52fdfc...
  
  # Using command line argument
  python3 authorize_hardware.py --hw-id 0x52fdfc... --private-key your_key
        """
    )
    
    parser.add_argument(
        '--hw-id', 
        required=True, 
        help='Hardware identity from ESP32 (0x... 64 hex chars)'
    )
    
    parser.add_argument(
        '--private-key', 
        help='Private key (or use PRIVATE_KEY environment variable)'
    )
    
    args = parser.parse_args()
    
    # Get private key
    private_key = args.private_key or os.environ.get('PRIVATE_KEY')
    
    if not private_key:
        print("Error: Private key required")
        print("  Set PRIVATE_KEY environment variable, or")
        print("  Use --private-key argument")
        sys.exit(1)
    
    # Remove 0x prefix if present
    if private_key.startswith('0x'):
        private_key = private_key[2:]
    
    try:
        tx_hash = authorize_hardware(args.hw_id, private_key)
        
        if tx_hash:
            print(f"\n{'='*70}")
            print(f"  NEXT STEPS")
            print(f"{'='*70}")
            print(f"\n1. Approve firmware hash (if not done):")
            print(f"   python3 scripts/approve_firmware.py --fw-hash 0x...")
            print(f"\n2. Generate receipt on ESP32-S3")
            print(f"   (Already happening automatically on device)")
            print(f"\n3. Test receipt verification:")
            print(f"   python3 verifier/anchor_canonical_verifier.py")
            print()
        
    except Exception as e:
        print(f"\n{'='*70}")
        print(f"  ✗ ERROR")
        print(f"{'='*70}")
        print(f"\n{e}")
        print()
        sys.exit(1)

if __name__ == "__main__":
    main()
```

---

**Document Version:** 1.0  
**Status:** Reference (Sepolia prototype; target production)  
**Last Updated:** February 8, 2026  
**Maintainer:** Stylus Hardware Anchor Team

**END OF DEPLOYMENT GUIDE**
