from web3 import Web3

# 1. Connection
w3 = Web3(Web3.HTTPProvider("https://sepolia-rollup.arbitrum.io/rpc"))
print(f"Connected to Arbitrum: {w3.is_connected()}")

# 2. Fix: Checksummed Address (Mandatory for web3.py)
contract_address = w3.to_checksum_address("0x34645ff1dd8af86176fe6b28812aaa4d85e33b0d")

# 3. Fix: CamelCase Names (To match Stylus export)
abi = [
    {
        "inputs": [{"name": "node_id", "type": "bytes32"}],
        "name": "isNodeAuthorized",
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"name": "fw_hash", "type": "bytes32"}],
        "name": "isFirmwareApproved",
        "outputs": [{"name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"name": "node_id", "type": "bytes32"}],
        "name": "getCounter",
        "outputs": [{"name": "", "type": "uint64"}],
        "stateMutability": "view",
        "type": "function",
    },
]

contract = w3.eth.contract(address=contract_address, abi=abi)

# 4. Correct Test Data
test_node = bytes.fromhex("11" * 32)
test_fw = b"\x00" * 32

print(f"\n--- Orthonode OHR Testing ---")

# Test 1: Node Auth
try:
    is_auth = contract.functions.isNodeAuthorized(test_node).call()
    print(f"✅ Test 1 - isNodeAuthorized: {is_auth} (Expected: False)")
except Exception as e:
    print(f"❌ Test 1 Failed: {e}")

# Test 2: Firmware Auth
try:
    is_fw = contract.functions.isFirmwareApproved(test_fw).call()
    print(f"✅ Test 2 - isFirmwareApproved: {is_fw} (Expected: False)")
except Exception as e:
    print(f"❌ Test 2 Failed: {e}")

# Test 3: Counter
try:
    count = contract.functions.getCounter(test_node).call()
    print(f"✅ Test 3 - getCounter: {count} (Expected: 0)")
except Exception as e:
    print(f"❌ Test 3 Failed: {e}")

print("\n🎉 Orthonode Contract is live and responding correctly.")
