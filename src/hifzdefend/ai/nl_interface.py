"""
Natural language query interface for security logs using RAG (Retrieval Augmented Generation).
"""

import logging
from pathlib import Path
from typing import Any, Optional

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from hifzdefend.ai.claude_analyzer import ClaudeAnalyzer
from hifzdefend.utils.exceptions import HifzDefendError

logger = logging.getLogger(__name__)


class NLInterfaceError(HifzDefendError):
    """Natural language interface error."""

    pass


class NaturalLanguageInterface:
    """
    Natural language query interface for security logs.

    Features:
    - Vector-based semantic search over logs
    - RAG (Retrieval Augmented Generation) with Claude
    - Interactive threat investigation
    - Context-aware query responses
    """

    def __init__(
        self,
        vector_db_path: Path,
        claude_analyzer: ClaudeAnalyzer,
        embedding_model: str = "all-MiniLM-L6-v2",
        collection_name: str = "security_logs",
        max_context_results: int = 5,
    ):
        """
        Initialize natural language interface.

        Args:
            vector_db_path: Path to ChromaDB database
            claude_analyzer: Claude analyzer instance
            embedding_model: Sentence transformer model name
            collection_name: ChromaDB collection name
            max_context_results: Max results to retrieve for context
        """
        self.vector_db_path = Path(vector_db_path)
        self.claude_analyzer = claude_analyzer
        self.collection_name = collection_name
        self.max_context_results = max_context_results

        # Initialize embedding model
        try:
            logger.info(f"Loading embedding model: {embedding_model}")
            self.embedder = SentenceTransformer(embedding_model)
        except Exception as e:
            raise NLInterfaceError(f"Failed to load embedding model: {e}")

        # Initialize ChromaDB
        try:
            self.vector_db_path.mkdir(parents=True, exist_ok=True)
            self.client = chromadb.PersistentClient(
                path=str(self.vector_db_path),
                settings=Settings(anonymized_telemetry=False),
            )
            self.collection = self.client.get_or_create_collection(
                name=collection_name, metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"ChromaDB initialized at {self.vector_db_path}")
        except Exception as e:
            raise NLInterfaceError(f"Failed to initialize ChromaDB: {e}")

    def index_log_entry(
        self, log_id: str, log_data: dict[str, Any], metadata: Optional[dict[str, Any]] = None
    ) -> None:
        """
        Index a log entry for semantic search.

        Args:
            log_id: Unique log identifier
            log_data: Log data dictionary
            metadata: Additional metadata
        """
        try:
            # Create searchable text from log data
            text_parts = []
            for key, value in log_data.items():
                if isinstance(value, (str, int, float, bool)):
                    text_parts.append(f"{key}: {value}")
                elif isinstance(value, dict):
                    for k, v in value.items():
                        text_parts.append(f"{key}.{k}: {v}")

            searchable_text = " | ".join(text_parts)

            # Generate embedding
            embedding = self.embedder.encode(searchable_text).tolist()

            # Prepare metadata
            if metadata is None:
                metadata = {}
            metadata.update(
                {
                    "timestamp": log_data.get("timestamp", ""),
                    "severity": log_data.get("severity", ""),
                    "event_type": log_data.get("event_type", ""),
                }
            )

            # Add to collection
            self.collection.add(
                ids=[log_id],
                embeddings=[embedding],
                documents=[searchable_text],
                metadatas=[metadata],
            )

            logger.debug(f"Indexed log entry: {log_id}")

        except Exception as e:
            logger.error(f"Failed to index log entry {log_id}: {e}")
            raise NLInterfaceError(f"Failed to index log entry: {e}")

    def index_logs_batch(
        self, logs: list[tuple[str, dict[str, Any], Optional[dict[str, Any]]]]
    ) -> int:
        """
        Index multiple log entries in batch.

        Args:
            logs: List of (log_id, log_data, metadata) tuples

        Returns:
            Number of logs indexed successfully
        """
        indexed_count = 0
        for log_id, log_data, metadata in logs:
            try:
                self.index_log_entry(log_id, log_data, metadata)
                indexed_count += 1
            except NLInterfaceError:
                continue  # Skip failed entries

        logger.info(f"Indexed {indexed_count}/{len(logs)} log entries")
        return indexed_count

    def query(self, question: str, use_claude: bool = True) -> dict[str, Any]:
        """
        Query security logs using natural language.

        Args:
            question: Natural language question
            use_claude: Use Claude for answer generation

        Returns:
            Query result with answer and context
        """
        try:
            # Generate query embedding
            query_embedding = self.embedder.encode(question).tolist()

            # Search for relevant logs
            results = self.collection.query(
                query_embeddings=[query_embedding], n_results=self.max_context_results
            )

            # Extract context
            context_logs = []
            if results["documents"] and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                    distance = results["distances"][0][i] if results["distances"] else 0.0
                    context_logs.append(
                        {"document": doc, "metadata": metadata, "distance": distance}
                    )

            # Generate answer with Claude if requested
            answer = ""
            if use_claude and context_logs:
                # Build context string
                context_str = "\n\n".join(
                    [
                        f"Log {i+1} (relevance: {1-log['distance']:.2f}):\n{log['document']}"
                        for i, log in enumerate(context_logs)
                    ]
                )

                # Build prompt
                prompt = f"""Answer this question about security logs:

Question: {question}

Relevant log entries:
{context_str}

Provide a clear, concise answer based on the log entries. If the logs don't contain enough information, say so."""

                response = self.claude_analyzer._call_claude(prompt)
                answer = response["text"]
            else:
                answer = f"Found {len(context_logs)} relevant log entries (Claude disabled)"

            return {
                "question": question,
                "answer": answer,
                "context": context_logs,
                "num_results": len(context_logs),
            }

        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise NLInterfaceError(f"Query failed: {e}")

    def interactive_query(self) -> None:
        """
        Start an interactive query session.
        """
        print("\n=== HifzDefend Natural Language Query Interface ===")
        print("Ask questions about your security logs.")
        print("Type 'exit' or 'quit' to end the session.\n")

        while True:
            try:
                question = input("Q: ").strip()
                if question.lower() in ["exit", "quit", ""]:
                    print("Goodbye!")
                    break

                result = self.query(question)

                print(f"\nA: {result['answer']}\n")
                print(f"Context: {result['num_results']} relevant log entries\n")

                # Optionally show context
                if result["num_results"] > 0:
                    show_context = input("Show context logs? (y/n): ").strip().lower()
                    if show_context == "y":
                        for i, log in enumerate(result["context"]):
                            print(f"\n--- Log {i+1} ---")
                            print(log["document"])
                            print(f"Metadata: {log['metadata']}")
                        print()

            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}\n")

    def get_stats(self) -> dict[str, Any]:
        """
        Get statistics about the indexed logs.

        Returns:
            Dict with collection stats
        """
        count = self.collection.count()
        return {
            "collection_name": self.collection_name,
            "total_logs": count,
            "vector_db_path": str(self.vector_db_path),
            "embedding_model": self.embedder.get_sentence_embedding_dimension(),
        }

    def clear_index(self) -> int:
        """
        Clear all indexed logs.

        Returns:
            Number of logs removed
        """
        count = self.collection.count()
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.create_collection(
            name=self.collection_name, metadata={"hnsw:space": "cosine"}
        )
        logger.info(f"Cleared {count} log entries from index")
        return count
