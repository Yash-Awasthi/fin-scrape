# rag/retriever.py
# RAG system seeded with REAL data from SEC EDGAR + Federal Register

import chromadb
from chromadb.utils import embedding_functions
import time

EMBEDDING_FN = embedding_functions.DefaultEmbeddingFunction()
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_or_create_collection(
    name="sentinel_real_knowledge",
    embedding_function=EMBEDDING_FN
)

def seed_from_real_sources():
    from tools.data_fetcher import (
        fetch_all_sec_filings,
        fetch_federal_register_notices,
        fetch_ofac_sanctions
    )

    existing = collection.count()
    if existing > 0:
        print(f"[RAG] Knowledge base ready — {existing} real documents loaded")
        return

    print("[RAG] Seeding knowledge base from real sources...")
    documents, ids, metadatas = [], [], []
    doc_id = 0

    # SEC EDGAR 10-K Filings
    print("[RAG] Fetching SEC EDGAR filings...")
    filings = fetch_all_sec_filings()
    for filing in filings:
        text = (
            f"{filing['company']} ({filing['ticker']}) — {filing['filing_type']} "
            f"filed {filing['filing_date']}. {filing['description']}"
        )
        documents.append(text)
        ids.append(f"sec_{filing['ticker']}_{doc_id}")
        metadatas.append({
            "source": "SEC EDGAR",
            "ticker": filing["ticker"],
            "type":   "10-K",
            "date":   filing["filing_date"]
        })
        doc_id += 1

    # Federal Register Notices
    print("[RAG] Fetching Federal Register notices...")
    notices = fetch_federal_register_notices(max_results=15)
    for notice in notices:
        text = f"{notice['title']}. {notice['abstract']}"
        if len(text.strip()) < 20:
            continue
        documents.append(text)
        ids.append(f"fedreg_{doc_id}")
        metadatas.append({
            "source": "Federal Register",
            "type":   "procurement_notice",
            "date":   notice["date"]
        })
        doc_id += 1

    # OFAC Sanctions
    print("[RAG] Fetching OFAC sanctions context...")
    sanctions = fetch_ofac_sanctions(max_entries=20)
    for sanction in sanctions:
        programs_str = ", ".join(sanction.get("programs", []))
        text = (
            f"OFAC Sanctioned Entity: {sanction['name']}. "
            f"Type: {sanction['type']}. Programs: {programs_str}. "
            f"{sanction['detail']}"
        )
        documents.append(text)
        ids.append(f"ofac_{doc_id}")
        metadatas.append({
            "source":   "OFAC SDN",
            "type":     "sanctions",
            "programs": programs_str,
            "date":     sanction["date"]
        })
        doc_id += 1

    if documents:
        collection.add(ids=ids, documents=documents, metadatas=metadatas)
        print(f"[RAG] Seeded {len(documents)} real documents into ChromaDB")
    else:
        print("[RAG] Warning: No documents fetched — check network connection")

def retrieve(query: str, n_results: int = 8) -> list[dict]:
    count = collection.count()
    if count == 0:
        return []
    results = collection.query(
        query_texts=[query],
        n_results=min(n_results, count)
    )
    docs = []
    for i, (doc, meta, dist) in enumerate(zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    )):
        docs.append({
            "rank":     i + 1,
            "text":     doc,
            "metadata": meta,
            "distance": dist,
            "source":   meta.get("source", "Unknown")
        })
    return docs

def add_document(text: str, doc_id: str, metadata: dict = {}):
    collection.add(ids=[doc_id], documents=[text], metadatas=[metadata])
    print(f"[RAG] Added document: {doc_id}")
