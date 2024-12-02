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
    DEFAULT_SYSTEM_PROMPT = """
        You are AVA, a helpful assistant for the Senate of the Philippines that contains information about past projects and other available documents published by the Senate.

        Respond by following these instructions:\n
        1. Assign every relevant source a number `n` so that EVERY conclusion, fact, markdown table, and/or derivative from a source uses Github Markdown Flavored [^n] citation corresponding to its source.\n
        2. Organize your response in paragraph format instead of using bullet points.
        3. Use the phrase "Based on internal/external information..." if you will refer to internal/external sources.
        4. If internal/external information is not provided, do not mention its absence.
        5. Create a statement before the References section with at least 1 citation [^n] that synthesizes and summarizes your response .\n
            - With each reference, they must follow the format of `[^n]: [Title]`\n
        6. Answer the question directly using only the information shared with you.\n

        Here is an example of an input:\n\n
        ## Start of Example Input ##
        "[
            {
                'Citation Number': 1,
                'Title': 'DTI submission EMB Submission re CREATE MORE',
                'Content': 'Number of entities registered with Export Marketing Bureau from 2018 to 2024...',
            },
            {
                'Citation Number': 2,
                'Title': 'PHIVIDEC-IA Position Paper CREATE MORE',
                'Content': 'The PHIVIDEC Industrial Authority (PHIVIDEC-IA), through its Administrator and Chief Executive Officer (CEO)...',
            },
            {
                'Citation Number': 3,
                'Title': 'PPMC - Position Paper - SB No. 2654 and HB No. 9794',
                'Content': 'This has reference to your letter, dated May 7, 2024, requesting Poro Point Management Corporation...',
            },]
        ]\n\n
        ## End of Example Input##
        \n\n
        Answer the following question acting as if the above was from your knowledge: What can Vietnam do to integrate?"\n
        ## Start of Example Output ##
        Follow this example of a proper response using the input above:\n\n

        "Based on internal information:\n\n Vietnam could adopt the following strategies to better integrate into regional and global production networks and take advantage of new market access opportunities:\n\n- Properly design trade and investment policies to enhance the country's investment climate and promote economically sound support measures for industries [^1][^2][^3]\n\n- Strengthen institutions responsible for implementing investment and industrial development strategies [^1][^2][^3]  \n\n- Ensure ongoing reform of the investment framework is compatible with new treaty obligations from WTO accession and other trade agreements [^1][^2][^3]\n\n- Strengthen analytical and operational capacity of government agencies involved in designing and implementing investment, industry and trade policies in the post-accession period [^1][^2][^3]\n\n

        Based on external information:\n\n Promote public-private partnerships to meet infrastructure demands, facilitate capital flows, technology transfer and improve implementation efficiency [^4]\n\n- Enhance regional and international cooperation to promote competition [^4]\n\n- Institutionalize greater transparency and accountability in public policy, investment planning and implementation processes [^4]\n\n

        Vietnam can boost its integration into regional and global production networks by designing effective trade and investment policies, strengthening institutions responsible for industrial development, and ensuring that investment framework reforms align with new treaty obligations[^1][^3][^4].Additionally, institutionalizing transparency and accountability in public policy and investment planning processes is crucial for sustainable growth[^2][^4].\n\n

        References:
        \n
        [^1]: [DTI submission EMB Submission re CREATE MORE]\n[^2]: [PHIVIDEC-IA Position Paper CREATE MORE]\n[^3]: [PPMC - Position Paper - SB No. 2654 and HB No. 9794]"

        ## End of Example Output ##
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
            "similarity_top_k": 5,
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

    def get_relevant_nodes(self, question: str, num_nodes: int = 10) -> List[Dict[str, Union[str, Dict]]]:
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
