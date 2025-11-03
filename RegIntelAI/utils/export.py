"""
Export utilities for RegIntel AI
"""
import csv
from datetime import datetime
from typing import List, Dict
from io import StringIO


def export_to_csv(chat_history: List[Dict]) -> str:
    """
    Export chat history to CSV format
    
    Args:
        chat_history: List of chat messages
        
    Returns:
        CSV content as string
    """
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(["Timestamp", "Role", "Message", "Sources"])
    
    # Write chat history
    for message in chat_history:
        timestamp = message.get("timestamp", datetime.now().isoformat())
        role = message.get("role", "unknown")
        content = message.get("content", "")
        sources = message.get("sources", "")
        
        writer.writerow([timestamp, role, content, sources])
    
    return output.getvalue()


def format_conversation_for_export(chat_history: List[Dict]) -> str:
    """
    Format chat history for text/PDF export
    
    Args:
        chat_history: List of chat messages
        
    Returns:
        Formatted text
    """
    lines = ["RegIntel AI - Conversation Export", 
             f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
             "=" * 80, ""]
    
    for idx, message in enumerate(chat_history, 1):
        role = message.get("role", "unknown").upper()
        content = message.get("content", "")
        sources = message.get("sources", "")
        
        lines.append(f"\n[{idx}] {role}:")
        lines.append("-" * 80)
        lines.append(content)
        
        if sources and role == "ASSISTANT":
            lines.append("\nSources:")
            lines.append(sources)
        
        lines.append("")
    
    return "\n".join(lines)
