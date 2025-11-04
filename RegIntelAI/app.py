"""
RegIntel AI - Regulatory Intelligence Assistant
Modern ChatGPT-style Interface
"""
import streamlit as st
import os
from datetime import datetime
from typing import List, Dict
from config import (
    APP_TITLE,
    APP_SUBTITLE,
    MODEL_NAME,
    EMBEDDING_MODEL,
    CHUNK_SIZE,
    TOP_K_RESULTS,
    SUGGESTED_PROMPTS,
    OPENAI_API_KEY
)
from utils.rag_engine import RAGEngine
from utils.document_processor import (
    extract_text_from_file, 
    chunk_documents, 
    format_citations, 
    load_documents_from_folder
)
from utils.export import export_to_csv, format_conversation_for_export

# Configuration de la page
st.set_page_config(
    page_title="RegIntel AI",
    page_icon="🔷",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé pour le style moderne
def load_custom_css():
    st.markdown("""
    <style>
    /* Reset et style général */
    .main {
        background-color: white;
    }
    
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: white;
        border-right: 1px solid #e0e0e0;
        padding-top: 1rem;
    }
    
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 0;
    }
    
    /* Logo et titre dans la sidebar */
    .sidebar-header {
        text-align: center;
        padding: 10px 20px 20px 20px;
        border-bottom: 1px solid #e0e0e0;
        margin-bottom: 20px;
    }
    
    .sidebar-icon {
        font-size: 32px;
        margin-bottom: 10px;
    }
    
    .sidebar-title {
        color: #DC143C;
        font-size: 22px;
        font-weight: 600;
        margin: 0;
    }
    
    /* Boutons de la sidebar */
    .stButton button {
        width: 100%;
        border-radius: 8px;
        padding: 10px;
        font-size: 15px;
        border: 1px solid #e0e0e0;
        background-color: white;
        transition: all 0.3s;
    }
    
    .stButton button:hover {
        background-color: #f5f5f5;
        border-color: #ccc;
    }
    
    /* Titre principal centré */
    .main-title {
        text-align: center;
        font-size: 42px;
        font-weight: 400;
        color: #202124;
        margin-top: 80px;
        margin-bottom: 60px;
    }
    
    /* Zone de saisie */
    .chat-input-container {
        max-width: 800px;
        margin: 0 auto 30px auto;
    }
    
    /* Suggestions */
    .suggestions-container {
        max-width: 800px;
        margin: 0 auto;
        padding: 0 20px;
    }
    
    .suggestions-intro {
        text-align: left;
        color: #5f6368;
        font-size: 14px;
        margin-bottom: 20px;
        line-height: 1.6;
    }
    
    .suggestion-item {
        background-color: #f8f9fa;
        padding: 14px 18px;
        margin: 10px 0;
        border-radius: 8px;
        border-left: 3px solid #DC143C;
        font-size: 14px;
        color: #202124;
        line-height: 1.5;
        cursor: default;
    }
    
    /* Messages du chat */
    .chat-message {
        max-width: 800px;
        margin: 20px auto;
        padding: 15px 20px;
        border-radius: 12px;
    }
    
    .user-message {
        background-color: #f1f3f4;
        text-align: right;
    }
    
    .assistant-message {
        background-color: white;
        border: 1px solid #e0e0e0;
    }
    
    /* Upload zone */
    .upload-container {
        max-width: 800px;
        margin: 40px auto;
        padding: 40px;
        border: 2px dashed #dadce0;
        border-radius: 12px;
        text-align: center;
        background-color: #fafafa;
    }
    
    .upload-icon {
        font-size: 48px;
        margin-bottom: 20px;
        color: #5f6368;
    }
    
    .upload-text {
        color: #5f6368;
        font-size: 16px;
        margin-bottom: 20px;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Ajustements pour les éléments Streamlit */
    .stChatFloatingInputContainer {
        bottom: 20px;
    }
    
    /* Style des expanders */
    .streamlit-expanderHeader {
        font-size: 14px;
        color: #5f6368;
    }
    
    </style>
    """, unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables"""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'rag_engine' not in st.session_state:
        st.session_state.rag_engine = None
    if 'documents_loaded' not in st.session_state:
        st.session_state.documents_loaded = False
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = []
    if 'show_upload' not in st.session_state:
        st.session_state.show_upload = False


def initialize_rag():
    """Initialize RAG engine if not already done"""
    if st.session_state.rag_engine is None:
        try:
            st.session_state.rag_engine = RAGEngine()
        except Exception as e:
            st.error(f"❌ Error initializing RAG engine: {str(e)}")
            return False
    return True


def render_sidebar():
    """Render the modern sidebar with navigation"""
    with st.sidebar:
        # Logo et titre
        st.markdown("""
        <div class="sidebar-header">
            <div class="sidebar-icon">🔷</div>
            <div class="sidebar-title">RegIntel AI</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Bouton Nouveau Chat
        if st.button("💬  Nouveau chat", key="new_chat_btn"):
            st.session_state.messages = []
            st.session_state.show_upload = False
            st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Bouton Recherche
        st.button("🔍  Recherche", key="search_btn")
        
        # Bouton Documents
        if st.button("📄  Upload Documents", key="docs_btn"):
            st.session_state.show_upload = not st.session_state.get('show_upload', False)
            st.rerun()
        
        # Bouton Load from Data Folder
        if st.button("📁  Load from Data Folder", key="load_folder_btn"):
            if initialize_rag():
                if load_documents_from_data_folder():
                    st.success(f"Loaded {len(st.session_state.uploaded_files)} document(s)!")
                    st.rerun()
        
        st.markdown("---")
        
        # Informations sur les documents
        if st.session_state.documents_loaded:
            st.success(f"{len(st.session_state.uploaded_files)} document(s) loaded")
            
            with st.expander("📚 Active Documents", expanded=True):
                for idx, doc in enumerate(st.session_state.uploaded_files):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.write(f"📄 {doc}")
                    with col2:
                        if st.button("🗑️", key=f"del_{idx}", help="Remove this document"):
                            st.session_state.uploaded_files.remove(doc)
                            if len(st.session_state.uploaded_files) == 0:
                                st.session_state.rag_engine.clear_collection()
                                st.session_state.documents_loaded = False
                            st.rerun()
            
            if st.button("🗑️  Clear All Documents"):
                st.session_state.rag_engine.clear_collection()
                st.session_state.documents_loaded = False
                st.session_state.uploaded_files = []
                st.success("All documents cleared!")
                st.rerun()
        
        # Export
        if st.session_state.messages:
            st.markdown("---")
            st.markdown("### 💾 Export")
            
            txt_export = format_conversation_for_export(st.session_state.messages)
            st.download_button(
                label="📄  Exporter (TXT)",
                data=txt_export,
                file_name=f"regintel_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )
            
            csv_export = export_to_csv(st.session_state.messages)
            st.download_button(
                label="📊  Exporter (CSV)",
                data=csv_export,
                file_name=f"regintel_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )


def process_uploaded_file(uploaded_file):
    """Process an uploaded file (PDF, DOCX, TXT, MD)"""
    try:
        with st.spinner(f"Processing {uploaded_file.name}..."):
            # Extract text from file
            text = extract_text_from_file(uploaded_file, uploaded_file.name)
            
            # Chunk the document
            chunks = chunk_documents(text, uploaded_file.name)
            
            # Add to vector store
            st.session_state.rag_engine.add_documents(chunks)
            
            # Track loaded documents
            if uploaded_file.name not in st.session_state.uploaded_files:
                st.session_state.uploaded_files.append(uploaded_file.name)
            
            st.session_state.documents_loaded = True
            
            return True
    except Exception as e:
        st.error(f"Error processing {uploaded_file.name}: {str(e)}")
        return False


def load_documents_from_data_folder():
    """Load all documents from the data/sample_documents folder"""
    try:
        data_folder = os.path.join(os.path.dirname(__file__), "data", "sample_documents")
        
        if not os.path.exists(data_folder):
            st.warning("No data folder found. Create 'data/sample_documents' and add documents.")
            return False
        
        documents = load_documents_from_folder(data_folder)
        
        if not documents:
            st.info("No documents found in data/sample_documents folder.")
            return False
        
        with st.spinner(f"Loading {len(documents)} document(s) from folder..."):
            for doc in documents:
                # Chunk the document
                chunks = chunk_documents(doc['text'], doc['filename'])
                
                # Add to vector store
                st.session_state.rag_engine.add_documents(chunks)
                
                # Track loaded documents
                if doc['filename'] not in st.session_state.uploaded_files:
                    st.session_state.uploaded_files.append(doc['filename'])
            
            st.session_state.documents_loaded = True
            return True
            
    except Exception as e:
        st.error(f"Error loading documents from folder: {str(e)}")
        return False


def render_welcome_screen():
    """Render the welcome screen when no documents are uploaded"""
    # Titre principal
    st.markdown('<h1 class="main-title">How can I help you?</h1>', unsafe_allow_html=True)
    
    # Upload de documents si demandé
    if st.session_state.get('show_upload', False):
        st.markdown("""
        <div class="upload-container">
            <div class="upload-icon">📄</div>
            <div class="upload-text">Upload regulatory documents</div>
            <div style="color: #5f6368; font-size: 14px; margin-top: 10px;">
                Supported formats: PDF, DOCX, TXT, MD
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        uploaded_files = st.file_uploader(
            "Choose files (PDF, DOCX, TXT, MD)",
            type=["pdf", "docx", "txt", "md"],
            accept_multiple_files=True,
            label_visibility="collapsed"
        )
        
        if uploaded_files:
            st.info(f"📋 {len(uploaded_files)} file(s) selected")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                for file in uploaded_files:
                    file_size = len(file.getvalue()) / 1024  # KB
                    st.write(f"• {file.name} ({file_size:.1f} KB)")
            
            with col2:
                if st.button("📤 Process", use_container_width=True, type="primary"):
                    success_count = 0
                    for uploaded_file in uploaded_files:
                        if uploaded_file.name not in st.session_state.uploaded_files:
                            if process_uploaded_file(uploaded_file):
                                success_count += 1
                    
                    if success_count > 0:
                        st.success(f"{success_count} document(s) processed successfully!")
                        st.rerun()
    
    # Suggestions
    st.markdown("""
    <div class="suggestions-container">
        <p class="suggestions-intro">
            <strong>💬 General questions</strong> (ask now without documents):
        </p>
        <div class="suggestion-item">
            • What is GDPR and how does it apply to banking?
        </div>
        <div class="suggestion-item">
            • Explain the EU AI Act key requirements
        </div>
        <div class="suggestions-intro" style="margin-top: 30px;">
            <strong>📄 Document analysis</strong> (upload documents first):
        </div>
        <div class="suggestion-item">
            • Compare this internal policy to EU AI Act Article 9
        </div>
        <div class="suggestion-item">
            • Highlight regulatory gaps in this document against EBA guidelines
        </div>
        <div class="suggestion-item">
            • Perform a gap analysis between our current policies and GDPR Article 35
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_chat_interface():
    """Render the chat interface - works with or without documents"""
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar="👤" if message["role"] == "user" else "🔷"):
            st.markdown(message["content"])
            
            # Display sources if available
            if message.get("sources"):
                with st.expander("📚 Sources"):
                    st.markdown(message["sources"])
    
    # Chat input
    if prompt := st.chat_input("Message RegIntel AI"):
        # Add user message
        st.session_state.messages.append({
            "role": "user",
            "content": prompt
        })
        
        # Display user message
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)
        
        # Get response (RAG if documents loaded, otherwise general chat)
        with st.chat_message("assistant", avatar="🔷"):
            with st.spinner("Analyzing..."):
                try:
                    if st.session_state.documents_loaded:
                        # RAG mode with documents
                        result = st.session_state.rag_engine.query(prompt)
                        
                        # Display answer
                        st.markdown(result["answer"])
                        
                        # Format and display citations
                        citations = format_citations(result["sources"])
                        
                        if citations:
                            with st.expander("📚 Sources"):
                                st.markdown(citations)
                        
                        # Add to message history
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": result["answer"],
                            "sources": citations
                        })
                    else:
                        # General chat mode without documents
                        response = st.session_state.rag_engine.client.chat.completions.create(
                            model=MODEL_NAME,
                            messages=[
                                {"role": "system", "content": "You are RegIntel AI, an expert compliance and regulatory assistant for banking. Help users understand regulations, compliance requirements, and best practices."},
                                {"role": "user", "content": prompt}
                            ],
                            temperature=0.7
                        )
                        
                        answer = response.choices[0].message.content
                        
                        # Display answer
                        st.markdown(answer)
                        st.info("💡 Upload documents for specific analysis with citations!")
                        
                        # Add to message history
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": answer
                        })
                    
                except Exception as e:
                    error_msg = f"❌ Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg
                    })


def main():
    """Main application logic"""
    
    # Load custom CSS
    load_custom_css()
    
    # Initialize session state
    init_session_state()
    
    # Initialize RAG engine
    initialize_rag()
    
    # Render sidebar
    render_sidebar()
    
    # Main content area
    if not st.session_state.messages:
        # Welcome screen (with suggestions)
        render_welcome_screen()
    
    # Always show chat interface if there are messages
    if st.session_state.messages or not st.session_state.get('show_upload', False):
        render_chat_interface()


if __name__ == "__main__":
    main()
