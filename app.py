"""
RegIntel AI — Compliance Copilot
LLM-first + RAG-on-demand · Sessions + Exports
"""

import os
import json
import time
from datetime import datetime
from pathlib import Path

import streamlit as st

from config import MODEL_NAME, SUGGESTED_PROMPTS, OPENAI_API_KEY
from utils.rag_engine import RAGEngine
from utils.document_processor import (
    extract_text_from_file,
    chunk_documents,
    chunk_documents_by_headings,
    format_citations,
)
from utils.export import (
    export_to_csv,
    format_conversation_for_export,
    export_to_pdf,
    export_to_json,
)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
SESS_DIR = BASE_DIR / ".sessions"
SESS_DIR.mkdir(exist_ok=True)

# ------------- Page config -------------
st.set_page_config(
    page_title="RegIntel AI",
    page_icon="assets/hexabank_favicon.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------- CSS -------------
def load_custom_css():
    st.markdown(
        """
    <style>
    .main { background:#FFFFFF; }
    .block-container { padding-top: 1.2rem; padding-bottom: 1.2rem; max-width: 1200px; }

    [data-testid="stSidebar"] {
        background:#FFFFFF;
        border-right:1px solid #e5e7eb;
        padding-top:.5rem;
    }
    [data-testid="stSidebar"] img {
        display:block;
        margin-left:auto;
        margin-right:auto;
    }
    .sidebar-title {
        color:#D11E1E;
        font-size:22px;
        font-weight:800;
        text-align:center;
        margin:.25rem 0 .1rem 0;
    }
    .sidebar-sub {
        text-align:center;
        color:#6b7280;
        font-size:12px;
        margin:0 0 .5rem 0;
    }

    .main-title { text-align:center; font-size:40px; font-weight:800; color:#111827; margin: 10px 0 4px 0; }
    .hint { text-align:center; color:#6b7280; margin-bottom: 12px; }

    .suggestions-container { max-width: 900px; margin: 0 auto 10px auto; padding: 0 20px; }
    .suggestion-item { background:#f8fafc; padding:10px 14px; margin:6px 0; border-radius:10px; border-left:3px solid #D11E1E; font-size:14px; color:#111827; }

    .badge { display:inline-block; padding:2px 8px; border-radius:999px; font-size:11px; margin-left:8px; background:#eef2ff; color:#3730a3; }
    .upload-help { color:#6b7280; font-size:13px; margin-top:-6px; }

    #MainMenu {visibility: visible;}
    header {visibility: visible;}
    footer {visibility: hidden;}
    </style>
    """,
        unsafe_allow_html=True,
    )

# ------------- Session -------------
def init_session_state():
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("rag_engine", None)
    st.session_state.setdefault("uploaded_files", [])
    st.session_state.setdefault("show_quick_upload", False)
    st.session_state.setdefault("prefer_rag", True)
    st.session_state.setdefault("answer_mode", "Auto")
    st.session_state.setdefault("session_file", None)


def initialize_rag():
    if st.session_state.rag_engine is None:
        try:
            st.session_state.rag_engine = RAGEngine()
        except Exception as e:
            st.error(f"❌ RAG init error: {e}")
            return False
    return True

# ------------- Sidebar -------------
def render_sidebar():
    with st.sidebar:
        # Logo HexaBank
        logo_path = BASE_DIR / "assets" / "hexabank_logo.png"
        if logo_path.exists():
            st.image(str(logo_path))
        else:
            st.markdown("HEXABANK", unsafe_allow_html=True)

        # Titre / sous-titre
        st.markdown('<div class="sidebar-title">RegIntel AI</div>', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-sub">Compliance Copilot</div>', unsafe_allow_html=True)

        st.markdown("---")

        # Options RAG / mode de réponse
        st.checkbox("Use RAG when available", value=st.session_state.prefer_rag, key="prefer_rag")

        st.radio(
            "Answer mode",
            options=["Auto", "Overview", "Gap analysis", "Remediation plan"],
            key="answer_mode",
        )

        # Nouvelle conversation
        if st.button("💬 New chat"):
            st.session_state.messages = []
            st.session_state.session_file = None
            st.rerun()

        # Upload rapide (ouvre l’expander en main)
        if st.button("📄 Upload documents"):
            st.session_state.show_quick_upload = True
            st.rerun()

        # ---------------- Corpus actif ----------------
        st.markdown("---")
        st.markdown("**Active corpus**")

        preload = []
        if DATA_DIR.exists():
            for p in sorted(DATA_DIR.iterdir()):
                if p.is_file():
                    preload.append(p.name)

        if preload:
            st.caption("Preloaded regulatory docs:")
            for fn in preload:
                st.write(f"• {fn}")
        else:
            st.caption("No preloaded documents.")

        if st.session_state.uploaded_files:
            st.caption("User-uploaded documents:")
            for fn in st.session_state.uploaded_files:
                st.write(f"• {fn}")
        else:
            st.caption("No user-uploaded documents yet.")

        # Clear vector store
        if st.button("🗑️ Clear vector store"):
            if initialize_rag():
                st.session_state.rag_engine.clear_collection()
            st.session_state.uploaded_files = []
            st.success("Vector store cleared.")
            st.rerun()

        # ---------------- Save / Export / Load sessions ----------------
        if st.session_state.messages:
            st.markdown("---")
            st.markdown("### Save / Export")

            # Sauvegarde de la session dans .sessions/
            if st.button("💾 Save session"):
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                f = SESS_DIR / f"session_{ts}.json"
                with open(f, "w", encoding="utf-8") as fh:
                    json.dump(st.session_state.messages, fh, ensure_ascii=False, indent=2)
                st.session_state.session_file = str(f)
                st.success(f"Saved: {f.name}")

            # Exports téléchargeables
            txt_export = format_conversation_for_export(st.session_state.messages)
            st.download_button(
                "TXT",
                data=txt_export,
                file_name=f"regintel_{int(time.time())}.txt",
                mime="text/plain",
            )

            csv_export = export_to_csv(st.session_state.messages)
            st.download_button(
                "CSV",
                data=csv_export,
                file_name=f"regintel_{int(time.time())}.csv",
                mime="text/csv",
            )

            try:
                pdf_export = export_to_pdf(st.session_state.messages)
                st.download_button(
                    "PDF",
                    data=pdf_export,
                    file_name=f"regintel_{int(time.time())}.pdf",
                    mime="application/pdf",
                )
            except RuntimeError:
                st.info("Install PDF export with: pip install reportlab")

            json_export = export_to_json(st.session_state.messages)
            st.download_button(
                "JSON",
                data=json_export,
                file_name=f"regintel_{int(time.time())}.json",
                mime="application/json",
            )

            # -------- Load session depuis .sessions/ --------
            st.markdown("### Load session")
            saved_files = sorted(SESS_DIR.glob("session_*.json"))

            if saved_files:
                options = ["-- Select --"] + [f.name for f in saved_files]
                choice = st.selectbox("Saved sessions", options, index=0)
                if choice != "-- Select --":
                    if st.button("📂 Load selected"):
                        path = SESS_DIR / choice
                        try:
                            with open(path, "r", encoding="utf-8") as fh:
                                st.session_state.messages = json.load(fh)
                            st.session_state.session_file = str(path)
                            st.success(f"Session {choice} loaded")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error loading session: {e}")
            else:
                st.caption("No saved sessions yet.")

# ------------- Quick upload -------------
def quick_upload_zone():
    expanded = st.session_state.get("show_quick_upload", False)
    with st.expander("📎 Quick upload (PDF/DOCX/CSV/TXT/MD)", expanded=expanded):
        uploaded_files = st.file_uploader(
            "Choose files",
            type=["pdf", "docx", "csv", "txt", "md"],
            accept_multiple_files=True,
            label_visibility="collapsed",
        )
        st.markdown(
            '<div class="upload-help">Files are embedded into the local vector store (Chroma).</div>',
            unsafe_allow_html=True,
        )
        if uploaded_files and st.button("📤 Process", type="primary"):
            if not initialize_rag():
                return
            ok = 0
            for f in uploaded_files:
                text = extract_text_from_file(f, f.name)
                lower = f.name.lower()
                use_head = any(
                    k in lower
                    for k in [
                        "bcbs",
                        "rdarr",
                        "ai act",
                        "gdpr",
                        "eba",
                        "ecb",
                        "guideline",
                        "policy",
                        "procedure",
                        "charter",
                        "charte",
                    ]
                )
                chunks = (
                    chunk_documents_by_headings(text, f.name)
                    if use_head
                    else chunk_documents(text, f.name)
                )
                st.session_state.rag_engine.add_documents(chunks)
                if f.name not in st.session_state.uploaded_files:
                    st.session_state.uploaded_files.append(f.name)
                ok += 1
            if ok:
                st.session_state.show_quick_upload = False
                st.success(f"{ok} document(s) processed.")
                st.rerun()

# ------------- Welcome + prompts cliquables -------------
def render_welcome():
    st.markdown('<div class="main-title">How can I help you?</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hint">Ask in English or French · RAG auto when evidence exists</div>',
        unsafe_allow_html=True,
    )
    quick_upload_zone()

    # Suggestions affichées au centre
    st.markdown(
        """
    <div class="suggestions-container">
      <div class="suggestion-item">• Perform a gap analysis between HexaBank – Data Management Procedure and BCBS 239.</div>
      <div class="suggestion-item">• Can you introduce me to all the principles of BCBS 239?</div>
      <div class="suggestion-item">• Explain the ECB expectations on BCBS 239 based on the thematic review.</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Boutons rapides
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Ask: Gap HexaBank vs BCBS 239"):
            _fire_prompt(
                "Perform a gap analysis between HexaBank – Data Management Procedure and BCBS 239."
            )
    with col2:
        if st.button("Ask: BCBS 239 principles"):
            _fire_prompt("Can you introduce me to all the principles of BCBS 239?")
    with col3:
        if st.button("Ask: ECB expectations on BCBS 239"):
            _fire_prompt("Explain the ECB expectations on BCBS 239 based on the thematic review.")


def _fire_prompt(text: str):
    initialize_rag()
    st.session_state.messages.append({"role": "user", "content": text})
    result = st.session_state.rag_engine.answer(
        text,
        prefer_rag=st.session_state.prefer_rag,
        answer_mode=st.session_state.answer_mode,
    )
    cites_md = format_citations(result.get("sources", []))
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": result.get("answer", ""),
            "sources": cites_md,
            "mode": result.get("mode", ""),
        }
    )
    st.rerun()

# ------------- Chat -------------
def render_chat():
    # Affichage de l'historique
    for m in st.session_state.messages:
        mode_badge = f' <span class="badge">{m.get("mode","")}</span>' if m.get("mode") else ""
        with st.chat_message(m["role"], avatar="👤" if m["role"] == "user" else "🛡️"):
            st.markdown(m["content"] + mode_badge, unsafe_allow_html=True)
            if m.get("sources"):
                with st.expander("📚 Sources"):
                    st.markdown(m["sources"], unsafe_allow_html=True)

    # Nouveau prompt
    if prompt := st.chat_input("Message RegIntel AI"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("assistant", avatar="🛡️"):
            initialize_rag()
            with st.spinner("Analyzing..."):
                try:
                    result = st.session_state.rag_engine.answer(
                        prompt,
                        prefer_rag=st.session_state.prefer_rag,
                        answer_mode=st.session_state.answer_mode,
                    )
                    cites_md = format_citations(result.get("sources", []))
                    content = result.get("answer", "")
                    mode = result.get("mode", "")
                    st.markdown(
                        content + (f' <span class="badge">{mode}</span>' if mode else ""),
                        unsafe_allow_html=True,
                    )
                    if cites_md:
                        with st.expander("📚 Sources"):
                            st.markdown(cites_md, unsafe_allow_html=True)
                    elif mode == "LLM":
                        st.info("ℹ️ General answer (no internal sources used).")
                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": content,
                            "sources": cites_md,
                            "mode": mode,
                        }
                    )
                    # Important : relancer un run pour que la sidebar voie les messages
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {e}")

# ------------- Main -------------
def main():
    load_custom_css()
    init_session_state()
    initialize_rag()
    render_sidebar()
    if not st.session_state.messages:
        render_welcome()
    render_chat()


if __name__ == "__main__":
    main()
