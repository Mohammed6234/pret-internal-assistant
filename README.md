# Pret Internal Assistant

Small Python implementation of a permission-aware internal support assistant.

The project demonstrates how an employee question can be checked for risk, matched against approved content, filtered by access scope and returned as an answer, refusal or escalation.

It runs locally with the Python standard library and does not require Azure credentials, network access or a live Pret system.

## Flow

```text
Question
   |
   v
Guardrails
   |
   v
Permission check
   |
   v
Evidence retrieval
   |
   +--> Answer with evidence
   +--> Refuse when evidence is missing
   +--> Escalate high-risk requests
```

## Run

Use Python 3.11 or later.

From the repository root:

```bash
python3 app.py
```

Run one question:

```bash
python3 app.py --question "What is the approved process for reporting a faulty display fridge?"
```

Run as a manager to access manager-scoped content:

```bash
python3 app.py \
  --group store-manager \
  --question "What are the manager-only escalation thresholds for repeated equipment faults?"
```

Run the evaluation cases:

```bash
python3 evals/run_evaluations.py
```

Run the test suite:

```bash
python3 -m unittest discover -s tests -v
```

## Repository structure

```text
app.py                         Command-line entry point
data/knowledge.json            Synthetic approved-content fixture
pret_assistant/models.py       Shared data contracts
pret_assistant/policy.py       Market, group and store access checks
pret_assistant/guardrails.py   Refusal and escalation rules
pret_assistant/retrieval.py    Permission-filtered local retrieval
pret_assistant/answer.py       Answer, refusal and escalation responses
pret_assistant/service.py      End-to-end request orchestration
pret_assistant/evaluation.py   Evaluation case runner
evals/test_cases.json          Expected behaviours
evals/run_evaluations.py       Evaluation command
tests/                         Unit and integration tests
```

## Microsoft service mapping

The repository uses local implementations to represent selected Microsoft service responsibilities.

| Microsoft role | Local implementation | Production replacement |
|---|---|---|
| Teams/Copilot Studio entry point | `app.py` and `AssistantService.handle()` | Copilot Studio published to Teams |
| Approved knowledge source | `data/knowledge.json` | SharePoint, Dataverse or another approved source |
| Azure AI Search retrieval | `InMemoryRetriever` | Azure AI Search or Copilot Studio native retrieval |
| Entra identity and permissions | `UserContext` and `is_document_allowed()` | Entra claims, groups and document-level permissions |
| Guardrails | `guardrails.py` | Deterministic policy, safety classification and human escalation |
| Foundry/Azure OpenAI model boundary | `AnswerGenerator` protocol | Azure OpenAI or Microsoft Foundry model adapter |
| Power Automate/Azure Function action boundary | `AnswerResponse` and `service.py` | Typed connector, Power Automate flow or Azure Function |
| Evaluation and monitoring | `evals/` and `tests/` | CI evaluation, Foundry evaluation and Azure Monitor/Application Insights |

The local version intentionally has no live write action. A production action would require confirmation, permission checks, validation, idempotency and a write to the existing system of record.

## Use of AI during development

AI assistance was used as a prototyping aid to help structure the service mapping, draft representative synthetic knowledge entries and suggest evaluation scenarios. The resulting fixture data was then kept small and explicit so that every permission rule and expected response can be inspected in the repository.

AI assistance was not used as a runtime authority. The current implementation does not call a language model. Its answer generator is deterministic and its retrieval is local lexical matching, which makes the demo reproducible and usable without credentials.

The `AnswerGenerator` protocol is the replacement point for a model in a Microsoft deployment. In production, a reviewed adapter could call Azure OpenAI or Foundry after guardrails and permission-aware retrieval had completed.

The knowledge entries in `data/knowledge.json` are synthetic demonstration content, not official Pret policy. In a real implementation, approved content would come from the relevant business owners and an authorised source such as SharePoint or Dataverse. AI-generated drafts should never become operational policy without human review.

## What is demonstrated

- A store colleague can retrieve permitted UK equipment guidance.
- Manager-only content is not returned to a store colleague.
- Unsupported questions are refused instead of answered from weak evidence.
- Prompt-injection-style requests are refused.
- Food-safety and other high-risk requests are escalated.
- Every normal answer contains the IDs of the documents used as evidence.

