"""
A dependency-free, fully offline embedding function for ChromaDB.

ChromaDB's default embedding function downloads a pretrained model
(sentence-transformers/all-MiniLM-L6-v2, ~90MB) from the internet on
first use. That's a reasonable choice in production, but it means the
whole RAG feature would silently fail in any environment without
internet access to Hugging Face -- which includes plenty of locked-down
corporate/CI environments SprintNova might run in.

This class is NOT a semantic embedding model. It's a deterministic
bag-of-words hashing vectorizer with light stemming: each word is
stemmed, hashed into one of N buckets, and the resulting count vector is
L2-normalized. It gives ChromaDB's cosine-similarity search a real,
computable notion of document similarity based on shared vocabulary --
good enough to find "the payment refund policy doc" when asked about
"refunds for payments" -- without any network call or model download.

Swap this for a real embedding model (sentence-transformers, Gemini's
embedding API, OpenAI embeddings, ...) in production for stronger
semantic matching; this keeps local dev, demos, and offline CI fully
functional without that dependency.
"""
import hashlib
import math
import re

try:
    from chromadb import EmbeddingFunction, Documents, Embeddings
except ImportError:  # pragma: no cover - chromadb not installed
    EmbeddingFunction = object
    Documents = list
    Embeddings = list

_SUFFIXES = ("ing", "edly", "ed", "es", "s")

# Common English words carry no discriminating signal but, in a short
# query like "what is our refund policy", they'd otherwise make up most
# of the vector and drown out the one word that matters ("refund").
_STOPWORDS = frozenset("""
a an and are as at be been by for from has have how i in is it its of on or our
that the their there these they this to was were what when where which who will
with would you your do does did can could should must my me we us
""".split())


def _stem(word: str) -> str:
    for suffix in _SUFFIXES:
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            return word[: -len(suffix)]
    return word


def _stable_bucket(word: str, dims: int) -> int:
    """
    Maps a word to a bucket index deterministically ACROSS PROCESSES.

    Python's built-in hash() for strings is randomly salted per process
    (PYTHONHASHSEED), so using it here would mean documents indexed by one
    process (e.g. the seed script) and queried by another (the API server)
    hash the same word into different buckets -- silently producing
    near-orthogonal vectors and garbage search results. blake2b is stable
    everywhere, forever.
    """
    digest = hashlib.blake2b(word.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "big") % dims


def _tokenize(text: str) -> list[str]:
    return [
        _stem(w) for w in re.findall(r"[a-z0-9]+", text.lower())
        if w not in _STOPWORDS
    ]


class HashingEmbeddingFunction(EmbeddingFunction):
    def __init__(self, dims: int = 256):
        self.dims = dims

    @staticmethod
    def name() -> str:  # must be a staticmethod -- chromadb calls it on the CLASS
        return "sprintnova-hashing-bow-v1"

    def get_config(self) -> dict:  # required by chromadb's EmbeddingFunction protocol
        return {"dims": self.dims}

    @staticmethod
    def build_from_config(config: dict) -> "HashingEmbeddingFunction":
        return HashingEmbeddingFunction(dims=config.get("dims", 256))

    def __call__(self, input: "Documents") -> "Embeddings":
        return [self._embed(text) for text in input]

    def _embed(self, text: str) -> list[float]:
        counts: dict[int, float] = {}
        for word in _tokenize(text):
            bucket = _stable_bucket(word, self.dims)
            counts[bucket] = counts.get(bucket, 0.0) + 1.0

        # Sublinear TF scaling (1 + log tf), the standard TF-IDF-style
        # damping: a word appearing 5x in a long document shouldn't
        # outweigh a short document that's squarely about that word.
        vec = [0.0] * self.dims
        for bucket, tf in counts.items():
            vec[bucket] = 1.0 + math.log(tf)

        norm = sum(v * v for v in vec) ** 0.5
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec
