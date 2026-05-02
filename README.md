# SmartIPGuard 2.0
AI-Driven Intellectual Property Protection using Blockchain and IPFS

SmartIPGuard 2.0 is a final-year B.Tech Computer Science project that provides
secure ownership verification and plagiarism detection for digital assets
such as images, text documents, and audio files using AI fingerprinting,
blockchain immutability, and decentralized storage.

------------------------------------------------------------

PROBLEM STATEMENT
Digital content can be copied, modified, and redistributed without permission.
Existing copyright systems are centralized, slow, and lack transparency.

------------------------------------------------------------

SOLUTION OVERVIEW
SmartIPGuard 2.0 uses:
- AI-based fingerprinting for originality detection
- SHA-256 hashing for content integrity
- Blockchain (Ganache) for immutable ownership proof
- IPFS-style decentralized storage (simulated)
- Monitoring module for violation detection

------------------------------------------------------------

TECHNOLOGIES USED
Frontend:
- HTML
- CSS
- JavaScript

Backend:
- Python
- Flask

Blockchain:
- Ethereum
- Ganache
- Truffle
- Web3.py

AI & Processing:
- CNN (Images)
- Text embeddings
- Audio feature extraction
- FAISS similarity search

Database & Storage:
- SQLite
- IPFS (Simulated)

------------------------------------------------------------

PROJECT WORKFLOW
User Upload
    |
AI Fingerprinting (Text/Image/Audio)
    |
SHA-256 Hash Generation
    |
IPFS Storage (CID Generation)
    |
Blockchain Registration (Ganache)
    |
Metadata Database Storage
    |
Verification & Similarity Checking
    |
Dashboard & Violation Alerts

------------------------------------------------------------

BLOCKCHAIN DETAILS
- Uses Ganache private Ethereum network
- Stores:
  - File hash
  - IPFS CID
  - Owner ID
  - Timestamp
- Ensures immutability and ownership proof

------------------------------------------------------------

KEY FEATURES
- Digital asset fingerprinting
- Invisible watermarking
- Blockchain-based proof of ownership
- Plagiarism detection
- Violation monitoring and reporting
- Dashboard visualization

------------------------------------------------------------

HOW TO RUN THE PROJECT

1. Start Ganache
   - Open Ganache GUI
   - Use port 7545

2. Deploy Smart Contract
   cd blockchain
   truffle migrate --reset

3. Run Backend Server
   cd backend
   python app.py

4. Run Frontend
   Open frontend/index.html in browser

------------------------------------------------------------

ACADEMIC NOTE
This project is designed for academic and demonstration purposes.
Real IPFS and Ethereum mainnet can be integrated in future enhancements.

------------------------------------------------------------

DEVELOPED BY
B.Tech Computer Science Engineering
Final Year Project

------------------------------------------------------------

LICENSE
For academic and educational use only.
