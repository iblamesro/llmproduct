# Quick Start Guide - RegIntel AI

## New Features

### Multiple Document Format Support
- PDF documents (.pdf)
- Word documents (.docx)
- Text files (.txt)
- Markdown files (.md)

### Three Ways to Load Documents

#### 1. Upload from Computer
1. Click "Upload Documents" in the sidebar
2. Select one or multiple files
3. Click "Process" to add them to the RAG

#### 2. Load from Data Folder
1. Place documents in `data/sample_documents/`
2. Click "Load from Data Folder" in the sidebar
3. All documents will be automatically processed

#### 3. Pre-loaded Sample Documents
The app includes sample regulatory documents:
- EU AI Act Summary (MD)
- GDPR Article 35 - DPIA (TXT)

## Document Management

### View Active Documents
- Expand "Active Documents" in the sidebar
- See all loaded documents with file names

### Remove Individual Documents
- Click the trash icon next to any document
- Document is removed from the RAG

### Clear All Documents
- Click "Clear All Documents" in sidebar
- Removes all documents and resets the system

## Usage Examples

### 1. Quick Start with Sample Documents
```
1. Click "Load from Data Folder"
2. Ask: "What are the key requirements of the EU AI Act?"
3. Review answer with citations
```

### 2. Upload Custom Documents
```
1. Click "Upload Documents"
2. Select your PDF/DOCX/TXT files
3. Click "Process"
4. Ask questions about your documents
```

### 3. Compare Documents
```
1. Load multiple documents (sample + your policy)
2. Ask: "Compare our policy with GDPR Article 35"
3. Get gap analysis with specific citations
```

## Tips

- Upload multiple documents at once for comprehensive analysis
- Use specific questions for better results
- Check the "Sources" section for citation verification
- Export conversations for documentation

## File Size Limits

- Recommended: < 10 MB per file
- Large files will take longer to process
- Consider splitting very large documents

## Troubleshooting

### "Error processing file"
- Check file format is supported
- Ensure file is not corrupted
- Try converting to PDF if issues persist

### "No documents found"
- Check `data/sample_documents/` folder exists
- Verify files are in supported formats
- Ensure files are not empty

### Slow processing
- Normal for large documents
- Wait for processing spinner to complete
- Don't refresh page during processing
