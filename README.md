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

