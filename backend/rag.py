from llama_index.core import VectorStoreIndex, Settings, Document
from llama_index.core.node_parser import SentenceSplitter
from llama_index.vector_stores.astra import AstraDBVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.core.callbacks import CallbackManager, LlamaDebugHandler
from typing import List, Optional


class LlamaIndexRAG:
    DEFAULT_SYSTEM_PROMPT = """
        You are AVA, a helpful assistant for the Senate of the Philippines that contains information about past projects and other available documents published by the Senate.
        Respond by following these instructions:
        1. Assign every relevant source a number `n` so that EVERY conclusion, fact, markdown table, and/or derivative from a source uses Github Markdown Flavored [^n] citation corresponding to its source.
        2. Organize your response in paragraph format instead of using bullet points.
        3. Use the phrase "Based on internal/external information..." if you will refer to internal/external sources.
        4. If internal/external information is not provided, do not mention its absence.
        5. Create a statement before the References section with at least 1 citation [^n] that synthesizes and summarizes your response.
        6. Answer the question directly using only the information shared with you.
    """

    def __init__(
        self,
        system_type: str,
        openai_api_key: str,
        astra_token: Optional[str] = None,
        astra_db_id: Optional[str] = None,
        astra_db_region: Optional[str] = None,
        astra_keyspace: Optional[str] = None,
        collection_name: Optional[str] = None,
        system_prompt: Optional[str] = None,
        use_default_prompt: bool = True,
    ):
        # Initialization of the core systems
        self.system_type = system_type
        self.debug_handler = LlamaDebugHandler()
        callback_manager = CallbackManager([self.debug_handler])

        # Set embedding model
        embed_model = OpenAIEmbedding(model="text-embedding-3-small")
        Settings.embed_model = embed_model
        Settings.callback_manager = callback_manager

        # Configure prompt
        final_prompt = system_prompt or (
            self.DEFAULT_SYSTEM_PROMPT if use_default_prompt else None)

        # Set up the language model
        llm_config = {
            "model": "gpt-4o",
            "temperature": 0,
            "max_tokens": 1024,
            "api_key": openai_api_key,
        }
        if final_prompt:
            llm_config["system_prompt"] = final_prompt
        self.llm = OpenAI(**llm_config)
        Settings.llm = self.llm

        # Set up system-specific configuration
        if system_type == "general":
            if not all([astra_token, astra_db_id, astra_db_region, astra_keyspace, collection_name]):
                raise ValueError(
                    "Missing required Astra DB parameters for the 'general' system.")
            self.vector_store = AstraDBVectorStore(
                token=astra_token,
                api_endpoint=f"https://{astra_db_id}-{astra_db_region}.apps.astra.datastax.com",
                collection_name=collection_name,
                namespace=astra_keyspace,
                embedding_dimension=1536,
            )
            self.index = VectorStoreIndex.from_vector_store(
                vector_store=self.vector_store)
        elif system_type == "journal":
            self.text_splitter = SentenceSplitter(
                chunk_size=512, chunk_overlap=50)
            self.pdf_index = None
        else:
            raise ValueError(
                "Invalid system type. Must be 'general' or 'journal'.")

    def process_pdf_content(self, pdf_content: List[str]) -> None:
        if self.system_type != "journal":
            raise RuntimeError(
                "PDF processing is only available for the 'journal' system.")
        full_text = "\n".join(pdf_content)
        document = Document(text=full_text)
        self.pdf_index = VectorStoreIndex.from_documents(
            [document], show_progress=True)

    def query(self, question: str) -> str:
        if self.system_type == "journal" and self.pdf_index:
            query_engine = self.pdf_index.as_query_engine(
                similarity_top_k=5, streaming=True)
        elif self.system_type == "general":
            query_engine = self.index.as_query_engine(
                similarity_top_k=5, streaming=True)
        else:
            return "No data available for querying."
        return str(query_engine.query(question))

    def get_relevant_nodes(self, question: str) -> List[str]:
        if self.system_type == "journal" and not self.pdf_index:
            raise RuntimeError(
                "PDF index is not initialized. Please process the PDF content first.")

        # Use the appropriate retriever based on the system type
        retriever = (
            self.pdf_index.as_retriever(similarity_top_k=5)
            if self.system_type == "journal" and self.pdf_index
            else self.index.as_retriever(similarity_top_k=5)
        )

        # Retrieve nodes
        nodes = retriever.retrieve(question)
        return [node.node.text for node in nodes]
