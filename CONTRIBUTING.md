# Contributing to Nexus Protocol

Thank you for your interest in contributing to Nexus Protocol!
This document provides guidelines for contributing to the project.

## 🎯 How to Contribute

### Reporting Bugs

If you find a bug, please open an issue with:

- **Clear title** describing the issue
- **Steps to reproduce** the problem
- **Expected vs. actual behavior**
- **Environment details** (OS, Rust version, firmware version)
- **Relevant logs or error messages**

### Suggesting Features

We welcome feature suggestions! Please:

- Check existing issues first to avoid duplicates
- Clearly describe the use case and benefits
- Explain how it fits with Nexus Protocol's vision

### Pull Requests

1. **Fork** the repository
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Make your changes** following our coding standards (see below)
4. **Test thoroughly** - all tests must pass
5. **Commit** with clear messages (`git commit -m 'Add amazing feature'`)
6. **Push** to your fork (`git push origin feature/amazing-feature`)
7. **Open a Pull Request** with a detailed description

## 📋 Coding Standards

### Rust Code (Smart Contracts & Firmware)

- **Format:** All Rust code must pass `cargo fmt`
- **Lint:** Code must pass `cargo clippy` with no warnings
- **Test:** Include unit tests for new functionality
- **Documentation:** Add doc comments for public functions

```bash
# Before submitting, run:
cargo fmt
cargo clippy -- -D warnings
cargo test
```

### Python Code (Middleware & Scripts)

- **Style:** Follow PEP 8 guidelines
- **Format:** Use `black` for formatting
- **Type hints:** Include type annotations where applicable
- **Documentation:** Add docstrings for functions and classes

```bash
# Before submitting, run:
black .
pylint your_file.py
```

### ESP32 Firmware

- **Format:** Follow PlatformIO standards
- **Security:** Never hardcode secrets or private keys
- **Testing:** Verify on actual hardware before submitting
- **Documentation:** Comment critical cryptographic operations

## 🔐 Security Guidelines

- **Never commit** private keys, `.env` files, or secrets
- **Review dependencies** for known vulnerabilities
- **Use constant-time** operations for cryptographic comparisons
- **Report security issues** privately (see SECURITY.md)

## 🧪 Testing Requirements

### Smart Contract Tests

- All public functions must have unit tests
- Test both success and failure cases
- Verify gas usage remains reasonable

### Firmware Tests

- Test on actual ESP32-S3 hardware
- Verify Keccak-256 output matches test vectors
- Test counter overflow/replay scenarios

### Integration Tests

- End-to-end receipt generation and verification
- Test against deployed testnet contracts
- Verify all error cases

## 📝 Commit Message Format

Use conventional commits:

```
type(scope): short description

Longer description if needed

Fixes #123
```

**Types:**

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Adding tests
- `refactor`: Code refactoring
- `chore`: Maintenance tasks

**Example:**

```text
feat(verifier): Add batch receipt verification

Implements optimized batch verification for multiple receipts
in a single transaction, reducing gas costs by ~40%.

Closes #42
```

## 🌐 Development Environment

### Prerequisites
- Rust 1.93.0 or later
- Python 3.8+
- PlatformIO Core
- ESP32-S3 development board

### Setup

```bash
# Clone the repository
git clone https://github.com/your-org/nexus-protocol.git
cd nexus-protocol

# Install Rust dependencies
cargo build

# Install Python dependencies
pip install -r requirements.txt

# Build firmware
cd ohr_firmware
pio run
```

## 🤝 Code of Conduct

- **Be respectful** and professional
- **Collaborate constructively** with other contributors
- **Focus on** the technical merits of contributions
- **Welcome newcomers** and help them learn

## 📧 Questions?

If you have questions about contributing:
- Open a GitHub Discussion
- Join our Discord (if applicable)
- Email: arhant6armate@gmail.com

## 🎓 Learning Resources

- [Arbitrum Stylus Documentation](https://docs.arbitrum.io/stylus/)
- [ESP32-S3 Technical Reference](https://www.espressif.com/en/products/socs/esp32-s3)
- [Ethereum Keccak-256 Specification](https://ethereum.org/en/developers/docs/data-structures-and-encoding/rlp/)

---

Thank you for contributing to Nexus Protocol! 🚀
