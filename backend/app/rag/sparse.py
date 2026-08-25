import math
import re
from typing import List, Dict, Set
from backend.app.schemas.document import ChunkMetadata
from backend.app.schemas.rag import ScoredChunk


STOPWORDS: Set[str] = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can", "can't", "cannot", "could",
    "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down",
    "during", "each", "few", "for", "from", "further", "had", "hadn't", "has",
    "hasn't", "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her",
    "here", "here's", "hers", "herself", "him", "himself", "his", "how", "how's",
    "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it",
    "it's", "its", "itself", "let's", "me", "more", "most", "mustn't", "my",
    "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other",
    "ought", "our", "ours", "ourselves", "out", "over", "own", "same", "shan't",
    "she", "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such",
    "than", "that", "that's", "the", "their", "theirs", "them", "themselves",
    "then", "there", "there's", "these", "they", "they'd", "they'll", "they're",
    "they've", "this", "those", "through", "to", "too", "under", "until", "up",
    "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were",
    "weren't", "what", "what's", "when", "when's", "where", "where's", "which",
    "while", "who", "who's", "whom", "why", "why's", "with", "won't", "would",
    "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours",
    "yourself", "yourselves"
}


def tokenize(text: str) -> List[str]:
    # Extract alphanumeric tokens, keeping underscores and hyphens in identifiers (e.g. ERR_AUTH_042)
    tokens = re.findall(r"\b[\w\-_]+\b", text.lower())
    return [t for t in tokens if t not in STOPWORDS and len(t) > 1]


class BM25Index:
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus_size = 0
        self.avg_doc_len = 0.0
        self.doc_lengths: List[int] = []
        self.doc_term_freqs: List[Dict[str, int]] = []
        self.doc_freqs: Dict[str, int] = {}
        self.chunks: List[ChunkMetadata] = []

    def index(self, chunks: List[ChunkMetadata]) -> None:
        self.chunks = chunks
        self.corpus_size = len(chunks)
        self.doc_lengths = []
        self.doc_term_freqs = []
        self.doc_freqs = {}

        if self.corpus_size == 0:
            self.avg_doc_len = 0.0
            return

        total_tokens = 0
        for chunk in chunks:
            tokens = tokenize(chunk.text)
            doc_len = len(tokens)
            self.doc_lengths.append(doc_len)
            total_tokens += doc_len

            term_freq: Dict[str, int] = {}
            for token in tokens:
                term_freq[token] = term_freq.get(token, 0) + 1
            self.doc_term_freqs.append(term_freq)

            for token in term_freq.keys():
                self.doc_freqs[token] = self.doc_freqs.get(token, 0) + 1

        self.avg_doc_len = total_tokens / self.corpus_size if self.corpus_size > 0 else 0.0

    def search(self, query: str, top_k: int = 20) -> List[ScoredChunk]:
        if self.corpus_size == 0:
            return []

        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        scores: List[float] = [0.0] * self.corpus_size

        for token in query_tokens:
            if token not in self.doc_freqs:
                continue

            # Calculate IDF with standard smoothing
            n_q = self.doc_freqs[token]
            idf = math.log(1.0 + (self.corpus_size - n_q + 0.5) / (n_q + 0.5))

            for idx, doc_tf in enumerate(self.doc_term_freqs):
                if token not in doc_tf:
                    continue
                tf = doc_tf[token]
                doc_len = self.doc_lengths[idx]
                denom = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / (self.avg_doc_len or 1.0)))
                score_gain = idf * ((tf * (self.k1 + 1.0)) / denom)
                scores[idx] += score_gain

        scored_pairs = [(score, idx) for idx, score in enumerate(scores) if score > 0.0]
        scored_pairs.sort(key=lambda x: x[0], reverse=True)

        results: List[ScoredChunk] = []
        for score, idx in scored_pairs[:top_k]:
            chunk = self.chunks[idx]
            results.append(
                ScoredChunk(
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    user_id=chunk.user_id,
                    knowledge_base_id=chunk.knowledge_base_id,
                    filename=chunk.filename,
                    page_number=chunk.page_number,
                    chunk_index=chunk.chunk_index,
                    text=chunk.text,
                    score=float(score),
                    retrieval_type="sparse"
                )
            )

        return results
