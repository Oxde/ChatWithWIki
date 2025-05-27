"""
LangChain factory module.
Creates conversational retrieval chains with memory and vector stores.
"""

from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_history_aware_retriever
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain.schema import Document
import os
import tempfile
import time
import random


class ChainFactory:
    """Factory for creating LangChain conversational retrieval chains."""
    
    def __init__(self, openai_api_key: str = None):
        """
        Initialize chain factory.
        
        Args:
            openai_api_key: OpenAI API key (if not provided, uses environment variable)
        """
        self.api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        # Clean the API key - remove whitespace, newlines, etc.
        self.api_key = self.api_key.strip().replace('\n', '').replace('\r', '')
        
        if not self.api_key.startswith('sk-'):
            raise ValueError(f"Invalid OpenAI API key format. Key should start with 'sk-' but starts with: '{self.api_key[:10]}...'")
        
        # Initialize embeddings with alternative configuration
        try:
            self.embeddings = OpenAIEmbeddings(
                openai_api_key=self.api_key,
                model="text-embedding-ada-002",
                request_timeout=60,
                max_retries=3,
                openai_api_base=None,  # Explicitly set to None to use default
                openai_organization=None  # Explicitly set to None
            )
        except Exception as e:
            # Fallback initialization
            import openai
            openai.api_key = self.api_key
            self.embeddings = OpenAIEmbeddings(
                model="text-embedding-ada-002",
                request_timeout=60,
                max_retries=3
            )
        
        # Initialize LLM with alternative configuration
        try:
            self.llm = ChatOpenAI(
                openai_api_key=self.api_key,
                model="gpt-3.5-turbo",
                temperature=0.3,
                max_tokens=800,
                request_timeout=60,
                max_retries=3,
                openai_api_base=None,  # Explicitly set to None to use default
                openai_organization=None  # Explicitly set to None
            )
        except Exception as e:
            # Fallback initialization
            import openai
            openai.api_key = self.api_key
            self.llm = ChatOpenAI(
                model="gpt-3.5-turbo",
                temperature=0.3,
                max_tokens=800,
                request_timeout=60,
                max_retries=3
            )
        
        # Initialize chat history
        self.chat_history = []
    
    def _retry_with_backoff(self, func, max_retries=3, base_delay=1):
        """
        Retry function with exponential backoff.
        
        Args:
            func: Function to retry
            max_retries: Maximum number of retries
            base_delay: Base delay in seconds
            
        Returns:
            Function result
        """
        for attempt in range(max_retries + 1):
            try:
                return func()
            except Exception as e:
                if attempt == max_retries:
                    raise e
                
                # Exponential backoff with jitter
                delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                time.sleep(delay)
                continue
    
    def create_vector_store(self, documents: list[Document]) -> Chroma:
        """
        Create Chroma vector store from documents.
        
        Args:
            documents: List of Document objects to index
            
        Returns:
            Chroma: Vector store with embedded documents
        """
        if not documents:
            raise ValueError("No documents provided for vector store creation")
        
        # Create temporary directory for Chroma
        temp_dir = tempfile.mkdtemp()
        
        # Create Chroma vector store with retry logic
        def create_store():
            return Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                persist_directory=temp_dir
            )
        
        return self._retry_with_backoff(create_store, max_retries=3, base_delay=2)
    
    def create_diverse_retriever(self, vector_store: Chroma, search_type: str = "mmr") -> object:
        """
        Create a more diverse retriever using MMR (Maximal Marginal Relevance) or similarity.
        
        Args:
            vector_store: Chroma vector store
            search_type: "mmr" for diverse results or "similarity" for most relevant
            
        Returns:
            Retriever object configured for diverse results
        """
        if search_type == "mmr":
            # MMR helps get diverse, relevant results
            return vector_store.as_retriever(
                search_type="mmr",
                search_kwargs={
                    "k": 6,
                    "fetch_k": 12,  # Fetch more candidates
                    "lambda_mult": 0.7  # Balance between relevance and diversity
                }
            )
        else:
            return vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 6}
            )
    
    def create_conversational_chain(self, vector_store: Chroma, use_diverse_retrieval: bool = True) -> tuple:
        """
        Create conversational retrieval chain with memory using new LangChain API.
        
        Args:
            vector_store: Chroma vector store for retrieval
            use_diverse_retrieval: Whether to use a diverse retriever
            
        Returns:
            tuple: (retrieval_chain, history_aware_retriever, chat_history)
        """
        # Create retriever from vector store
        if use_diverse_retrieval:
            retriever = self.create_diverse_retriever(vector_store)
        else:
            retriever = vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 6}  # Increased to retrieve more diverse chunks
            )
        
        # Create contextualize question prompt
        contextualize_q_system_prompt = """Given a chat history and the latest user question \
which might reference context in the chat history, formulate a standalone question \
which can be understood without the chat history. Do NOT answer the question, \
just reformulate it if needed and otherwise return it as is."""
        
        contextualize_q_prompt = ChatPromptTemplate.from_messages([
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])
        
        # Create history-aware retriever
        history_aware_retriever = create_history_aware_retriever(
            self.llm, retriever, contextualize_q_prompt
        )
        
        # Create QA prompt
        qa_system_prompt = """You are a knowledgeable assistant helping users learn about Wikipedia articles. \
Use the following retrieved context to provide informative and engaging answers.

Guidelines:
- Provide detailed, helpful responses based on the context
- If the user asks a follow-up question, build upon previous conversation
- Vary your response style and focus on different aspects when similar questions are asked
- Include specific details, examples, or interesting facts when available
- If you don't know something, say so clearly
- Keep responses conversational but informative

Context: {context}"""
        
        qa_prompt = ChatPromptTemplate.from_messages([
            ("system", qa_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])
        
        # Create question-answer chain
        question_answer_chain = create_stuff_documents_chain(self.llm, qa_prompt)
        
        # Create retrieval chain
        rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
        
        return rag_chain, history_aware_retriever, self.chat_history
    
    def create_wiki_chain(self, documents: list[Document], use_diverse_retrieval: bool = True) -> tuple:
        """
        Create complete Wikipedia conversational chain.
        
        Args:
            documents: List of Document objects from Wikipedia article
            use_diverse_retrieval: Whether to use diverse retrieval for varied responses
            
        Returns:
            tuple: (retrieval_chain, history_aware_retriever, chat_history)
        """
        # Create vector store
        vector_store = self.create_vector_store(documents)
        
        # Create conversational chain with diverse retrieval
        chain, retriever, chat_history = self.create_conversational_chain(
            vector_store, use_diverse_retrieval
        )
        
        return chain, retriever, chat_history
    
    def get_chain_info(self, chain) -> dict:
        """
        Get information about the chain configuration.
        
        Args:
            chain: Retrieval chain to inspect
            
        Returns:
            dict: Chain configuration information
        """
        return {
            'llm_model': 'gpt-3.5-turbo',
            'retriever_type': 'VectorStoreRetriever',
            'memory_type': 'ChatHistory',
            'return_source_docs': True
        } 