import streamlit as st
import requests
import os

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")

st.set_page_config(page_title="RAG Chat System", page_icon="🤖", layout="wide")

# Custom CSS
st.markdown(
    """
<style>
    /* Main header */
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
        color: #1f77b4;
    }
    
    /* Full width buttons */
    .stButton>button {
        width: 100%;
    }
    
    /* Chat message styling */
    .stChatMessage {
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 10px;
    }
    
    /* Assistant message markdown styling */
    .stChatMessage [data-testid="stMarkdownContainer"] h1,
    .stChatMessage [data-testid="stMarkdownContainer"] h2,
    .stChatMessage [data-testid="stMarkdownContainer"] h3 {
        margin-top: 0.8rem;
        margin-bottom: 0.4rem;
        color: #1f77b4;
    }
    
    /* Code blocks */
    .stChatMessage [data-testid="stMarkdownContainer"] code {
        background-color: #f0f2f6;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.85em;
        color: #e83e8c;
    }
    
    /* Code block (multi-line) */
    .stChatMessage [data-testid="stMarkdownContainer"] pre {
        background-color: #1e1e1e;
        color: #d4d4d4;
        padding: 15px;
        border-radius: 8px;
        overflow-x: auto;
    }
    
    /* Bullet points */
    .stChatMessage [data-testid="stMarkdownContainer"] ul {
        padding-left: 1.5rem;
        margin: 0.5rem 0;
    }
    
    /* List items */
    .stChatMessage [data-testid="stMarkdownContainer"] li {
        margin-bottom: 0.3rem;
    }
    
    /* Bold text */
    .stChatMessage [data-testid="stMarkdownContainer"] strong {
        color: #0f0f0f;
        font-weight: 700;
    }
    
    /* Blockquote */
    .stChatMessage [data-testid="stMarkdownContainer"] blockquote {
        border-left: 4px solid #1f77b4;
        padding-left: 1rem;
        margin: 0.5rem 0;
        color: #555;
        font-style: italic;
    }
    
    /* Tables */
    .stChatMessage [data-testid="stMarkdownContainer"] table {
        width: 100%;
        border-collapse: collapse;
        margin: 1rem 0;
    }
    
    .stChatMessage [data-testid="stMarkdownContainer"] th {
        background-color: #1f77b4;
        color: white;
        padding: 8px 12px;
        text-align: left;
    }
    
    .stChatMessage [data-testid="stMarkdownContainer"] td {
        padding: 8px 12px;
        border-bottom: 1px solid #ddd;
    }
    
    .stChatMessage [data-testid="stMarkdownContainer"] tr:hover {
        background-color: #f5f5f5;
    }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown('<div class="main-header">🤖 RAG Chat System</div>', unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "session_id" not in st.session_state:
    st.session_state.session_id = None  # Will be set by backend on first message

# Sidebar for file upload
with st.sidebar:
    st.header("📁 Document Management")

    # Check backend health
    try:
        health_response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if health_response.status_code == 200:
            st.success("✅ Backend Connected")

        else:
            st.error("❌ Backend Unhealthy")
    except Exception as e:
        st.error(f"❌ Backend Unreachable: {str(e)}")

    st.markdown("---")

    # File upload section
    st.subheader("Upload Documents")
    uploaded_file = st.file_uploader(
        "Choose a PDF or TXT file",
        type=["pdf", "txt"],
        help="Upload documents to index them in the knowledge base",
    )

    if uploaded_file is not None:
        if st.button("📤 Index Document", use_container_width=True):
            with st.spinner("Indexing document..."):
                try:
                    files = {
                        "file": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            uploaded_file.type,
                        )
                    }
                    response = requests.post(
                        f"{BACKEND_URL}/index",
                        files=files,
                        timeout=300,  # 5 minutes timeout for indexing
                    )

                    if response.status_code == 200:
                        result = response.json()
                        st.success(
                            f"✅ Successfully indexed {result['chunks_indexed']} chunks from {result['filename']}"
                        )
                    else:
                        st.error(
                            f"❌ Error: {response.json().get('detail', 'Unknown error')}"
                        )

                except requests.exceptions.Timeout:
                    st.error("❌ Request timed out. The document might be too large.")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

    st.markdown("---")

    # Settings
    st.subheader("⚙️ Settings")
    top_k = st.slider(
        "Number of context chunks",
        min_value=1,
        max_value=10,
        value=3,
        help="Number of relevant chunks to retrieve for context",
    )

    if st.button("🗑️ Clear Chat History", use_container_width=True):
        # Clear session on backend if exists
        if st.session_state.session_id:
            try:
                requests.delete(f"{BACKEND_URL}/session/{st.session_state.session_id}")
            except Exception as e:
                pass  # Ignore errors

        # Clear local state
        st.session_state.messages = []
        st.session_state.session_id = None
        st.rerun()

# Main chat interface
st.header("💬 Chat")

# Display chat messages
chat_container = st.container()
with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant":
                st.markdown(message["content"], unsafe_allow_html=True)
            else:
                st.markdown(message["content"])

            # Display sources if available
            if message["role"] == "assistant" and "sources" in message:
                if message["sources"]:
                    with st.expander("📚 Sources"):
                        for source in message["sources"]:
                            st.markdown(f"- {source}")

# Chat input
if prompt := st.chat_input("Ask a question about your documents..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get assistant response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = requests.post(
                    f"{BACKEND_URL}/chat",
                    json={
                        "query": prompt,
                        "top_k": top_k,
                        "session_id": st.session_state.session_id,  # Pass session_id
                    },
                    timeout=300,
                )

                if response.status_code == 200:
                    result = response.json()
                    answer = result["answer"]
                    sources = result["sources"]
                    session_id = result.get(
                        "session_id"
                    )  # Get session_id from response

                    # Store session_id for future requests
                    if session_id:
                        st.session_state.session_id = session_id

                    st.markdown(answer, unsafe_allow_html=True)

                    # Display sources
                    if sources:
                        with st.expander("📚 Sources"):
                            for source in sources:
                                st.markdown(f"- {source}")

                    # Add assistant message to chat history
                    st.session_state.messages.append(
                        {"role": "assistant", "content": answer, "sources": sources}
                    )
                else:
                    error_msg = (
                        f"Error: {response.json().get('detail', 'Unknown error')}"
                    )
                    st.error(error_msg)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": error_msg, "sources": []}
                    )

            except requests.exceptions.Timeout:
                error_msg = "Request timed out. Please try again."
                st.error(error_msg)
                st.session_state.messages.append(
                    {"role": "assistant", "content": error_msg, "sources": []}
                )
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append(
                    {"role": "assistant", "content": error_msg, "sources": []}
                )

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>Powered by Qwen-0.5B, BGE-Small, Qdrant, and FastAPI</div>",
    unsafe_allow_html=True,
)
