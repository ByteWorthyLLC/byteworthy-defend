"""
AI-powered threat analysis and natural language query interface.

This module provides Claude AI integration for:
- Script analysis (PowerShell, Batch, Python)
- Network behavior analysis
- Plain language threat explanations
- Natural language queries over security logs
- Incident report generation
"""

from hifzdefend.ai.claude_analyzer import ClaudeAnalyzer

# ChromaDB is optional - only import if available
try:
    from hifzdefend.ai.nl_interface import NaturalLanguageInterface

    CHROMADB_AVAILABLE = True
except (ImportError, Exception):
    # ChromaDB not available or incompatible
    NaturalLanguageInterface = None  # type: ignore
    CHROMADB_AVAILABLE = False

__all__ = ["ClaudeAnalyzer", "NaturalLanguageInterface", "CHROMADB_AVAILABLE"]
