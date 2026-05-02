import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Database
DATABASE_PATH = os.path.join(BASE_DIR, "database", "metadata.db")

# Logs
LOG_PATH = os.path.join(BASE_DIR, "logs", "activity.log")

# Blockchain (Ganache)
GANACHE_URL = "http://127.0.0.1:7545"
CHAIN_ID = 1337

# Wallet
WALLET_ADDRESS = os.getenv("WALLET_ADDRESS")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")

# Pinata
PINATA_API_KEY = os.getenv("PINATA_API_KEY")
PINATA_SECRET_API_KEY = os.getenv("PINATA_SECRET_API_KEY")

# Smart Contract
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
CONTRACT_ABI_PATH = os.path.join(
    BASE_DIR, "../blockchain/build/contracts/IPP.json"
)
