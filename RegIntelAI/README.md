# RegIntel AI

**AI-Driven Regulatory & Compliance Copilot for HexaBank**

A specialized LLM application trained on European regulations (EBA, ECB, EU AI Act, etc.) that automatically extracts key requirements, performs gap analyses with HexaBank's internal policies, and drafts compliance updates for review.

---

## Business Value

- **Cuts regulatory-watch and interpretation time × 5**
- **Reduces compliance & reputational risk**
- **Ensures proactive alignment with Responsible AI and EU AI Act obligations**

---

## Features

### Core Capabilities
- **Hybrid Document Input**: Drag-and-drop PDF upload for regulatory documents
- **RAG-Powered Analysis**: Retrieval-Augmented Generation for evidence-based answers
- **Citations & Evidence**: Traceable references to source documents
- **Suggested Prompts**: Pre-defined compliance questions for quick analysis
- **Session Management**: Chat history with memory
- **Export Options**: Download conversations as TXT or CSV
- **Bilingual Support**: English and French

### Technical Architecture
- **Model**: GPT-4-mini (fast reasoning, bilingual)
- **Embeddings**: text-embedding-3-small (cheap and multilingual)
- **Vector Store**: ChromaDB (local, persistent)
- **Framework**: Streamlit (low-code, rapid deployment)
- **Hosting**: On-premise deployment for security

---

## Quick Start

### Prerequisites
- Python 3.9+
- OpenAI API key
- PDF documents (regulations, policies, etc.)

### Installation

1. **Clone or download the project**
```bash
cd RegIntelAI
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure OpenAI API Key**
```bash
# Copy the example env file
cp .env.example .env

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=sk-your-key-here
```

### Running the Application

```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

---

## Usage Guide

### 1. Upload Documents
- Click "Browse files" in the sidebar
- Select one or more PDF files (regulations, policies, etc.)
- Click "Process Documents"
- Wait for processing confirmation

### 2. Ask Questions
You can either:
- Click on suggested prompts for common queries
- Type your own compliance question in the chat input

**Example questions:**
- "Compare this internal policy to EU AI Act Article 9"
- "Highlight regulatory gaps in this document against EBA guidelines"
- "What are the key compliance requirements from this regulation?"
- "Perform a gap analysis between our current policies and GDPR Article 35"

### 3. Review Results
- Read the AI-generated analysis
- Click "Sources / Citations" to see evidence
- Continue the conversation with follow-up questions

### 4. Export Results
- Use "Download as TXT" for readable reports
- Use "Download as CSV" for structured data export

### 5. Session Management
- **Clear Chat**: Remove conversation history (keeps documents)
- **Clear All**: Reset everything (removes documents and history)

---

## Project Structure

```
RegIntelAI/
├── app.py                      # Main Streamlit application
├── config.py                   # Configuration settings
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules
├── README.md                  # This file
├── utils/
│   ├── __init__.py
│   ├── rag_engine.py          # RAG implementation (ChromaDB + OpenAI)
│   ├── document_processor.py  # PDF processing and chunking
│   └── export.py              # Export utilities (CSV, TXT)
├── data/                      # Uploaded documents (gitignored)
└── chroma_db/                 # Vector database (gitignored)
```

---

## Configuration

Edit `config.py` to customize:

```python
# Model Configuration
MODEL_NAME = "gpt-4o-mini"
EMBEDDING_MODEL = "text-embedding-3-small"

# RAG Parameters
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
TOP_K_RESULTS = 5

# Suggested Prompts
SUGGESTED_PROMPTS = [
    "Your custom prompts here..."
]
```

---

## Security Considerations

- **On-premise deployment**: Recommended for sensitive regulatory data
- **API Key Security**: Store in `.env` file (never commit to git)
- **Data Privacy**: Documents stored locally in ChromaDB
- **Access Control**: Deploy behind corporate VPN/firewall

---

## Testing

### Test with Sample Documents
1. Download sample regulations (e.g., EU AI Act PDF)
2. Upload to RegIntel AI
3. Try suggested prompts
4. Verify citations match source documents

### Example Test Cases
- **Gap Analysis**: "Compare our data governance policy to GDPR Article 35"
- **Requirement Extraction**: "List all mandatory requirements from ECB Regulation 2024/123"
- **Risk Assessment**: "What compliance risks does this policy introduce?"

---

## Troubleshooting

### "Impossible de résoudre l'importation" errors
These are IDE warnings before installation. Install dependencies to resolve:
```bash
pip install -r requirements.txt
```

### "Please set your OpenAI API key"
Create `.env` file with:
```
OPENAI_API_KEY=sk-your-actual-key
```

### ChromaDB errors
Delete the `chroma_db` folder and restart:
```bash
rm -rf chroma_db
streamlit run app.py
```

### Slow processing
- Reduce `CHUNK_SIZE` in `config.py`
- Use fewer documents
- Upgrade to faster OpenAI models

---

## Performance Metrics

**Expected Performance:**
- Document upload: ~5-10 seconds per PDF
- Query response: ~3-5 seconds
- Accuracy: Depends on document quality and query clarity
- Cost: ~$0.01-0.05 per query (embeddings + generation)

---

## Future Enhancements

1. **Multi-language support**: Add more EU languages
2. **Advanced analytics**: Compliance score dashboard
3. **Document comparison**: Side-by-side gap analysis
4. **Automated reports**: Scheduled compliance summaries
5. **Fine-tuned models**: Domain-specific regulatory model
6. **API integration**: Connect to internal policy databases

---

## Development Notes

### Built With
- **Streamlit**: Low-code web framework
- **LangChain**: Document processing utilities
- **ChromaDB**: Vector database for semantic search
- **OpenAI**: LLM and embeddings
- **PyPDF**: PDF text extraction

### Design Decisions
- **RAG over Fine-tuning**: Better traceability and updateability
- **Local vector store**: Data privacy and security
- **Streamlit**: 6-hour delivery target achieved
- **Chunk-based citations**: Granular source attribution

---

## License

Proprietary - HexaBank Internal Use Only

---

## Contributors

**Albert School - LLM Product Development**
- Group A
- November 2025

---

## Support

For issues or questions:
1. Check troubleshooting section
2. Review configuration settings
3. Contact internal AI team

---

## References

- [EU AI Act](https://artificialintelligenceact.eu/)
- [EBA Guidelines](https://www.eba.europa.eu/)
- [ECB Regulations](https://www.ecb.europa.eu/)
- [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [OpenAI API Reference](https://platform.openai.com/docs)

---

**Built for HexaBank Compliance Team**
