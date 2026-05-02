import os

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CRAWLED_DATA_DIR = os.path.join(BASE_DIR, "monitoring", "crawled_data")

os.makedirs(CRAWLED_DATA_DIR, exist_ok=True)


# --------------------------------------------------
# WEB CRAWLER (SIMULATION)
# --------------------------------------------------
def crawl_web_sources():
    """
    Simulates web crawling.
    Returns list of downloaded/suspicious file paths.
    """

    samples = [
        "This is a copied academic document",
        "Original image reused without permission",
        "Audio content reposted illegally"
    ]

    crawled_files = []

    for i, text in enumerate(samples):
        file_path = os.path.join(CRAWLED_DATA_DIR, f"suspect_{i}.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(text)
        crawled_files.append(file_path)

    return crawled_files


# --------------------------------------------------
# TEST MODE
# --------------------------------------------------
if __name__ == "__main__":
    files = crawl_web_sources()
    print("Crawled files:", files)
