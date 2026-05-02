import faiss
import numpy as np
import os

INDEX_PATH = os.path.join("database", "vector_index.faiss")
DIMENSION = 128  # embedding size

def create_faiss_index():
    index = faiss.IndexFlatL2(DIMENSION)
    faiss.write_index(index, INDEX_PATH)
    print("✅ FAISS index created")

def load_faiss_index():
    if not os.path.exists(INDEX_PATH):
        create_faiss_index()
    return faiss.read_index(INDEX_PATH)

if __name__ == "__main__":
    create_faiss_index()
