import os
import shutil
import uuid
import hashlib
import requests

from config import PINATA_API_KEY, PINATA_SECRET_API_KEY

USE_PINATA = True   #  Set False to simulate local IPFS

# Local IPFS-style storage (for demo)
IPFS_ROOT = os.path.join(os.path.dirname(__file__), "..", "ipfs")
UPLOAD_DIR = os.path.join(IPFS_ROOT, "uploaded")
CID_FILE = os.path.join(IPFS_ROOT, "pinned_cids.txt")

os.makedirs(UPLOAD_DIR, exist_ok=True)

PINATA_URL = "https://api.pinata.cloud/pinning/pinFileToIPFS"
HEADERS = {
    "pinata_api_key": PINATA_API_KEY,
    "pinata_secret_api_key": PINATA_SECRET_API_KEY
}

def upload_to_ipfs(file_path):

    # 🔹 REAL PINATA MODE
    if USE_PINATA:
        with open(file_path, "rb") as f:
            response = requests.post(
                PINATA_URL,
                files={"file": f},
                headers=HEADERS
            )

        if response.status_code != 200:
            raise Exception(f"Pinata upload failed: {response.text}")

        cid = response.json()["IpfsHash"]

        with open(CID_FILE, "a") as f:
            f.write(f"{file_path} -> {cid}\n")

        print(f"UPLOAD--> Uploaded to Pinata | CID: {cid}")
        return cid

    #  SIMULATED LOCAL IPFS MODE
    with open(file_path, "rb") as f:
        file_bytes = f.read()

    cid = "Qm" + hashlib.sha256(file_bytes).hexdigest()[:44]
    unique_name = f"{uuid.uuid4().hex}_{os.path.basename(file_path)}"

    shutil.copy(file_path, os.path.join(UPLOAD_DIR, unique_name))

    with open(CID_FILE, "a") as f:
        f.write(f"{unique_name} -> {cid}\n")

    print(f" STORE--> Stored locally | CID: {cid}")
    return cid


# CLI test support
if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python utils/storage_ipfs.py <file_path>")
        exit(1)

    upload_to_ipfs(sys.argv[1])
