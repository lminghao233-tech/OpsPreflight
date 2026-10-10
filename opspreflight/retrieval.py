"""Hybrid runbook retrieval with an offline, reproducible dense baseline."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import re
from typing import Sequence


CATALOG_PATH = Path(__file__).resolve().parents[1] / "runbooks" / "catalog.json"
TOKEN_PATTERN = re.compile(r"[a-z0-9_-]+", re.I)


def tokenize(text: str) -> list[str]:
    return [token.casefold() for token in TOKEN_PATTERN.findall(text)]


def _embed(text: str, dimensions: int = 128) -> list[float]:
    vector = [0.0] * dimensions
    tokens = tokenize(text)
    for feature in tokens + [f"{a}::{b}" for a, b in zip(tokens, tokens[1:])]:
        digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
        vector[int.from_bytes(digest[:4], "big") % dimensions] += (
            1.0 if digest[4] & 1 else -1.0
        )
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]


@dataclass(frozen=True)
class Runbook:
    doc_id: str
    title: str
    rule_ids: tuple[str, ...]
    source: str
    text: str


@dataclass(frozen=True)
class RunbookHit:
    doc_id: str
    title: str
    source: str
    excerpt: str
    score: float
    sparse_score: float
    dense_score: float


class RunbookRetriever:
    def __init__(
        self,
        runbooks: Sequence[Runbook] | None = None,
        *,
        catalog_path: Path = CATALOG_PATH,
    ) -> None:
        self.runbooks = list(runbooks or self.load(catalog_path))
        if not self.runbooks:
            raise ValueError("at least one runbook is required")
        self._tokens = [tokenize(f"{item.title} {item.text}") for item in self.runbooks]
        self._counts = [Counter(tokens) for tokens in self._tokens]
        self._average_length = sum(map(len, self._tokens)) / len(self._tokens)
        self._document_frequency = Counter(
            token for tokens in self._tokens for token in set(tokens)
        )
        self._vectors = [_embed(f"{item.title} {item.text}") for item in self.runbooks]

    @staticmethod
    def load(path: Path = CATALOG_PATH) -> list[Runbook]:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return [
            Runbook(
                doc_id=item["doc_id"],
                title=item["title"],
                rule_ids=tuple(item["rule_ids"]),
                source=item["source"],
                text=item["text"],
            )
            for item in raw
        ]

    def _bm25(self, query: Sequence[str], index: int) -> float:
        score = 0.0
        count = self._counts[index]
        length = len(self._tokens[index])
        total = len(self.runbooks)
        for token in set(query):
            frequency = count[token]
            if not frequency:
                continue
            seen = self._document_frequency[token]
            inverse_frequency = math.log(1 + (total - seen + 0.5) / (seen + 0.5))
            denominator = frequency + 1.5 * (
                1 - 0.75 + 0.75 * length / self._average_length
            )
            score += inverse_frequency * frequency * 2.5 / denominator
        return score

    def search(
        self,
        query: str,
        *,
        rule_ids: Sequence[str] = (),
        top_k: int = 3,
    ) -> list[RunbookHit]:
        if not query.strip():
            raise ValueError("query must not be empty")
        if top_k <= 0:
            raise ValueError("top_k must be positive")
        wanted = set(rule_ids)
        candidates = [
            index
            for index, item in enumerate(self.runbooks)
            if not wanted or wanted.intersection(item.rule_ids)
        ]
        if not candidates:
            candidates = list(range(len(self.runbooks)))
        query_tokens = tokenize(query)
        query_vector = _embed(query)
        sparse = {index: self._bm25(query_tokens, index) for index in candidates}
        maximum = max(sparse.values(), default=0.0) or 1.0
        hits = []
        for index in candidates:
            dense = max(
                0.0,
                sum(a * b for a, b in zip(query_vector, self._vectors[index])),
            )
            sparse_score = sparse[index] / maximum
            score = 0.65 * sparse_score + 0.35 * dense
            item = self.runbooks[index]
            hits.append(
                RunbookHit(
                    doc_id=item.doc_id,
                    title=item.title,
                    source=item.source,
                    excerpt=item.text,
                    score=round(score, 6),
                    sparse_score=round(sparse_score, 6),
                    dense_score=round(dense, 6),
                )
            )
        return sorted(hits, key=lambda hit: (-hit.score, hit.doc_id))[:top_k]
