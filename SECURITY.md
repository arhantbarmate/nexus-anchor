# Security Policy

## 🔒 Reporting Security Vulnerabilities

**Please do not open public GitHub issues for security vulnerabilities.**

Stylus Hardware Anchor takes security seriously. If you discover a security vulnerability, we appreciate your help in disclosing it to us responsibly.

### How to Report

**Email:** arhant6armate@gmail.com

**Include in your report:**
- Description of the vulnerability
- Steps to reproduce the issue
- Potential impact and severity
- Suggested fix (if you have one)
- Your contact information for follow-up

### What to Expect

1. **Acknowledgment:** We'll acknowledge receipt within 48 hours
2. **Assessment:** We'll investigate and assess the severity within 7 days
3. **Fix:** We'll develop and test a fix (timeline depends on severity)
4. **Disclosure:** We'll coordinate public disclosure with you
5. **Credit:** We'll credit you in our security advisory (if you wish)

## 🎯 Scope

### In Scope
- Smart contract vulnerabilities (reentrancy, overflow, access control)
- Cryptographic implementation flaws (Keccak-256, signature verification)
- Replay attack vectors
- Hardware receipt forgery
- Private key exposure risks
- Denial of service attacks

### Out of Scope
- Social engineering attacks
- Physical device theft (hardware security is user responsibility)
- Third-party dependencies (report to upstream projects)
- Already known issues listed in our issue tracker

## 🛡️ Security Measures

Stylus Hardware Anchor implements multiple layers of security:

### Smart Contract Security
- **Replay protection:** Monotonic counter validation
- **Access control:** Hardware ID authorization system
- **Immutable verification:** On-chain cryptographic proof
- **Audited dependencies:** Using battle-tested Stylus SDK

### Hardware Security
- **Unique hardware IDs:** Generated from ESP32 eFuse MAC
- **Keccak-256 hashing:** Ethereum-standard cryptography
- **Counter persistence:** Prevents receipt replay
- **Firmware approval:** On-chain firmware hash validation

### Operational Security
- **No PII collection:** Zero personal data in receipts or on-chain
- **Open source:** Full transparency for community review
- **Testnet deployment:** Phase 1 is testnet-only (Arbitrum Sepolia); mainnet planned for Phase 2 (future grant)
- **Upgrade path:** Designed for secure contract migration

## 📚 Security Best Practices for Users

### Node Operators
1. **Secure your private keys** - Never commit to version control
2. **Use hardware wallets** for mainnet or production deployments
3. **Verify firmware hashes** before approval on-chain
4. **Monitor counter values** for unexpected jumps
5. **Keep firmware updated** to latest secure version

### Developers
1. **Review all code changes** before deployment
2. **Run security tests** (`cargo clippy`, static analysis)
3. **Use reproducible builds** for contract verification
4. **Follow principle of least privilege** for authorization
5. **Document security assumptions** clearly

## 🔄 Security Updates

We publish security advisories at:
- **GitHub Security Advisories:** [Your repo]/security/advisories
- **Discord Announcements:** [Your Discord] (if applicable)
- **Twitter/X:** @anchorProtocol (if applicable)

## 🏆 Security Hall of Fame

We recognize security researchers who responsibly disclose vulnerabilities:

- *No disclosures yet - be the first!*

## 📜 Security Audit Status

**Current Status:** Phase 1 security hardening pending formal approval. Testnet-only (Sepolia); no production deployment in Phase 1 scope.

**Audit positioning:**
- Optional independent review may occur in Phase 1 (post–Milestone 1 unlock; not required for Phase 1 completion).
- Professional third-party audit is deferred to Phase 2 (future grant application).

## 🚨 Known Limitations

**Current Known Issues:**
- Counter overflow after 2^64 receipts (cosmically unlikely)
- Single-threaded receipt verification (planned batch support in Milestone 2)
- ESP32 physical tampering (hardware security module planned for Phase 2 — future grant)

## 💬 Security Contact

- **Email:** arhant6armate@gmail.com
- **PGP Key:** [Coming soon]
- **Response Time:** Within 48 hours for critical issues

---

**Last Updated:** February 2026  
**Version:** 1.0 (prototype; Milestone 1 hardening pending)
