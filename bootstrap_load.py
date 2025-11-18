"""
Bootstrap RAG index from all documents in ./data

Usage:
  # (optionnel) repartir de zéro
  rm -rf .chroma

  # (re)construire l'index
  python bootstrap_load.py
"""

from pathlib import Path
from utils.rag_engine import RAGEngine
from utils.document_processor import (
    load_documents_from_folder,
    chunk_documents,
    chunk_documents_by_headings,
    chunk_bcbs_principles,
)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"


def main():
    if not DATA_DIR.exists():
        print(f"⚠️ data folder not found: {DATA_DIR}")
        return

    print("📂 data folder contains:")
    for p in sorted(DATA_DIR.iterdir()):
        if p.is_file():
            print(f"   • {p.name}")
    print()

    # --- init RAG ---
    R = RAGEngine(collection_name="regintel_local")

    # on repart de zéro pour éviter les vieilles versions de docs
    print("🧹 Clearing existing vector store…")
    R.clear_collection()

    docs = load_documents_from_folder(str(DATA_DIR))
    if not docs:
        print("⚠️ No readable documents found in data/")
        return

    total_chunks = 0

    for doc in docs:
        filename = doc["filename"]
        text = doc["text"] or ""
        if not text.strip():
            print(f"⚠️ {filename}: empty text after extraction, skipped")
            continue

        lower = filename.lower()

        # Cas 1 : textes cœur BCBS 239 → chunking par principe
        if "bcbs239" in lower or "bcbs_239" in lower or "principles for effective risk data aggregation" in lower:
            chunks = chunk_bcbs_principles(text, filename)

        # Cas 2 : rapport SSM sur BCBS 239 (sections "BCBS Principle X")
        elif "ssm.bcbs_239_report" in lower or "thematic review" in lower:
            chunks = chunk_bcbs_principles(text, filename)

        # Cas 3 : guide RDARR / autres guides & policies → headings génériques
        else:
            use_headings = any(
                key in lower
                for key in [
                    "rdarr",
                    "bcbs",
                    "guide",
                    "report",
                    "ai act",
                    "gdpr",
                    "eba",
                    "ecb",
                    "policy",
                    "procedure",
                    "procédure",
                    "charter",
                    "charte",
                ]
            )

            if use_headings:
                chunks = chunk_documents_by_headings(text, filename)
            else:
                chunks = chunk_documents(text, filename)

        if not chunks:
            print(f"⚠️ {filename}: no chunks generated, skipped")
            continue

        R.add_documents(chunks)
        total_chunks += len(chunks)
        print(f"✅ {filename}: {len(chunks)} chunks")

    print(f"\n✅ Bootstrapped — total chunks added: {total_chunks}")


if __name__ == "__main__":
    main()
