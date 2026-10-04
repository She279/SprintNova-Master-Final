"""
ChromaDB-backed project knowledge retrieval. See app/services/embeddings.py
for why the embedding function is a lightweight offline hashing vectorizer
rather than a downloaded pretrained model.

Every function here degrades gracefully: if chromadb can't be imported or
the persistent client can't be created for any reason (read-only
filesystem, disk full, whatever), retrieval falls back to a real (not
fake) keyword-overlap search directly over the `project_documents` table
in Postgres/SQLite. The response always reports which method was used
(`retrieval_method: "vector" | "keyword"`) so this is never silently
misrepresented as semantic search when it wasn't.
"""
import re
from functools import lru_cache

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.project_document import ProjectDocument

_client = None


def _get_client():
    global _client
    if _client is not None:
        return _client
    try:
        import chromadb
        _client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
    except Exception:
        _client = False  # sentinel: tried and failed, don't retry every call
    return _client


@lru_cache(maxsize=1)
def _embedding_function():
    from app.services.embeddings import HashingEmbeddingFunction
    return HashingEmbeddingFunction()


def _get_collection(project_id: int):
    client = _get_client()
    if not client:
        return None
    try:
        return client.get_or_create_collection(
            f"project_{project_id}_docs", embedding_function=_embedding_function(),
        )
    except Exception:
        return None


def index_document(doc: ProjectDocument) -> None:
    collection = _get_collection(doc.project_id)
    if not collection:
        return
    try:
        collection.upsert(
            ids=[str(doc.id)],
            documents=[f"{doc.title}\n{doc.content}"],
            metadatas=[{"title": doc.title, "doc_type": doc.doc_type.value}],
        )
    except Exception:
        pass  # indexing is best-effort; the row in Postgres is the source of truth


def remove_document(project_id: int, document_id: int) -> None:
    collection = _get_collection(project_id)
    if not collection:
        return
    try:
        collection.delete(ids=[str(document_id)])
    except Exception:
        pass


def reindex_project(db: Session, project_id: int) -> int:
    """Rebuilds the Chroma collection for a project from scratch. Useful
    after wiping CHROMA_PERSIST_DIR or migrating to a new embedding
    function. Returns the number of documents indexed."""
    docs = db.query(ProjectDocument).filter(ProjectDocument.project_id == project_id).all()
    for doc in docs:
        index_document(doc)
    return len(docs)


def _keyword_search(db: Session, project_id: int, query: str, top_k: int) -> list[dict]:
    words = set(re.findall(r"[a-z0-9]+", query.lower()))
    docs = db.query(ProjectDocument).filter(ProjectDocument.project_id == project_id).all()

    scored = []
    for doc in docs:
        haystack = f"{doc.title} {doc.content}".lower()
        score = sum(1 for w in words if w in haystack)
        if score > 0:
            scored.append((score, doc))
    scored.sort(key=lambda pair: pair[0], reverse=True)

    return [
        {
            "id": doc.id, "title": doc.title, "doc_type": doc.doc_type.value,
            "snippet": doc.content[:280], "score": score,
        }
        for score, doc in scored[:top_k]
    ]


def search(db: Session, project_id: int, query: str, top_k: int = 3) -> tuple[list[dict], str]:
    """Returns (results, retrieval_method)."""
    collection = _get_collection(project_id)
    if collection is not None:
        try:
            if collection.count() > 0:
                res = collection.query(query_texts=[query], n_results=min(top_k, collection.count()))
                results = []
                for i, doc_id in enumerate(res["ids"][0]):
                    meta = res["metadatas"][0][i] or {}
                    results.append({
                        "id": int(doc_id),
                        "title": meta.get("title", ""),
                        "doc_type": meta.get("doc_type", ""),
                        "snippet": (res["documents"][0][i] or "")[:280],
                        "distance": res["distances"][0][i] if res.get("distances") else None,
                    })
                return results, "vector"
        except Exception:
            pass  # fall through to keyword search

    return _keyword_search(db, project_id, query, top_k), "keyword"
