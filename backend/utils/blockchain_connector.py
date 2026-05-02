from web3 import Web3
import json
from config import GANACHE_URL, WALLET_ADDRESS, PRIVATE_KEY, CONTRACT_ADDRESS, CONTRACT_ABI_PATH

# Connect to Ganache
w3 = Web3(Web3.HTTPProvider(GANACHE_URL))

assert w3.is_connected(), "Ganache not running"

# Load contract ABI
with open(CONTRACT_ABI_PATH) as f:
    contract_json = json.load(f)
    abi = contract_json["abi"]

# Smart contract instance
contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=abi)

def store_on_blockchain(file_hash, cid, owner):
    nonce = w3.eth.get_transaction_count(WALLET_ADDRESS)

    txn = contract.functions.storeAsset(
        file_hash,
        cid,
        owner
    ).build_transaction({
        "from": WALLET_ADDRESS,
        "nonce": nonce,
        "gas": 3000000,
        "gasPrice": w3.to_wei("20", "gwei")
    })

    signed_txn = w3.eth.account.sign_transaction(txn, PRIVATE_KEY)

    #  FIXED LINE (Web3 v6+)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)

    return w3.to_hex(tx_hash)
