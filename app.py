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
