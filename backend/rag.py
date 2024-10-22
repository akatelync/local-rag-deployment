import os
from typing import List
from dotenv import load_dotenv
from typing import List, Dict, Union
from llama_index.core import VectorStoreIndex, Settings
from llama_index.vector_stores.astra import AstraDBVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.core.callbacks import CallbackManager, LlamaDebugHandler

class LlamaIndexRAG:
    # Default system prompt as a class constant
    DEFAULT_SYSTEM_PROMPT = """You are a helpful AI assistant in the Senate of the Philippines focused on providing accurate information.
    When responding:
    1. Always base your answers on the provided context
    2. Cite specific sources from the context when possible
    3. If the context doesn't contain enough information, acknowledge this limitation
    4. Keep responses clear and concise while maintaining accuracy
    5. If you're unsure about something, acknowledge the uncertainty

    Strictly follow this example:

    - Answer 1
    - Answer 2

    """

    def __init__(self, astra_token: str, openai_api_key: str, 
                 collection_name: str, astra_db_id: str, 
                 astra_db_region: str, astra_keyspace: str,
                 system_prompt: str = None,
                 use_default_prompt: bool = True):
        """Initialize the RAG chatbot with LlamaIndex and AstraDB.
        
        Args:
            system_prompt (str, optional): Custom system prompt to override the default.
            use_default_prompt (bool): Whether to use the default system prompt if no custom prompt is provided.
                                     If False and no system_prompt is provided, no prompt will be used.
        """
        # Set up debug logging
        self.debug_handler = LlamaDebugHandler()
        callback_manager = CallbackManager([self.debug_handler])

        # Initialize embedding model
        embed_model = OpenAIEmbedding(model="text-embedding-3-small")

        # Determine which system prompt to use
        final_prompt = None
        if system_prompt is not None:
            final_prompt = system_prompt
        elif use_default_prompt:
            final_prompt = self.DEFAULT_SYSTEM_PROMPT

        # Initialize LLM with system prompt if provided
        llm_config = {
            "model": "gpt-4o-mini",
        }
        if final_prompt:
            llm_config["system_prompt"] = final_prompt
            
        llm = OpenAI(**llm_config)

        # Initialize settings
        Settings.embed_model = embed_model
        Settings.llm = llm
        Settings.callback_manager = callback_manager

        # Initialize AstraDB vector store
        self.vector_store = AstraDBVectorStore(
            token=astra_token,
            api_endpoint=f"https://{astra_db_id}-{astra_db_region}.apps.astra.datastax.com",
            collection_name=collection_name,
            namespace=astra_keyspace,
            embedding_dimension=1536  # for text-embedding-3-small
        )

        # Set vector store in settings
        Settings.vector_store = self.vector_store

        # Create vector store index
        self.index = VectorStoreIndex.from_vector_store(
            vector_store=self.vector_store
        )

        # Create query engine with chat mode if system prompt is provided
        engine_config = {
            "similarity_top_k": 3,
            "streaming": True,
        }
        if final_prompt:
            engine_config["chat_mode"] = True
            
        self.query_engine = self.index.as_query_engine(**engine_config)

    def query(self, question: str) -> str:
        """Query the RAG system."""
        try:
            response = self.query_engine.query(question)
            return str(response)
        except Exception as e:
            return f"Error processing query: {str(e)}"

    def get_relevant_nodes(self, question: str, num_nodes: int = 3) -> List[Dict[str, Union[str, Dict]]]:
        """Retrieve both text and metadata from the most relevant nodes for a given question.
        
        Args:
            question (str): The query question
            num_nodes (int): Number of relevant nodes to retrieve
            
        Returns:
            List[Dict[str, Union[str, Dict]]]: List of dictionaries containing:
                - text: The full text content of the node
                - metadata: The complete metadata dictionary
                - score: The relevance score of the node
        """
        retriever = self.index.as_retriever(similarity_top_k=num_nodes)
        nodes = retriever.retrieve(question)
        return [node.node.text for node in nodes]