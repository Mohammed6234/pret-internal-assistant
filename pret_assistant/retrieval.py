import re
from typing import Iterable, Protocol

from .models import KnowledgeDocument, RetrievedEvidence, UserContext
from .policy import is_document_allowed


STOP_WORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "for",
        "how",
        "i",
        "in",
        "is",
        "it",
        "of",
        "on",
        "the",
        "to",
        "what",
        "with",
    }
)

MIN_MATCHED_TERMS = 2
MIN_SCORE = 0.55


def _tokenise(text: str) -> tuple[str, ...]:
    tokens = re.findall(r"[a-z0-9]+", text.casefold())
    return tuple(token for token in tokens if token not in STOP_WORDS and len(token) > 2)


class Retriever(Protocol):
    def retrieve(
        self,
        question: str,
        user: UserContext,
        *,
        top_k: int = 3,
    ) -> list[RetrievedEvidence]:
        ...


class InMemoryRetriever:
    def __init__(self, documents: Iterable[KnowledgeDocument]) -> None:
        self._documents = tuple(documents)

    def retrieve(
        self,
        question: str,
        user: UserContext,
        *,
        top_k: int = 3,
    ) -> list[RetrievedEvidence]:
        if top_k <= 0:
            return []

        question_terms = set(_tokenise(question))
        if not question_terms:
            return []

        candidates: list[RetrievedEvidence] = []
        for document in self._documents:
            if not is_document_allowed(user, document):
                continue

            document_terms = set(_tokenise(f"{document.title} {document.content}"))
            matched_terms = tuple(sorted(question_terms.intersection(document_terms)))
            if len(matched_terms) < MIN_MATCHED_TERMS:
                continue

            score = len(matched_terms) / len(question_terms)
            if score < MIN_SCORE:
                continue
            candidates.append(
                RetrievedEvidence(
                    document=document,
                    score=score,
                    matched_terms=matched_terms,
                )
            )

        candidates.sort(key=lambda item: (-item.score, item.document.doc_id))
        return candidates[:top_k]
