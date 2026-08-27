import os
from typing import List, Dict, Any, Literal, Optional
from dataclasses import dataclass
import streamlit as st
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_milvus import Milvus
import tempfile
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from langchain.schema import HumanMessage
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langgraph.prebuilt import create_react_agent
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.language_models import BaseLanguageModel
from langchain.prompts import ChatPromptTemplate


def init_session_state():
    """Initialize session state variables"""
    if 'openai_api_key' not in st.session_state:
        st.session_state.openai_api_key = ""
    if 'milvus_uri' not in st.session_state:
        st.session_state.milvus_uri = "./milvus_data.db"  # Milvus Lite (local file)
    if 'embeddings' not in st.session_state:
        st.session_state.embeddings = None
    if 'llm' not in st.session_state:
        st.session_state.llm = None
    if 'databases' not in st.session_state:
        st.session_state.databases = {}


init_session_state()

DatabaseType = Literal["products", "support", "finance"]


@dataclass
class CollectionConfig:
    name: str
    description: str
    collection_name: str


# Collection configurations
COLLECTIONS: Dict[DatabaseType, CollectionConfig] = {
    "products": CollectionConfig(
        name="Product Information",
        description="Product details, specifications, and features",
        collection_name="products_collection"
    ),
    "support": CollectionConfig(
        name="Customer Support & FAQ",
        description="Customer support information, frequently asked questions, and guides",
        collection_name="support_collection"
    ),
    "finance": CollectionConfig(
        name="Financial Information",
        description="Financial data, revenue, costs, and liabilities",
        collection_name="finance_collection"
    )
}


def initialize_models():
    """Initialize OpenAI models and Milvus vector stores"""
    if st.session_state.openai_api_key:
        os.environ["OPENAI_API_KEY"] = st.session_state.openai_api_key
        st.session_state.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        st.session_state.llm = ChatOpenAI(temperature=0)

        try:
            st.session_state.databases = {}
            for db_type, config in COLLECTIONS.items():
                vector_store = Milvus(
                    embedding_function=st.session_state.embeddings,
                    collection_name=config.collection_name,
                    connection_args={"uri": st.session_state.milvus_uri},
                    auto_id=True,
                    drop_old=False,
                )
                st.session_state.databases[db_type] = vector_store

            return True
        except Exception as e:
            st.error(f"Failed to initialize Milvus: {str(e)}")
            return False
    return False


def process_document(file) -> List[Document]:
    """Process uploaded PDF document"""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(file.getvalue())
            tmp_path = tmp_file.name

        loader = PyPDFLoader(tmp_path)
        documents = loader.load()

        # Clean up temporary file
        os.unlink(tmp_path)

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        texts = text_splitter.split_documents(documents)

        return texts
    except Exception as e:
        st.error(f"Error processing document: {e}")
        return []


def create_routing_agent() -> Agent:
    """Creates a routing agent using agno framework"""
    return Agent(
        model=OpenAIChat(
            id="gpt-4o",
            api_key=st.session_state.openai_api_key
        ),
        tools=[],
        description="""You are a query routing expert. Your only job is to analyze questions and determine which database they should be routed to.
        You must respond with exactly one of these three options: 'products', 'support', or 'finance'. The user's question is: {question}""",
        instructions=[
            "Follow these rules strictly:",
            "1. For questions about products, features, specifications, or item details, or product manuals → return 'products'",
            "2. For questions about help, guidance, troubleshooting, or customer service, FAQ, or guides → return 'support'",
            "3. For questions about costs, revenue, pricing, or financial data, or financial reports and investments → return 'finance'",
            "4. Return ONLY the database name, no other text or explanation",
            "5. If you're not confident about the routing, return an empty response"
        ],
        markdown=False,
        show_tool_calls=False
    )


def route_query(question: str) -> Optional[DatabaseType]:
    """Route query by searching all databases and comparing relevance scores.
    Returns None if no suitable database is found."""
    try:
        best_score = -1
        best_db_type = None
        all_scores = {}

        # Search each database and compare relevance scores
        for db_type, db in st.session_state.databases.items():
            try:
                results = db.similarity_search_with_score(
                    question,
                    k=3
                )
            except Exception:
                # Collection might be empty
                continue

            if results:
                # Milvus returns (doc, distance); lower distance = more similar
                # Convert to similarity score: score = 1 / (1 + distance)
                avg_score = sum(1 / (1 + score) for _, score in results) / len(results)
                all_scores[db_type] = avg_score

                if avg_score > best_score:
                    best_score = avg_score
                    best_db_type = db_type

        confidence_threshold = 0.5
        if best_score >= confidence_threshold and best_db_type:
            st.success(f"Using vector similarity routing: {best_db_type} (confidence: {best_score:.3f})")
            return best_db_type

        st.warning(f"Low confidence scores (below {confidence_threshold}), falling back to LLM routing")

        # Fallback to LLM routing
        routing_agent = create_routing_agent()
        response = routing_agent.run(question)

        db_type = (response.content
                   .strip()
                   .lower()
                   .translate(str.maketrans('', '', '`\'"')))

        if db_type in COLLECTIONS:
            st.success(f"Using LLM routing decision: {db_type}")
            return db_type

        st.warning("No suitable database found, will use web search fallback")
        return None

    except Exception as e:
        st.error(f"Routing error: {str(e)}")
        return None


def create_fallback_agent(chat_model: BaseLanguageModel):
    """Create a LangGraph agent for web research."""

    def web_research(query: str) -> str:
        """Web search with result formatting."""
        try:
            search = DuckDuckGoSearchRun(num_results=5)
            results = search.run(query)
            return results
        except Exception as e:
            return f"Search failed: {str(e)}. Providing answer based on general knowledge."

    tools = [web_research]

    agent = create_react_agent(
        model=chat_model,
        tools=tools,
        debug=False
    )

    return agent


def query_database(db: Milvus, question: str) -> tuple[str, list]:
    """Query the Milvus vector store and return answer and relevant documents"""
    try:
        retriever = db.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 4}
        )

        relevant_docs = retriever.get_relevant_documents(question)

        if relevant_docs:
            retrieval_qa_prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a helpful AI assistant that answers questions based on provided context.
                             Always be direct and concise in your responses.
                             If the context doesn't contain enough information to fully answer the question, acknowledge this limitation.
                             Base your answers strictly on the provided context and avoid making assumptions."""),
                ("human", "Here is the context:\n{context}"),
                ("human", "Question: {input}"),
                ("assistant", "I'll help answer your question based on the context provided."),
                ("human", "Please provide your answer:"),
            ])
            combine_docs_chain = create_stuff_documents_chain(st.session_state.llm, retrieval_qa_prompt)
            retrieval_chain = create_retrieval_chain(retriever, combine_docs_chain)

            response = retrieval_chain.invoke({"input": question})
            return response['answer'], relevant_docs

        raise ValueError("No relevant documents found in database")

    except Exception as e:
        st.error(f"Error: {str(e)}")
        return "I encountered an error. Please try rephrasing your question.", []


def _handle_web_fallback(question: str) -> tuple[str, list]:
    """Handle web search fallback when no relevant documents found."""
    st.info("No relevant documents found. Searching web...")
    fallback_agent = create_fallback_agent(st.session_state.llm)

    with st.spinner('Researching...'):
        agent_input = {
            "messages": [
                HumanMessage(content=f"Research and provide a detailed answer for: '{question}'")
            ],
            "is_last_step": False
        }

        try:
            response = fallback_agent.invoke(agent_input, config={"recursion_limit": 100})
            if isinstance(response, dict) and "messages" in response:
                answer = response["messages"][-1].content
                return f"Web Search Result:\n{answer}", []

        except Exception:
            # Fallback to general LLM response
            fallback_response = st.session_state.llm.invoke(question).content
            return f"Web search unavailable. General response: {fallback_response}", []


def main():
    """Main application function."""
    st.set_page_config(page_title="RAG Agent with Milvus Routing", page_icon="🔍")
    st.title("🔍 RAG Agent with Milvus Database Routing")

    # Sidebar for API keys and configuration
    with st.sidebar:
        st.header("Configuration")

        # OpenAI API Key
        api_key = st.text_input(
            "Enter OpenAI API Key:",
            type="password",
            value=st.session_state.openai_api_key,
            key="api_key_input"
        )

        # Milvus Configuration
        milvus_uri = st.text_input(
            "Milvus URI:",
            value=st.session_state.milvus_uri,
            help="Local file path for Milvus Lite (e.g. ./milvus_data.db) or remote URI (e.g. http://localhost:19530)"
        )

        # Update session state
        if api_key:
            st.session_state.openai_api_key = api_key
        if milvus_uri:
            st.session_state.milvus_uri = milvus_uri

        # Initialize models if credentials are provided
        if st.session_state.openai_api_key:
            if initialize_models():
                st.success("Connected to OpenAI and Milvus successfully!")
            else:
                st.error("Failed to initialize. Please check your credentials.")
        else:
            st.warning("Please enter OpenAI API Key to continue")
            st.stop()

        st.markdown("---")
        st.markdown("""
        **Milvus Modes:**
        - **Milvus Lite**: Use a local file path (e.g. `./milvus_data.db`) — no server needed
        - **Milvus Standalone/Cluster**: Use `http://localhost:19530` or your server URI
        """)

    st.header("Document Upload")
    st.info("Upload documents to populate the databases. Each tab corresponds to a different collection.")
    tabs = st.tabs([config.name for config in COLLECTIONS.values()])

    for (collection_type, collection_config), tab in zip(COLLECTIONS.items(), tabs):
        with tab:
            st.write(collection_config.description)
            uploaded_files = st.file_uploader(
                f"Upload PDF documents to {collection_config.name}",
                type="pdf",
                key=f"upload_{collection_type}",
                accept_multiple_files=True
            )

            if uploaded_files:
                with st.spinner('Processing documents...'):
                    all_texts = []
                    for uploaded_file in uploaded_files:
                        texts = process_document(uploaded_file)
                        all_texts.extend(texts)

                    if all_texts:
                        db = st.session_state.databases[collection_type]
                        db.add_documents(all_texts)
                        st.success(f"Documents processed and added to {collection_config.name}!")

    # Query section
    st.header("Ask Questions")
    st.info("Enter your question below to find answers from the relevant database.")
    question = st.text_input("Enter your question:")

    if question:
        with st.spinner('Finding answer...'):
            # Route the question
            collection_type = route_query(question)

            if collection_type is None:
                # Use web search fallback directly
                answer, relevant_docs = _handle_web_fallback(question)
                st.write("### Answer (from web search)")
                st.write(answer)
            else:
                # Display routing information and query the database
                st.info(f"Routing question to: {COLLECTIONS[collection_type].name}")
                db = st.session_state.databases[collection_type]
                answer, relevant_docs = query_database(db, question)
                st.write("### Answer")
                st.write(answer)

                # Show source documents
                if relevant_docs:
                    with st.expander("View Source Documents"):
                        for i, doc in enumerate(relevant_docs, 1):
                            st.markdown(f"**Document {i}:**")
                            st.write(doc.page_content[:500])
                            st.markdown("---")


if __name__ == "__main__":
    main()
