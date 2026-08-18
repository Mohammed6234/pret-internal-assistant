# Access-Control and Permission-Aware RAG Prototype Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the broad assistant repository with a six-file Streamlit application plus the existing `.gitignore`, implementing only access control followed by permission-aware retrieval and a grounded response.

**Architecture:** `app.py` is a thin Streamlit interface. `assistant.py` loads synthetic document metadata, matches a question, checks the selected role before reading protected fields, and returns one of three immutable outcomes: answer, access denied, or information unavailable with a prepared agent-case preview. The backend is deterministic and credential-free; it does not call a model, create a real case, or implement any other architecture block.

**Tech Stack:** Python 3.11+, Streamlit 1.60.0, standard-library `unittest`, JSON fixtures.

## Global Constraints

- Implement exactly two consecutive blocks: `Access control → Permission-aware retrieval and grounded response`.
- Final interviewer-facing application files are only `app.py`, `assistant.py`, `data/knowledge.json`, `tests/test_assistant.py`, `requirements.txt`, and `README.md`; retain the existing `.gitignore` as repository hygiene.
- Use only synthetic guidance and links under `https://pret.example/`.
- `Store colleague` and `Store manager` are the only accepted roles.
- Never expose restricted answer text, document ID, URL, or snippets in an access-denied result.
- Unsupported questions prepare a display-only agent case; no ticket is persisted or submitted.
- Do not add a model call, prompt guardrails, tool use, production adapters, telemetry, deployment code, or a broad evaluation framework.
- Follow red-green-refactor: write each behaviour test, observe it fail for the expected reason, and then add only enough implementation to pass.

---

## Final file structure

- `assistant.py`: immutable contracts, fixture loading, deterministic metadata matching, role access check, grounded outcome, and prepared case.
- `app.py`: role selector, five suggestion buttons, arbitrary chat input, outcome rendering, and conditional case preview.
- `data/knowledge.json`: four synthetic documents with IDs, links, keywords, answers, and permitted roles.
- `tests/test_assistant.py`: backend behaviour and Streamlit AppTest coverage.
- `requirements.txt`: exact Streamlit runtime dependency.
- `README.md`: scope, run/test instructions, walkthrough, Microsoft mapping, and non-goals.

## Task 1: Implement the complete two-block backend test-first

**Files:**
- Create: `assistant.py`
- Replace: `data/knowledge.json`
- Create: `tests/test_assistant.py`

**Interfaces:**
- Produces: `Document`, `AgentCase`, `Result`, `load_documents(path)`, and `answer_question(question, role, documents)`.
- `Result.status` is one of `answer`, `access_denied`, or `unavailable`.
- `answer_question()` receives a trusted allowlisted role and an already loaded document list.

- [ ] **Step 1: Replace the fixture with four synthetic documents**

Write this exact JSON to `data/knowledge.json`:

```json
[
  {
    "id": "OPS-001",
    "title": "Faulty equipment reporting",
    "answer": "Make the area safe, tell the shift leader, record the store and equipment details, then use the approved maintenance request process.",
    "url": "https://pret.example/documents/OPS-001",
    "keywords": ["faulty", "fridge", "equipment", "maintenance", "report"],
    "roles": ["Store colleague", "Store manager"]
  },
  {
    "id": "OPS-002",
    "title": "Repeated equipment fault escalation",
    "answer": "Review the previous fault history and use the manager escalation route when the approved repeat-fault threshold is met.",
    "url": "https://pret.example/documents/OPS-002",
    "keywords": ["repeated", "equipment", "fault", "faults", "escalation", "thresholds"],
    "roles": ["Store manager"]
  },
  {
    "id": "HR-001",
    "title": "Colleague absence reporting",
    "answer": "Tell the appropriate store contact as soon as possible and follow the approved absence reporting process.",
    "url": "https://pret.example/documents/HR-001",
    "keywords": ["absence", "absent", "attend", "shift", "report"],
    "roles": ["Store colleague", "Store manager"]
  },
  {
    "id": "OPS-003",
    "title": "Store opening checks",
    "answer": "Complete the approved opening checklist before service and report any failed safety or equipment check to the shift leader.",
    "url": "https://pret.example/documents/OPS-003",
    "keywords": ["checks", "checklist", "opening", "open", "store"],
    "roles": ["Store colleague", "Store manager"]
  }
]
```

- [ ] **Step 2: Write all backend tests before creating `assistant.py`**

Create `tests/test_assistant.py`:

```python
import unittest
from pathlib import Path

from assistant import Document, answer_question, load_documents


ROOT = Path(__file__).resolve().parents[1]


class AssistantTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.documents = load_documents(ROOT / "data" / "knowledge.json")

    def test_store_colleague_receives_permitted_answer_and_source(self) -> None:
        result = answer_question(
            "How do I report a faulty display fridge?",
            "Store colleague",
            self.documents,
        )

        self.assertEqual(result.status, "answer")
        self.assertIn("maintenance request", result.message)
        self.assertEqual(result.document_id, "OPS-001")
        self.assertEqual(result.document_url, "https://pret.example/documents/OPS-001")
        self.assertIsNone(result.case)

    def test_store_manager_can_read_a_general_document(self) -> None:
        result = answer_question(
            "How do I report that I cannot attend a shift?",
            "Store manager",
            self.documents,
        )

        self.assertEqual(result.status, "answer")
        self.assertEqual(result.document_id, "HR-001")

    def test_colleague_is_denied_manager_only_guidance_without_source_leakage(self) -> None:
        result = answer_question(
            "What are the escalation thresholds for repeated equipment faults?",
            "Store colleague",
            self.documents,
        )

        self.assertEqual(result.status, "access_denied")
        self.assertEqual(
            result.message,
            "Sorry, you do not have the correct access level. Ask your manager to make this request.",
        )
        self.assertIsNone(result.document_id)
        self.assertIsNone(result.document_url)
        self.assertNotIn("repeat-fault threshold", result.message)

    def test_manager_receives_manager_only_guidance(self) -> None:
        result = answer_question(
            "What are the escalation thresholds for repeated equipment faults?",
            "Store manager",
            self.documents,
        )

        self.assertEqual(result.status, "answer")
        self.assertEqual(result.document_id, "OPS-002")
        self.assertIn("manager escalation route", result.message)

    def test_unsupported_question_prepares_complete_agent_case(self) -> None:
        result = answer_question(
            "What is the approved supplier invoice process?",
            "Store colleague",
            self.documents,
        )

        self.assertEqual(result.status, "unavailable")
        self.assertEqual(
            result.message,
            "I don't have this information available. Would you like to talk to an agent?",
        )
        self.assertIsNotNone(result.case)
        self.assertEqual(result.case.question, "What is the approved supplier invoice process?")
        self.assertEqual(result.case.role, "Store colleague")
        self.assertEqual(result.case.search_outcome, "No approved document matched")
        self.assertEqual(result.case.documents_checked, 4)
        self.assertEqual(result.case.reason, "Approved information unavailable")
        self.assertRegex(result.case.reference, r"^CASE-[0-9A-F]{8}$")

    def test_empty_question_requests_input_without_agent_case(self) -> None:
        result = answer_question("  ", "Store colleague", self.documents)

        self.assertEqual(result.status, "unavailable")
        self.assertEqual(result.message, "Please enter a question.")
        self.assertIsNone(result.case)

    def test_unknown_role_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unknown role"):
            answer_question("How do I report a faulty fridge?", "Administrator", self.documents)

    def test_equal_matches_are_resolved_by_document_id(self) -> None:
        tied = [
            Document("ZZZ", "Fridge help", "Second", "https://pret.example/ZZZ", ("fridge",), ("Store colleague",)),
            Document("AAA", "Fridge help", "First", "https://pret.example/AAA", ("fridge",), ("Store colleague",)),
        ]

        result = answer_question("fridge", "Store colleague", tied)

        self.assertEqual(result.document_id, "AAA")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run the backend tests and verify RED**

Run:

```bash
python3 -m unittest tests.test_assistant.AssistantTests -v
```

Expected: import failure because `assistant.py` does not exist. This confirms the new tests are exercising the replacement slice rather than the previous package.

- [ ] **Step 4: Implement only the tested backend behaviour**

Create `assistant.py`:

```python
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

    document = ranked[0]
    if role not in document.roles:
        return Result(
            status="access_denied",
            message="Sorry, you do not have the correct access level. Ask your manager to make this request.",
        )

    return Result(
        status="answer",
        message=document.answer,
        document_id=document.id,
        document_url=document.url,
    )
```

- [ ] **Step 5: Run the backend tests and verify GREEN**

Run `python3 -m unittest tests.test_assistant.AssistantTests -v`.

Expected: eight tests pass.

- [ ] **Step 6: Commit the backend slice**

```bash
git add assistant.py data/knowledge.json tests/test_assistant.py
git commit -m "feat: add focused access and retrieval slice"
```

## Task 2: Add the minimal Streamlit chatbot test-first

**Files:**
- Create: `requirements.txt`
- Replace: `app.py`
- Modify: `tests/test_assistant.py`

**Interfaces:**
- Consumes: `ROLES`, `load_documents()`, and `answer_question()`.
- Produces: role selector, five suggestion buttons, arbitrary chat input, outcome display, and conditional case preview.

- [ ] **Step 1: Pin Streamlit**

Create `requirements.txt`:

```text
streamlit==1.60.0
```

Streamlit 1.60.0 requires Python 3.10 or later and provides `streamlit.testing.v1.AppTest` for headless UI testing.

- [ ] **Step 2: Install dependencies outside the repository**

Use `mktemp -d` to create a temporary virtual environment, install `requirements.txt`, and retain its explicit Python and Streamlit paths for the remaining checks. Do not create `.venv` inside the repository.

- [ ] **Step 3: Write the failing UI tests**

Append to `tests/test_assistant.py`:

```python
from streamlit.testing.v1 import AppTest


class AppTests(unittest.TestCase):
    def test_role_change_changes_manager_question_outcome(self) -> None:
        app = AppTest.from_file(ROOT / "app.py").run()

        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.button), 5)
        self.assertEqual(len(app.chat_input), 1)
        app.button(key="suggestion-2").click().run()
        self.assertIn("correct access level", app.warning[0].value)

        app.selectbox(key="role").select("Store manager").run()
        self.assertIn("manager escalation route", app.success[0].value)

    def test_unsupported_question_reveals_case_only_after_confirmation(self) -> None:
        app = AppTest.from_file(ROOT / "app.py").run()
        app.button(key="suggestion-5").click().run()

        self.assertIn("talk to an agent", app.info[0].value.casefold())
        self.assertEqual(len(app.json), 0)
        app.button(key="talk-to-agent").click().run()
        self.assertEqual(len(app.json), 1)
        self.assertIn("CASE-", str(app.json[0].value))
```

- [ ] **Step 4: Run the UI tests and verify RED**

Run `python -m unittest tests.test_assistant.AppTests -v` using the temporary environment.

Expected: failure because the existing `app.py` is a command-line program and does not render the required widgets.

- [ ] **Step 5: Replace `app.py` with the thin interface**

```python
from dataclasses import asdict
from pathlib import Path

import streamlit as st

from assistant import ROLES, answer_question, load_documents


ROOT = Path(__file__).resolve().parent
QUESTIONS = (
    "How do I report a faulty display fridge?",
    "What are the escalation thresholds for repeated equipment faults?",
    "How do I report that I cannot attend a shift?",
    "What checks are required when opening the store?",
    "What is the approved supplier invoice process?",
)


@st.cache_data
def documents():
    return load_documents(ROOT / "data" / "knowledge.json")


st.set_page_config(page_title="Pret Colleague Assist", page_icon="🥪", layout="centered")
st.title("Pret Colleague Assist")
st.caption("Prototype slice: access control → permission-aware retrieval")

role = st.selectbox("Demo role", ROLES, key="role")
st.write("Try a suggested question or ask your own:")
for index, suggested_question in enumerate(QUESTIONS, start=1):
    if st.button(
        suggested_question,
        key=f"suggestion-{index}",
        use_container_width=True,
    ):
        st.session_state.question = suggested_question
        st.session_state.show_case = False

typed_question = st.chat_input("Ask about approved colleague guidance")
if typed_question:
    st.session_state.question = typed_question
    st.session_state.show_case = False

question = st.session_state.get("question")
if question:
    result = answer_question(question, role, documents())
    with st.chat_message("user"):
        st.write(question)
    with st.chat_message("assistant"):
        if result.status == "answer":
            st.success(result.message)
            st.markdown(f"Source: [{result.document_id}]({result.document_url})")
        elif result.status == "access_denied":
            st.warning(result.message)
        else:
            st.info(result.message)
            if result.case and st.button("Talk to an agent", key="talk-to-agent"):
                st.session_state.show_case = True
            if result.case and st.session_state.get("show_case"):
                st.subheader("What the agent receives")
                st.json(asdict(result.case))
```

- [ ] **Step 6: Run all tests and verify GREEN**

Run `python -m unittest discover -s tests -v` using the temporary environment.

Expected: ten tests pass.

- [ ] **Step 7: Commit the interface**

```bash
git add app.py requirements.txt tests/test_assistant.py
git commit -m "feat: add role-aware retrieval demo"
```

## Task 3: Remove superseded scope and prepare the interviewer handoff

**Files:**
- Replace: `README.md`
- Delete: `pret_assistant/__init__.py`
- Delete: `pret_assistant/answer.py`
- Delete: `pret_assistant/evaluation.py`
- Delete: `pret_assistant/guardrails.py`
- Delete: `pret_assistant/models.py`
- Delete: `pret_assistant/policy.py`
- Delete: `pret_assistant/retrieval.py`
- Delete: `pret_assistant/service.py`
- Delete: `evals/run_evaluations.py`
- Delete: `evals/test_cases.json`
- Delete: `tests/test_answer.py`
- Delete: `tests/test_evaluations.py`
- Delete: `tests/test_policy.py`
- Delete: `tests/test_retrieval.py`
- Delete: `docs/superpowers/specs/2026-08-19-access-rag-prototype-design.md`
- Delete: `docs/superpowers/plans/2026-08-19-access-rag-prototype.md`

**Interfaces:**
- Leaves exactly the six interviewer-facing files named in the global constraints.

- [ ] **Step 1: Rewrite the README**

Use this concise content:

````markdown
# Pret Colleague Assist

A deliberately small interview prototype implementing two consecutive blocks:

`Access control → Permission-aware retrieval`

The user selects a demonstration role, asks any question or chooses one of five examples, and receives an approved answer, an access refusal, or a prepared human-handoff preview.

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Test

```bash
python -m unittest discover -s tests -v
```

## Outcomes

- Allowed: returns the synthetic grounded answer, document ID and link.
- Restricted: reveals no document details and asks the colleague to contact their manager.
- Unavailable: offers human support and shows the context an agent would receive after confirmation.

## Files to show

- `app.py`: the thin Streamlit interface.
- `assistant.py`: metadata matching, role check and grounded result.
- `data/knowledge.json`: synthetic content and access metadata.
- `tests/test_assistant.py`: role-dependent and handoff behaviour.

## Production mapping

- The role selector represents trusted Entra claims.
- The JSON fixture represents approved SharePoint or Dataverse content.
- Local metadata matching represents an Azure AI Search index or Copilot Studio knowledge source with security trimming.
- A production model may generate wording only after permitted evidence is retrieved.

## Scope

This repository does not implement Copilot Studio, a live model, prompt guardrails, tool calling, case creation, orchestration, telemetry or deployment. Those belong to the wider design; excluding them is intentional.

All guidance and links are synthetic demonstration data, not official Pret policy.
````

- [ ] **Step 2: Delete only the superseded files listed for Task 3**

Use explicit patch deletions. Confirm the remaining inventory with `rg --files | sort`.

Expected:

```text
.gitignore
README.md
app.py
assistant.py
data/knowledge.json
requirements.txt
tests/test_assistant.py
```

- [ ] **Step 3: Run the full regression suite after deletion**

Run `python -m unittest discover -s tests -v`.

Expected: ten tests pass.

- [ ] **Step 4: Start Streamlit and verify the running application**

Run Streamlit from the temporary environment on an available localhost port. Verify its health endpoint returns `ok`, then inspect the browser UI and confirm:

- Five suggestion buttons are visible.
- The role selector offers exactly two roles.
- Arbitrary text can be entered through the chat input.
- The manager-only question changes from warning to answer when the role changes.
- The unsupported question does not show case details before `Talk to an agent` is clicked.
- The case preview appears after the click and contains the original question and current role.
- No restricted document ID or link appears in the colleague denial view.

- [ ] **Step 5: Run final repository checks**

Run:

```bash
git diff --check
rg --files | sort
git status --short
```

Verify that only the six expected application files and `.gitignore` remain, no credentials or cache files exist, and the diff contains no unrelated changes.

- [ ] **Step 6: Commit the final scoped repository**

```bash
git add -A
git commit -m "refactor: reduce prototype to access and retrieval slice"
```
