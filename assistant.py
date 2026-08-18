import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path


ROLES = ("Store colleague", "Store manager")
STOP_WORDS = {"a", "an", "and", "are", "do", "for", "how", "i", "is", "that", "the", "to", "what"}


@dataclass(frozen=True)
class Document:
    id: str
    title: str
    answer: str
    url: str
    keywords: tuple[str, ...]
    roles: tuple[str, ...]


@dataclass(frozen=True)
class AgentCase:
    reference: str
    question: str
    role: str
    search_outcome: str
    documents_checked: int
    reason: str


@dataclass(frozen=True)
class Result:
    status: str
    message: str
    document_id: str | None = None
    document_url: str | None = None
    case: AgentCase | None = None


def load_documents(path: str | Path) -> list[Document]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return [
        Document(
            id=item["id"],
            title=item["title"],
            answer=item["answer"],
            url=item["url"],
            keywords=tuple(item["keywords"]),
            roles=tuple(item["roles"]),
        )
        for item in payload
    ]


def _tokens(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", text.casefold())
        if len(token) > 2 and token not in STOP_WORDS
    }


def _ranked_documents(question: str, documents: list[Document]) -> list[Document]:
    question_tokens = _tokens(question)
    if not question_tokens:
        return []

    scored = []
    for document in documents:
        metadata_tokens = _tokens(document.title) | {
            keyword.casefold() for keyword in document.keywords
        }
        score = len(question_tokens & metadata_tokens)
        if score:
            scored.append((score, document.id, document))
    return [item[2] for item in sorted(scored, key=lambda item: (-item[0], item[1]))]


def answer_question(question: str, role: str, documents: list[Document]) -> Result:
    if role not in ROLES:
        raise ValueError(f"Unknown role: {role}")

    question = question.strip()
    if not question:
        return Result(status="unavailable", message="Please enter a question.")

    ranked = _ranked_documents(question, documents)
    if not ranked:
        digest = hashlib.sha256(f"{role}|{question.casefold()}".encode()).hexdigest()[:8].upper()
        return Result(
            status="unavailable",
            message="I don't have this information available. Would you like to talk to an agent?",
            case=AgentCase(
                reference=f"CASE-{digest}",
                question=question,
                role=role,
                search_outcome="No approved document matched",
                documents_checked=len(documents),
                reason="Approved information unavailable",
            ),
        )

    permitted = [document for document in ranked if role in document.roles]
    if not permitted:
        return Result(
            status="access_denied",
            message="Sorry, you do not have the correct access level. Ask your manager to make this request.",
        )

    document = permitted[0]
    return Result(
        status="answer",
        message=document.answer,
        document_id=document.id,
        document_url=document.url,
    )
